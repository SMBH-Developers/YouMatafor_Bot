import asyncio
import random
import logging

from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram import executor, types, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import markdown

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from pathlib import Path

from texts import Texts, dict_daily_bonuses
from keyboards import Markups
from bf_texts import bf_sending, SendingData
from src.common import settings
from src.models import db, db_sendings

from data.skip_100_lead import skip_100_leads


storage = RedisStorage2(db=settings.redis_db, pool_size=40)
bot = Bot(settings.tg_token)
dp = Dispatcher(bot, storage=storage)
ADMIN_IDS = (1371617744, 791363343)
markups = Markups()
daily_cards_photos = \
    [
        Path("data/photos/daily_cards_photos/card0.JPG"),
        Path("data/photos/daily_cards_photos/card1.JPG"),
        Path("data/photos/daily_cards_photos/card2.JPG"),
        Path("data/photos/daily_cards_photos/card3.JPG"),
        Path("data/photos/daily_cards_photos/card4.JPG"),
        Path("data/photos/daily_cards_photos/card5.JPG")
    ]

class States(StatesGroup):
    name = State()


async def get_photo_id(path: Path) -> str | types.InputFile:
    photo_id = await db.get_photo_id(path)
    if photo_id is None:
        photo_id = types.InputFile(path)
    return photo_id


@dp.message_handler(commands=['start'], state='*')
@logger.catch
async def send_welcome(message: types.Message, state: FSMContext):
    """Стартовая команда"""
    path_photo = Path("data/photos/start_photo.png")
    photo = await get_photo_id(path=path_photo)
    msg = await message.answer_photo(photo, Texts.start_text, reply_markup=Markups.mrkup_to_metaphorical_analysis)

    await db.registrate_if_not_exists(message.from_user.id)
    if isinstance(photo, types.InputFile):
        await db.register_photo(path_photo, msg.photo[0].file_id)

@dp.message_handler(lambda message: message.from_user.id in ADMIN_IDS, state='*', commands=['admin'])
async def admin_menu(message: types.Message, state: FSMContext) -> None:
    await bot.send_message(message.chat.id, text='Выберите действие', reply_markup=markups.admin_mrkup)


@dp.callback_query_handler(lambda call: call.from_user.id in ADMIN_IDS and call.data.startswith('Admin'), state='*')
async def admin_calls(call: types.CallbackQuery, state: FSMContext) -> None:
    action = '_'.join(call.data.split('_')[1:])
    if action == 'Users_Total':
        await call.message.edit_text(text=f'Пользователей всего: {await db.get_count_all_users()}',
                                     reply_markup=markups.back_admin_mrkup)

    elif action == 'Users_For_TODAY':
        await call.message.edit_text(text=f'Пользователей за сегодня: {await db.users_for_today()}',
                                     reply_markup=markups.back_admin_mrkup)

    elif action == 'BACK':
        await call.message.edit_text(text='Выберите действие', reply_markup=markups.admin_mrkup)


@dp.message_handler(lambda message: message.text in Texts.menu_texts.keys(), state='*')
async def send_analysis_message(message: types.Message, state: FSMContext):
    menu_item = Texts.menu_texts[message.text]
    if message.text == "🔮Ежедневный разбор":
        markup = types.ReplyKeyboardRemove()
    else:
        markup = Markups.to_menu_markup
    photo = await get_photo_id(menu_item.photo)
    msg = await message.answer_photo(photo, menu_item.text, reply_markup=markup)
    if isinstance(photo, types.InputFile):
        await db.register_photo(menu_item.photo, msg.photo[0].file_id)

    if message.text == "🔮Ежедневный разбор":
        asyncio.create_task(sending_cards(message))


@dp.message_handler(lambda message: message.text == '🎁Ежедневный бонус', state='*')
async def daily_bonus(message: types.Message, state: FSMContext):
    await message.answer(Texts.daily_bonus_text, reply_markup=Markups.daily_bonus_mrkup)


@dp.message_handler(lambda message: message.text == 'Получить бесплатную консультацию эксперта', state='*')
async def menu_metaphorical_analysis(message: types.Message, state: FSMContext):
    await message.answer("Очень рада, что Вы хотите разобраться в вопросе. Кстати, какую сферу хотелось бы разобрать:",
                         reply_markup=markups.mrkup_to_metaphorical_analysis)


