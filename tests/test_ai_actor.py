import json
from types import SimpleNamespace

from ai_fish_tank import playable_tank


class FakeClient:
    """Simple fake OpenAI client that returns one move call."""

    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, *args, **kwargs):
        call = SimpleNamespace(
            id="1",
            function=SimpleNamespace(
                name="move",
                arguments=json.dumps({"fish": "Nemo", "direction": "north"}),
            ),
        )
        message = SimpleNamespace(tool_calls=[call])
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_ai_run_moves_fish(monkeypatch):
    monkeypatch.setattr(playable_tank, "OpenAI", lambda: FakeClient())
    tank = playable_tank.ai_run(max_rounds=1)
    nemo = next(f for f in tank.fishes if f.name == "Nemo")
    assert nemo.position == (5, 4)
