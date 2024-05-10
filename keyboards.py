import json

from itertools import islice


from aiogram.types.reply_keyboard import ReplyKeyboardMarkup
from aiogram import types
from texts import Texts


class Markups:

    @staticmethod
    def chunk(it, size):
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    @staticmethod
    def get_titles_from_kb(kb):
        titles = []
        if isinstance(kb, types.ReplyKeyboardMarkup):
            json_kb = json.loads(kb.as_json())['keyboard']
            for row in json_kb:
                for btn in row:
                    titles.append(btn['text'])
        elif isinstance(kb, types.InlineKeyboardMarkup):
            for row in kb.inline_keyboard:
                for button in row:
                    titles.append(button.text)
        return titles

    @staticmethod
    def generate_daily_bonus_mrkup(day: int):
        """

        :param day: must be in range(0,3)
        :return:
        """
        available_bonuses = \
            ['📝Получить чек-лист "10 советов по отношениям"',
             '📝Получить чек-лист "Здоровая жизнь"',
             '📝Получить чек-лист "Обретение гармонии"'
             ]
        mrkup = ReplyKeyboardMarkup(resize_keyboard=True)
        mrkup.add(available_bonuses[day])
        mrkup.add("👈Обратно")
        return mrkup

    admin_mrkup = types.InlineKeyboardMarkup()
    admin_mrkup.add(types.InlineKeyboardButton(text='Пользователей всего', callback_data='Admin_Users_Total'))
    admin_mrkup.add(types.InlineKeyboardButton(text='Пользователей за сегодня', callback_data='Admin_Users_For_TODAY'))

    back_admin_mrkup = types.InlineKeyboardMarkup()
    back_admin_mrkup.add(types.InlineKeyboardButton(text='⬅️ В меню админа', callback_data='Admin_BACK'))

    daily_bonus_mrkup = ReplyKeyboardMarkup(resize_keyboard=True)
    daily_bonus_mrkup.add("❤️Карта дня")
    daily_bonus_mrkup.add("🧿Аффирмация дня")
    daily_bonus_mrkup.add("📝Чек-лист")
    daily_bonus_mrkup.add("👈Обратно")

    menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in Texts.menu_texts.keys():
        menu_markup.add(item)
    menu_markup.add('🎁Ежедневный бонус')
    menu_markup.add('Получить бесплатную консультацию эксперта')
    choose_card_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    choose_card_markup.add("Карта 1", "Карта 2")
    choose_card_markup.add("Карта 3", "Карта 4")
    choose_card_markup.add("Карта 5")
    choose_card_markup.add("👈Обратно")

    to_menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    to_menu_markup.add("👈Обратно")

    to_our_account = types.InlineKeyboardMarkup()
    to_our_account.add(types.InlineKeyboardButton("🔮 Получить метафорический разбор", url=f"https://t.me/spiriti_guide"))

    # mrkup_to_metaphorical_analysis = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # mrkup_to_metaphorical_analysis.add(types.KeyboardButton('💎 Финансы'), types.KeyboardButton('✨ Реализация'), types.KeyboardButton('👩‍❤️‍👨 Отношения'))
    # mrkup_to_metaphorical_analysis.add(types.KeyboardButton('🥺 Другое'), types.KeyboardButton('😷 Здоровье'))
    #
    # list_metaphorical_analysis = get_titles_from_kb(mrkup_to_metaphorical_analysis)
    # mrkup_to_metaphorical_analysis.add(types.KeyboardButton('👈Обратно'))

    mrkup_to_metaphorical_analysis = types.InlineKeyboardMarkup(row_width=2)
    mrkup_to_metaphorical_analysis.add(types.InlineKeyboardButton(text='💎 Финансы', callback_data='category:finance'),
                                       types.InlineKeyboardButton(text='✨ Реализация', callback_data='category:implementation'),
                                       types.InlineKeyboardButton(text='👩‍❤️‍👨 Отношения', callback_data='category:relationships'),
                                       types.InlineKeyboardButton(text='🥺 Другое', callback_data='category:other'),
                                       types.InlineKeyboardButton(text='😷 Здоровье', callback_data='category:health'),

                                       )

    list_metaphorical_analysis = get_titles_from_kb(mrkup_to_metaphorical_analysis)
