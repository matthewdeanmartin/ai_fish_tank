"""Fish memory system for remembering events and experiences."""

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_fish_tank.game_logger import GameLogger


@dataclass
class MemoryEvent:
    """Represents a single memory event in a fish's life."""

    round: int
    event_type: str
    actor: str
    target: str | None = None
    location: tuple[int, int] | None = None
    description: str = ""
    emotional_weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "event_type": self.event_type,
            "actor": self.actor,
            "target": self.target,
            "location": list(self.location) if self.location else None,
            "description": self.description,
            "emotional_weight": self.emotional_weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEvent":
        location = data.get("location")
        return cls(
            round=data["round"],
            event_type=data["event_type"],
            actor=data["actor"],
            target=data.get("target"),
            location=tuple(location) if location else None,
            description=data.get("description", ""),
            emotional_weight=data.get("emotional_weight", 0.0),
        )


@dataclass
class FishMemory:
    """Manages a fish's memory of events."""

    events: list[MemoryEvent] = field(default_factory=list)
    max_events: int = 100
    memory_decay_rounds: int = 50
    fish_name: str | None = None
    logger: "GameLogger | None" = None

    def add_event(self, event: MemoryEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]
        if self.logger and self.fish_name:
            self.logger.log_memory_event(
                fish_name=self.fish_name,
                round_num=event.round,
                memory_event=event.to_dict(),
            )

    def get_recent_events(self, count: int = 10) -> list[MemoryEvent]:
        return self.events[-count:] if self.events else []

    def get_events_about(self, fish_name: str) -> list[MemoryEvent]:
        return [event for event in self.events if event.actor == fish_name or event.target == fish_name]

    def get_food_locations(self) -> list[tuple[int, int]]:
        locations = []
        for event in self.events:
            if event.event_type == "ate" and event.location:
                locations.append(event.location)
            elif event.event_type == "spotted_food" and event.location:
                locations.append(event.location)
        return list(set(locations))

    def forget_old_events(self, current_round: int) -> None:
        cutoff = current_round - self.memory_decay_rounds
        self.events = [event for event in self.events if event.round >= cutoff]

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [event.to_dict() for event in self.events],
            "max_events": self.max_events,
            "memory_decay_rounds": self.memory_decay_rounds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FishMemory":
        memory = cls(
            max_events=data.get("max_events", 100),
            memory_decay_rounds=data.get("memory_decay_rounds", 50),
        )
        memory.events = [MemoryEvent.from_dict(event_data) for event_data in data.get("events", [])]
        return memory
