from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from ai_fish_tank.playable_tank import Fish


@dataclass
class FishBot:
    """AI controller for a single fish."""

    fish: Fish
    client: OpenAI
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        system_prompt = (
            f"You are role playing the fish named {self.fish.name} represented by {self.fish.emoji}. "
            "Decide only one action for this fish each turn using the provided tools."
        )
        self.messages.append({"role": "system", "content": system_prompt})

    def decide_action(self, tank_state: str, tools: list[dict]) -> list:
        """Ask the LLM for the next action for this fish."""
        self.messages.append({"role": "user", "content": tank_state})
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        self.messages.append(message)
        return tool_calls

    def record_tool_result(self, call, content: str) -> None:
        """Record the result of a tool call back to the conversation."""
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "name": call.function.name,
                "content": content,
            }
        )


