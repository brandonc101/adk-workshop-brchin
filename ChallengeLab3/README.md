# ADK Multi-Agent System — Challenge Lab 3

Builds on Challenge Lab 2 by turning the weather agent into a **multi-agent
system**: a coordinator (root) agent that delegates to two specialist
sub-agents.

## The three agents

| Agent | Role | Tools |
| --- | --- | --- |
| `root_agent` | Coordinator — receives every request and delegates | (none; `sub_agents`) |
| `weather_agent` | US weather questions | `geocode_place`, `get_weather` |
| `search_agent` | General / current-events questions | ADK built-in **`google_search`** |

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
├── weather_agent/
│   ├── agent.py          # root_agent + weather_agent + search_agent
│   ├── callbacks.py      # logging + screen_input_safety + validate_us_location
│   ├── validation.py     # US check + Model Armor screening
│   ├── tools.py          # geocode_place + get_weather
│   └── .env.example
├── test_agents.py        # drives the coordinator and prints the event stream
├── test_agent.py         # weather-only demo (still routes through root_agent)
├── demo_utils.py
├── tests/                # unit tests (tools, validation, demo_utils)
├── requirements.txt
└── README.md
```

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab3
pip install -r requirements.txt
gcloud services enable aiplatform.googleapis.com \
    geocoding-backend.googleapis.com modelarmor.googleapis.com
cp weather_agent/.env.example weather_agent/.env
# edit weather_agent/.env: GOOGLE_MAPS_API_KEY, GOOGLE_CLOUD_PROJECT,
# and (optional) MODEL_ARMOR_TEMPLATE_ID / MODEL_ARMOR_LOCATION
```

## Run it

```bash
# Multi-agent demo: prints the event stream showing delegation to each sub-agent
python test_agents.py

# Interactive:
adk run weather_agent
# e.g. "weather in Denver" -> weather_agent; "who won the last World Cup" -> search_agent
```

`test_agents.py` sends one weather question and one general question through the
**root** agent and prints each event with its author, so you can see the root
agent transfer to `weather_agent` (which calls `geocode_place`/`get_weather`)
and to `search_agent` (which calls `google_search`).

## Tests

```bash
python -m unittest discover -s tests -v      # 41 unit tests (tools/validation/utils)
python test_agents.py                        # integration: event stream / delegation
```
