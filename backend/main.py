from fastapi import FastAPI, Path
from pydantic import BaseModel
from typing import List, Dict
import openai
import os
import json
from llm_prompts import LLM_PROMPT_TEMPLATE
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file if present
load_dotenv()

app = FastAPI()

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for requirements and generated test steps
saved_tests: Dict[str, List[Dict]] = {}

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable not set. Please set it in your environment or in a .env file.")
openai.api_key = OPENAI_API_KEY
# To use: create a .env file with a line: OPENAI_API_KEY=sk-...your-key...

class TestGenerationRequest(BaseModel):
    requirements_text: str

class TestGenerationResponse(BaseModel):
    test_steps: List[dict]

@app.post("/api/apps/{aut_id}/tests/generate", response_model=TestGenerationResponse)
def generate_test_cases(aut_id: str = Path(...), req: TestGenerationRequest = ...):
    prompt = LLM_PROMPT_TEMPLATE.format(requirements_text=req.requirements_text)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2,
        )
        # Extract the JSON from the response
        content = response.choices[0].message["content"].strip()
        # Find the first and last brackets to extract the JSON array
        start = content.find("[")
        end = content.rfind("]") + 1
        steps_json = content[start:end]
        test_steps = json.loads(steps_json)
    except Exception as e:
        # Fallback to dummy steps if OpenAI fails
        test_steps = [
            {
                "action": "Navigate",
                "element_description": "Login page",
                "value": "https://example.com/login",
                "expected_result": "Login page is displayed."
            },
            {
                "action": "Type",
                "element_description": "Username input field",
                "value": "user@example.com",
                "expected_result": "Username is entered."
            },
            {
                "action": "Type",
                "element_description": "Password input field",
                "value": "password123",
                "expected_result": "Password is entered."
            },
            {
                "action": "Click",
                "element_description": "Login button",
                "value": None,
                "expected_result": "User is logged in and dashboard is visible."
            }
        ]
    # Save to in-memory store
    if aut_id not in saved_tests:
        saved_tests[aut_id] = []
    saved_tests[aut_id].append({
        "requirements": req.requirements_text,
        "test_steps": test_steps
    })
    return TestGenerationResponse(test_steps=test_steps) 