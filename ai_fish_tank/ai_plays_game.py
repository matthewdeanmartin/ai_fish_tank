"""Entrypoint for running the AI controlled fish tank game."""

from ai_fish_tank.playable_tank import ai_run


def main() -> None:
    """Run the AI actor game loop."""
    ai_run()


if __name__ == "__main__":
    main()