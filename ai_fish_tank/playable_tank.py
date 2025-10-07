"""Fish tank game with optional AI player."""

from openai import OpenAI
from ai_fish_tank.env_loader import load_env
from ai_fish_tank.fish_bot import FishBot

import logging
import json
from dataclasses import dataclass, field

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

    def update_field_of_view(self) -> None:
        """Updates the fish's field of view based on its current position in the tank."""
        LOGGER.info(f"Updating field of view for fish {self.name} at position {self.position}")
        self.field_of_view = self.tank.get_mini_map(self.position)

    def move(self, direction: str) -> None:
        """Attempts to move the fish in the specified direction."""
        LOGGER.info(f"Fish {self.name} attempting to move {direction} from position {self.position}")
        new_position = self.calculate_new_position(direction)
        if self.tank.is_move_possible(new_position):
            LOGGER.info(f"Move successful. {self.name} moved to {new_position}")
            self.position = new_position
            self.update_field_of_view()
        else:
            LOGGER.info(f"Move blocked. {self.name} remains at {self.position}")

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
        LOGGER.info(f"{self.name} is attempting to eat in the {direction} direction.")
        target_position = self.calculate_new_position(direction)
        target = self.tank.get_object_at_position(target_position)

        if target and target in self.likes_to_eat:
            LOGGER.info(f"{self.name} ate {target} at position {target_position}.")
            self.tank.remove_object_at_position(target_position)
        else:
            LOGGER.info(
                f"Nothing edible found at position {target_position} or {self.name} doesn't like to eat {target}."
            )

    def attack(self, direction: str) -> None:
        """Attempts to attack another fish in the specified direction."""
        LOGGER.info(f"{self.name} is attempting to attack in the {direction} direction.")
        target_position = self.calculate_new_position(direction)
        target_fish = self.tank.get_fish_at_position(target_position)

        if target_fish:
            LOGGER.info(f"{self.name} attacked {target_fish.name} at position {target_position}!")
            # Implement attack logic (e.g., reduce health or remove the fish)
            # For now, we can assume the fish is removed from the tank after attack
            self.tank.remove_fish_at_position(target_position)
        else:
            LOGGER.info(f"No fish found to attack at position {target_position}.")

    def speak(self, text: str) -> None:
        """Store a line of monologue for later rendering."""
        LOGGER.info(f"{self.name} says: {text}")
        self.monologue = text


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
                fish.monologue = "" # Clear monologue after displaying


def ai_run(max_rounds: int = 5, client=None) -> FishTank:
    """Run the game loop controlled by an AI actor."""
    load_env()
    if client is None:
        client = OpenAI()

    tank = FishTank(width=10, height=8)
    fish1 = Fish(name="Nemo", emoji="🐟", position=(5, 5), tank=tank, likes_to_eat=["🌿"])
    fish2 = Fish(name="Dory", emoji="�", position=(2, 2), tank=tank)
    tank.add_fish(fish1)
    tank.add_fish(fish2)

    rock = InanimateObject(emoji="🪨", position=(3, 3))
    seaweed = InanimateObject(emoji="🌿", position=(7, 7))
    tank.add_object(rock)
    tank.add_object(seaweed)

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

    bots = {fish.name: FishBot(fish=fish, client=client) for fish in tank.fishes}

    for i in range(max_rounds):
        print(f"\n--- Round {i+1} ---")
        state = tank.render_tank_str()
        for bot in bots.values():
            tool_calls = bot.decide_action(state, tools)
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

        tank.render_tank_with_monologues()

        if len(tank.fishes) <= 1:
            print("\n--- Game Over ---")
            break

    print("\n--- Final Tank State ---")
    tank.render_tank_with_monologues()
    return tank


if __name__ == "__main__":
    ai_run()
