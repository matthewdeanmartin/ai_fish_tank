"""Persistence utilities for saving and loading fish state."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, TYPE_CHECKING

from ai_fish_tank.memory import FishMemory
from ai_fish_tank.relationships import Relationship

if TYPE_CHECKING:
    from ai_fish_tank.playable_tank import Fish


def save_fish_state(fish: "Fish", filepath: Path) -> None:
    """Save a fish's state to a JSON file."""
    data = {
        "name": fish.name,
        "emoji": fish.emoji,
        "position": list(fish.position),
        "likes_to_eat": fish.likes_to_eat,
        "traits": fish.traits,
        "memory": fish.memory.to_dict(),
        "relationships": {name: rel.to_dict() for name, rel in fish.relationships.items()},
    }
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_fish_state_data(filepath: Path) -> dict[str, Any] | None:
    """Load fish state data from a JSON file."""
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def apply_fish_state(fish: "Fish", data: dict[str, Any]) -> None:
    """Apply loaded state data to a fish instance."""
    fish.position = tuple(data["position"])
    fish.likes_to_eat = data.get("likes_to_eat", [])
    fish.traits = data.get("traits", ["curious"])
    fish.memory = FishMemory.from_dict(data.get("memory", {}))
    fish.relationships = {name: Relationship.from_dict(rel_data) for name, rel_data in data.get("relationships", {}).items()}


def save_all_fish(fishes: list["Fish"], save_dir: Path) -> None:
    """Save all fish states to a directory."""
    save_dir.mkdir(parents=True, exist_ok=True)
    for fish in fishes:
        filepath = save_dir / f"{fish.name}.json"
        save_fish_state(fish, filepath)


def load_all_fish_data(save_dir: Path) -> dict[str, dict[str, Any]]:
    """Load all fish state data from a directory."""
    fish_data = {}
    if not save_dir.exists():
        return fish_data
    for filepath in save_dir.glob("*.json"):
        data = load_fish_state_data(filepath)
        if data and "name" in data:
            fish_data[data["name"]] = data
    return fish_data
