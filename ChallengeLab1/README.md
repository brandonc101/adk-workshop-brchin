# ADK Weather Agent

A weather agent built with the **Google Agent Development Kit (ADK)**. The
agent uses tools to retrieve real-time weather for user-supplied US locations
and returns a short summary or a weather alert based on current conditions.

## What it does

Given a place name (e.g. *"Denver, CO"*), the agent:

1. Calls `geocode_place` (Google Maps Geocoding API) to convert the place into
   latitude/longitude.
2. Calls `get_weather` (US National Weather Service API) to fetch the current
   forecast for that latitude/longitude.
3. Uses the model to summarize the conditions and flag any hazards as a
   **WEATHER ALERT**.

## Project layout

```
ChallengeLab1/
├── weather_agent/
│   ├── __init__.py        # exposes the agent package to the ADK
│   ├── agent.py           # defines root_agent (model + tools + instructions)
│   ├── tools.py           # geocode_place() and get_weather() tool functions
│   └── .env.example       # copy to .env and fill in (real .env is gitignored)
├── test_agent.py          # runs the agent against several US cities
├── requirements.txt
└── README.md
```

## Model support (Gemini + a third-party model)

The model is selected by the `MODEL_BACKEND` environment variable, so the same
agent runs on Gemini or on a third-party model with no code changes:

| `MODEL_BACKEND` | Model                                        | Auth needed                     |
| --------------- | -------------------------------------------- | ------------------------------- |
| `gemini` (default) | `gemini-2.5-flash` via Vertex AI          | GCP project + ADC (no API key)  |
| `claude`        | `anthropic/claude-opus-4-8` via LiteLLM      | `ANTHROPIC_API_KEY`             |
| `gpt`           | `openai/gpt-4o` via LiteLLM                  | `OPENAI_API_KEY`                |

Third-party models are wired through ADK's `LiteLlm` wrapper
(`google.adk.models.lite_llm`). The demo/tests run on Gemini by default.

## Setup (Google Cloud Shell)

All commands below are run from **inside this `ChallengeLab1/` directory**:

```bash
cd ChallengeLab1

# 1. Install dependencies
pip install -r requirements.txt

# 2. Enable the required APIs
gcloud services enable aiplatform.googleapis.com geocoding-backend.googleapis.com

# 3. Create a Google Maps API key for the Geocoding API
gcloud services api-keys create --display-name="adk-weather-geocoding"
#    ...then copy the keyString from the output.

# 4. Configure the environment
cp weather_agent/.env.example weather_agent/.env
#    Edit weather_agent/.env and set GOOGLE_MAPS_API_KEY (and confirm
#    GOOGLE_CLOUD_PROJECT matches your project).
```

## Run it

```bash
# Interactive chat in the terminal:
adk run weather_agent

# Or the web UI:
adk web

# Or the automated multi-city demo (default 5 US cities):
python test_agent.py

# ...or test your own cities by passing them as arguments:
python test_agent.py "Austin, TX" "Boston, MA"
```
