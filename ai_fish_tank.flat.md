# Contents of ai_fish_tank source tree

## File: ai_plays_game.py

```python

```

## File: env_loader.py

```python
import dotenv


def load_env(dotenv_path: str | None = None):

    try:
        dotenv.load_dotenv(dotenv_path)  ##

    except Exception as e:  ##

        print(f"Error loading .env file: {e}")
        print("Continuing without .env file.")

```

## File: playable_tank.py

```python
import logging
from dataclasses import dataclass, field


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Fish:

    name: str
    emoji: str
    position: tuple[int, int]
    tank: "FishTank"
    likes_to_eat: list[str] = field(default_factory=list)
    field_of_view: list[list[str | None]] = field(default_factory=list)

    def update_field_of_view(self) -> None:
        LOGGER.info(
            f"Updating field of view for fish {self.name} at position {self.position}"
        )
        self.field_of_view = self.tank.get_mini_map(self.position)

    def move(self, direction: str) -> None:
        LOGGER.info(
            f"Fish {self.name} attempting to move {direction} from position {self.position}"
        )
        new_position = self.calculate_new_position(direction)
        if self.tank.is_move_possible(new_position):
            LOGGER.info(f"Move successful. {self.name} moved to {new_position}")
            self.position = new_position
            self.update_field_of_view()
        else:
            LOGGER.info(f"Move blocked. {self.name} remains at {self.position}")

    def calculate_new_position(self, direction: str) -> tuple[int, int]:
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
        return self.position  ##

    def eat(self, direction: str) -> None:
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
        LOGGER.info(
            f"{self.name} is attempting to attack in the {direction} direction."
        )
        target_position = self.calculate_new_position(direction)
        target_fish = self.tank.get_fish_at_position(target_position)

        if target_fish:
            LOGGER.info(
                f"{self.name} attacked {target_fish.name} at position {target_position}!"
            )

            self.tank.remove_fish_at_position(target_position)
        else:
            LOGGER.info(f"No fish found to attack at position {target_position}.")


@dataclass
class InanimateObject:

    emoji: str
    position: tuple[int, int]


@dataclass
class FishTank:

    width: int
    height: int
    fishes: list[Fish] = field(default_factory=list)
    objects: list[InanimateObject] = field(default_factory=list)
    top_border: str = "🌊"
    bottom_border: str = "🪨"
    side_border: str = "🪟"

    def add_fish(self, fish: Fish) -> None:
        LOGGER.info(f"Adding fish {fish.name} at position {fish.position}")
        self.fishes.append(fish)

    def add_object(self, obj: InanimateObject) -> None:
        LOGGER.info(f"Adding object {obj.emoji} at position {obj.position}")
        self.objects.append(obj)

    def is_move_possible(self, position: tuple[int, int]) -> bool:
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
        for obj in self.objects:
            if obj.position == position:
                return obj.emoji
        return None

    def get_fish_at_position(self, position: tuple[int, int]) -> Fish | None:
        for fish in self.fishes:
            if fish.position == position:
                return fish
        return None

    def remove_object_at_position(self, position: tuple[int, int]) -> None:
        self.objects = [obj for obj in self.objects if obj.position != position]
        LOGGER.info(f"Object at position {position} has been removed from the tank.")

    def remove_fish_at_position(self, position: tuple[int, int]) -> None:
        self.fishes = [fish for fish in self.fishes if fish.position != position]
        LOGGER.info(f"Fish at position {position} has been removed from the tank.")

    def get_mini_map(
        self, position: tuple[int, int], view_range: int = 2
    ) -> list[list[str | None]]:
        x, y = position
        mini_map = []
        for dy in range(-view_range, view_range + 1):
            row: list[str | None] = []
            for dx in range(-view_range, view_range + 1):
                px, py = x + dx, y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    found_object = None

                    for fish in self.fishes:
                        if fish.position == (px, py):
                            found_object = fish.emoji
                            break

                    if not found_object:
                        for obj in self.objects:
                            if obj.position == (px, py):
                                found_object = obj.emoji
                                break
                    row.append(found_object if found_object else " ")
                else:
                    row.append(None)  ##

            mini_map.append(row)
        LOGGER.info(f"Mini-map for fish at position {position} generated.")
        return mini_map

    def render_tank(self) -> None:
        LOGGER.info("Rendering fish tank with borders.")

        print(self.top_border * (self.width + 2))

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
            print("".join(row))

        print(self.bottom_border * (self.width + 2))


def run():

    tank = FishTank(width=10, height=8)
    fish1 = Fish(
        name="Nemo", emoji="🐟", position=(5, 5), tank=tank, likes_to_eat=["🌿"]
    )
    fish2 = Fish(name="Dory", emoji="🐠", position=(2, 2), tank=tank)
    tank.add_fish(fish1)
    tank.add_fish(fish2)

    rock = InanimateObject(emoji="🪨", position=(3, 3))
    seaweed = InanimateObject(emoji="🌿", position=(7, 7))
    tank.add_object(rock)
    tank.add_object(seaweed)

    tank.render_tank()

    fish1.move("north")
    fish1.eat("south")
    fish1.move("west")
    fish1.attack("south")

    fish2.move("east")
    fish2.move("south")

    tank.render_tank()

    print(f"Fish {fish1.name} field of view:")
    for row in fish1.field_of_view:
        print(row)
    print(f"Fish {fish2.name} field of view:")
    for row in fish2.field_of_view:
        print(row)


if __name__ == "__main__":
    run()

```

