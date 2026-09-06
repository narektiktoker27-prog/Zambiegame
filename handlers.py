from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import MAX_PLAYERS, MIN_PLAYERS
from game_engine import GameManager


def lobby_keyboard(chat_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 Միանալ", callback_data=f"join:{chat_id}"),
            InlineKeyboardButton("▶️ Սկսել", callback_data=f"start:{chat_id}"),
        ]
    ])


def player_keyboard(game, player):
    chat_id = game.chat_id

    rows = []

    if player.infected:
        rows.append([
            InlineKeyboardButton("🦷 Կծել", callback_data=f"bite:{chat_id}"),
            InlineKeyboardButton("👁️ Հետախուզել", callback_data=f"scout:{chat_id}"),
        ])
        rows.append([
            InlineKeyboardButton("🏃 Հետապնդել", callback_data=f"chase:{chat_id}"),
            InlineKeyboardButton("🧟 Թաքնվել", callback_data=f"ihide:{chat_id}"),
        ])
    else:
        rows.append([
            InlineKeyboardButton("🔫 Կրակել", callback_data=f"shoot:{chat_id}"),
            InlineKeyboardButton("🏃 Փախչել", callback_data=f"flee:{chat_id}"),
        ])
        rows.append([
            InlineKeyboardButton("🚪 Թաքնվել", callback_data=f"hide:{chat_id}"),
            InlineKeyboardButton("🩹 Բուժվել", callback_data=f"heal:{chat_id}"),
        ])

    rows.extend([
        [
            InlineKeyboardButton("🔍 Փնտրել", callback_data=f"search:{chat_id}"),
            InlineKeyboardButton("🚪 Տեղափոխվել", callback_data=f"move:{chat_id}"),
        ],
        [
            InlineKeyboardButton("🎒 Գույք", callback_data=f"inv:{chat_id}"),
            InlineKeyboardButton("🗺️ Քարտեզ", callback_data=f"map:{chat_id}"),
        ],
    ])

    if not player.infected:
        rows.append([
            InlineKeyboardButton("🧪 Պատրաստել բուժումը", callback_data=f"prepare:{chat_id}"),
            InlineKeyboardButton("💥 Կրակել բուժիչ փամփուշտը", callback_data=f"cure:{chat_id}"),
        ])

    return InlineKeyboardMarkup(rows)


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or chat.type == "private":
        await update.message.reply_text("❌ Խաղը պետք է ստեղծել Telegram խմբում։")
        return

    manager: GameManager = context.application.bot_data["manager"]

    if manager.get(chat.id):
        await update.message.reply_text("⚠️ Այս խմբում արդեն կա ընթացիկ խաղ։")
        return

    game = manager.create(chat.id, user.id)
    manager.join(game, user)

    await update.message.reply_text(
        "🧟 ՎԱՐԱԿՎԱԾ ՔԱՂԱՔԸ\n\n"
        "Քաղաքում տարածվել է անհայտ վարակ։\n"
        "Գտեք 💊 բուժիչ նյութը, 🔫 հատուկ զենքը և պատրաստեք բուժիչ փամփուշտը։\n\n"
        "👥 Խաղացողներ՝ 1/100\n"
        "⚠️ Մեկ խաղացողի դեպքում խաղը չի սկսվում։\n\n"
        "Խաղը ստեղծողը կարող է սեղմել «Սկսել»։",
        reply_markup=lobby_keyboard(chat.id),
    )


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    manager: GameManager = context.application.bot_data["manager"]
    game = manager.get(chat.id) if chat else None

    if not game:
        await update.message.reply_text("ℹ️ Այս խմբում ընթացիկ խաղ չկա։ Օգտագործիր /startgame")
        return

    player = game.players.get(user.id)
    if not player:
        await update.message.reply_text("❌ Դու այս խաղի մասնակից չես։")
        return

    await update.message.reply_text(
        manager.status_text(game, player),
        reply_markup=player_keyboard(game, player),
    )


