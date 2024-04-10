from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
from easycim.templates import line_impedance_template

_log = logging.getLogger(__name__)

def get_impedance_data_per_line(network:GraphModel, use_cached:bool=True, dedicated_query=False) -> dict:
    """Returns a dictionary of ACLineSegment object parameters with impedance
    of each line, phases, and impedance per length. The impedance data is 
    sorted by each line

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of discoverd lines and their impedance
    :rtype: dict
    """    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    
    try:
        # Use cached result in CIM-Graph network, if available
        if use_cached:
            line_data = network.impedance_data_per_line
        else:
            line_data
    except:
        # Otherwise create new line data dictionary
        if dedicated_query:
            
            pass
        else:
            # Use CIM-Graph to build data from graph
            network.get_all_edges(cim.ACLineSegment)
            network.get_all_edges(cim.ACLineSegmentPhase)
            network.get_all_edges(cim.PerLengthImpedance)
            network.get_all_edges(cim.PerLengthPhaseImpedance)
            network.get_all_edges(cim.PerLengthSequenceImpedance)
            network.get_all_edges(cim.PhaseImpedanceData)
            line_data = {}
            if cim.ACLineSegment in network.graph:
                for line in network.graph[cim.ACLineSegment].values():
                    line_data[line.mRID] = line_impedance_template(line)
    return line_data

        