# @dp.callback_query_handler(lambda query: query.data in ['category:finance', 'category:implementation', 'category:relationships', 'category:other', 'category:health'], state='*')
# async def after_menu_metaphorical_analysis(callback_query: types.CallbackQuery, state: FSMContext):
#     await callback_query.message.answer("Отлично, это наиболее популярный запрос! С удовольствием помогу. Как могу к Вам обращаться?",
#                          reply_markup=Markups.to_menu_markup)
#     await state.set_state(States.name.state)


@dp.callback_query_handler(lambda query: query.data in ['category:finance', 'category:implementation', 'category:relationships', 'category:other', 'category:health'], state='*')
async def set_number_metaphorical_analysis(callback_query: types.CallbackQuery, state: FSMContext):
    number = random.randint(10000, 100000)
    path = Path("data/photos/metaphorical_analysis.png")
    photo_id = await get_photo_id(path)
    msg = await callback_query.message.answer_photo(photo_id,
                                     f"Напишете пожалуйста вашу дату рождения в формате дд.мм.гггг мне в личные сообщения @spiriti_guide 👈, чтобы получить бесплатный расклад",
                                     reply_markup=Markups.to_menu_markup)
    if isinstance(photo_id, types.InputFile):
        await db.register_photo(path, msg["photo"][0]["file_id"])
    await state.finish()


@dp.message_handler(lambda message: message.text == "❤️Карта дня", state='*')
async def daily_card(message: types.Message, state: FSMContext):
    await message.answer(Texts.daily_card_text, reply_markup=types.ReplyKeyboardRemove())
    asyncio.create_task(send_card_day(message))


async def send_card_day(message: types.Message):
    await asyncio.sleep(2.7)
    user_step = await db.get_daily_card_step(message.from_user.id)
    photo = daily_cards_photos[user_step]
    if isinstance(photo, str):
        await message.answer_photo(photo, reply_markup=Markups.to_menu_markup)
    else:
        with photo.open('rb') as f:
            msg = await message.answer_photo(f, reply_markup=Markups.to_menu_markup)
        daily_cards_photos[user_step] = msg.photo[-1].file_id


@dp.message_handler(lambda message: message.text == '🧿Аффирмация дня', state='*')
async def daily_affirmation(message: types.Message, state: FSMContext):
    await message.answer(Texts.daily_affirmation[await db.get_daily_affirmation_step(message.from_user.id)], reply_markup=Markups.to_menu_markup)


@dp.message_handler(lambda message: message.text == '📝Чек-лист', state='*')
async def check_lists_menu(message: types.Message, state: FSMContext):
    daily_bonus_step = await db.get_day_bonus_step(message.from_user.id)
    await message.answer(Texts.generate_day_bonus_text(daily_bonus_step), reply_markup=Markups.generate_daily_bonus_mrkup(daily_bonus_step))


@dp.message_handler(lambda message: message.text in dict_daily_bonuses, state='*')
async def show_daily_bonus(message: types.Message, state: FSMContext):
    daily_bonus = dict_daily_bonuses[message.text]  # check-list file
    if isinstance(daily_bonus.file, Path):
        with daily_bonus.file.open('rb') as check_list_file:
            bot_msg = await message.answer_document(check_list_file, caption=daily_bonus.text, reply_markup=Markups.to_menu_markup)
        daily_bonus.file = bot_msg.document.file_id
    else:
        await message.answer_document(daily_bonus.file, caption=daily_bonus.text, reply_markup=Markups.to_menu_markup)


async def sending_cards(message: types.Message):
    for index_card, card in enumerate(Texts.card_on_day):
        if index_card == len(Texts.card_on_day)-1:
            mrkup = Markups.choose_card_markup
        else:
            mrkup = None
        await asyncio.sleep(1.5)
        photo = await get_photo_id(card.photo)
        msg = await message.answer_photo(photo, card.name, reply_markup=mrkup)
        if isinstance(photo, types.InputFile):
            await db.register_photo(card.photo, msg.photo[0].file_id)


@dp.message_handler(lambda message: message.text.startswith('Карта ') and not message.text.endswith("дня"), state="*")
async def message_items(message: types.Message, state: FSMContext):
    card_step = int(message.text.split()[1])-1
    meta_card = Texts.card_on_day[int(card_step)]
    card_text = random.choice(Texts.card_texts)
    photo = await get_photo_id(meta_card.photo)
    msg = await message.answer_photo(photo, card_text, reply_markup=Markups.to_menu_markup)
    if isinstance(photo, types.InputFile):
        await db.register_photo(meta_card.photo, msg.photo[0].file_id)
    asyncio.create_task(send_late_thanks(message, meta_card.late_thanks_text))


