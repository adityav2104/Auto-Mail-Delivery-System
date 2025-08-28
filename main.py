from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from database import Base, engine
from agents import ParserAgent, ValidatorAgent, SchedulerAgent, MailerAgent, ReporterAgent
import time

Base.metadata.create_all(bind=engine)

app = FastAPI()

parser = ParserAgent()
validator = ValidatorAgent()
scheduler = SchedulerAgent()
mailer = MailerAgent()
reporter = ReporterAgent()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/schedule-mail-stream/")
def schedule_mail_stream(request: PromptRequest):
    prompt = request.prompt

    def event_stream():
        yield "data: Parsing...\n\n"
        parsed = parser.parse_prompt(prompt)
        yield f"data: Parsing successful! {parsed}\n\n"
        time.sleep(2)

        yield "data: Validating...\n\n"
        is_valid, msg = validator.validate(parsed)
        if not is_valid:
            yield f"data: Validation failed! {msg}\n\n"
            return
        yield f"data: Validation successful! {msg}\n\n"
        time.sleep(2)

        yield "data: Scheduling...\n\n"
        mail_id = scheduler.schedule(parsed)
        yield f"data: Scheduling successful! mail_id: {mail_id}\n\n"
        yield f"data: Mail will be sent at scheduled time: {parsed['schedule_time']}\n\n"
        time.sleep(2)

        yield f"data: Use /logs/{mail_id} to track sending status.\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/logs/{mail_id}")
def stream_logs(mail_id: int):
    def log_stream():
        seen = set()
        while True:
            logs = reporter.get_logs(mail_id)
            for log in logs:
                key = (log["time"], log["message"])
                if key not in seen:
                    seen.add(key)
                    yield f"data: [{log['time']}] {log['agent']}: {log['message']}\n\n"
                    if "mail sent" in log["message"].lower():
                        return
            time.sleep(2)

    return StreamingResponse(log_stream(), media_type="text/event-stream")
