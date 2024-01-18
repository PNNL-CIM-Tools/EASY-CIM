from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)

def get_inverter_data(network:GraphModel) -> dict:
    """This method returns a dictionary of single-phase and three-phase inverter
    data sorted by the overall inverter object.

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of inverter data
    :rtype: dict
    """    
    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.PowerElectronicsConnection)
    network.get_all_edges(cim.PowerElectronicsConnectionPhase)
    network.get_all_edges(cim.PowerElectronicsUnit)
    network.get_all_edges(cim.PowerElectronicsWindUnit)
    network.get_all_edges(cim.BatteryUnit)

    if 'PhotoVoltaicUnit' in cim.__all__: # handling inconsistent spelling
        network.get_all_edges(cim.PhotoVoltaicUnit)
    elif 'PhotovoltaicUnit' in cim.__all__:
        network.get_all_edges(cim.PhotovoltaicUnit)
    
    inverter_data = {}
    if cim.PowerElectronicsConnection in network.graph:
        for inverter in network.graph[cim.PowerElectronicsConnection].values():
            # inverter_data[inverter.mRID] = inverter_iterator(inverter)

            inverter_data[inverter.mRID] = get_data(inverter, data_profile.PowerElectronicsConnection)
            # get phase data
            inverter_data[inverter.mRID]['phases'] = []
            for phase in inverter.PowerElectronicsConnectionPhases:
                phase_data = get_data(phase, data_profile.PowerElectronicsConnectionPhase)
                inverter_data[inverter.mRID]['phases'].append(phase_data)

            # get unit data
            inverter_data[inverter.mRID]['PowerElectronicsUnit'] = []
            for unit in inverter.PowerElectronicsUnit:
                unit_data = get_data(unit, data_profile.PowerElectronicsUnit)
                if unit.__class__.__name__ == 'BatteryUnit':
                    unit_data = get_data(unit, data_profile.BatteryUnit, unit_data)
                unit_data['__class__'] = unit.__class__.__name__
                inverter_data[inverter.mRID]['PowerElectronicsUnit'].append(unit_data)
                
    return inverter_data
            