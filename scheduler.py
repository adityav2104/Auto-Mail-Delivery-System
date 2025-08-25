from apscheduler.schedulers.background import BackgroundScheduler
from email_utils import send_email
from database import SessionLocal
from models import MailTask, Log

scheduler = BackgroundScheduler()
scheduler.start()


def log_action(mail_id, agent, message):
    """Logs actions for any agent."""
    if mail_id is None:
        return  
    db = SessionLocal()
    new_log = Log(mail_id=mail_id, agent=agent, message=message)
    db.add(new_log)
    db.commit()
    db.close()


def job_send_email(mail_id, to, subject, body):
    """Job to send email and log status."""
    success = send_email(to, subject, body)
    db = SessionLocal()
    task = db.query(MailTask).filter(MailTask.id == mail_id).first()
    if not task:
        db.close()
        return

    if success:
        task.status = "sent"
        log_action(mail_id, "MailerAgent", f"Email sent successfully to {to}")
    else:
        task.status = "failed"
        log_action(mail_id, "MailerAgent", "Email sending failed")

    db.commit()
    db.close()


def schedule_mail(mail_id, to, subject, body, run_time):
    """Schedules mail to be sent at run_time."""
    scheduler.add_job(
        job_send_email,
        'date',
        run_date=run_time,
        args=[mail_id, to, subject, body]
    )
    log_action(mail_id, "SchedulerAgent", f"Mail scheduled at {run_time}")

