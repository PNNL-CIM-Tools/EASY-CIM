from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cimgraph.data_profile.cimhub_2023 as cim


def get_all_line_data_sparql(container: cim.EquipmentContainer) -> str:
    """ Generates SPARQL query string for a given catalog of objects and feeder id
    Args:
        feeder_mrid (str | Feeder object): The mRID of the feeder or feeder object
        typed_catalog (dict[type, dict[str, object]]): The typed catalog of CIM objects organized by
            class type and object mRID
    Returns:
        query_message: query string that can be used in blazegraph connection or STOMP client
    """

    query_message = """
        PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX cim:  <http://iec.ch/TC57/CIM100#>
        SELECT ?mRID ?name ?BaseVoltage ?Location ?p ?q ?customerCount ?grounded ?phaseConnection ?LoadResponse
            (group_concat(distinct ?Terminal; separator=";") as ?Terminals)
            (group_concat(distinct ?Measurement; separator=";") as ?Measurements)
            (group_concat(distinct ?EnergyConsumerPhase; separator=";") as ?EnergyConsumerPhase)
        WHERE {
          ?eq r:type cim:EnergyConsumer.
          VALUES ?container {"%s"}""" % container.mRID

    # add all attributes
    query_message += """               }
        ?eq cim:Equipment.EquipmentContainer ?fdr.
        ?fdr cim:IdentifiedObject.mRID ?container.

        ?eq cim:IdentifiedObject.mRID ?mRID.
        ?eq cim:IdentifiedObject.name ?name.

        OPTIONAL {?eq cim:ConductingEquipment.BaseVoltage ?bv.
        ?bv cim:IdentifiedObject.mRID ?BaseVoltage.}

        OPTIONAL {?eq cim:PowerSystemResource.Location ?loc.
        ?loc cim:IdentifiedObject.mRID ?Location.}

        ?t cim:Terminal.ConductingEquipment ?eq.
        ?t cim:IdentifiedObject.mRID ?Terminal

        OPTIONAL {?meas cim:Measurement.Terminal ?t.
        ?meas cim:IdentifiedObject.mRID ?meas_id.
        ?meas a ?meas_cls.
        bind(concat(str(?meas_id),",",strafter(str(?meas_cls),"CIM100#")) as ?Measurement).}

        OPTIONAL {?eq cim:EnergyConsumer.p ?p.}
        OPTIONAL {?eq cim:EnergyConsumer.q ?q.}
        OPTIONAL {?eq cim:EnergyConsumer.customerCount ?customerCount.}
        OPTIONAL {?eq cim:EnergyConsumer.grounded ?grounded.}

        OPTIONAL {?eq cim:EnergyConsumer.phaseConnection ?phs.
                  bind(strafter(str(?phs),"PhaseShuntConnectionKind.") as ?phaseConnection) }
        OPTIONAL {?eq cim:EnergyComsumer.LoadResponse ?lr.
                  ?lr cim:IdentifiedObject.mRID ?LoadResponse}
        OPTIONAL {?ecp cim:EnergyConsumerPhase.EnergyConsumer ?eq.
                  ?ecp cim:IdentifiedObject.mRID ?EnergyConsumerPhase.}

        }
        GROUP by ?mRID ?name ?BaseVoltage ?Location ?p ?q ?customerCount ?grounded ?phaseConnection ?LoadResponse
        ORDER by  ?name
        """
    return query_message
