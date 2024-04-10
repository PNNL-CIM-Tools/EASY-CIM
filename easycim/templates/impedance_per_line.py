import logging

from easycim.data_iterator import get_data
from easycim.reduced_data_profile import ReducedDataProfile
cim = ReducedDataProfile

def line_impedance_template(line:cim.ACLineSegment):
    data_profile = ReducedDataProfile()
    data = get_data(line, data_profile.ACLineSegment)
    # phase data
    data['ACLineSegmentPhases'] = []
    for phase in line.ACLineSegmentPhases:
        data = get_data(phase, data_profile.ACLineSegmentPhase)
        data['ACLineSegmentPhases'].append(data)

    # sequence and phase impedance data
    per_length_impedance = line.PerLengthImpedance
    data['PerLengthImpedance'] = {}
    if per_length_impedance is not None:
        # check if positive/zero sequence impedance data
        if per_length_impedance.__class__.__name__ == 'PerLengthSequenceImpedance':
            data = get_data(per_length_impedance, data_profile.PerLengthSequenceImpedance)
            data['PerLengthImpedance'] = data
        # check if phase impedance data
        elif per_length_impedance.__class__.__name__ == 'PerLengthPhaseImpedance':
            data = get_data(per_length_impedance, data_profile.PerLengthPhaseImpedance)
            data['PerLengthImpedance'] = data
            data['PerLengthImpedance']['PhaseImpedanceData'] = []
            for phase_impedance_data in per_length_impedance.PhaseImpedanceData:
                data = get_data(phase_impedance_data, data_profile.PhaseImpedanceData)
                data['PerLengthImpedance']['PhaseImpedanceData'].append(data)
    return data