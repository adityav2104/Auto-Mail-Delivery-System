from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from database import SessionLocal
from models import Log
from llms import gemini_llm
import json



@tool
def fetch_logs_tool(mail_id_json: str) -> str:
    """
    mail_id_json: JSON string with key 'mail_id'
    Returns logs as JSON array
    """
    data = json.loads(mail_id_json)
    mail_id = int(data["mail_id"])
    db = SessionLocal()
    logs = db.query(Log).filter(Log.mail_id == mail_id).all()
    db.close()
    logs_list = [
        {"agent": log.agent, "message": log.message, "time": log.timestamp.isoformat()}
        for log in logs
    ]
    return json.dumps({"logs": logs_list})


class ReporterAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools=[fetch_logs_tool],
            llm=gemini_llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def get_logs(self, mail_id: int):
        """
        Use LLM + tool to fetch and optionally format logs
        """
        mail_id_json = json.dumps({"mail_id": mail_id})
        result_json = self.agent.run(f"Fetch logs using fetch_logs_tool: {mail_id_json}")
        try:
            result = json.loads(result_json)
            return result.get("logs", [])
        except Exception:
            raise ValueError(f"Could not parse logs JSON: {result_json}")

