import random


STATES = {"IDLE", "SEARCHING", "ALERT", "CHASING", "ATTACKING", "DEAD"}


def spawn_zombies(game, count):
    locations = list(game.location_names)
    for zid in range(count):
        game.zombies[zid] = __import__("models").Zombie(
            zid=zid,
            location=random.choice(locations),
        )


def step_zombies(game):
    humans = game.alive_humans()

    for zombie in game.zombies.values():
        if not zombie.alive:
            continue

        if zombie.cooldown > 0:
            zombie.cooldown -= 1

        visible = [
            p for p in humans
            if p.location == zombie.location and not p.hidden
        ]

        if visible:
            target = random.choice(visible)
            zombie.target_id = target.user_id
            zombie.state = "ATTACKING"

            if zombie.cooldown == 0:
                zombie.cooldown = 2
                # The bite itself is the infection trigger.
                if random.random() < 0.52:
                    target.infected = True
                    target.bites += 1
                    target.health = max(1, target.health - random.randint(8, 18))
            continue

        if humans and random.random() < 0.78:
            target = random.choice(humans)
            zombie.target_id = target.user_id
            zombie.state = "CHASING"

            exits = game.neighbors.get(zombie.location, [])
            if target.location in exits:
                zombie.location = target.location
            elif exits:
                zombie.location = random.choice(exits)
        else:
            zombie.state = random.choice(["IDLE", "SEARCHING", "ALERT"])
            exits = game.neighbors.get(zombie.location, [])
            if exits and random.random() < 0.55:
                zombie.location = random.choice(exits)
