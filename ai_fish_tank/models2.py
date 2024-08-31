from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import logging

# Setting up logging
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Fish:
    """Represents a fish in the fish tank."""
    name: str
    emoji: str
    position: Tuple[int, int]
    tank: 'FishTank'
    likes_to_eat: List[str] = field(default_factory=list)
    field_of_view: List[List[Optional[str]]] = field(default_factory=list)

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

    def calculate_new_position(self, direction: str) -> Tuple[int, int]:
        """Calculates the new position based on the current position and the given direction."""
        x, y = self.position
        if direction == "north":
            return x, y - 1
        elif direction == "south":
            return x, y + 1
        elif direction == "east":
            return x + 1, y
        elif direction == "west":
            return x - 1, y
        else:
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
                f"Nothing edible found at position {target_position} or {self.name} doesn't like to eat {target}.")

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


@dataclass
class InanimateObject:
    """Represents an inanimate object in the fish tank."""
    emoji: str
    position: Tuple[int, int]


@dataclass
class FishTank:
    """Represents the fish tank containing fish and inanimate objects."""
    width: int
    height: int
    fishes: List[Fish] = field(default_factory=list)
    objects: List[InanimateObject] = field(default_factory=list)
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

    def is_move_possible(self, position: Tuple[int, int]) -> bool:
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

    def get_object_at_position(self, position: Tuple[int, int]) -> Optional[str]:
        """Returns the emoji of the object at the given position, or None if there's no object."""
        for obj in self.objects:
            if obj.position == position:
                return obj.emoji
        return None

    def get_fish_at_position(self, position: Tuple[int, int]) -> Optional[Fish]:
        """Returns the fish at the given position, or None if there's no fish."""
        for fish in self.fishes:
            if fish.position == position:
                return fish
        return None

    def remove_object_at_position(self, position: Tuple[int, int]) -> None:
        """Removes an object at the specified position."""
        self.objects = [obj for obj in self.objects if obj.position != position]
        LOGGER.info(f"Object at position {position} has been removed from the tank.")

    def remove_fish_at_position(self, position: Tuple[int, int]) -> None:
        """Removes a fish at the specified position."""
        self.fishes = [fish for fish in self.fishes if fish.position != position]
        LOGGER.info(f"Fish at position {position} has been removed from the tank.")

    def get_mini_map(self, position: Tuple[int, int], view_range: int = 2) -> List[List[Optional[str]]]:
        """Generates a mini-map of the surrounding area based on the fish's position."""
        x, y = position
        mini_map = []
        for dy in range(-view_range, view_range + 1):
            row = []
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

    def render_tank(self) -> None:
        """Renders the entire fish tank with borders and objects."""
        LOGGER.info("Rendering fish tank with borders.")

        # Render the top border
        print(self.top_border * (self.width + 2))

        for y in range(self.height):
            row = [self.side_border]
            for x in range(self.width):
                # Check if there's a fish at the current position
                emoji = "⬛"
                for fish in self.fishes:
                    if fish.position == (x, y):
                        emoji = fish.emoji
                        break
                # Check if there's an object at the current position
                if emoji == "⬛":
                    for obj in self.objects:
                        if obj.position == (x, y):
                            emoji = obj.emoji
                            break
                row.append(emoji)
            row.append(self.side_border)
            print("".join(row))

        # Render the bottom border
        print(self.bottom_border * (self.width + 2))


if __name__ == "__main__":
    # Example setup and usage of the classes.
    tank = FishTank(width=10, height=8)
    fish1 = Fish(name="Nemo", emoji="🐟", position=(5, 5), tank=tank, likes_to_eat=["🌿"])
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

    # For debugging purposes to see the field of view
    print(f"Fish {fish1.name} field of view:")
    for row in fish1.field_of_view:
        print(row)
    print(f"Fish {fish2.name} field of view:")
    for row in fish2.field_of_view:
        print(row)