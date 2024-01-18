from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)


def phase_geometry_iterator(wire_info:cim.WireInfo) -> list[dict]:
    """Iterator method to extract phase data for a WireInfo object

    :param wire_info: An instance of WireInfo or any of its child classes
    :type wire_info: cim.WireInfo
    :return: a list of ACLineSegmentPhase dictionaries
    :rtype: list[dict]
    """    
    data_profile = ReducedDataProfile()
    all_phases = []
    for phase in wire_info.ACLineSegmentPhases:
        phase_data = get_data(phase, data_profile.ACLineSegmentPhase)
        line_data = {}
        line_data['mRID'] = phase.ACLineSegment.mRID
        line_data['name'] = phase.ACLineSegment.name
        phase_data['ACLineSegment'] = line_data
        all_phases.append(phase_data)
    return all_phases


def get_line_data_per_geometry(network:GraphModel) -> dict:
    """This method returns a dictionary of overhead line and underground cable
    geometry data with ACLineSegmentPhase objects sorted by the type of conductor
    used by that line conductor.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of conductors and each line using that geometry
    :rtype: dict
    """    
    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.ACLineSegment)
    network.get_all_edges(cim.ACLineSegmentPhase)
    network.get_all_edges(cim.WireSpacingInfo)
    network.get_all_edges(cim.WirePosition)
    network.get_all_edges(cim.WireInfo)
    network.get_all_edges(cim.OverheadWireInfo)
    network.get_all_edges(cim.CableInfo)
    network.get_all_edges(cim.TapeShieldCableInfo)
    network.get_all_edges(cim.ConcentricNeutralCableInfo)


    geo_data = {}
    geo_data['OverheadWireInfo'] = {}
    geo_data['TapeShieldCableInfo'] = {}
    geo_data['ConcentricNeutralCableInfo'] = {}

    # Loop through all overhead wires
    if cim.OverheadWireInfo in network.graph:
        for wire_info in network.graph[cim.OverheadWireInfo].values():
            wire_data = get_data(wire_info, data_profile.WireInfo)
            geo_data['OverheadWireInfo'][wire_info.mRID] = wire_data
            phase_data = phase_geometry_iterator(wire_info)
            geo_data['OverheadWireInfo'][wire_info.mRID]['ACLineSegmentPhases'] = phase_data
    # Loop through all tape shield cables
    if cim.TapeShieldCableInfo in network.graph:
        for wire_info in network.graph[cim.TapeShieldCableInfo].values():
            wire_data = get_data(wire_info, data_profile.WireInfo)
            wire_data = get_data(wire_info, data_profile.CableInfo, wire_data)
            wire_data = get_data(wire_info, data_profile.TapeShieldCableInfo, wire_data)
            geo_data['TapeShieldCableInfo'][wire_info.mRID] = wire_data
            phase_data = phase_geometry_iterator(wire_info)
            geo_data['TapeShieldCableInfo'][wire_info.mRID]['ACLineSegmentPhases'] = phase_data
    # Loop through all tape shield cables
    if cim.ConcentricNeutralCableInfo in network.graph:
        for wire_info in network.graph[cim.ConcentricNeutralCableInfo].values():
            wire_data = get_data(wire_info, data_profile.WireInfo)
            wire_data = get_data(wire_info, data_profile.CableInfo, wire_data)
            wire_data = get_data(wire_info, data_profile.ConcentricNeutralCableInfo, wire_data)
            geo_data['ConcentricNeutralCableInfo'][wire_info.mRID] = wire_data
            phase_data = phase_geometry_iterator(wire_info)
            geo_data['ConcentricNeutralCableInfo'][wire_info.mRID]['ACLineSegmentPhases'] = phase_data
    return geo_data


def get_geometry_data_per_line(network):
    """This method returns a dictionary of ACLineSegment objects and the
    conductor geometry 

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of discoverd lines and their impedance
    :rtype: dict
    """
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.ACLineSegment)
    network.get_all_edges(cim.ACLineSegmentPhase)
    network.get_all_edges(cim.WireSpacingInfo)
    network.get_all_edges(cim.WirePosition)
    network.get_all_edges(cim.WireInfo)
    network.get_all_edges(cim.OverheadWireInfo)
    network.get_all_edges(cim.CableInfo)
    network.get_all_edges(cim.TapeShieldCableInfo)
    network.get_all_edges(cim.ConcentricNeutralCableInfo)
    # Build output data
    line_data = {}
    if cim.ACLineSegment in network.graph:

        for line in network.graph[cim.ACLineSegment].values():
            line_data[line.mRID] = get_data(line, data_profile.IdentifiedObject)
            line_data[line.mRID]['length'] = line.length
            # phase data
            line_data[line.mRID]['ACLineSegmentPhases'] = []
            for phase in line.ACLineSegmentPhases:
                phase_data = get_data(phase, data_profile.ACLineSegmentPhase)
                line_data[line.mRID]['ACLineSegmentPhases'].append(phase_data)
                # wire geometry data
                wire_info = phase.WireInfo
                if wire_info is not None:
                    wire_data = get_data(wire_info, data_profile.IdentifiedObject)
                    wire_data['__class__'] = wire_info.__class__.__name__
                    phase_data['WireInfo'] = wire_data
                    # wire_data = get_data(wire_info, data_profile.WireInfo)
                    # if wire_info.__class__.__name__ in ['OverheadWireInfo', 'WireInfo']:
                    #     phase_data['WireInfo'] = wire_data
                    # elif wire_info.__class__.__name__ == 'CableInfo':
                    #     wire_data = get_data(wire_info, data_profile.CableInfo, wire_data)
                    #     phase_data['WireInfo'] = wire_data
                    # elif wire_info.__class__.__name__ == 'TapeShieldCableInfo':
                    #     wire_data = get_data(wire_info, data_profile.CableInfo, wire_data)
                    #     wire_data = get_data(wire_info, data_profile.TapeShieldCableInfo, wire_data)
                    #     phase_data['WireInfo'] = wire_data
                    # elif wire_info.__class__.__name__ == 'CableInfo':
                    #     wire_data = get_data(wire_info, data_profile.CableInfo, wire_data)
                    #     wire_data = get_data(wire_info, data_profile.ConcentricNeutralCableInfo, wire_data)
                    #     phase_data['WireInfo'] = wire_data
                else:
                    phase_data['WireInfo'] = {}
                line_data[line.mRID]['ACLineSegmentPhases'].append(phase_data)
            # wire spacing data
            wire_spacing = line.WireSpacingInfo
            if wire_spacing is not None:
                spacing_data = get_data(wire_spacing, data_profile.WireSpacingInfo)
                spacing_data['WirePosition'] = []
                for wire_position in wire_spacing.WirePositions:
                    position_data = get_data(wire_position, data_profile.WirePosition)
                    spacing_data['WirePosition'].append(position_data)
                line_data[line.mRID]['WireSpacingInfo'] = spacing_data
            else:
                line_data[line.mRID]['WireSpacingInfo'] = {}


                
    return line_data