import os
import time
import json
from openai import OpenAI
from env import OME_OPENAI_API_KEY
from datetime import datetime

# Ensure the API key is available
if not OME_OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set OME_OPENAI_API_KEY in your .env file.")

# Initialize the OpenAI client
# The client automatically uses the OPENAI_API_KEY environment variable if it's set,
# but we explicitly pass it for clarity.
client = OpenAI(api_key=OME_OPENAI_API_KEY)

print(f"--- Using API Key from env: {OME_OPENAI_API_KEY[:5]}...{OME_OPENAI_API_KEY[-4:]} ---")

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

# Load context files
system_actions = read_file('Om_E_Lm/data/llm/actions/system.json')
execution_tree_example = json.loads(read_file('Om_E_Lm/data/llm/execution_tree.example.json'))

user_request = "Open Google Chrome, then open openai.com, and finally say 'I'm a horny badger' through the speakers."

# New, more robust system prompt
system_prompt = (
    "You are a precise automation agent. Your task is to generate a valid execution tree in JSON format based on the user's request.\n"
    "**CRITICAL RULES:**\n"
    "1. **JSON ONLY**: Your entire response must be a single, valid JSON object. Do not include any text, explanation, or markdown before or after the JSON.\n"
    "2. **NO PLACEHOLDERS**: Do not use placeholders like `<...>` or `...`. All values must be complete and valid.\n"
    "3. **TIMESTAMPS**: For all `created_at` fields, use the exact string `\"<TIMESTAMP>\"`. This will be replaced later.\n"
    "4. **IDs**: Generate descriptive, unique IDs for `goal_id`, `objective_id`, and `task_id` based on the user's request (e.g., \"open-browser-task\")."
)

prompt = (
    "You are an automation agent.\n"
    "Given the following system actions and a real execution tree example, generate a valid execution tree for the user request below.\n"
    "Respond ONLY with the JSON. No explanation, no commentary, no markdown.\n\n"
    f"system.json (actions):\n{system_actions}\n\n"
    f"execution_tree example:\n{json.dumps(execution_tree_example, indent=2)}\n\n"
    f"User request: {user_request}\n"
)

# Print the full prompt to the terminal before sending
print("\n===== PROMPT SENT TO LLM =====\n")
print(prompt)
print("\n===== END PROMPT =====\n")

# Define the payload for the OpenAI API
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": prompt}
]

start = time.time()
try:
    # Make the API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Or "gpt-3.5-turbo"
        messages=messages,
        response_format={"type": "json_object"} # Use JSON mode for guaranteed JSON output
    )
    end = time.time()
    
    # Extract the content and post-process
    raw_content = response.choices[0].message.content
    
    # Replace the timestamp placeholder
    timestamp_str = datetime.now().isoformat()
    processed_content = raw_content.replace("\"<TIMESTAMP>\"", f"\"{timestamp_str}\"")
    
    print("OpenAI response (processed):\n", processed_content)

except Exception as e:
    end = time.time()
    print(f"An error occurred: {e}")

print(f"Response time: {end - start:.2f} seconds") 