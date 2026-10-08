from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InputRichMessage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select

import keyboards as kb
import info_table as it

router = Router()

ADMIN_IDS = [5020055582]

@router.message (F.photo)
async def photo_id(message: Message):
    await message.answer(f'{message.photo[-1].file_id}')


@router.message (CommandStart())
async def start(message: Message):
    await it.set_user(message.from_user.id)
    tg_id = message.from_user.id
    user_grade = await it.get_user_grade(tg_id=tg_id)
    if user_grade is not None:
        await message.answer_rich(rich_message=InputRichMessage(html=START))
        await message.answer_rich(rich_message=InputRichMessage(html=INFORMATION), reply_markup=kb.Main)
    else:    
        await message.answer_rich(rich_message=InputRichMessage(html=START + "<hr/>" + "\n<i>Але перед тим як почати, будь-ласка, оберіть свій клас</i>"), 
                                                                reply_markup=await kb.grades())
    
START = (
    f"<h1>Вас вітає Meccha Chameleon квест!</h1>"
    "<p>По усій школі заховані маленькі фігурки людей. Будьте першими хто знайде <b>кожну</b>!</p>"
)

@router.callback_query(F.data.startswith('grade_'))
async def grade(callback: CallbackQuery):
    grade_id = callback.data.split('_')[1]
    grade_data = await it.get_grade(grade_id)
    user_id = callback.from_user.id
    grade = grade_data.grade
    photo_id = await it.get_info_id(grade=grade)
    await it.set_grade(user_id=user_id, grade=grade)
    await callback.answer(f"Ви обрали {grade_data.grade} клас")
    await callback.message.delete()
    await callback.message.answer_rich(rich_message=InputRichMessage(html=f"\n✅ <b>Ви обрали {grade_data.grade} клас</b>"))
    await message.answer_photo(photo=f'{photo_id}',
                                caption=(
                                    f'<b>Доброго дня, {grade} клас!</b>\n'
                                    f'На фото ви бачите людинку, яку треба шукати <b>вам</b>.\n'
                                    f'<i>Люди, що мають інші аксесуари для інших класів. Будь ласка, не чіпайте їх. Адже за порушення цього правила на вас чекає 10хв штрафного часу.</i>'
                                ), 
                                parse_mode="HTML")
    await message.answer_rich(rich_message=InputRichMessage(html=INFORMATION), reply_markup=kb.Main)

INFORMATION = (
    "<h1>ℹ️ Info</h1>"
    "<hr/>"
    "<details>"
    "<summary>Де шукати людей?</summary>"
    "<p>Шукайте по кабінетах на першому поверсі! Людей немає в сховищі, в туалетах чи в коридорах.</p>"
    "</details>"
    "<details>"
    "<summary>В мене декілька завдань з різними відповідями!</summary>"
    "<p>Напишіть відповідь до кожного завдання послідовно, не переносячи відповіді на наступний рядок і не роблячи пробілів. Наприклад, в першому завданні у вас 5, в другому 7, а в третьому 2. До бота вам треба написати: 572.</p>"
    "</details>"
    "<details>"
    "<summary>В мене завдання з сірниками / кросворд / математичний лабіринт!</summary>"
    "<p>Повідомте вчителя, що перебуває в класі, про своє завдання. Учитель видасть вам реквізит (роздруківку або сірники). І після успішного розв’язку, повідомить код, що треба надіслати до бота.</p>"
    "</details>"
    "<details>"
    "<summary>Призи?</summary>"
    "<p>Лише найшвидші команди отримуюють призи! 1 місце - 3 зелених магніти кожному. 2 місце - 2 зелених магніти кожному. 3 місце - 1 зелений магніт кожному.</p>"
    "</details>"
)

@router.message(F.text == 'Трішки про квест.')
async def information(message: Message):
    tg_id = message.from_user.id
    grade = await it.get_user_grade(tg_id=tg_id)
    photo_id = await it.get_info_id(grade=grade)
    await message.answer_photo(photo=f'{photo_id}',
                                caption=(
                                    f'<b>Доброго дня, {grade} клас!</b>\n'
                                    f'На фото ви бачите людинку, яку треба шукати <b>вам</b>.\n'
                                    f'<i>Люди, що мають інші аксесуари для інших класів. Будь ласка, не чіпайте їх. Адже за порушення цього правила на вас чекає 10хв штрафного часу.</i>'
                                ), 
                                parse_mode="HTML")
    await message.answer_rich(rich_message=InputRichMessage(html=INFORMATION))

@router.message (F.text == 'Ми знайшли людинку!')
async def I_found_a_person(message: Message):
    tg_id = message.from_user.id
    grade = await it.get_user_grade(tg_id=tg_id)
    await message.answer_rich(rich_message=InputRichMessage(html=IFOUNDAPERSON), 
                            reply_markup=await kb.people(tg_id=tg_id, grade=grade))