async def send_late_thanks(message: types.Message, text: str):
    await asyncio.sleep(4.5)
    await message.answer(f"💫Только сегодня специалист Мари готова сделать Вам бесплатный персональный метафорический разбор по Вашей дате рождения!\n\nДля получения достаточно отправить дату своего рождения в личные сообщения Мари — @spiriti_guide 👈", reply_markup=Markups.to_our_account)


@dp.message_handler(lambda message: message.text == "👈Обратно", state="*")
async def message_items(message: types.Message, state: FSMContext):
    path_photo = Path("data/photos/start_photo.png")
    photo = await get_photo_id(path=path_photo)
    msg = await message.answer_photo(photo, Texts.start_text, reply_markup=Markups.menu_markup)

    await db.registrate_if_not_exists(message.from_user.id)
    if isinstance(photo, types.InputFile):
        await db.register_photo(path_photo, msg.photo[0].file_id)



async def sending_messages_2h():
    while True:
        try:
            await asyncio.sleep(7)
            path = Path("data/photos/sending_photos/2_h.png")
            photo_id = await get_photo_id(path)

            text_for_2h_autosending = f'{markdown.hbold("Здравствуйте!")}\n\nОчень рада с вами познакомиться😊 Я Мари  - дипломированный энергокоуч по метафорическим разборам с опытом более 5 лет.\n\n⭐ В честь знакомства хочу предложить Вам первую {markdown.hbold("бесплатную консультацию!")}\n\n❗На ней Вы сможете найти свои подсознательные {markdown.hbold("причины проблем")} и поведения с помощью метафорических ассоциативных карт. Эта методика позволяет {markdown.hbold("найти ответы и решения по любому вопросу")} — от отношений в семье до финансов😎.\n\n😉 Не упустите шанс изменить свою жизнь к лучшему уже сегодня!\n\nПросто напишите мне в личные сообщения слово "Разбор" и мы сразу же приступим!\nЖду Вас — @spiriti_guide 👈'
            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton('Получить РАЗБОР ⚡', url=f'https://t.me/spiriti_guide'))

            users = await db_sendings.get_users_2h_autosending()
            for user in users:
                try:
                    msg = await bot.send_photo(user, photo=photo_id, caption=text_for_2h_autosending, parse_mode='html', reply_markup=mrkup)
                    if isinstance(photo_id, types.InputFile):
                        await db.register_photo(path, msg["photo"][0]["file_id"])
                    logger.info(f'ID: {user}. Got 2h_autosending')
                    await db_sendings.mark_got_2h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            logger.error(ex)
            await bot.send_message(1371617744, f'Happened: {ex}')


async def sending_message_24_h():
    while True:
        try:
            await asyncio.sleep(12)
            path = Path("data/photos/sending_photos/24_h.png")
            photo_id = await get_photo_id(path)

            text_autosending_24h = f'Сегодня мощные энергетически лунные сутки, когда {markdown.hbold("легко можно улучшить судьбу")} 🌕\n\nВ такие дни я стараюсь помочь большему количеству людей, но успею принять лишь {markdown.hbold("9 человек на бесплатную трансформацию")} любой сферы жизни, которую хотелось бы улучшить!\n\n❗️Не упустите  этот знак Вселенной - возможно, именно он станет ключевым в Вашей жизни 😉\n\nПиши прямо сейчас мне в личные сообщения @spiriti_guide слово {markdown.hbold("Разбор")} 👇'
            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton('✨ РАЗБОР ✨', url=f'https://t.me/spiriti_guide'))

            users = await db_sendings.get_users_24h_autosending()
            for user in users:
                try:
                    msg = await bot.send_photo(user, photo=photo_id, caption=text_autosending_24h, parse_mode='html', reply_markup=mrkup)
                    if isinstance(photo_id, types.InputFile):
                        await db.register_photo(path, msg["photo"][0]["file_id"])
                    logger.info(f'ID: {user}. Got autosending_24h')
                    await db_sendings.mark_got_24h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            logger.error(ex)
            await bot.send_message(1371617744, f'Happened: {ex}')

