from database import SessionLocal
from models import Log

class ReporterAgent:
    """Fetches logs for a mail task."""
    agent_name = "ReporterAgent"

    def get_logs(self, mail_id):
        db = SessionLocal()
        logs = db.query(Log).filter(Log.mail_id == mail_id).all()
        db.close()
        return [
            {"agent": log.agent, "message": log.message, "time": log.timestamp}
            for log in logs
        ]
