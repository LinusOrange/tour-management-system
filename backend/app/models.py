import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # 新增：判断是否为管理员
    is_admin = Column(Boolean, default=False)


class Location(Base):
    """地点表：存储研学基地的基础物理信息"""
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)
    # 存储经纬度，格式：{"lat": 39.9, "lng": 116.4}
    coordinates = Column(JSONB, nullable=True)
    # 标签，如 ["博物馆", "科技类"]
    tags = Column(JSONB, server_default='[]')
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 核心修复点 1：增加所有者 ID，解决 AttributeError 错误
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 关联关系
    activities = relationship("AtomicActivity", back_populates="location", cascade="all, delete-orphan")
    owner = relationship("User")

class AtomicActivity(Base):
    """原子活动积木表：存储教学单元"""
    __tablename__ = "atomic_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    title = Column(String(255), nullable=False)
    duration = Column(Integer, default=60) 
    content = Column(Text, nullable=True)
    edu_goals = Column(JSONB, server_default='{}')
    cost_metadata = Column(JSONB, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 核心修复点 2：确保积木也强制关联用户，且不可为空
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 关联关系
    location = relationship("Location", back_populates="activities")
    owner = relationship("User")

class Itinerary(Base):
    """行程方案表：存储生成的排产计划"""
    __tablename__ = "itineraries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 核心修复点 3：行程方案也需要隔离，防止用户看到别人的排产计划
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 关联关系
    items = relationship("ItineraryItem", back_populates="itinerary", cascade="all, delete-orphan")
    owner = relationship("User")

class ItineraryItem(Base):
    """行程项：积木在方案中的实例化"""
    __tablename__ = "itinerary_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id"))
    activity_id = Column(UUID(as_uuid=True), ForeignKey("atomic_activities.id"))
    sequence = Column(Integer) # 顺序
    scheduled_time = Column(DateTime, nullable=True) # 具体开始时间
    
    itinerary = relationship("Itinerary", back_populates="items")
    activity = relationship("AtomicActivity")