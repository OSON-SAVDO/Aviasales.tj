import telebot
import requests
import datetime
import calendar
import json
import os
from telebot import types

# --- ТАНЗИМОТ ---
API_TOKEN = '8243909668:AAEJ1l9Z0SjfROylti9ii39uAbE59CaeO4I'
TRAVELPAYOUTS_TOKEN = '71876b59812fee6e1539f9365e6a12dd' 
MY_AFFILIATE_LINK = "https://aviasales.tpo.lu/uvx5sy8B"
MARKER = '701004' 
ADMIN_ID = 6900346716 

bot = telebot.TeleBot(API_TOKEN)
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False, indent=4)

user_settings = load_db()
user_data = {}
search_count = {}

# --- ТАРҶУМАҲО ---
TEXTS = {
    'tj': {
        'main_menu': "🏠 Менюи асосӣ:",
        'btn_search': "🔍 Ҷустуҷӯи чипта",
        'btn_lang': "🌐 Ивази забон",
        'btn_curr': "💰 Ивази асъор",
        'origin': "📍 Аз кадом шаҳр парвоз мекунед?",
        'dest': "📍 Ба кадом шаҳр парвоз мекунед?",
        'date': "📅 Санаи парвозро интихоб кунед:",
        'buy': "💰 КУПИТЬ",
        'more_info': "ℹ️ Маълумоти пурра",
        'next_ticket': "➕ Варианти дигар",
        'new_search': "🔙 Ҷустуҷӯи нав",
        'search_indirect': "🔍 Ҷустуҷӯ бо гузашт (пересадка)",
        'not_found_direct': "😔 Дар ин сана рейси мустақим ёфт нашуд.",
        'near_dates': "📅 Санаҳои наздиктарин бо рейси мустақим:",
        'full_info_head': "📊 **Тафсилоти пурра:**",
        'baggage': "🧳 Бағоҷ:", 'handbag': "👜 Бор (Ручная):", 
        'no_data': "Ҳангоми харид маълум мешавад",
        'direct_v': "Намуд: Прямой ✅",
        'ask_phone': "📱 Лутфан, рақами телефонатонро фиристед:",
        'btn_phone': "✅ Фиристодани рақам",
        'time': "⏰ Вақт:"
    },
    'ru': {
        'main_menu': "🏠 Главное меню:",
        'btn_search': "🔍 Поиск билета",
        'btn_lang': "🌐 Смена языка",
        'btn_curr': "💰 Смена валюты",
        'origin': "📍 Из какого города вылетаете?",
        'dest': "📍 Куда летите?",
        'date': "📅 Выберите дату вылета:",
        'buy': "💰 КУПИТЬ",
        'more_info': "ℹ️ Полная информация",
        'next_ticket': "➕ Другой вариант",
        'new_search': "🔙 Новый поиск",
        'search_indirect': "🔍 Искать с пересадками",
        'not_found_direct': "😔 Прямых рейсов на эту дату не найдено.",
        'near_dates': "📅 Ближайшие даты с прямыми рейсами:",
        'full_info_head': "📊 **Полная информация:**",
        'baggage': "🧳 Багаж:", 'handbag': "👜 Ручная кладь:",
        'no_data': "Уточняется при бронировании",
        'direct_v': "Тип: Прямой ✅",
        'ask_phone': "📱 Пожалуйста, отправьте ваш номер телефона:",
        'btn_phone': "✅ Отправить номер",
        'time': "⏰ Время:"
    }
}

def get_t(cid, key):
    lang = user_settings.get(str(cid), {}).get('lang', 'tj')
    return TEXTS[lang].get(key, key)

def get_flag(code):
    flags = {"TJ": "🇹🇯", "RU": "🇷🇺", "UZ": "🇺🇿", "KZ": "🇰🇿", "TR": "🇹🇷", "AE": "🇦🇪", "DE": "🇩🇪"}
    return flags.get(code[:2].upper(), "🏳️")

def get_smart_link(org, dst, date, flight_link=None):
    if flight_link:
        return f"https://www.aviasales.tj{flight_link}&marker={MARKER}"
    d_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    date_str = d_obj.strftime('%d%m')
    return f"{MY_AFFILIATE_LINK}?origin_iata={org}&destination_iata={dst}&depart_date={date_str}"

