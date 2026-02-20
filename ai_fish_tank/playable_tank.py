"""Fish tank game with optional AI player."""

from openai import OpenAI
from ai_fish_tank.env_loader import load_env
from ai_fish_tank.fish_bot import FishBot
from ai_fish_tank.memory import FishMemory, MemoryEvent
from ai_fish_tank.relationships import Relationship
from ai_fish_tank.game_logger import get_logger
from ai_fish_tank.session import SessionManager, FishInfo

import logging
import json
from dataclasses import dataclass, field
from pathlib import Path

# Setting up logging
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Fish:
    """Represents a fish in the fish tank."""

    name: str
    emoji: str
    position: tuple[int, int]
    tank: "FishTank"
    likes_to_eat: list[str] = field(default_factory=list)
    field_of_view: list[list[str | None]] = field(default_factory=list)
    monologue: str = ""
    memory: FishMemory = field(default_factory=FishMemory)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    traits: list[str] = field(default_factory=lambda: ["curious"])

    def update_field_of_view(self) -> None:
        """Updates the fish's field of view based on its current position in the tank."""
        LOGGER.info(f"Updating field of view for fish {self.name} at position {self.position}")
        self.field_of_view = self.tank.get_mini_map(self.position)

    def get_current_round(self) -> int:
        """Get the current round from the tank."""
        return getattr(self.tank, "current_round", 0)

    def move(self, direction: str) -> None:
        """Attempts to move the fish in the specified direction."""
        logger = get_logger()
        LOGGER.info(f"Fish {self.name} attempting to move {direction} from position {self.position}")
        old_position = self.position
        new_position = self.calculate_new_position(direction)
        if self.tank.is_move_possible(new_position):
            LOGGER.info(f"Move successful. {self.name} moved to {new_position}")
            self.position = new_position
            self.update_field_of_view()
            event = MemoryEvent(
                round=self.get_current_round(),
                event_type="move",
                actor=self.name,
                location=old_position,
                description=f"{self.name} moved {direction} to {new_position}.",
                emotional_weight=0.0,
            )
            self.memory.add_event(event)
            self.tank.broadcast_event(event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="move",
                success=True,
                details={
                    "direction": direction,
                    "from_position": list(old_position),
                    "to_position": list(new_position),
                },
            )
        else:
            LOGGER.info(f"Move blocked. {self.name} remains at {self.position}")
            event = MemoryEvent(
                round=self.get_current_round(),
                event_type="move_blocked",
                actor=self.name,
                location=self.position,
                description=f"{self.name} tried to move {direction} but was blocked.",
                emotional_weight=-0.1,
            )
            self.memory.add_event(event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="move",
                success=False,
                details={
                    "direction": direction,
                    "from_position": list(old_position),
                    "blocked_at": list(new_position),
                },
            )

    def calculate_new_position(self, direction: str) -> tuple[int, int]:
        """Calculates the new position based on the current position and the given direction."""
        x, y = self.position
        if direction == "north":
            return x, y - 1
        if direction == "south":
            return x, y + 1
        if direction == "east":
            return x + 1, y
        if direction == "west":
            return x - 1, y

        LOGGER.warning(f"Invalid direction '{direction}' provided.")
        return self.position  # Return the same position if the direction is invalid

    def eat(self, direction: str) -> None:
        """Attempts to eat something in the specified direction."""
        logger = get_logger()
        LOGGER.info(f"{self.name} is attempting to eat in the {direction} direction.")
        target_position = self.calculate_new_position(direction)
        target = self.tank.get_object_at_position(target_position)

        if target and target in self.likes_to_eat:
            LOGGER.info(f"{self.name} ate {target} at position {target_position}.")
            self.tank.remove_object_at_position(target_position)
            event = MemoryEvent(
                round=self.get_current_round(),
                event_type="ate",
                actor=self.name,
                location=target_position,
                description=f"{self.name} ate {target} at {target_position}.",
                emotional_weight=0.5,
            )
            self.memory.add_event(event)
            self.tank.broadcast_event(event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="eat",
                success=True,
                details={
                    "direction": direction,
                    "target": target,
                    "position": list(target_position),
                },
            )
        else:
            LOGGER.info(f"Nothing edible found at position {target_position} or {self.name} doesn't like to eat {target}.")
            event = MemoryEvent(
                round=self.get_current_round(),
                event_type="eat_failed",
                actor=self.name,
                location=target_position,
                description=f"{self.name} tried to eat in {direction} but found nothing edible.",
                emotional_weight=-0.1,
            )
            self.memory.add_event(event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="eat",
                success=False,
                details={
                    "direction": direction,
                    "target": target,
                    "position": list(target_position),
                },
            )

    def attack(self, direction: str) -> None:
        """Attempts to attack another fish in the specified direction."""
        logger = get_logger()
        LOGGER.info(f"{self.name} is attempting to attack in the {direction} direction.")
        target_position = self.calculate_new_position(direction)
        target_fish = self.tank.get_fish_at_position(target_position)

        if target_fish:
            LOGGER.info(f"{self.name} attacked {target_fish.name} at position {target_position}!")
            attacker_event = MemoryEvent(
                round=self.get_current_round(),
                event_type="attack",
                actor=self.name,
                target=target_fish.name,
                location=target_position,
                description=f"{self.name} attacked {target_fish.name}.",
                emotional_weight=0.2,
            )
            self.memory.add_event(attacker_event)
            if target_fish.name not in self.relationships:
                self.relationships[target_fish.name] = Relationship(other_fish_name=target_fish.name)
            self.relationships[target_fish.name].update_from_event(attacker_event)
            victim_event = MemoryEvent(
                round=self.get_current_round(),
                event_type="attacked",
                actor=self.name,
                target=target_fish.name,
                location=target_position,
                description=f"{target_fish.name} was attacked by {self.name}.",
                emotional_weight=-0.8,
            )
            target_fish.memory.add_event(victim_event)
            if self.name not in target_fish.relationships:
                target_fish.relationships[self.name] = Relationship(other_fish_name=self.name)
            target_fish.relationships[self.name].update_from_event(victim_event)
            self.tank.remove_fish_at_position(target_position)
            self.tank.broadcast_event(attacker_event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="attack",
                success=True,
                details={
                    "direction": direction,
                    "target_fish": target_fish.name,
                    "position": list(target_position),
                },
            )
        else:
            LOGGER.info(f"No fish found to attack at position {target_position}.")
            event = MemoryEvent(
                round=self.get_current_round(),
                event_type="attack_failed",
                actor=self.name,
                location=target_position,
                description=f"{self.name} tried to attack in {direction} but found no target.",
                emotional_weight=-0.1,
            )
            self.memory.add_event(event)
            logger.log_fish_action(
                fish_name=self.name,
                round_num=self.get_current_round(),
                action="attack",
                success=False,
                details={
                    "direction": direction,
                    "position": list(target_position),
                },
            )

    def speak(self, text: str) -> None:
        """Store a line of monologue for later rendering."""
        logger = get_logger()
        LOGGER.info(f"{self.name} says: {text}")
        self.monologue = text
        event = MemoryEvent(
            round=self.get_current_round(),
            event_type="speak",
            actor=self.name,
            description=f"{self.name} said: {text}",
            emotional_weight=0.1,
        )
        self.memory.add_event(event)
        logger.log_fish_action(
            fish_name=self.name,
            round_num=self.get_current_round(),
            action="speak",
            success=True,
            details={"text": text},
        )


