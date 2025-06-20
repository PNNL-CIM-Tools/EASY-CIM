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

def get_three_phase_transformer_data(network: GraphModel,
                                   shacl_shapes_file: str = None) -> dict:
    """
    SHACL-based version of get_three_phase_transformer_data
    
    Returns a dictionary of three-phase transformer impedance data 
    sorted by the way the impedance was specified (star or mesh).
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file for transformer export
    :return: Dictionary of transformer data
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_transformer_shapes_file()
    
    # Create SHACL data exporter
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    
    # Load all required transformer data
    _ensure_transformer_data_loaded(network, cim)
    
    transformer_data = {}
    
    if cim.PowerTransformer in network.graph:
        for transformer in network.graph[cim.PowerTransformer].values():
            # Check if it's a three-phase transformer (no tanks)
            is_three_phase = not bool(transformer.TransformerTanks)
            
            if is_three_phase:
                # Export transformer data using SHACL shape
                transformer_export_data = exporter.export_object_data(
                    transformer, 'PowerTransformerExport'
                )
                transformer_data[str(transformer.mRID)] = transformer_export_data
    
    return transformer_data

def _ensure_transformer_data_loaded(network: GraphModel, cim) -> None:
    """Ensure all required transformer data is loaded into the graph"""
    
    required_classes = [
        cim.PowerTransformer,
        cim.PowerTransformerEnd,
        cim.Terminal,
        cim.ConnectivityNode
    ]
    
    # Optional impedance model classes
    optional_classes = [
        ('TransformerTank', getattr(cim, 'TransformerTank', None)),
        ('TransformerCoreAdmittance', getattr(cim, 'TransformerCoreAdmittance', None)),
        ('TransformerMeshImpedance', getattr(cim, 'TransformerMeshImpedance', None)),
        ('TransformerStarImpedance', getattr(cim, 'TransformerStarImpedance', None)),
    ]
    
    # Load required classes
    for cim_class in required_classes:
        try:
            network.get_all_edges(cim_class)
        except Exception as e:
            _log.debug(f"Could not load {cim_class.__name__}: {e}")
    
    # Load optional impedance model classes
    for class_name, cim_class in optional_classes:
        if cim_class is not None:
            try:
                network.get_all_edges(cim_class)
                _log.debug(f"Loaded optional class {class_name}")
            except Exception as e:
                _log.debug(f"Optional class {class_name} not available: {e}")

def _get_transformer_shapes_file() -> str:
    """Get default SHACL shapes file path for transformer export"""
    import os
    package_dir = os.path.dirname(__file__)
    return os.path.join(package_dir, 'shacl', 'three_phase_transformer_shapes.ttl')

# ===== ENHANCED TRANSFORMER ANALYSIS FUNCTIONS =====

def get_transformer_impedance_models(network: GraphModel,
                                   shacl_shapes_file: str = None) -> Dict:
    """
    Analyze which impedance models are used in transformers
    
    :return: Dictionary categorizing transformers by impedance model type
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_transformer_shapes_file()
    
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    _ensure_transformer_data_loaded(network, cim)
    
    impedance_models = {
        'star_model': {},
        'mesh_model': {},
        'direct_impedance': {},
        'mixed_model': {}
    }
    
    if cim.PowerTransformer in network.graph:
        for transformer in network.graph[cim.PowerTransformer].values():
            is_three_phase = not bool(transformer.TransformerTanks)
            
            if is_three_phase:
                summary_data = exporter.export_object_data(
                    transformer, 'TransformerImpedanceModelSummary'
                )
                
                has_star = any(end.get('hasStarImpedance', False) 
                             for end in summary_data.get('impedanceModels', []))
                has_mesh = any(end.get('hasMeshImpedance', False) 
                             for end in summary_data.get('impedanceModels', []))
                has_direct = any(end.get('hasDirectR', False) and end.get('hasDirectX', False)
                               for end in summary_data.get('impedanceModels', []))
                
                transformer_id = str(transformer.mRID)
                
                if has_star and has_mesh:
                    impedance_models['mixed_model'][transformer_id] = summary_data
                elif has_star:
                    impedance_models['star_model'][transformer_id] = summary_data
                elif has_mesh:
                    impedance_models['mesh_model'][transformer_id] = summary_data
                elif has_direct:
                    impedance_models['direct_impedance'][transformer_id] = summary_data
    
    return impedance_models

