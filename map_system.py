import random


LOCATIONS = {
    "safehouse": ("🏚️ Ապաստարան", ["hospital", "police", "school"]),
    "hospital": ("🏥 Հիվանդանոց", ["safehouse", "lab", "metro"]),
    "police": ("🚓 Ոստիկանություն", ["safehouse", "gas", "warehouse"]),
    "lab": ("🧪 Լաբորատորիա", ["hospital", "factory"]),
    "factory": ("🏭 Գործարան", ["lab", "warehouse", "metro"]),
    "school": ("🏫 Դպրոց", ["safehouse", "apartments"]),
    "metro": ("🚇 Մետրո", ["hospital", "factory", "store"]),
    "store": ("🏪 Խանութ", ["metro", "gas"]),
    "gas": ("⛽ Բենզալցակայան", ["police", "store"]),
    "apartments": ("🏢 Բարձրահարկ", ["school", "warehouse"]),
    "warehouse": ("🔐 Գաղտնի պահեստ", ["police", "factory", "apartments"]),
}


def build_world(player_count):
    location_names = {key: value[0] for key, value in LOCATIONS.items()}
    neighbors = {key: list(value[1]) for key, value in LOCATIONS.items()}

    objective_pool = ["hospital", "lab", "police", "factory", "warehouse"]
    medicine, weapon = random.sample(objective_pool, 2)

    lock_count = min(4, max(1, 1 + player_count // 12))
    locked = set(random.sample(objective_pool, lock_count))

    # Never lock both objective rooms permanently: a key/code path will open them.
    tasks = [
        "🔋 Գտիր մարտկոցը",
        "📻 Միացրու ռադիոն",
        "🔑 Գտիր պահեստի բանալին",
        "🗺️ Գտիր քարտեզի հատվածը",
        "📡 Ակտիվացրու ազդանշանը",
        "🧩 Գտիր գաղտնի կոդը",
    ]
    random.shuffle(tasks)

    item_locations = {
        "battery": random.choice(list(LOCATIONS)),
        "radio": random.choice(list(LOCATIONS)),
        "map_fragment": random.choice(list(LOCATIONS)),
        "key": random.choice(["police", "school", "apartments", "store"]),
    }

    return {
        "location_names": location_names,
        "neighbors": neighbors,
        "medicine": medicine,
        "weapon": weapon,
        "locked": locked,
        "tasks": tasks[: min(5, 3 + player_count // 20)],
        "item_locations": item_locations,
    }
