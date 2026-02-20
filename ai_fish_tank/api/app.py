"""FastAPI application for serving fish tank game data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from ai_fish_tank.session import SessionManager, GameSession

app = FastAPI(title="AI Fish Tank Viewer", version="0.1.0")

LOG_DIR = Path("logs")
session_manager = SessionManager(log_dir=LOG_DIR)


def read_jsonl_events(session_id: str, since_timestamp: str | None = None) -> list[dict[str, Any]]:
    events = []
    log_file = LOG_DIR / f"session_{session_id}.jsonl"
    if not log_file.exists():
        return events

    with open(log_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if since_timestamp:
                    if event.get("timestamp", "") > since_timestamp:
                        events.append(event)
                else:
                    events.append(event)
            except json.JSONDecodeError:
                continue
    return events


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<html><body><h1>AI Fish Tank</h1><p>Static files not found.</p></body></html>")


@app.get("/api/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    sessions = session_manager.list_sessions()
    return [session.to_dict() for session in sessions]


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    session = session_manager.load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.get("/api/sessions/{session_id}/events")
async def get_session_events(session_id: str, since: str | None = None) -> list[dict[str, Any]]:
    events = read_jsonl_events(session_id, since)
    if not events and not (LOG_DIR / f"session_{session_id}.jsonl").exists():
        raise HTTPException(status_code=404, detail="Session not found")
    return events


@app.get("/api/sessions/{session_id}/fish")
async def get_session_fish(session_id: str) -> list[dict[str, Any]]:
    session = session_manager.load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    events = read_jsonl_events(session_id)

    fish_data = {}
    for fish_info in session.fish_roster:
        fish_data[fish_info.name] = {
            "name": fish_info.name,
            "emoji": fish_info.emoji,
            "traits": fish_info.traits,
            "likes_to_eat": fish_info.likes_to_eat,
            "position": list(fish_info.position),
            "monologue": "",
            "memories": [],
            "relationships": {},
        }

    for event in events:
        event_type = event.get("event_type")
        data = event.get("data", {})
        fish_name = event.get("fish_name")

        if event_type == "round_end":
            for fish_state in data.get("fish_states", []):
                name = fish_state.get("name")
                if name in fish_data:
                    fish_data[name]["position"] = fish_state.get("position", fish_data[name]["position"])
                    fish_data[name]["monologue"] = fish_state.get("monologue", "")

        if event_type == "memory_event" and fish_name and fish_name in fish_data:
            fish_data[fish_name]["memories"].append(data)

        if event_type == "relationship_change" and fish_name and fish_name in fish_data:
            other_fish = data.get("other_fish")
            if other_fish:
                fish_data[fish_name]["relationships"][other_fish] = data.get("new_values", {})

        if event_type == "ai_response" and fish_name and fish_name in fish_data:
            fish_data[fish_name]["last_ai_response"] = data

    return list(fish_data.values())


@app.get("/api/sessions/{session_id}/state")
async def get_session_state(session_id: str) -> dict[str, Any]:
    session = session_manager.load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    events = read_jsonl_events(session_id)

    last_tank_state = ""
    last_round = 0
    for event in reversed(events):
        if event.get("event_type") == "round_start":
            last_tank_state = event.get("data", {}).get("tank_state", "")
            last_round = event.get("round", 0)
            break

    return {
        "session_id": session_id,
        "tank_width": session.tank_width,
        "tank_height": session.tank_height,
        "current_round": last_round,
        "tank_state": last_tank_state,
        "game_ended": session.end_time is not None,
        "winner": session.winner,
        "survivors": session.survivors,
    }


@app.get("/api/live")
async def get_live_session() -> dict[str, Any]:
    session = session_manager.get_latest_session()
    if session is None:
        raise HTTPException(status_code=404, detail="No sessions found")
    return session.to_dict()


@app.get("/api/live/events")
async def get_live_events(since: str | None = None) -> list[dict[str, Any]]:
    session = session_manager.get_latest_session()
    if session is None:
        raise HTTPException(status_code=404, detail="No sessions found")
    return read_jsonl_events(session.session_id, since)


@app.get("/api/live/fish")
async def get_live_fish() -> list[dict[str, Any]]:
    session = session_manager.get_latest_session()
    if session is None:
        raise HTTPException(status_code=404, detail="No sessions found")
    return await get_session_fish(session.session_id)


@app.get("/api/live/state")
async def get_live_state() -> dict[str, Any]:
    session = session_manager.get_latest_session()
    if session is None:
        raise HTTPException(status_code=404, detail="No sessions found")
    return await get_session_state(session.session_id)


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
