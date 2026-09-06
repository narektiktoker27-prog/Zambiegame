import asyncio
import random
import time

from config import (
    BASE_ZOMBIES,
    MAX_GAME_MINUTES,
    MAX_INVENTORY,
    MIN_GAME_MINUTES,
    MIN_PLAYERS,
    NORMAL_START_BULLETS,
    TARGET_GAME_MINUTES,
    TWO_PLAYER_START_BULLETS,
)
from models import GameState, Player
from map_system import build_world
from inventory import add_item, has_item, remove_item, render_inventory
from combat import shoot_zombie, infected_bite
from zombie_ai import spawn_zombies, step_zombies
from events import choose_event


class GameManager:
    def __init__(self):
        self.games = {}

    def get(self, chat_id):
        return self.games.get(chat_id)

    def create(self, chat_id, creator_id):
        if chat_id in self.games:
            return None

        game = GameState(chat_id=chat_id, creator_id=creator_id)
        world = build_world(1)

        game.location_names = world["location_names"]
        game.neighbors = world["neighbors"]
        game.medicine_location = world["medicine"]
        game.weapon_location = world["weapon"]
        game.locked = set(world["locked"])
        game.tasks = list(world["tasks"])
        game.item_locations = dict(world["item_locations"])

        self.games[chat_id] = game
        return game

    def join(self, game, user):
        if game.phase != "LOBBY":
            return False, "Խաղն արդեն սկսվել է։"

        if len(game.players) >= 100:
            return False, "❌ Խաղը լիքն է։"

        if user.id not in game.players:
            game.players[user.id] = Player(
                user_id=user.id,
                name=user.full_name or str(user.id),
            )

        return True, "Դու միացար խաղին։"

    def start(self, game):
        if len(game.players) < MIN_PLAYERS:
            return False, "❌ Խաղը սկսելու համար պետք է առնվազն 2 խաղացող։"

        # Re-roll world with the real player count.
        world = build_world(len(game.players))
        game.location_names = world["location_names"]
        game.neighbors = world["neighbors"]
        game.medicine_location = world["medicine"]
        game.weapon_location = world["weapon"]
        game.locked = set(world["locked"])
        game.tasks = list(world["tasks"])
        game.item_locations = dict(world["item_locations"])

        game.difficulty = max(1, 1 + len(game.players) // 6)

        if len(game.players) == 2:
            zombie_count = 4
        else:
            zombie_count = min(
                180,
                BASE_ZOMBIES + len(game.players) * 2 + game.difficulty * 2,
            )

        spawn_zombies(game, zombie_count)

        starting_bullets = (
            TWO_PLAYER_START_BULLETS
            if len(game.players) == 2
            else NORMAL_START_BULLETS
        )

        for player in game.players.values():
            player.bullets = starting_bullets

        game.phase = "RUNNING"
        game.started_at = time.time()
        game.tick = 0
        return True, "Խաղը սկսվեց։"

    def delete(self, chat_id):
        self.games.pop(chat_id, None)

    def neighbors_for(self, game, player):
        return game.neighbors.get(player.location, [])

    def status_text(self, game, player):
        state = "🧟 ԶՈՄԲԻՆԵՐԻ ԹԻՄ" if player.infected else "👤 ՄԱՐԴ"
        return (
            f"{state}\n"
            f"📍 {game.location_names[player.location]}\n"
            f"❤️ Առողջություն՝ {player.health}\n"
            f"🩸 Վարակված՝ {'Այո' if player.infected else 'Ոչ'}\n"
            f"🔫 Փամփուշտներ՝ {player.bullets}\n"
            f"🎒 Գույք՝ {render_inventory(player)}"
        )

    def search(self, game, player):
        location = player.location

        if location in game.locked:
            if has_item(player, "key"):
                remove_item(player, "key")
                game.locked.remove(location)
                game.unlocked.add(location)
                return "🔑 Դու օգտագործեցիր բանալին և բացեցիր փակ տարածքը։"

            if random.random() < 0.35:
                add_item(player, "key")
                return "🔑 Դու գտար բանալի։ Փակ տարածքները հիմա կարող են բացվել։"

            return "🚪 Տարածքը փակ է։ Այստեղ ինչ-որ բան է պետք։"

        if location == game.medicine_location and not game.medicine_found:
            game.medicine_found = True
            player.medicine = True
            add_item(player, "medicine")
            return "💊 Դու գտար ՀԱՏՈՒԿ ԲՈՒԺԻՉ ՆՅՈՒԹԸ։ Այն պետք է վերջնական բուժման համար։"

        if location == game.weapon_location and not game.weapon_found:
            game.weapon_found = True
            player.special_weapon = True
            add_item(player, "special_weapon")
            return "🔫 Դու գտար ՀԱՏՈՒԿ ԶԵՆՔԸ։"

        special_items = [
            ("battery", "🔋 Դու գտար մարտկոց։"),
            ("first_aid", "🩹 Դու գտար առաջին օգնության փաթեթ։"),
            ("map_fragment", "🗺️ Դու գտար քարտեզի հատված։"),
            ("radio", "📻 Դու գտար ռադիո։"),
        ]

        if random.random() < 0.46:
            item, message = random.choice(special_items)
            if add_item(player, item):
                return message
            return "🎒 Գույքդ լիքն է։"

        if random.random() < 0.45:
            player.bullets += random.randint(1, 2)
            return "🔫 Դու գտար 1–2 սովորական փամփուշտ։"

        available = [
            task for task in game.tasks
            if task not in game.completed_tasks
        ]
        if available and random.random() < 0.32:
            task = random.choice(available)
            game.completed_tasks.add(task)
            return f"🧩 Առաջադրանք կատարված է՝ {task}"

        return "🔍 Ոչինչ օգտակար չգտար։ Քաղաքը լուռ է... չափազանց լուռ։"

    def move(self, game, player, destination):
        if destination not in game.neighbors.get(player.location, []):
            return False, "❌ Այդ վայրը այստեղից հասանելի չէ։"

        if destination in game.locked:
            return False, "🚪 Ճանապարհը փակ է։ Նախ անհրաժեշտ է բանալի կամ բացման գործողություն։"

        player.location = destination
        player.hidden = False
        return True, f"📍 Դու հասար {game.location_names[destination]}։"

    def hide(self, player):
        player.hidden = True
        return "🚪 Դու թաքնվեցիր։ Հաջորդ zombie ստուգման ժամանակ քեզ հայտնաբերելը դժվար կլինի։"

    def flee(self, game, player):
        exits = self.neighbors_for(game, player)
        if not exits:
            return "🏃 Փախչելու ուղղություն չկա։"

        # Prefer an exit without a visible zombie.
        danger_locations = {
            z.location for z in game.zombies.values()
            if z.alive
        }
        safe = [x for x in exits if x not in danger_locations]
        destination = random.choice(safe or exits)
        player.location = destination
        player.hidden = False
        return f"🏃 Դու փախար դեպի {game.location_names[destination]}։"

    def shoot(self, game, player):
        zombie = next(
            (
                z for z in game.zombies.values()
                if z.alive and z.location == player.location
            ),
            None,
        )
        if zombie is None:
            return "🧟 Այստեղ կենդանի NPC զոմբի չկա։"

        _, message = shoot_zombie(player, zombie)
        return message

    def prepare_cure(self, game, player):
        if not player.medicine:
            return False, "💊 Հատուկ բուժիչ նյութը քեզ մոտ չէ։"

        if not player.special_weapon:
            return False, "🔫 Հատուկ զենքը քեզ մոտ չէ։"

        if not player.healing_bullet:
            player.healing_bullet = True
            game.cure_ready = True
            return True, "💥 Դու համադրեցիր դեղանյութը հատուկ զենքի հետ և պատրաստեցիր բուժիչ փամփուշտը։"

        return True, "💥 Բուժիչ փամփուշտն արդեն պատրաստ է։"

    def fire_cure(self, game, player):
        if not player.healing_bullet:
            return False, "💥 Բուժիչ փամփուշտը դեռ պատրաստ չէ։"

        if not player.special_weapon:
            return False, "🔫 Հատուկ զենքը պետք է քեզ մոտ լինի։"

        game.cure_used = True
        game.phase = "WON"
        game.winner = "HUMANS"
        game.end_reason = "Վերջնական բուժումը հաջողվեց։"

        for p in game.players.values():
            p.infected = False
            p.health = 100
            p.alive = True

        for z in game.zombies.values():
            z.alive = False
            z.state = "DEAD"

        return True, "CURE"

    def infected_scout(self, game, player):
        locations = {}
        for p in game.alive_humans():
            locations.setdefault(p.location, []).append(p.name)

        if not locations:
            return "👁️ Այլևս առողջ մարդ չկա։"

        if player.location in locations:
            return "👁️ Այստեղ մարդ կա։"

        return "👁️ Դու զգում ես մարդկանց ներկայությունը քաղաքի որոշ հատվածներում։"

    def infected_chase(self, game, player):
        humans = game.alive_humans()
        if not humans:
            return "👁️ Թիրախ չկա։"

        # Limited information: reveal a target's neighboring region indirectly.
        target = random.choice(humans)
        exits = game.neighbors.get(player.location, [])

        if target.location in exits:
            player.location = target.location
            return "🏃 Հետապնդման ընթացքում դու հասար թիրախի տարածք։"

        if exits:
            player.location = random.choice(exits)
            return "🏃 Դու հետևեցիր հետքին և տեղափոխվեցիր մոտակա տարածք։"

        return "🏃 Հետքը կորավ։"

    def infected_hide(self, player):
        player.hidden = True
        return "🧟 Դու թաքնվեցիր։"

    def infected_bite_action(self, game, player):
        targets = [
            p for p in game.alive_humans()
            if p.location == player.location
        ]
        if not targets:
            return False, "🦷 Այստեղ առողջ մարդ չկա։"

        target = random.choice(targets)
        success = infected_bite(player, target)
        if not success:
            return False, "🦷 Թիրախը կարողացավ խուսափել։"

        return True, target

    def use_first_aid(self, player):
        if not has_item(player, "first_aid"):
            return False, "🩹 Առաջին օգնություն չունես։"

        if player.health >= 100:
            return False, "❤️ Առողջությունդ արդեն լիքն է։"

        remove_item(player, "first_aid")
        player.health = min(100, player.health + 35)
        return True, "🩹 Առաջին օգնությունը օգտագործվեց։"

    def check_end_conditions(self, game):
        if game.phase != "RUNNING":
            return

        if not game.alive_humans():
            game.phase = "LOST"
            game.winner = "ZOMBIES"
            game.end_reason = "Բոլոր իրական խաղացողները վարակվեցին։"
            return

        elapsed = (time.time() - game.started_at) / 60

        # Never force a loss before the minimum intended duration.
        # After the maximum duration the outbreak overwhelms the city.
        if elapsed >= MAX_GAME_MINUTES:
            game.phase = "LOST"
            game.winner = "ZOMBIES"
            game.end_reason = "Քաղաքի պաշտպանությունը փլուզվեց։ Ժամանակը սպառվեց։"

    async def send_private(self, application, player, text, keyboard=None):
        try:
            await application.bot.send_message(
                chat_id=player.user_id,
                text=text,
                reply_markup=keyboard,
            )
            return True
        except Exception:
            return False

    async def world_loop(self, application):
        while True:
            await asyncio.sleep(12)

            for game in list(self.games.values()):
                if game.phase != "RUNNING":
                    continue

                game.tick += 1
                step_zombies(game)

                # Infected player AI is intentionally player-controlled,
                # but periodic pressure keeps them relevant.
                for infected in game.alive_infected():
                    if random.random() < 0.15:
                        nearby = [
                            p for p in game.alive_humans()
                            if p.location == infected.location
                        ]
                        if nearby:
                            target = random.choice(nearby)
                            if infected_bite(infected, target):
                                try:
                                    await application.bot.send_message(
                                        target.user_id,
                                        "🩸 Դու հանկարծակի հարձակման ենթարկվեցիր...\n"
                                        "🧟 Դու վարակվեցիր։",
                                    )
                                except Exception:
                                    pass

                event = choose_event(game)
                if event and game.tick - game.last_event_tick >= 2:
                    game.last_event_tick = game.tick
                    game.events_seen += 1
                    kind, text = event
                    # Atmosphere and danger events are deliberately ambiguous.
                    try:
                        await application.bot.send_message(
                            game.chat_id,
                            text,
                        )
                    except Exception:
                        pass

                self.check_end_conditions(game)

                if game.phase in {"WON", "LOST"}:
                    try:
                        await self.broadcast_end(application, game)
                    except Exception:
                        pass

    async def broadcast_end(self, application, game):
        if game.finalizing:
            return
        game.finalizing = True

        if game.phase == "WON":
            sequence = [
                "🔫 Դու բարձրացրեցիր զենքը...",
                "🌌 Քաղաքը լռեց...",
                "💥 ԿՐԱԿՈՑ։",
                "🧟🧟🧟 ...",
                "✨ ԲՈՒԺԻՉ ԱԼԻՔԸ ՏԱՐԱԾՎԵՑ ՔԱՂԱՔՈՎ։",
                "👤 Բոլոր վարակվածները բուժվեցին։",
                "🎉 ՎԱՐԱԿՎԱԾ ՔԱՂԱՔԸ ՓՐԿՎԵՑ։",
            ]
        else:
            sequence = [
                "🌑 Քաղաքի վերջին լույսերը մարեցին...",
                "🧟 Զոմբիների ձայները մոտեցան...",
                "☠️ ՎԱՐԱԿԸ ՀԱՂԹԵՑ։",
                "🧟 Քաղաքը այլևս անվտանգ չէ։",
            ]

        for text in sequence:
            try:
                await application.bot.send_message(game.chat_id, text)
            except Exception:
                pass
            await asyncio.sleep(1.2)

        elapsed = (time.time() - game.started_at) / 60 if game.started_at else 0
        summary = (
            f"\n\n⏱️ Տևողություն՝ {elapsed:.1f} րոպե"
            f"\n👥 Խաղացողներ՝ {len(game.players)}"
            f"\n🧟 NPC զոմբիներ՝ {len(game.zombies)}"
            f"\n📡 Պատահական իրադարձություններ՝ {game.events_seen}"
        )

        try:
            await application.bot.send_message(
                game.chat_id,
                ("🎉 ԽԱՂԻ ՎԵՐՋ\n" if game.phase == "WON" else "☠️ ԽԱՂԻ ՎԵՐՋ\n")
                + game.end_reason
                + summary,
            )
        except Exception:
            pass
