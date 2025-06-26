import gdm.distribution.equipment as gdm
import cimgraph.data_profile.cim17v40 as cim
from cimgraph.models import GraphModel
from easycim.registry import register_converter

@register_converter(gdm.ConcentricCableEquipment)
def convert_bare_conductor(conductor:gdm.ConcentricCableEquipment, network:GraphModel=None) -> cim.ConcentricNeutralCableInfo:
    """Convert a GDM ConcentricCableEquipment to CIM ConcentricNeutralCableInfo."""
    cable_info = cim.ConcentricNeutralCableInfo(identifier = conductor.uuid)
    cable_info.name = conductor.name
    cable_info.insulated = True
    cable_info.gmr = cim.Length(value = conductor.conductor_gmr.magnitude,
                              input_unit = conductor.conductor_gmr.units)
    cable_info.radius = cim.Length(value = conductor.conductor_diameter.magnitude/2,
                                 input_unit = conductor.conductor_diameter.units)
    cable_info.ratedCurrent = cim.CurrentFlow(value = conductor.ampacity.magnitude,
                                            input_unit = conductor.ampacity.units)
    cable_info.diameterOverInsulation = cim.Length(value = conductor.insulation_diameter.magnitude,
                                                    input_unit = conductor.insulation_diameter.units)
    cable_info.insulationThickness = cim.Length(value = conductor.insulation_thickness.magnitude,
                                                input_unit = conductor.insulation_thickness.units)
    cable_info.rAC25 = cim.ResistancePerLength(value = conductor.phase_ac_resistance.magnitude,
                                                input_unit = conductor.phase_ac_resistance.units)
    cable_info.neutralStrandCount = conductor.num_neutral_strands
    cable_info.neutralStrandGmr = cim.Length(value = conductor.strand_gmr.magnitude,
                                       input_unit = conductor.strand_gmr.units)
    cable_info.neutralStrandRadius = cim.Length(value = conductor.strand_diameter.magnitude/2,
                                           input_unit = conductor.strand_diameter.units)
    #TODO: Add conversion of CIM 18 extension classes
    # cable_info.ratedVoltage = cim.Voltage(value = conductor.rated_voltage.magnitude,
    #                                             input_unit = conductor.rated_voltage.units)

    if network is not None:
        network.add_to_graph(cable_info)
        
    return cable_info