"""Structured JSON logging for game events and AI decisions."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
import uuid


class GameLogger:
    """Thread-safe logger that writes structured JSON events to a file."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        log_dir: Path | None = None,
        session_id: str | None = None,
    ):
        if self._initialized:
            return

        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id or self._generate_session_id()
        self.session_start_time = datetime.now(timezone.utc)
        self._file_lock = Lock()
        self._log_file: Path | None = None
        self._initialized = True

    def _generate_session_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"{timestamp}_{short_uuid}"

    @property
    def log_file(self) -> Path:
        if self._log_file is None:
            self._log_file = self.log_dir / f"session_{self.session_id}.jsonl"
        return self._log_file

    def log_event(
        self,
        event_type: str,
        data: dict[str, Any],
        round_num: int = 0,
        fish_name: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Log a structured event to the JSON lines file."""
        event = {
            "session_id": self.session_id,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "round": round_num,
            "event_type": event_type,
            "fish_name": fish_name,
            "data": data,
        }

        with self._file_lock:
            with open(self.log_file, "a", encoding="utf-8") as file:
                file.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    def log_ai_prompt(
        self,
        fish_name: str,
        round_num: int,
        prompt: str,
        tools: list[dict] | None = None,
    ) -> None:
        """Log an AI prompt sent to the LLM."""
        self.log_event(
            event_type="ai_prompt",
            round_num=round_num,
            fish_name=fish_name,
            data={
                "prompt": prompt,
                "tools": tools,
            },
        )

    def log_ai_response(
        self,
        fish_name: str,
        round_num: int,
        raw_response: str,
        tool_calls: list[dict],
        tokens_used: int | None = None,
        model: str | None = None,
    ) -> None:
        """Log an AI response from the LLM."""
        self.log_event(
            event_type="ai_response",
            round_num=round_num,
            fish_name=fish_name,
            data={
                "raw_response": raw_response,
                "tool_calls": tool_calls,
                "tokens_used": tokens_used,
                "model": model,
            },
        )

    def log_fish_action(
        self,
        fish_name: str,
        round_num: int,
        action: str,
        success: bool,
        details: dict[str, Any],
    ) -> None:
        """Log a fish action (move, eat, attack, speak)."""
        self.log_event(
            event_type="fish_action",
            round_num=round_num,
            fish_name=fish_name,
            data={
                "action": action,
                "success": success,
                **details,
            },
        )

    def log_memory_event(
        self,
        fish_name: str,
        round_num: int,
        memory_event: dict[str, Any],
    ) -> None:
        """Log a memory event being added to a fish's memory."""
        self.log_event(
            event_type="memory_event",
            round_num=round_num,
            fish_name=fish_name,
            data=memory_event,
        )

    def log_relationship_change(
        self,
        fish_name: str,
        other_fish_name: str,
        round_num: int,
        changes: dict[str, float],
        new_values: dict[str, float],
        trigger_event: str,
    ) -> None:
        """Log a relationship change between two fish."""
        self.log_event(
            event_type="relationship_change",
            round_num=round_num,
            fish_name=fish_name,
            data={
                "other_fish": other_fish_name,
                "changes": changes,
                "new_values": new_values,
                "trigger_event": trigger_event,
            },
        )

    def log_game_start(
        self,
        fish_roster: list[dict[str, Any]],
        tank_size: tuple[int, int],
        config: dict[str, Any] | None = None,
    ) -> None:
        """Log game start with initial state."""
        self.log_event(
            event_type="game_start",
            data={
                "fish_roster": fish_roster,
                "tank_size": tank_size,
                "config": config or {},
            },
        )

    def log_game_end(
        self,
        final_round: int,
        winner: str | None,
        survivors: list[str],
    ) -> None:
        """Log game end with final state."""
        self.log_event(
            event_type="game_end",
            round_num=final_round,
            data={
                "winner": winner,
                "survivors": survivors,
                "total_rounds": final_round,
            },
        )

    def log_round_start(self, round_num: int, tank_state: str) -> None:
        """Log the start of a new round."""
        self.log_event(
            event_type="round_start",
            round_num=round_num,
            data={"tank_state": tank_state},
        )

    def log_round_end(self, round_num: int, fish_states: list[dict[str, Any]]) -> None:
        """Log the end of a round with fish states."""
        self.log_event(
            event_type="round_end",
            round_num=round_num,
            data={"fish_states": fish_states},
        )


def get_logger() -> GameLogger:
    """Get the singleton GameLogger instance."""
    return GameLogger()


def reset_logger() -> None:
    """Reset the singleton instance (useful for testing)."""
    with GameLogger._lock:
        GameLogger._instance = None
