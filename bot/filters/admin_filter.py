from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config.config import ADMIN_IDS

class AdminFilter(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Проверка, что событие - это сообщение или callback и у него есть from_user
        if isinstance(event, (Message, CallbackQuery)) and event.from_user.id not in ADMIN_IDS:
            if isinstance(event, Message):
                await event.answer("You are not authorized to use this bot.")
            elif isinstance(event, CallbackQuery):
                await event.answer("You are not authorized to use this bot.", show_alert=True)
            return
        return await handler(event, data)

def is_admin(func):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id in ADMIN_IDS:
            return await func(message, *args, **kwargs)
        await message.answer("You are not authorized to use this command.")
    return wrapper
