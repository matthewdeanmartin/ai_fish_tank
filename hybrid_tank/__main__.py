""""
Fish tank. Bot controls entire board.
"""
import textwrap

import openai
import pickle
from pathlib import Path
from typing import List, Tuple, Dict
import logging
import random

import os

from openai import OpenAI

from ai_fish_tank.env_loader import load_env

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Ensure you have set your OpenAI API key
load_env()
TANK_WIDTH = 5
TANK_HEIGHT = 5


class Fish:
    """Represents a fish in the fish tank with attributes such as name, position, species, and personality traits."""

    def __init__(self, name: str, position: Tuple[int, int], species: str, traits: str, emoji: str, goal: str) -> None:
        """
        Initializes a Fish object.

        Args:
            name (str): Name of the fish.
            position (Tuple[int, int]): (x, y) Position of the fish in the tank (index-based).
            species (str): Species of the fish.
            traits (str): Personality traits of the fish.
            emoji (str): Emoji representing the fish.
            goal (str): The goal or purpose of the fish in life.
        """
        self.name = name
        self.position = position
        self.species = species
        self.traits = traits
        self.emoji = emoji
        self.goal = goal

    def move(self, new_position: Tuple[int, int]) -> None:
        """
        Updates the fish's position based on its personality and the bot's instructions.

        Args:
            new_position (Tuple[int, int]): The new (x, y) position for the fish.
        """
        self.position = new_position

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, {self.traits}) at position {self.position}"


class FishTank:
    """Represents the fish tank environment with fish and plants."""

    def __init__(self, fish_list: List[Fish]) -> None:
        """
        Initializes the FishTank object.

        Args:
            fish_list (List[Fish]): List of Fish objects in the tank.
        """
        self.rounds = 0
        self.fish_list = fish_list
        self.plants_list = []
        self.tank_size = (TANK_WIDTH, TANK_HEIGHT)  # 12x12 grid
        self.story_so_far = []
        # ocean themed emojis. non living, rocks and stuff
        self.initialize_with_plants(["🌿", "🌱"])
        self.current_layout = []
        self.conversation = []

    def initialize_with_plants(self, plants: List[str]) -> None:
        """
        Initializes the fish tank with plants.

        Args:
            plants (List[str]): List of plant emojis to add to the tank.
        """
        # select a random position for each plant bound by tank size
        for plant in plants:
            x, y = random.randint(0, self.tank_size[0] - 1), random.randint(0, self.tank_size[1] - 1)
            self.plants_list.append((plant, (x, y)))

    def personae_dramatis_markdown(self):
        """
        Returns a markdown summary of the fish in the tank.
        """
        return "\n".join([f"- {fish.emoji} {fish.name} ({fish.species}, {fish.traits})" for fish in self.fish_list])

    def draw(self) -> str:
        """Visual representation of the fish tank as a 12x12 grid."""
        tank = [["⬜" for _ in range(self.tank_size[1])] for _ in range(self.tank_size[0])]

        # fixed plants
        for plant, (x, y) in self.plants_list:
            tank[x][y] = plant

        # moving fish
        for fish in self.fish_list:
            x, y = fish.position
            tank[x][y] = fish.emoji

        LOGGER.info(self.list_differences(tank))
        self.current_layout = tank
        return "\n".join(["".join(row) for row in tank])

    def list_differences(self, new_layout: List[List[str]]) -> Dict[str, Tuple[int, int]]:
        """
        Returns the differences between the current layout and the new layout.

        Args:
            new_layout (List[List[str]]): The new layout of the fish tank.

        Returns:
            Dict[str, Tuple[int, int]]: A dictionary containing the differences between the two layouts.
        """
        differences = {}
        for i in range(len(self.current_layout)):
            for j in range(len(self.current_layout[i])):
                if self.current_layout[i][j] != new_layout[i][j]:
                    differences[self.current_layout[i][j] + new_layout[i][j]] = (
                    self.current_layout[i][j], new_layout[i][j])
        return differences

    def pretty_print_and_wrap(self, story: str) -> str:
        """
        Pretty prints and wraps the story to fit the terminal width.

        Args:
            story (str): The story to pretty print and wrap.

        Returns:
            str: The pretty printed and wrapped story.
        """
        return "\n".join(textwrap.fill(line, width=80) for line in story.split("\n"))

    def update_tank(self, bot_answer: str) -> None:
        """
        Updates the tank by moving each fish based on the bot's response.

        Args:
            bot_answer (str): The bot's response containing the new positions of the fish.
        """
        # Parsing the bot's response for new positions
        if "---start tank---\n" not in bot_answer or "---end tank---\n" not in bot_answer:
            LOGGER.error("Invalid response from bot. Expected '---start tank---' and '---end tank---' markers.")
            return
        tank_data = bot_answer.split("---start tank---\n")[1].split("---end tank---\n")[0].strip().split("\n")
        if "---start story---\n" not in bot_answer or "---end story---\n" not in bot_answer:
            LOGGER.error("Invalid response from bot. Expected '---start story---' and '---end story---' markers.")
            return
        tank_story = bot_answer.split("---start story---\n")[1].split("---end story---\n")[0].strip()
        self.story_so_far.append(tank_story)

        # validated tank size
        rows = len(tank_data)
        cols = len(tank_data[0])
        LOGGER.warning("Rows: %s, Cols: %s", rows, cols)

        # clear tank
        for i in range(rows):
            for j in range(cols):
                tank_data[i] = tank_data[i].replace("⬜", " ")

        for i, row in enumerate(tank_data):
            for j, cell in enumerate(row):
                for fish in self.fish_list:
                    if cell == fish.emoji:
                        fish.move((i, j))

    def generate_story(self) -> str:
        """
        Generates a story based on the current state of the fish tank using OpenAI API.

        Returns:
            str: The story generated by the OpenAI API.
        """
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.rounds += 1
        if self.rounds == 1:
            prompt = "Here is the personae dramatis:\n" + self.personae_dramatis_markdown() + "\n"
        else:
            prompt = ""
        prompt = (prompt + "Here is a fish tank:\n" + self.draw() + "\n")
        if self.rounds == 1:
            prompt += "Respond with `---start tank---\n` the fishtank's new arrangement, then `---end tank---\n`"
        " and a story, using `---start story---\n` and `---end story---\n`."

        prompt += " Describe what happens as each fish moves and interacts, keeping the story under 500 characters."

        LOGGER.debug("Sending prompt to OpenAI API: %s", prompt)

        if not self.conversation:
            self.conversation = [
                {"role": "system", "content": "You are a fish tank simulator. You will get a picture of the fish tank, "
                                              "generate the next fish tank, and then say a bit about what happened."},
                {"role": "user", "content": prompt},
            ]
        else:
            self.conversation.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.conversation,
            max_tokens=5000
        )

        # story = response['choices'][0]['message']['content'].strip()
        story = response.choices[0].message.content

        # update conversation
        self.conversation.append({"role": "system", "content": story})

        LOGGER.debug("Received story: %s", story)
        return story

    def save_state(self, save_path) -> None:
        """Saves the current state of the fish tank to a pickle file."""
        LOGGER.debug("Saving fish tank state to %s", save_path)
        with open(save_path, 'wb') as file:
            pickle.dump(self, file)

    @classmethod
    def load_state(cls, save_path:Path) -> "FishTank":
        """Loads the fish tank state from a pickle file."""
        if save_path.exists():
            LOGGER.debug("Loading fish tank state from %s", save_path)
            with open(save_path, 'rb') as file:
                return pickle.load(file)
        else:
            LOGGER.warning("No save file found at %s", save_path)


