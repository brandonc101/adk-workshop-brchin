"""Interactive chat with the agent deployed on Vertex AI Agent Engine.

Opens one session on the deployed engine and lets you type messages in a loop -
each is sent to the remote agent and its response is streamed back. The whole
conversation runs on the deployed engine (not locally).

Prerequisites (environment variables):
    GOOGLE_CLOUD_PROJECT    - your GCP project id
    GOOGLE_CLOUD_LOCATION   - region (default us-central1)
    AGENT_ENGINE_RESOURCE   - the deployed engine's resource name

Run from the ChallengeLab5 directory:

    python chat_deployed.py

Type 'exit' (or Ctrl-D) to quit.
"""

import os

import vertexai
from vertexai import agent_engines

from event_utils import extract_texts, get_field

USER_ID = "interactive_user"


def main() -> None:
    """Run an interactive chat loop against the deployed agent."""
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    resource = os.environ["AGENT_ENGINE_RESOURCE"]

    vertexai.init(project=project, location=location)
    remote_app = agent_engines.get(resource)
    print(f"Connected to deployed agent: {remote_app.resource_name}")

    session = remote_app.create_session(user_id=USER_ID)
    session_id = session["id"] if isinstance(session, dict) else session.id
    print("Chatting with the DEPLOYED agent. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query or query.lower() in ("exit", "quit"):
            break
        for event in remote_app.stream_query(
            user_id=USER_ID, session_id=session_id, message=query
        ):
            author = get_field(event, "author") or "agent"
            for text in extract_texts(event):
                print(f"{author}> {text}")
        print()


if __name__ == "__main__":
    main()
