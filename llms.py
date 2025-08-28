import os
from langchain_google_genai import ChatGoogleGenerativeAI


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2
)
