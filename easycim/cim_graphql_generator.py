from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Optional
import importlib
import enum

from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim.graphql_example import AutoGraphQLGenerator

_log = logging.getLogger(__name__)


class CIMGraphQLGenerator(AutoGraphQLGenerator):
    """
    CIM-specific GraphQL generator that extends AutoGraphQLGenerator
    to work with CIM objects and GraphModel instances.
    Pure GraphQL approach without dependency on ReducedDataProfile.
    """
    
    def __init__(self):
        super().__init__()
        self.schemas_path = Path(__file__).parent / "schemas"
    
    def load_schema(self, class_name: str) -> dict:
        """Load JSON schema for a CIM class"""
        schema_file = self.schemas_path / f"{self.camel_to_snake(class_name)}_schema.json"
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    def extract_cim_object_data(self, cim_obj: object, class_name: str) -> dict:
        """
        Extract data from a CIM object using schema-driven approach.
        This method uses the JSON schema to determine what data to extract.
        """
        try:
            schema = self.load_schema(class_name)
            return self._extract_data_from_schema(cim_obj, schema)
        except FileNotFoundError:
            _log.warning(f"No schema found for {class_name}, using basic extraction")
            return self._extract_basic_data(cim_obj, class_name)
        except Exception as e:
            _log.error(f"Error extracting data for {class_name}: {str(e)}")
            return self._extract_basic_data(cim_obj, class_name)
    
    def _extract_data_from_schema(self, cim_obj: object, schema: dict) -> dict:
        """
        Generic schema-driven data extraction method.
        Traverses the JSON schema and extracts corresponding data from the CIM object.
        """
        catalog_schema = schema.get('properties', {}).get('catalog', {}).get('properties', {})
        catalog_data = {}
        
        for field_name, field_schema in catalog_schema.items():
            if field_name == '@type':
                # Set the type from the schema constant
                catalog_data['@type'] = field_schema.get('const', cim_obj.__class__.__name__)
            elif field_schema.get('type') == 'array':
                # Handle array fields (like PowerTransformerEnd, phases, etc.)
                catalog_data[field_name] = self._extract_array_field(cim_obj, field_name, field_schema)
            elif field_schema.get('type') == 'object':
                # Handle nested object fields (like House, PerLengthImpedance, etc.)
                catalog_data[field_name] = self._extract_object_field(cim_obj, field_name, field_schema)
            else:
                # Handle simple fields (string, number, etc.)
                catalog_data[field_name] = self._extract_simple_field(cim_obj, field_name)
        
        return {"catalog": catalog_data}
    
    def _extract_simple_field(self, cim_obj: object, field_name: str) -> str:
        """Extract a simple field value from a CIM object"""
        value = getattr(cim_obj, field_name, '')
        
        # Handle enum values
        if hasattr(value, '__class__') and type(value.__class__) is enum.EnumMeta:
            return str(value.value)
        elif value is None:
            return ''
        else:
            return str(value)
    
    def _extract_array_field(self, cim_obj: object, field_name: str, field_schema: dict) -> list:
        """Extract an array field from a CIM object"""
        result = []
        
        # Map common field name variations
        field_variations = [
            field_name,
            field_name.rstrip('s'),  # Remove trailing 's' (e.g., phases -> phase)
            field_name + 's',        # Add trailing 's'
        ]
        
        # Try different attribute names that might contain the array data
        array_data = None
        for variation in field_variations:
            if hasattr(cim_obj, variation):
                array_data = getattr(cim_obj, variation)
                break
        
        if array_data and hasattr(array_data, '__iter__'):
            item_schema = field_schema.get('items', {}).get('properties', {})
            for item in array_data:
                item_data = {}
                for item_field, item_field_schema in item_schema.items():
                    if item_field == '@type':
                        item_data['@type'] = item_field_schema.get('const', item.__class__.__name__)
                    else:
                        item_data[item_field] = self._extract_simple_field(item, item_field)
                result.append(item_data)
        
        return result
    
    def _extract_object_field(self, cim_obj: object, field_name: str, field_schema: dict) -> dict:
        """Extract a nested object field from a CIM object"""
        nested_obj = getattr(cim_obj, field_name, None)
        if nested_obj is None:
            return {}
        
        result = {}
        object_properties = field_schema.get('properties', {})
        
        for prop_name, prop_schema in object_properties.items():
            if prop_name == '@type':
                result['@type'] = prop_schema.get('const', nested_obj.__class__.__name__)
            else:
                result[prop_name] = self._extract_simple_field(nested_obj, prop_name)
        
        return result
    
    
    def _extract_basic_data(self, cim_obj: object, class_name: str) -> dict:
        """Basic data extraction for unsupported classes"""
        return {
            "catalog": {
                "@type": class_name,
                "name": getattr(cim_obj, 'name', ''),
                "mRID": getattr(cim_obj, 'mRID', ''),
                "data": "Basic extraction - schema not implemented"
            }
        }
    
    def generate_cim_data(self, network: GraphModel, class_name: str) -> dict:
        """
        Generate structured data for all objects of a given CIM class
        using GraphQL-style processing.
        """
        try:
            # Load the schema for this class
            schema = self.load_schema(class_name)
            
            # Get CIM profile using the new approach
            cim_profile, cim_module = get_cim_profile()
            cim = cim_module
            
            # Get the CIM class
            cim_class = getattr(cim, class_name)
            
            # Ensure we have the data in the network
            network.get_all_edges(cim_class)
            
            # Extract data for all objects of this class
            result_data = {}
            if cim_class in network.graph:
                for obj_id, cim_obj in network.graph[cim_class].items():
                    extracted_data = self.extract_cim_object_data(cim_obj, class_name)
                    result_data[obj_id] = extracted_data
            
            return result_data
            
        except Exception as e:
            _log.error(f"Error generating data for {class_name}: {str(e)}")
            return {}
    
    def create_graphql_query_for_class(self, class_name: str) -> str:
        """
        Create a GraphQL query string for a CIM class based on its schema.
        """
        try:
            schema = self.load_schema(class_name)
            query_schema = schema.get('properties', {}).get('catalog', {})
            return self.generate_graphql_query_from_schema(query_schema)
        except Exception as e:
            _log.error(f"Error creating GraphQL query for {class_name}: {str(e)}")
            return ""
