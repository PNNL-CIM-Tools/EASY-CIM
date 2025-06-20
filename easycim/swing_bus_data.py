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

def get_swing_bus_data(network: GraphModel,
                      shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_swing_bus_data
    
    Returns a dictionary of single-phase and three-phase source data 
    sorted by the overall source object.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for source export
    :return: Dictionary of source data
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_source_shapes_file()
    
    # Create SHACL data exporter
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required source data
    _ensure_source_data_loaded(network, cim)
    
    source_data = {}
    
    if cim.EnergySource in network.graph:
        for source in network.graph[cim.EnergySource].values():
            # Export source data using SHACL shape
            source_export_data = exporter.export_object_data(source, 'EnergySourceExport')
            source_data[str(source.mRID)] = source_export_data
    
    return source_data

def source_iterator(energy_source,
                   shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of source_iterator
    
    Iterator method to extract phase data for an EnergySource object
    
    :param energy_source: An instance of EnergySource or any of its child classes
    :param shacl_shapes_file: Path to SHACL shapes file for source export
    :return: EnergySource dictionary with phase data
    """
    
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_source_shapes_file()
    
    # Get CIM module from the energy_source object
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    return exporter.export_object_data(energy_source, 'EnergySourceExport')

def get_all_source_data(network: GraphModel,
                       shacl_shapes_file: str = None) -> dict:
    """
    Get all types of sources including EnergySource, EquivalentInjection, etc.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for source export
    :return: Dictionary of all source data by type
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_source_shapes_file()
    
    # Create SHACL data exporter
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required source data
    _ensure_source_data_loaded(network, cim)
    
    all_source_data = {
        'EnergySource': {},
        'EquivalentInjection': {},
        'ExternalNetworkInjection': {}
    }
    
    # Export EnergySource
    if cim.EnergySource in network.graph:
        for source in network.graph[cim.EnergySource].values():
            source_data = exporter.export_object_data(source, 'EnergySourceExport')
            all_source_data['EnergySource'][str(source.mRID)] = source_data
    
    # Export EquivalentInjection (if present)
    if hasattr(cim, 'EquivalentInjection') and cim.EquivalentInjection in network.graph:
        for source in network.graph[cim.EquivalentInjection].values():
            source_data = exporter.export_object_data(source, 'EquivalentInjectionExport')
            all_source_data['EquivalentInjection'][str(source.mRID)] = source_data
    
    # Export ExternalNetworkInjection (if present)
    if hasattr(cim, 'ExternalNetworkInjection') and cim.ExternalNetworkInjection in network.graph:
        for source in network.graph[cim.ExternalNetworkInjection].values():
            source_data = exporter.export_object_data(source, 'ExternalNetworkInjectionExport')
            all_source_data['ExternalNetworkInjection'][str(source.mRID)] = source_data
    
    # Remove empty categories
    return {k: v for k, v in all_source_data.items() if v}

def _ensure_source_data_loaded(network: GraphModel, cim) -> None:
    """Ensure all required source data is loaded into the graph"""
    
    # Required classes
    required_classes = [
        cim.EnergySource,
        cim.EnergySourcePhase
    ]
    
    # Optional source classes that may not exist in all profiles
    optional_source_classes = [
        ('EquivalentInjection', getattr(cim, 'EquivalentInjection', None)),
        ('ExternalNetworkInjection', getattr(cim, 'ExternalNetworkInjection', None)),
    ]
    
    # Load required classes
    for cim_class in required_classes:
        try:
            network.get_all_edges(cim_class)
        except Exception as e:
            _log.debug(f"Could not load {cim_class.__name__}: {e}")
    
    # Load optional source classes
    for class_name, cim_class in optional_source_classes:
        if cim_class is not None:
            try:
                network.get_all_edges(cim_class)
                _log.debug(f"Loaded optional class {class_name}")
            except Exception as e:
                _log.debug(f"Optional class {class_name} not available: {e}")

def _get_source_shapes_file() -> str:
    """Get default SHACL shapes file path for source export"""
    import os
    package_dir = os.path.dirname(__file__)
    return os.path.join(package_dir, 'shacl', 'source_data_shapes.ttl')

# ===== CONVENIENCE EXPORT FUNCTIONS =====

def export_swing_bus_data(network: GraphModel,
                         output_file: Union[str, Path],
                         format: str = 'json',
                         shacl_shapes_file: str = None,
                         include_phases: bool = True) -> None:
    """Export swing bus data to file with options"""
    
    source_data = get_swing_bus_data(network, shacl_shapes_file)
    
    # Optional filtering
    if not include_phases:
        for source_id, source_info in source_data.items():
            if 'phases' in source_info:
                del source_info['phases']
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(source_data, output_file)
    elif format.lower() == 'csv':
        EquipmentDataWriter.write_csv(source_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(source_data, output_file, 'Swing Bus Data')
    else:
        raise ValueError(f"Unsupported format: {format}")

def get_source_summary(network: GraphModel,
                      shacl_shapes_file: str = None) -> Dict:
    """Get summary statistics of source data"""
    
    all_source_data = get_all_source_data(network, shacl_shapes_file)
    
    summary = {
        'total_sources': 0,
        'source_types': {},
        'voltage_levels': [],
        'total_short_circuit_power': 0.0,
        'phase_count': {'single': 0, 'three': 0}
    }
    
    for source_type, sources in all_source_data.items():
        summary['source_types'][source_type] = len(sources)
        summary['total_sources'] += len(sources)
        
        for source_id, source_info in sources.items():
            # Collect voltage levels
            if 'nominalVoltage' in source_info and source_info['nominalVoltage']:
                voltage = float(source_info['nominalVoltage'])
                if voltage not in summary['voltage_levels']:
                    summary['voltage_levels'].append(voltage)
            
            # Count phases
            phases = source_info.get('phases', [])
            if len(phases) == 1:
                summary['phase_count']['single'] += 1
            elif len(phases) >= 3:
                summary['phase_count']['three'] += 1
            
            # Calculate short circuit power (rough estimate)
            if 'nominalVoltage' in source_info and 'x' in source_info:
                try:
                    v = float(source_info['nominalVoltage'])
                    x = float(source_info['x'])
                    if x > 0:
                        sc_power = (v * v) / x  # Rough estimate
                        summary['total_short_circuit_power'] += sc_power
                except:
                    pass
    
    summary['voltage_levels'].sort()
    return summary

def get_slack_buses(network: GraphModel,
                   shacl_shapes_file: str = None) -> Dict:
    """
    Get sources that are configured as slack/swing buses
    (those with voltage magnitude and angle specified)
    """
    
    source_data = get_swing_bus_data(network, shacl_shapes_file)
    
    slack_buses = {}
    
    for source_id, source_info in source_data.items():
        # A slack bus typically has voltage magnitude and angle specified
        has_voltage_mag = 'voltageMagnitude' in source_info and source_info['voltageMagnitude'] is not None
        has_voltage_angle = 'voltageAngle' in source_info and source_info['voltageAngle'] is not None
        
        if has_voltage_mag and has_voltage_angle:
            slack_buses[source_id] = source_info
    
    return slack_buses

def get_sources_by_voltage_level(network: GraphModel,
                                voltage_level: float,
                                tolerance: float = 0.01,
                                shacl_shapes_file: str = None) -> Dict:
    """Get sources at a specific voltage level"""
    
    all_source_data = get_all_source_data(network, shacl_shapes_file)
    
    filtered_sources = {}
    
    for source_type, sources in all_source_data.items():
        for source_id, source_info in sources.items():
            if 'nominalVoltage' in source_info and source_info['nominalVoltage']:
                source_voltage = float(source_info['nominalVoltage'])
                if abs(source_voltage - voltage_level) / voltage_level <= tolerance:
                    filtered_sources[source_id] = source_info
    
    return filtered_sources