from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ReducedDataProfile():
    def __post_init__(self):
        self.IdentifiedObject = [
            'mRID',
            'name'
        ]

        self.ACLineSegment = [
            'length',
            'r',
            'x',
            'bch',
            'r0',
            'x0',
            'b0ch'
        ]

        self.ACLineSegmentPhase = [
            'phase',
            'sequenceNumber'
        ]

        self.BatteryUnit =[
            'batteryState',
            'ratedE',
            'storedE'
        ]

        self.CableInfo = [
            'constructionKind',
            'diameterOverCore',
            'diameterOverInsulation',
            'diameterOverJacket',
            'diameterOverScreen',
            'isStrandFill',
            'nominalTemperature',
            'outerJacketKind',
            'relativePermittivity',
            'sheathAsNeutral',
            'shieldMaterial'
        ]

        self.ConcentricNeutralCableInfo = [
            'diameterOverNeutral',
            'neutralStrandCount',
            'neutralStrandGmr',
            'neutralStrandRadius',
            'neutralStrandRDC20'
        ]

        self.EnergyConsumer = [
            'p',
            'q',
            'customerCount',
            'grounded',
            'phaseConnection'
        ]

        self.EnergyConsumerPhase = [
            'p',
            'q',
            'phase'
        ]

        self.EnergySource = [
            "r",
            "r0",
            "x",
            "x0",
            "nominalVoltage",
            "voltageMagnitude",
            "voltageAngle"
        ]

        self.EnergySourcePhase = [
            'phase'
        ]

        self.House = [
            'coolingSetpoint',
            'coolingSystem',
            'floorArea',
            'heatingSetpoint',
            'heatingSystem',
            'hvacPowerFactor',
            'numberOfStories'
        ]

        self.NoLoadTest = [
            "energisedEndVoltage",
            "excitingCurrent",
            "excitingCurrentZero",
            "loss",
            "lossZero"
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
            'name',
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
            'p',
            'q',
            'minQ',
            'maxQ',
            'ratedS',
            'ratedU',
            'maxIFault'
        ]

        self.PowerElectronicsConnectionPhase = [
            'p',
            'q',
            'phase'
        ]

        self.PowerElectronicsUnit =[
            'minP',
            'maxP'
        ]

        self.PowerTransformer = [
            'vectorGroup'
        ]

        self.PowerTransformerEnd = [
            "connectionKind",
            "phaseAngleClock",
            "ratedS",
            "ratedU",
            'r',
            'x',
            'b',
            'g'
            'r0',
            'x0',
            'b0',
            'g0'
        ]

        self.ShortCircuitTest = [
            "energisedEndStep",
            "groundedEndStep",
            "leakageImpedance",
            "leakageImpedanceZero",
            "loss",
            "lossZero"
        ]

        

        self.TapeShieldCableInfo = [
            'tapeLap',
            'tapeThickness'
        ]

        self.Terminal = [
            'sequenceNumber'
        ]


        self.TransformerEnd = [
            "endNumber",
            "grounded",
            "rground",
            "xground",
            'bmagSat',
            'magBaseU',
            'magSatFlux'
        ]

        self.TransformerEndInfo = [
            "connectionKind",
            "emergencyS",
            "endNumber",
            "insulationU",
            "phaseAngleClock",
            "r",
            "ratedS",
            "ratedU",
            "shortTermS"
        ]

        self.TransformerMeshImpedance = [
            'r',
            'x',
            'r0',
            'x0'
        ]
        
        self.TransformerCoreAdmittance = [
            'b',
            'g',
            'b0',
            'g0'
        ]

        self.TransformerStarImpedance = [
            'r',
            'x',
            'r0',
            'x0'
        ]

        self.TransformerTank = []



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

        self.WirePosition = [
            'sequenceNumber',
            'xCoord',
            'yCoord'
        ]

        self.WireSpacingInfo = [
            'isCable',
            'phaseWireCount',
            'phaseWireSpacing',
            'usage'
        ]