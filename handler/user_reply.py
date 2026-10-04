from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from ai import ask_shiina
from database import (
    get_hearts, add_hearts, get_top, get_user_rank,
    log_metric,
    get_metrics_summary, get_top_users, get_recent_errors, get_top_words,
    get_mode_breakdown, get_avg_duration,
)
import random
import re
import json
import datetime
import os

router = Router()

ADMIN_ID = os.getenv("ADMIN_ID")


QUOTES_FILE = "quotes.json"

QUOTE_COMMENTS = [
    "Хм, а ведь что-то в этом есть 😏",
    "Блин, даже задумалась 🌸",
    "Ну, тут не поспоришь ✨",
    "Кто это вообще придумал? 😅",
    "Сохранила себе в цитатник 🙃",
    "Иногда полезно такое вспомнить 😊",
    "Звучит умно, аж завидно 😏",
    "Мне нравится. Не спрашивай почему 🌸",
    "Ну да, ну да. Как будто я спорила ✨",
    "Запиши куда-нибудь, пригодится 🙃",
]

HEART_COMMENTS = [
    "Держи, ты сегодня не бесил 🌸",
    "Ладно, вот тебе немного тепла ✨",
    "Ну... ты старался, так что вот 😏",
    "Не привыкай, но сегодня — твоя удача 💗",
    "Блин, ну как тут не подобреешь 🙃",
    "Шиина сегодня добрая. Не наглей 😊",
    "Вот. Но не думай, что ты особенный ✨",
    "Просто хорошее настроение. Не твоя заслуга 🌸",
    "Держи, мне не жалко 💗",
    "Немного милоты тебе на сегодня 😏",
]


def load_quotes():
    with open(QUOTES_FILE, "r", encoding="utf-8-sig") as f:
        return json.load(f)



@router.message(Command("start"), F.chat.type == "private")
async def start_private(message: Message):
    await message.answer(
        "🌸 Привет! Я Шиина Махиру!\n\n"
        "Я живу в групповых чатах и могу:\n"
        "💬 Общаться с участниками группы\n"
        "✨ Отвечать на ваши сообщения\n"
        "🎲 Развлекать вас различными командами\n"
        "🌸 Поддерживать интересное общение\n\n"
        "📌 Чтобы начать общение, добавь меня в свою группу и напиши:\n\n"
        "@ShiinaaAi_bot привет\n\n"
        "Я обязательно отвечу 😊\n\n"
        "📖 Доступные команды и функции — в меню ниже.\n\n"
    )


@router.message(Command("help"), F.chat.type == "private")
async def help_private(message: Message):
    await message.answer(
        "📋 Команды Шиины:\n\n"
        "👤 В личке:\n"
        "🟢 /start — информация о боте\n"
        "📋 /help — список команд\n\n"
        "👥 В группе:\n"
        "🟢 /start@ShiinaaAi_bot — информация о боте\n"
        "📋 /help@ShiinaaAi_bot — список команд\n"
        "🟡 /coin@ShiinaaAi_bot — подбросить монетку\n"
        "📜 /quote@ShiinaaAi_bot — случайная цитата\n"
        "💗 /heart@ShiinaaAi_bot — получить сердечко\n"
        "💗 /hearts@ShiinaaAi_bot — посмотреть свой счёт\n"
        "🏆 /top_hearts@ShiinaaAi_bot — топ-10 любимчиков\n\n"
        "💬 Общение:\n"
        "@ShiinaaAi_bot <сообщение>\n"
        "Например: @ShiinaaAi_bot привет 🌸"
    )



@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def start_group(message: Message):
    await message.answer(
        "🌸 Привет! Я Шиина Махиру!\n"
        "Чтобы поговорить со мной, просто напиши:\n\n"
        "@ShiinaaAi_bot привет\n\n"
        "Я обязательно отвечу 😊"
    )


@router.message(Command("help"), F.chat.type.in_({"group", "supergroup"}))
async def group_help(message: Message):
    await message.answer(
        "📋 Команды Шиины:\n\n"
        "👤 В личке:\n"
        "🟢 /start — информация о боте\n"
        "📋 /help — список команд\n\n"
        "👥 В группе:\n"
        "🟢 /start@ShiinaaAi_bot — информация о боте\n"
        "📋 /help@ShiinaaAi_bot — список команд\n"
        "🟡 /coin@ShiinaaAi_bot — подбросить монетку\n"
        "📜 /quote@ShiinaaAi_bot — случайная цитата\n"
        "💗 /heart@ShiinaaAi_bot — получить сердечко\n"
        "💗 /hearts@ShiinaaAi_bot — посмотреть свой счёт\n"
        "🏆 /top_hearts@ShiinaaAi_bot — топ-10 любимчиков\n\n"
        "💬 Общение:\n"
        "@ShiinaaAi_bot <сообщение>\n"
        "Например: @ShiinaaAi_bot привет 🌸"
    )


@router.message(Command("coin"), F.chat.type.in_({"group", "supergroup"}))
async def coin_group(message: Message):
    result = random.choice(["Орёл", "Решка"])
    await message.answer(f"Выпало: {result}")

    log_metric(
        chat_id=str(message.chat.id),
        user_id=str(message.from_user.id),
        username=message.from_user.username or message.from_user.first_name,
        event_type="command_coin",
    )


@router.message(Command("quote"), F.chat.type.in_({"group", "supergroup"}))
async def quote_group(message: Message):
    quotes = load_quotes()

    if not quotes:
        await message.answer("Цитаты закончились 🌸")
        return

    quote = random.choice(quotes)
    comment = random.choice(QUOTE_COMMENTS)

    text = f"«{quote['text']}»"
    if quote.get("author"):
        text += f"\n— {quote['author']}"
    text += f"\n\n{comment}"

    await message.answer(text)

    log_metric(
        chat_id=str(message.chat.id),
        user_id=str(message.from_user.id),
        username=message.from_user.username or message.from_user.first_name,
        event_type="command_quote",
    )


