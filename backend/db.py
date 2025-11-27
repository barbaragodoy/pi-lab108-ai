# backend/db.py
from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine

DATABASE_URL = "sqlite:///./smarttwin.db"
engine = create_engine(DATABASE_URL, echo=False)


class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Tempo
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Variável de processo
    value_real: float
    value_pred: Optional[float] = None
    residual: Optional[float] = None
    zscore_residual: Optional[float] = None
    iforest_score: Optional[float] = None
    is_anomaly: Optional[bool] = None

    # Decisão de amostragem
    sampling_level: Optional[str] = None

    # Origem do dado (simulator, upload, etc.)
    source: str = "simulator"

    # 🔹 Metadados do processo (absorvendo campos do CSV)
    product: Optional[str] = None
    operation: Optional[str] = None
    variable: Optional[str] = None
    machine: Optional[str] = None
    section: Optional[str] = None
    operator: Optional[str] = None
    sample_id: Optional[int] = None


class DailyCep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    day: date
    n: int
    mean: Optional[float] = None
    std: Optional[float] = None
    r: Optional[float] = None
    cp: Optional[float] = None
    cpk: Optional[float] = None
    lsl: Optional[float] = None
    usl: Optional[float] = None


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    level: str
    message: str
    meta: Optional[str] = None


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
