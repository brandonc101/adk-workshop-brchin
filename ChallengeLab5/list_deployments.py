"""List agents deployed to Vertex AI Agent Engine in this project/location.

A replacement for `gcloud ai reasoning-engines list`, which isn't available in
all gcloud versions. Run from the ChallengeLab5 directory:

    python list_deployments.py

Requires GOOGLE_CLOUD_PROJECT (and optionally GOOGLE_CLOUD_LOCATION).
"""

import os

import vertexai
from vertexai import agent_engines


def main() -> None:
    """Print each deployed agent's resource name and display name."""
    vertexai.init(
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )
    deployed = list(agent_engines.list())
    if not deployed:
        print("No deployed agents found in this project/location.")
        return
    for agent in deployed:
        print(agent.resource_name, "-", getattr(agent, "display_name", ""))


if __name__ == "__main__":
    main()
