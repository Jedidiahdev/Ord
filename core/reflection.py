from dataclasses import asdict, dataclass
from typing import Dict


@dataclass
class StructuredReflection:
    task_id: str
    agent_id: str
    objective: str
    outcome: str
    what_worked: str
    what_failed: str
    next_improvement: str
    intelligence_score: float

    def to_payload(self) -> Dict[str, str]:
        return asdict(self)