@dataclass
class InanimateObject:
    """Represents an inanimate object in the fish tank."""

    emoji: str
    position: tuple[int, int]


@dataclass
class FishTank:
    """Represents the fish tank containing fish and inanimate objects."""

    width: int
    height: int
    fishes: list[Fish] = field(default_factory=list)
    objects: list[InanimateObject] = field(default_factory=list)
    top_border: str = "🌊"
    bottom_border: str = "🪨"
    side_border: str = "🪟"
    current_round: int = 0
    view_range: int = 2

    def add_fish(self, fish: Fish) -> None:
        """Adds a fish to the tank."""
        LOGGER.info(f"Adding fish {fish.name} at position {fish.position}")
        self.fishes.append(fish)

    def add_object(self, obj: InanimateObject) -> None:
        """Adds an inanimate object to the tank."""
        LOGGER.info(f"Adding object {obj.emoji} at position {obj.position}")
        self.objects.append(obj)

    def is_move_possible(self, position: tuple[int, int]) -> bool:
        """Checks if a move is possible (within bounds and no collision with objects)."""
        x, y = position
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        for obj in self.objects:
            if obj.position == position:
                return False

        for fish in self.fishes:
            if fish.position == position:
                return False

        return True

    def get_object_at_position(self, position: tuple[int, int]) -> str | None:
        """Returns the emoji of the object at the given position, or None if there's no object."""
        for obj in self.objects:
            if obj.position == position:
                return obj.emoji
        return None

    def get_fish_at_position(self, position: tuple[int, int]) -> Fish | None:
        """Returns the fish at the given position, or None if there's no fish."""
        for fish in self.fishes:
            if fish.position == position:
                return fish
        return None

    def remove_object_at_position(self, position: tuple[int, int]) -> None:
        """Removes an object at the specified position."""
        self.objects = [obj for obj in self.objects if obj.position != position]
        LOGGER.info(f"Object at position {position} has been removed from the tank.")

    def remove_fish_at_position(self, position: tuple[int, int]) -> None:
        """Removes a fish at the specified position."""
        self.fishes = [fish for fish in self.fishes if fish.position != position]
        LOGGER.info(f"Fish at position {position} has been removed from the tank.")

    def is_in_view(self, observer_pos: tuple[int, int], event_pos: tuple[int, int] | None) -> bool:
        """Check if an event position is within view range of an observer."""
        if event_pos is None:
            return False
        distance = abs(observer_pos[0] - event_pos[0]) + abs(observer_pos[1] - event_pos[1])
        return distance <= self.view_range

    def broadcast_event(self, event: MemoryEvent) -> None:
        """Broadcast an event to all fish who can observe it."""
        for fish in self.fishes:
            if fish.name == event.actor:
                continue
            if event.location and self.is_in_view(fish.position, event.location):
                fish.memory.add_event(event)
                if event.target and event.event_type == "attack":
                    observer_event = MemoryEvent(
                        round=event.round,
                        event_type="observed_attack",
                        actor=event.actor,
                        target=event.target,
                        location=event.location,
                        description=f"{fish.name} saw {event.actor} attack {event.target}.",
                        emotional_weight=-0.3,
                    )
                    if event.actor not in fish.relationships:
                        fish.relationships[event.actor] = Relationship(other_fish_name=event.actor)
                    fish.relationships[event.actor].update_from_event(observer_event)

    def get_mini_map(self, position: tuple[int, int], view_range: int = 2) -> list[list[str | None]]:
        """Generates a mini-map of the surrounding area based on the fish's position."""
        x, y = position
        mini_map = []
        for dy in range(-view_range, view_range + 1):
            row: list[str | None] = []
            for dx in range(-view_range, view_range + 1):
                px, py = x + dx, y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    found_object = None
                    # Check for fish first
                    for fish in self.fishes:
                        if fish.position == (px, py):
                            found_object = fish.emoji
                            break
                    # Check for objects
                    if not found_object:
                        for obj in self.objects:
                            if obj.position == (px, py):
                                found_object = obj.emoji
                                break
                    row.append(found_object if found_object else " ")
                else:
                    row.append(None)  # Out of bounds
            mini_map.append(row)
        LOGGER.info(f"Mini-map for fish at position {position} generated.")
        return mini_map

    def render_tank_str(self) -> str:
        """Return the tank as a string instead of printing."""
        lines = [self.top_border * (self.width + 2)]
        for y in range(self.height):
            row = [self.side_border]
            for x in range(self.width):
                emoji = "⬛"
                for fish in self.fishes:
                    if fish.position == (x, y):
                        emoji = fish.emoji
                        break
                if emoji == "⬛":
                    for obj in self.objects:
                        if obj.position == (x, y):
                            emoji = obj.emoji
                            break
                row.append(emoji)
            row.append(self.side_border)
            lines.append("".join(row))
        lines.append(self.bottom_border * (self.width + 2))
        return "\n".join(lines)

    def render_tank_with_monologues(self) -> None:
        """Render the tank followed by the latest monologues for each fish."""
        print(self.render_tank_str())
        for fish in self.fishes:
            if fish.monologue:
                print(f"{fish.emoji} {fish.name}: {fish.monologue}")
                fish.monologue = ""  # Clear monologue after displaying


