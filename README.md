\# AI Business Agent



A local-first AI agent that turns a business direction into structured digital-product ideas, saves them to disk, and prints them as a table — all on a laptop, with no cloud API.



This is the \*\*first agent\*\* in a longer pipeline that will eventually help automate a small digital-product business (idea → research → prompt → generate → QC → publish → analyze).



\---



\## Why this exists



I am a 17-year-old ECE student in Tamil Nadu. My longer-term goal is to build a legitimate digital-product business while keeping my studies as the priority. Doing that by hand (researching niches, writing prompts, generating metadata, sorting files) would eat hours I don't have.



This project is my attempt to let a small AI agent do the repetitive work — idea generation, metadata, file organization — so I can focus on the parts that actually need human judgment: strategy, quality, and decisions.



It is also a \*\*portfolio project\*\* for engineering internships and future work: it demonstrates Python, AI agent architecture, LLM integration, Git, testing, and clean project structure.



The business targets (Rs. 2,00,000 cumulative in 6 months; Rs. 50,000/month longer term) are ambitious goals to work toward, \*\*not\*\* guaranteed outcomes. This agent does not create money. It creates \*time\*.



\---



\## What it does today



Right now the agent can:



1\. Accept a business direction, e.g. "printable wall art for engineering students"

2\. Generate 1-10 structured product ideas using a \*\*local\*\* LLM (via Ollama)

3\. Validate every idea against a fixed schema

4\. Normalize common small-model quirks (e.g. comma-joined keyword lists)

5\. Print the ideas as a readable table

6\. Save them as timestamped JSON in `data/processed/`



Example output:



&#x20;   --- 1. Tech Circuit Art ---

&#x20;     Buyer:      Engineering students

&#x20;     Format:     PNG pack, 5 sizes, 300 DPI

&#x20;     Why:        Relevant to engineering studies and popular among students for dorm room decor.

&#x20;     Difficulty: easy

&#x20;     Price:      Rs.99-299

&#x20;     Keywords:   tech art, engineering, circuit design



\---



\## Architecture



The flow, top to bottom:



1\. \*\*CLI\*\* (`app/main.py`) — parses commands from the user

2\. \*\*Workflow\*\* (`app/workflows/idea\_workflow.py`) — orchestrates: run, print, save

3\. \*\*Idea Agent\*\* (`app/agents/idea\_agent.py`) — role + schema + validation

4\. \*\*LLM Wrapper\*\* (`app/models/llm.py`) — the only file that talks to Ollama

5\. \*\*Ollama\*\* (local runtime) — runs `qwen2.5:7b`



Key principle: \*\*the model is the unreliable part; our code is the reliable part.\*\* Every agent validates its output before the workflow saves anything.



\---



\## Tech stack



\- Language: Python 3.11+

\- Local LLM runtime: Ollama

\- Default model: `qwen2.5:7b`

\- Config: python-dotenv (`.env`)

\- Version control: Git + GitHub



No paid APIs. No cloud dependency. The project works offline.



\---



\## Setup



Prerequisites: Python 3.11+, Ollama installed, Git.



&#x20;   git clone https://github.com/andrewsuvinston/AI-Business-Agent.git

&#x20;   cd AI-Business-Agent



&#x20;   ollama pull qwen2.5:7b



&#x20;   python -m venv .venv

&#x20;   .\\.venv\\Scripts\\Activate.ps1

&#x20;   pip install -r requirements.txt



&#x20;   copy .env.example .env



Edit `.env` if needed:



&#x20;   OLLAMA\_HOST=http://localhost:11434

&#x20;   OLLAMA\_MODEL=qwen2.5:7b



\---



\## Usage



Free-text mode (any prompt):



&#x20;   python -m app.main "What is machine learning?"



Idea mode (structured product ideas, saved to disk):



&#x20;   python -m app.main ideas "printable wall art for engineering students" --count 3



`--count` is optional (default 5). JSON files land in `data/processed/` with timestamps.



\---



\## Project structure



&#x20;   AI-Business-Agent/

&#x20;   |-- app/

&#x20;   |   |-- agents/          one file per agent

&#x20;   |   |-- workflows/       orchestrators that chain agents

&#x20;   |   |-- models/          LLM wrappers

&#x20;   |   |-- utils/           small helpers (JSON, files)

&#x20;   |   |-- main.py          CLI entry point

&#x20;   |-- config/

&#x20;   |   |-- settings.py      reads .env, exposes paths

&#x20;   |-- data/

&#x20;   |   |-- raw/             untouched inputs

&#x20;   |   |-- processed/       agent output (JSON)

&#x20;   |   |-- ready\_to\_upload/ QC-passed products

&#x20;   |   |-- rejected/        QC-failed products

&#x20;   |-- outputs/             generated assets

&#x20;   |-- tests/               smoke tests

&#x20;   |-- .env.example

&#x20;   |-- requirements.txt

&#x20;   |-- README.md



\---



\## Design decisions



\*\*Why Ollama instead of a cloud API?\*\*

Free, offline, no rate limits, no key management, no surprise bills. Cloud APIs can be added later as an optional fallback — the LLM wrapper is the only file that would need to change.



\*\*Why JSON output instead of free text?\*\*

Structured data can be filtered, sorted, chained into the next agent, and counted. Free text cannot. We force the model into JSON mode via Ollama's `format="json"` and then validate the shape in code.



\*\*Why validate before saving?\*\*

LLMs occasionally produce malformed output. A bad idea that reaches `data/processed/` becomes a bug two steps later. Validation at the source means the failure is loud and local instead of silent and distant.



\*\*Why a workflow layer between CLI and agent?\*\*

`main.py` handles user input. Workflows handle pipelines. Agents do one job each. This keeps each piece small enough to understand and test in isolation.



\---



\## Limitations (honest)



\- Small model. `qwen2.5:7b` is capable for its size but not GPT-4. Idea quality varies.

\- No internet research. The agent generates ideas from its training data only. It does not verify that a niche is underserved or that a price is realistic.

\- No image generation. It only produces text.

\- No publishing. Everything is manual.

\- Windows-tested. Should work on macOS/Linux but hasn't been verified there.

\- Not a money-maker. This is a productivity tool. Whether the business works depends on dozens of things this code does not control.



\---



\## Roadmap



\- \[x] Idea agent with schema validation

\- \[x] JSON persistence with timestamps

\- \[x] CLI subcommand

\- \[ ] Metadata agent (titles, descriptions, tags per idea)

\- \[ ] Quality-control agent (screens ideas before saving)

\- \[ ] Folder automation (READY\_TO\_UPLOAD / REJECTED pipeline)

\- \[ ] Daily report generator

\- \[ ] Optional cloud LLM fallback

\- \[ ] Analytics agent (compare saved ideas against real-world outcomes)



\---



\## Author



\*\*Andrew Suvinston\*\*

ECE student, Alagappa Chettiar Government College of Engineering \& Technology (ACGCET), Karaikudi, Tamil Nadu.



GitHub: https://github.com/andrewsuvinston



\---



\## License



No license chosen yet. All rights reserved for now.

