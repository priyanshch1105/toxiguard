from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_text = Column(Text, nullable=False)
    clean_text = Column(Text, nullable=False)
    is_toxic = Column(Boolean, nullable=False, default=False)
    moderation_result = Column(String(32), nullable=False)
    toxic = Column(Float, nullable=False, default=0.0)
    severe_toxic = Column(Float, nullable=False, default=0.0)
    obscene = Column(Float, nullable=False, default=0.0)
    threat = Column(Float, nullable=False, default=0.0)
    insult = Column(Float, nullable=False, default=0.0)
    identity_hate = Column(Float, nullable=False, default=0.0)
    max_confidence = Column(Float, nullable=False, default=0.0)
    triggered_labels = Column(Text, nullable=True)
    source = Column(String(64), default="web")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, echo=False, future=True, connect_args=connect_args)
    return engine


def init_db(database_url: str):
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine, SessionLocal