## File: simulated_tank.py

```python
import logging
import os
import pickle  ##

import random
import textwrap
from pathlib import Path
from typing import Any

from openai import OpenAI

from ai_fish_tank.env_loader import load_env

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


load_env()
TANK_WIDTH = 5
TANK_HEIGHT = 5


class Fish:

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        species: str,
        traits: str,
        emoji: str,
        goal: str,
    ) -> None:
        self.name = name
        self.position = position
        self.species = species
        self.traits = traits
        self.emoji = emoji
        self.goal = goal

    def move(self, new_position: tuple[int, int]) -> None:
        self.position = new_position

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.species}, {self.traits}) at position {self.position}"
        )


class FishTank:

    def __init__(self, fish_list: list[Fish]) -> None:
        self.rounds = 0
        self.fish_list = fish_list
        self.plants_list: list[str] = []
        self.tank_size = (TANK_WIDTH, TANK_HEIGHT)  ##

        self.story_so_far = []

        self.initialize_with_plants(["🌿", "🌱"])
        self.current_layout: list[str] = []
        self.conversation: list[str] = []

    def initialize_with_plants(self, plants: list[str]) -> None:

        for plant in plants:
            x, y = random.randint(0, self.tank_size[0] - 1), random.randint(
                0, self.tank_size[1] - 1
            )  ##

            self.plants_list.append((plant, (x, y)))

    def personae_dramatis_markdown(self):
        return "\n".join(
            [
                f"- {fish.emoji} {fish.name} ({fish.species}, {fish.traits})"
                for fish in self.fish_list
            ]
        )

    def draw(self) -> str:
        tank = [
            ["⬜" for _ in range(self.tank_size[1])] for _ in range(self.tank_size[0])
        ]

        for plant, (x, y) in self.plants_list:
            tank[x][y] = plant

        for fish in self.fish_list:
            x, y = fish.position
            tank[x][y] = fish.emoji

        LOGGER.info(self.list_differences(tank))
        self.current_layout = tank
        return "\n".join(["".join(row) for row in tank])

    def list_differences(
        self, new_layout: list[list[str]]
    ) -> dict[Any, tuple[Any, str]]:
        differences = {}
        for i in range(len(self.current_layout)):
            for j in range(len(self.current_layout[i])):
                if self.current_layout[i][j] != new_layout[i][j]:
                    differences[self.current_layout[i][j] + new_layout[i][j]] = (
                        self.current_layout[i][j],
                        new_layout[i][j],
                    )
        return differences

    def pretty_print_and_wrap(self, story: str) -> str:
        return "\n".join(textwrap.fill(line, width=80) for line in story.split("\n"))

    def update_tank(self, bot_answer: str) -> None:

        if (
            "---start tank---\n" not in bot_answer
            or "---end tank---\n" not in bot_answer
        ):
            LOGGER.error(
                "Invalid response from bot. Expected '---start tank---' and '---end tank---' markers."
            )
            return
        tank_data = (
            bot_answer.split("---start tank---\n")[1]
            .split("---end tank---\n")[0]
            .strip()
            .split("\n")
        )
        if (
            "---start story---\n" not in bot_answer
            or "---end story---\n" not in bot_answer
        ):
            LOGGER.error(
                "Invalid response from bot. Expected '---start story---' and '---end story---' markers."
            )
            return
        tank_story = (
            bot_answer.split("---start story---\n")[1]
            .split("---end story---\n")[0]
            .strip()
        )
        self.story_so_far.append(tank_story)

        rows = len(tank_data)
        cols = len(tank_data[0])
        LOGGER.warning("Rows: %s, Cols: %s", rows, cols)

        for i in range(rows):
            for _j in range(cols):
                tank_data[i] = tank_data[i].replace("⬜", " ")

        for i, row in enumerate(tank_data):
            for j, cell in enumerate(row):
                for fish in self.fish_list:
                    if cell == fish.emoji:
                        fish.move((i, j))

    def generate_story(self) -> str:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.rounds += 1
        if self.rounds == 1:
            prompt = (
                "Here is the personae dramatis:\n"
                + self.personae_dramatis_markdown()
                + "\n"
            )
        else:
            prompt = ""
        prompt = prompt + "Here is a fish tank:\n" + self.draw() + "\n"
        if self.rounds == 1:
            prompt += (
                "Respond with `---start tank---\n` the fishtank's new arrangement, then `---end tank---\n`"
                " and a story, using `---start story---\n` and `---end story---\n`."
            )

        prompt += " Describe what happens as each fish moves and interacts, keeping the story under 500 characters."

        LOGGER.debug("Sending prompt to OpenAI API: %s", prompt)

        if not self.conversation:
            self.conversation = [
                {
                    "role": "system",
                    "content": "You are a fish tank simulator. You will get a picture of the fish tank, "
                    "generate the next fish tank, and then say a bit about what happened.",
                },
                {"role": "user", "content": prompt},
            ]
        else:
            self.conversation.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=self.conversation, max_tokens=5000
        )

        story = response.choices[0].message.content

        self.conversation.append({"role": "system", "content": story})

        LOGGER.debug("Received story: %s", story)
        return story or ""

    def save_state(self, save_path) -> None:
        LOGGER.debug("Saving fish tank state to %s", save_path)
        with open(save_path, "wb") as file:
            pickle.dump(self, file)

    @classmethod
    def load_state(cls, save_path: Path) -> "FishTank | None":
        if save_path.exists():
            LOGGER.debug("Loading fish tank state from %s", save_path)
            with open(save_path, "rb") as file:
                return pickle.load(file)  ##

        LOGGER.warning("No save file found at %s", save_path)
        return None


class FishTankSimulator:

    def __init__(self, fish_tank: FishTank, save_path: Path) -> None:
        self.fish_tank = fish_tank
        self.save_path = save_path

    def run_simulation(self) -> None:
        print(self.fish_tank.personae_dramatis_markdown())
        while True:
            print("\nCurrent Fish Tank:")
            print(self.fish_tank.draw())
            story = self.fish_tank.generate_story()
            print("\nStory:")

            print(self.fish_tank.pretty_print_and_wrap(story))

            self.fish_tank.update_tank(story)
            self.fish_tank.save_state(self.save_path)

            user_input = input("\nContinue simulation? (y/n): ").strip().lower()
            if user_input != "y":
                break


def run_with_ai():
    fish_list = [
        Fish("Goldie", (0, 0), "Goldfish", "curious", "🐠", "Exploring the tank"),
        Fish("Bubbles", (1, 1), "Betta", "timid", "🐟", "Finding a quiet spot"),
        Fish("Finley", (2, 2), "Angelfish", "bold", "🐡", "Patrolling territory"),
        Fish("Stripe", (3, 3), "Zebra Fish", "aggressive", "🐙", "Challenging rivals"),
        Fish("Glimmer", (4, 4), "Guppy", "peaceful", "🦐", "Socializing with others"),
    ]

    for fish in fish_list:
        possible = (
            random.randint(0, TANK_WIDTH - 1),
            random.randint(0, TANK_HEIGHT - 1),
        )  ##

        if possible not in [fish.position for fish in fish_list]:
            fish.move(possible)

    emojis = [fish.emoji for fish in fish_list]
    if not len(emojis) == len(set(emojis)):
        raise TypeError("Fish must have distinct emojis")

    save_path = Path("fish_tank_state.pkl")
    if save_path.exists():
        fish_tank = FishTank.load_state(save_path)
    else:
        fish_tank = FishTank(fish_list=fish_list)

    simulator = FishTankSimulator(
        fish_tank=fish_tank, save_path=Path("fish_tank_state.pkl")
    )
    simulator.run_simulation()


if __name__ == "__main__":
    run_with_ai()

```

## File: __init__.py

```python

```

## File: __main__.py

```python
from ai_fish_tank.playable_tank import run

if __name__ == "__main__":
    run()

```

