import json
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.db.database import Base, get_engine, get_session_factory


class EvalLogORM(Base):
    __tablename__ = "eval_logs"

    trace_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    intent = Column(String, default="")
    response = Column(Text, default="")
    contexts_json = Column(Text, default="[]")       # list[str] serialized
    trajectory_json = Column(Text, default="[]")     # list[dict] serialized
    user_feedback = Column(Integer, nullable=True)   # 1=赞, -1=踩, None=未反馈
    eval_metrics_json = Column(Text, nullable=True)  # dict serialized
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalLogRepo:
    def __init__(self):
        Base.metadata.create_all(bind=get_engine())
        self._Session = get_session_factory()

    def save(
        self,
        trace_id: str,
        user_id: str,
        query: str,
        intent: str,
        response: str,
        contexts: list[str],
        trajectory: list[dict],
    ) -> None:
        with self._Session() as session:
            row = EvalLogORM(
                trace_id=trace_id,
                user_id=user_id,
                query=query,
                intent=intent,
                response=response,
                contexts_json=json.dumps(contexts, ensure_ascii=False),
                trajectory_json=json.dumps(trajectory, ensure_ascii=False),
                created_at=datetime.utcnow(),
            )
            session.merge(row)
            session.commit()

    def query_by_date(self, date_str: str) -> list[dict]:
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1)
        with self._Session() as session:
            rows = session.query(EvalLogORM).filter(
                EvalLogORM.created_at >= start,
                EvalLogORM.created_at < end,
            ).all()
            return [self._to_dict(r) for r in rows]

    def query_recent(self, days: int) -> list[dict]:
        since = datetime.utcnow() - timedelta(days=days)
        with self._Session() as session:
            rows = session.query(EvalLogORM).filter(
                EvalLogORM.created_at >= since,
            ).all()
            return [self._to_dict(r) for r in rows]

    def update_metrics(self, trace_id: str, metrics: dict) -> None:
        with self._Session() as session:
            row = session.get(EvalLogORM, trace_id)
            if row:
                row.eval_metrics_json = json.dumps(metrics, ensure_ascii=False)
                session.commit()

    def update_feedback(self, trace_id: str, feedback: int) -> None:
        with self._Session() as session:
            row = session.get(EvalLogORM, trace_id)
            if row:
                row.user_feedback = feedback
                session.commit()

    @staticmethod
    def _to_dict(row: EvalLogORM) -> dict:
        return {
            "trace_id": row.trace_id,
            "user_id": row.user_id,
            "query": row.query,
            "intent": row.intent,
            "response": row.response,
            "contexts_json": row.contexts_json,
            "trajectory_json": row.trajectory_json,
            "user_feedback": row.user_feedback,
            "eval_metrics_json": row.eval_metrics_json,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
