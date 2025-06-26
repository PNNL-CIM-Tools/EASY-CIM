import gdm.distribution.equipment as gdm
import cimgraph.data_profile.cim17v40 as cim
from cimgraph.models import GraphModel
from easycim.registry import register_converter

@register_converter(gdm.BatteryEquipment)
def convert_battery_equipment(battery: gdm.BatteryEquipment, network: GraphModel = None) -> cim.BatteryUnit:
    """Convert a GDM BatteryEquipment to CIM BatteryUnit with PowerElectronicsConnection."""
    # Create the BatteryUnit
    battery_unit = cim.BatteryUnit(identifier=battery.uuid)
    battery_unit.name = battery.name
    
    # Map rated energy capacity
    battery_unit.ratedE = cim.RealEnergy(value=battery.rated_energy.magnitude,
                                        input_unit=battery.rated_energy.units)
    
    # Map rated power to maxP (assuming rated_power represents maximum capacity)
    battery_unit.maxP = cim.ActivePower(value=battery.rated_power.magnitude,
                                       input_unit=battery.rated_power.units)
    
    # Set minP to negative of maxP for bidirectional operation (charging/discharging)
    battery_unit.minP = cim.ActivePower(value=-battery.rated_power.magnitude,
                                       input_unit=battery.rated_power.units)
    
    # Create the PowerElectronicsConnection
    connection = cim.PowerElectronicsConnection(identifier=f"{battery.uuid}_connection")
    connection.name = f"{battery.name}_Connection"
    
    # Map voltage information to the connection
    connection.ratedU = cim.Voltage(value=battery.rated_voltage.magnitude,
                                   input_unit=battery.rated_voltage.units)
    
    # Map power ratings to the connection as well
    connection.ratedS = cim.ApparentPower(value=battery.rated_power.magnitude,
                                     input_unit=battery.rated_power.units)
    
  
    # Set up the bidirectional relationship between BatteryUnit and PowerElectronicsConnection
    battery_unit.PowerElectronicsConnection = connection
    connection.PowerElectronicsUnit = [battery_unit]  # This is typically a list
    
    # Note: efficiency values (charging_efficiency, discharging_efficiency, idling_efficiency)
    # would typically be handled through operational curves or additional CIM objects
    
    #TODO: Add conversion of extension classes
    #TODO: batteryUnit.chargingEfficiency
    #TODO: batteryUnit.dischargingEfficiency
    #TODO: batteryUnit.idlingP
    
    # Note: voltage_type (line-to-line vs line-to-neutral) might require additional
    # configuration at the connection or terminal level
    
    if network is not None:
        ratedU = battery.rated_voltage.magnitude
        base_voltage = network.find_by_attribute(cim_class=cim.BaseVoltage, attribute="nominalVoltage", value=ratedU)
        if base_voltage:
            connection.BaseVoltage = base_voltage[0]
        else:
            # If no matching BaseVoltage found, create a new one
            base_voltage = cim.BaseVoltage(name = f'base_voltage_{ratedU}')
            base_voltage.nominalVoltage = ratedU
            # base_voltage.nominalVoltage = cim.Voltage(value=battery.rated_voltage.magnitude,
            #                                           input_unit=battery.rated_voltage.units)
            network.add_to_graph(base_voltage)
            connection.BaseVoltage = base_voltage
        network.add_to_graph(battery_unit)
        network.add_to_graph(connection)
        
    return battery_unit