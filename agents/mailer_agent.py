from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from scheduler import job_send_email, log_action
from llms import gemini_llm
import json



@tool
def send_email_tool(mail_info_json: str) -> str:
    """
    mail_info_json: JSON string with keys task_id, recipient, subject, body
    Sends the email and returns JSON message
    """
    data = json.loads(mail_info_json)
    job_send_email(
        int(data["task_id"]),
        data["recipient"],
        data["subject"],
        data["body"]
    )
    return json.dumps({"message": f"Email sent to {data['recipient']}"})

@tool
def log_action_tool(log_info_json: str) -> str:
    """
    log_info_json: JSON string with keys task_id, agent_name, message
    Logs action and returns JSON message
    """
    data = json.loads(log_info_json)
    log_action(int(data["task_id"]), data["agent_name"], data["message"])
    return json.dumps({"message": f"Logged: {data['agent_name']} - {data['message']}"})


class MailerAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools=[send_email_tool, log_action_tool],
            llm=gemini_llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def send(self, mail_task: dict):
        """
        Orchestrates sending email via LLM + tools:
        1. Send the email
        2. Log the action
        """
       
        mail_info_json = json.dumps({
            "task_id": mail_task["id"],
            "recipient": mail_task["recipient"],
            "subject": mail_task["subject"],
            "body": mail_task["body"]
        })
        self.agent.run(f"Send email using send_email_tool: {mail_info_json}")

       
        log_info_json = json.dumps({
            "task_id": mail_task["id"],
            "agent_name": "MailerAgent",
            "message": f"Email sent to {mail_task['recipient']}"
        })
        self.agent.run(f"Log email sent using log_action_tool: {log_info_json}")

