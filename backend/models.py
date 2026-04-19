from typing import List, Literal
from pydantic import BaseModel


class Assumption(BaseModel):
    variable: str
    value: str
    source: str
    raw_tool_call: str = ""


class AgentOutput(BaseModel):
    recommendation: str
    assumptions: List[Assumption]
    source: str


class Stage1Output(BaseModel):
    agent_a: AgentOutput
    agent_b: AgentOutput


DivergenceType = Literal["data_conflict", "missing_var", "horizon_mismatch", "agreed"]


class AssumptionRow(BaseModel):
    variable: str
    agent_a_value: str
    agent_a_source: str
    agent_b_value: str
    agent_b_source: str
    divergence_type: DivergenceType
    is_crux: bool


class ForensicsOutput(BaseModel):
    assumption_table: List[AssumptionRow]
    divergence_type: str
    finding: str
    crux_variable: str


Verdict = Literal["outlier", "aligned", "unverifiable"]


class GroundedAssumption(BaseModel):
    variable: str
    agent_a_value: str
    agent_b_value: str
    market_benchmark: str
    verdict: Verdict
    source_url: str
    source_name: str
    note: str


class GroundingOutput(BaseModel):
    grounded_assumptions: List[GroundedAssumption]


class OutcomePath(BaseModel):
    name: str
    description: str
    success_condition: str
    failure_condition: str
    recommended: bool


class SimulationOutput(BaseModel):
    path_a: OutcomePath
    path_b: OutcomePath
    hybrid: OutcomePath


class AuditEntry(BaseModel):
    claim: str
    source_url: str
    source_name: str


class BriefOutput(BaseModel):
    headline: str = ""
    context: str
    divergence_finding: str
    recommended_decision: str
    rationale: str
    dissenting_opinion: str
    trigger_conditions: List[str]
    audit_log: List[AuditEntry]
