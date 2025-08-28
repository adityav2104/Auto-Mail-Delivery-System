from datetime import datetime, timedelta
import json, re, dateparser
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from llms import gemini_llm


@tool
def parse_datetime_tool(text: str) -> str:
    """Convert natural language datetime into ISO format string"""
    dt = dateparser.parse(text)
    if not dt:
        raise ValueError(f"Could not parse datetime from: {text}")
    return dt.isoformat()


class ParserAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools = [parse_datetime_tool],
            llm = gemini_llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def parse_prompt(self, prompt: str):
        system_prompt = """
        You are a mail parser.
        Extract fields: recipient, subject, body, schedule_time.
        If schedule_time is in natural language, use DatetimeParser tool.
        Return strict JSON only.

        Rules for schedule_time:
        - If user says "today evening" → convert to "today 6:00 PM".
        - If user says "tomorrow morning" → convert to "tomorrow 9:00 AM".
        - Always resolve vague terms like 'morning, noon, afternoon, evening, night' into exact hours.
        - If no time is provided, default to "today +2 hours" from now.

        Generate reasonable defaults if fields are missing.
        """
        response = self.agent.run(f"{system_prompt}\nUser prompt: {prompt}")
        cleaned = re.sub(r"```json|```", "", response).strip()
        parsed = json.loads(cleaned)

        dt = dateparser.parse(parsed["schedule_time"])
        now = datetime.now()
        if dt and dt < now and dt.date() == now.date():
            dt = now + timedelta(minutes=1)
        parsed["schedule_time"] = dt
        return parsed
