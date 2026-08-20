# ADK Weather Agent — Challenge Lab 2 (Callbacks + Model Armor)

Builds on the Challenge Lab 1 weather agent by adding **ADK callbacks** for
logging and input validation, including malicious-content screening with
**Google Cloud Model Armor**.

## What's new vs Lab 1

Three callbacks are wired into the agent (`weather_agent/agent.py`):

| Callback | Hook | Purpose |
| --- | --- | --- |
| `log_user_prompt` | before-model | Logs the incoming user prompt (`[USER PROMPT] ...`) |
| `validate_user_input` | before-model | Validates the prompt and **blocks** the model call if it's rejected |
| `log_model_response` | after-model | Logs the model's response (`[MODEL RESPONSE] ...`) |

`validate_user_input` enforces two rules before the request ever reaches the model:

1. **Not malicious** — screened with **Google Cloud Model Armor**
   (prompt-injection / jailbreak / etc.).
2. **US location only** — the request is geocoded and rejected if it resolves
   to a country other than the US (the National Weather Service API is US-only).

If a prompt is blocked, the user gets a friendly refusal and the model is never
called.

## Project layout

```
ChallengeLab2/
├── weather_agent/
│   ├── __init__.py
│   ├── agent.py          # wires callbacks into the Agent
│   ├── tools.py          # geocode_place (now returns `country`) + get_weather
│   ├── callbacks.py      # log_user_prompt / validate_user_input / log_model_response
│   ├── validation.py     # pure, testable logic: US check + Model Armor screen
│   └── .env.example
├── test_agent.py         # multi-city demo (accepts city args)
├── demo_utils.py
├── tests/                # test_tools, test_validation, test_demo_utils
├── requirements.txt
└── README.md
```

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab2
pip install -r requirements.txt

# APIs: Vertex AI, Geocoding, and Model Armor
gcloud services enable aiplatform.googleapis.com \
    geocoding-backend.googleapis.com modelarmor.googleapis.com

# Maps key (same as Lab 1) + env file
cp weather_agent/.env.example weather_agent/.env
# edit weather_agent/.env: set GOOGLE_MAPS_API_KEY, confirm GOOGLE_CLOUD_PROJECT
```

### Create a Model Armor template

In the Cloud Console: **Security → Model Armor → Templates → Create template**.
Enable the detections you want (e.g. Prompt Injection & Jailbreak), pick a
region (e.g. `us-central1`), and note the **template ID**. Then set in
`weather_agent/.env`:

```
MODEL_ARMOR_TEMPLATE_ID=your-template-id
MODEL_ARMOR_LOCATION=us-central1
```

> If `MODEL_ARMOR_TEMPLATE_ID` is left blank, malicious-content screening is
> skipped (fail-open, logged as a warning) — the logging callbacks and the
> US-location check still work, so the callback behavior is fully demonstrable
> even before Model Armor is configured.

## Run it

```bash
adk run weather_agent            # interactive; try a non-US city to see it blocked
python test_agent.py             # multi-city demo (default US cities)
python test_agent.py "Paris"     # blocked: non-US location
```

The callback log lines (`[USER PROMPT]`, `[MODEL RESPONSE]`, `[BLOCKED]`) print
to the console.

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers the tools, the CLI city selection, and (the focus of this lab) the
validation logic: user-text extraction, the US-location check, Model Armor
screening (match / no-match / not-configured / error), and the combined
`evaluate_user_prompt` including malicious-before-geocode precedence. All tests
run offline with no ADK, network, keys, or Model Armor library required.
