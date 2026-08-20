# ADK Answer Team — Challenge Lab 4 (answer → verify → refine)

Builds on Challenge Lab 3. Instead of a single search answer, this system
**answers, verifies, and refines** a response before returning it, using an ADK
**workflow (Sequential) agent** to orchestrate a team of specialist agents.

## The agents

| Agent | Module | Role |
| --- | --- | --- |
| `root_agent` | `qa_agent/agent.py` | Coordinator — greets, or routes to the weather agent or the answer team |
| `greeter_agent` | `qa_agent/greeter_agent.py` | Handles greetings / small talk |
| `weather_agent` | `qa_agent/weather_agent.py` | US weather questions (NWS + geocoding, US-only) |
| `answer_team` | `qa_agent/answer_team.py` | **`SequentialAgent`** running the three steps below in order |
| `search_agent` | `qa_agent/search_agent.py` | Finds data with **`google_search`** → `draft_answer` |
| `critique_agent` | `qa_agent/critique_agent.py` | Suggests improvements to the draft → `critique` |
| `refine_agent` | `qa_agent/refine_agent.py` | Rewrites the answer using the critique → `final_answer` |

### How the workflow flows

```
root_agent
├── greeter_agent                     (greetings)
├── weather_agent                     (US weather questions)
└── answer_team  (SequentialAgent)     (all other questions)
    ├── search_agent    -> state["draft_answer"]
    ├── critique_agent  -> state["critique"]   (reads {draft_answer})
    └── refine_agent    -> state["final_answer"] (reads {draft_answer} + {critique})
```

Each step passes data to the next via **session state**: an agent's response is
stored under its `output_key`, and the next agent references it in its
instruction with `{draft_answer}` / `{critique}` templating.

Carried over from Labs 2–3: the root agent logs the user prompt and model
response and screens input for malicious content with **Google Cloud Model
Armor**.

## Models

`MODEL_BACKEND` selects the model (`gemini` default; `claude`/`gpt` via
LiteLLM). The **search agent is always Gemini**, because the built-in Google
Search tool only supports Gemini.

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab4
pip install -r requirements.txt
gcloud services enable aiplatform.googleapis.com \
    geocoding-backend.googleapis.com modelarmor.googleapis.com
cp qa_agent/.env.example qa_agent/.env
# edit qa_agent/.env: GOOGLE_MAPS_API_KEY (for the weather agent),
# GOOGLE_CLOUD_PROJECT, and (optional) MODEL_ARMOR_TEMPLATE_ID
```

## Run it

```bash
# Interactive:
adk run qa_agent
#   "hi there"                         -> greeter_agent
#   "weather in Denver, CO"            -> weather_agent
#   "what is the tallest mountain?"    -> answer_team (search -> critique -> refine)

# Browser dev UI (Cloud Shell: Web Preview on port 8000):
adk web

# Scripted event demo (prints the workflow's event stream):
python test_agents.py
```

`test_agents.py` sends a greeting and a question through the **root** agent and
prints each event with its author, so you can see the coordinator transfer to
`greeter_agent`, and to `answer_team` where `search_agent`, `critique_agent`,
and `refine_agent` run in sequence.

## Tests

```bash
python -m unittest discover -s tests -v      # 48 tests (7 structure tests need the ADK)
python test_agents.py                        # integration: workflow event stream
```

`tests/test_agent_structure.py` verifies the workflow wiring: the answer team is
a `SequentialAgent` running search → critique → refine, the output keys chain the
steps, the search agent uses only `google_search`, and the root callbacks are
attached. It requires the ADK, so it runs in Cloud Shell and auto-skips locally.
