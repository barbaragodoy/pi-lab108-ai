# backend/services/datastore.py
from typing import List

from sqlalchemy import delete
from sqlmodel import Session, select

from ..db import engine, Measurement, DailyCep, Alert


def add_measurement(m: Measurement) -> Measurement:
    with Session(engine) as session:
        session.add(m)
        session.commit()
        session.refresh(m)
        return m


def get_last_measurements(limit: int = 200) -> List[Measurement]:
    with Session(engine) as session:
        stmt = select(Measurement).order_by(Measurement.timestamp.desc()).limit(limit)
        rows = session.exec(stmt).all()
        return list(reversed(rows))


def get_all_measurements() -> List[Measurement]:
    with Session(engine) as session:
        stmt = select(Measurement).order_by(Measurement.timestamp.asc())
        return session.exec(stmt).all()


def clear_daily_cep() -> None:
    with Session(engine) as session:
        stmt = delete(DailyCep)
        session.exec(stmt)
        session.commit()


def save_daily_cep(rows: List[DailyCep]) -> None:
    with Session(engine) as session:
        stmt = delete(DailyCep)
        session.exec(stmt)
        for r in rows:
            session.add(r)
        session.commit()


def get_daily_cep() -> List[DailyCep]:
    with Session(engine) as session:
        stmt = select(DailyCep).order_by(DailyCep.day.asc())
        return session.exec(stmt).all()


def add_alert(level: str, message: str, meta: str | None = None) -> Alert:
    a = Alert(level=level, message=message, meta=meta)
    with Session(engine) as session:
        session.add(a)
        session.commit()
        session.refresh(a)
        return a


def get_alerts(limit: int = 100) -> List[Alert]:
    with Session(engine) as session:
        stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
        return session.exec(stmt).all()
