import graphene
import json
from jsonschema import RefResolver
from graphene import ObjectType, String, List, Field, Int, Float, Boolean, JSONString
from typing import Dict, Any, Union, Optional
import re
from rich import print
from pydantic import BaseModel

class AutoGraphQLGenerator:
    def __init__(self):
        self.type_registry = {}
        
    def snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    def camel_to_snake(self, camel_str: str) -> str:
        """Convert camelCase to snake_case"""
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str).lower()
        
    def json_type_to_graphql_type(self, json_schema: Union[str, dict], field_name: str = None):
        """Convert JSON schema type to GraphQL type"""
        if isinstance(json_schema, dict):
            if json_schema.get('type') == 'object':
                type_name = json_schema.get('title', field_name or 'GeneratedType')
                return self.create_object_type_from_schema(json_schema, type_name)
            elif json_schema.get('type') == 'array':
                items_type = self.json_type_to_graphql_type(json_schema.get('items', {}), f"{field_name}Item")
                return List(items_type)
            elif json_schema.get('type') == 'string':
                return String
            elif json_schema.get('type') == 'integer':
                return Int
            elif json_schema.get('type') == 'number':
                return Float
            elif json_schema.get('type') == 'boolean':
                return Boolean
        elif isinstance(json_schema, str):
            type_mapping = {
                'string': String,
                'integer': Int,
                'number': Float,
                'boolean': Boolean,
            }
            return type_mapping.get(json_schema, JSONString)
        
        return JSONString
    
    def create_object_type_from_schema(self, schema: dict, type_name: str):
        """Create a GraphQL ObjectType from JSON schema"""
        if type_name in self.type_registry:
            return self.type_registry[type_name]
        
        properties = schema.get('properties', {})
        attrs = {}
        
        for field_name, field_schema in properties.items():
            graphql_type = self.json_type_to_graphql_type(field_schema, field_name)
            
            # Create a custom field with resolver that handles snake_case to camelCase conversion
            def create_field_resolver(original_field_name):
                def resolver(self, info):
                    # Convert GraphQL field name back to original JSON field name
                    if hasattr(self, original_field_name):
                        return getattr(self, original_field_name)
                    elif isinstance(self, dict):
                        return self.get(original_field_name)
                    return None
                return resolver
            
            # Use camelCase for GraphQL field name
            graphql_field_name = self.snake_to_camel(field_name)
            
            # Create field with custom resolver
            if graphql_field_name != field_name:
                # Field that needs name conversion
                field_with_resolver = Field(graphql_type, resolver=create_field_resolver(field_name))
                attrs[graphql_field_name] = field_with_resolver
            else:
                # Field that doesn't need conversion
                attrs[field_name] = Field(graphql_type)
        
        # Create the type dynamically
        generated_type = type(type_name, (ObjectType,), attrs)
        self.type_registry[type_name] = generated_type
        
        return generated_type
    
    def create_resolver(self, field_name: str, field_schema: dict, big_json_data: dict):
        """Create a resolver function for a field"""
        def resolver(self, info, **args):
            data = big_json_data.get(field_name)
            
            # Handle filtering by arguments
            if args and data:
                if isinstance(data, list):
                    # Handle common filtering arguments
                    if 'id' in args:
                        data = next((item for item in data if item.get('id') == args['id']), None)
                    elif 'filter' in args:
                        # Add custom filtering logic here
                        pass
                elif isinstance(data, dict):
                    # Handle object filtering if needed
                    pass
            
            return data
        
        return resolver
    
    def generate_graphql_query_from_schema(self, query_schema: dict, max_depth: int = 3, current_depth: int = 0) -> str:
        """Generate GraphQL query string from query schema"""
        if current_depth >= max_depth:
            return ""
        
        query_parts = []
        properties = query_schema.get('properties', {})
        
        for field_name, field_schema in properties.items():
            # Convert field name to camelCase for GraphQL
            graphql_field_name = self.snake_to_camel(field_name)
            field_query = graphql_field_name
            
            # Add arguments if specified
            if 'arguments' in field_schema:
                args = []
                for arg_name, arg_schema in field_schema['arguments'].items():
                    # Generate sample argument values based on type
                    if arg_schema.get('type') == 'integer':
                        args.append(f'{arg_name}: 1')
                    elif arg_schema.get('type') == 'string':
                        args.append(f'{arg_name}: "sample"')
                    elif arg_schema.get('type') == 'boolean':
                        args.append(f'{arg_name}: true')
                
                if args:
                    field_query += f"({', '.join(args)})"
            
            # Handle nested fields
            if field_schema.get('type') == 'object':
                nested_query = self.generate_graphql_query_from_schema(field_schema, max_depth, current_depth + 1)
                if nested_query:
                    field_query += f" {{\n{self._indent(nested_query, current_depth + 2)}\n{self._indent('', current_depth + 1)}}}"
            elif field_schema.get('type') == 'array' and 'items' in field_schema:
                items_schema = field_schema['items']
                if items_schema.get('type') == 'object':
                    nested_query = self.generate_graphql_query_from_schema(items_schema, max_depth, current_depth + 1)
                    if nested_query:
                        field_query += f" {{\n{self._indent(nested_query, current_depth + 2)}\n{self._indent('', current_depth + 1)}}}"
            
            query_parts.append(field_query)
        
        return '\n'.join(f"{self._indent('', current_depth)}{part}" for part in query_parts)
    
    def _indent(self, text: str, level: int) -> str:
        """Add indentation to text"""
        if not text.strip():
            return "    " * level
        lines = text.split('\n')
        return '\n'.join("    " * level + line for line in lines)
    
    def execute_query_and_get_result(self, query_schema: dict, big_json_data: dict) -> dict:
        """Generate schema, query, and execute to return result object"""
        
        # Create Query type
        query_attrs = {}
        resolvers = {}
        
        query_properties = query_schema.get('properties', {})
        
        for field_name, field_schema in query_properties.items():
            graphql_type = self.json_type_to_graphql_type(field_schema, field_name)
            
            # Handle arguments
            field_args = {}
            if 'arguments' in field_schema:
                for arg_name, arg_schema in field_schema['arguments'].items():
                    arg_type = self.json_type_to_graphql_type(arg_schema)
                    if arg_schema.get('required', False):
                        field_args[arg_name] = arg_type(required=True)
                    else:
                        field_args[arg_name] = arg_type()
            
            # Convert field name to camelCase for GraphQL
            graphql_field_name = self.snake_to_camel(field_name)
            
            # Add field to query
            if field_args:
                query_attrs[graphql_field_name] = Field(graphql_type, **field_args)
            else:
                query_attrs[graphql_field_name] = Field(graphql_type)
            
            # Create resolver
            resolver_func = self.create_resolver(field_name, field_schema, big_json_data)
            resolvers[f'resolve_{graphql_field_name}'] = resolver_func
        
        # Create Query class dynamically
        query_attrs.update(resolvers)
        QueryType = type('Query', (ObjectType,), query_attrs)
        
        # Create schema
        schema = graphene.Schema(query=QueryType)
        
        # Generate query string (using camelCase field names)
        query_string = "{\n" + self.generate_graphql_query_from_schema(query_schema, max_depth=3) + "\n}"
        print("Generated GraphQL Query:")
        print(query_string)
        print("\n" + "="*50 + "\n")
        
        # Execute query
        result = schema.execute(query_string)
        
        if result.errors:
            return {"errors": [str(error) for error in result.errors]}
        
        return result.data
    
