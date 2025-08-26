class ValidatorAgent:
    """Validates parsed mail data."""
    agent_name = "ValidatorAgent"

    def validate(self, mail_data):
        if "@" not in mail_data.get("recipient", ""):
            return False, "Invalid email address"
        if not mail_data.get("body", "").strip():
            return False, "Body cannot be empty"
        return True, "Validation successful"
