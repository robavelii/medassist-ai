from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class LLMCache(Base):
    __tablename__ = "llm_cache"

    id = Column(String(64), primary_key=True, index=True)
    structured_prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_name = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    patient_id = Column(String(64), nullable=True, index=True)
    visit_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