async def deletegame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    manager: GameManager = context.application.bot_data["manager"]
    game = manager.get(chat.id) if chat else None

    if not game:
        await update.message.reply_text("ℹ️ Այս խմբում ընթացիկ խաղ չկա։")
        return

    if update.effective_user.id != game.creator_id:
        await update.message.reply_text("❌ Դու այս խաղի ստեղծողը չես։")
        return

    await update.message.reply_text(
        "⚠️ Վստա՞հ ես, որ ուզում ես ջնջել ընթացիկ խաղը։",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Ջնջել խաղը", callback_data=f"confirmdelete:{chat.id}"),
            InlineKeyboardButton("❌ Չեղարկել", callback_data=f"canceldelete:{chat.id}"),
        ]]),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    action = parts[0]
    chat_id = int(parts[1])

    manager: GameManager = context.application.bot_data["manager"]
    game = manager.get(chat_id)

    if not game:
        await query.message.reply_text("ℹ️ Խաղն այլևս գոյություն չունի։")
        return

    user = query.from_user
    player = game.players.get(user.id)

    if action == "join":
        ok, message = manager.join(game, user)
        await query.edit_message_text(
            "🧟 ՎԱՐԱԿՎԱԾ ՔԱՂԱՔԸ\n\n"
            f"👥 Խաղացողներ՝ {len(game.players)}/{MAX_PLAYERS}\n"
            f"{message}\n\n"
            "Երբ պատրաստ եք, Creator-ը կարող է սեղմել «Սկսել»։",
            reply_markup=lobby_keyboard(chat_id),
        )
        return

    if action == "start":
        if user.id != game.creator_id:
            await query.answer("❌ Միայն Creator-ը կարող է սկսել։", show_alert=True)
            return

        ok, message = manager.start(game)
        if not ok:
            await query.answer(message, show_alert=True)
            return

        await query.edit_message_text(
            "🧟 ԽԱՂԸ ՍԿՍՎԵՑ\n\n"
            f"👥 Խաղացողներ՝ {len(game.players)}\n"
            "🔍 Քաղաքը ստեղծվեց պատահականորեն։\n"
            "🤫 Գաղտնի տվյալները կստանաք Private Chat-ում։"
        )

        for p in game.players.values():
            sent = await manager.send_private(
                context.application,
                p,
                "🤫 ՔՈ ԳԱՂՏՆԻ ԽԱՂԱՅԻՆ ՎԱՀԱՆԱԿԸ\n\n"
                + manager.status_text(game, p),
                player_keyboard(game, p),
            )
            if not sent:
                try:
                    await context.bot.send_message(
                        chat_id=game.chat_id,
                        text=f"⚠️ {p.name}-ի private chat-ը հասանելի չէ։"
                    )
                except Exception:
                    pass
        return

    if action == "confirmdelete":
        if user.id != game.creator_id:
            await query.answer("❌ Դու Creator-ը չես։", show_alert=True)
            return
        manager.delete(chat_id)
        await query.edit_message_text("🗑️ Ընթացիկ խաղը ջնջվեց RAM-ից։")
        return

    if action == "canceldelete":
        await query.edit_message_text("❌ Ջնջումը չեղարկվեց։")
        return

    if not player:
        await query.answer("❌ Դու այս խաղի մասնակից չես։", show_alert=True)
        return

    if game.phase != "RUNNING":
        await query.answer("ℹ️ Խաղն ավարտված է։", show_alert=True)
        return

    if action == "inv":
        await query.message.reply_text(
            manager.status_text(game, player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "map":
        lines = ["🗺️ ՔԱՂԱՔ"]
        for key, name in game.location_names.items():
            exits = ", ".join(game.location_names[x] for x in game.neighbors[key])
            marker = "🔒" if key in game.locked else "📍"
            lines.append(f"{marker} {name} → {exits}")

        await query.message.reply_text(
            "\n".join(lines),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "search":
        result = manager.search(game, player)
        await query.message.reply_text(
            result,
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "hide":
        await query.message.reply_text(
            manager.hide(player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "ihide":
        await query.message.reply_text(
            manager.infected_hide(player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "flee":
        await query.message.reply_text(
            manager.flee(game, player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "shoot":
        await query.message.reply_text(
            manager.shoot(game, player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "heal":
        ok, result = manager.use_first_aid(player)
        await query.message.reply_text(
            result,
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "bite":
        ok, result = manager.infected_bite_action(game, player)
        if ok:
            target = result
            try:
                await context.bot.send_message(
                    target.user_id,
                    "🩸 Դու այլևս առաջվանը չես...\n"
                    "🧟 Դու վարակվեցիր և ստացար ԶՈՄԲԻՆԵՐԻ ԹԻՄԻ գաղտնի գործողությունները։",
                    reply_markup=player_keyboard(game, target),
                )
            except Exception:
                pass

            await query.message.reply_text(
                "🦷 Դու կծեցիր թիրախին։",
                reply_markup=player_keyboard(game, player),
            )
        else:
            await query.message.reply_text(
                result,
                reply_markup=player_keyboard(game, player),
            )
        return

    if action == "scout":
        await query.message.reply_text(
            manager.infected_scout(game, player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "chase":
        await query.message.reply_text(
            manager.infected_chase(game, player),
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "prepare":
        ok, result = manager.prepare_cure(game, player)
        await query.message.reply_text(
            result,
            reply_markup=player_keyboard(game, player),
        )
        return

    if action == "cure":
        ok, result = manager.fire_cure(game, player)
        if not ok:
            await query.message.reply_text(
                result,
                reply_markup=player_keyboard(game, player),
            )
            return

        # The world loop will broadcast the cinematic once.
        await query.message.reply_text("🔫 Դու կրակեցիր օդ։ Քաղաքը սպասում է բուժիչ ալիքին...")
        return

    if action == "move":
        destinations = manager.neighbors_for(game, player)
        buttons = [
            [InlineKeyboardButton(
                game.location_names[d],
                callback_data=f"goto:{chat_id}:{d}"
            )]
            for d in destinations
        ]
        await query.message.reply_text(
            "🚪 Ընտրիր ուղղությունը։",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return


async def goto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, chat_id_text, destination = query.data.split(":")
    chat_id = int(chat_id_text)

    manager: GameManager = context.application.bot_data["manager"]
    game = manager.get(chat_id)
    if not game:
        await query.message.reply_text("ℹ️ Խաղն ավարտված է կամ ջնջված է։")
        return

    player = game.players.get(query.from_user.id)
    if not player:
        await query.answer("❌ Դու այս խաղում չկաս։", show_alert=True)
        return

    ok, message = manager.move(game, player, destination)
    await query.message.reply_text(
        message,
        reply_markup=player_keyboard(game, player),
    )


def register_handlers(application, manager):
    application.bot_data["manager"] = manager

    application.add_handler(CommandHandler("startgame", startgame))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("deletegame", deletegame))

    application.add_handler(
        CallbackQueryHandler(goto, pattern=r"^goto:")
    )
    application.add_handler(
        CallbackQueryHandler(button)
    )
