"""Deploy the qa_agent multi-agent system to Vertex AI Agent Engine.

Agent Engine (part of the Vertex AI "Agent Platform") hosts and runs ADK agents
for you. This script wraps the root agent in an ``AdkApp`` and deploys it.

Prerequisites (environment variables):
    GOOGLE_CLOUD_PROJECT   - your GCP project id
    GOOGLE_CLOUD_LOCATION  - region, e.g. us-central1 (default)
    STAGING_BUCKET         - a GCS bucket for staging, e.g. gs://my-bucket
    GOOGLE_MAPS_API_KEY    - (optional) for the weather agent
    MODEL_ARMOR_TEMPLATE_ID / MODEL_ARMOR_LOCATION - (optional) input screening

Run from the ChallengeLab5 directory:

    python deploy.py

On success it prints the deployed agent's resource name - save it to test the
deployment (see test_deployment.py).
"""

import os

import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

from qa_agent.agent import root_agent


def main() -> None:
    """Deploy root_agent to Vertex AI Agent Engine and print its resource name."""
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = os.environ["STAGING_BUCKET"]  # e.g. gs://<project>-agent-staging

    vertexai.init(project=project, location=location, staging_bucket=staging_bucket)

    # AdkApp adapts an ADK agent to the Agent Engine runtime.
    app = reasoning_engines.AdkApp(agent=root_agent)

    print("Deploying to Vertex AI Agent Engine — this can take several minutes...")
    remote_app = agent_engines.create(
        agent_engine=app,
        display_name="qa-answer-team",
        description=(
            "Coordinator routing to a greeter, a US weather agent, and a "
            "search -> critique -> refine answer team."
        ),
        # Packages installed in the deployed runtime.
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]",
            "google-adk",
            "litellm",
            "requests",
            "python-dotenv",
            "google-cloud-modelarmor",
        ],
        # Local package(s) uploaded with the deployment.
        extra_packages=["qa_agent"],
        # Runtime configuration for the deployed agent.
        # NOTE: GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION are reserved by
        # Agent Engine (set automatically) - do NOT pass them here.
        env_vars={
            "MODEL_BACKEND": "gemini",
            # Route Gemini through Vertex AI in the deployed runtime (otherwise
            # the google-genai client defaults to the Developer API and fails
            # with no API key, which surfaces as a NoneType subscript error).
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # Pin a broadly-available model.
            "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", ""),
            "MODEL_ARMOR_TEMPLATE_ID": os.getenv("MODEL_ARMOR_TEMPLATE_ID", ""),
            "MODEL_ARMOR_LOCATION": os.getenv("MODEL_ARMOR_LOCATION", "us"),
        },
    )

    print("\nDeployed successfully!")
    print("Resource name:", remote_app.resource_name)
    print("\nSave it for testing:")
    print(f"  export AGENT_ENGINE_RESOURCE={remote_app.resource_name}")


if __name__ == "__main__":
    main()
