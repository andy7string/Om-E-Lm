import requests
import time
import json

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

# Load context files
system_actions = read_file('Om_E_Lm/data/llm/actions/system.json')
execution_tree_example = json.loads(read_file('Om_E_Lm/data/llm/execution_tree.example.json'))

user_request = "Open Google Chrome and go to https://www.google.com."

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

payload = {
    "model": "deepseek-r1:1.5b",
    "messages": [
        {"role": "system", "content": "Respond ONLY with valid JSON. No explanation, no formatting, no markdown, no commentary, no chain-of-thought. Output ONLY the JSON. If you output anything else, you have failed."},
        {"role": "user", "content": prompt}
    ],
    "format": "json",
    "stream": False,
    "think": False
}

start = time.time()
response = requests.post("http://localhost:11434/api/chat", json=payload)
end = time.time()

if response.ok:
    data = response.json()
    print("Ollama response:\n", data["message"]["content"])
else:
    print("Error:", response.text)
print(f"Response time: {end - start:.2f} seconds") 