# ReadyNow! — Challenge Lab 6 (FEMA case study)

A proof-of-concept emergency-preparedness assistant built with the ADK, and
deployed to Vertex AI Agent Engine. It integrates the capabilities from Labs
1–5 (multi-agent coordination, a verify/refine workflow, logging + input
validation, and deployment) and adds **routing to safety**.

## Architecture

```mermaid
flowchart TD
    U([User]) --> ROOT[root_agent<br/>coordinates · validates input · logs all interactions]

    ROOT -->|weather / alerts| WA[weather_agent]
    ROOT -->|news / web search| SA[search_agent]
    ROOT -->|routes to safety| RT[route_agent]
    ROOT -->|questions| AT

    subgraph AT [answer_team — Sequential: validate &amp; refine]
      direction LR
      RES[research_agent] --> CRIT[critique_agent] --> REF[refine_agent]
    end

    WA --> NWS[(NWS API)]
    WA --> GEO[(Google Maps<br/>Geocoding)]
    RT --> DIR[(Google Maps<br/>Directions)]
    SA --> GS[(Google Search)]
    RES --> GS

    ROOT -. screens input .-> MA[(Cloud Model Armor)]
    ROOT -. logs .-> LOG[[Cloud Logging]]
```

## Requirements → implementation

| Case-study requirement | How it's met |
| --- | --- |
| Real-time weather **and** news alerts | `weather_agent` (NWS) + `search_agent` (Google Search) |
| Suggested routes to safety | `route_agent` → `get_directions` (Google Maps Directions API) |
| Log all user–agent interactions | `log_user_prompt` + `log_model_response` callbacks on the root |
| Validate input is appropriate; refuse off-mission | `screen_input_safety` (Model Armor) + the root's mission instruction |
| Ensure responses are valid, well-written, clear | `answer_team` Sequential workflow: research → **critique** → **refine** |
| Root agent describes capabilities + coordinates | `root_agent` (instruction + `sub_agents`) |
| Sub-agents: weather, search, routes, Q&A | `weather_agent`, `search_agent`, `route_agent`, `answer_team` |
| Deploy to Agent Platform | `deploy.py` → Vertex AI Agent Engine |
| Test code | `test_agents.py` (local events), `tests/` unit tests, `test_deployment.py` (deployed) |

## Agents

| Agent | Module | Role |
| --- | --- | --- |
| `root_agent` | `agent.py` | Coordinator; describes the mission, validates + logs, routes to sub-agents |
| `weather_agent` | `weather_agent.py` | US weather forecasts + alerts (NWS + geocoding, US-only) |
| `search_agent` | `search_agent.py` | Real-time internet search / news / alerts (Google Search) |
| `route_agent` | `route_agent.py` | Driving routes to safety (Google Maps Directions) |
| `answer_team` | `answer_team.py` | Sequential validate/refine: `research_agent → critique_agent → refine_agent` |

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab6
pip install -r requirements.txt
gcloud services enable aiplatform.googleapis.com geocoding-backend.googleapis.com \
    directions-backend.googleapis.com modelarmor.googleapis.com
cp readynow_agent/.env.example readynow_agent/.env
# edit readynow_agent/.env: GOOGLE_MAPS_API_KEY, GOOGLE_CLOUD_PROJECT,
# and (optional) MODEL_ARMOR_TEMPLATE_ID / MODEL_ARMOR_LOCATION
```

The Google Maps API key must have the **Geocoding** and **Directions** APIs
enabled.

## Run locally

```bash
adk run readynow_agent          # interactive
adk web --allow_origins='*'     # browser dev UI (Cloud Shell: Web Preview port 8000)
python test_agents.py           # scripted demo of all capabilities (prints events)
python -m unittest discover -s tests -v   # unit tests
```

Try: `what can you do?` · `weather in Miami, FL` · `any severe weather warnings
right now?` · `directions from Sacramento, CA to UC Davis Medical Center` · an
off-mission request (declined).

## Deploy to Agent Platform + verify

```bash
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export GOOGLE_CLOUD_LOCATION=us-central1
export STAGING_BUCKET=gs://${GOOGLE_CLOUD_PROJECT}-agent-staging
gsutil mb -l ${GOOGLE_CLOUD_LOCATION} ${STAGING_BUCKET} 2>/dev/null || true
export GOOGLE_MAPS_API_KEY=your-maps-key
export MODEL_ARMOR_TEMPLATE_ID=CL2modelArmor MODEL_ARMOR_LOCATION=us

python deploy.py                                    # deploys; prints resource name
export AGENT_ENGINE_RESOURCE=projects/.../reasoningEngines/NNNN
python list_deployments.py                          # confirm it's deployed
python test_deployment.py "any severe weather warnings right now?"   # test the deployed agent
python chat_deployed.py                             # interactive chat with the deployed agent
```

> Deployment pins `google-adk` to the Cloud Shell version (see `deploy.py`) so
> the deployed runtime matches local behavior.
