### Long form code for the Switch data

### For Swing bus data
import importlib
import logging

from cimgraph.models import GraphModel

from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile

cim = ReducedDataProfile

_log = logging.getLogger(__name__)

from cimgraph.databases import ConnectionParameters, BlazegraphConnection, XMLFile
from cimgraph.models import FeederModel

cim_profile = 'cimhub_2023'
cim = importlib.import_module('cimgraph.data_profile.' + cim_profile)

params = ConnectionParameters(filename="IEEE13_Assets.xml", cim_profile='cimhub_2023', iec61970_301=8)
rdf = XMLFile(params)

#feeder_mrid = "49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"
feeder_mrid = 'CBE09B55-091B-4BB0-95DA-392237B12640'
# feeder_mrid = '6DEF3353-8276-402F-AC8E-3DEF4A396FFE'

feeder = cim.Feeder(mRID = feeder_mrid)
network = FeederModel(connection=rdf, container=feeder, distributed=False)

data_profile = ReducedDataProfile()
cim_profile = network.connection.connection_params.cim_profile
cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')



data_profile = ReducedDataProfile()
cim_profile = network.connection.connection_params.cim_profile
cim = importlib.import_module(f'cimgraph.data_profile.{cim_profile}')
# Run network queries
network.get_all_edges(cim.Breaker)
# network.get_all_edges(cim.EnergySourcePhase)

def source_iterator(Breaker_var: cim.Breaker) -> dict:
    """Iterator method to extract phase data for an EnergySource object

    :param energy_source: An instance of EnergySource or any of its child classes
    :type energy_source: cim.EnergySource
    :return: an EnergySource dictionaries
    :rtype: dict
    """
    data_profile = ReducedDataProfile()
    source_data = get_data(Breaker_var, data_profile.Breaker_var)
    # source_data['phases'] = []
    # for phase in energy_source.EnergySourcePhase:
    #     phase_data = get_data(phase, data_profile.EnergySourcePhase)
    #     source_data['phases'].append(phase_data)
    return source_data

source_data = {}
if cim.Breaker in network.graph:
    print('Flag')
    for source in network.graph[cim.Breaker].values():
        source_data[source.mRID] = source_iterator(source)

# print(source_data.keys())
# print('\n')
# print(source_data.values())

print(source_data)
print(len(network.graph[cim.ACLineSegment]))

