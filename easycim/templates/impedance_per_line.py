import cimgraph.data_profile.cimhub_ufls as cim
from easycim.templates.graphql_template import template_builder

def create_acline_segment_template_fluent(cim:cim):
    """
    Same template using fluent API
    """
    
    # Build nested templates using fluent API
    phase_impedance_template = (template_builder(cim.PhaseImpedanceData)
                               .field("row")
                               .field("column") 
                               .field("r")
                               .field("x")
                               .field("b")
                               .field("g")
                               .build())
    
    per_length_impedance_template = (template_builder(cim.PerLengthImpedance)
                                   .field("name")
                                   .field("conductorCount")
                                   .nested("PhaseImpedanceData", phase_impedance_template)
                                   .build())
    
    wire_info_template = (template_builder(cim.WireInfo)
                         .build())  # Empty template
    
    acline_segment_phases_template = (template_builder(cim.ACLineSegmentPhase)
                                    .field("phase")
                                    .field("sequenceNumber")
                                    .nested("WireInfo", wire_info_template)
                                    .build())
    
    wire_spacing_info_template = (template_builder(cim.WireSpacingInfo)
                                .build())  # Empty template
    
    # Main template
    acline_segment_template = (template_builder(cim.ACLineSegment)
                             .field("mRID")
                             .field("name") 
                             .field("length")
                             .nested("ACLineSegmentPhases", acline_segment_phases_template)
                             .nested("WireSpacingInfo", wire_spacing_info_template)
                             .nested("PerLengthImpedance", per_length_impedance_template)
                             .filter(mRID="173879C4-4FDB-4521-A60D-5B102B3781B2")
                             .build())
    
    return acline_segment_template

# import logging

# from easycim.data_iterator import get_data
# from easycim.reduced_data_profile import ReducedDataProfile

# cim = ReducedDataProfile


# def line_impedance_template(line: cim.ACLineSegment):
#     data_profile = ReducedDataProfile()
#     data = get_data(line, data_profile.ACLineSegment)
#     # phase data
#     data['ACLineSegmentPhases'] = []
#     for phase in line.ACLineSegmentPhases:
#         data = get_data(phase, data_profile.ACLineSegmentPhase)
#         data['ACLineSegmentPhases'].append(data)

#     # sequence and phase impedance data
#     per_length_impedance = line.PerLengthImpedance
#     data['PerLengthImpedance'] = {}
#     if per_length_impedance is not None:
#         # check if positive/zero sequence impedance data
#         if per_length_impedance.__class__.__name__ == 'PerLengthSequenceImpedance':
#             data = get_data(per_length_impedance,
#                             data_profile.PerLengthSequenceImpedance)
#             data['PerLengthImpedance'] = data
#         # check if phase impedance data
#         elif per_length_impedance.__class__.__name__ == 'PerLengthPhaseImpedance':
#             data = get_data(per_length_impedance,
#                             data_profile.PerLengthPhaseImpedance)
#             data['PerLengthImpedance'] = data
#             data['PerLengthImpedance']['PhaseImpedanceData'] = []
#             for phase_impedance_data in per_length_impedance.PhaseImpedanceData:
#                 data = get_data(phase_impedance_data,
#                                 data_profile.PhaseImpedanceData)
#                 data['PerLengthImpedance']['PhaseImpedanceData'].append(data)
#     return data
