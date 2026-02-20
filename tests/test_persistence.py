import json
import tempfile
from pathlib import Path

from ai_fish_tank.memory import FishMemory, MemoryEvent
from ai_fish_tank.relationships import Relationship
from ai_fish_tank.persistence import (
    save_fish_state,
    load_fish_state_data,
    apply_fish_state,
    save_all_fish,
    load_all_fish_data,
)


class MockFish:
    def __init__(self, name, emoji, position):
        self.name = name
        self.emoji = emoji
        self.position = position
        self.likes_to_eat = ["🌿"]
        self.traits = ["curious", "friendly"]
        self.memory = FishMemory()
        self.relationships = {}


def test_save_fish_state():
    fish = MockFish("Nemo", "🐟", (5, 5))
    fish.memory.add_event(MemoryEvent(round=1, event_type="move", actor="Nemo", description="Nemo moved."))
    fish.relationships["Dory"] = Relationship(other_fish_name="Dory", friendship=0.5)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "nemo.json"
        save_fish_state(fish, filepath)
        assert filepath.exists()
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        assert data["name"] == "Nemo"
        assert data["position"] == [5, 5]
        assert data["traits"] == ["curious", "friendly"]
        assert len(data["memory"]["events"]) == 1


def test_load_fish_state_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "nemo.json"
        data = {
            "name": "Nemo",
            "emoji": "🐟",
            "position": [3, 4],
            "likes_to_eat": ["🌿", "🌱"],
            "traits": ["brave"],
            "memory": {"events": [], "max_events": 100},
            "relationships": {},
        }
        with open(filepath, "w") as file:
            json.dump(data, file)
        loaded = load_fish_state_data(filepath)
        assert loaded["name"] == "Nemo"
        assert loaded["position"] == [3, 4]


def test_load_fish_state_data_missing_file():
    result = load_fish_state_data(Path("/nonexistent/path.json"))
    assert result is None


def test_apply_fish_state():
    fish = MockFish("Nemo", "🐟", (0, 0))
    data = {
        "position": [7, 8],
        "likes_to_eat": ["🌿", "🐛"],
        "traits": ["brave", "adventurous"],
        "memory": {
            "events": [{"round": 1, "event_type": "move", "actor": "Nemo", "description": "Moved."}],
            "max_events": 100,
        },
        "relationships": {"Dory": {"other_fish_name": "Dory", "trust": 0.5, "fear": 0.0, "friendship": 0.0, "interactions_count": 1, "last_interaction_round": 1}},
    }
    apply_fish_state(fish, data)
    assert fish.position == (7, 8)
    assert fish.likes_to_eat == ["🌿", "🐛"]
    assert fish.traits == ["brave", "adventurous"]
    assert len(fish.memory.events) == 1
    assert "Dory" in fish.relationships


def test_save_all_fish():
    fish1 = MockFish("Nemo", "🐟", (5, 5))
    fish2 = MockFish("Dory", "🐠", (2, 2))

    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir = Path(tmpdir) / "saves"
        save_all_fish([fish1, fish2], save_dir)
        assert (save_dir / "Nemo.json").exists()
        assert (save_dir / "Dory.json").exists()


def test_load_all_fish_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir = Path(tmpdir)
        nemo_data = {
            "name": "Nemo",
            "emoji": "🐟",
            "position": [5, 5],
            "likes_to_eat": ["🌿"],
            "traits": ["curious"],
            "memory": {"events": []},
            "relationships": {},
        }
        dory_data = {
            "name": "Dory",
            "emoji": "🐠",
            "position": [2, 2],
            "likes_to_eat": [],
            "traits": ["friendly"],
            "memory": {"events": []},
            "relationships": {},
        }
        with open(save_dir / "Nemo.json", "w") as file:
            json.dump(nemo_data, file)
        with open(save_dir / "Dory.json", "w") as file:
            json.dump(dory_data, file)
        all_data = load_all_fish_data(save_dir)
        assert "Nemo" in all_data
        assert "Dory" in all_data
        assert all_data["Nemo"]["position"] == [5, 5]
