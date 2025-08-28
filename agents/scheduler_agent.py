from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from datetime import datetime
from database import SessionLocal
from models import MailTask
from scheduler import schedule_mail, log_action
from llms import gemini_llm
import json


@tool
def create_mail_task_tool(mail_data_json: str) -> str:
    """
    mail_data_json: JSON string with recipient, subject, body, schedule_time
    Returns: task_id as string
    """
    data = json.loads(mail_data_json)
    db = SessionLocal()
    task = MailTask(
        recipient=data["recipient"],
        subject=data["subject"],
        body=data["body"],
        schedule_time=datetime.fromisoformat(data["schedule_time"])
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = str(task.id)
    db.close()
    return json.dumps({"task_id": task_id})  


@tool
def schedule_mail_tool(mail_info_json: str) -> str:
    """
    mail_info_json: JSON string with keys task_id, recipient, subject, body, schedule_time
    """
    data = json.loads(mail_info_json)
    dt = datetime.fromisoformat(data["schedule_time"])
    schedule_mail(
        int(data["task_id"]),
        data["recipient"],
        data["subject"],
        data["body"],
        dt
    )
    return json.dumps({"message": f"Mail scheduled for {data['schedule_time']}"}) 


@tool
def log_action_tool(log_info_json: str) -> str:
    """
    log_info_json: JSON string with keys task_id, agent_name, message
    """
    data = json.loads(log_info_json)
    log_action(int(data["task_id"]), data["agent_name"], data["message"])
    return json.dumps({"message": f"Logged: {data['agent_name']} - {data['message']}"})  



class SchedulerAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools=[create_mail_task_tool, schedule_mail_tool, log_action_tool],
            llm=gemini_llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def schedule(self, mail_data: dict):
        """
        LLM + tools orchestrates:
        1. Create MailTask
        2. Log parser and validator outputs
        3. Schedule the mail
        Returns task_id
        """
      
        mail_data_json = json.dumps({
            "recipient": mail_data["recipient"],
            "subject": mail_data["subject"],
            "body": mail_data["body"],
            "schedule_time": mail_data["schedule_time"].isoformat()
        })
        prompt_create = f"""
        Create a mail task using create_mail_task_tool.
        Input: {mail_data_json}
        Return ONLY JSON like: {{ "task_id": "39" }}
        """
        task_id_json = self.agent.run(prompt_create).strip()
        try:
            task_id = json.loads(task_id_json)["task_id"]
        except Exception:
            raise ValueError(f"Could not parse task_id JSON: {task_id_json}")

       
        log_parser_json = json.dumps({
            "task_id": task_id,
            "agent_name": "ParserAgent",
            "message": f"Parsed prompt: {mail_data}"
        })
        self.agent.run(f"Log parser output using log_action_tool: {log_parser_json}")

        log_validator_json = json.dumps({
            "task_id": task_id,
            "agent_name": "ValidatorAgent",
            "message": "Validation successful"
        })
        self.agent.run(f"Log validator output using log_action_tool: {log_validator_json}")

      
        schedule_json = json.dumps({
            "task_id": task_id,
            "recipient": mail_data["recipient"],
            "subject": mail_data["subject"],
            "body": mail_data["body"],
            "schedule_time": mail_data["schedule_time"].isoformat()
        })
        self.agent.run(f"Schedule mail using schedule_mail_tool: {schedule_json}")

        return task_id

