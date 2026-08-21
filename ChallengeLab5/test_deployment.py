"""Test the qa_agent deployed on Vertex AI Agent Engine.

Connects to the deployed agent by resource name, opens a session, and sends a
greeting and a question - verifying the deployment is live and responding.

Prerequisites (environment variables):
    GOOGLE_CLOUD_PROJECT    - your GCP project id
    GOOGLE_CLOUD_LOCATION   - region (default us-central1)
    AGENT_ENGINE_RESOURCE   - the resource name printed by deploy.py

Run from the ChallengeLab5 directory:

    python test_deployment.py
"""

import os

import vertexai
from vertexai import agent_engines

USER_ID = "test_user"

QUERIES = [
    "Hi there!",
    "What is the tallest mountain in the world, and how tall is it?",
]


def _print_text(event) -> None:
    """Print any text parts contained in a streamed Agent Engine event."""
    content = event.get("content") if isinstance(event, dict) else None
    if not content:
        return
    for part in content.get("parts", []):
        text = part.get("text")
        if text and text.strip():
            print(text.strip())


def main() -> None:
    """Query the deployed agent and print its responses."""
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    resource = os.environ["AGENT_ENGINE_RESOURCE"]

    vertexai.init(project=project, location=location)

    remote_app = agent_engines.get(resource)
    print("Connected to deployed agent:", remote_app.resource_name)

    session = remote_app.create_session(user_id=USER_ID)
    session_id = session["id"] if isinstance(session, dict) else session.id

    for query in QUERIES:
        print(f"\n{'=' * 60}\nQUERY: {query}\n{'=' * 60}")
        for event in remote_app.stream_query(
            user_id=USER_ID, session_id=session_id, message=query
        ):
            _print_text(event)


if __name__ == "__main__":
    main()
