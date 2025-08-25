from fastapi import FastAPI
from database import Base, engine
from agents import ParserAgent, ValidatorAgent, SchedulerAgent, ReporterAgent

Base.metadata.create_all(bind=engine)

app = FastAPI()

parser = ParserAgent()
validator = ValidatorAgent()
scheduler = SchedulerAgent()
reporter = ReporterAgent()

@app.post("/schedule-mail/")
def schedule_mail_endpoint(prompt: str):
    parsed = parser.parse_prompt(prompt)
    is_valid, msg = validator.validate(parsed)
    if not is_valid:
        return {"error": msg}
    mail_id = scheduler.schedule(parsed)
    return {"message": "Mail scheduled", "mail_id": mail_id}

@app.get("/status/{mail_id}")
def check_status(mail_id: int):
    logs = reporter.get_logs(mail_id)
    return {"mail_id": mail_id, "logs": logs}
