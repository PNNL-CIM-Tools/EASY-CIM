from __future__ import annotations
import importlib
import logging
from cimgraph.models import GraphModel
from easycim.templates.data_iterator import get_data
from easycim.templates.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)







def get_capacitor_data(network: GraphModel) -> dict:
    """This method returns a dictionary of capacitor
    data sorted by the overall capacitor object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of capacitor data
    :rtype: dict
    """

    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.StaticVarCompensator)
    network.get_all_edges(cim.RegulatingCondEq)
  
    network.get_all_edges(cim.ShuntCompensator)
    network.get_all_edges(cim.NonlinearShuntCompensator)
    network.get_all_edges(cim.NonlinearShuntCompensatorPoint)
    network.get_all_edges(cim.LinearShuntCompensator)
    network.get_all_edges(cim.NonlinearShuntCompensatorPoint)
    network.get_all_edges(cim.ShuntCompensatorPhase)
    network.get_all_edges(cim.NonlinearShuntCompensatorPoint)
    network.get_all_edges(cim.LinearShuntCompensatorPhase)
    network.get_all_edges(cim.NonlinearShuntCompensatorPoint)
    network.get_all_edges(cim.NonlinearShuntCompensatorPhase)
    network.get_all_edges(cim.NonlinearShuntCompensatorPhasePoint)
    network.get_all_edges(cim.RegulatingControl)
    network.get_all_edges(cim.Terminal)
    network.get_all_edges(cim.SVCControlMode)
    network.get_all_edges(cim.PhaseShuntConnectionKind)
    network.get_all_edges(cim.PhaseCode)
    network.get_all_edges(cim.SinglePhaseKind)


    capacitor_data = {}
    if cim.LinearShuntCompensator in network.graph:
        for capacitor_equip in network.graph[cim.LinearShuntCompensator].values():
            data_profile = ReducedDataProfile()
            capacitor_data[capacitor_equip.mRID] = get_data(capacitor_equip, data_profile.LinearShuntCompensator)

    if cim.NonlinearShuntCompensatorPoint in network.graph:
        for capacitor_equip in network.graph[cim.NonlinearShuntCompensatorPoint].values():
            data_profile = ReducedDataProfile()
            capacitor_data[capacitor_equip.mRID] = get_data(capacitor_equip, data_profile.NonlinearShuntCompensatorPoint)

    if cim.StaticVarCompensator in network.graph:
        for capacitor_equip in network.graph[cim.StaticVarCompensator].values():
            data_profile = ReducedDataProfile()
            capacitor_data[capacitor_equip.mRID] = get_data(capacitor_equip, data_profile.StaticVarCompensator)

    return capacitor_data