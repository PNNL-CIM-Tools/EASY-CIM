from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.inverter_data import get_inverter_data
from easycim.line_impedance_data import get_impedance_data_per_line
from easycim.line_geometry_data import get_geometry_data_per_line, get_line_data_per_geometry
from easycim.load_data import get_load_data
from easycim.swing_bus_data import get_swing_bus_data
from easycim.three_phase_transformer_data import get_three_phase_transformer_data
from easycim.reduced_data_profile import ReducedDataProfile

cim = ReducedDataProfile
_log = logging.getLogger(__name__)

def get_all_data(network:GraphModel, class_name:str) -> dict:

    if class_name == 'ACLineSegment':
        impedance_data = get_impedance_data_per_line(network)
        data = get_geometry_data_per_line(network)
        for line_id in data:
            data[line_id]['PerLengthImpedance'] = impedance_data[line_id]['PerLengthImpedance']
            data[line_id]['r'] = impedance_data[line_id]['r']
            data[line_id]['x'] = impedance_data[line_id]['x']
            data[line_id]['bch'] = impedance_data[line_id]['bch']
            data[line_id]['r0'] = impedance_data[line_id]['r0']
            data[line_id]['x0'] = impedance_data[line_id]['x0']
            data[line_id]['b0ch'] = impedance_data[line_id]['b0ch']

    elif class_name == 'EnergyConsumer':
        data = get_load_data(network)
    elif class_name == 'EnergySource':
        data = get_swing_bus_data(network)
    elif class_name == 'PowerElectronicsConnection':
        data = get_inverter_data(network)
    elif class_name == 'WireInfo':
        data = get_line_data_per_geometry(network)
    elif class_name == 'PowerTransformer':
        data = get_three_phase_transformer_data(network)
    elif class_name == 'TransformerTank':
        data = {}
    elif class_name == 'RatioTapChanger':
        data = {}
    elif class_name == 'ConnectivityNode':
        data = {}
    else:
        _log.warning(f'Class {class_name} not supported in EASY-CIM. Try running network.get_all_edges(cim.{class_name}) instead.')
        data = {}


    return data
