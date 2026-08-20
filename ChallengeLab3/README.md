# ADK Multi-Agent System — Challenge Lab 3

Builds on Challenge Lab 2 by turning the weather agent into a **multi-agent
system**: a coordinator (root) agent that delegates to two specialist
sub-agents, each defined in its own module.

## The three agents

| Agent | Module | Role | Tools |
| --- | --- | --- | --- |
| `root_agent` | `multi_agent/agent.py` | Coordinator — receives every request and delegates | (none; `sub_agents`) |
| `weather_agent` | `multi_agent/weather_agent.py` | US weather questions | `geocode_place`, `get_weather` |
| `search_agent` | `multi_agent/search_agent.py` | General / current-events questions | ADK built-in **`google_search`** |

`root_agent` has `sub_agents=[weather_agent, search_agent]` and instructions to
route weather questions to `weather_agent` and everything else to
`search_agent`. Delegation happens via the ADK's `transfer_to_agent` mechanism.

Callbacks carried over from Lab 2:
- **Root**: logs the user prompt, screens it for malicious content with
  **Google Cloud Model Armor**, and logs the model response.
- **Weather agent**: validates that the location is in the US (the NWS API is
  US-only). General search requests are not geo-restricted.

## Models

`MODEL_BACKEND` selects the model for the coordinator and weather agent
(`gemini` default; `claude`/`gpt` via LiteLLM). The **search agent is always a
Gemini model**, because the built-in Google Search tool only supports Gemini.

## Project layout

```
ChallengeLab3/
├── multi_agent/
│   ├── __init__.py
│   ├── agent.py          # root_agent (coordinator)
│   ├── weather_agent.py  # weather_agent (sub-agent)
│   ├── search_agent.py   # search_agent (sub-agent, google_search)
│   ├── models.py         # shared model selection
│   ├── callbacks.py      # logging + screen_input_safety + validate_us_location
│   ├── validation.py     # US check + Model Armor screening
│   ├── tools.py          # geocode_place + get_weather
│   └── .env.example
├── test_agents.py        # drives the coordinator and prints the event stream
├── test_agent.py         # weather-only demo (routes through root_agent)
├── demo_utils.py
├── tests/                # unit tests (tools, validation, demo_utils, structure)
├── requirements.txt
└── README.md
```

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab3
pip install -r requirements.txt
gcloud services enable aiplatform.googleapis.com \
    geocoding-backend.googleapis.com modelarmor.googleapis.com
cp multi_agent/.env.example multi_agent/.env
# edit multi_agent/.env: GOOGLE_MAPS_API_KEY, GOOGLE_CLOUD_PROJECT,
# and (optional) MODEL_ARMOR_TEMPLATE_ID / MODEL_ARMOR_LOCATION
```

## Run it

```bash
# Interactive (the coordinator delegates to the sub-agents):
adk run multi_agent
#   "weather in Denver"        -> weather_agent
#   "who won the last World Cup" -> search_agent
#   "weather in Paris"         -> blocked (non-US)

# Or the browser dev UI (Cloud Shell: Web Preview on port 8000):
adk web

# Or the scripted event demo (prints delegation events):
python test_agents.py
```

> `adk run multi_agent` / `adk web` load the `multi_agent` **package**, whose
> entry point is `root_agent` — that's the coordinator, so the CLI shows
> `Running agent root_agent`.

## Tests

```bash
python -m unittest discover -s tests -v      # 48 tests (7 structure tests need the ADK)
python test_agents.py                        # integration: event stream / delegation
```

Unit tests cover the tools, validation logic, CLI city selection, and the
multi-agent wiring (`tests/test_agent_structure.py` — sub-agents, tools,
transfer flags, and callback placement). The structure tests require the ADK,
so they run in Cloud Shell and auto-skip where `google-adk` isn't installed.
