import json

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from arxiv_pulse.models.base import Base, utcnow


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#409EFF")
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Collection(id={self.id}, name={self.name})>"


class CollectionPaper(Base):
    __tablename__ = "collection_papers"

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    notes = Column(Text)
    tags = Column(String(500))
    read_status = Column(String(20), default="unread")
    starred = Column(Boolean, default=False)
    added_at = Column(DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "paper_id": self.paper_id,
            "notes": self.notes,
            "tags": json.loads(self.tags) if self.tags else [],
            "read_status": self.read_status,
            "starred": self.starred,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }

    def __repr__(self):
        return f"<CollectionPaper(collection_id={self.collection_id}, paper_id={self.paper_id})>"
