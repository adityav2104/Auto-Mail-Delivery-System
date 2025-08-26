from datetime import datetime, timedelta
import os, json, re, dateparser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool, AgentType


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2
)

def parse_datetime_tool(text: str) -> str:
    dt = dateparser.parse(text)
    if not dt:
        raise ValueError(f"Could not parse datetime from: {text}")
    return dt.isoformat()


class ParserAgent:
    def __init__(self):
        tools = [
            Tool(
                name="DatetimeParser",
                func=parse_datetime_tool,
                description="Convert natural language datetime into ISO format string"
            )
        ]
        self.agent = initialize_agent(
            tools,
            gemini_llm,
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
