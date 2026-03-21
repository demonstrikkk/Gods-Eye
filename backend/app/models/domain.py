import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime
import enum

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FLAGGED = "FLAGGED"

class RoleType(enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    STRATEGIST = "STRATEGIST"
    MANAGER = "MANAGER"
    WORKER = "WORKER"
    ANALYST = "ANALYST"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    role = Column(Enum(RoleType), default=RoleType.WORKER)
    department = Column(String(100), nullable=True) # E.g., Govt agency handling schemes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks_assigned = relationship("WorkerTask", back_populates="worker")

class Region(Base):
    """
    Geospatial Hierarchy storing State -> District -> Constituency -> Ward -> Booth
    """
    __tablename__ = "regions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True)
    type = Column(String(50)) # 'STATE', 'DISTRICT', 'CONSTITUENCY', 'WARD', 'BOOTH'
    parent_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    
    # Store PostGIS polygonal boundary geometry mapping the region 
    # Use generic GEOMETRY for safety, or POLYGON. SRID 4326 is standard GPS coordinates.
    boundary = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=True)
    center_point = Column(Geometry('POINT', srid=4326), nullable=True)
    
    # Pre-calculated aggregations for quick dashboard loading
    demographics = Column(JSONB, default={}) # { "youth": 40, "women": 50 }
    sentiment_score = Column(Float, nullable=True) # 0 to 100
    
    children = relationship("Region", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Region", back_populates="children", remote_side=[id])
    schemes_active = relationship("SchemeRegionMapping", back_populates="region")
    projects = relationship("Project", back_populates="region")

class Scheme(Base):
    """ Government or Civic Scheme details """
    __tablename__ = "schemes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True)
    description = Column(String)
    eligibility_criteria = Column(JSONB) # Storing structured eligibility attributes
    total_budget = Column(Float, nullable=True)
    
    regions_mapped = relationship("SchemeRegionMapping", back_populates="scheme")

class SchemeRegionMapping(Base):
    """ M2M Association Table for Scheme Penetration Metrics """
    __tablename__ = "scheme_region_mappings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("schemes.id"))
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))
    beneficiary_count = Column(Integer, default=0)
    target_count = Column(Integer, nullable=True)

    scheme = relationship("Scheme", back_populates="regions_mapped")
    region = relationship("Region", back_populates="schemes_active")

class Project(Base):
    """ Project Accountability (Roads, Infrastructure) """
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))
    location = Column(Geometry('POINT', srid=4326))
    status = Column(String(50)) # 'PROPOSED', 'ONGOING', 'COMPLETED'
    budget = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    before_image_url = Column(String, nullable=True)
    after_image_url = Column(String, nullable=True)
    
    region = relationship("Region", back_populates="projects")

class WorkerTask(Base):
    """ Field Operations Tracking """
    __tablename__ = "worker_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))
    task_type = Column(String(100)) # 'SURVEY', 'AWARENESS', 'ISSUE_VERIFICATION'
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Store exact location check-in of the worker when submitting the task
    check_in_location = Column(Geometry('POINT', srid=4326), nullable=True)
    field_notes = Column(String, nullable=True)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    worker = relationship("User", back_populates="tasks_assigned")
    region = relationship("Region")
