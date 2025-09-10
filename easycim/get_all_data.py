from __future__ import annotations

import importlib
import logging

from cimgraph.models import GraphModel

from easycim.inverter_data import get_inverter_data
from easycim.line_geometry_data import (get_geometry_data_per_line,
                                        get_line_data_per_geometry)
from easycim.line_impedance_data import get_impedance_data_per_line
from easycim.load_data import get_load_data
from easycim.swing_bus_data import get_swing_bus_data
from easycim.three_phase_transformer_data import \
    get_three_phase_transformer_data
from easycim.cim_graphql_generator import CIMGraphQLGenerator

_log = logging.getLogger(__name__)


def get_all_data(network: GraphModel, class_name: str, use_graphql: bool = False) -> dict:
    """
    Get all data for a given CIM class. Can use either the legacy hard-coded 
    approach or the new GraphQL-based approach.
    
    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :param class_name: Name of the CIM class to extract data for
    :type class_name: str
    :param use_graphql: Whether to use the new GraphQL-based approach
    :type use_graphql: bool
    :return: A dictionary of extracted data
    :rtype: dict
    """
    
    if use_graphql:
        return get_all_data_graphql(network, class_name)
    else:
        return get_all_data_legacy(network, class_name)


def get_all_data_graphql(network: GraphModel, class_name: str) -> dict:
    """
    Get all data for a given CIM class using the new GraphQL-based approach.
    
    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :param class_name: Name of the CIM class to extract data for
    :type class_name: str
    :return: A dictionary of extracted data
    :rtype: dict
    """
    
    generator = CIMGraphQLGenerator()
    
    # Classes that have GraphQL schemas implemented
    supported_classes = ['PowerTransformer', 'ACLineSegment', 'EnergyConsumer']
    
    if class_name in supported_classes:
        try:
            data = generator.generate_cim_data(network, class_name)
            _log.info(f'Successfully extracted {class_name} data using GraphQL approach')
            return data
        except Exception as e:
            _log.error(f'GraphQL extraction failed for {class_name}: {str(e)}')
            _log.info(f'Falling back to legacy approach for {class_name}')
            return get_all_data_legacy(network, class_name)
    else:
        _log.info(f'{class_name} not yet supported in GraphQL approach, using legacy method')
        return get_all_data_legacy(network, class_name)


def get_all_data_legacy(network: GraphModel, class_name: str) -> dict:
    """
    Get all data for a given CIM class using the legacy hard-coded approach.
    This maintains backward compatibility with existing code.
    
    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :param class_name: Name of the CIM class to extract data for
    :type class_name: str
    :return: A dictionary of extracted data
    :rtype: dict
    """

    if class_name == 'ACLineSegment':
        impedance_data = get_impedance_data_per_line(network)
        data = get_geometry_data_per_line(network)
        for line_id in data:
            data[line_id]['PerLengthImpedance'] = impedance_data[line_id][
                'PerLengthImpedance']
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
        _log.warning(
            f'Class {class_name} not supported in EASY-CIM. Try running network.get_all_edges(cim.{class_name}) instead.'
        )
        data = {}

    return data
