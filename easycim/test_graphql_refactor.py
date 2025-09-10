#!/usr/bin/env python3
"""
Test script to demonstrate the new GraphQL-based data extraction
compared to the legacy hard-coded approach.
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

def test_schema_loading():
    """Test that schemas can be loaded correctly"""
    from easycim.cim_graphql_generator import CIMGraphQLGenerator
    
    generator = CIMGraphQLGenerator()
    
    # Test loading each schema
    test_classes = ['PowerTransformer', 'ACLineSegment', 'EnergyConsumer']
    
    for class_name in test_classes:
        try:
            schema = generator.load_schema(class_name)
            _log.info(f"✓ Successfully loaded schema for {class_name}")
            _log.info(f"  Schema has {len(schema.get('properties', {}).get('catalog', {}).get('properties', {}))} top-level properties")
        except Exception as e:
            _log.error(f"✗ Failed to load schema for {class_name}: {str(e)}")

def test_graphql_query_generation():
    """Test GraphQL query generation from schemas"""
    from easycim.cim_graphql_generator import CIMGraphQLGenerator
    
    generator = CIMGraphQLGenerator()
    
    test_classes = ['PowerTransformer', 'ACLineSegment', 'EnergyConsumer']
    
    for class_name in test_classes:
        try:
            query = generator.create_graphql_query_for_class(class_name)
            _log.info(f"✓ Generated GraphQL query for {class_name}")
            _log.info(f"  Query preview: {query[:100]}...")
        except Exception as e:
            _log.error(f"✗ Failed to generate query for {class_name}: {str(e)}")

def test_mock_data_extraction():
    """Test data extraction with mock CIM objects"""
    from easycim.cim_graphql_generator import CIMGraphQLGenerator
    
    generator = CIMGraphQLGenerator()
    
    # Create a mock PowerTransformer object
    class MockPowerTransformerEnd:
        def __init__(self):
            self.name = "hvmv69_12_End_1"
            self.mRID = "end_1_mrid"
            self.endNumber = 1
            self.grounded = True
            self.rground = 0.0
            self.xground = 0.0
            self.connectionKind = "WindingConnection.Y"
            self.phaseAngleClock = 0
            self.r = 1.594935
            self.x = 18.90117
            self.b = 0.0
            self.ratedS = 20000000
            self.ratedU = 69000
    
    class MockPowerTransformer:
        def __init__(self):
            self.name = "hvmv69_12"
            self.mRID = "transformer_mrid"
            self.vectorGroup = "Yy"
            self.PowerTransformerEnd = [MockPowerTransformerEnd()]
    
    # Test extraction
    mock_transformer = MockPowerTransformer()
    extracted_data = generator.extract_cim_object_data(mock_transformer, 'PowerTransformer')
    
    _log.info("✓ Successfully extracted mock PowerTransformer data")
    _log.info(f"  Extracted data structure: {json.dumps(extracted_data, indent=2)}")
    
    # Verify the structure matches the target format
    catalog = extracted_data.get('catalog', {})
    if catalog.get('@type') == 'PowerTransformer' and 'PowerTransformerEnd' in catalog:
        _log.info("✓ Data structure matches target format")
    else:
        _log.error("✗ Data structure does not match target format")

def test_comparison_with_target():
    """Compare generated structure with target hv69_12.json"""
    from easycim.cim_graphql_generator import CIMGraphQLGenerator
    
    # Load target format
    target_file = Path(__file__).parent / "catalog" / "hv69_12.json"
    if target_file.exists():
        with open(target_file, 'r') as f:
            target_data = json.load(f)
        
        _log.info("✓ Loaded target format from hv69_12.json")
        
        # Compare structure
        target_catalog = target_data.get('catalog', {})
        target_keys = set(target_catalog.keys())
        
        _log.info(f"  Target has keys: {sorted(target_keys)}")
        
        # Check if our schema covers the same keys
        generator = CIMGraphQLGenerator()
        schema = generator.load_schema('PowerTransformer')
        schema_catalog = schema.get('properties', {}).get('catalog', {}).get('properties', {})
        schema_keys = set(schema_catalog.keys())
        
        _log.info(f"  Schema has keys: {sorted(schema_keys)}")
        
        missing_keys = target_keys - schema_keys
        extra_keys = schema_keys - target_keys
        
        if missing_keys:
            _log.warning(f"  Missing keys in schema: {sorted(missing_keys)}")
        if extra_keys:
            _log.info(f"  Extra keys in schema: {sorted(extra_keys)}")
        if not missing_keys and not extra_keys:
            _log.info("✓ Schema keys match target format perfectly")
    else:
        _log.error("✗ Target file hv69_12.json not found")

def main():
    """Run all tests"""
    _log.info("Starting GraphQL refactor tests...")
    _log.info("=" * 50)
    
    test_schema_loading()
    _log.info("-" * 30)
    
    test_graphql_query_generation()
    _log.info("-" * 30)
    
    test_mock_data_extraction()
    _log.info("-" * 30)
    
    test_comparison_with_target()
    _log.info("=" * 50)
    _log.info("GraphQL refactor tests completed!")

if __name__ == "__main__":
    main()
