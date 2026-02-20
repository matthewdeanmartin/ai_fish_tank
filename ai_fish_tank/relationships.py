"""Fish relationship system for tracking interactions between fish."""

from dataclasses import dataclass, field, asdict
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_fish_tank.memory import MemoryEvent
    from ai_fish_tank.game_logger import GameLogger


@dataclass
class Relationship:
    """Represents a fish's unilateral relationship with another fish."""

    other_fish_name: str
    trust: float = 0.0
    fear: float = 0.0
    friendship: float = 0.0
    interactions_count: int = 0
    last_interaction_round: int = 0
    fish_name: str | None = None
    logger: "GameLogger | None" = None

    def _log_change(self, changes: dict[str, float], trigger_event: str, round_num: int) -> None:
        if self.logger and self.fish_name:
            self.logger.log_relationship_change(
                fish_name=self.fish_name,
                other_fish_name=self.other_fish_name,
                round_num=round_num,
                changes=changes,
                new_values={
                    "trust": self.trust,
                    "fear": self.fear,
                    "friendship": self.friendship,
                },
                trigger_event=trigger_event,
            )

    def update_from_event(self, event: "MemoryEvent") -> None:
        self.interactions_count += 1
        self.last_interaction_round = event.round

        changes = {}
        if event.event_type == "attack" or event.event_type == "attacked":
            old_fear = self.fear
            old_trust = self.trust
            old_friendship = self.friendship
            self.fear = min(1.0, self.fear + 0.3)
            self.trust = max(-1.0, self.trust - 0.4)
            self.friendship = max(0.0, self.friendship - 0.2)
            changes = {
                "fear": self.fear - old_fear,
                "trust": self.trust - old_trust,
                "friendship": self.friendship - old_friendship,
            }
        elif event.event_type == "speak" or event.event_type == "spoke":
            emotional = event.emotional_weight
            old_trust = self.trust
            old_friendship = self.friendship
            if emotional > 0:
                self.friendship = min(1.0, self.friendship + 0.1)
                self.trust = min(1.0, self.trust + 0.05)
            elif emotional < 0:
                self.trust = max(-1.0, self.trust - 0.1)
            changes = {
                "trust": self.trust - old_trust,
                "friendship": self.friendship - old_friendship,
            }
        elif event.event_type == "shared_food":
            old_trust = self.trust
            old_friendship = self.friendship
            self.trust = min(1.0, self.trust + 0.2)
            self.friendship = min(1.0, self.friendship + 0.15)
            changes = {
                "trust": self.trust - old_trust,
                "friendship": self.friendship - old_friendship,
            }
        elif event.event_type == "observed_attack":
            if event.actor == self.other_fish_name:
                old_fear = self.fear
                old_trust = self.trust
                self.fear = min(1.0, self.fear + 0.15)
                self.trust = max(-1.0, self.trust - 0.2)
                changes = {
                    "fear": self.fear - old_fear,
                    "trust": self.trust - old_trust,
                }
        elif event.event_type == "observed_kindness":
            old_trust = self.trust
            old_friendship = self.friendship
            self.trust = min(1.0, self.trust + 0.1)
            self.friendship = min(1.0, self.friendship + 0.1)
            changes = {
                "trust": self.trust - old_trust,
                "friendship": self.friendship - old_friendship,
            }

        if changes:
            self._log_change(changes, event.event_type, event.round)

    def decay(self, rounds_since_interaction: int, decay_rate: float = 0.01) -> None:
        decay_factor = 1 - decay_rate * rounds_since_interaction
        self.friendship = max(0.0, self.friendship * decay_factor)
        self.fear = max(0.0, self.fear * decay_factor)
        self.trust = self.trust * decay_factor

    def get_summary(self) -> str:
        parts = []
        if self.friendship > 0.5:
            parts.append("friend")
        elif self.friendship > 0.2:
            parts.append("acquaintance")
        if self.fear > 0.5:
            parts.append("feared")
        elif self.fear > 0.2:
            parts.append("intimidating")
        if self.trust > 0.5:
            parts.append("trusted")
        elif self.trust < -0.3:
            parts.append("untrustworthy")
        return ", ".join(parts) if parts else "neutral"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        return cls(
            other_fish_name=data["other_fish_name"],
            trust=data.get("trust", 0.0),
            fear=data.get("fear", 0.0),
            friendship=data.get("friendship", 0.0),
            interactions_count=data.get("interactions_count", 0),
            last_interaction_round=data.get("last_interaction_round", 0),
        )
