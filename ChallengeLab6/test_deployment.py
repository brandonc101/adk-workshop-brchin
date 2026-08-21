"""Test the readynow_agent deployed on Vertex AI Agent Engine.

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
import sys

import vertexai
from vertexai import agent_engines

from event_utils import extract_texts, get_field

USER_ID = "test_user"

QUERIES = [
    "Hi there!",
    "What is the tallest mountain in the world, and how tall is it?",
]


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

    # Use any messages passed on the command line, else the default demo pair.
    queries = sys.argv[1:] or QUERIES
    for query in queries:
        print(f"\n{'=' * 60}\nQUERY: {query}\n{'=' * 60}")
        saw_output = False
        last_event = None
        for event in remote_app.stream_query(
            user_id=USER_ID, session_id=session_id, message=query
        ):
            last_event = event
            author = get_field(event, "author") or "?"
            for text in extract_texts(event):
                print(f"[{author}] {text}")
                saw_output = True
        if not saw_output:
            # Nothing matched our text extraction - show the raw shape so we
            # can see what the deployed agent returned.
            print("(no text parts found; last raw event below)")
            print(repr(last_event)[:800])


if __name__ == "__main__":
    main()
