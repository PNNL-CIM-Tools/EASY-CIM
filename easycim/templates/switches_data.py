from __future__ import annotations
import importlib
import logging
from cimgraph.models import GraphModel
from easycim.templates.data_iterator import get_data
from easycim.templates.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)



def get_switch_data(network: GraphModel) -> dict:
    """This method returns a dictionary of switch data 
    sorted by the overall switch object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of switch data
    :rtype: dict
    """

    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.Breaker)
    network.get_all_edges(cim.Fuse)
    network.get_all_edges(cim.Recloser)
    network.get_all_edges(cim.Sectionaliser)
    network.get_all_edges(cim.LoadBreakSwitch)
    network.get_all_edges(cim.Switch)
    network.get_all_edges(cim.ProtectedSwitch)
    
  

    switch_data = {}
    if cim.Breaker in network.graph:
        for switch_equip in network.graph[cim.Breaker].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.Breaker)

    if cim.Fuse in network.graph:
        for switch_equip in network.graph[cim.Fuse].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.Fuse)

    if cim.Recloser in network.graph:
        for switch_equip in network.graph[cim.Recloser].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.Recloser)

    if cim.Sectionaliser in network.graph:
        for switch_equip in network.graph[cim.Sectionaliser].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.Sectionaliser)

    if cim.LoadBreakSwitch in network.graph:
        for switch_equip in network.graph[cim.LoadBreakSwitch].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.LoadBreakSwitch)

    if cim.Switch in network.graph:
        for switch_equip in network.graph[cim.Switch].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.Switch)   

    if cim.ProtectedSwitch in network.graph:
        for switch_equip in network.graph[cim.ProtectedSwitch].values():
            switch_data[switch_equip.mRID] = get_data(switch_equip, data_profile.ProtectedSwitch)     

    return switch_data

### Q3. Should we get attributes inside switch? eg:SwitchPhase, how to get that?, what about inheritance? where do we draw boundaries as to what all to add?