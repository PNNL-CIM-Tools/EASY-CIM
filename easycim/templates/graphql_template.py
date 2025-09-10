from __future__ import annotations
import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Dict, Any, List, Optional, Union, Set
from uuid import UUID
from cimgraph.models import GraphModel
from cimgraph.data_profile.identity import Identity
import cimgraph.data_profile.cimhub_2023 as cim

@dataclass
class GraphQLTemplate:
    """
    Represents a GraphQL-like template for extracting data from a GraphModel.
    """
    root_type: type
    root_filter: Optional[Dict[str, Any]] = None
    fields: Dict[str, Union[bool, 'GraphQLTemplate']] = None
    limit: Optional[int] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = {}

class GraphQLTemplater:
    """
    Generic GraphQL templater for flattening GraphModel typed property graphs
    into nested JSON structures.
    """
    
    def __init__(self, graph_model: GraphModel):
        if not isinstance(graph_model, GraphModel):
            raise TypeError("graph_model must be an instance of GraphModel, not the class itself")
        self.graph_model = graph_model
        self._processed_objects: Set[UUID] = set()
    
    def query(self, template: GraphQLTemplate, root_name: str = "catalog") -> Dict[str, Any]:
        """
        Execute a GraphQL-like query against the graph model.
        
        Args:
            template: GraphQLTemplate defining what to extract
            root_name: Name for the root object in output
            
        Returns:
            Dict containing the flattened graph data
        """
        self._processed_objects.clear()
        
        # Get root objects
        root_objects = self._get_root_objects(template)
        
        if not root_objects:
            return {}
        
        # For single object, return it directly under root_name
        if len(root_objects) == 1:
            result = self._process_object(root_objects[0], template)
            return {root_name: result}
        
        # For multiple objects, return as array
        results = [self._process_object(obj, template) for obj in root_objects]
        return {root_name: results}
    
    def _get_root_objects(self, template: GraphQLTemplate) -> List[Identity]:
        """Get root objects based on template criteria."""
        # Use the correct method signature
        objects = self.graph_model.list_by_class(template.root_type)
        
        # Apply filters if specified
        if template.root_filter:
            filtered_objects = []
            for obj in objects:
                if self._matches_filter(obj, template.root_filter):
                    filtered_objects.append(obj)
            objects = filtered_objects
        
        # Apply limit if specified
        if template.limit:
            objects = objects[:template.limit]
            
        return objects
    
    def _matches_filter(self, obj: Identity, filter_criteria: Dict[str, Any]) -> bool:
        """Check if object matches filter criteria."""
        for attr_name, expected_value in filter_criteria.items():
            if not hasattr(obj, attr_name):
                return False
            
            actual_value = getattr(obj, attr_name)
            
            # Handle different comparison types
            if isinstance(expected_value, dict):
                # Handle operators like {"$eq": value}, {"$in": [values]}
                for op, value in expected_value.items():
                    if op == "$eq" and actual_value != value:
                        return False
                    elif op == "$in" and actual_value not in value:
                        return False
                    elif op == "$ne" and actual_value == value:
                        return False
            else:
                # Direct equality comparison
                if str(actual_value) != str(expected_value):
                    return False
        
        return True
    
    def _process_object(self, obj: Identity, template: GraphQLTemplate) -> Dict[str, Any]:
        """Process a single object according to the template."""
        if obj.identifier in self._processed_objects:
            # Return minimal reference to avoid cycles
            return {
                "@id": str(obj.identifier),
                "@type": obj.__class__.__name__
            }
        
        self._processed_objects.add(obj.identifier)
        
        result = {
            "@type": obj.__class__.__name__
        }
        
        # Process requested fields
        for field_name, field_spec in template.fields.items():
            if field_name == "@type":
                continue  # Already handled
                
            if hasattr(obj, field_name):
                field_value = getattr(obj, field_name)
                processed_value = self._process_field_value(
                    field_value, field_spec, obj
                )
                if processed_value is not None:
                    result[field_name] = processed_value
        
        # If no specific fields requested, include all non-empty scalar fields
        if not template.fields:
            result.update(self._get_default_fields(obj))
        
        return result
    
    def _process_field_value(self, value: Any, field_spec: Union[bool, GraphQLTemplate], parent_obj: Identity) -> Any:
        """Process a field value according to its specification."""
        if value is None:
            return None
        
        # Handle simple inclusion (field_spec = True)
        if field_spec is True:
            return self._serialize_value(value)
        
        # Handle nested template
        elif isinstance(field_spec, GraphQLTemplate):
            if isinstance(value, list):
                results = []
                for item in value:
                    if isinstance(item, Identity):
                        # Check if this item matches the template's root_type
                        if isinstance(item, field_spec.root_type):
                            results.append(self._process_object(item, field_spec))
                return results if results else None
            elif isinstance(value, Identity):
                if isinstance(value, field_spec.root_type):
                    return self._process_object(value, field_spec)
                else:
                    return self._serialize_value(value)
            else:
                return self._serialize_value(value)
        
        # Handle exclusion (field_spec = False)
        elif field_spec is False:
            return None
        
        # Default serialization
        else:
            return self._serialize_value(value)
    
    def _get_default_fields(self, obj: Identity) -> Dict[str, Any]:
        """Get default fields for an object when no specific fields are requested."""
        result = {}
        
        for field in fields(obj):
            field_name = field.name
            if field_name in ['identifier', '__uuid__', '__json_ld__']:
                continue
                
            value = getattr(obj, field_name)
            if value is not None and value != [] and value != "":
                # For relationships, include basic info
                if isinstance(value, Identity):
                    result[field_name] = {
                        "@id": str(value.identifier),
                        "@type": value.__class__.__name__
                    }
                    # Include name if available
                    if hasattr(value, 'name') and value.name:
                        result[field_name]["name"] = str(value.name)
                
                elif isinstance(value, list) and value and isinstance(value[0], Identity):
                    result[field_name] = [
                        {
                            "@id": str(item.identifier),
                            "@type": item.__class__.__name__,
                            **({"name": str(item.name)} if hasattr(item, 'name') and item.name else {})
                        }
                        for item in value
                    ]
                else:
                    result[field_name] = self._serialize_value(value)
        
        return result
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON output."""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif hasattr(value, 'value'):  # Handle enums and CIMUnit
            return str(value.value)
        else:
            return str(value)


# Convenience functions for common use cases
def create_template(root_type: type, **kwargs) -> GraphQLTemplate:
    """
    Create a GraphQL template with builder pattern.
    
    Args:
        root_type: The root class type to query
        **kwargs: Additional template parameters
    
    Returns:
        GraphQLTemplate instance
    """
    return GraphQLTemplate(root_type=root_type, **kwargs)

def template_builder(root_type: type) -> 'TemplateBuilder':
    """Create a template builder for fluent API."""
    return TemplateBuilder(root_type)

class TemplateBuilder:
    """Fluent API for building GraphQL templates."""
    
    def __init__(self, root_type: type):
        self._root_type = root_type
        self._fields = {}
        self._filter = None
        self._limit = None
    
    def field(self, name: str, include: bool = True) -> 'TemplateBuilder':
        """Include or exclude a simple field."""
        self._fields[name] = include
        return self
    
    def nested(self, name: str, template: GraphQLTemplate) -> 'TemplateBuilder':
        """Include a nested field with its own template."""
        self._fields[name] = template
        return self
    
    def filter(self, **criteria) -> 'TemplateBuilder':
        """Add filter criteria."""
        self._filter = criteria
        return self
    
    def limit(self, count: int) -> 'TemplateBuilder':
        """Limit number of results."""
        self._limit = count
        return self
    
    def build(self) -> GraphQLTemplate:
        """Build the final template."""
        return GraphQLTemplate(
            root_type=self._root_type,
            fields=self._fields,
            root_filter=self._filter,
            limit=self._limit
        )

# Corrected usage example
def example_usage(graph_model_instance):
    """
    Example of how to use the GraphQL templater.
    
    Args:
        graph_model_instance: An actual instance of GraphModel (not the class)
    """
    # You need to import your actual CIM classes
    # For example purposes, I'll use placeholder names
    # try:
        # Try to get CIM classes from the graph model
        # cim = graph_model_instance.cim
        # PowerTransformer = cim.PowerTransformer
        # PowerTransformerEnd = getattr(cim, 'PowerTransformerEnd', None)
        
        # if not PowerTransformer or not PowerTransformerEnd:
        #     print("PowerTransformer or PowerTransformerEnd classes not found in CIM profile")
        #     return "{}"
        
    # except AttributeError:
    #     print("Could not access CIM classes from graph model")
    #     return "{}"
    
    # Example 1: Simple template for PowerTransformer with PowerTransformerEnds
    power_transformer_end_template = create_template(
        root_type=cim.PowerTransformerEnd,
        fields={
            "name": True,
            "endNumber": True,
            "grounded": True,
            "rground": True,
            "xground": True,
            "connectionKind": True,
            "phaseAngleClock": True,
            "r": True,
            "x": True,
            "b": True,
            "ratedS": True,
            "ratedU": True
        }
    )
    
    transformer_template = create_template(
        root_type=cim.PowerTransformer,
        fields={
            "name": True,
            "vectorGroup": True,
            "PowerTransformerEnd": power_transformer_end_template
        },
        root_filter={"name": "hvmv69_12"}  # Filter for specific transformer
    )
    
    # Execute query with the INSTANCE, not the class
    templater = GraphQLTemplater(graph_model_instance)
    result = templater.query(transformer_template)
    
    # Example 2: Using fluent API
    template = (template_builder(cim.PowerTransformer)
                .field("name")
                .field("vectorGroup") 
                .nested("PowerTransformerEnd", 
                       template_builder(cim.PowerTransformerEnd)
                       .field("name")
                       .field("endNumber")
                       .field("grounded")
                       .build())
                .filter(name="hvmv69_12")
                .build())
    
    result = templater.query(template)
    
    return json.dumps(result, indent=2)

# Proper usage pattern:
def how_to_use():
    """
    Shows the correct way to use the templater
    """
    print("""
    # Correct usage:
    
    # 1. Create a GraphModel INSTANCE (not class)
    container = YourContainer()  # Your CIM container
    connection = YourConnection()  # Your database connection
    graph_model = GraphModel(container=container, connection=connection)
    
    # 2. Populate the graph with data
    # ... add objects to graph_model ...
    
    # 3. Create and use templater
    templater = GraphQLTemplater(graph_model)  # Pass INSTANCE
    
    # 4. Define template and query
    template = create_template(
        root_type=YourCIMClass,
        fields={"name": True, "other_field": True}
    )
    
    result = templater.query(template)
    print(json.dumps(result, indent=2))
    """)