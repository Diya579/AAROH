from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class DistressStateCreate(BaseModel):
    case_id: int
    observation_date: datetime
    distress_score: Optional[float] = None
    trajectory: Optional[str] = None
    confidence: Optional[float] = None
