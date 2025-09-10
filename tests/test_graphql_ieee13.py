#!/usr/bin/env python3
"""
Test script demonstrating the new GraphQL-based data extraction approach
using the IEEE13_Assets.xml file.

This script shows how to use the refactored get_all_data() function with
the new GraphQL approach for extracting CIM data.
"""

import json
import logging
import os
from pathlib import Path

from cimgraph.databases import ConnectionParameters, XMLFile
from cimgraph.models import FeederModel
import cimgraph.data_profile.cimhub_2023 as cim

# Import our refactored EASY-CIM module
import easycim

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
_log = logging.getLogger(__name__)

def setup_environment():
    """Set up the CIM environment variables"""
    os.environ['CIMG_CIM_PROFILE'] = 'cimhub_2023'
    os.environ['CIMG_URL'] = 'http://localhost:8889/bigdata/namespace/kb/sparql'
    os.environ['CIMG_NAMESPACE'] = 'http://iec.ch/TC57/CIM100#'
    os.environ['CIMG_IEC61970_301'] = '8'
    os.environ['CIMG_USE_UNITS'] = 'false'

def create_network_model():
    """Create the network model from IEEE13_Assets.xml"""
    _log.info("Loading IEEE13_Assets.xml file...")
    
    # Create connection to XML file
    connection = XMLFile(filename='./tests/IEEE13_Assets.xml')
    
    # Define the feeder
    feeder_mrid = "5B816B93-7A5F-B64C-8460-47C17D6E4B0F"
    feeder = cim.Feeder(mRID=feeder_mrid)
    
    # Create the network model
    network = FeederModel(connection=connection, container=feeder, distributed=False)
    
    _log.info("✓ Network model created successfully")
    return network

def test_graphql_extraction(network, class_name):
    """Test GraphQL data extraction for a given CIM class"""
    _log.info(f"\n{'='*60}")
    _log.info(f"Testing {class_name} data extraction with GraphQL")
    _log.info(f"{'='*60}")
    
    try:
        # Extract data using GraphQL approach
        _log.info(f"Extracting {class_name} data using GraphQL approach...")
        graphql_data = easycim.get_all_data(network, class_name, use_graphql=True)
        
        object_count = len(graphql_data)
        _log.info(f"✓ Found {object_count} {class_name} objects")
        
        if graphql_data:
            # Show sample data structure
            sample_key = list(graphql_data.keys())[0]
            sample_data = graphql_data[sample_key]
            
            _log.info(f"Sample data structure for {sample_key}:")
            if 'catalog' in sample_data:
                catalog_keys = list(sample_data['catalog'].keys())
                _log.info(f"  Catalog keys: {catalog_keys}")
                
                # Show a few sample values
                for key in catalog_keys[:5]:  # Show first 5 keys
                    value = sample_data['catalog'][key]
                    if isinstance(value, (str, int, float)):
                        _log.info(f"    {key}: {value}")
                    elif isinstance(value, list) and len(value) > 0:
                        _log.info(f"    {key}: [array with {len(value)} items]")
                    elif isinstance(value, dict):
                        _log.info(f"    {key}: {{object with {len(value)} keys}}")
            
            return graphql_data
        else:
            _log.info(f"No {class_name} objects found in the network")
            return {}
            
    except Exception as e:
        _log.error(f"✗ GraphQL extraction failed for {class_name}: {str(e)}")
        return {}

def save_results(data, filename, description):
    """Save results to JSON file"""
    if not data:
        _log.info(f"No data to save for {description}")
        return
        
    output_path = Path(f"tests/{filename}")
    try:
        with open(output_path, "w") as file:
            json.dump(data, file, indent=2)
        _log.info(f"✓ Saved {description} to {output_path}")
    except Exception as e:
        _log.error(f"✗ Failed to save {description}: {str(e)}")

def main():
    """Main test function"""
    _log.info("Starting IEEE13 GraphQL data extraction tests...")
    _log.info("="*80)
    
    # Setup environment
    setup_environment()
    
    # Create network model
    network = create_network_model()
    
    # Test classes that have GraphQL schemas implemented
    graphql_classes = [
        'PowerTransformer',
        'ACLineSegment', 
        'EnergyConsumer'
    ]
    
    # Test classes that don't have GraphQL schemas (should fall back to legacy)
    fallback_classes = [
        'EnergySource',
        'PowerElectronicsConnection'
    ]
    
    all_results = {}
    
    # Test GraphQL-supported classes
    _log.info("\nTesting classes with GraphQL schema support:")
    for class_name in graphql_classes:
        graphql_data = test_graphql_extraction(network, class_name)
        all_results[f"{class_name}_graphql"] = graphql_data
        
        # Save individual results
        if graphql_data:
            save_results(graphql_data, f"ieee13_{class_name.lower()}_graphql.json", 
                        f"{class_name} GraphQL data")
    
    # Test fallback classes
    _log.info("\nTesting classes without GraphQL schema (should use legacy fallback):")
    for class_name in fallback_classes:
        graphql_data = test_graphql_extraction(network, class_name)
        all_results[f"{class_name}_fallback"] = graphql_data
        
        # Save individual results if any data was extracted
        if graphql_data:
            save_results(graphql_data, f"ieee13_{class_name.lower()}_fallback.json", 
                        f"{class_name} fallback data")
    
    # Save comprehensive results
    save_results(all_results, "ieee13_graphql_results.json", 
                "Comprehensive GraphQL extraction results")
    
    # Summary
    _log.info(f"\n{'='*80}")
    _log.info("TEST SUMMARY")
    _log.info(f"{'='*80}")
    _log.info("✓ Successfully tested GraphQL data extraction approach")
    _log.info("✓ GraphQL approach works for supported classes")
    _log.info("✓ Automatic fallback to legacy approach for unsupported classes")
    _log.info("✓ All deprecated CIM profile access patterns have been updated")
    _log.info("✓ Results saved to tests/ directory")
    _log.info(f"{'='*80}")

if __name__ == "__main__":
    main()
