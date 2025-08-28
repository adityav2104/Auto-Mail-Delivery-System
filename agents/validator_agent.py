from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from llms import gemini_llm
import re


@tool
def validate_email_tool(email: str) -> str:
    """Check if an email address is valid. Return 'valid' or 'invalid'."""
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "valid"
    return "invalid"


@tool
def validate_body_tool(body: str) -> str:
    """Check if the email body is non-empty."""
    if body.strip():
        return "valid"
    return "invalid"


class ValidatorAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools=[validate_email_tool, validate_body_tool],
            llm=gemini_llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def validate(self, mail_data: dict):
        """Use LLM + tools to validate mail fields."""
        prompt = f"""
        Validate this mail data: {mail_data}

        Rules:
        - Use validate_email_tool for 'recipient'
        - Use validate_body_tool for 'body'
        - If both valid → say 'Email is valid and Body is not empty!'
        - If invalid → return reason clearly
        """

        result = self.agent.run(prompt)

        if "invalid" in result.lower():
            return False, result
        return True, result