IFOUNDAPERSON = (
    "<h1>ТАК ТРИМАТИ!</h1>"
    "<p><b>Відліпіть</b> людинку від її місця перебування. <b>З іншої сторони</b> людинки, яку ви знайшли, повинний бути <b>номер</b>. Будь-ласка, натисніть відповідну кнопку, що запроваджена нижче.</p>"
    "<tg-spoiler><i>(ви справді молодці)</i></tg-spoiler>"
)

class Reg(StatesGroup):
    person = State()
    answer = State()

@router.callback_query(F.data.startswith('person_'))
async def category(callback: CallbackQuery, state: FSMContext, bot: Bot):
    tg_id = callback.from_user.id
    data_parts = callback.data.split('_')
    person_id = int(data_parts[1])
    person_grade = data_parts[2]
    person_data_id = await it.get_person(person_id)
    person_data_grade = await it.get_user_grade(tg_id=tg_id)

    async with it.async_session() as session:
        user = await session.scalar(select(it.User).where(it.User.tg_id == tg_id))
    user_photo_status = getattr(user, f"photo{person_id}_id", None) if user else None
    
    if user_photo_status == "approved":
        await callback.answer('Цю людину ви вже знайшли і вирішили задачу до неї.', show_alert=True)
    elif user_photo_status == "task":
        await callback.answer('Цю людину ви вже знайшли. Залишилось лише виконати завдання!', show_alert=True)
    elif user_photo_status is not None:
        await callback.answer('Цю людину ви вже знайшли, почекайте доки адміністратори не затвердять або відхилять фото.', show_alert=True)
    else:
        await callback.answer(f'Ви обрали №{person_data_id.person}')
        await callback.message.edit_text(f'Вітаємо вас із знаходженням людини №{person_data_id.person}.\nБудь ласка, зробіть фотографію людини під цим номером і надішліть.',
                                        reply_markup=kb.BackFromPerson)
        await state.update_data(
            person_num=int(person_data_id.person),
            person_grade=person_grade,
            user_grade=person_data_grade
        )
        await state.set_state(Reg.person)

@router.message (Reg.person, F.photo)
async def reg_person(message:Message, state: FSMContext, bot: Bot):
    user_fsm_data = await state.get_data()
    person_number = user_fsm_data.get("person_num")
    person_grade = user_fsm_data.get("person_grade")
    user_grade = user_fsm_data.get("user_grade")
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    username = message.from_user.username
    grade = await it.get_user_grade(tg_id = user_id)
    await it.update_user_photo(grade=grade, photo_id=photo_id, person_number=person_number)
    await message.answer('Дякую! Фото надіслно до адміністраторів. Найближчим часом ваше фото затвердять.', reply_markup=kb.Main)
    admin_markup = await kb.admin_kb(user_id=user_id, person_number=person_number)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id, photo=photo_id,
                caption=(
                    f"Нове фото на перевірку!\n"
                    f"Відправник: {f'@{username}' if username else 'юзернейм приховано'} (ID: {user_id}).\n"
                    f"Клас відправника: {user_grade if user_grade else 'не вказано'}.\n"
                    f"Знайдена людина: №{person_number}."
                ),
                reply_markup= admin_markup
            )
        except Exception as e:
            print(f"Не вдалося надіслати сповіщення адміну {admin_id}: {e}")
    await state.clear()
    