class FishTankSimulator:
    """Controls the simulation of the fish tank environment."""

    def __init__(self, fish_tank: FishTank, save_path: Path) -> None:
        """
        Initializes the FishTankSimulator object.

        Args:
            fish_tank (FishTank): The fish tank environment to simulate.
            save_path (Path): Path to save the simulation state.
        """
        self.fish_tank = fish_tank
        self.save_path = save_path


    def run_simulation(self) -> None:
        """Runs the fish tank simulation, updating the tank and generating stories."""
        print(self.fish_tank.personae_dramatis_markdown())
        while True:
            print("\nCurrent Fish Tank:")
            print(self.fish_tank.draw())
            story = self.fish_tank.generate_story()
            print("\nStory:")

            # format story so it word wraps nicely
            print(self.fish_tank.pretty_print_and_wrap(story))

            self.fish_tank.update_tank(story)
            self.fish_tank.save_state(self.save_path)

            user_input = input("\nContinue simulation? (y/n): ").strip().lower()
            if user_input != 'y':
                break


if __name__ == "__main__":
    # Update for new attributes

    fish_list = [
        Fish("Goldie", (0, 0), "Goldfish", "curious", "🐠", "Exploring the tank"),
        Fish("Bubbles", (1, 1), "Betta", "timid", "🐟", "Finding a quiet spot"),
        Fish("Finley", (2, 2), "Angelfish", "bold", "🐡", "Patrolling territory"),
        Fish("Stripe", (3, 3), "Zebra Fish", "aggressive", "🐙", "Challenging rivals"),
        Fish("Glimmer", (4, 4), "Guppy", "peaceful", "🦐", "Socializing with others")
    ]

    # Randomize positions of fish
    for fish in fish_list:
        possible = (random.randint(0, TANK_WIDTH - 1), random.randint(0, TANK_HEIGHT - 1))
        if possible not in [fish.position for fish in fish_list]:
            fish.move(possible)

    # Validate that the fish all have distinct emojis
    emojis = [fish.emoji for fish in fish_list]
    assert len(emojis) == len(set(emojis)), "Fish must have distinct emojis"

    save_path = Path("fish_tank_state.pkl")
    if save_path.exists():
        fish_tank = FishTank.load_state(save_path)
    else:
        fish_tank = FishTank(fish_list=fish_list)

    simulator = FishTankSimulator(fish_tank=fish_tank, save_path=Path("fish_tank_state.pkl"))
    simulator.run_simulation()
