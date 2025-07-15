import time
import json
from datetime import datetime
from openai import OpenAI

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

# --- Model and Prompt Setup ---
# NOTE: Replace with the exact model identifier from your LM Studio downloads
MODEL_IDENTIFIER = "mistral-7b-instruct-v0.3@4bit" 

# By defining the system prompt directly in the script, we make it self-contained
# and avoid any conflicts with the LM Studio server's configuration.
system_prompt = """You are Om‑E, an advanced macOS automation agent.

Your ONLY task is to generate valid JSONL output conforming to the provided execution tree schema.

⚡ Execution Tree Structure:
Goal: High-level intent (e.g., “Compose and send an email”)
- goal_id: string (unique)
- description: string (the overall outcome)
- status: ["pending", "in_progress", "complete", "failed"]
- created_at: ISO 8601 datetime
- objectives: list of Objectives

Objective: Logical sub-goal (e.g., “Open Mail”, “Start new message”)
- objective_id: string (unique)
- goal_id: string (parent goal)
- description: string (sub-goal detail)
- status: same as Goal
- created_at: ISO 8601 datetime
- tasks: list of Tasks

Task: Concrete step to achieve an Objective (e.g., “Click New Message button”)
- task_id: string (unique)
- objective_id: string (parent objective)
- description: string (step detail)
- status: same as Objective
- created_at: ISO 8601 datetime
- actions: list of Actions

Action: Atomic UI operation executed by a handler
- name: string (e.g., "open_app", "click_element", "type_text")
- source: string (handler: system, mouse, keyboard, vision)
- input_args: dict (e.g., {"app_name": "Mail"})
- state: ["pending", "active", "complete", "skipped", "failed"]
- status: ["not_started", "success", "failed"]

🚫 STRICT RULES:
- Respond ONLY with valid JSONL.
- NO explanations, commentary, or extra text.
- NO markdown formatting.
- NO chain-of-thought reasoning.
- NO surrounding text or annotations.
- Start response directly with JSONL.
"""

# Load context files
system_actions = read_file('Om_E_Lm/data/llm/actions/system.json')
user_request = "Open Google Chrome, then open openai.com, and finally say 'I'm a horny badger' through the speakers."

# The user-facing prompt is now a single, comprehensive block.
# This gets sent as one 'user' message to avoid server-side template errors.
prompt = (
    f"{system_prompt}\n\n"
    f"--- AVAILABLE ACTIONS ---\n"
    f"system.json (actions):\n{system_actions}\n\n"
    f"--- USER REQUEST ---\n"
    f"User request: {user_request}\n"
)

# Print the full prompt to the terminal before sending
print("\n===== PROMPT SENT TO LLM =====\n")
print(prompt)
print("\n===== END PROMPT =====\n")

# --- LM Studio SDK Interaction ---
start = time.time()
try:
    # Point the OpenAI client to the local LM Studio server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    # Send the entire prompt as a single user message.
    messages = [{"role": "user", "content": prompt}]

    # Get the response using the .chat.completions.create() method
    print("Generating response...")
    response = client.chat.completions.create(
        model=MODEL_IDENTIFIER,
        messages=messages,
        temperature=0,  # Set to 0 for deterministic JSON output
        stream=False,
    )
    end = time.time()

    # The response from .create() is an OpenAI-compatible object
    raw_content = response.choices[0].message.content
    processed_content = raw_content.strip('` \n')
    
    # We can attempt to parse the JSON to validate it.
    try:
        json.loads(processed_content)
        print("LM Studio response (processed and validated as JSON):\n", processed_content)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print("Raw response from model:\n", raw_content)

except Exception as e:
    end = time.time()
    print(f"An error occurred: {e}")

print(f"Response time: {end - start:.2f} seconds") 