def resolve_schema_with_jsonschema(schema):
    """Resolve all $ref using jsonschema library"""
    
    # Create a resolver
    resolver = RefResolver.from_schema(schema)
    
    def resolve_refs_recursive(obj):
        if isinstance(obj, dict):
            if '$ref' in obj:
                # Resolve the reference
                url, resolved = resolver.resolve(obj['$ref'])
                return resolve_refs_recursive(resolved)
            else:
                return {k: resolve_refs_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs_recursive(item) for item in obj]
        else:
            return obj
    
    # Create a copy and resolve
    resolved = resolve_refs_recursive(schema)
    
    # Remove definitions
    if '$defs' in resolved:
        del resolved['$defs']
    if 'definitions' in resolved:
        del resolved['definitions']
        
    return resolved

def demo():
    # Query schema (resolved, no refs)
    query_schema = {
        "type": "object",
        "properties": {
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        # "posts": {
                        #     "type": "array",
                        #     "items": {
                        #         "type": "object",
                        #         "properties": {
                        #             "id": {"type": "integer"},
                        #             "title": {"type": "string"},
                        #             "likes": {"type": "integer"}
                        #         }
                        #     }
                        # },
                        "profile": {
                            "type": "object",
                            "properties": {
                                # "age": {"type": "integer"},
                                "city": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "arguments": {
                    "id": {"type": "integer", "required": True,}
                }
            },
            "stats": {
                "type": "object",
                "properties": {
                    "total_users": {"type": "integer"},
                    "total_posts": {"type": "integer"}
                }
            }
        }
    }

    class Profile(BaseModel):
        age: Optional[int] = None

    class UserItem(BaseModel):
        id: int
        name: str
        email: str
        profile: Profile

    class MyModel(BaseModel):
        users: list[UserItem]
    
    # Big JSON data (with snake_case field names)
    big_json_data = {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "posts": [
                    {"id": 101, "title": "GraphQL is awesome", "likes": 25},
                    {"id": 102, "title": "JSON querying made easy", "likes": 15}
                ],
                "profile": {"age": 30, "city": "New York"}
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "posts": [
                    {"id": 201, "title": "Python tips and tricks", "likes": 40}
                ],
                "profile": {"age": 25, "city": "London"}
            }
        ],
        "stats": {
            "total_users": 2,
            "total_posts": 3
        }
    }
    
    # Generate and execute
    generator = AutoGraphQLGenerator()
    schema = resolve_schema_with_jsonschema(MyModel.model_json_schema())
    result = generator.execute_query_and_get_result(query_schema, big_json_data)
    
    print("Query Result Object:")
    print(resolve_schema_with_jsonschema(MyModel.model_json_schema()))
    print(json.dumps(result, indent=2))
    # print(MyModel.model_validate(result))

if __name__ == "__main__":
    demo()