from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.menus.main_menu import main_menu  # Главное меню
from bot.filters.admin_filter import is_admin  # Фильтр для админов

# Создаем маршрутизатор для команды /start
router = Router()

# Обработчик команды /start
@router.message(CommandStart())
@is_admin
async def start_command_handler(message: Message, **kwargs):
    await message.answer("Привет! Это меню ноды. Выберите действие:", reply_markup=main_menu())
