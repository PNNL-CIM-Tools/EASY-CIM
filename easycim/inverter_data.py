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

def get_inverter_data(network: GraphModel,
                     shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_inverter_data
    
    Returns a dictionary of single-phase and three-phase inverter data 
    sorted by the overall inverter object.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for inverter export
    :return: Dictionary of inverter data
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_inverter_shapes_file()
    
    # Create SHACL data exporter
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required inverter data
    _ensure_inverter_data_loaded(network, cim)
    
    inverter_data = {}
    
    if cim.PowerElectronicsConnection in network.graph:
        for inverter in network.graph[cim.PowerElectronicsConnection].values():
            # Export inverter data using SHACL shape
            inverter_export_data = exporter.export_object_data(
                inverter, 'PowerElectronicsConnectionExport'
            )
            inverter_data[str(inverter.mRID)] = inverter_export_data
    
    return inverter_data

def _ensure_inverter_data_loaded(network: GraphModel, cim) -> None:
    """Ensure all required inverter data is loaded into the graph"""
    
    # Required classes
    required_classes = [
        cim.PowerElectronicsConnection,
        cim.PowerElectronicsConnectionPhase,
        cim.PowerElectronicsUnit
    ]
    
    # Optional unit classes that may not exist in all profiles
    optional_unit_classes = [
        ('PowerElectronicsWindUnit', getattr(cim, 'PowerElectronicsWindUnit', None)),
        ('BatteryUnit', getattr(cim, 'BatteryUnit', None)),
        ('SolarGeneratingUnit', getattr(cim, 'SolarGeneratingUnit', None)),
        # ('AsynchronousMachine', getattr(cim, 'AsynchronousMachine', None)),
        # ('SynchronousMachine', getattr(cim, 'SynchronousMachine', None)),
    ]
    
    # Handle PhotoVoltaic vs Photovoltaic spelling variations
    pv_classes = []
    if hasattr(cim, 'PhotoVoltaicUnit'):
        pv_classes.append(('PhotoVoltaicUnit', cim.PhotoVoltaicUnit))
    if hasattr(cim, 'PhotovoltaicUnit'):
        pv_classes.append(('PhotovoltaicUnit', cim.PhotovoltaicUnit))
    
    # Load required classes
    for cim_class in required_classes:
        try:
            network.get_all_edges(cim_class)
        except Exception as e:
            _log.debug(f"Could not load {cim_class.__name__}: {e}")
    
    # Load optional unit classes
    for class_name, cim_class in optional_unit_classes:
        if cim_class is not None:
            try:
                network.get_all_edges(cim_class)
                _log.debug(f"Loaded optional class {class_name}")
            except Exception as e:
                _log.debug(f"Optional class {class_name} not available: {e}")
    
    # Load PV classes (handle spelling variations)
    for class_name, cim_class in pv_classes:
        try:
            network.get_all_edges(cim_class)
            _log.debug(f"Loaded PV class {class_name}")
        except Exception as e:
            _log.debug(f"PV class {class_name} not available: {e}")

def _get_inverter_shapes_file() -> str:
    """Get default SHACL shapes file path for inverter export"""
    import os
    package_dir = os.path.dirname(__file__)
    return os.path.join(package_dir, 'shacl', 'inverter_data_shapes.ttl')

# ===== CONVENIENCE EXPORT FUNCTIONS =====

def export_inverter_data(network: GraphModel,
                        output_file: Union[str, Path],
                        format: str = 'json',
                        shacl_shapes_file: str = None,
                        include_phases: bool = True,
                        include_units: bool = True) -> None:
    """Export inverter data to file with options"""
    
    inverter_data = get_inverter_data(network, shacl_shapes_file)
    
    # Optional filtering
    if not include_phases:
        for inverter_id, inverter_info in inverter_data.items():
            if 'phases' in inverter_info:
                del inverter_info['phases']
    
    if not include_units:
        for inverter_id, inverter_info in inverter_data.items():
            if 'PowerElectronicsUnit' in inverter_info:
                del inverter_info['PowerElectronicsUnit']
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(inverter_data, output_file)
    elif format.lower() == 'csv':
        EquipmentDataWriter.write_csv(inverter_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(inverter_data, output_file, 'Inverter Data')
    else:
        raise ValueError(f"Unsupported format: {format}")

def get_inverter_summary(network: GraphModel,
                        shacl_shapes_file: str = None) -> Dict:
    """Get summary statistics of inverter data"""
    
    inverter_data = get_inverter_data(network, shacl_shapes_file)
    
    summary = {
        'total_inverters': len(inverter_data),
        'unit_types': {},
        'total_rated_s': 0.0,
        'total_p': 0.0,
        'total_q': 0.0,
        'phase_count': {'single': 0, 'three': 0},
        'with_battery': 0,
        'with_pv': 0,
        'with_wind': 0
    }
    
    for inverter_id, inverter_info in inverter_data.items():
        # Sum rated power
        if 'ratedS' in inverter_info and inverter_info['ratedS'] is not None:
            try:
                summary['total_rated_s'] += float(inverter_info['ratedS'])
            except:
                pass
        
        # Sum active/reactive power
        if 'p' in inverter_info and inverter_info['p'] is not None:
            try:
                summary['total_p'] += float(inverter_info['p'])
            except:
                pass
        
        if 'q' in inverter_info and inverter_info['q'] is not None:
            try:
                summary['total_q'] += float(inverter_info['q'])
            except:
                pass
        
        # Count phases
        phases = inverter_info.get('phases', [])
        if len(phases) == 1:
            summary['phase_count']['single'] += 1
        elif len(phases) >= 3:
            summary['phase_count']['three'] += 1
        
        # Count unit types
        units = inverter_info.get('PowerElectronicsUnit', [])
        for unit in units:
            unit_type = unit.get('__class__', 'Unknown')
            summary['unit_types'][unit_type] = summary['unit_types'].get(unit_type, 0) + 1
            
            # Count specific technologies
            if 'Battery' in unit_type:
                summary['with_battery'] += 1
            elif 'PhotoVoltaic' in unit_type or 'Photovoltaic' in unit_type or 'Solar' in unit_type:
                summary['with_pv'] += 1
            elif 'Wind' in unit_type:
                summary['with_wind'] += 1
    
    return summary

def get_inverters_by_technology(network: GraphModel,
                               technology: str,
                               shacl_shapes_file: str = None) -> Dict:
    """
    Get inverters filtered by technology type
    
    :param technology: 'battery', 'pv', 'wind', or 'solar'
    """
    
    inverter_data = get_inverter_data(network, shacl_shapes_file)
    
    tech_keywords = {
        'battery': ['Battery'],
        'pv': ['PhotoVoltaic', 'Photovoltaic', 'Solar'],
        'solar': ['PhotoVoltaic', 'Photovoltaic', 'Solar'],
        'wind': ['Wind']
    }
    
    keywords = tech_keywords.get(technology.lower(), [technology])
    
    filtered_data = {}
    
    for inverter_id, inverter_info in inverter_data.items():
        units = inverter_info.get('PowerElectronicsUnit', [])
        
        for unit in units:
            unit_type = unit.get('__class__', '')
            if any(keyword in unit_type for keyword in keywords):
                filtered_data[inverter_id] = inverter_info
                break
    
    return filtered_data

def get_battery_storage_data(network: GraphModel,
                            shacl_shapes_file: str = None) -> Dict:
    """Get detailed battery storage information"""
    
    inverter_data = get_inverter_data(network, shacl_shapes_file)
    
    battery_data = {}
    
    for inverter_id, inverter_info in inverter_data.items():
        units = inverter_info.get('PowerElectronicsUnit', [])
        
        for unit in units:
            if unit.get('__class__', '') == 'BatteryUnit':
                battery_data[inverter_id] = {
                    'inverter_info': inverter_info,
                    'battery_state': unit.get('batteryState'),
                    'rated_energy': unit.get('ratedE'),
                    'stored_energy': unit.get('storedE'),
                    'min_power': unit.get('minP'),
                    'max_power': unit.get('maxP')
                }
                break
    
    return battery_data