def get_transformer_classification(network: GraphModel,
                                 shacl_shapes_file: str = None) -> Dict:
    """
    Classify transformers as single-phase or three-phase
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    if shacl_shapes_file is None:
        shacl_shapes_file = _get_transformer_shapes_file()
    
    exporter = SHACLDataExporter(shacl_shapes_file, cim)
    _ensure_transformer_data_loaded(network, cim)
    
    classification = {
        'three_phase': {},
        'single_phase': {},
        'multi_winding': {}
    }
    
    if cim.PowerTransformer in network.graph:
        for transformer in network.graph[cim.PowerTransformer].values():
            class_data = exporter.export_object_data(
                transformer, 'TransformerClassificationExport'
            )
            
            transformer_id = str(transformer.mRID)
            has_tanks = class_data.get('hasTanks', 0) > 0
            end_count = class_data.get('endCount', 0)
            
            if has_tanks:
                classification['single_phase'][transformer_id] = class_data
            elif end_count == 2:
                classification['three_phase'][transformer_id] = class_data
            elif end_count > 2:
                classification['multi_winding'][transformer_id] = class_data
    
    return classification

def export_three_phase_transformer_data(network: GraphModel,
                                       output_file: Union[str, Path],
                                       format: str = 'json',
                                       shacl_shapes_file: str = None,
                                       include_impedance_models: bool = True) -> None:
    """Export three-phase transformer data to file"""
    
    transformer_data = get_three_phase_transformer_data(network, shacl_shapes_file)
    
    # Optionally include impedance model analysis
    if include_impedance_models:
        impedance_models = get_transformer_impedance_models(network, shacl_shapes_file)
        output_data = {
            'transformers': transformer_data,
            'impedance_model_analysis': impedance_models
        }
    else:
        output_data = transformer_data
    
    from easycim.file_writers import EquipmentDataWriter
    
    if format.lower() == 'json':
        EquipmentDataWriter.write_json(output_data, output_file)
    elif format.lower() == 'csv':
        # For CSV, flatten the transformer data only
        EquipmentDataWriter.write_csv(transformer_data, output_file)
    elif format.lower() in ['xlsx', 'excel']:
        EquipmentDataWriter.write_excel(transformer_data, output_file, 'Three-Phase Transformers')
    else:
        raise ValueError(f"Unsupported format: {format}")

def get_transformer_summary(network: GraphModel,
                          shacl_shapes_file: str = None) -> Dict:
    """Get comprehensive transformer summary"""
    
    transformer_data = get_three_phase_transformer_data(network, shacl_shapes_file)
    classification = get_transformer_classification(network, shacl_shapes_file)
    impedance_models = get_transformer_impedance_models(network, shacl_shapes_file)
    
    summary = {
        'total_transformers': len(transformer_data),
        'classification': {
            'three_phase': len(classification['three_phase']),
            'single_phase': len(classification['single_phase']),
            'multi_winding': len(classification['multi_winding'])
        },
        'impedance_models': {
            'star_model': len(impedance_models['star_model']),
            'mesh_model': len(impedance_models['mesh_model']),
            'direct_impedance': len(impedance_models['direct_impedance']),
            'mixed_model': len(impedance_models['mixed_model'])
        },
        'voltage_levels': [],
        'vector_groups': {}
    }
    
    # Analyze voltage levels and vector groups
    for transformer_id, transformer_info in transformer_data.items():
        # Vector groups
        vector_group = transformer_info.get('vectorGroup', 'Unknown')
        summary['vector_groups'][vector_group] = summary['vector_groups'].get(vector_group, 0) + 1
        
        # Voltage levels
        for end in transformer_info.get('PowerTransformerEnd', []):
            rated_u = end.get('ratedU')
            if rated_u:
                voltage = float(rated_u)
                if voltage not in summary['voltage_levels']:
                    summary['voltage_levels'].append(voltage)
    
    summary['voltage_levels'].sort()
    
    return summary

def get_transformers_by_impedance_model(network: GraphModel,
                                      model_type: str,
                                      shacl_shapes_file: str = None) -> Dict:
    """
    Get transformers filtered by impedance model type
    
    :param model_type: 'star', 'mesh', 'direct', or 'mixed'
    """
    
    impedance_models = get_transformer_impedance_models(network, shacl_shapes_file)
    
    model_map = {
        'star': 'star_model',
        'mesh': 'mesh_model', 
        'direct': 'direct_impedance',
        'mixed': 'mixed_model'
    }
    
    model_key = model_map.get(model_type.lower(), model_type.lower() + '_model')
    
    return impedance_models.get(model_key, {})

def get_transformers_by_vector_group(network: GraphModel,
                                   vector_group: str,
                                   shacl_shapes_file: str = None) -> Dict:
    """Get transformers filtered by vector group"""
    
    transformer_data = get_three_phase_transformer_data(network, shacl_shapes_file)
    
    filtered_transformers = {
        xfmr_id: xfmr_data 
        for xfmr_id, xfmr_data in transformer_data.items()
        if xfmr_data.get('vectorGroup', '').upper() == vector_group.upper()
    }
    
    return filtered_transformers