import random
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION

router = Router()


BOT_ADDED_TEXT = (
    "🌸 Привет, я Шиина Махиру!\n\n"
    "Я умею:\n"
    "💬 Общаться — просто напиши @ShiinaaAi_bot <сообщение>\n"
    "🎲 /coin — подбросить монетку\n"
    "📜 /quote — случайная цитата\n"
    "💗 /heart — получить сердечко\n"
    "💗 /hearts — мой счёт\n"
    "🏆 /top_hearts — топ любимчиков\n"
    "🔮 @ShiinaaAi_bot шанс <вопрос> — гадалка\n\n"
    "📖 /help — все команды"
)

WELCOME_TEXTS = [
    "🌸 О, {name} заглянул(а). Привет-привет.",
    "✨ {name}, ты как раз вовремя. Устраивайся.",
    "😊 Привет, {name}. Не стесняйся, тут не кусаются. Почти.",
    "🙃 {name}, надеюсь, ты пришёл(ла) с хорошим настроением. А то у нас тут и без тебя хватает.",
    "🌸 {name} присоединился(лась). Посмотрим, что ты за человек 😏",
    "✨ О, свежая кровь. Привет, {name}.",
    "😊 {name}, привет. Только не пиши «привет» три раза подряд, я это запомню.",
    "💗 {name}, добро пожаловать. Обещаю не подкалывать. Первые пять минут.",
    "🌸 Ну наконец-то, {name}. А то в чате скучно стало.",
    "😏 {name}, привет. Если ты пришёл(ла) флудить — тебе к другим.",
]

FAREWELL_TEXTS = [
    "🌸 {name} ушёл(ла). Ну и ладно.",
    "😏 {name}, уходишь? Скатертью дорожка.",
    "✨ О, {name} покинул(а) чат. Кто-то остался без внимания.",
    "🙃 Бля, {name} ушёл(ла). А я только привыкла.",
    "💗 {name}, возвращайся. Или не возвращайся. Мне всё равно 🌸",
    "😊 Пока, {name}. Захочешь — вернёшься.",
    "🌸 {name} сбежал(а). Не забудь написать, если что.",
    "😏 {name}, ты серьёзно уходишь? Ну-ну.",
    "✨ {name} ушёл(ла) тихо, без скандала. Уважаю.",
    "🙃 Минус один. {name}, тебя будет не хватать. Наверное.",
]


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_bot_added(event: ChatMemberUpdated):
    if event.chat.type not in {"group", "supergroup"}:
        return

    await event.bot.send_message(
        chat_id=event.chat.id,
        text=BOT_ADDED_TEXT,
    )


@router.message(F.new_chat_members)
async def on_new_members(message: Message):
    if message.chat.type not in {"group", "supergroup"}:
        return

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        name = user.first_name or user.username or "Кто-то"
        text = random.choice(WELCOME_TEXTS).format(name=name)
        await message.answer(text)


@router.message(F.left_chat_member)
async def on_left_member(message: Message):
    if message.chat.type not in {"group", "supergroup"}:
        return

    user = message.left_chat_member
    if user.is_bot:
        return

    name = user.first_name or user.username or "Кто-то"
    text = random.choice(FAREWELL_TEXTS).format(name=name)
    await message.answer(text)