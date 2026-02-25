from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

DATABASE_URL = "sqlite:///./research.db"

Base = declarative_base()

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    scraped_contents = relationship("ScrapedContent", back_populates="session")

class ScrapedContent(Base):
    __tablename__ = "scraped_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    url = Column(String)
    title = Column(String, nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ResearchSession", back_populates="scraped_contents")
