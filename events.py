import random


HORROR_EVENTS = [
    ("atmosphere", "💡 Լույսերը հանկարծ անջատվեցին։"),
    ("atmosphere", "👂 Դու ինչ-որ մեկի քայլերի ձայն լսեցիր..."),
    ("danger", "🚨 Զոմբիների ակտիվությունը կտրուկ աճեց։"),
    ("atmosphere", "📻 Ռադիոն միացավ։ Ինչ-որ մեկը օգնություն է խնդրում։"),
    ("atmosphere", "🚪 Հեռվում դուռ փակվեց։"),
    ("danger", "🌫️ Մառախուղը խտացավ քաղաքի փողոցներում։"),
]


def choose_event(game):
    # Events start after players have had time to explore.
    if game.tick < 4:
        return None

    chance = min(0.45, 0.16 + game.tick / 250)
    if random.random() > chance:
        return None

    return random.choice(HORROR_EVENTS)
