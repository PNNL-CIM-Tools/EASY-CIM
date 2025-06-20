from __future__ import annotations
from importlib import resources
from typing import Dict, List, Union, Any
from collections import defaultdict
from pathlib import Path
from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim import shacl
from cimgraph.utils import get_all_line_data
import cimgraph.data_profile.cimhub_ufls as cim

import logging

_log = logging.getLogger(__name__)

def get_line_data_per_geometry(network: GraphModel,
                              shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_line_data_per_geometry
    
    Returns a dictionary of overhead line and underground cable geometry data 
    with ACLineSegmentPhase objects sorted by the type of conductor used.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for geometry export
    :return: Dictionary of conductors and each line using that geometry
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_geometry_shapes_file()
    
    # Create SHACL data exporter
    exporter = shacl.SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required geometry data
    get_all_line_data(network)
    
    geo_data = {
        'OverheadWireInfo': defaultdict(dict),
        'TapeShieldCableInfo': defaultdict(dict),
        'ConcentricNeutralCableInfo': defaultdict(dict)
    }
    
    # Export OverheadWireInfo
    if cim.OverheadWireInfo in network.graph:
        for wire_info in network.graph[cim.OverheadWireInfo].values():
            wire_data = exporter.export_object_data(wire_info, 'OverheadWireInfoExport')
            geo_data['OverheadWireInfo'][str(wire_info.mRID)] = wire_data
    
    # Export TapeShieldCableInfo
    if cim.TapeShieldCableInfo in network.graph:
        for wire_info in network.graph[cim.TapeShieldCableInfo].values():
            wire_data = exporter.export_object_data(wire_info, 'TapeShieldCableInfoExport')
            geo_data['TapeShieldCableInfo'][str(wire_info.mRID)] = wire_data
    
    # Export ConcentricNeutralCableInfo
    if cim.ConcentricNeutralCableInfo in network.graph:
        for wire_info in network.graph[cim.ConcentricNeutralCableInfo].values():
            wire_data = exporter.export_object_data(wire_info, 'ConcentricNeutralCableInfoExport')
            geo_data['ConcentricNeutralCableInfo'][str(wire_info.mRID)] = wire_data
    
    return geo_data

def get_geometry_data_per_line(network: GraphModel,
                              shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_geometry_data_per_line
    
    Returns a dictionary of ACLineSegment objects and the conductor geometry.
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for geometry export
    :return: Dictionary of discovered lines and their geometry
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_geometry_shapes_file()
    
    # Create SHACL data exporter
    exporter = shacl.SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required geometry data
    _ensure_geometry_data_loaded(network, cim)
    
    line_data = defaultdict(dict)
    
    if cim.ACLineSegment in network.graph:
        for line in network.graph[cim.ACLineSegment].values():
            # Export line with geometry data using SHACL
            line_data[str(line.mRID)] = exporter.export_object_data(
                line, 'ACLineSegmentGeometryExport'
            )
    
    return line_data

def phase_geometry_iterator(wire_info, 
                           shacl_shapes_file: str = None) -> list[dict]:
    """
    SHACL-based version of phase_geometry_iterator
    
    Iterator method to extract phase data for a WireInfo object
    
    :param wire_info: An instance of WireInfo or any of its child classes
    :param shacl_shapes_file: Path to SHACL shapes file
    :return: List of ACLineSegmentPhase dictionaries
    """
    
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_geometry_shapes_file()
    
    # Get CIM module from wire_info
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    exporter = shacl.SHACLDataExporter(shacl_shapes_file, cim)
    
    all_phases = []
    
    if hasattr(wire_info, 'ACLineSegmentPhases'):
        for phase in wire_info.ACLineSegmentPhases:
            phase_data = exporter.export_object_data(
                phase, 'ACLineSegmentPhaseForWireExport'
            )
            all_phases.append(phase_data)
    
    return all_phases

def _ensure_geometry_data_loaded(network: GraphModel, cim) -> None:
    """Ensure all required geometry data is loaded into the graph"""
    required_classes = [
        cim.ACLineSegment,
        cim.ACLineSegmentPhase,
        cim.WireSpacingInfo,
        cim.WirePosition,
        cim.WireInfo,
        cim.OverheadWireInfo,
        cim.CableInfo,
        cim.TapeShieldCableInfo,
        cim.ConcentricNeutralCableInfo
    ]
    
    for cim_class in required_classes:
        try:
            network.get_all_edges(cim_class)
        except Exception as e:
            _log.debug(f"Could not load {cim_class.__name__}: {e}")

def _get_geometry_shapes_file() -> str:
    """Get default SHACL shapes file path for geometry export"""
    import os
    package_dir = os.path.dirname(__file__)
    return os.path.join(package_dir, 'shacl', 'line_geometry_shapes.ttl')

# ===== CONVENIENCE EXPORT FUNCTIONS =====

def export_line_geometry_by_wire(network: GraphModel,
                                output_file: Union[str, Path],
                                format: str = 'json',
                                shacl_shapes_file: str = None) -> None:
    """Export line geometry data organized by wire type"""
    
    geo_data = get_line_data_per_geometry(network, shacl_shapes_file)
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(geo_data, output_file)
    elif format.lower() == 'csv':
        EquipmentDataWriter.write_csv(geo_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(geo_data, output_file, 'Line Geometry by Wire')
    else:
        raise ValueError(f"Unsupported format: {format}")

def export_line_geometry_by_line(network: GraphModel,
                                output_file: Union[str, Path],
                                format: str = 'json',
                                shacl_shapes_file: str = None) -> None:
    """Export line geometry data organized by line segment"""
    
    geo_data = get_geometry_data_per_line(network, shacl_shapes_file)
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(geo_data, output_file)
    elif format.lower() == 'csv':
        EquipmentDataWriter.write_csv(geo_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(geo_data, output_file, 'Line Geometry by Line')
    else:
        raise ValueError(f"Unsupported format: {format}")