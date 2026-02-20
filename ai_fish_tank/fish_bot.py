from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, TYPE_CHECKING

from openai import OpenAI

from ai_fish_tank.game_logger import get_logger

if TYPE_CHECKING:
    from ai_fish_tank.playable_tank import Fish


@dataclass
class FishBot:
    """AI controller for a single fish."""

    fish: "Fish"
    client: OpenAI
    messages: List[Dict[str, str]] = field(default_factory=list)
    model: str = "gpt-4o-mini"

    def __post_init__(self) -> None:
        traits_str = ", ".join(self.fish.traits) if self.fish.traits else "curious"
        system_prompt = f"You are role playing the fish named {self.fish.name} represented by {self.fish.emoji}. Decide only one action for this fish each turn using the provided tools. Consider your past experiences and relationships when making decisions. Your personality traits: {traits_str}"
        self.messages.append({"role": "system", "content": system_prompt})

    def decide_action(self, tank_state: str, tools: List[Dict], round_num: int = 0) -> list:
        """Ask the LLM for the next action for this fish."""
        logger = get_logger()
        context_prompt = self.build_context_prompt(tank_state)
        self.messages.append({"role": "user", "content": context_prompt})

        logger.log_ai_prompt(
            fish_name=self.fish.name,
            round_num=round_num,
            prompt=context_prompt,
            tools=tools,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        tool_calls_data = []
        for call in tool_calls:
            tool_calls_data.append(
                {
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                }
            )

        raw_content = message.content or ""

        logger.log_ai_response(
            fish_name=self.fish.name,
            round_num=round_num,
            raw_response=raw_content,
            tool_calls=tool_calls_data,
            tokens_used=response.usage.total_tokens if response.usage else None,
            model=self.model,
        )

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

    def build_context_prompt(self, tank_state: str) -> str:
        """Build the context prompt including tank state, memories, and relationships."""
        parts = [tank_state]
        memories = self._format_recent_memories(5)
        if memories:
            parts.append("\n--- Your Recent Memories ---")
            parts.append(memories)
        relationships = self._format_relationships()
        if relationships:
            parts.append("\n--- Your Relationships ---")
            parts.append(relationships)
        return "\n".join(parts)

    def _format_recent_memories(self, count: int = 5) -> str:
        events = self.fish.memory.get_recent_events(count)
        if not events:
            return ""
        return "\n".join(f"- {event.description}" for event in events)

    def _format_relationships(self) -> str:
        lines = []
        for name, rel in self.fish.relationships.items():
            if rel.interactions_count > 0:
                summary = rel.get_summary()
                lines.append(f"- {name}: {summary}")
        return "\n".join(lines) if lines else ""
