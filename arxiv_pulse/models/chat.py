import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from arxiv_pulse.models.base import Base, utcnow


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    paper_ids = Column(Text)
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "paper_ids": json.loads(self.paper_ids) if self.paper_ids else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"
