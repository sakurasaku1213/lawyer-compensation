from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CaseData:
    case_id: str
    client_name: str
    accident_date: str # Consider using datetime.date for internal representation later
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
