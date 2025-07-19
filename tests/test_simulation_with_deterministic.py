from unittest.mock import patch

import pytest

from ai_fish_tank.simulated_tank import Fish, FishTank


@pytest.fixture
def fixed_fish_tank():
    fish_list = [
        Fish("Goldie", (0, 0), "Goldfish", "curious", "🐠", "Exploring the tank"),
        Fish("Bubbles", (1, 1), "Betta", "timid", "🐟", "Finding a quiet spot"),
        Fish("Finley", (2, 2), "Angelfish", "bold", "🐡", "Patrolling territory"),
        Fish("Stripe", (3, 3), "Zebra Fish", "aggressive", "🐙", "Challenging rivals"),
        Fish("Glimmer", (4, 4), "Guppy", "peaceful", "🦐", "Socializing with others"),
    ]
    return FishTank(fish_list=fish_list)


def test_update_tank_with_fake_response(fixed_fish_tank):
    fake_story = (
        "---start tank---\n"
        "🐠⬜⬜⬜⬜\n"
        "⬜🐟⬜⬜⬜\n"
        "⬜⬜🐡⬜⬜\n"
        "⬜⬜⬜🐙⬜\n"
        "⬜⬜⬜⬜🦐\n"
        "---end tank---\n"
        "---start story---\n"
        "Each fish gently swam to a new spot in the tank, exploring their surroundings.\n"
        "---end story---"
    )
    fixed_fish_tank.update_tank(fake_story)
    positions = [fish.position for fish in fixed_fish_tank.fish_list]
    assert sorted(positions) == [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]


def test_generate_story_deterministic(fixed_fish_tank):
    # Patch OpenAI call to return a deterministic fake story
    with patch("ai_fish_tank.simulated_tank.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_chat = mock_client.chat
        mock_completions = mock_chat.completions
        mock_completions.create.return_value.choices = [
            type("obj", (object,), {"message": type("msg", (object,), {"content": "Fake story here"})})
        ]

        story = fixed_fish_tank.generate_story()
        assert story == "Fake story here"
