from __future__ import annotations
from importlib import resources
from collections import defaultdict
from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim import shacl
from cimgraph.utils import get_all_line_data
import cimgraph.data_profile.cimhub_ufls as cim
import logging
_log = logging.getLogger(__name__)


def get_impedance_data_per_line(network: GraphModel,
                               shacl_shapes_file: str = None,
                               use_cached: bool = True,
                               dedicated_query: bool = False) -> dict:
    """
    SHACL-based version of get_impedance_data_per_line
    
    Returns a dictionary of ACLineSegment object parameters with impedance
    of each line, phases, and impedance per length. 
    
    :param network: A CIMGraph power system model
    :param shacl_shapes_file: Path to SHACL shapes file (optional)
    :param use_cached: Use cached result if available
    :param dedicated_query: Use dedicated SPARQL query
    :return: Dictionary of discovered lines and their impedance
    """
    
    # Get CIM module
    cim: cim
    cim_profile, cim = get_cim_profile()
    
    # Use default shapes file if not provided
    if shacl_shapes_file is None:
        shacl_shapes_file = resources.files(shacl).joinpath('line_impedance_shapes.ttl')
    
    try:
        # Use cached result if available
        if use_cached and hasattr(network, 'impedance_data_per_line'):
            return network.impedance_data_per_line
    except:
        pass
    
    # Create SHACL data exporter
    exporter = shacl.SHACLDataExporter(shacl_shapes_file, cim)
    
    if dedicated_query:
        # TODO: Implement dedicated SPARQL query approach
        pass
    else:
        # Use CIM-Graph to build data from graph
        get_all_line_data(network)
        
        line_data = defaultdict(dict)
        
        if cim.ACLineSegment in network.graph:
            line: cim.ACLineSegment
            for line in network.graph[cim.ACLineSegment].values():
                # Export main line data using SHACL
                line_data[str(line.mRID)] = exporter.export_object_data(line, 'ACLineSegmentExport')
                
                # Handle polymorphic impedance data
                per_length_impedance = line.PerLengthImpedance
                if per_length_impedance is not None:
                    impedance_class_name = per_length_impedance.__class__.__name__
                    impedance_shape = f"{impedance_class_name}Export"
                    
                    impedance_data = exporter.export_object_data(per_length_impedance, impedance_shape)
                    line_data[str(line.mRID)]['PerLengthImpedance'] = impedance_data
                    
                    # Handle phase impedance data if present
                    if hasattr(per_length_impedance, 'PhaseImpedanceData'):
                        phase_impedance_list = []
                        
                        for phase_imp in per_length_impedance.PhaseImpedanceData:
                            phase_data = exporter.export_object_data(phase_imp, 'PhaseImpedanceDataExport')
                            phase_impedance_list.append(phase_data)
                        line_data[str(line.mRID)]['PerLengthImpedance']['PhaseImpedanceData'] = phase_impedance_list
        
        # Cache the result
        network.impedance_data_per_line = line_data
        
    return line_data