import asyncio
import os
from typing import Any, Dict, List, Optional

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

bot = Bot(token=TOKEN)
dp = Dispatcher()


class GenreCB(CallbackData, prefix="genre"):
    name: str
    page: int = 1


class FilmCB(CallbackData, prefix="film"):
    id: int | str


async def fetch_json(
    session: aiohttp.ClientSession, url: str, params: Optional[Dict[str, Any]] = None
) -> Any:
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    await message.answer("Введите название фильма для поиска:")


@dp.message(Command("genres"))
async def cmd_genres(message: types.Message, http_session: aiohttp.ClientSession):
    url = f"{API_BASE_URL}/api/genres/"
    try:
        genres_data: List[str] = await fetch_json(http_session, url)
    except Exception as e:
        await message.answer(f"Не удалось получить жанры: {e}")
        return

    if not genres_data:
        await message.answer("Жанры не найдены")
        return

    buttons = [
        [
            types.InlineKeyboardButton(
                text=genre, callback_data=GenreCB(name=genre, page=1).pack()
            )
        ]
        for genre in genres_data
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите жанр:", reply_markup=markup)


@dp.callback_query(GenreCB.filter())
async def handle_genre_callback(
    call: types.CallbackQuery,
    callback_data: GenreCB,
    http_session: aiohttp.ClientSession,
):
    genre = callback_data.name
    page = callback_data.page
    page_size = 5

    url = f"{API_BASE_URL}/api/films"
    params = {"genre": genre, "page": page, "page_size": page_size}

    try:
        films: List[Dict[str, Any]] = await fetch_json(http_session, url, params=params)
    except Exception as e:
        await call.message.answer(f"Не удалось получить фильмы жанра {genre}: {e}")
        await call.answer()
        return

    await call.answer()

    if not films and page == 1:
        await call.message.answer(
            f"Фильмы жанра *{genre}* не найдены", parse_mode="Markdown"
        )
        return

    if page == 1:
        await call.message.answer(
            f"Фильмы жанра *{genre}* (Страница {page}):", parse_mode="Markdown"
        )

    for film in films:
        title = film.get("title", "Без названия")
        film_id = film.get("id")

        details_markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Подробнее",
                        callback_data=FilmCB(id=film_id).pack(),
                    )
                ]
            ]
        )
        await call.message.answer(f"🎬 {title}", reply_markup=details_markup)

    if len(films) == page_size:
        more_markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Ещё 🍿",
                        callback_data=GenreCB(name=genre, page=page + 1).pack(),
                    )
                ]
            ]
        )
        await call.message.answer(
            "Загрузить следующие фильмы:", reply_markup=more_markup
        )


@dp.message(F.text & ~F.via_bot)
async def handle_text(message: types.Message, http_session: aiohttp.ClientSession):
    query = (message.text or "").strip()
    if not query:
        return

    if len(query) < 3:
        await message.answer("Запрос должен содержать минимум 3 символа.")
        return

    url = f"{API_BASE_URL}/api/films"
    try:
        films: List[Dict[str, Any]] = await fetch_json(
            http_session, url, params={"q": query}
        )
    except Exception as e:
        await message.answer(f"Не удалось выполнить поиск: {e}")
        return

    if not films:
        await message.answer("Ничего не найдено")
        return

    for film in films:
        title = film.get("title", "Без названия")
        film_id = film.get("id")
        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Подробнее",
                        callback_data=FilmCB(id=film_id).pack(),
                    )
                ]
            ]
        )
        await message.answer(f"🎬 {title}", reply_markup=markup)


@dp.callback_query(FilmCB.filter())
async def handle_film_details(
    call: types.CallbackQuery,
    callback_data: FilmCB,
    http_session: aiohttp.ClientSession,
):
    film_id = callback_data.id
    url = f"{API_BASE_URL}/api/films/{film_id}"

    try:
        film_data: Dict[str, Optional[Any]] = await fetch_json(http_session, url)
    except Exception as e:
        await call.message.answer(f"Не удалось получить информацию о фильме: {e}")
        await call.answer()
        return

    title = film_data.get("title") or "Без названия"
    year = film_data.get("year") or "—"
    rating = film_data.get("rating") or "—"
    description = film_data.get("description") or "Описание отсутствует"

    message_text = (
        f"🎞 <b>{title}</b>\n\n"
        f"🗓️ Год: {year}\n"
        f"🌟 Рейтинг: {rating}\n"
        f"📖 Описание: {description}"
    )

    await call.message.answer(message_text, parse_mode="HTML")
    await call.answer()


async def main():
    async with aiohttp.ClientSession() as session:
        dp["http_session"] = session
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
