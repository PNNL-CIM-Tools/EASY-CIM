from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ReducedDataProfile():
    def __post_init__(self):
        self.ACLineSegment = [
            'mRID',
            'name',
            'length',
            'r',
            'x',
            'bch',
            'r0',
            'x0',
            'b0ch'
        ]

        self.ACLineSegmentPhase = [
            'name',
            'phase',
            'sequenceNumber'
        ]

        self.CableInfo = [
            "constructionKind",
            "diameterOverCore",
            "diameterOverInsulation",
            "diameterOverJacket",
            "diameterOverScreen",
            "isStrandFill",
            "nominalTemperature",
            "outerJacketKind",
            "relativePermittivity",
            "sheathAsNeutral",
            "shieldMaterial"
        ]

        self.ConcentricNeutralCableInfo = [
            "diameterOverNeutral",
            "neutralStrandCount",
            "neutralStrandGmr",
            "neutralStrandRadius",
            "neutralStrandRDC20"
        ]

        
        self.PhaseImpedanceData = [
            'row',
            'column',
            'r',
            'x',
            'b',
            'g'
        ]

        self.PerLengthPhaseImpedance = [
            'conductorCount'
        ]

        self.PerLengthSequenceImpedance = [
            'name',
            'r',
            'x',
            'bch',
            'gch'
            'r0',
            'x0',
            'b0ch',
            'g0ch'
        ]

        self.PowerElectronicsConnection = [
            'mRID',
            'name',
            'p',
            'q'
        ]

        self.TapeShieldCableInfo = [
            "tapeLap",
            "tapeThickness"
        ]
        
        self.WireInfo = [
            'name',
            'coreRadius',
            'coreStrandCount',
            'gmr',
            'insulated',
            'insulationMaterial',
            'insulationThickness',
            'material',
            'rAC25',
            'rAC50',
            'rAC75',
            'radius',
            'ratedCurrent',
            'rDC20',
            'sizeDescription',
            'strandCount'
        ]