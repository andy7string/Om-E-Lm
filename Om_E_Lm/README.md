# Om‑E Agent Sandbox

A modular sandbox project for developing a local AI agent that:
- Uses DeepSeek (1.5B for dev, 7B for prod) via Ollama
- Parses natural language requests into structured JSONL execution trees
- Interfaces with the OM‑E automation framework (mouse, keyboard, system handlers)
- Maintains memory and context awareness across sessions
- Prioritises speed and efficiency for real-time macOS automation

## Project Structure

```
ome_agent_sandbox/
├── agent/
│   ├── deepseek_agent.py
│   ├── memory_manager.py
│   ├── context_builder.py
│   └── utils.py
├── data/
│   ├── llm/
│   │   ├── menu_tree.json
│   │   ├── nav_map.jsonl
│   │   ├── execution_tree.json
│   │   ├── agent_memory.json
│   └── logs/
├── main.py
├── requirements.txt
└── README.md
```

## Setup

1. **Install Python 3.11.2** (strict requirement for compatibility)
2. **Create a virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Install and run Ollama locally**
   - [Ollama installation guide](https://ollama.com/download)
   - Pull DeepSeek model: `ollama pull deepseek-r1:1.5b`

## Usage

- Run the agent:
  ```bash
  python main.py
  ```
- The agent will:
  - Accept natural language input
  - Load context from `data/llm/`
  - Send prompt + context to DeepSeek via Ollama
  - Stream and log JSONL execution trees
  - Write planned trees and memory to `data/llm/`

## Features
- Modular agent logic
- Session and persistent memory
- JSONL I/O for workflows and context
- Fast iteration with DeepSeek 1.5B
- Ready for OM‑E integration and scaling to 7B

## License
MIT
