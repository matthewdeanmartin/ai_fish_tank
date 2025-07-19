PEP: 2
Title: AI Actor for playable_tank.py
Author: OpenAI Codex <https://openai.com/>
Status: Draft
Type: Standards Track
Created: 2025-07-19

# Abstract

Introduce an AI agent that plays the ``playable_tank`` fish-tank game by controlling
``Fish.move()``, ``.eat()``, and ``.attack()`` via OpenAI function calling.

# Rationale

Using OpenAI's tool feature keeps the game loop in Python while delegating
move selection to the model.

# Specification

* Define ``move``, ``eat`` and ``attack`` as tools in a chat completion call.
* Provide the tank state and mini maps to the model in each turn.
* Execute each returned tool call if legal, otherwise respond with a
  polite error message so the model can retry.
* Continue looping until no more tool calls or game over conditions are met.

# Backwards Compatibility

The classic ``run()`` entry point remains. A new ``ai_run()`` function
invokes the AI loop.