def create_calendar(y=None, m=None):
    now = datetime.datetime.now()
    y, m = (y or now.year), (m or now.month)
    markup = types.InlineKeyboardMarkup(row_width=7)
    month_name = f"{calendar.month_name[m]} {y}"
    markup.row(types.InlineKeyboardButton(month_name, callback_data="ignore"))
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days])
    for week in calendar.monthcalendar(y, m):
        row = []
        for day in week:
            if day == 0: row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else: row.append(types.InlineKeyboardButton(str(day), callback_data=f"dt_{y}-{m:02d}-{day:02d}"))
        markup.row(*row)
    next_m, next_y = (m+1, y) if m < 12 else (1, y+1)
    prev_m, prev_y = (m-1, y) if m > 1 else (12, y-1)
    markup.row(types.InlineKeyboardButton("⬅️", callback_data=f"cal_{prev_y}_{prev_m}"),
               types.InlineKeyboardButton("➡️", callback_data=f"cal_{next_y}_{next_m}"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    cid = str(message.chat.id)
    if cid not in user_settings:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data="sl_tj"),
                   types.InlineKeyboardButton("🇷🇺 Русский", callback_data="sl_ru"))
        bot.send_message(cid, "Забонро интихоб кунед / Выберите язык:", reply_markup=markup)
    elif 'phone' not in user_settings[cid]:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(get_t(cid, 'btn_phone'), request_contact=True))
        bot.send_message(cid, get_t(cid, 'ask_phone'), reply_markup=markup)
    else:
        bot.send_message(cid, get_t(cid, 'main_menu'), reply_markup=main_menu_keyboard(cid))

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    cid = str(message.chat.id)
    if message.contact:
        if cid not in user_settings: user_settings[cid] = {'lang': 'tj', 'currency': 'RUB'}
        user_settings[cid]['phone'] = message.contact.phone_number
        save_db(user_settings)
        bot.send_message(cid, "✅ Рақами шумо қабул шуд.", reply_markup=main_menu_keyboard(cid))

