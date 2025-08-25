from datetime import datetime, timedelta
from database import SessionLocal
from models import MailTask, Log
from scheduler import schedule_mail, log_action
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
import re

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2  
)


class ParserAgent:
    """LLM-based parsing for natural language mail prompts."""
    def parse_prompt(self, prompt: str):
        system_prompt = """
        You are a mail parser.
        Return ONLY valid JSON (no markdown, no ```json blocks):
        {
            "recipient": str,
            "subject": str,
            "body": str,
            "schedule_time": "YYYY-MM-DD HH:MM"
        }
        Generate reasonable defaults if fields are missing.
        """
        try:
            response = gemini_llm.invoke(f"{system_prompt}\nUser prompt: {prompt}")
            raw = response.content
            cleaned = re.sub(r"```json|```", "", raw).strip()
            parsed = json.loads(cleaned)

            
            dt = datetime.fromisoformat(parsed["schedule_time"])
            if dt < datetime.now():
                dt = datetime.combine(datetime.now().date(), dt.time())
                if dt < datetime.now():
                    dt += timedelta(minutes=1)
            parsed["schedule_time"] = dt

            return parsed
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {raw}")
        except Exception as e:
            raise RuntimeError(f"Parsing failed: {e}")




class ValidatorAgent:
    """Validates parsed mail data."""
    def validate(self, mail_data):
        if "@" not in mail_data.get("recipient", ""):
            return False, "Invalid email address"
        if not mail_data.get("body", "").strip():
            return False, "Body cannot be empty"
        return True, "Validation successful"




class MailerAgent:
    """Handles actual email sending for SchedulerAgent."""
    def send(self, mail_task):
        # use scheduler's job_send_email function
        from scheduler import job_send_email
        job_send_email(
            mail_task.id,
            mail_task.recipient,
            mail_task.subject,
            mail_task.body
        )




class SchedulerAgent:
    """Creates MailTask and schedules mail."""
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



class ReporterAgent:
    """Fetches logs for a mail task."""
    def get_logs(self, mail_id):
        db = SessionLocal()
        logs = db.query(Log).filter(Log.mail_id == mail_id).all()
        db.close()
        return [
            {
                "agent": log.agent,
                "message": log.message,
                "time": log.timestamp
            } for log in logs
        ]





