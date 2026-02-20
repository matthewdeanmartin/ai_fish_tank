let lastTimestamp = null;
let allEvents = [];
let sessionEnded = false;
const POLL_INTERVAL = 1000;

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

function formatTime(isoString) {
    if (!isoString) return "-";
    const date = new Date(isoString);
    return date.toLocaleTimeString();
}

function truncate(text, maxLen = 100) {
    if (!text) return "";
    return text.length > maxLen ? text.substring(0, maxLen) + "..." : text;
}

function updateStatusBar(state) {
    const sessionId = document.getElementById("session-id");
    const currentRound = document.getElementById("current-round");
    const gameStatus = document.getElementById("game-status");
    
    if (state.session_id) {
        sessionId.textContent = state.session_id.substring(0, 20) + "...";
    }
    currentRound.textContent = state.current_round || 0;
    
    if (state.game_ended) {
        gameStatus.textContent = state.winner ? `Winner: ${state.winner}` : "Game Over";
        gameStatus.style.color = "#ff6b6b";
        sessionEnded = true;
    } else {
        gameStatus.textContent = "Running";
        gameStatus.style.color = "#00d4ff";
    }
}

function renderTank(tankState) {
    const display = document.getElementById("tank-display");
    if (!tankState) {
        display.textContent = "Waiting for game data...";
        return;
    }
    display.textContent = tankState;
}

function renderFish(fishData) {
    const container = document.getElementById("fish-panels");
    if (!fishData || fishData.length === 0) {
        container.innerHTML = "<p>No fish data available</p>";
        return;
    }

    container.innerHTML = fishData.map(fish => `
        <div class="fish-card">
            <div class="fish-header">
                <span class="fish-emoji">${fish.emoji || "🐟"}</span>
                <div>
                    <strong>${fish.name}</strong>
                    <div class="fish-traits">${(fish.traits || []).join(", ")}</div>
                </div>
            </div>
            ${fish.monologue ? `<div class="fish-monologue">"${truncate(fish.monologue, 150)}"</div>` : ""}
            ${fish.memories && fish.memories.length > 0 ? `
                <div class="fish-memories">
                    <strong>Recent memories:</strong>
                    <ul>
                        ${fish.memories.slice(-3).map(m => `<li>${truncate(m.description, 60)}</li>`).join("")}
                    </ul>
                </div>
            ` : ""}
            ${fish.relationships && Object.keys(fish.relationships).length > 0 ? `
                <div style="margin-top: 8px;">
                    <strong>Relationships:</strong><br>
                    ${Object.entries(fish.relationships).map(([name, rel]) => `
                        <span class="relationship">${name}: T=${(rel.trust || 0).toFixed(1)} F=${(rel.fear || 0).toFixed(1)}</span>
                    `).join("")}
                </div>
            ` : ""}
        </div>
    `).join("");
}

function renderAIDecisions(events) {
    const container = document.getElementById("ai-decisions");
    const aiEvents = events.filter(e => 
        e.event_type === "ai_prompt" || e.event_type === "ai_response"
    ).slice(-20).reverse();

    if (aiEvents.length === 0) {
        container.innerHTML = "<p>No AI decisions yet...</p>";
        return;
    }

    let html = "";
    let currentPrompt = null;

    for (const event of aiEvents) {
        if (event.event_type === "ai_prompt") {
            currentPrompt = event;
        } else if (event.event_type === "ai_response" && currentPrompt) {
            const toolCalls = event.data?.tool_calls || [];
            const toolCallsStr = toolCalls.map(tc => 
                `${tc.name}(${tc.arguments ? truncate(tc.arguments, 50) : ""})`
            ).join(", ");

            html += `
                <div class="ai-decision">
                    <div style="color: #00d4ff; margin-bottom: 5px;">
                        <strong>${event.fish_name || "Unknown"}</strong> 
                        <span style="color: #666; font-size: 0.8em;">Round ${event.round}</span>
                    </div>
                    <div class="ai-prompt">${truncate(currentPrompt.data?.prompt, 200)}</div>
                    <div class="ai-response">
                        <strong>Action:</strong> ${toolCallsStr || "No action"}
                        ${event.data?.tokens_used ? `<span style="color: #666;"> (${event.data.tokens_used} tokens)</span>` : ""}
                    </div>
                </div>
            `;
            currentPrompt = null;
        }
    }

    container.innerHTML = html || "<p>No AI decisions yet...</p>";
}

function renderEventFeed(events) {
    const container = document.getElementById("event-feed");
    const displayEvents = events.slice(-50).reverse();

    if (displayEvents.length === 0) {
        container.innerHTML = "<p>No events yet...</p>";
        return;
    }

    container.innerHTML = displayEvents.map(event => {
        let details = "";
        const data = event.data || {};

        switch (event.event_type) {
            case "fish_action":
                details = `${data.action}${data.success ? "" : " (failed)"} - ${JSON.stringify(data).substring(0, 80)}`;
                break;
            case "ai_response":
                const tc = data.tool_calls || [];
                details = tc.map(t => `${t.name}(${truncate(t.arguments, 30)})`).join(", ") || "No action";
                break;
            case "memory_event":
                details = truncate(data.description, 60);
                break;
            case "relationship_change":
                details = `with ${data.other_fish}: ${JSON.stringify(data.changes)}`;
                break;
            case "game_start":
                details = `${data.fish_roster?.length || 0} fish`;
                break;
            case "game_end":
                details = `Winner: ${data.winner || "None"}`;
                break;
            default:
                details = truncate(JSON.stringify(data), 60);
        }

        return `
            <div class="event">
                <span class="event-type ${event.event_type}">${event.event_type}</span>
                <span class="event-time">${formatTime(event.timestamp)}</span>
                ${event.fish_name ? `<strong style="color: #00d4ff;">${event.fish_name}</strong>: ` : ""}
                <span>${details}</span>
            </div>
        `;
    }).join("");
}

async function refresh() {
    try {
        const state = await fetchJSON("/api/live/state");
        updateStatusBar(state);

        const fish = await fetchJSON("/api/live/fish");
        renderFish(fish);

        renderTank(state.tank_state);

        const events = await fetchJSON("/api/live/events?since=" + (lastTimestamp || ""));
        if (events.length > 0) {
            allEvents = allEvents.concat(events);
            lastTimestamp = events[events.length - 1].timestamp;
            renderAIDecisions(allEvents);
            renderEventFeed(allEvents);
        }

        document.getElementById("last-update").textContent = new Date().toLocaleTimeString();

        if (!sessionEnded) {
            setTimeout(refresh, POLL_INTERVAL);
        }
    } catch (error) {
        console.error("Refresh error:", error);
        document.getElementById("last-update").textContent = "Error: " + error.message;
        setTimeout(refresh, POLL_INTERVAL * 2);
    }
}

document.addEventListener("DOMContentLoaded", refresh);