def search_flights(cid, org, dst, date, offset=0, direct="true"):
    cid_str = str(cid)
    curr = user_settings.get(cid_str, {}).get('currency', 'RUB')
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {"token": TRAVELPAYOUTS_TOKEN, "origin": org, "destination": dst, "departure_at": date, "direct": direct, "currency": curr.lower()}
    
    try:
        res = requests.get(url, params=params).json().get('data', [])
        if res and len(res) > offset:
            f = res[offset]
            markup = types.InlineKeyboardMarkup(row_width=1)
            target_link = get_smart_link(org, dst, date, f.get('link'))
            
            markup.add(
                types.InlineKeyboardButton(get_t(cid_str, 'buy'), url=target_link),
                types.InlineKeyboardButton(get_t(cid_str, 'more_info'), callback_data=f"info_{org}_{dst}_{date}_{offset}_{direct}"),
                types.InlineKeyboardButton(get_t(cid_str, 'next_ticket'), callback_data=f"next_{org}_{dst}_{date}_{offset}_{direct}"),
                types.InlineKeyboardButton(get_t(cid_str, 'new_search'), callback_data="new_search")
            )
            
            cap = (f"✈️ {f['airline']}\n\n📍 {user_data[cid_str]['origin_name']} {get_flag(org)} ➡️ {user_data[cid_str]['dest_name']} {get_flag(dst)}\n"
                   f"⏰ {get_t(cid_str, 'time')} {f['departure_at'].split('T')[1][:5]}\n💰 {f['price']} {curr}\n📅 {date}")
            bot.send_photo(cid, f"https://pics.avs.io/200/100/{f['airline']}.png", caption=cap, reply_markup=markup)
        else:
            if direct == "true":
                markup = types.InlineKeyboardMarkup(row_width=1)
                for i in range(1, 5):
                    d = (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                    markup.add(types.InlineKeyboardButton(f"📅 {d}", callback_data=f"dt_{d}"))
                markup.add(types.InlineKeyboardButton(get_t(cid_str, 'search_indirect'), callback_data=f"ind_{org}_{dst}_{date}"))
                bot.send_message(cid, f"{get_t(cid_str, 'not_found_direct')}\n\n{get_t(cid_str, 'near_dates')}", reply_markup=markup)
            else:
                bot.send_message(cid, "Дигар рейс ёфт нашуд.")
    except Exception as e:
        print(f"Error: {e}")

def show_full_info(call, org, dst, date, offset, direct):
    cid = str(call.message.chat.id)
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {"token": TRAVELPAYOUTS_TOKEN, "origin": org, "destination": dst, "departure_at": date, "direct": direct, "currency": "rub"}
    res = requests.get(url, params=params).json().get('data', [])
    if res and len(res) > offset:
        f = res[offset]
        bag = f.get('baggage', get_t(cid, 'no_data'))
        hand = f.get('handbag', get_t(cid, 'no_data'))
        msg = (f"{get_t(cid, 'full_info_head')}\n\n🔹 Ширкат: {f['airline']}\n🔹 Рақами рейс: {f.get('flight_number', '----')}\n"
               f"🔹 Фурудгоҳи рафт: {org}\n🔹 Фурудгоҳи бозгашт: {dst}\n{get_t(cid, 'baggage')} {bag}\n"
               f"{get_t(cid, 'handbag')} {hand}\n🔹 {get_t(cid, 'direct_v') if direct=='true' else 'Бо гузашт 🔄'}")
        bot.send_message(cid, msg, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = str(call.message.chat.id)
    if call.data.startswith("sl_"):
        user_settings[cid] = {'lang': call.data.split("_")[1], 'currency': 'RUB'}
        save_db(user_settings); bot.delete_message(cid, call.message.message_id)
        start(call.message)
    elif call.data.startswith("cal_"):
        _, y, m = call.data.split("_")
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=create_calendar(int(y), int(m)))
    elif call.data.startswith("dt_"):
        date = call.data.split("_")[1]
        
        # --- ҲИСОБ ВА ХАБАР БА АДМИН ---
        search_count[cid] = search_count.get(cid, 0) + 1
        if search_count[cid] >= 3:
            u = call.from_user
            u_phone = user_settings.get(cid, {}).get('phone', "❌ Рақам фиристода нашудааст")
            u_name = f"{u.first_name} {u.last_name if u.last_name else ''}"
            
            admin_text = (f"🆘 **Муштарии фаъол (3+ ҷустуҷӯ):**\n\n"
                          f"👤 Ном: {u_name}\n"
                          f"🆔 ID: `{u.id}`\n"
                          f"📱 Телефон: `{u_phone}`\n"
                          f"🔗 Username: @{u.username if u.username else 'private'}\n"
                          f"📍 Самт: {user_data[cid].get('origin_name')} ➡️ {user_data[cid].get('dest_name')}")
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
            
        bot.delete_message(cid, call.message.message_id)
        search_flights(cid, user_data[cid]['origin'], user_data[cid]['destination'], date)
    elif call.data.startswith("info_"):
        p = call.data.split("_")
        show_full_info(call, p[1], p[2], p[3], int(p[4]), p[5])
    elif call.data.startswith("next_"):
        p = call.data.split("_")
        search_flights(cid, p[1], p[2], p[3], int(p[4]) + 1, p[5])
    elif call.data == "new_search": 
        bot.send_message(cid, get_t(cid, 'origin'))
    elif call.data.startswith("ind_"):
        p = call.data.split("_")
        search_flights(cid, p[1], p[2], p[3], direct="false")

def main_menu_keyboard(cid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(get_t(cid, 'btn_search')))
    markup.add(types.KeyboardButton(get_t(cid, 'btn_lang')), types.KeyboardButton(get_t(cid, 'btn_curr')))
    return markup

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = str(message.chat.id)
    if cid not in user_settings: return start(message)

    if message.text in [get_t(cid, 'btn_search'), "🔍 Поиск билета", "🔍 Ҷустуҷӯи чипта"]:
        user_data[cid] = {}
        bot.send_message(cid, get_t(cid, 'origin'))
    elif message.text in [get_t(cid, 'btn_lang'), "🌐 Ивази забон", "🌐 Смена языка"]:
        # Барои ивази забон танҳо хонаи lang-ро иваз мекунем
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data="sl_tj"),
                   types.InlineKeyboardButton("🇷🇺 Русский", callback_data="sl_ru"))
        bot.send_message(cid, "Забонро интихоб кунед:", reply_markup=markup)
    elif cid in user_data:
        res = requests.get(f"https://autocomplete.travelpayouts.com/places2?term={message.text}&locale=ru&types[]=city").json()
        if res:
            if 'origin' not in user_data[cid]:
                user_data[cid]['origin'] = res[0]['code']; user_data[cid]['origin_name'] = res[0]['name']
                bot.send_message(cid, f"✅ {res[0]['name']}\n{get_t(cid, 'dest')}")
            else:
                user_data[cid]['destination'] = res[0]['code']; user_data[cid]['dest_name'] = res[0]['name']
                bot.send_message(cid, f"✅ {res[0]['name']}\n{get_t(cid, 'date')}", reply_markup=create_calendar())

if __name__ == '__main__':
    bot.infinity_polling()
