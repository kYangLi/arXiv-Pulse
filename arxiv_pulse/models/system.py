import json

from sqlalchemy import Column, DateTime, Integer, String, Text

from arxiv_pulse.models.base import Base, utcnow


class SyncTask(Base):
    __tablename__ = "sync_tasks"

    id = Column(String(36), primary_key=True)
    task_type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    message = Column(Text)
    result = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "message": self.message,
            "result": json.loads(self.result) if self.result else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<SyncTask(id={self.id}, type={self.task_type}, status={self.status})>"


class RecentResult(Base):
    __tablename__ = "recent_results"

    id = Column(Integer, primary_key=True)
    days_back = Column(Integer, default=7)
    paper_ids = Column(Text)
    total_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "days_back": self.days_back,
            "paper_ids": json.loads(self.paper_ids) if self.paper_ids else [],
            "total_count": self.total_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<RecentResult(id={self.id}, days_back={self.days_back}, count={self.total_count})>"


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(500))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value[:20] if self.value else None}...)>"
