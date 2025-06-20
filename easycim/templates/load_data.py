from __future__ import annotations
import importlib
import logging
from typing import Dict, Optional, Union, List
from pathlib import Path
from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim.shacl import SHACLDataExporter
import cimgraph.data_profile.cimhub_ufls as cim

_log = logging.getLogger(__name__)

def get_load_data(network: GraphModel,
                 shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_load_data
    
    Returns a dictionary of single-phase and three-phase load data 
    sorted by the overall load object.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for load export
    :return: Dictionary of load data
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_load_shapes_file()
    
    # Create SHACL data exporter
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required load data
    _ensure_load_data_loaded(network, cim)
    
    load_data = {}
    
    # Process all load types using polymorphic export
    load_classes = [cim.EnergyConsumer, cim.ConformLoad, cim.NonConformLoad]
    
    for load_class in load_classes:
        if load_class in network.graph:
            for load in network.graph[load_class].values():
                # Use polymorphic shape that handles all load types
                load_export_data = exporter.export_object_data(load, 'LoadPolymorphicExport')
                load_data[str(load.mRID)] = load_export_data
    
    return load_data

def load_iterator(energy_consumer,
                 shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of load_iterator
    
    Iterator method to extract phase data for an EnergyConsumer object
    
    :param energy_consumer: An instance of EnergyConsumer or any of its child classes
    :param shacl_shapes_file: Path to SHACL shapes file for load export
    :return: EnergyConsumer dictionary with phase data
    """
    
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_load_shapes_file()
    
    # Get CIM module from the energy_consumer object
    cim_module = importlib.import_module(energy_consumer.__module__.split('.')[0] + 
                                       '.data_profile.' + 
                                       energy_consumer.__module__.split('.')[-1])
    
    exporter = SHACLDataExporter(shacl_shapes_file, cim_module)
    
    # Determine the correct shape based on the object type
    class_name = energy_consumer.__class__.__name__
    shape_name = f"{class_name}Export"
    
    # Fallback to polymorphic shape if specific shape not found
    if shape_name not in exporter.processor.catalog_shapes:
        shape_name = 'LoadPolymorphicExport'
    
    return exporter.export_object_data(energy_consumer, shape_name)

def _ensure_load_data_loaded(network: GraphModel, cim: cim) -> None:
    """Ensure all required load data is loaded into the graph"""
    required_classes = [
        cim.EnergyConsumer,
        cim.EnergyConsumerPhase
    ]
    
    # Optional classes that may not exist in all profiles
    optional_classes = [
        ('ConformLoad', cim.ConformLoad if hasattr(cim, 'ConformLoad') else None),
        ('NonConformLoad', cim.NonConformLoad if hasattr(cim, 'NonConformLoad') else None),
        ('House', cim.House if hasattr(cim, 'House') else None),
        ('LoadResponseCharacteristic', cim.LoadResponseCharacteristic if hasattr(cim, 'LoadResponseCharacteristic') else None),
        ('LoadGroup', cim.LoadGroup if hasattr(cim, 'LoadGroup') else None)
    ]
    
    # Load required classes
    for cim_class in required_classes:
        try:
            network.get_all_edges(cim_class)
        except Exception as e:
            _log.debug(f"Could not load {cim_class.__name__}: {e}")
    
    # Load optional classes
    for class_name, cim_class in optional_classes:
        if cim_class is not None:
            try:
                network.get_all_edges(cim_class)
                _log.debug(f"Loaded optional class {class_name}")
            except Exception as e:
                _log.debug(f"Optional class {class_name} not available: {e}")

def _get_load_shapes_file() -> str:
    """Get default SHACL shapes file path for load export"""
    import os
    package_dir = os.path.dirname(__file__)
    return os.path.join(package_dir, 'shacl', 'load_data_shapes.ttl')

# ===== CONVENIENCE EXPORT FUNCTIONS =====

def export_load_data(network: GraphModel,
                    output_file: Union[str, Path],
                    format: str = 'json',
                    shacl_shapes_file: str = None,
                    include_phases: bool = True,
                    include_house_data: bool = True) -> None:
    """Export load data to file with options"""
    
    load_data = get_load_data(network, shacl_shapes_file)
    
    # Optional filtering
    if not include_phases:
        for load_id, load_info in load_data.items():
            if 'phases' in load_info:
                del load_info['phases']
    
    if not include_house_data:
        for load_id, load_info in load_data.items():
            if 'House' in load_info:
                del load_info['House']
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(load_data, output_file)
    elif format.lower() == 'csv':
        EquipmentDataWriter.write_csv(load_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(load_data, output_file, 'Load Data')
    else:
        raise ValueError(f"Unsupported format: {format}")

def get_load_summary(network: GraphModel,
                    shacl_shapes_file: str = None) -> Dict:
    """Get summary statistics of load data"""
    
    load_data = get_load_data(network, shacl_shapes_file)
    
    summary = {
        'total_loads': len(load_data),
        'load_types': {},
        'total_p': 0.0,
        'total_q': 0.0,
        'phase_count': {'single': 0, 'three': 0},
        'with_house_data': 0
    }
    
    for load_id, load_info in load_data.items():
        # Count by type
        load_type = load_info.get('@type', 'Unknown')
        summary['load_types'][load_type] = summary['load_types'].get(load_type, 0) + 1
        
        # Sum power
        if 'p' in load_info and load_info['p'] is not None:
            try:
                summary['total_p'] += float(load_info['p'])
            except:
                pass
        
        if 'q' in load_info and load_info['q'] is not None:
            try:
                summary['total_q'] += float(load_info['q'])
            except:
                pass
        
        # Count phases
        phases = load_info.get('phases', [])
        if len(phases) == 1:
            summary['phase_count']['single'] += 1
        elif len(phases) >= 3:
            summary['phase_count']['three'] += 1
        
        # Count house data
        if 'House' in load_info and load_info['House']:
            summary['with_house_data'] += 1
    
    return summary

def get_loads_by_type(network: GraphModel,
                     load_type: str,
                     shacl_shapes_file: str = None) -> Dict:
    """Get only loads of a specific type"""
    
    load_data = get_load_data(network, shacl_shapes_file)
    
    filtered_data = {
        load_id: load_info 
        for load_id, load_info in load_data.items()
        if load_info.get('@type', '').endswith(load_type)
    }
    
    return filtered_data