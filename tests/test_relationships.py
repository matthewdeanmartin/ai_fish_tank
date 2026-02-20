import pytest

from ai_fish_tank.relationships import Relationship
from ai_fish_tank.memory import MemoryEvent


def test_relationship_initial_state():
    rel = Relationship(other_fish_name="Dory")
    assert rel.trust == 0.0
    assert rel.fear == 0.0
    assert rel.friendship == 0.0
    assert rel.interactions_count == 0


def test_relationship_update_from_attack():
    rel = Relationship(other_fish_name="Nemo")
    event = MemoryEvent(
        round=1,
        event_type="attack",
        actor="Nemo",
        target="Dory",
        description="Nemo attacked Dory.",
    )
    rel.update_from_event(event)
    assert rel.fear > 0
    assert rel.trust < 0
    assert rel.interactions_count == 1


def test_relationship_update_from_friendly_speak():
    rel = Relationship(other_fish_name="Nemo")
    event = MemoryEvent(
        round=1,
        event_type="speak",
        actor="Nemo",
        description="Nemo said hello.",
        emotional_weight=0.5,
    )
    rel.update_from_event(event)
    assert rel.friendship > 0
    assert rel.trust > 0


def test_relationship_update_from_negative_speak():
    rel = Relationship(other_fish_name="Nemo")
    event = MemoryEvent(
        round=1,
        event_type="speak",
        actor="Nemo",
        description="Nemo was rude.",
        emotional_weight=-0.5,
    )
    rel.update_from_event(event)
    assert rel.trust < 0


def test_relationship_decay():
    rel = Relationship(other_fish_name="Nemo", fear=0.8, friendship=0.6, trust=0.4)
    rel.decay(rounds_since_interaction=10, decay_rate=0.01)
    assert rel.fear < 0.8
    assert rel.friendship < 0.6
    assert rel.trust < 0.4


def test_relationship_get_summary_friend():
    rel = Relationship(other_fish_name="Nemo", friendship=0.7, trust=0.6)
    summary = rel.get_summary()
    assert "friend" in summary
    assert "trusted" in summary


def test_relationship_get_summary_feared():
    rel = Relationship(other_fish_name="Nemo", fear=0.8)
    summary = rel.get_summary()
    assert "feared" in summary


def test_relationship_serialization():
    rel = Relationship(
        other_fish_name="Dory",
        trust=0.5,
        fear=0.2,
        friendship=0.7,
        interactions_count=5,
        last_interaction_round=10,
    )
    data = rel.to_dict()
    restored = Relationship.from_dict(data)
    assert restored.other_fish_name == "Dory"
    assert restored.trust == 0.5
    assert restored.fear == 0.2
    assert restored.friendship == 0.7
    assert restored.interactions_count == 5