async def sending_message_48_h():
    while True:
        try:
            await asyncio.sleep(12)
            path = Path("data/photos/sending_photos/48_h.png")
            photo_id = await get_photo_id(path)

            text_autosending_48h = f'{markdown.hbold("Ответы внутри Вас")}💖\n\nМы не меняем ничего в своей жизни, просто потому, что боимся неизвестности😞. Благодаря метафорическим картам вы сможете построить {markdown.hbold("желаемый сценарий жизни")} и прийти к нему. 🤩 {markdown.hbold("Ведь правильные ответы есть внутри Вас!")}\n\nСегодня АКЦИЯ на разборы, на которых составляю стратегию роста в сфере денег и реализации на ближайшие 5 лет! Помимо этого мы с Вами исправим и текущие проблемы в сферах {markdown.hbold("проявленности и самореализации.")}\n\n❗️Возьму {markdown.hbold("бесплатно")} первых 5 счастливчиков! Надеюсь тебе повезет 😉\n\nПиши скорей в личку слово {markdown.hbold("РАЗБОР")} @spiriti_guide 👈'
            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton('⚡️ БЕСПЛАТНЫЙ РАЗБОР ⚡️', url=f'https://t.me/spiriti_guide'))

            users_for_autosending_1 = await db_sendings.get_users_48h_autosending()
            for user in users_for_autosending_1:
                try:
                    msg = await bot.send_photo(user, photo=photo_id, caption=text_autosending_48h, parse_mode='html', reply_markup=mrkup)
                    if isinstance(photo_id, types.InputFile):
                        await db.register_photo(path, msg["photo"][0]["file_id"])
                    logger.info(f'ID: {user}. Got autosending_text_48h')
                    await db_sendings.mark_got_48h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            logger.error(ex)
            await bot.send_message(1371617744, f'Happened: {ex}')


async def bf_task(id_: int, sending: SendingData, db_func, skip_if_chat_member: bool = False, only_for_chat_member: bool = False):
    try:

        if skip_if_chat_member or only_for_chat_member:
            chat_member = await bot.get_chat_member(-1002059782974, id_)
            if chat_member.is_chat_member() and skip_if_chat_member:
                return 'skip'
            elif not chat_member.is_chat_member() and only_for_chat_member:
                return 'skip'
            name = chat_member.user.first_name
        else:
            name = None

        if id_ in skip_100_leads:
            return 'skip'

        text = await sending.get_text(bot, id_, name)
        if sending.photo is not None:
            await bot.send_photo(id_, types.InputFile(sending.photo), caption=text, reply_markup=sending.kb,
                                 parse_mode='html', disable_notification=True)
        else:
            await bot.send_message(id_, text=text, reply_markup=sending.kb,
                                   parse_mode='html', disable_web_page_preview=True)
        await db_func(id_)
        sending.count += 1
        logger.success(f'{id_} sending_{sending.uid} text')

    except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound):
        logger.exception(f'ID: {id_}. DELETED')
        await db.delete_user(id_)
    except Exception as e:
        logger.error(f'BUG: {e}')
    else:
        return 'success'
    return 'false'


async def sending_newsletter():
    white_day = 30
    now_time = datetime.now()

    if now_time.day > white_day:
        return

    while True:
        await asyncio.sleep(2)
        if now_time.day == white_day and now_time.hour >= 15:
            try:
                tasks = []
                users = [1371617744] + list(await db_sendings.get_users_for_sending_newsletter_by_date())
                print(len(users))
                for user in users:
                    logger.info(f"Пытаюсь отправить сообщение рассылки - {user}")
                    try:
                        _s = bf_sending
                        # if _s.count >= 80000:
                        #     break
                        tasks.append(asyncio.create_task(bf_task(user, _s, db_sendings.set_newsletter)))
                        if len(tasks) > 40:
                            print(len(tasks))
                            r = await asyncio.gather(*tasks, return_exceptions=False)
                            await asyncio.wait(tasks)
                            await asyncio.sleep(0.4)
                            logger.info(f"{r.count('success')=}", f"{r.count('false')=}", f"{r.count('skip')=}")
                            tasks.clear()

                    except Exception as ex:
                        logger.error(f'Ошибка в малом блоке sending: {ex}')
                    finally:
                        await asyncio.sleep(0.03)
            except Exception as ex:
                logger.error(f"Ошибка в большом блоке sending - {ex}")
            finally:
                await bot.send_message(1371617744, f"ERROR Рассылка стопнулась.")
                logger.info("Рассылка завершилась")


async def on_startup(_):
    #asyncio.create_task(sending_newsletter())
    asyncio.create_task(sending_messages_2h())
    asyncio.create_task(sending_message_24_h())
    asyncio.create_task(sending_message_48_h())


try:
    a_logger = logging.getLogger('apscheduler.scheduler')
    a_logger.setLevel(logging.DEBUG)
    scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
    scheduler.add_job(trigger='cron', hour='00', minute='00', func=db.update_users_daily_steps)
    scheduler.start()
    executor.start_polling(dp, on_startup=on_startup)
finally:
    stop = True
