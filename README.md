# ai_fish_tank
Fish tank that has a story going on

## Usage

```bash
uv run python -m ai_fish_tank.api_server
uv run python -m ai_fish_tank
```

## Background

This is a terminal fish tank game/simulator that will have an AI component.

## AI is Game player

The playable_tank is a game. The goal is to have an AI play the game and provide commentary and role play each
fish with suitable goals and behaviors concordant with the fish's goals.

## AI generates the tableau
The AI doesn't really issue commands to a fish tank game, but generates a fish tank with fish who each are playing
out a role. This way, the bot doesn't have to deal with tool calling or attempting to make invalid moves, etc.


## Roadmap, Issues

- Probably should have been entirely a website to start with. Terminal is a bit cramped for space.
- This is two designs mashed into one. That was a bad idea.
- Still don't have a good way to show what the fish is doing thinking in a nice way. Current solution scrolls too fast. 
- Fish actions are too limited, AI text dialog comes across as unnecessary flavor text. Needs some story