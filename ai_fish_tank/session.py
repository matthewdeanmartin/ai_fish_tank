"""Game session metadata management."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class FishInfo:
    """Snapshot of fish info at session start."""

    name: str
    emoji: str
    position: tuple[int, int]
    traits: list[str]
    likes_to_eat: list[str]


@dataclass
class GameSession:
    """Metadata for a game session."""

    session_id: str
    start_time: str
    end_time: str | None = None
    tank_width: int = 10
    tank_height: int = 8
    max_rounds: int = 5
    fish_roster: list[FishInfo] = field(default_factory=list)
    final_round: int = 0
    winner: str | None = None
    survivors: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fish_roster"] = [asdict(fish) for fish in self.fish_roster]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameSession":
        fish_roster = [FishInfo(**fish) for fish in data.get("fish_roster", [])]
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            tank_width=data.get("tank_width", 10),
            tank_height=data.get("tank_height", 8),
            max_rounds=data.get("max_rounds", 5),
            fish_roster=fish_roster,
            final_round=data.get("final_round", 0),
            winner=data.get("winner"),
            survivors=data.get("survivors", []),
            config=data.get("config", {}),
        )


class SessionManager:
    """Manages game session metadata files."""

    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_session_file(self, session_id: str) -> Path:
        return self.log_dir / f"session_{session_id}_meta.json"

    def save_session(self, session: GameSession) -> Path:
        filepath = self.get_session_file(session.session_id)
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(session.to_dict(), file, indent=2, ensure_ascii=False)
        return filepath

    def load_session(self, session_id: str) -> GameSession | None:
        filepath = self.get_session_file(session_id)
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        return GameSession.from_dict(data)

    def list_sessions(self) -> list[GameSession]:
        sessions = []
        for filepath in self.log_dir.glob("session_*_meta.json"):
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            sessions.append(GameSession.from_dict(data))
        sessions.sort(key=lambda session: session.start_time, reverse=True)
        return sessions

    def get_latest_session(self) -> GameSession | None:
        sessions = self.list_sessions()
        return sessions[0] if sessions else None

    def create_session(
        self,
        session_id: str,
        tank_width: int,
        tank_height: int,
        max_rounds: int,
        fish_roster: list[FishInfo],
        config: dict[str, Any] | None = None,
    ) -> GameSession:
        session = GameSession(
            session_id=session_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            tank_width=tank_width,
            tank_height=tank_height,
            max_rounds=max_rounds,
            fish_roster=fish_roster,
            config=config or {},
        )
        self.save_session(session)
        return session

    def end_session(
        self,
        session_id: str,
        final_round: int,
        winner: str | None,
        survivors: list[str],
    ) -> GameSession | None:
        session = self.load_session(session_id)
        if session is None:
            return None
        session.end_time = datetime.now(timezone.utc).isoformat()
        session.final_round = final_round
        session.winner = winner
        session.survivors = survivors
        self.save_session(session)
        return session
