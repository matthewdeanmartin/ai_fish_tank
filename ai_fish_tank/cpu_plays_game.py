from ai_fish_tank.playable_tank import FishTank, Fish, InanimateObject


def run():
    # Example setup and usage of the classes.
    # This could have prompted a human or a user for each game action/motion.
    tank = FishTank(width=10, height=8)
    fish1 = Fish(name="Nemo", emoji="🐟", position=(5, 5), tank=tank, likes_to_eat=["🌿"])
    fish2 = Fish(name="Dory", emoji="🐠", position=(2, 2), tank=tank)
    tank.add_fish(fish1)
    tank.add_fish(fish2)

    rock = InanimateObject(emoji="🪨", position=(3, 3))
    seaweed = InanimateObject(emoji="🌿", position=(7, 7))
    tank.add_object(rock)
    tank.add_object(seaweed)

    tank.render_tank_with_monologues()

    tank.render_tank_with_monologues()

    tank.render_tank_str()

    fish1.move("north")
    fish1.eat("south")
    fish1.move("west")
    fish1.attack("south")

    fish2.move("east")
    fish2.move("south")

    tank.render_tank_str()

    # For debugging purposes to see the field of view
    print(f"Fish {fish1.name} field of view:")
    for row in fish1.field_of_view:
        print(row)
    print(f"Fish {fish2.name} field of view:")
    for row in fish2.field_of_view:
        print(row)

if __name__ == '__main__':
    run()