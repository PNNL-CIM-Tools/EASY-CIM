from __future__ import annotations
import importlib
import logging
from cimgraph.models import GraphModel
from cimgraph.databases import get_cim_profile
from easycim.templates.data_iterator import get_data
from easycim.templates.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)




def get_generator_data(network: GraphModel) -> dict:
    """This method returns a dictionary of generator
    data sorted by the overall capacitor object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of capacitor data
    :rtype: dict
    """

    data_profile = ReducedDataProfile()
    cim: cim
    cim_profile, cim = get_cim_profile()
    # Run network queries
    network.get_all_edges(cim.RotatingMachine)
    network.get_all_edges(cim.SynchronousMachine)
    network.get_all_edges(cim.AsynchronousMachine)
    network.get_all_edges(cim.RegulatingCondEq)
    network.get_all_edges(cim.EnergyConnection)
    network.get_all_edges(cim.ConductingEquipment)
    network.get_all_edges(cim.Equipment)
    network.get_all_edges(cim.PowerSystemResource)
    network.get_all_edges(cim.SynchronousMachineKind)
    network.get_all_edges(cim.AsynchronousMachineKind)
    network.get_all_edges(cim.SynchronousMachineOperatingMode)
  

    generator_data = {}
    if cim.SynchronousMachine in network.graph:
        for generator_equip in network.graph[cim.SynchronousMachine].values():
            # generator_data[generator_equip.mRID] = get_data(generator_equip, ['ikk', 'maxQ', 'minQ', 'operatingMode', 'type']) ## data_profile.SynchronousMachine
            generator_data[generator_equip.mRID] = get_data(generator_equip, data_profile.SynchronousMachine) ## data_profile.SynchronousMachine


    if cim.AsynchronousMachine in network.graph:
        for generator_equip in network.graph[cim.AsynchronousMachine].values():
            generator_data[generator_equip.mRID] = get_data(generator_equip, data_profile.AsynchronousMachine)
    
    if cim.RotatingMachine in network.graph:
        for generator_equip in network.graph[cim.RotatingMachine].values():
            generator_data[generator_equip.mRID] = get_data(generator_equip, data_profile.RotatingMachine)
    
    
    
    # if cim.Conformgenerator_equip in network.graph:
    #     for generator_equip in network.graph[cim.Conformgenerator_equip].values():
    #         generator_data[generator_equip.mRID] = gen_iterator(generator_equip)

    # if cim.NonConformgenerator_equip in network.graph:
    #     for generator_equip in network.graph[cim.NonConformgenerator_equip].values():
    #         generator_data[generator_equip.mRID] = gen_iterator(generator_equip)
    
    return generator_data