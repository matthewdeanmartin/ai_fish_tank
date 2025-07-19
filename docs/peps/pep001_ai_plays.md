PEP: 1
Title: AI Plays the Fish Tank
Author: OpenAI Codex <https://openai.com/>
Status: Draft
Type: Standards Track
Content-Type: text/markdown
Created: 2025-07-19
Post-History: 2025-07-19

# Abstract

This proposal describes how language models will control the fish in the
terminal fish tank game. The LLM will narrate the story of the tank and
provide each fish with a coherent reason for movement and internal
thoughts.

# Motivation

The current terminal fish tank offers a static experience. Adding an AI
narrator and decision maker will turn the tank into an evolving tableau.
Each fish will move according to its traits and goals. The story will be
rendered after each update so the player can follow the drama.

# Specification

* The simulator maintains a conversation history with the LLM so the fish
  can recall prior events.
* On each turn the game sends the current tank layout and a reminder of
  each fish's personality traits.
* The LLM replies with an updated tank layout wrapped in
  `---start tank---` and `---end tank---` markers.
* A short narrative for the player is returned between
  `---start story---` and `---end story---` markers.
* Each fish also receives a one line "thought" explaining why it moved.
* The program validates that the tank layout is legal before applying it.
* Actions must remain consistent with each fish's stated goals.

# Reference Implementation

`ai_fish_tank.simulated_tank` calls the OpenAI API to generate the next
state. The PEP does not mandate a particular model but assumes a
GPT‑compatible interface. Each response includes the next grid state,
a narration for the user and a short justification for every fish.

# Rationale

A shared story with distinct characters gives players a reason to watch
fish swim around the screen. The use of an LLM avoids hard coding
behavior while keeping the interface simple.

# Backwards Compatibility

This feature is additive. Existing code will continue to run when the AI
features are disabled.

# Security Considerations

The PEP assumes the LLM is sandboxed and cannot issue arbitrary code. The
host application should validate all output to avoid escape sequences or
malicious instructions being displayed to the user.

# Reference

This document follows the style of Python Enhancement Proposals.