def ai_run(max_rounds: int = 5, client=None, save_dir: Path | None = None) -> FishTank:
    """Run the game loop controlled by an AI actor."""

    load_env()
    if client is None:
        client = OpenAI()

    logger = get_logger()
    session_manager = SessionManager()

    tank = FishTank(width=10, height=8)
    fish1 = Fish(
        name="Nemo",
        emoji="🐟",
        position=(5, 5),
        tank=tank,
        likes_to_eat=["🌿"],
        traits=["curious", "friendly", "brave"],
    )
    fish2 = Fish(
        name="Dory",
        emoji="🐠",
        position=(2, 2),
        tank=tank,
        traits=["forgetful", "optimistic", "friendly"],
    )
    tank.add_fish(fish1)
    tank.add_fish(fish2)

    rock = InanimateObject(emoji="🪨", position=(3, 3))
    seaweed = InanimateObject(emoji="🌿", position=(7, 7))
    tank.add_object(rock)
    tank.add_object(seaweed)

    fish_roster = [
        FishInfo(
            name=fish.name,
            emoji=fish.emoji,
            position=fish.position,
            traits=fish.traits,
            likes_to_eat=fish.likes_to_eat,
        )
        for fish in tank.fishes
    ]
    session_manager.create_session(
        session_id=logger.session_id,
        tank_width=tank.width,
        tank_height=tank.height,
        max_rounds=max_rounds,
        fish_roster=fish_roster,
    )

    logger.log_game_start(
        fish_roster=[fish_info.__dict__ for fish_info in fish_roster],
        tank_size=(tank.width, tank.height),
        config={"max_rounds": max_rounds},
    )

    tank.render_tank_with_monologues()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "move",
                "description": "Move one cell in a cardinal direction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["north", "south", "east", "west"]},
                    },
                    "required": ["direction"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "eat",
                "description": "Attempt to eat in a direction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["north", "south", "east", "west"]},
                    },
                    "required": ["direction"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "attack",
                "description": "Attempt to attack another fish in a direction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["north", "south", "east", "west"]},
                    },
                    "required": ["direction"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "speak",
                "description": "Provide a monologue for this fish.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The content of the fish's monologue."},
                    },
                    "required": ["text"],
                },
            },
        },
    ]

    from ai_fish_tank.persistence import save_all_fish

    bots = {fish.name: FishBot(fish=fish, client=client) for fish in tank.fishes}

    final_round = 0
    winner = None
    for round_num in range(max_rounds):
        tank.current_round = round_num + 1
        final_round = tank.current_round
        print(f"\n--- Round {tank.current_round} ---")
        state = tank.render_tank_str()

        logger.log_round_start(round_num=tank.current_round, tank_state=state)

        for bot in bots.values():
            if bot.fish not in tank.fishes:
                continue
            tool_calls = bot.decide_action(state, tools, round_num=tank.current_round)
            for call in tool_calls:
                args = json.loads(call.function.arguments)
                fish = bot.fish
                content = ""
                function_name = call.function.name
                if function_name == "move":
                    direction = args.get("direction")
                    new_pos = fish.calculate_new_position(direction)
                    if tank.is_move_possible(new_pos):
                        fish.move(direction)
                        content = f"{fish.name} moved {direction}."
                    else:
                        content = f"Move for {fish.name} to {direction} was invalid; please try again."
                elif function_name == "eat":
                    direction = args.get("direction")
                    fish.eat(direction)
                    content = f"{fish.name} attempted to eat."
                elif function_name == "attack":
                    direction = args.get("direction")
                    fish.attack(direction)
                    content = f"{fish.name} attempted to attack."
                elif function_name == "speak":
                    text = args.get("text")
                    fish.speak(text)
                    content = f"{fish.name} spoke."
                LOGGER.info(content)
                bot.record_tool_result(call, content)

        for fish in tank.fishes:
            fish.memory.forget_old_events(tank.current_round)

        fish_states = [
            {
                "name": fish.name,
                "emoji": fish.emoji,
                "position": list(fish.position),
                "monologue": fish.monologue,
            }
            for fish in tank.fishes
        ]
        logger.log_round_end(round_num=tank.current_round, fish_states=fish_states)

        if save_dir:
            save_all_fish(tank.fishes, save_dir)

        tank.render_tank_with_monologues()

        if len(tank.fishes) <= 1:
            print("\n--- Game Over ---")
            if tank.fishes:
                winner = tank.fishes[0].name
            break

    survivors = [fish.name for fish in tank.fishes]
    logger.log_game_end(final_round=final_round, winner=winner, survivors=survivors)
    session_manager.end_session(
        session_id=logger.session_id,
        final_round=final_round,
        winner=winner,
        survivors=survivors,
    )

    print("\n--- Final Tank State ---")
    tank.render_tank_with_monologues()
    return tank


if __name__ == "__main__":
    ai_run()
