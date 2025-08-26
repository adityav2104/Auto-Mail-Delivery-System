from scheduler import job_send_email
class MailerAgent:
    """Handles actual email sending for scheduled tasks."""
    agent_name = "MailerAgent"

    def send(self, mail_task):
        job_send_email(
            mail_task.id,
            mail_task.recipient,
            mail_task.subject,
            mail_task.body
        )
