"""Small pure helpers for the weather agent demo (``test_agent.py``).

Kept in a separate module (with no ADK/Vertex imports) so the logic can be
unit-tested in isolation.
"""


def select_cities(cli_args: list[str], default_cities: list[str]) -> list[str]:
    """Choose which cities the demo should run.

    Args:
        cli_args: City strings passed on the command line (typically
            ``sys.argv[1:]``).
        default_cities: The fallback list used when no CLI args are given.

    Returns:
        A new list of city strings: a copy of ``cli_args`` when it is
        non-empty, otherwise a copy of ``default_cities``. The inputs are
        never mutated.
    """
    return list(cli_args) if cli_args else list(default_cities)