@router.callback_query(F.data == 'backfromperson')
async def back_from_person(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    grade = await it.get_user_grade(tg_id=user_id)
    await state.set_state(None)
    await callback.answer('Повертаємося до списку номерків')
    await callback.message.delete()
    await callback.message.answer_rich(rich_message=InputRichMessage(html=IFOUNDAPERSON), 
                                        reply_markup=await kb.people(tg_id=user_id, grade=grade))

@router.callback_query(F.data.startswith('approvephoto_'))
async def approve_photo(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data_parts = callback.data.split('_')
    user_id = int(data_parts[1])
    person_number = int(data_parts[2])
    grade = await it.get_user_grade(tg_id=user_id)
    task_data = await it.get_task_photo_id(grade=grade, task_number=person_number)
    photo_id = task_data.task_id
    task_answer = task_data.task_answer
    
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n✅ <b>ЗАТВЕРДЖЕНО (Кнопки видалено)</b>",
            parse_mode="HTML"
        )
        await callback.message.delete_reply_markup()
    except TelegramBadRequest:
        pass

    await bot.send_message(
        chat_id=user_id,
        text=f"✅ Фото з людиною №{person_number}, що ви надіслали, було затверджено."
    )
    await callback.answer("Успішно затверджено!")

    await bot.send_photo(
        chat_id=user_id, photo=photo_id, 
        caption=(
            f"Згідно зі статтею 307 цивільного кодексу України фотографування людини без її дозволу карається законом.\n"
            f"<b>Але людинка №{person_number} готова вас пробачити якщо ви допоможете їй розв'язати задачку на фото!</b>\n\n"
            f"<i>Відповідь надішліть боту. Не використовуйте ніякі символи окрім цифер.</i>"
        ), 
        parse_mode="HTML"
    )
    
    await it.update_user_photo_task(grade = grade, person_number = person_number)
    await it.set_waiting_answer(user_id=user_id, correct_answer=task_answer, person_number=person_number)
    await state.set_state(Reg.answer)

@router.callback_query(F.data.startswith('reject_'))
async def approve_photo(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split('_')
    user_id = int(data_parts[1])
    person_number = int(data_parts[2])

    reasons_kb = kb.get_reasons_keyboard(user_id=user_id, person_number=person_number)

    await callback.message.edit_reply_markup(reply_markup=reasons_kb)
    await callback.answer("Оберіть причину відмови")

@router.callback_query(F.data.startswith('reason_'))
async def reject_photo_final(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split('_')
    user_id = int(data_parts[1])
    person_number = int(data_parts[2])
    reason_type = data_parts[3]
    grade = await it.get_user_grade(tg_id=user_id)

    if reason_type == "blur":
        reason_text = "фото занадто розмите або неякісне. Спробуйте зробити більш чіткий знімок."
    elif reason_type == "wrong":
        reason_text = "номер біля людини не збігається з обраним вами номером кнопки."
    elif reason_type == "nograde":
        reason_text = "ви не позначили, в якому класі навчаєтеся."
    else:
        reason_text = "на фотографії не видно людину під цим номером."

    await it.update_user_photo_reject(grade=grade, person_number=person_number)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>Фото з людиною №{person_number} було відхилено.</b>\n\n"
                f"📝 <b>Причина відмови:</b> {reason_text}\n\n"
                f"Будь ласка, врахуйте зауваження та надішліть фото знову!"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Помилка відправки користувачу: {e}")
        
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n❌ <b>ВІДХИЛЕНО (Причина: {reason_text})</b>",
            parse_mode="HTML"
        )
        await callback.message.delete_reply_markup()
    except TelegramBadRequest:
        pass
        
    await callback.answer("Сповіщення надіслано гравцю!")

@router.callback_query(F.data.startswith('approveback_'))
async def approve_back(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split('_')
    user_id = int(data_parts[1])
    person_number = int(data_parts[2])
    await callback.message.edit_reply_markup(reply_markup=await kb.admin_kb(user_id=user_id, person_number=person_number))
    await callback.answer('Назад')

@router.message (Reg.answer, F.text)
async def reg_answer(message:Message, state: FSMContext, bot: Bot):
    user_answer = message.text.strip()
    user_id = message.from_user.id
    grade = await it.get_user_grade(tg_id=user_id)
    task_data = await it.get_waiting_answer(tg_id=user_id)
    if await it.get_waiting_answer(tg_id=user_id) is None:
        return
    correct_answer = task_data.task_answer
    person_number = task_data.person_number

    if await it.get_waiting_answer(tg_id=user_id) is None:
        return

    if correct_answer == user_answer:
        await message.answer('✅ Все вірно!', reply_markup = kb.Main)
        users_in_grade = await it.get_users_by_grade(grade=grade)
        for user in users_in_grade:
            try:
                await bot.send_message(    
                    chat_id=user.tg_id,
                    text=f"Молодці, людинка №{person_number} зарахована як знайдена!"
                )
            except Exception as e:
                print(f"Не вдалося надіслати повідомлення юзеру {user.tg_id}: {e}")
        
        await it.update_user_photo_approve(grade=grade, person_number=person_number)
        if await it.all_done(user_id=user_id): 
            for user in users_in_grade:
                try:
                    await bot.send_rich_message(    
                        chat_id=user.tg_id,
                        rich_message=InputRichMessage(html=FINISH)
                    )
                except Exception as e:
                    print(f"Не вдалося надіслати повідомлення юзеру {user.tg_id}: {e}")
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=(f"✅ {grade} клас закінчив усі свої завдання.")
                    )
                except Exception as e:
                    print(f"Не вдалося надіслати повідомлення адміністратору {admin_id}: {e}")
        await state.clear()
        await it.none_waiting_answer(user_id=user_id)
    else:
        await message.answer('❌ Відповідь, що ви надіслали не є вірною. Перевірте свої розрахунки та спробуйте надіслати іншу відповідь.')

FINISH = (
    "🎉 <h1>ВІТАЄМО! Ваш клас знайшов абсолютно всіх людей і повністю пройшов квест!</h1>"
    "<i>Сподіваємося вам було весело! Дякую що пройшли наш міні-квест, ми дуже раді.</i>"
)

