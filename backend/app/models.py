import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Shop(Base):
    __tablename__ = "shops"

    shop_id = Column(String(36), primary_key=True, default=generate_uuid)
    shop_name = Column(String(255), nullable=False)
    device_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    jobs = relationship("Job", back_populates="shop", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True, default=generate_uuid)
    shop_id = Column(String(36), ForeignKey("shops.shop_id"), nullable=False)
    status = Column(String(20), nullable=False, default="UPLOADED")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    shop = relationship("Shop", back_populates="jobs")
    documents = relationship(
        "Document", back_populates="job", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    document_type = Column(String(50), nullable=True, default="unknown")
    input_path = Column(Text, nullable=False)
    output_path = Column(Text, nullable=True)
    preview_path = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="UPLOADED")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    job = relationship("Job", back_populates="documents")
