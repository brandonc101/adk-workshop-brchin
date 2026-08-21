# ADK Agent on Agent Platform — Challenge Lab 5 (deploy to Agent Engine)

Builds on Challenge Lab 4. The same multi-agent `qa_agent` (coordinator →
greeter / weather / answer team) is **deployed to Vertex AI Agent Engine**
(the "Agent Platform"), which hosts and runs the agent for you, and then tested
remotely.

## Files added for deployment

| File | Purpose |
| --- | --- |
| `deploy.py` | Wraps `root_agent` in an `AdkApp` and deploys it to Vertex AI Agent Engine |
| `test_deployment.py` | Connects to the deployed agent, opens a session, and queries it |

The agent itself (`qa_agent/`) is unchanged from Lab 4.

## Setup (Google Cloud Shell)

```bash
cd ChallengeLab5
pip install -r requirements.txt

# APIs used by the agent + Agent Engine
gcloud services enable aiplatform.googleapis.com \
    geocoding-backend.googleapis.com modelarmor.googleapis.com

# A GCS staging bucket for the deployment artifacts
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export GOOGLE_CLOUD_LOCATION=us-central1
export STAGING_BUCKET=gs://${GOOGLE_CLOUD_PROJECT}-agent-staging
gsutil mb -l ${GOOGLE_CLOUD_LOCATION} ${STAGING_BUCKET} 2>/dev/null || true

# Runtime config for the deployed agent (optional but recommended)
export GOOGLE_MAPS_API_KEY=your-maps-key
export MODEL_ARMOR_TEMPLATE_ID=CL2modelArmor
export MODEL_ARMOR_LOCATION=us
```

## Deploy

```bash
python deploy.py
```

This uploads `qa_agent/`, builds the runtime, and creates the Agent Engine
resource (several minutes). It prints a **resource name** like
`projects/…/locations/us-central1/reasoningEngines/1234567890`. Save it:

```bash
export AGENT_ENGINE_RESOURCE=projects/.../reasoningEngines/1234567890
```

## Verify it's deployed and running

```bash
# List deployed agents
gcloud ai reasoning-engines list --region=${GOOGLE_CLOUD_LOCATION}

# Query the deployed agent (greeting + question)
python test_deployment.py
```

`test_deployment.py` connects by `AGENT_ENGINE_RESOURCE`, creates a session, and
streams a greeting and a question, printing the deployed agent's responses — so
you can confirm it is live and answering.

You can also see it in the Console: **Vertex AI → Agent Engine**.

## Local checks (no deployment needed)

```bash
python -m unittest discover -s tests -v    # unit tests
python test_agents.py                      # local event-stream demo
adk run qa_agent                           # interactive, locally
```

## Clean up (optional)

```bash
gcloud ai reasoning-engines delete ${AGENT_ENGINE_RESOURCE} --region=${GOOGLE_CLOUD_LOCATION}
```

> **Note on import paths:** the Agent Engine SDK is evolving. If `deploy.py`
> errors on `from vertexai.preview import reasoning_engines`, your installed
> `google-cloud-aiplatform` may expose it as `from vertexai import agent_engines`
> with `agent_engines.AdkApp` — adjust the two import lines accordingly.
