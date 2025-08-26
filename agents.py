# from datetime import datetime, timedelta
# from database import SessionLocal
# from models import MailTask, Log
# from scheduler import schedule_mail, log_action, job_send_email
# from langchain_google_genai import ChatGoogleGenerativeAI
# import os
# import json
# import re
# import dateparser

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# gemini_llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=GOOGLE_API_KEY,
#     temperature=0.2
# )


# class ParserAgent:
#     """LLM-based parsing for natural language mail prompts with human-friendly time support."""
    
#     def parse_prompt(self, prompt: str):
#         system_prompt = """
#         You are a mail parser.
#         Return ONLY valid JSON (no markdown, no ```json blocks):
#         {
#             "recipient": str,
#             "subject": str,
#             "body": str,
#             "schedule_time": str  # natural language datetime like 'today 6:30 PM'
#         }
#         Generate reasonable defaults if fields are missing.
#         """
#         try:
#             response = gemini_llm.invoke(f"{system_prompt}\nUser prompt: {prompt}")
#             raw = response.content
#             cleaned = re.sub(r"```json|```", "", raw).strip()
#             parsed = json.loads(cleaned)

#             # parse human-friendly datetime
#             dt = dateparser.parse(parsed["schedule_time"])
#             if not dt:
#                 raise ValueError(f"Could not parse schedule_time: {parsed['schedule_time']}")

#             now = datetime.now()

#             # Respect user-specified time:
#             if dt < now:
#                 if dt.date() == now.date():
#                     dt = now + timedelta(minutes=1)  # schedule a minute later if same day
#                 else:
#                     # future date remains as-is
#                     pass

#             parsed["schedule_time"] = dt
#             return parsed

#         except json.JSONDecodeError:
#             raise ValueError(f"LLM returned invalid JSON: {raw}")
#         except Exception as e:
#             raise RuntimeError(f"Parsing failed: {e}")


# class ValidatorAgent:
#     """Validates parsed mail data."""
#     agent_name = "ValidatorAgent"

#     def validate(self, mail_data):
#         if "@" not in mail_data.get("recipient", ""):
#             return False, "Invalid email address"
#         if not mail_data.get("body", "").strip():
#             return False, "Body cannot be empty"
#         return True, "Validation successful"


# class SchedulerAgent:
#     """Creates MailTask and schedules mail."""
#     agent_name = "SchedulerAgent"

#     def schedule(self, mail_data):
#         db = SessionLocal()
#         task = MailTask(**mail_data)
#         db.add(task)
#         db.commit()
#         db.refresh(task)

#         # Log Parser and Validator outputs
#         log_action(task.id, "ParserAgent", f"Parsed prompt: {mail_data}")
#         log_action(task.id, "ValidatorAgent", "Validation successful")

#         # Schedule the mail
#         schedule_mail(task.id, task.recipient, task.subject, task.body, task.schedule_time)
#         db.close()
#         return task.id


# class MailerAgent:
#     """Handles actual email sending for scheduled tasks."""
#     agent_name = "MailerAgent"

#     def send(self, mail_task):
#         job_send_email(
#             mail_task.id,
#             mail_task.recipient,
#             mail_task.subject,
#             mail_task.body
#         )


# class ReporterAgent:
#     """Fetches logs for a mail task."""
#     agent_name = "ReporterAgent"

#     def get_logs(self, mail_id):
#         db = SessionLocal()
#         logs = db.query(Log).filter(Log.mail_id == mail_id).all()
#         db.close()
#         return [
#             {"agent": log.agent, "message": log.message, "time": log.timestamp}
#             for log in logs
#         ]
