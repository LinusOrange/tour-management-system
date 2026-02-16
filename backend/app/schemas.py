from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

# --- Location Schemas ---
class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    tags: List[str] = []
    description: Optional[str] = None

class LocationCreate(LocationBase):
    pass  # 创建时需要的字段

class LocationRead(LocationBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True # 允许从 SQLAlchemy 模型自动转换

# --- Activity Schemas ---
class ActivityBase(BaseModel):
    title: str
    duration: int = Field(gt=0, description="时长必须大于0分钟")
    content: Optional[str] = None
    edu_goals: Dict[str, str] = {}
    cost_metadata: Dict[str, float] = {}

class ActivityCreate(ActivityBase):
    location_id: UUID

class ActivityRead(ActivityBase):
    id: UUID
    location_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class MegaIngestRequest(BaseModel):
    raw_text: str

class MegaIngestResponse(BaseModel):
    location: LocationRead
    activities: List[ActivityRead]