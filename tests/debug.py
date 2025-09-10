import json
import importlib
import os

from cimgraph.databases import ConnectionParameters, XMLFile
from cimgraph.models import FeederModel
import cimgraph.data_profile.cimhub_2023 as cim

os.environ['CIMG_CIM_PROFILE'] = 'cimhub_2023'
os.environ['CIMG_URL'] = 'http://localhost:8889/bigdata/namespace/kb/sparql'
os.environ['CIMG_NAMESPACE'] = 'http://iec.ch/TC57/CIM100#'
os.environ['CIMG_IEC61970_301'] = '8'
os.environ['CIMG_USE_UNITS'] = 'false'

connection = XMLFile(filename='./tests/IEEE13_Assets.xml')

# feeder_mrid = "49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"
feeder_mrid = "5B816B93-7A5F-B64C-8460-47C17D6E4B0F"
feeder = cim.Feeder(mRID = feeder_mrid)
network = FeederModel(connection=connection, container=feeder, distributed=False)

import easycim as easycim

line_data = easycim.get_impedance_data_per_line(network)

geometry_data = easycim.get_geometry_data_per_line(network)

all_line_data = easycim.get_all_data(network, 'ACLineSegment')


geo_data2 = easycim.get_line_data_per_geometry(network)

load_data = easycim.get_load_data(network)
load_data = easycim.get_all_data(network, 'EnergyConsumer')

inverter_data = easycim.get_inverter_data(network)
inverter_data = easycim.get_all_data(network, 'PowerElectronicsConnection')

swing_data = easycim.get_swing_bus_data(network)
swing_data = easycim.get_all_data(network, 'EnergySource')

xfmr_3ph = easycim.get_three_phase_transformer_data(network)
swing_data = easycim.get_all_data(network, 'PowerTransformer')

# impedance per line
line_data = easycim.get_impedance_data_per_line(network)


with open("geometry_per_line.json", "w") as file:
    json.dump(geometry_data, file, indent=4)
    
# geometry per line
geometry_data = easycim.get_geometry_data_per_line(network)

with open("impedance_per_line.json", "w") as file:
    json.dump(line_data, file, indent=4)