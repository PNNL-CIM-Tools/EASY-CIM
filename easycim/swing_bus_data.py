from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)

def source_iterator(energy_source:cim.EnergySource) -> dict:
    """Iterator method to extract phase data for an EnergySource object

    :param energy_source: An instance of EnergySource or any of its child classes
    :type energy_source: cim.EnergySource
    :return: an EnergySource dictionaries
    :rtype: dict
    """    
    data_profile = ReducedDataProfile()
    source_data = get_data(energy_source, data_profile.EnergySource)
    source_data['phases'] = []
    for phase in energy_source.EnergySourcePhase:
        phase_data = get_data(phase, data_profile.EnergySourcePhase)
        source_data['phases'].append(phase_data)
    return source_data

def get_swing_bus_data(network:GraphModel) -> dict:
    """This method returns a dictionary of single-phase and three-phase source
    data sorted by the overall source object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of source data
    :rtype: dict
    """    
    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.EnergySource)
    network.get_all_edges(cim.EnergySourcePhase)

    
    source_data = {}
    if cim.EnergySource in network.graph:
        for source in network.graph[cim.EnergySource].values():
            source_data[source.mRID] = source_iterator(source)
    return source_data