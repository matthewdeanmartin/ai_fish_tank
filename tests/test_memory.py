import pytest

from ai_fish_tank.memory import FishMemory, MemoryEvent


def test_memory_event_to_dict():
    event = MemoryEvent(
        round=1,
        event_type="move",
        actor="Nemo",
        target=None,
        location=(5, 5),
        description="Nemo moved north.",
        emotional_weight=0.0,
    )
    data = event.to_dict()
    assert data["round"] == 1
    assert data["event_type"] == "move"
    assert data["actor"] == "Nemo"
    assert data["location"] == [5, 5]


def test_memory_event_from_dict():
    data = {
        "round": 2,
        "event_type": "attack",
        "actor": "Dory",
        "target": "Nemo",
        "location": [3, 4],
        "description": "Dory attacked Nemo.",
        "emotional_weight": -0.5,
    }
    event = MemoryEvent.from_dict(data)
    assert event.round == 2
    assert event.event_type == "attack"
    assert event.target == "Nemo"
    assert event.location == (3, 4)


def test_fish_memory_add_event():
    memory = FishMemory()
    event = MemoryEvent(round=1, event_type="move", actor="Nemo", description="Nemo moved.")
    memory.add_event(event)
    assert len(memory.events) == 1
    assert memory.events[0].actor == "Nemo"


def test_fish_memory_max_events():
    memory = FishMemory(max_events=5)
    for index in range(10):
        event = MemoryEvent(round=index, event_type="move", actor="Nemo", description=f"Move {index}")
        memory.add_event(event)
    assert len(memory.events) == 5
    assert memory.events[0].round == 5


def test_fish_memory_get_recent_events():
    memory = FishMemory()
    for index in range(10):
        event = MemoryEvent(round=index, event_type="move", actor="Nemo", description=f"Move {index}")
        memory.add_event(event)
    recent = memory.get_recent_events(3)
    assert len(recent) == 3
    assert recent[0].round == 7
    assert recent[2].round == 9


def test_fish_memory_get_events_about():
    memory = FishMemory()
    memory.add_event(MemoryEvent(round=1, event_type="move", actor="Nemo", target=None, description="Nemo moved."))
    memory.add_event(MemoryEvent(round=2, event_type="attack", actor="Dory", target="Nemo", description="Dory attacked Nemo."))
    memory.add_event(MemoryEvent(round=3, event_type="speak", actor="Nemo", description="Nemo spoke."))
    events = memory.get_events_about("Nemo")
    assert len(events) == 3


def test_fish_memory_forget_old_events():
    memory = FishMemory(memory_decay_rounds=5)
    for index in range(10):
        event = MemoryEvent(round=index, event_type="move", actor="Nemo", description=f"Move {index}")
        memory.add_event(event)
    memory.forget_old_events(current_round=10)
    assert len(memory.events) == 5
    assert memory.events[0].round == 5


def test_fish_memory_serialization():
    memory = FishMemory()
    memory.add_event(MemoryEvent(round=1, event_type="move", actor="Nemo", location=(5, 5), description="Nemo moved."))
    data = memory.to_dict()
    restored = FishMemory.from_dict(data)
    assert len(restored.events) == 1
    assert restored.events[0].actor == "Nemo"
