import random


def shoot_zombie(player, zombie):
    if not zombie.alive:
        return False, "🧟 Այդ զոմբին արդեն մեռած է։"
    if player.bullets <= 0:
        return False, "🔫 Փամփուշտ չունես։"

    player.bullets -= 1

    # Most NPC zombies die from one successful shot in this ruleset.
    if random.random() < 0.88:
        zombie.hp = 0
        zombie.alive = False
        zombie.state = "DEAD"
        return True, "🔫 Կրակոցը դիպավ։ Զոմբին ոչնչացվեց։"

    zombie.hp -= 1
    zombie.state = "ALERT"
    return True, "🔫 Դիպար, բայց զոմբին դեռ շարժվում է։"


def infected_bite(infected, target):
    if not infected.infected or not target.alive or target.infected:
        return False

    if infected.location != target.location:
        return False

    if target.hidden and random.random() < 0.70:
        return False

    target.infected = True
    target.hidden = False
    target.bites += 1
    target.health = max(20, target.health - 10)
    return True
