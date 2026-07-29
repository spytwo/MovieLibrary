import asyncio
import os
from typing import Any, Dict, List, Optional

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def fetch_json(session: aiohttp.ClientSession, url: str) -> Any:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    await message.answer("Film:")


@dp.message(Command("genres"))
async def cmd_genres(message: types.Message):
    url = f"{API_BASE_URL}/api/filters/genres/"
    async with aiohttp.ClientSession() as session:
        try:
            genres_data: List[str] = await fetch_json(session, url)
        except Exception as e:
            await message.answer(f"Couldn't get genres: {e}")
            return

    if not genres_data:
        await message.answer("Genres not found")
        return

    buttons = [
        [types.InlineKeyboardButton(text=genre, callback_data=f"genre_{genre}")]
        for genre in genres_data
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Choose a genre:", reply_markup=markup)


@dp.callback_query(F.data.startswith("genre_"))
async def handle_genre_callback(call: types.CallbackQuery):
    data = call.data.replace("genre_", "")

    if "|" in data:
        genre, offset_str = data.split("|", 1)
        try:
            offset = int(offset_str)
        except ValueError:
            offset = 0
    else:
        genre = data
        offset = 0

    url = f"{API_BASE_URL}/api/filters/genres/{genre}"
    async with aiohttp.ClientSession() as session:
        try:
            films: List[Dict[str, Any]] = await fetch_json(session, url)
        except Exception as e:
            await call.message.answer(f"Couldn't get genre films {genre}: {e}")
            await call.answer()
            return

    await call.answer()

    if not films:
        await call.message.answer(
            f"Movies of the genre *{genre}* not found", parse_mode="Markdown"
        )
        return

    if offset == 0:
        await call.message.answer(
            f"Movies of the genre *{genre}*:", parse_mode="Markdown"
        )

    films_slice = films[offset : offset + 5]

    for film in films_slice:
        title = film.get("title", "Untitled")
        film_id = film.get("id")

        details_markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="More detailed", callback_data=f"film_{film_id}"
                    )
                ]
            ]
        )
        await call.message.answer(f"🎬 {title}", reply_markup=details_markup)

    next_offset = offset + 5
    if next_offset < len(films):
        more_markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="More", callback_data=f"genre_{genre}|{next_offset}"
                    )
                ]
            ]
        )
        await call.message.answer("🍿", reply_markup=more_markup)


@dp.message(F.text & ~F.via_bot)
async def handle_text(message: types.Message):
    query = (message.text or "").strip()
    if not query:
        return

    url = f"{API_BASE_URL}/api/films/search?q={query}"
    async with aiohttp.ClientSession() as session:
        try:
            films: List[Dict[str, Any]] = await fetch_json(session, url)
        except Exception as e:
            await message.answer(f"Couldn't complete the search: {e}")
            return

    if not films:
        await message.answer("Nothing was found")
        return

    for film in films:
        title = film.get("title", "Untitled")
        film_id = film.get("id")
        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="More detailed", callback_data=f"film_{film_id}"
                    )
                ]
            ]
        )
        await message.answer(f"🎬 {title}", reply_markup=markup)


@dp.callback_query(F.data.startswith("film_"))
async def handle_film_details(call: types.CallbackQuery):
    film_id = call.data.split("_", 1)[1]
    url = f"{API_BASE_URL}/api/films/{film_id}"

    async with aiohttp.ClientSession() as session:
        try:
            film_data: Dict[str, Optional[Any]] = await fetch_json(session, url)
        except Exception as e:
            await call.message.answer(f"Couldn't get information about the movie: {e}")
            await call.answer()
            return

    title = film_data.get("title") or "Untitled"
    year = film_data.get("year") or "—"
    rating = film_data.get("rating") or "—"
    description = film_data.get("description") or "The description is missing"

    message_text = (
        f"🎞 <b>{title}</b>\n\n"
        f"🗓️ Year: {year}\n"
        f"🌟 Rating: {rating}\n"
        f"📖 Description: {description}"
    )

    await call.message.answer(message_text, parse_mode="HTML")
    await call.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
