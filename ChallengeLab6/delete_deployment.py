"""Delete Agent Engine deployments by resource name.

Pass one or more resource names as arguments:

    python delete_deployment.py <resource_name> [<resource_name> ...]

Requires GOOGLE_CLOUD_PROJECT (and optionally GOOGLE_CLOUD_LOCATION).
"""

import os
import sys

import vertexai
from vertexai import agent_engines


def main() -> None:
    """Delete each Agent Engine deployment named on the command line."""
    if len(sys.argv) < 2:
        print("Usage: python delete_deployment.py <resource_name> [...]")
        return

    vertexai.init(
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )
    for name in sys.argv[1:]:
        agent_engines.get(name).delete(force=True)
        print("deleted:", name)


if __name__ == "__main__":
    main()
