import gdm.distribution.equipment as gdm
import cimgraph.data_profile.cim17v40 as cim
from cimgraph.models import GraphModel
from easycim.registry import register_converter

@register_converter(gdm.BareConductorEquipment)
def convert_bare_conductor(conductor:gdm.BareConductorEquipment, network:GraphModel=None) -> cim.OverheadWireInfo:
    """Convert a GDM BareConductorEquipment to CIM WireInfo."""
    wire_info = cim.OverheadWireInfo(identifier = conductor.uuid)
    wire_info.name = conductor.name
    wire_info.gmr = cim.Length(value = conductor.conductor_gmr.magnitude,
                              input_unit = conductor.conductor_gmr.units)
    wire_info.radius = cim.Length(value = conductor.conductor_diameter.magnitude/2,
                                 input_unit = conductor.conductor_diameter.units)
    wire_info.ratedCurrent = cim.CurrentFlow(value = conductor.ampacity.magnitude,
                                            input_unit = conductor.ampacity.units)
    wire_info.rDC20 = cim.ResistancePerLength(value = conductor.dc_resistance.magnitude,
                                            input_unit = conductor.dc_resistance.units)
    wire_info.rAC25 = cim.ResistancePerLength(value = conductor.ac_resistance.magnitude,
                                            input_unit = conductor.ac_resistance.units)

    if network is not None:
        network.add_to_graph(wire_info)
        
    return wire_info