@router.message(Command("heart"), F.chat.type.in_({"group", "supergroup"}))
async def heart_group(message: Message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "Кто-то"
    today = datetime.date.today().isoformat()

    row = get_hearts(chat_id, user_id)

    if row and row["last_date"] == today:
        await message.answer("Ты уже получал сегодня. Приходи завтра 🌸")
        return

    amount = random.randint(1, 20)
    comment = random.choice(HEART_COMMENTS)

    add_hearts(chat_id, user_id, name, amount, today)

    new_row = get_hearts(chat_id, user_id)
    total = new_row["hearts"] if new_row else amount

    await message.answer(
        f"Шиина подарила тебе +{amount} сердечек 💗\n"
        f"У тебя {total} сердечек.\n\n"
        f"{comment}"
    )

    log_metric(
        chat_id=chat_id,
        user_id=user_id,
        username=message.from_user.username or name,
        event_type="command_heart",
        response=str(amount),
    )


@router.message(Command("hearts"), F.chat.type.in_({"group", "supergroup"}))
async def hearts_group(message: Message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    row = get_hearts(chat_id, user_id)

    if not row:
        await message.answer("У тебя пока 0 сердечек. Напиши /heart 💗")
        return

    rank = get_user_rank(chat_id, user_id)
    await message.answer(
        f"У тебя {row['hearts']} сердечек 💗\n"
        f"Ты на {rank} месте в этой группе."
    )

    log_metric(
        chat_id=chat_id,
        user_id=user_id,
        username=message.from_user.username or message.from_user.first_name,
        event_type="command_hearts",
    )


@router.message(Command("top_hearts"), F.chat.type.in_({"group", "supergroup"}))
async def top_hearts_group(message: Message):
    chat_id = str(message.chat.id)
    rows = get_top(chat_id, limit=10)

    if not rows:
        await message.answer("Тут пока никто не получал сердечки 🌸")
        return

    lines = ["🏆 Топ любимчиков Шиины:"]
    for i, row in enumerate(rows, start=1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(f"{medal} {row['name']} — {row['hearts']} 💗")

    await message.answer("\n".join(lines))

    log_metric(
        chat_id=chat_id,
        user_id=str(message.from_user.id),
        username=message.from_user.username or message.from_user.first_name,
        event_type="command_top_hearts",
    )



@router.message(Command("stats"), F.chat.type.in_({"group", "supergroup"}))
async def stats_group(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        return

    summary = get_metrics_summary(days=7)
    modes = get_mode_breakdown(days=7)
    avg_ms = get_avg_duration(days=7)
    top_users = get_top_users(days=7, limit=5)
    top_words = get_top_words(days=7, limit=10)
    errors = get_recent_errors(limit=5)

    lines = ["📊 Статистика за 7 дней:"]

    if not summary:
        lines.append("(пока нет данных)")
    else:
        for row in summary:
            lines.append(f"• {row['event_type']}: {row['cnt']}")

    if modes:
        lines.append("\n📈 Режимы AI:")
        for row in modes:
            lines.append(f"• {row['mode']}: {row['cnt']}")

    if avg_ms:
        lines.append(f"\n⏱ Средняя скорость ответа: {avg_ms} мс")

    if top_users:
        lines.append("\n👥 Топ активных:")
        for row in top_users:
            uname = row["username"] or row["user_id"]
            lines.append(f"• {uname}: {row['cnt']}")

    if top_words:
        lines.append("\n🔥 Частые слова в запросах:")
        for word, count in top_words:
            lines.append(f"• {word}: {count}")

    if errors:
        lines.append("\n⚠️ Последние ошибки:")
        for row in errors:
            lines.append(f"• {row['model']}: {str(row['response'])[:40]}")

    await message.answer("\n".join(lines))



@router.message(
    F.text.regexp(r"^@ShiinaaAi_bot\s+шанс\b", flags=re.IGNORECASE),
    F.chat.type.in_({"group", "supergroup"})
)
async def gadalka(message: Message):
    text = message.text.replace("@ShiinaaAi_bot", "").strip()
    text = re.sub(r"^шанс\b\s*", "", text, flags=re.IGNORECASE).strip()

    if not text:
        await message.answer("А что гадать-то? 😶‍🌫️")
        return

    result = random.randint(1, 100)

    if result == 100:
        await message.answer("О, тут даже гадать нечего — 100% 🌸")
    elif result >= 80:
        await message.answer(f"Блин, да почти наверняка. {result}% 😏")
    elif result > 50:
        await message.answer(f"Хм, скорее да, чем нет. {result}% ✨")
    elif result == 50:
        await message.answer("Ну, ровно 50 на 50. Как монетка 🙃")
    elif result > 20:
        await message.answer(f"Скорее нет, чем да. {result}% 😊")
    else:
        await message.answer(f"Бля, шансы так себе. {result}% 🙃")

    log_metric(
        chat_id=str(message.chat.id),
        user_id=str(message.from_user.id),
        username=message.from_user.username or message.from_user.first_name,
        event_type="command_gadalka",
        text=text,
        response=str(result),
    )



@router.message(F.text.startswith("@ShiinaaAi_bot"), F.chat.type.in_({"group", "supergroup"}))
async def user_message(message: Message):
    the_text = message.text.replace("@ShiinaaAi_bot", "").strip()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name

    response = await ask_shiina(
        the_text,
        chat_id=chat_id,
        user_id=user_id,
        username=username,
    )
    await message.answer(response)