from __future__ import annotations
import importlib
import logging

from cimgraph import GraphModel
from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

_log = logging.getLogger(__name__)

def get_three_phase_transformer_data(network:GraphModel) -> dict:
    """This method returns a dictionary of three-phase transformer impedance
    data sorted by the way the impedance was specified (star or mesh).

    :param network: A CIMantic Graphs power system model
    :type network: GraphModel
    :return: A dictionary of inverter data
    :rtype: dict
    """    
    
    data_profile = ReducedDataProfile()
    cim_profile = network.connection.connection_params.cim_profile
    cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
    # Run network queries
    network.get_all_edges(cim.PowerTransformer)
    network.get_all_edges(cim.PowerTransformerEnd)
    network.get_all_edges(cim.TransformerTank)
    network.get_all_edges(cim.TransformerCoreAdmittance)
    network.get_all_edges(cim.TransformerMeshImpedance)
    network.get_all_edges(cim.TransformerStarImpedance)
    network.get_all_edges(cim.Terminal)
    network.get_all_edges(cim.ConnectivityNode)

    transformer_data = {}
    if cim.PowerTransformer in network.graph:
        for transformer in network.graph[cim.PowerTransformer].values():
            three_phase = True
            if transformer.TransformerTanks:
                three_phase = False
            # TODO: Write better logic

            if three_phase:
                xfmr_data = get_data(transformer, data_profile.PowerTransformer)
                xfmr_data['PowerTransformerEnd'] = []
                for end in transformer.PowerTransformerEnd:
                    end_data = {}
                    end_data['Terminal'] = get_data(end.Terminal, data_profile.Terminal)
                    end_data['Terminal']['ConnectivityNode'] = end.Terminal.ConnectivityNode.name
                    end_data = get_data(end, data_profile.TransformerEnd, end_data)
                    end_data = get_data(end, data_profile.PowerTransformerEnd, end_data)
                    # Star impedance
                    if end.StarImpedance is not None:
                        data = get_data(end.StarImpedance, data_profile.TransformerStarImpedance)
                        end_data['StarImpedance'] = data
                    else:
                        end_data['StarImpedance'] = {}
                    # Mesh impedance
                    end_data['ToMeshImpedance'] = []
                    for impedance in end.ToMeshImpedance:
                        data = get_data(impedance, data_profile.TransformerMeshImpedance)
                        end_data['ToMeshImpedance'].append(data)
                    end_data['FromMeshImpedance'] = []
                    # Mesh impedance
                    for impedance in end.FromMeshImpedance:
                        data = get_data(impedance, data_profile.TransformerMeshImpedance)
                        end_data['FromMeshImpedance'].append(data)
                    # Core admittance
                    if end.CoreAdmittance is not None:
                        data = get_data(end.CoreAdmittance, data_profile.TransformerCoreAdmittance)
                        end_data['CoreAdmittance'] = data
                    else:
                        end_data['CoreAdmittance'] = {}
                    xfmr_data['PowerTransformerEnd'].append(end_data)

                transformer_data[transformer.mRID] = xfmr_data

    return transformer_data