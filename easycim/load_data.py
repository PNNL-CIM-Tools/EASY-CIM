from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)

def load_iterator(energy_consumer:cim.EnergyConsumer) -> dict:
    """Iterator method to extract phase data for an EnergyConsumer object

    :param energy_consumer: An instance of EnergyConsumer or any of its child classes
    :type energy_consumer: cim.EnergyConsumer
    :return: an EnergyConsumer dictionaries
    :rtype: dict
    """    
    data_profile = ReducedDataProfile()
    load_data = get_data(energy_consumer, data_profile.EnergyConsumer)
    load_data['phases'] = []
    for phase in energy_consumer.EnergyConsumerPhase:
        phase_data = get_data(phase, data_profile.EnergyConsumerPhase)
        load_data['phases'].append(phase_data)

    if 'House' in energy_consumer.__dataclass_fields__:
        if energy_consumer.House is not None:
            load_data['House'] = get_data(energy_consumer.House, data_profile.House)
    return load_data

def get_load_data(network:GraphModel) -> dict:
    """This method returns a dictionary of single-phase and three-phase load
    data sorted by the overall load object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of load data
    :rtype: dict
    """    
    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.EnergyConsumer)
    network.get_all_edges(cim.ConformLoad)
    network.get_all_edges(cim.NonConformLoad)
    network.get_all_edges(cim.EnergyConsumerPhase)
    if 'House' in cim.__all__:
        network.get_all_edges(cim.House)
    # if 'LoadResponseCharacteristic' in cim.__all__:
    #     network.get_all_edges(cim.LoadResponseCharacteristic)
    
    load_data = {}
    if cim.EnergyConsumer in network.graph:
        for load in network.graph[cim.EnergyConsumer].values():
            load_data[load.mRID] = load_iterator(load)

    if cim.ConformLoad in network.graph:
        for load in network.graph[cim.ConformLoad].values():
            load_data[load.mRID] = load_iterator(load)

    if cim.NonConformLoad in network.graph:
        for load in network.graph[cim.NonConformLoad].values():
            load_data[load.mRID] = load_iterator(load)
    return load_data