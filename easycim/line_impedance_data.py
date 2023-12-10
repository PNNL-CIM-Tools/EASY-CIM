from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile


_log = logging.getLogger(__name__)

def get_impedance_data_per_line(network:GraphModel) -> dict:
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

    network.get_all_edges(cim.ACLineSegment)
    network.get_all_edges(cim.ACLineSegmentPhase)
    network.get_all_edges(cim.PerLengthImpedance)
    network.get_all_edges(cim.PerLengthPhaseImpedance)
    network.get_all_edges(cim.PerLengthSequenceImpedance)
    network.get_all_edges(cim.PhaseImpedanceData)
    line_data = {}
    if cim.ACLineSegment in network.graph:
        for line in network.graph[cim.ACLineSegment].values():
            line_data[line.mRID] = get_data(line, data_profile.ACLineSegment)
            # phase data
            line_data[line.mRID]['ACLineSegmentPhases'] = []
            for phase in line.ACLineSegmentPhases:
                data = get_data(phase, data_profile.ACLineSegmentPhase)
                line_data[line.mRID]['ACLineSegmentPhases'].append(data)

            # sequence and phase impedance data
            per_length_impedance = line.PerLengthImpedance
            line_data[line.mRID]['PerLengthImpedance'] = {}
            if per_length_impedance is not None:
                # check if positive/zero sequence impedance data
                if per_length_impedance.__class__.__name__ == 'PerLengthSequenceImpedance':
                    data = get_data(per_length_impedance, data_profile.PerLengthSequenceImpedance)
                    line_data[line.mRID]['PerLengthImpedance'] = data
                # check if phase impedance data
                elif per_length_impedance.__class__.__name__ == 'PerLengthPhaseImpedance':
                    data = get_data(per_length_impedance, data_profile.PerLengthPhaseImpedance)
                    line_data[line.mRID]['PerLengthImpedance'] = data
                    line_data[line.mRID]['PerLengthImpedance']['PhaseImpedanceData'] = []
                    for phase_impedance_data in per_length_impedance.PhaseImpedanceData:
                        data = get_data(phase_impedance_data, data_profile.PhaseImpedanceData)
                        line_data[line.mRID]['PerLengthImpedance']['PhaseImpedanceData'].append(data)
    return line_data

        