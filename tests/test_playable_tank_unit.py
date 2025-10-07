
from ai_fish_tank.playable_tank import Fish, FishTank, InanimateObject


def test_calculate_new_position():
    tank = FishTank(width=3, height=3)
    fish = Fish(name="Nemo", emoji="🐟", position=(1, 1), tank=tank)
    assert fish.calculate_new_position("north") == (1, 0)
    assert fish.calculate_new_position("south") == (1, 2)
    assert fish.calculate_new_position("east") == (2, 1)
    assert fish.calculate_new_position("west") == (0, 1)
    # Invalid direction returns current position
    assert fish.calculate_new_position("up") == (1, 1)


def test_move_blocked_by_object():
    tank = FishTank(width=3, height=3)
    fish = Fish(name="Nemo", emoji="🐟", position=(1, 1), tank=tank)
    tank.add_fish(fish)
    rock = InanimateObject(emoji="🪨", position=(1, 0))
    tank.add_object(rock)
    fish.move("north")
    assert fish.position == (1, 1)


def test_get_mini_map_edge():
    tank = FishTank(width=3, height=3)
    fish = Fish(name="Nemo", emoji="🐟", position=(0, 0), tank=tank)
    tank.add_fish(fish)
    rock = InanimateObject(emoji="🪨", position=(1, 1))
    tank.add_object(rock)
    mini_map = tank.get_mini_map((0, 0), view_range=1)
    assert mini_map == [
        [None, None, None],
        [None, "🐟", " "],
        [None, " ", "🪨"],
    ]

