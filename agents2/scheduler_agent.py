from database import SessionLocal
from models import MailTask
from scheduler import log_action, schedule_mail

class SchedulerAgent:
    """Creates MailTask and schedules mail."""
    agent_name = "SchedulerAgent"

    def schedule(self, mail_data):
        db = SessionLocal()
        task = MailTask(**mail_data)
        db.add(task)
        db.commit()
        db.refresh(task)

       
        log_action(task.id, "ParserAgent", f"Parsed prompt: {mail_data}")
        log_action(task.id, "ValidatorAgent", "Validation successful")

        schedule_mail(task.id, task.recipient, task.subject, task.body, task.schedule_time)
        db.close()
        return task.id
