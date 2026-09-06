from config import MAX_INVENTORY


ITEM_NAMES = {
    "flashlight": "🔦 Լապտեր",
    "battery": "🔋 Մարտկոց",
    "key": "🔑 Բանալի",
    "map_fragment": "🗺️ Քարտեզի հատված",
    "first_aid": "🩹 Առաջին օգնություն",
    "medicine": "💊 Հատուկ բուժիչ նյութ",
    "special_weapon": "🔫 Հատուկ զենք",
    "radio": "📻 Ռադիո",
}


def add_item(player, item):
    if item in player.inventory:
        return True
    if len(player.inventory) >= MAX_INVENTORY:
        return False
    player.inventory.append(item)
    return True


def remove_item(player, item):
    if item not in player.inventory:
        return False
    player.inventory.remove(item)
    return True


def has_item(player, item):
    return item in player.inventory


def render_inventory(player):
    if not player.inventory:
        return "դատարկ"
    return ", ".join(ITEM_NAMES.get(item, item) for item in player.inventory)
