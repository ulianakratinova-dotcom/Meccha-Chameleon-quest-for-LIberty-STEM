from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import info_table as it
from sqlalchemy import select

async def grades():
    all_grades = await it.get_grades()
    keyboard = InlineKeyboardBuilder()
    for grade in all_grades:
        keyboard.add(InlineKeyboardButton(text=grade.grade, callback_data=f"grade_{grade.id}"))
    return keyboard.adjust(3).as_markup()

Main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Ми знайшли людинку!')],
    [KeyboardButton(text='Трішки про квест.')]
],
    resize_keyboard=True,
    input_field_placeholder='оберіть пункт панельки.')

async def people(tg_id: int, grade: str) -> InlineKeyboardMarkup:
    async with it.async_session() as session:
        user = await session.scalar(select(it.User).where(it.User.tg_id == tg_id))
        result = await session.scalars(select(it.Person))
        all_people = result.all()
    
    builder = InlineKeyboardBuilder()
    
    for p in all_people:
        p_num = p.person
        user_photo_status = getattr(user, f"photo{p_num}_id", None) if user else None

        if user_photo_status == "approved":
            button_text = f"№{p.person} ✅"
        elif user_photo_status == "task":
            button_text = f"№{p.person} 🔢"
        elif user_photo_status is not None:
            button_text = f"№{p.person} ⏳"
        else:
            button_text = f"№{p.person}"
    
        builder.add(InlineKeyboardButton(text=button_text, callback_data=f"person_{p.id}_{grade}"))
    
    builder.adjust(3)
    return builder.as_markup()

BackFromPerson = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = '<- Назад', callback_data='backfromperson')]
])

async def admin_kb(user_id: int, person_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Затвердити", callback_data=f"approvephoto_{user_id}_{person_number}"),
            InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{user_id}_{person_number}")
        ]
    ])

def get_reasons_keyboard(user_id: int, person_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Розмите фото", callback_data=f"reason_{user_id}_{person_number}_blur"),
            InlineKeyboardButton(text="🔢 Не той номер", callback_data=f"reason_{user_id}_{person_number}_wrong")
        ],
        [
            InlineKeyboardButton(text="👤 Немає людини на фото", callback_data=f"reason_{user_id}_{person_number}_nobody"),
            InlineKeyboardButton(text="🏫 Не зареєстрований клас", callback_data=f"reason_{user_id}_{person_number}_nograde")
        ],
        [
            InlineKeyboardButton(text="⬅️ Скасувати (назад)", callback_data=f"approveback_{user_id}_{person_number}") 
        ]
    ])