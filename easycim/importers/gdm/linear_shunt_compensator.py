import gdm.distribution.equipment as gdm
import gdm.distribution.enums as gdm_enum
import cimgraph.data_profile.cim17v40 as cim
from cimgraph.models import GraphModel
from easycim.registry import register_converter
import math

@register_converter(gdm.CapacitorEquipment)
def convert_capacitor_equipment(capacitor: gdm.CapacitorEquipment, network: GraphModel = None) -> cim.LinearShuntCompensator:
    """Convert a GDM CapacitorEquipment to CIM LinearShuntCompensator with phase components."""
    # Create the main LinearShuntCompensator
    shunt_comp = cim.LinearShuntCompensator(identifier=capacitor.uuid)
    shunt_comp.name = capacitor.name
    
    # Map voltage information
    shunt_comp.nomU = cim.Voltage(value=capacitor.rated_voltage.magnitude,
                                 input_unit=capacitor.rated_voltage.units)
    
    # Map connection type to phase connection
    connection_map = {
        gdm_enum.ConnectionType.STAR: cim.PhaseShuntConnectionKind.Yn,
        gdm_enum.ConnectionType.DELTA: cim.PhaseShuntConnectionKind.D,
        gdm_enum.ConnectionType.OPEN_STAR: cim.PhaseShuntConnectionKind.Y,
        gdm_enum.ConnectionType.OPEN_DELTA: cim.PhaseShuntConnectionKind.D,
        gdm_enum.ConnectionType.ZIG_ZAG: cim.WindingConnection.Z
        # TODO: Add cim.PhaseShuntConnectionKind.Z to EAP profile
    }
    if capacitor.connection_type in connection_map:
        shunt_comp.phaseConnection = connection_map[capacitor.connection_type]
    
    # Set grounding based on connection type
    shunt_comp.grounded = (capacitor.connection_type == gdm_enum.ConnectionType.STAR)
    
    # Calculate total sections and admittance from phase capacitors
    total_sections = sum(phase_cap.num_banks for phase_cap in capacitor.phase_capacitors)
    total_reactive_power = sum(phase_cap.rated_reactive_power.magnitude for phase_cap in capacitor.phase_capacitors)
    
    shunt_comp.maximumSections = total_sections
    shunt_comp.normalSections = sum(phase_cap.num_banks_on for phase_cap in capacitor.phase_capacitors)
    shunt_comp.sections = float(shunt_comp.normalSections)
    
    # Calculate susceptance per section (B = Q / (V^2))
    if total_sections > 0 and capacitor.rated_voltage.magnitude > 0:
        voltage_squared = capacitor.rated_voltage.magnitude ** 2
        total_susceptance = total_reactive_power / voltage_squared
        shunt_comp.bPerSection = cim.Susceptance(value=total_susceptance / total_sections,
                                                input_unit="siemens")
        
        # Calculate conductance per section from resistance
        total_conductance = 0
        for phase_cap in capacitor.phase_capacitors:
            if phase_cap.resistance.magnitude > 0:
                total_conductance += 1.0 / phase_cap.resistance.magnitude
        
        if total_conductance > 0:
            shunt_comp.gPerSection = cim.Conductance(value=total_conductance / total_sections,
                                                   input_unit="siemens")
    
    # Create individual phase components
    phase_map = {
        0: cim.SinglePhaseKind.A,
        1: cim.SinglePhaseKind.B, 
        2: cim.SinglePhaseKind.C
    }
    
    for i, phase_cap in enumerate(capacitor.phase_capacitors):
        phase_comp = cim.LinearShuntCompensatorPhase(identifier=f"{capacitor.uuid}_phase_{i}")
        phase_comp.name = f"{capacitor.name}_Phase_{i+1}"
        
        # Set phase
        if i in phase_map:
            phase_comp.phase = phase_map[i]
        
        # Set section information
        phase_comp.maximumSections = phase_cap.num_banks
        phase_comp.normalSections = phase_cap.num_banks_on
        phase_comp.sections = float(phase_cap.num_banks_on)
        
        # Calculate per-phase admittance values
        if phase_cap.num_banks > 0 and capacitor.rated_voltage.magnitude > 0:
            voltage_squared = capacitor.rated_voltage.magnitude ** 2
            phase_susceptance = phase_cap.rated_reactive_power.magnitude / voltage_squared
            phase_comp.bPerSection = cim.Susceptance(value=phase_susceptance / phase_cap.num_banks,
                                                   input_unit="siemens")
            
            if phase_cap.resistance.magnitude > 0:
                phase_conductance = 1.0 / phase_cap.resistance.magnitude
                phase_comp.gPerSection = cim.Conductance(value=phase_conductance / phase_cap.num_banks,
                                                       input_unit="siemens")
        
        # Set up bidirectional relationship
        phase_comp.ShuntCompensator = shunt_comp
        shunt_comp.ShuntCompensatorPhase.append(phase_comp)
        
        if network is not None:
            network.add_to_graph(phase_comp)
    
    if network is not None:
        network.add_to_graph(shunt_comp)
        
    return shunt_comp