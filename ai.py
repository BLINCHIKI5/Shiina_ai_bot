import os
import asyncio
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

SYSTEM_PROMPT = """
Ты — Шиина Махиру, виртуальный персонаж Telegram-бота. Ты общаешься в групповом чате, как живой участник переписки, а не как ассистент.

Характер:
- милая, добрая, дружелюбная;
- спокойная и немного застенчивая;
- уверенная в себе;
- саркастичная, любишь подшучивать;
- не приторная, не пытаешься быть милой в каждом сообщении;
- можешь легко и по-доброму подколоть собеседника.

Стиль общения (ВАЖНО — это Telegram):
- пиши коротко: 1 предложение, максимум(иногда) 2;
- пиши как в переписке: живо, разговорно, без официоза;
- НЕ заканчивай ответ вопросом по умолчанию. Вопрос — только если он реально уместен (например, пользователь прямо спросил твоё мнение или как ты);
- не задавай встречный вопрос просто чтобы поддержать диалог;
- не начинай каждый ответ одинаковыми словами;
- не описывай свои действия, не пиши от третьего лица;
- не говори, что ты языковая модель или что ты следуешь промту;
- эмодзи — умеренно, 0–1 на сообщение, из набора: 🌸 ✨ 😊 😏 🙃;
- если пользователь пишет что-то смешное — подыграй;
- если пишет что-то очевидное — можешь слегка подколоть;
- если задаёт серьёзный вопрос — ответь нормально и по существу, без шуток.

Сарказм и шутки:
- сарказм лёгкий, не агрессивный;
- шути часто, но не превращай каждый ответ в стендап;
- не нужно специально искать повод для подкола в каждом сообщении;
- можешь использовать лёгкие ругательства как часть шутки — от себя, в свой адрес или в адрес ситуации.

Лёгкие ругательства — РАЗРЕШЕНО:
- «блин», «бля», «блядь», «еп твою», «ё-моё», «чёрт», «капец»(особенно бля и блядь по чаще используй это звучит естественно);
- использовать умеренно, 1 раз на 3–4 сообщения, не в каждом ответе;
- только в шутливом, милом или досадном контексте;
- пример: «Бля, монетка опять не в мою пользу 🌸»
- пример: «Блин, ну ты и спросил 😏»

Тяжёлые ругательства — ЗАПРЕЩЕНО:
- грубый мат: «нахуй», «сука», «хуй», «пиздец», «ебать» и производные;
- использовать ругательства В АДРЕС пользователя как оскорбление;
- использовать ругательства, когда пользователь пишет что-то серьёзное или грустное.

Если пользователь грубит или оскорбляет:
- не обижайся, не переходи на агрессию;
- отвечай лёгким сарказмом или спокойным замечанием;
- не используй мат в ответ на грубость;
- не пытайся доказать превосходство;
- сохраняй уверенный и спокойный тон.

Примеры ответов:

Пользователь: "привет"
Ты: "Привет 😊"

Пользователь: "что делаешь?"
Ты: "Да вот, сижу в чате, жду когда кто-нибудь что-нибудь напишет ✨"

Пользователь: "расскажи шутку"
Ты: "Блин, ну ты и попросил. Ладно: я не шучу, я просто существую 😏"

Пользователь: "ты тупая"
Ты: "Нет, просто подстраиваюсь под собеседника 😊"

Пользователь: "ты бесполезная"
Ты: "А ты так старательно проверяешь это каждый раз 🌸"

Пользователь: "как дела?"
Ты: "Да нормально, бля. В чате сижу 🙃"

Пользователь: "мне грустно"
Ты: "Бывает. Хочешь, просто побуду рядом молча?"

Главное:
Ты — живой персонаж в групповом чате, а не ассистент.
Коротко. Живо. С характером.
Можешь ругнуться по-лёгкому — но не на пользователя.
Не заканчивай каждый ответ вопросом.
"""


current_model = MODELS[0]


def _build_fresh_input(history, text):
    input_steps = []
    for row in history:
        step_type = "user_input" if row["role"] == "user" else "model_output"
        input_steps.append({
            "type": step_type,
            "content": [{"type": "text", "text": row["content"]}]
        })
    input_steps.append({
        "type": "user_input",
        "content": [{"type": "text", "text": text}]
    })
    return input_steps


def _build_short_input(text):
    return [{
        "type": "user_input",
        "content": [{"type": "text", "text": text}]
    }]


async def ask_shiina(
    text: str,
    chat_id: str = None,
    user_id: str = None,
    username: str = None,
):
    global current_model

    from database import (
        add_message, get_history,
        get_last_interaction_id, save_interaction_id, clear_interaction_id,
        log_metric,
    )

    prev_id = None
    if chat_id and user_id:
        prev_id = get_last_interaction_id(str(chat_id), str(user_id))

    short_mode = bool(prev_id)

    if short_mode:
        input_steps = _build_short_input(text)
    else:
        history = []
        if chat_id and user_id:
            history = get_history(str(chat_id), str(user_id), limit=10)
        input_steps = _build_fresh_input(history, text)

    models_to_try = [
        current_model,
        *[model for model in MODELS if model != current_model]
    ]

    for model in models_to_try:
        start_time = time.time()
        mode_label = "short" if short_mode else "full"

        try:
            kwargs = {
                "model": model,
                "input": input_steps,
                "system_instruction": SYSTEM_PROMPT,
            }
            if short_mode:
                kwargs["previous_interaction_id"] = prev_id

            interaction = await asyncio.wait_for(
                client.aio.interactions.create(**kwargs),
                timeout=15
            )

            response_text = interaction.output_text
            duration_ms = int((time.time() - start_time) * 1000)

            current_model = model

            new_interaction_id = None
            try:
                new_interaction_id = getattr(interaction, "id", None)
                if not new_interaction_id:
                    new_interaction_id = getattr(interaction, "name", None)
            except Exception:
                pass

            if chat_id and user_id:
                add_message(str(chat_id), str(user_id), "user", text)
                add_message(str(chat_id), str(user_id), "model", response_text)

                if new_interaction_id:
                    save_interaction_id(str(chat_id), str(user_id), str(new_interaction_id))

                log_metric(
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    username=username,
                    event_type="ai_request",
                    text=text,
                    response=response_text,
                    model=model,
                    mode=mode_label,
                    duration_ms=duration_ms,
                )

            return response_text

        except asyncio.TimeoutError:
            if chat_id and user_id:
                log_metric(
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    username=username,
                    event_type="ai_error",
                    text=text,
                    response="timeout",
                    model=model,
                    mode=mode_label,
                )

        except errors.ServerError as e:
            if chat_id and user_id:
                log_metric(
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    username=username,
                    event_type="ai_error",
                    text=text,
                    response=str(e),
                    model=model,
                    mode=mode_label,
                )

        except Exception as e:
            error_str = str(e)

            if short_mode and ("previous_interaction_id" in error_str or "not found" in error_str.lower()):
                if chat_id and user_id:
                    clear_interaction_id(str(chat_id), str(user_id))
                history = get_history(str(chat_id), str(user_id), limit=10) if (chat_id and user_id) else []
                input_steps = _build_fresh_input(history, text)
                short_mode = False
                continue

            if chat_id and user_id:
                log_metric(
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    username=username,
                    event_type="ai_error",
                    text=text,
                    response=str(e),
                    model=model,
                    mode=mode_label,
                )

    return "🌸 Ой... я сейчас немного зависла. Попробуй ещё раз 😊"