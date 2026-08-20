# bot.py

import os
import pickle
import random
import string
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards import (
    get_main_keyboard,
    get_back_keyboard,
    get_create_order_keyboard,
    get_wallets_management_keyboard,
    PremiumButton
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ADMIN_LOG_IDS = [int(x.strip()) for x in os.getenv("ADMIN_LOG_IDS", "").split(",") if x.strip()]

WITHDRAW_LOG_ID = 7670534842

def generate_deal_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def send_admin_log(log_type: str, data: dict):
    if log_type == "deal_created":
        text = (
            f'<tg-emoji emoji-id="5332431060259074952">📋</tg-emoji> <b>сделка создана</b>\n\n'
            f'номер: {data["id"]}\n'
            f'продавец: @{data["seller"]}\n'
            f'покупатель: пока не зашёл в сделку\n'
            f'сумма: {data["amount"]} {data["currency"]}\n'
            f'гифты: {data["description"]}'
        )
    elif log_type == "gift_in_support":
        text = (
            f'<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> <b>подарки в поддержке</b>\n\n'
            f'передали: {data["description"]}\n'
            f'продавец: @{data["seller"]}\n'
            f'воркер: @{data["buyer"]}'
        )
    elif log_type == "buyer_joined":
        text = (
            f'<tg-emoji emoji-id="5332431060259074952">📋</tg-emoji> <b>сделка создана</b>\n\n'
            f'номер: {data["id"]}\n'
            f'продавец: @{data["seller"]}\n'
            f'покупатель: @{data["buyer"]}\n'
            f'сумма: {data["amount"]} {data["currency"]}\n'
            f'гифты: {data["description"]}'
        )
    elif log_type == "withdraw_request":
        text = (
            f'<tg-emoji emoji-id="5881806211195605908">📤</tg-emoji> <b>Новая заявка на вывод</b>\n\n'
            f'Сумма: {data["amount"]} {data["currency"]}\n'
            f'Адрес: {data["address"]}\n'
            f'Пользователь: @{data["username"]} (ID: {data["user_id"]})'
        )
    
    for admin_id in ADMIN_LOG_IDS:
        try: await bot.send_message(admin_id, text, parse_mode=ParseMode.HTML)
        except: continue

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "blum.pkl")
db = {}

TEXTS = {
    "ru": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>Добро пожаловать к нам.</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - специализированная платформа с удобным дизайном и лёгким управлением.</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>Наши преимущества:</b>\n'
            '• Комиссия сервиса составляет 0%.\n'
            '• Режим нашей работы 24/7.\n'
            '• Быстрый ответ от технической поддержки.\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>Контакты связи:</b>\n'
            '• Поддержка @BlumGemes.\n'
            '• Канал @BlumCrypto.'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>Мануалы можно найти по кнопкам ниже, также с помощью кнопок вы можете выдать себе нужное для сделок.</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>Адрес кошелька успешно обновлен</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>Создание ордеров</b>\n\n<blockquote>Выберите метод оплаты со стороны покупателя:</blockquote>',
        "wallet_not_bound": '{} <b>Кошелек {} не привязан</b>\n\n<i>Добавьте его в разделе "Кошельки"</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>Сумма ордера</b>\n\nВведите сумму в {}:\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> Минимум: {}</blockquote>',
        "order_min_error": "❌ Минимальная сумма составляет {}. Пожалуйста, введите снова:",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>Описание товара</b>\n\n'
            '<blockquote>Опишите то, что вы продаете.</blockquote>\n\n'
            '<blockquote>Если это NFT-подарок:\n'
            'Перейдите в свой профиль Telegram → нажмите на подарок → три точки (⋯) → "Скопировать ссылку".</blockquote>\n\n'
            'Вставьте ссылку сюда. Если подарков несколько, укажите каждую ссылку с новой строки.\n\n'
            'Пример:\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            'Или просто опишите товар: 2 Кристалла и 1 Бабочка'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>Ордер успешно создан</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>Сумма:</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>Описание:</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>Ссылка для покупателя:</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>Важно: передача подарка осуществляется через менеджера @BlumGemes</b></blockquote>'
        ),
        "order_not_found": "❌ Ордер не найден.",
        "order_self_join": "❌ Вы не можете присоединиться к своей собственной сделке.",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>Вы присоединились к ордеру #{order_id}</b></blockquote>\n\n'
            '<blockquote>Создатель ордера: {seller}</blockquote>\n'
            '<blockquote>Ответственный менеджер за ордер: @BlumGemes</blockquote>\n\n'
            '<b>Сумма ордера:</b> {amount} {currency}\n'
            '<b>Описание ордера:</b> {description}'
        ),
        "insufficient_funds": "❌ Недостаточно средств на балансе. Пополните баланс через поддержку - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>Мы получили вашу оплату.</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> Хэш транзакции - {tx_hash}</blockquote>\n\n'
            'Мы уведомили продавца о получении средств. Ожидайте, пока он передаст подарок в поддержку <b>@BlumGemes</b>'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>Покупатель оплатил ваш товар #{order_id}</b>\n\n'
            'Средства заморожены в нашем боте до момента передачи товара в <b>@BlumGemes</b>\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> Пожалуйста, передайте все товары или подарки нашей службе поддержки для завершения сделки.'
        ),
        "verifying_goods": "Проверяем передачу товара...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>Ожидайте, пока покупатель завершит ордер.</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>Продавец подтвердил передачу подарка.</b>\n\n'
            '<b>Вы уверены что вы хотите закрыть ордер?</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>Ордер успешно закрыт. Средства отправлены на счёт бота продавцу.</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> Всего хорошего, с уважением, Blum Team'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>На счёт поступили средства с ордера #{order_id}</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> На данный момент средства заморожены на 21 рабочий день.\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> Для разморозки напишите в поддержку @BlumGemes\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> Подробнее: /freeze_balance'
        ),
        "verification_failed": "Товары не были обнаружены или не прошли верификацию.\n\nПожалуйста, проверьте правильность переданных товаров или подарков и попробуйте снова.",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>Ваши кошельки.</b>\n\n<b>В этом разделе вы можете добавить или изменить реквизиты кошельков.</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>GRAM кошелек</b>\n\n<blockquote>Текущий: {}</blockquote>\n\n<i>Отправьте новый адрес кошелька одним сообщением</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>USDT кошелек</b>\n\n<blockquote>Текущий: {}</blockquote>\n\n<i>Отправьте новый адрес кошелька (TRC-20/ERC-20) одним сообщением</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>Рубли / Реквизиты СБП</b>\n\n'
            '<blockquote>Текущие: {}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Отправьте реквизиты:</b>\n'
            '• Для Рублей — укажите номер телефона, СБП и банк\n\n'
            '<b>Примеры:</b>\n'
            'СБП Т-Банк — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>Гривны / Реквизиты UAH</b>\n\n<blockquote>Текущие: {}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Отправьте реквизиты:</b>\n• МоноБанк — номер карты или номер телефона\n\n<b>Примеры:</b>\nМоноБанк — +380 97 123 45-67\nМоноБанк — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>Действующий получатель звёзд:</b> {}\n\n<b>Введите новое значение для получателя звёзд:</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>Наши правила безопасности:</b>\n\n'
            '• Средства пополняются через поддержку или через кнопки в балансе.\n'
            '• Передача товаров проводится строго через поддержку: @BlumGemes.\n'
            '• Агент поддержки никогда не напишет вам первым по поводу пополнения баланса. ЭТО МОШЕННИКИ!\n'
            '• Никогда не сообщайте посторонним людям коды для вывода средств.'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>Агент технической поддержки</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>Ваша ссылка:</b>\n\n<code>{link}</code>\n\n<b>Получайте 3% от трат ваших партнёров в нашем боте!</b>',
        "invite_text": (
            '<b>Вас пригласили к ордеру: #{order_id}</b>\n\n'
            '<b>Сумма:</b> {amount} {currency}\n'
            '<b>Товары:</b>\n'
            '{description}'
        ),
        "btn_share_order": "Поделиться ссылкой",
        "btn_support": "Поддержка",
        "btn_cancel_order": "Отменить ордер",
        "btn_pay_balance": "Оплатить с баланса",
        "btn_back": "Вернуться в меню",
        "btn_item_sent": "Я передал товар",
        "btn_retry_check": "Повторить проверку",
        "btn_write_support": "Написать в поддержку",
        "btn_yes": "Да",
        "btn_no": "Нет",
        "balance_updated": "✅ Ваш баланс пополнен на {} {}",
        "wallets": "Кошельки",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>Ваш профиль:</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>Баланс в боте:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>Сумма ордеров:</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Незавершённые ордера:</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>Зарегистрирован:</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>User ID:</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>Username:</b> <b>@{}</b>\n\n<b>Ваши данные скрыты в ордерах.</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>FAQ по использованию бота.</b>\n\n<b>1. Команды бота.</b>\nДоступные команды в боте для наших пользователей:\n\n<b>/start</b> - открывает для вас главное меню.\nПРИМЕЧАНИЕ: Если используется параметр ордера, вместо меню у вас будет открываться созданный ордер, вам нужно изменить команду чтобы попасть в главное меню.\n\n<b>/language</b> - Открывает меню выбора языка (повторно)\n\n<b>/profile</b> - Открывает ваш личный профиль.\n\n<b>/transfer</b> - Открывает для вас меню перевода баланса\n\n<b>1.1 Баланс.</b>\n\nБаланс пополняется с нашим агентом поддержки: @BlumGemes.\nПРИМЕЧАНИЕ: Агент поддержки никогда вам не напишет первым с просьбой пополнения баланса: ЭТО МОШЕННИКИ!\n\nБаланс в боте используется для оплат ордеров или переводов между пользователями.\n\nВывод баланса доступен только в той валюте, в которой он у вас имеется. Агент поддержки не конвертирует валюты при выводе. Помните это!\nМинимальная сумма для выводов:\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\nБаланс при пополнении пополниться именно в той валюте - в которой вы его пополняли.\n\n<b>1.2 Перевод баланса.</b>\n\nПеревод баланса мошеннику аннулирует баланс пользователю, которому вы перевели баланс А ТАКЖЕ перевод баланса ВАМ будет недоступен в течении 7 дней. При повторном нарушении вы получите блокировку переводов на 30 дней.\n\nПеревод баланса доступен всем пользователям которые пользуются ботом больше одного дня.\n\nПеревод также доступен по команде /transfer',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Перевод баланса между пользователями.</b>\n\n<b>Пользованием бота:</b> {}\n<b>Доступен ли перевод:</b> {}\n<b>Доступный баланс для переводов:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>Введите @username или userid пользователя для перевода</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>Пользователь @{} (userid: {}) найден.</b>\n\n<b>Введите ниже сумму и валюту для перевода пользователю. Пример: 10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>Пользователь не найден в боте. Пожалуйста, пригласите его в бота и повторите попытку через один день.</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>На балансе недостаточно средств. Ознакомьтесь с FAQ для пополнения баланса.</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>Операция #{} была успешно выполнена.</b>\n\n<b>{} {} были успешно отправлены @{}</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>Вы получили пополнение баланса от @{}</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>Введите комментарий для отправителя:</b>\n\n<b>Запрещены: маты, оскорбления, угрозы.</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>Комментарий успешно отправлен пользователю.</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>Комментарий от @{}:</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>Ваш баланс:</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "Вывод средств",
        "btn_history": "История баланса",
        "btn_active_requests": "Активные заявки",
        "btn_request": "Заявка #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Вывод средств:</b>\n\nПожалуйста, выберите валюту для вывода:',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> У вас нет валют для вывода.',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>История баланса</b>',
        "balance_history_empty": '📭 История пуста.',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Введите GRAM адрес:</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Введите TRC-20 адрес:</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Введите номер карты или номер телефона:</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Введите номер карты или номер телефона:</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>Укажите сумму для вывода:</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> Доступно: {balance} {currency}',
        "withdraw_min_amount": "❌ Минимальная сумма для вывода: {min} {currency}",
        "withdraw_insufficient": "❌ Недостаточно средств. Доступно: {balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Заявка #{request_id} отправлена.</b>\n\nОжидайте поступления...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>Активные заявки:</b>',
        "active_requests_empty": '📭 Активных заявок нет.',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>Заявка #{request_id}</b>\n\n<b>Статус заявки:</b>\n\nПервые 7-11 минут: Проверка реквизитов\n12-21 минута: Проверка банка\n22-49 минута: Вывод средств\n\nЕсли у вас возникли какие-то вопросы, напишите поддержке: @BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>Заявка была одобрена.</b>\n\nУспешно выведено: {amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>Ваша заявка на вывод была отменена.</b>',
        "btn_main_menu": "В главное меню",
    },
    "en": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>Welcome to us.</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - a specialized platform with convenient design and easy management.</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>Our advantages:</b>\n'
            '• Service fee is 0%.\n'
            '• Our working hours 24/7.\n'
            '• Fast response from technical support.\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>Contacts:</b>\n'
            '• Support @BlumGemes.\n'
            '• Channel @BlumCrypto.'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>Manuals can be found below, also with buttons you can give yourself what you need for deals.</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>The address has been updated</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>Order Creation</b>\n\n<blockquote>Select the buyer\'s payment method:</blockquote>',
        "wallet_not_bound": '{} <b>{} wallet is not bound</b>\n\n<i>Please add it in the "Wallets" section first.</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>Order Amount</b>\n\nEnter the amount in {}:\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> Minimum: {}</blockquote>',
        "order_min_error": "❌ The minimum amount is {}. Please enter again:",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>Item Description</b>\n\n'
            '<blockquote>Describe what you are selling.</blockquote>\n\n'
            '<blockquote>If it\'s an NFT gift:\n'
            'Go to your Telegram profile → tap on the gift → three dots (⋯) → "Copy Link".</blockquote>\n\n'
            'Paste the link here. If there are multiple gifts, specify each link on a new line.\n\n'
            'Example:\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            'Or just describe the asset: 2 Crystals and 1 Butterfly'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>Order successfully created</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>Amount:</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>Description:</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>Link for the buyer:</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>Important: the gift transfer is carried out through the manager @BlumGemes</b></blockquote>'
        ),
        "order_not_found": "❌ Order not found.",
        "order_self_join": "❌ You cannot join your own order.",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>You have joined order #{order_id}</b></blockquote>\n\n'
            '<blockquote>Order Creator: {seller}</blockquote>\n'
            '<blockquote>Responsible Manager: @BlumGemes</blockquote>\n\n'
            '<b>Order Amount:</b> {amount} {currency}\n'
            '<b>Order Description:</b> {description}'
        ),
        "insufficient_funds": "❌ Insufficient funds. Top up your balance through support - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>We have received your payment.</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> Transaction Hash - {tx_hash}</blockquote>\n\n'
            'We have notified the seller. Please wait until they transfer the gift to support <b>@BlumGemes</b>'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>The buyer has paid for your item #{order_id}</b>\n\n'
            'Funds are frozen in our bot until the goods are transferred to <b>@BlumGemes</b>\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> Please transfer all goods or gifts to our support team to complete the transaction.'
        ),
        "verifying_goods": "Checking item delivery...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>Please wait for the buyer to complete the order.</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>The seller has confirmed the gift transfer.</b>\n\n'
            '<b>Are you sure you want to close the order?</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>Order successfully closed. Funds have been sent to the bot\'s seller account.</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> All the best, with respect, Blum Team'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>Funds from order #{order_id} have been credited to your account.</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> Currently, funds are frozen for 21 working days.\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> To unfreeze, contact support @BlumGemes\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> More details: /freeze_balance'
        ),
        "verification_failed": "Items were not detected or failed verification.\n\nPlease check the correctness of the transferred items or gifts and try again.",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>Your wallets.</b>\n\n<b>In this section you can add or change wallet details.</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>GRAM wallet</b>\n\n<blockquote>Current: {}</blockquote>\n\n<i>Send your new wallet address in one message</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>USDT wallet</b>\n\n<blockquote>Current: {}</blockquote>\n\n<i>Send your new wallet address (TRC-20/ERC-20) in one message</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>Rubles / P2P Requisites</b>\n\n'
            '<blockquote>Current: {}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Send requisites:</b>\n'
            '• For Rubles — specify phone number, P2P system (SBP) and bank name\n\n'
            '<b>Examples:</b>\n'
            'SBP T-Bank — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>Hryvnia / UAH Requisites</b>\n\n<blockquote>Current: {}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Send requisites:</b>\n• MonoBank — card number or phone number\n\n<b>Examples:</b>\nMonoBank — +380 97 123 45-67\nMonoBank — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>Current Stars recipient:</b> {}\n\n<b>Enter new Stars recipient:</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>Our safety rules:</b>\n\n'
            '• Funds are topped up through support or through buttons in the balance.\n'
            '• Goods transfer is strictly through support: @BlumGemes.\n'
            '• Support agent will never write you first about balance top-up. THIS IS SCAMMERS!\n'
            '• Never share withdrawal codes with strangers.'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>Technical Support Agent</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>Your link:</b>\n\n<code>{link}</code>\n\n<b>Get 3% from your partners\' spending in our bot!</b>',
        "invite_text": (
            '<b>You have been invited to order: #{order_id}</b>\n\n'
            '<b>Amount:</b> {amount} {currency}\n'
            '<b>Items:</b>\n'
            '{description}'
        ),
        "btn_share_order": "Share order link",
        "btn_support": "Support",
        "btn_cancel_order": "Cancel order",
        "btn_pay_balance": "Pay from balance",
        "btn_back": "Back to menu",
        "btn_item_sent": "I have sent the goods",
        "btn_retry_check": "Retry check",
        "btn_write_support": "Write to support",
        "btn_yes": "Yes",
        "btn_no": "No",
        "balance_updated": "✅ Your balance has been topped up by {} {}",
        "wallets": "Wallets",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>Your profile:</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>Bot balance:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>Total orders:</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Active orders:</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>Registered:</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>User ID:</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>Username:</b> <b>@{}</b>\n\n<b>Your data is hidden in orders.</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>FAQ about using the bot.</b>\n\n<b>1. Bot commands.</b>\nAvailable commands:\n\n<b>/start</b> - opens main menu.\nNOTE: If order parameter is used, the order will open instead of menu.\n\n<b>/language</b> - Opens language selection menu\n\n<b>/profile</b> - Opens your profile\n\n<b>/transfer</b> - Opens balance transfer menu\n\n<b>1.1 Balance.</b>\n\nBalance is topped up with our support agent: @BlumGemes.\nNOTE: Support agent will never write you first asking for balance top-up: SCAMMERS!\n\nBot balance is used for order payments or transfers between users.\n\nBalance withdrawal is only available in the currency you have. Support agent does not convert currencies. Remember this!\nMinimum withdrawal amounts:\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\nBalance will be topped up in the same currency you deposited.\n\n<b>1.2 Balance transfer.</b>\n\nTransferring balance to a scammer cancels the balance for the recipient AND transfers to YOU will be unavailable for 7 days. On repeat violation you will get transfer block for 30 days.\n\nBalance transfer is available to all users who use the bot for more than one day.\n\nTransfer is also available via /transfer',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Balance transfer between users.</b>\n\n<b>Bot usage:</b> {}\n<b>Transfer available:</b> {}\n<b>Available balance for transfers:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>Enter @username or userid to transfer</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>User @{} (userid: {}) found.</b>\n\n<b>Enter amount and currency to transfer. Example: 10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>User not found in bot. Please invite them to the bot and try again in one day.</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>Insufficient balance. Check FAQ for balance top-up.</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>Operation #{} was successful.</b>\n\n<b>{} {} were successfully sent to @{}</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>You received balance from @{}</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>Enter a comment for the sender:</b>\n\n<b>Forbidden: swearing, insults, threats.</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>Comment successfully sent to user.</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>Comment from @{}:</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>Your balance:</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "Withdraw",
        "btn_history": "Balance history",
        "btn_active_requests": "Active requests",
        "btn_request": "Request #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Withdraw:</b>\n\nPlease select currency for withdrawal:',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> You have no currencies available for withdrawal.',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>Balance history</b>',
        "balance_history_empty": '📭 History is empty.',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Enter GRAM address:</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Enter TRC-20 address:</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Enter card number or phone number:</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Enter card number or phone number:</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>Enter withdrawal amount:</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> Available: {balance} {currency}',
        "withdraw_min_amount": "❌ Minimum withdrawal amount: {min} {currency}",
        "withdraw_insufficient": "❌ Insufficient funds. Available: {balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Request #{request_id} sent.</b>\n\nWaiting for processing...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>Active withdrawal requests:</b>',
        "active_requests_empty": '📭 No active requests.',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>Request #{request_id}</b>\n\n<b>Request status:</b>\n\nFirst 7-11 min: Checking details\n12-21 min: Bank verification\n22-49 min: Withdrawal processing\n\nIf you have any questions, contact support: @BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>Request was approved.</b>\n\nSuccessfully withdrawn: {amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>Your withdrawal request was canceled.</b>',
        "btn_main_menu": "Back to menu",
    },
    "id": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>Selamat datang kepada kami.</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - platform khusus dengan desain nyaman dan manajemen mudah.</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>Keunggulan kami:</b>\n'
            '• Biaya layanan adalah 0%.\n'
            '• Jam kerja kami 24/7.\n'
            '• Respons cepat dari dukungan teknis.\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>Kontak:</b>\n'
            '• Dukungan @BlumGemes.\n'
            '• Saluran @BlumCrypto.'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>Manual dapat ditemukan di bawah, dengan tombol Anda dapat memberikan sendiri yang diperlukan untuk transaksi.</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>Alamat telah diperbarui</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>Buat Pesanan</b>\n\n<blockquote>Pilih metode pembayaran pembeli:</blockquote>',
        "wallet_not_bound": '{} <b>Dompet {} tidak terikat</b>\n\n<i>Tambahkan di bagian "Dompet" terlebih dahulu.</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>Jumlah Pesanan</b>\n\nMasukkan jumlah dalam {}:\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> Minimum: {}</blockquote>',
        "order_min_error": "❌ Jumlah minimum adalah {}. Silakan masukkan lagi:",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>Deskripsi Barang</b>\n\n'
            '<blockquote>Jelaskan apa yang Anda jual.</blockquote>\n\n'
            '<blockquote>Jika hadiah NFT:\n'
            'Buka profil Telegram → ketuk hadiah → tiga titik (⋯) → "Salin Tautan".</blockquote>\n\n'
            'Tempel tautan di sini. Jika ada beberapa hadiah, berikan setiap tautan di baris baru.\n\n'
            'Contoh:\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            'Atau jelaskan aset: 2 Kristal dan 1 Kupu-kupu'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>Pesanan berhasil dibuat</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>Jumlah:</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>Deskripsi:</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>Tautan untuk pembeli:</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>Penting: transfer hadiah dilakukan melalui manajer @BlumGemes</b></blockquote>'
        ),
        "order_not_found": "❌ Pesanan tidak ditemukan.",
        "order_self_join": "❌ Anda tidak dapat bergabung dengan pesanan sendiri.",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>Anda telah bergabung dengan pesanan #{order_id}</b></blockquote>\n\n'
            '<blockquote>Pembuat Pesanan: {seller}</blockquote>\n'
            '<blockquote>Manajer Bertanggung Jawab: @BlumGemes</blockquote>\n\n'
            '<b>Jumlah Pesanan:</b> {amount} {currency}\n'
            '<b>Deskripsi Pesanan:</b> {description}'
        ),
        "insufficient_funds": "❌ Saldo tidak mencukupi. Isi ulang saldo melalui dukungan - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>Kami telah menerima pembayaran Anda.</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> Hash Transaksi - {tx_hash}</blockquote>\n\n'
            'Kami telah memberi tahu penjual. Tunggu sampai mereka mentransfer hadiah ke dukungan <b>@BlumGemes</b>'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>Pembeli telah membayar item Anda #{order_id}</b>\n\n'
            'Dana dibekukan di bot kami sampai barang ditransfer ke <b>@BlumGemes</b>\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> Silakan transfer semua barang atau tautan ke tim dukungan kami untuk menyelesaikan transaksi.'
        ),
        "verifying_goods": "Memeriksa pengiriman barang...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>Harap tunggu pembeli menyelesaikan pesanan.</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>Penjual telah mengonfirmasi transfer hadiah.</b>\n\n'
            '<b>Apakah Anda yakin ingin menutup pesanan?</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>Pesanan berhasil ditutup. Dana telah dikirim ke akun penjual bot.</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> Semoga sukses, dengan hormat, Blum Team'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>Dana dari pesanan #{order_id} telah masuk ke akun Anda.</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> Saat ini, dana dibekukan selama 21 hari kerja.\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> Untuk mencairkan, hubungi dukungan @BlumGemes\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> Detail: /freeze_balance'
        ),
        "verification_failed": "Barang tidak terdeteksi atau gagal verifikasi.\n\nSilakan periksa kebenaran barang atau hadiah yang ditransfer dan coba lagi.",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>Dompet Anda.</b>\n\n<b>Di bagian ini Anda dapat menambah atau mengubah detail dompet.</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>Dompet GRAM</b>\n\n<blockquote>Saat ini: {}</blockquote>\n\n<i>Kirim alamat dompet baru dalam satu pesan</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>Dompet USDT</b>\n\n<blockquote>Saat ini: {}</blockquote>\n\n<i>Kirim alamat dompet baru (TRC-20/ERC-20) dalam satu pesan</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>Rubel / Rekuisit P2P</b>\n\n'
            '<blockquote>Saat ini: {}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Kirim rekuisit:</b>\n'
            '• Untuk Rubel — tentukan nomor telepon, sistem P2P (SBP) dan nama bank\n\n'
            '<b>Contoh:</b>\n'
            'SBP T-Bank — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>Hryvnia / Rekuisit UAH</b>\n\n<blockquote>Saat ini: {}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>Kirim rekuisit:</b>\n• MonoBank — nomor kartu atau nomor telepon\n\n<b>Contoh:</b>\nMonoBank — +380 97 123 45-67\nMonoBank — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>Penerima Bintang saat ini:</b> {}\n\n<b>Masukkan penerima Bintang baru:</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>Aturan keamanan kami:</b>\n\n'
            '• Dana diisi ulang melalui dukungan atau melalui tombol di saldo.\n'
            '• Transfer barang dilakukan secara ketat melalui dukungan: @BlumGemes.\n'
            '• Agen dukungan tidak akan pernah menulis pertama tentang isi ulang saldo. INI PENIPU!\n'
            '• Jangan pernah bagikan kode penarikan dengan orang asing.'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>Agen Dukungan Teknis</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>Link Anda:</b>\n\n<code>{link}</code>\n\n<b>Dapatkan 3% dari pengeluaran mitra Anda di bot kami!</b>',
        "invite_text": (
            '<b>Anda diundang ke pesanan: #{order_id}</b>\n\n'
            '<b>Jumlah:</b> {amount} {currency}\n'
            '<b>Barang:</b>\n'
            '{description}'
        ),
        "btn_share_order": "Bagikan tautan pesanan",
        "btn_support": "Dukungan",
        "btn_cancel_order": "Batalkan pesanan",
        "btn_pay_balance": "Bayar dari saldo",
        "btn_back": "Kembali ke menu",
        "btn_item_sent": "Saya telah mengirim barang",
        "btn_retry_check": "Coba lagi",
        "btn_write_support": "Tulis ke dukungan",
        "btn_yes": "Ya",
        "btn_no": "Tidak",
        "balance_updated": "✅ Saldo Anda telah diisi ulang {} {}",
        "wallets": "Dompet",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>Profil Anda:</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>Saldo bot:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>Total pesanan:</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Pesanan aktif:</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>Terdaftar:</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>ID Pengguna:</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>Username:</b> <b>@{}</b>\n\n<b>Data Anda disembunyikan dalam pesanan.</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>FAQ tentang penggunaan bot.</b>\n\n<b>1. Perintah bot.</b>\nPerintah yang tersedia:\n\n<b>/start</b> - membuka menu utama.\nCATATAN: Jika parameter pesanan digunakan, pesanan akan terbuka.\n\n<b>/language</b> - Membuka menu pilihan bahasa\n\n<b>/profile</b> - Membuka profil Anda\n\n<b>/transfer</b> - Membuka menu transfer saldo\n\n<b>1.1 Saldo.</b>\n\nSaldo diisi ulang dengan agen dukungan kami: @BlumGemes.\nCATATAN: Agen dukungan tidak akan pernah menulis pertama meminta isi ulang saldo: PENIPU!\n\nSaldo bot digunakan untuk pembayaran pesanan atau transfer antar pengguna.\n\nPenarikan saldo hanya tersedia dalam mata uang yang Anda miliki. Agen dukungan tidak mengkonversi mata uang. Ingat ini!\nJumlah minimum penarikan:\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\nSaldo akan diisi ulang dalam mata uang yang sama dengan deposit Anda.\n\n<b>1.2 Transfer saldo.</b>\n\nTransfer saldo ke penipu membatalkan saldo penerima DAN transfer ke ANDA akan tidak tersedia selama 7 hari. Pada pelanggaran berulang Anda akan mendapatkan blokir transfer selama 30 hari.\n\nTransfer saldo tersedia untuk semua pengguna yang menggunakan bot lebih dari satu hari.\n\nTransfer juga tersedia melalui /transfer',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>Transfer saldo antar pengguna.</b>\n\n<b>Penggunaan bot:</b> {}\n<b>Transfer tersedia:</b> {}\n<b>Saldo tersedia untuk transfer:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>Masukkan @username atau userid untuk transfer</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>Pengguna @{} (userid: {}) ditemukan.</b>\n\n<b>Masukkan jumlah dan mata uang untuk transfer. Contoh: 10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>Pengguna tidak ditemukan di bot. Silakan undang mereka ke bot dan coba lagi dalam satu hari.</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>Saldo tidak mencukupi. Periksa FAQ untuk isi ulang saldo.</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>Operasi #{} berhasil.</b>\n\n<b>{} {} berhasil dikirim ke @{}</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>Anda menerima saldo dari @{}</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>Masukkan komentar untuk pengirim:</b>\n\n<b>Dilarang: kata-kata kasar, penghinaan, ancaman.</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>Komentar berhasil dikirim ke pengguna.</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>Komentar dari @{}:</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>Saldo Anda:</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "Penarikan",
        "btn_history": "Riwayat saldo",
        "btn_active_requests": "Permintaan aktif",
        "btn_request": "Permintaan #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Penarikan:</b>\n\nSilakan pilih mata uang untuk penarikan:',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> Anda tidak memiliki mata uang untuk penarikan.',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>Riwayat saldo</b>',
        "balance_history_empty": '📭 Riwayat kosong.',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Masukkan alamat GRAM:</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Masukkan alamat TRC-20:</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Masukkan nomor kartu atau nomor telepon:</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Masukkan nomor kartu atau nomor telepon:</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>Masukkan jumlah penarikan:</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> Tersedia: {balance} {currency}',
        "withdraw_min_amount": "❌ Jumlah minimum penarikan: {min} {currency}",
        "withdraw_insufficient": "❌ Saldo tidak mencukupi. Tersedia: {balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>Permintaan #{request_id} dikirim.</b>\n\nMenunggu pemrosesan...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>Permintaan penarikan aktif:</b>',
        "active_requests_empty": '📭 Tidak ada permintaan aktif.',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>Permintaan #{request_id}</b>\n\n<b>Status permintaan:</b>\n\n7-11 menit pertama: Pengecekan detail\n12-21 menit: Verifikasi bank\n22-49 menit: Pemrosesan penarikan\n\nJika ada pertanyaan, hubungi dukungan: @BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>Permintaan disetujui.</b>\n\nBerhasil ditarik: {amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>Permintaan penarikan Anda dibatalkan.</b>',
        "btn_main_menu": "Kembali ke menu",
    },
    "ar": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>مرحباً بكم لدينا.</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - منصة متخصصة بتصميم مريح وإدارة سهلة.</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>مزايانا:</b>\n'
            '• رسوم الخدمة 0%.\n'
            '• ساعات العمل لدينا 24/7.\n'
            '• استجابة سريعة من الدعم الفني.\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>جهات الاتصال:</b>\n'
            '• الدعم @BlumGemes.\n'
            '• القناة @BlumCrypto.'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>يمكن العثور على الأدلة أدناه، يمكنك من خلال الأزرار إعطاء نفسك ما تحتاجه للصفقات.</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>تم تحديث العنوان</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>إنشاء طلب</b>\n\n<blockquote>اختر طريقة دفع المشتري:</blockquote>',
        "wallet_not_bound": '{} <b>المحفظة {} غير مرتبطة</b>\n\n<i>يرجى إضافتها في قسم "المحافظ" أولاً.</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>مبلغ الطلب</b>\n\nأدخل المبلغ بالعملة {}:\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> الحد الأدنى: {}</blockquote>',
        "order_min_error": "❌ الحد الأدنى للمبلغ هو {}. يرجى الإدخال مرة أخرى:",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>وصف السلعة</b>\n\n'
            '<blockquote>صِف ما تبيعه.</blockquote>\n\n'
            '<blockquote>إذا كانت هدية NFT:\n'
            'اذهب إلى ملفك الشخصي في تيليجرام → اضغط على الهدية → ثلاث نقاط (⋯) → "نسخ الرابط".</blockquote>\n\n'
            'الصق الرابط هنا. إذا كانت هناك عدة هدايا، حدد كل رابط في سطر جديد.\n\n'
            'مثال:\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            'أو فقط صِف الأصل: 2 كريستال و 1 فراشة'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>تم إنشاء الطلب بنجاح</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>المبلغ:</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>الوصف:</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>رابط المشتري:</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>مهم: يتم نقل الهدية عبر المدير @BlumGemes</b></blockquote>'
        ),
        "order_not_found": "❌ الطلب غير موجود.",
        "order_self_join": "❌ لا يمكنك الانضمام إلى طلبك الخاص.",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>لقد انضممت إلى الطلب #{order_id}</b></blockquote>\n\n'
            '<blockquote>منشئ الطلب: {seller}</blockquote>\n'
            '<blockquote>المدير المسؤول: @BlumGemes</blockquote>\n\n'
            '<b>مبلغ الطلب:</b> {amount} {currency}\n'
            '<b>وصف الطلب:</b> {description}'
        ),
        "insufficient_funds": "❌ رصيد غير كافٍ. قم بشحن الرصيد عبر الدعم - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>لقد استلمنا دفعتك.</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> هاش المعاملة - {tx_hash}</blockquote>\n\n'
            'لقد أبلغنا البائع. يرجى الانتظار حتى يقوم بنقل الهدية إلى الدعم <b>@BlumGemes</b>'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>المشتري دفع مقابل سلعتك #{order_id}</b>\n\n'
            'الأموال محتجزة في بوتنا حتى يتم نقل البضائع إلى <b>@BlumGemes</b>\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> يرجى نقل جميع البضائع أو الهدايا إلى فريق الدعم لإكمال المعاملة.'
        ),
        "verifying_goods": "جاري التحقق من تسليم البضائع...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>يرجى انتظار إكمال المشتري للطلب.</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>أكد البائع نقل الهدية.</b>\n\n'
            '<b>هل أنت متأكد أنك تريد إغلاق الطلب؟</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>تم إغلاق الطلب بنجاح. تم إرسال الأموال إلى حساب البائع في البوت.</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> كل التوفيق، مع الاحترام، Blum Team'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>تم إيداع الأموال من الطلب #{order_id} في حسابك.</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> حالياً، الأموال محتجزة لمدة 21 يوم عمل.\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> للإفراج، اتصل بالدعم @BlumGemes\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> للمزيد: /freeze_balance'
        ),
        "verification_failed": "لم يتم اكتشاف البضائع أو فشل التحقق.\n\nيرجى التحقق من صحة البضائع أو الهدايا المنقولة والمحاولة مرة أخرى.",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>محافظك.</b>\n\n<b>في هذا القسم يمكنك إضافة أو تغيير تفاصيل المحفظة.</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>محفظة GRAM</b>\n\n<blockquote>الحالي: {}</blockquote>\n\n<i>أرسل عنوان محفظتك الجديد في رسالة واحدة</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>محفظة USDT</b>\n\n<blockquote>الحالي: {}</blockquote>\n\n<i>أرسل عنوان محفظتك الجديد (TRC-20/ERC-20) في رسالة واحدة</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>روبل / تفاصيل P2P</b>\n\n'
            '<blockquote>الحالي: {}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>أرسل التفاصيل:</b>\n'
            '• للروبل — حدد رقم الهاتف ونظام P2P (SBP) واسم البنك\n\n'
            '<b>أمثلة:</b>\n'
            'SBP T-Bank — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>هريفنيا / تفاصيل UAH</b>\n\n<blockquote>الحالي: {}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>أرسل التفاصيل:</b>\n• مونوبانك — رقم البطاقة أو رقم الهاتف\n\n<b>أمثلة:</b>\nمونوبانك — +380 97 123 45-67\nمونوبانك — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>مستلم النجوم الحالي:</b> {}\n\n<b>أدخل مستلم النجوم الجديد:</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>قواعد الأمان الخاصة بنا:</b>\n\n'
            '• يتم شحن الأموال عبر الدعم أو عبر الأزرار في الرصيد.\n'
            '• يتم نقل البضائع بشكل صارم عبر الدعم: @BlumGemes.\n'
            '• وكيل الدعم لن يكتب لك أولاً بشأن شحن الرصيد. هؤلاء محتالون!\n'
            '• لا تشارك أبداً رموز السحب مع الغرباء.'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>وكيل الدعم الفني</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>رابطك:</b>\n\n<code>{link}</code>\n\n<b>احصل على 3% من إنفاق شركائك في بوتنا!</b>',
        "invite_text": (
            '<b>لقد تمت دعوتك إلى الطلب: #{order_id}</b>\n\n'
            '<b>المبلغ:</b> {amount} {currency}\n'
            '<b>السلع:</b>\n'
            '{description}'
        ),
        "btn_share_order": "مشاركة رابط الطلب",
        "btn_support": "الدعم",
        "btn_cancel_order": "إلغاء الطلب",
        "btn_pay_balance": "الدفع من الرصيد",
        "btn_back": "العودة إلى القائمة",
        "btn_item_sent": "لقد أرسلت البضائع",
        "btn_retry_check": "إعادة المحاولة",
        "btn_write_support": "اكتب إلى الدعم",
        "btn_yes": "نعم",
        "btn_no": "لا",
        "balance_updated": "✅ تم شحن رصيدك بمبلغ {} {}",
        "wallets": "المحافظ",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>ملفك الشخصي:</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>رصيد البوت:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>إجمالي الطلبات:</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>الطلبات النشطة:</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>تاريخ التسجيل:</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>معرف المستخدم:</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>اسم المستخدم:</b> <b>@{}</b>\n\n<b>بياناتك مخفية في الطلبات.</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>الأسئلة الشائعة حول استخدام البوت.</b>\n\n<b>1. أوامر البوت.</b>\nالأوامر المتاحة:\n\n<b>/start</b> - يفتح القائمة الرئيسية.\nملاحظة: إذا تم استخدام معلمة الطلب، سيفتح الطلب بدلاً من القائمة.\n\n<b>/language</b> - يفتح قائمة اختيار اللغة\n\n<b>/profile</b> - يفتح ملفك الشخصي\n\n<b>/transfer</b> - يفتح قائمة تحويل الرصيد\n\n<b>1.1 الرصيد.</b>\n\nيتم شحن الرصيد عبر وكيل الدعم: @BlumGemes.\nملاحظة: وكيل الدعم لن يكتب لك أولاً طالباً شحن الرصيد: هذا محتالون!\n\nرصيد البوت يستخدم لدفع الطلبات أو التحويلات بين المستخدمين.\n\nسحب الرصيد متاح فقط بالعملة التي لديك. وكيل الدعم لا يحول العملات. تذكر هذا!\nالحد الأدنى للسحب:\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\nسيتم شحن الرصيد بنفس العملة التي أودعتها.\n\n<b>1.2 تحويل الرصيد.</b>\n\nتحويل الرصيد إلى محتال يلغي رصيد المستلم وسيكون التحويل إليك غير متاح لمدة 7 أيام. عند التكرار ستحصل على حظر تحويل لمدة 30 يوم.\n\nتحويل الرصيد متاح لجميع المستخدمين الذين يستخدمون البوت لأكثر من يوم واحد.\n\nالتحويل متاح أيضاً عبر /transfer',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>تحويل الرصيد بين المستخدمين.</b>\n\n<b>استخدام البوت:</b> {}\n<b>التحويل متاح:</b> {}\n<b>الرصيد المتاح للتحويل:</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>أدخل @username أو userid للتحويل</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>تم العثور على المستخدم @{} (userid: {}).</b>\n\n<b>أدخل المبلغ والعملة للتحويل. مثال: 10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>المستخدم غير موجود في البوت. يرجى دعوته إلى البوت والمحاولة مرة أخرى بعد يوم.</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>رصيد غير كافٍ. راجع الأسئلة الشائعة لشحن الرصيد.</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>تمت العملية #{} بنجاح.</b>\n\n<b>تم إرسال {} {} بنجاح إلى @{}</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>لقد استلمت رصيداً من @{}</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>أدخل تعليقاً للمرسل:</b>\n\n<b>ممنوع: الشتائم، الإهانات، التهديدات.</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>تم إرسال التعليق بنجاح إلى المستخدم.</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>تعليق من @{}:</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>رصيدك:</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "سحب",
        "btn_history": "سجل الرصيد",
        "btn_active_requests": "الطلبات النشطة",
        "btn_request": "الطلب #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>سحب الأموال:</b>\n\nيرجى اختيار العملة للسحب:',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> ليس لديك عملات متاحة للسحب.',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>سجل الرصيد</b>',
        "balance_history_empty": '📭 السجل فارغ.',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>أدخل عنوان GRAM:</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>أدخل عنوان TRC-20:</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>أدخل رقم البطاقة أو رقم الهاتف:</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>أدخل رقم البطاقة أو رقم الهاتف:</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>أدخل مبلغ السحب:</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> المتاح: {balance} {currency}',
        "withdraw_min_amount": "❌ الحد الأدنى للسحب: {min} {currency}",
        "withdraw_insufficient": "❌ رصيد غير كافٍ. المتاح: {balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>تم إرسال الطلب #{request_id}.</b>\n\nفي انتظار المعالجة...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>طلبات السحب النشطة:</b>',
        "active_requests_empty": '📭 لا توجد طلبات نشطة.',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>الطلب #{request_id}</b>\n\n<b>حالة الطلب:</b>\n\n7-11 دقيقة الأولى: التحقق من التفاصيل\n12-21 دقيقة: التحقق من البنك\n22-49 دقيقة: معالجة السحب\n\nإذا كان لديك أي أسئلة، اتصل بالدعم: @BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>تم الموافقة على الطلب.</b>\n\nتم السحب بنجاح: {amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>تم إلغاء طلب السحب الخاص بك.</b>',
        "btn_main_menu": "العودة إلى القائمة",
    },
    "zh": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>欢迎来到我们这里。</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - 一个具有便捷设计和轻松管理的专业平台。</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>我们的优势：</b>\n'
            '• 服务费为0%。\n'
            '• 我们的工作时间为24/7。\n'
            '• 技术支持快速响应。\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>联系方式：</b>\n'
            '• 支持 @BlumGemes。\n'
            '• 频道 @BlumCrypto。'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>手册可以在下面找到，你也可以通过按钮给自己需要的交易内容。</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>地址已更新</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>创建订单</b>\n\n<blockquote>选择买家的支付方式：</blockquote>',
        "wallet_not_bound": '{} <b>{} 钱包未绑定</b>\n\n<i>请先在"钱包"部分添加。</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>订单金额</b>\n\n输入{}金额：\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> 最低：{}</blockquote>',
        "order_min_error": "❌ 最低金额为{}。请重新输入：",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>商品描述</b>\n\n'
            '<blockquote>描述您要出售的商品。</blockquote>\n\n'
            '<blockquote>如果是NFT礼物：\n'
            '前往您的Telegram个人资料 → 点击礼物 → 三个点 (⋯) → "复制链接"。</blockquote>\n\n'
            '在此粘贴链接。如果有多个礼物，请每行指定一个链接。\n\n'
            '示例：\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            '或直接描述资产：2颗水晶和1只蝴蝶'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>订单创建成功</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>金额：</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>描述：</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>买家链接：</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>重要：礼物转移通过经理 @BlumGemes 进行</b></blockquote>'
        ),
        "order_not_found": "❌ 订单未找到。",
        "order_self_join": "❌ 您不能加入自己的订单。",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>您已加入订单 #{order_id}</b></blockquote>\n\n'
            '<blockquote>订单创建者：{seller}</blockquote>\n'
            '<blockquote>负责经理：@BlumGemes</blockquote>\n\n'
            '<b>订单金额：</b> {amount} {currency}\n'
            '<b>订单描述：</b> {description}'
        ),
        "insufficient_funds": "❌ 余额不足。通过支持充值 - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>我们已收到您的付款。</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> 交易哈希 - {tx_hash}</blockquote>\n\n'
            '我们已通知卖家。请等待他们将礼物转移到支持 <b>@BlumGemes</b>'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>买家已支付您的商品 #{order_id}</b>\n\n'
            '资金在我们的机器人中冻结，直到商品转移到 <b>@BlumGemes</b>\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> 请将所有商品或礼物转移给我们的支持团队以完成交易。'
        ),
        "verifying_goods": "正在检查商品交付...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>请等待买家完成订单。</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>卖家已确认礼物转移。</b>\n\n'
            '<b>您确定要关闭订单吗？</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>订单成功关闭。资金已发送到机器人的卖家账户。</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> 祝一切顺利，致以敬意，Blum团队'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>订单 #{order_id} 的资金已存入您的账户。</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> 目前，资金被冻结21个工作日。\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> 要解冻，请联系支持 @BlumGemes\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> 详情：/freeze_balance'
        ),
        "verification_failed": "未检测到商品或验证失败。\n\n请检查转移的商品或礼物的正确性并重试。",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>您的钱包。</b>\n\n<b>在此部分您可以添加或更改钱包详情。</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>GRAM钱包</b>\n\n<blockquote>当前：{}</blockquote>\n\n<i>在一则消息中发送您的新钱包地址</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>USDT钱包</b>\n\n<blockquote>当前：{}</blockquote>\n\n<i>在一则消息中发送您的新钱包地址 (TRC-20/ERC-20)</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>卢布 / P2P详情</b>\n\n'
            '<blockquote>当前：{}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>发送详情：</b>\n'
            '• 对于卢布 — 指定电话号码、P2P系统 (SBP) 和银行名称\n\n'
            '<b>示例：</b>\n'
            'SBP T-Bank — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>格里夫纳 / UAH详情</b>\n\n<blockquote>当前：{}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>发送详情：</b>\n• 莫诺银行 — 卡号或电话号码\n\n<b>示例：</b>\n莫诺银行 — +380 97 123 45-67\n莫诺银行 — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>当前星星接收者：</b> {}\n\n<b>输入新的星星接收者：</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>我们的安全规则：</b>\n\n'
            '• 资金通过支持或余额中的按钮充值。\n'
            '• 商品转移严格通过支持进行：@BlumGemes。\n'
            '• 支持代理永远不会先给您发消息关于充值余额。这是骗子！\n'
            '• 切勿与陌生人分享提现代码。'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>技术支持代理</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>您的链接：</b>\n\n<code>{link}</code>\n\n<b>从您的合作伙伴在机器人中的消费中获得3%！</b>',
        "invite_text": (
            '<b>您被邀请加入订单: #{order_id}</b>\n\n'
            '<b>金额:</b> {amount} {currency}\n'
            '<b>商品:</b>\n'
            '{description}'
        ),
        "btn_share_order": "分享订单链接",
        "btn_support": "支持",
        "btn_cancel_order": "取消订单",
        "btn_pay_balance": "从余额支付",
        "btn_back": "返回菜单",
        "btn_item_sent": "我已发送商品",
        "btn_retry_check": "重试",
        "btn_write_support": "联系支持",
        "btn_yes": "是",
        "btn_no": "否",
        "balance_updated": "✅ 您的余额已充值 {} {}",
        "wallets": "钱包",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>您的个人资料：</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>机器人余额：</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>总订单：</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>活跃订单：</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>注册日期：</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>用户ID：</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>用户名：</b> <b>@{}</b>\n\n<b>您的数据在订单中隐藏。</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>关于使用机器人的常见问题。</b>\n\n<b>1. 机器人命令。</b>\n可用命令：\n\n<b>/start</b> - 打开主菜单。\n注意：如果使用了订单参数，将打开订单而不是菜单。\n\n<b>/language</b> - 打开语言选择菜单\n\n<b>/profile</b> - 打开您的个人资料\n\n<b>/transfer</b> - 打开余额转账菜单\n\n<b>1.1 余额。</b>\n\n余额通过我们的支持代理充值：@BlumGemes。\n注意：支持代理永远不会先给您发消息要求充值余额：这是骗子！\n\n机器人余额用于订单支付或用户之间的转账。\n\n余额提现仅适用于您拥有的货币。支持代理不转换货币。请记住这一点！\n最低提现金额：\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\n余额将以您存入的相同货币充值。\n\n<b>1.2 余额转账。</b>\n\n向骗子转账将取消接收者的余额，并且向您的转账将在7天内不可用。如果重复违规，您将获得30天的转账封锁。\n\n余额转账适用于使用机器人超过一天的所有用户。\n\n转账也可通过 /transfer 进行',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>用户之间的余额转账。</b>\n\n<b>机器人使用时间：</b> {}\n<b>转账可用：</b> {}\n<b>可用于转账的余额：</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>输入 @username 或 userid 进行转账</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>找到用户 @{} (userid: {})。</b>\n\n<b>输入转账金额和货币。示例：10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>在机器人中未找到用户。请邀请他们加入机器人并在一天后重试。</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>余额不足。查看常见问题了解余额充值。</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>操作 #{} 成功。</b>\n\n<b>已成功发送 {} {} 给 @{}</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>您收到了来自 @{} 的余额</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>为发送者输入评论：</b>\n\n<b>禁止：脏话、侮辱、威胁。</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>评论已成功发送给用户。</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>来自 @{} 的评论：</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>您的余额：</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "提现",
        "btn_history": "余额历史",
        "btn_active_requests": "活跃请求",
        "btn_request": "请求 #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>提现：</b>\n\n请选择提现货币：',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> 您没有可提现的货币。',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>余额历史</b>',
        "balance_history_empty": '📭 历史为空。',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>输入GRAM地址：</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>输入TRC-20地址：</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>输入卡号或电话号码：</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>输入卡号或电话号码：</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>输入提现金额：</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> 可用：{balance} {currency}',
        "withdraw_min_amount": "❌ 最低提现金额：{min} {currency}",
        "withdraw_insufficient": "❌ 余额不足。可用：{balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>请求 #{request_id} 已发送。</b>\n\n等待处理...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>活跃提现请求：</b>',
        "active_requests_empty": '📭 没有活跃请求。',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>请求 #{request_id}</b>\n\n<b>请求状态：</b>\n\n前7-11分钟：检查详情\n12-21分钟：银行验证\n22-49分钟：提现处理\n\n如有问题，请联系支持：@BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>请求已批准。</b>\n\n成功提现：{amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>您的提现请求已被取消。</b>',
        "btn_main_menu": "返回菜单",
    },
    "ja": {
        "lang_selection": '<tg-emoji emoji-id="5260512129240276089">🌐</tg-emoji> <b>Choose language:</b>',
        "welcome": (
            '<tg-emoji emoji-id="5938537205847822613">👋</tg-emoji> <b>当社へようこそ。</b>\n\n'
            '<tg-emoji emoji-id="5296742257146241213">🌟</tg-emoji> <b>Blum Gem - 便利なデザインと簡単な管理を備えた専門プラットフォーム。</b>\n\n'
            '<tg-emoji emoji-id="5882207227997066107">⚡</tg-emoji> <b>当社の強み：</b>\n'
            '• サービス手数料は0%です。\n'
            '• 営業時間は24/7です。\n'
            '• テクニカルサポートからの迅速な対応。\n\n'
            '<tg-emoji emoji-id="6039605143601680423">📌</tg-emoji> <b>連絡先：</b>\n'
            '• サポート @BlumGemes。\n'
            '• チャンネル @BlumCrypto。'
        ),
        "admin_team": '<tg-emoji emoji-id="5994297722574737553">📚</tg-emoji> <b>マニュアルは下のボタンから見つけられます。ボタンを使って取引に必要なものを自分に付与することもできます。</b>',
        "wallet_updated": '<tg-emoji emoji-id="5818821611016426346">✅</tg-emoji> <b>アドレスが更新されました</b>',
        "order_creation_title": '<tg-emoji emoji-id="5296420173253727054">📋</tg-emoji> <b>注文作成</b>\n\n<blockquote>買い手の支払い方法を選択：</blockquote>',
        "wallet_not_bound": '{} <b>{} ウォレットがバインドされていません</b>\n\n<i>まず「ウォレット」セクションで追加してください。</i>',
        "order_amount_prompt": '<tg-emoji emoji-id="5845872131090422743">💰</tg-emoji> <b>注文金額</b>\n\n{}で金額を入力：\n\n<blockquote><tg-emoji emoji-id="5294099499344482822">⚠️</tg-emoji> 最小：{}</blockquote>',
        "order_min_error": "❌ 最小金額は{}です。再度入力してください：",
        "order_desc_prompt": (
            '<tg-emoji emoji-id="5296355619895270007">📝</tg-emoji> <b>商品説明</b>\n\n'
            '<blockquote>販売する商品を説明してください。</blockquote>\n\n'
            '<blockquote>NFTギフトの場合：\n'
            'Telegramプロフィールに移動 → ギフトをタップ → 三点（⋯）→ 「リンクをコピー」。</blockquote>\n\n'
            'リンクをここに貼り付けてください。複数のギフトがある場合は、各行にリンクを指定してください。\n\n'
            '例：\n'
            '<blockquote>https://t.me/nft/PlushPepe-1\n'
            'https://t.me/nft/DurovsCap-1</blockquote>\n\n'
            'または資産を説明：クリスタル2個とバタフライ1匹'
        ),
        "order_success": (
            '<tg-emoji emoji-id="5294343891573561212">✨</tg-emoji> <b>注文が正常に作成されました</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5816584452746253634">💵</tg-emoji> <b>金額：</b> {amount} {currency}</blockquote>\n'
            '<blockquote><tg-emoji emoji-id="5816611412255970516">ℹ️</tg-emoji> <b>説明：</b> {description}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816604308380062332">🔗</tg-emoji> <b>買い手へのリンク：</b>\n\n'
            '{link}\n\n'
            '<blockquote><tg-emoji emoji-id="5296420173253727054">⚠️</tg-emoji> <b>重要：ギフトの転送はマネージャー @BlumGemes を通じて行われます</b></blockquote>'
        ),
        "order_not_found": "❌ 注文が見つかりません。",
        "order_self_join": "❌ 自分の注文に参加することはできません。",
        "buyer_joined": (
            '<blockquote><tg-emoji emoji-id="5429356699624426193">🤝</tg-emoji> <b>注文 #{order_id} に参加しました</b></blockquote>\n\n'
            '<blockquote>注文作成者：{seller}</blockquote>\n'
            '<blockquote>責任マネージャー：@BlumGemes</blockquote>\n\n'
            '<b>注文金額：</b> {amount} {currency}\n'
            '<b>注文説明：</b> {description}'
        ),
        "insufficient_funds": "❌ 残高が不足しています。サポートを通じて残高をチャージしてください - @BlumGemes",
        "buyer_paid_success": (
            '<tg-emoji emoji-id="5431438822460121897">📥</tg-emoji> <b>お支払いを受領しました。</b>\n\n'
            '<blockquote><tg-emoji emoji-id="5454200942243112302">🔑</tg-emoji> トランザクションハッシュ - {tx_hash}</blockquote>\n\n'
            '販売者に通知しました。ギフトをサポート <b>@BlumGemes</b> に転送するまでお待ちください。'
        ),
        "seller_notification": (
            '<tg-emoji emoji-id="5386508168849283575">💰</tg-emoji> <b>買い手が商品 #{order_id} の支払いを完了しました</b>\n\n'
            '商品が <b>@BlumGemes</b> に転送されるまで、資金はボットで凍結されます\n\n'
            '<tg-emoji emoji-id="5231415241933357312">📦</tg-emoji> 取引を完了するために、すべての商品またはギフトをサポートチームに転送してください。'
        ),
        "verifying_goods": "商品の配達を確認中...",
        "waiting_for_buyer": (
            '<tg-emoji emoji-id="5879770735999717115">⏳</tg-emoji> <b>買い手が注文を完了するまでお待ちください。</b>'
        ),
        "buyer_close_order": (
            '<tg-emoji emoji-id="5891243564309942507">📢</tg-emoji> <b>販売者がギフトの転送を確認しました。</b>\n\n'
            '<b>注文を閉じてもよろしいですか？</b>'
        ),
        "order_closed_buyer": (
            '<tg-emoji emoji-id="5958376256788502078">✅</tg-emoji> <b>注文が正常に閉じられました。資金はボットの販売者アカウントに送信されました。</b>\n\n'
            '<tg-emoji emoji-id="5899833370052923106">🤝</tg-emoji> ご幸運を、敬意を込めて、Blumチーム'
        ),
        "order_closed_seller": (
            '<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>注文 #{order_id} からの資金がアカウントに入金されました。</b>\n\n'
            '<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> 現在、資金は21営業日間凍結されています。\n\n'
            '<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> 凍結解除には、サポート @BlumGemes にお問い合わせください\n\n'
            '<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> 詳細：/freeze_balance'
        ),
        "verification_failed": "商品が検出されなかったか、検証に失敗しました。\n\n転送された商品またはギフトの正確性を確認して、もう一度お試しください。",
        "wallets_menu_title": '<tg-emoji emoji-id="5424976816530014958">💼</tg-emoji> <b>あなたのウォレット。</b>\n\n<b>このセクションではウォレットの詳細を追加または変更できます。</b>',
        "gram_setup_title": '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji> <b>GRAMウォレット</b>\n\n<blockquote>現在：{}</blockquote>\n\n<i>新しいウォレットアドレスを1つのメッセージで送信</i>',
        "usdt_setup_title": '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji> <b>USDTウォレット</b>\n\n<blockquote>現在：{}</blockquote>\n\n<i>新しいウォレットアドレス（TRC-20/ERC-20）を1つのメッセージで送信</i>',
        "card_setup_title": (
            '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji> <b>ルーブル / P2P詳細</b>\n\n'
            '<blockquote>現在：{}</blockquote>\n\n'
            '<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>詳細を送信：</b>\n'
            '• ルーブルの場合 — 電話番号、P2Pシステム（SBP）、銀行名を指定\n\n'
            '<b>例：</b>\n'
            'SBP T-Bank — +7 912 345-67-89'
        ),
        "uah_setup_title": '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji> <b>フリヴニャ / UAH詳細</b>\n\n<blockquote>現在：{}</blockquote>\n\n<tg-emoji emoji-id="5816671391474259077">📝</tg-emoji> <b>詳細を送信：</b>\n• モノバンク — カード番号または電話番号\n\n<b>例：</b>\nモノバンク — +380 97 123 45-67\nモノバンク — 5168 7520 1234 5678',
        "stars_setup_title": '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji> <b>現在のスター受取人：</b> {}\n\n<b>新しいスター受取人を入力：</b>',
        "safety_rules": (
            '<tg-emoji emoji-id="5276240711795107620">🛡️</tg-emoji> <b>安全ルール：</b>\n\n'
            '• 資金はサポートまたは残高のボタンからチャージされます。\n'
            '• 商品の転送は厳密にサポートを通じて行われます：@BlumGemes。\n'
            '• サポートエージェントが先に残高チャージについて連絡することはありません。これは詐欺師です！\n'
            '• 出金コードを他人と共有しないでください。'
        ),
        "support_title": '<tg-emoji emoji-id="5312325601086956561">👨‍💻</tg-emoji> <b>テクニカルサポートエージェント</b>',
        "referral_title": '<tg-emoji emoji-id="6028171274939797252">🎎</tg-emoji> <b>あなたのリンク：</b>\n\n<code>{link}</code>\n\n<b>ボットでのパートナーの支出から3%を獲得しましょう！</b>',
        "invite_text": (
            '<b>注文に招待されました: #{order_id}</b>\n\n'
            '<b>金額:</b> {amount} {currency}\n'
            '<b>商品:</b>\n'
            '{description}'
        ),
        "btn_share_order": "注文リンクを共有",
        "btn_support": "サポート",
        "btn_cancel_order": "注文をキャンセル",
        "btn_pay_balance": "残高から支払う",
        "btn_back": "メニューに戻る",
        "btn_item_sent": "商品を送信しました",
        "btn_retry_check": "再試行",
        "btn_write_support": "サポートに連絡",
        "btn_yes": "はい",
        "btn_no": "いいえ",
        "balance_updated": "✅ 残高が {} {} チャージされました",
        "wallets": "ウォレット",
        "profile_title": '<tg-emoji emoji-id="5330274342431381948">👤</tg-emoji> <b>プロフィール：</b>\n\n<tg-emoji emoji-id="5312129492880222571">💰</tg-emoji> <b>ボット残高：</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}\n<tg-emoji emoji-id="5312455145890538641">📊</tg-emoji> <b>総注文数：</b> <b>{}</b>\n<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>アクティブな注文：</b> <b>{}</b>\n<tg-emoji emoji-id="5312173623669188535">📅</tg-emoji> <b>登録日：</b> <b>{}</b>\n<tg-emoji emoji-id="5330274342431381948">🆔</tg-emoji> <b>ユーザーID：</b> <b>{}</b>\n<tg-emoji emoji-id="5312167726679092208">👤</tg-emoji> <b>ユーザー名：</b> <b>@{}</b>\n\n<b>データは注文で非表示になります。</b>',
        "faq_title": '<tg-emoji emoji-id="5987565374223159187">📖</tg-emoji> <b>ボット使用に関するFAQ。</b>\n\n<b>1. ボットコマンド。</b>\n利用可能なコマンド：\n\n<b>/start</b> - メインメニューを開きます。\n注意：注文パラメータが使用されている場合、メニューの代わりに注文が開きます。\n\n<b>/language</b> - 言語選択メニューを開きます\n\n<b>/profile</b> - プロフィールを開きます\n\n<b>/transfer</b> - 残高転送メニューを開きます\n\n<b>1.1 残高。</b>\n\n残高はサポートエージェント @BlumGemes を通じてチャージされます。\n注意：サポートエージェントが先に残高チャージを求めてメッセージを送ることはありません：詐欺師です！\n\nボット残高は注文の支払いやユーザー間の転送に使用されます。\n\n残高の引き出しは、お持ちの通貨でのみ可能です。サポートエージェントは通貨を変換しません。これを覚えておいてください！\n最低引き出し金額：\nGram - 5\nUSDT - 5\nRUB - 350\nStars - 300\nUAH - 100\n\n残高は入金したのと同じ通貨でチャージされます。\n\n<b>1.2 残高転送。</b>\n\n詐欺師に残高を転送すると、受取人の残高がキャンセルされ、さらにあなたへの転送が7日間利用できなくなります。違反を繰り返すと、30日間の転送ブロックが適用されます。\n\n残高転送は、ボットを1日以上使用しているすべてのユーザーが利用できます。\n\n転送は /transfer からも利用可能です',
        "transfer_title": '<tg-emoji emoji-id="5312028114472168558">📋</tg-emoji> <b>ユーザー間の残高転送。</b>\n\n<b>ボット利用期間：</b> {}\n<b>転送可能：</b> {}\n<b>転送可能な残高：</b>\nGram: {}\nUSDT: {}\nRUB: {}\nStars: {}\nUAH: {}',
        "transfer_choose": '<tg-emoji emoji-id="5312508996190495880">📝</tg-emoji> <b>転送先の @username または userid を入力</b>',
        "transfer_found": '<tg-emoji emoji-id="5312401587648359164">✅</tg-emoji> <b>ユーザー @{} (userid: {}) が見つかりました。</b>\n\n<b>転送する金額と通貨を入力してください。例：10 usdt</b>',
        "transfer_not_found": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>ボット内にユーザーが見つかりません。ボットに招待して、1日後に再試行してください。</b>',
        "transfer_insufficient": '<tg-emoji emoji-id="5312508996190495880">❌</tg-emoji> <b>残高が不足しています。残高チャージについてはFAQをご覧ください。</b>',
        "transfer_success": '<tg-emoji emoji-id="5312011303970170399">✅</tg-emoji> <b>操作 #{} が成功しました。</b>\n\n<b>{} {} が @{} に正常に送信されました</b>',
        "transfer_received": '<tg-emoji emoji-id="5312508996190495880">📥</tg-emoji> <b>@{} から残高を受信しました</b>\n\n<b>{} {}</b>',
        "transfer_comment_prompt": '<tg-emoji emoji-id="5312325601086956561">✍️</tg-emoji> <b>送信者へのコメントを入力：</b>\n\n<b>禁止：悪口、侮辱、脅迫。</b>',
        "transfer_comment_success": '<tg-emoji emoji-id="5312325601086956561">✅</tg-emoji> <b>コメントがユーザーに正常に送信されました。</b>',
        "transfer_comment_received": '<tg-emoji emoji-id="5312325601086956561">💬</tg-emoji> <b>@{} からのコメント：</b>\n\n{}',
        "balance_title": '<tg-emoji emoji-id="5974217466270716579">💰</tg-emoji> <b>残高：</b>\n\n• Stars: {stars}\n• Gram: {gram}\n• Usdt: {usdt}\n• Rub: {rub}\n• Uah: {uah}',
        "btn_withdraw": "出金",
        "btn_history": "残高履歴",
        "btn_active_requests": "アクティブなリクエスト",
        "btn_request": "リクエスト #{request_id}",
        "balance_withdraw": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>出金：</b>\n\n出金する通貨を選択してください：',
        "balance_no_withdraw": '<tg-emoji emoji-id="5278578973595427038">❌</tg-emoji> 出金可能な通貨がありません。',
        "balance_history_title": '<tg-emoji emoji-id="5276395476646653290">📊</tg-emoji> <b>残高履歴</b>',
        "balance_history_empty": '📭 履歴は空です。',
        "balance_history_item": '<tg-emoji emoji-id="5276229330131772747">📌</tg-emoji> {text}',
        "withdraw_enter_gram": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>GRAMアドレスを入力：</b>',
        "withdraw_enter_usdt": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>TRC-20アドレスを入力：</b>',
        "withdraw_enter_rub": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>カード番号または電話番号を入力：</b>',
        "withdraw_enter_uah": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>カード番号または電話番号を入力：</b>',
        "withdraw_amount_prompt": '<tg-emoji emoji-id="5278413853577734640">💰</tg-emoji> <b>出金額を入力：</b>\n\n<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> 利用可能：{balance} {currency}',
        "withdraw_min_amount": "❌ 最低出金額：{min} {currency}",
        "withdraw_insufficient": "❌ 残高が不足しています。利用可能：{balance} {currency}",
        "withdraw_success": '<tg-emoji emoji-id="5278753302023004775">💸</tg-emoji> <b>リクエスト #{request_id} を送信しました。</b>\n\n処理をお待ちください...',
        "active_requests": '<tg-emoji emoji-id="5206476089127372379">📋</tg-emoji> <b>アクティブな出金リクエスト：</b>',
        "active_requests_empty": '📭 アクティブなリクエストはありません。',
        "request_details": '<tg-emoji emoji-id="5276395476646653290">📋</tg-emoji> <b>リクエスト #{request_id}</b>\n\n<b>リクエストステータス：</b>\n\n最初の7-11分：詳細確認\n12-21分：銀行検証\n22-49分：出金処理\n\nご質問がある場合は、サポートまでお問い合わせください：@BlumGemes',
        "withdraw_approved": '<tg-emoji emoji-id="6039486778597970865">✅</tg-emoji> <b>リクエストが承認されました。</b>\n\n正常に出金されました：{amount} {currency}',
        "withdraw_rejected": '<tg-emoji emoji-id="5276384644739129761">❌</tg-emoji> <b>出金リクエストはキャンセルされました。</b>',
        "btn_main_menu": "メニューに戻る",
    }
}

class WalletStates(StatesGroup):
    waiting_for_gram_address = State()
    waiting_for_usdt_address = State()
    waiting_for_card_sbp = State()
    waiting_for_stars_recipient = State()
    waiting_for_uah_requisites = State()

class OrderStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()

class AdminStates(StatesGroup):
    waiting_for_balance = State()
    waiting_for_deals_count = State()

class TransferStates(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_amount_currency = State()
    waiting_for_comment = State()

class WithdrawStates(StatesGroup):
    waiting_for_currency = State()
    waiting_for_address = State()
    waiting_for_amount = State()

def load_db():
    global db
    print(f"[DEBUG] Ищу файл: {os.path.abspath(DB_FILE)}")
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                db = pickle.load(f)
            print(f"[DEBUG] Файл загружен, пользователей: {len(db)}")
        except Exception as e:
            print(f"[DEBUG] Ошибка загрузки: {e}")
            db = {}
    else:
        print(f"[DEBUG] Файл не найден, создаю новый")
        db = {}
        save_db()

def save_db():
    try:
        with open(DB_FILE, "wb") as f:
            pickle.dump(db, f)
        print(f"[DEBUG] Файл сохранен в: {os.path.abspath(DB_FILE)}")
        print(f"[DEBUG] Размер: {os.path.getsize(DB_FILE)} байт")
    except Exception as e:
        print(f"[DEBUG] ОШИБКА СОХРАНЕНИЯ: {e}")

def generate_code(length=7) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def register_user(user_id: int, username: str = None):
    if user_id not in db:
        db[user_id] = {
            "lang": "ru",
            "ref_code": generate_code(8),
            "gram_wallet": "не указан",
            "card_wallet": "не указан",
            "usdt_wallet": "не указан",
            "stars_wallet": "не указан",
            "uah_wallet": "не указан",
            "username": username or f"id{user_id}",
            "balance_gram": 0.0,
            "balance_rub": 0.0,
            "balance_usdt": 0.0,
            "balance_stars": 0.0,
            "balance_uah": 0.0,
            "referrer_id": None,
            "deals_count": 0,
            "register_date": datetime.now().strftime("%d.%m.%Y | %H:%M:%S"),
            "transfer_blocked_until": None,
            "transfer_violations": 0,
            "agreed_to_terms": False,
            "lang_set": False,
            "frozen_balance": {},
            "history": [],
            "withdrawals": []
        }
    else:
        if "lang" not in db[user_id]: db[user_id]["lang"] = "ru"
        if "balance_gram" not in db[user_id]: db[user_id]["balance_gram"] = 0.0
        if "balance_rub" not in db[user_id]: db[user_id]["balance_rub"] = 0.0
        if "balance_usdt" not in db[user_id]: db[user_id]["balance_usdt"] = 0.0
        if "balance_stars" not in db[user_id]: db[user_id]["balance_stars"] = 0.0
        if "balance_uah" not in db[user_id]: db[user_id]["balance_uah"] = 0.0
        if "gram_wallet" not in db[user_id]: db[user_id]["gram_wallet"] = "не указан"
        if "card_wallet" not in db[user_id]: db[user_id]["card_wallet"] = "не указан"
        if "usdt_wallet" not in db[user_id]: db[user_id]["usdt_wallet"] = "не указан"
        if "stars_wallet" not in db[user_id]: db[user_id]["stars_wallet"] = "не указан"
        if "uah_wallet" not in db[user_id]: db[user_id]["uah_wallet"] = "не указан"
        if "referrer_id" not in db[user_id]: db[user_id]["referrer_id"] = None
        if "deals_count" not in db[user_id]: db[user_id]["deals_count"] = 0
        if "register_date" not in db[user_id]: db[user_id]["register_date"] = datetime.now().strftime("%d.%m.%Y | %H:%M:%S")
        if "transfer_blocked_until" not in db[user_id]: db[user_id]["transfer_blocked_until"] = None
        if "transfer_violations" not in db[user_id]: db[user_id]["transfer_violations"] = 0
        if "agreed_to_terms" not in db[user_id]: db[user_id]["agreed_to_terms"] = False
        if "lang_set" not in db[user_id]: db[user_id]["lang_set"] = False
        if "frozen_balance" not in db[user_id]: db[user_id]["frozen_balance"] = {}
        if "history" not in db[user_id]: db[user_id]["history"] = []
        if "withdrawals" not in db[user_id]: db[user_id]["withdrawals"] = []
        if username: db[user_id]["username"] = username

def get_lang(user_id: int) -> str:
    return db.get(user_id, {}).get("lang", "ru")

active_orders = {}

async def safe_delete(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass

async def show_language_selection(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    user_id = message.from_user.id
    lang = get_lang(user_id)
    
    builder.row(
        PremiumButton(text="Русский", emoji_id="5449408995691341691", callback_data="set_lang_ru", style="primary"),
        PremiumButton(text="English", emoji_id="5202021044105257611", callback_data="set_lang_en", style="primary"),
        PremiumButton(text="Indonesia", emoji_id="5291937150814661333", callback_data="set_lang_id", style="primary")
    )
    builder.row(
        PremiumButton(text="中文", emoji_id="5431782733376399004", callback_data="set_lang_zh", style="primary"),
        PremiumButton(text="日本語", emoji_id="5456261908069885892", callback_data="set_lang_ja", style="primary"),
        PremiumButton(text="عربي", emoji_id="5226476858471626962", callback_data="set_lang_ar", style="primary")
    )
    
    await message.answer(
        text=TEXTS[lang]["lang_selection"],
        reply_markup=builder.as_markup()
    )

async def show_worker_panel(message: types.Message, lang: str):
    builder = InlineKeyboardBuilder()
    
    builder.row(
        PremiumButton(
            text="Ссылка на тиму (актуал)",
            emoji_id="5877465816030515018",
            url="https://t.me/+Zi3cR-N-5q43YjVh",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text="Выдача баланса",
            emoji_id="5987880246865565644",
            callback_data="admin_give_balance",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text="Парсер",
            emoji_id="5875465628285931233",
            callback_data="admin_parser",
            style="primary"
        ),
        PremiumButton(
            text="Накрутка сделок",
            emoji_id="5985433648810171091",
            callback_data="admin_deals_fake",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text="Мануал",
            emoji_id="5931415565955503486",
            callback_data="show_manual",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text="Скрыть",
            emoji_id="5877540355187937244",
            callback_data="hide_panel",
            style="danger"
        )
    )
    
    await message.answer(
        text=TEXTS[lang]["admin_team"],
        reply_markup=builder.as_markup()
    )

async def show_balance_menu(message: types.Message, edit: bool = False):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    user = db[user_id]
    
    print(f"[DEBUG] ПОКАЗ БАЛАНСА: rub={user.get('balance_rub', 0)}")
    
    text = TEXTS[lang]["balance_title"].format(
        stars=user.get("balance_stars", 0),
        gram=user.get("balance_gram", 0),
        usdt=user.get("balance_usdt", 0),
        rub=user.get("balance_rub", 0),
        uah=user.get("balance_uah", 0)
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_withdraw"],
            emoji_id="5846097080002550195",
            callback_data="balance_withdraw",
            style="success"
        ),
        PremiumButton(
            text=TEXTS[lang]["btn_history"],
            emoji_id="5775896410780079073",
            callback_data="balance_history",
            style="primary"
        )
    )
    
    if user.get("withdrawals"):
        builder.row(
            PremiumButton(
                text=TEXTS[lang]["btn_active_requests"],
                emoji_id="5206476089127372379",
                callback_data="active_requests",
                style="primary"
            )
        )
    
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    
    if edit:
        await message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    else:
        await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "balance")
async def process_balance(callback: types.CallbackQuery):
    await callback.answer()
    await show_balance_menu(callback.message, edit=True)

@dp.callback_query(lambda call: call.data == "back_to_main")
async def process_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    await callback.message.edit_text(
        text=TEXTS[lang]["welcome"],
        reply_markup=get_main_keyboard(lang),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "balance_withdraw")
async def balance_withdraw(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    user = db[user_id]
    
    builder = InlineKeyboardBuilder()
    has_currency = False
    
    if user.get("balance_gram", 0) > 0:
        builder.row(PremiumButton(
            text="GRAM",
            emoji_id="5193179982775476271",
            callback_data="withdraw_currency_gram",
            style="primary"
        ))
        has_currency = True
    
    if user.get("balance_usdt", 0) > 0:
        builder.row(PremiumButton(
            text="USDT",
            emoji_id="5255933397750014894",
            callback_data="withdraw_currency_usdt",
            style="primary"
        ))
        has_currency = True
    
    if user.get("balance_rub", 0) > 0:
        builder.row(PremiumButton(
            text="RUB",
            emoji_id="5255806447106679302",
            callback_data="withdraw_currency_rub",
            style="primary"
        ))
        has_currency = True
    
    if user.get("balance_uah", 0) > 0:
        builder.row(PremiumButton(
            text="UAH",
            emoji_id="5255787742524103649",
            callback_data="withdraw_currency_uah",
            style="primary"
        ))
        has_currency = True
    
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_balance",
            style="primary"
        )
    )
    
    if not has_currency:
        await callback.message.edit_text(
            text=TEXTS[lang]["balance_no_withdraw"],
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.edit_text(
            text=TEXTS[lang]["balance_withdraw"],
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )

@dp.callback_query(lambda call: call.data == "back_to_balance")
async def back_to_balance(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await show_balance_menu(callback.message, edit=True)

@dp.callback_query(lambda call: call.data.startswith("withdraw_currency_"))
async def withdraw_currency_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    currency = callback.data.replace("withdraw_currency_", "")
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    
    await state.update_data(withdraw_currency=currency)
    
    if currency == "gram":
        text = TEXTS[lang]["withdraw_enter_gram"]
    elif currency == "usdt":
        text = TEXTS[lang]["withdraw_enter_usdt"]
    elif currency == "rub":
        text = TEXTS[lang]["withdraw_enter_rub"]
    elif currency == "uah":
        text = TEXTS[lang]["withdraw_enter_uah"]
    else:
        text = "❌ Неизвестная валюта"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_withdraw",
            style="primary"
        )
    )
    
    await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await state.set_state(WithdrawStates.waiting_for_address)

@dp.callback_query(lambda call: call.data == "back_to_withdraw")
async def back_to_withdraw(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await balance_withdraw(callback, state)

@dp.message(WithdrawStates.waiting_for_address)
async def withdraw_address_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    address = message.text.strip()
    
    data = await state.get_data()
    currency = data.get("withdraw_currency")
    
    await state.update_data(withdraw_address=address)
    
    balance_key = f"balance_{currency}"
    balance = db[user_id].get(balance_key, 0)
    
    text = TEXTS[lang]["withdraw_amount_prompt"].format(
        balance=balance,
        currency=currency.upper()
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_withdraw",
            style="primary"
        )
    )
    
    await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await state.set_state(WithdrawStates.waiting_for_amount)

@dp.message(WithdrawStates.waiting_for_amount)
async def withdraw_amount_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число")
        return
    
    data = await state.get_data()
    currency = data.get("withdraw_currency")
    address = data.get("withdraw_address")
    
    balance_key = f"balance_{currency}"
    balance = db[user_id].get(balance_key, 0)
    
    min_amounts = {"gram": 5, "usdt": 5, "rub": 350, "uah": 100}
    min_amount = min_amounts.get(currency, 5)
    
    if amount < min_amount:
        await message.answer(TEXTS[lang]["withdraw_min_amount"].format(min=min_amount, currency=currency.upper()))
        return
    
    if amount > balance:
        await message.answer(TEXTS[lang]["withdraw_insufficient"].format(balance=balance, currency=currency.upper()))
        return
    
    request_id = generate_code(6)
    
    db[user_id][balance_key] -= amount
    
    history_entry = f"Заявка на вывод [ {amount} {currency.upper()} ]"
    if "history" not in db[user_id]:
        db[user_id]["history"] = []
    db[user_id]["history"].append(history_entry)
    
    withdraw_request = {
        "id": request_id,
        "currency": currency,
        "amount": amount,
        "address": address,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    if "withdrawals" not in db[user_id]:
        db[user_id]["withdrawals"] = []
    db[user_id]["withdrawals"].append(withdraw_request)
    
    save_db()
    
    await state.clear()
    
    try:
        username = db[user_id].get("username", str(user_id))
        log_text = (
            f'<tg-emoji emoji-id="5881806211195605908">📤</tg-emoji> <b>Новая заявка на вывод</b>\n\n'
            f'Сумма: {amount} {currency.upper()}\n'
            f'Адрес: {address}\n'
            f'Пользователь: @{username} (ID: {user_id})'
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            PremiumButton(
                text="Принять",
                callback_data=f"withdraw_approve_{request_id}_{user_id}_{currency}_{amount}",
                style="success"
            ),
            PremiumButton(
                text="Отклонить",
                callback_data=f"withdraw_reject_{request_id}_{user_id}",
                style="danger"
            )
        )
        
        await bot.send_message(
            chat_id=WITHDRAW_LOG_ID,
            text=log_text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"[DEBUG] Ошибка отправки лога: {e}")
    
    text = TEXTS[lang]["withdraw_success"].format(request_id=request_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_balance",
            style="primary"
        )
    )
    
    await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data.startswith("withdraw_approve_"))
async def withdraw_approve(callback: types.CallbackQuery):
    await callback.answer()
    
    parts = callback.data.split("_")
    request_id = parts[2]
    user_id = int(parts[3])
    currency = parts[4]
    amount = float(parts[5])
    
    lang = get_lang(user_id)
    
    withdrawals = db[user_id].get("withdrawals", [])
    for w in withdrawals:
        if w.get("id") == request_id:
            w["status"] = "approved"
            break
    
    save_db()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_main_menu"],
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=TEXTS[lang]["withdraw_approved"].format(amount=amount, currency=currency.upper()),
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"[DEBUG] Ошибка уведомления: {e}")
    
    await callback.message.edit_text(
        text=callback.message.text + "\n\n✅ <b>Заявка одобрена</b>",
        parse_mode=ParseMode.HTML
    )
    
    await callback.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda call: call.data.startswith("withdraw_reject_"))
async def withdraw_reject(callback: types.CallbackQuery):
    await callback.answer()
    
    parts = callback.data.split("_")
    request_id = parts[2]
    user_id = int(parts[3])
    
    lang = get_lang(user_id)
    
    withdrawals = db[user_id].get("withdrawals", [])
    for w in withdrawals:
        if w.get("id") == request_id:
            w["status"] = "rejected"
            break
    
    save_db()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_main_menu"],
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=TEXTS[lang]["withdraw_rejected"],
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"[DEBUG] Ошибка уведомления: {e}")
    
    await callback.message.edit_text(
        text=callback.message.text + "\n\n❌ <b>Заявка отклонена</b>",
        parse_mode=ParseMode.HTML
    )
    
    await callback.message.edit_reply_markup(reply_markup=None)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except:
            pass
    
    register_user(message.from_user.id, message.from_user.username)
    
    if referrer_id and referrer_id != message.from_user.id:
        if referrer_id in db:
            if db[message.from_user.id].get("referrer_id") is None:
                db[message.from_user.id]["referrer_id"] = referrer_id
                save_db()
    
    if len(args) > 1 and args[1].startswith("deal_"):
        order_id = args[1].replace("deal_", "")
        if order_id in active_orders:
            await handle_join_order(message, order_id)
            return

    user_id = message.from_user.id
    
    if not db[user_id].get("lang_set", False):
        await show_language_selection(message)
    else:
        lang = get_lang(user_id)
        await message.answer(text=TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await show_language_selection(message)

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    user = db[user_id]
    
    total_orders = user["deals_count"]
    active_orders_count = sum(1 for order in active_orders.values() if order["seller_id"] == user_id or order.get("buyer_id") == user_id)
    username = user.get("username", str(user_id))
    
    await message.answer(
        text=TEXTS[lang]["profile_title"].format(
            user.get("balance_gram", 0),
            user.get("balance_usdt", 0),
            user.get("balance_rub", 0),
            user.get("balance_stars", 0),
            user.get("balance_uah", 0),
            total_orders,
            active_orders_count,
            user["register_date"],
            user_id,
            username
        ),
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("transfer"))
async def cmd_transfer(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    user = db[user_id]
    
    register_date = datetime.strptime(user["register_date"], "%d.%m.%Y | %H:%M:%S")
    days_used = (datetime.now() - register_date).days
    hours_used = (datetime.now() - register_date).seconds // 3600
    
    if days_used >= 1:
        time_used = f"{days_used} дней" if days_used > 1 else "1 день"
    else:
        time_used = f"{hours_used} часов" if hours_used > 0 else "менее часа"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_pay_balance"],
            emoji_id="5312011303970170399",
            callback_data="transfer_yes",
            style="primary"
        ),
        PremiumButton(
            text="❌ Отказаться" if lang == "ru" else "❌ Cancel" if lang == "en" else "❌ Batal" if lang == "id" else "❌ إلغاء" if lang == "ar" else "❌ 取消" if lang == "zh" else "❌ キャンセル",
            callback_data="transfer_no",
            style="danger"
        )
    )
    
    yes_text = "Да" if lang == "ru" else "Yes" if lang == "en" else "Ya" if lang == "id" else "نعم" if lang == "ar" else "是" if lang == "zh" else "はい"
    
    await message.answer(
        text=TEXTS[lang]["transfer_title"].format(
            time_used, 
            yes_text,
            user.get("balance_gram", 0),
            user.get("balance_usdt", 0),
            user.get("balance_rub", 0),
            user.get("balance_stars", 0),
            user.get("balance_uah", 0)
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("rocket"))
async def cmd_rocket(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    
    if db[user_id].get("agreed_to_terms", False):
        await show_worker_panel(message, lang)
        return
    
    text = (
        '<tg-emoji emoji-id="5465618910936072194">📢</tg-emoji> <b>В связи со сносами Тимы, приняты меры использовать мануал в самом боте.</b>\n\n'
        '<b>Принимая условия вы соглашаетесь с:</b>\n'
        '<i>Мануалы публикуются только в боте.</i>'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text="Принимаю",
            emoji_id="5467852517268290519",
            callback_data="accept_terms",
            style="success"
        ),
        PremiumButton(
            text="Отклоняю",
            emoji_id="5326056199215406977",
            callback_data="decline_terms",
            style="danger"
        )
    )
    
    await message.answer(text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.message(Command("add_freeze_balance"))
async def cmd_add_freeze_balance(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.answer(
                "❌ Неверный формат команды.\n\n"
                "Использование: /add_freeze_balance <username или userid> <сумма> <валюта>\n\n"
                "Примеры:\n"
                "/add_freeze_balance @test 13 gram\n"
                "/add_freeze_balance 123456789 50 usdt\n"
                "/add_freeze_balance @user 100 uah"
            )
            return
        
        target_input = parts[1]
        amount = float(parts[2])
        currency = parts[3].lower()
        
        target_user_id = None
        target_username = None
        
        if target_input.startswith("@"):
            username = target_input[1:]
            for uid, data in db.items():
                if data.get("username", "").lower() == username.lower():
                    target_user_id = uid
                    target_username = data.get("username")
                    break
        else:
            try:
                target_user_id = int(target_input)
                if target_user_id in db:
                    target_username = db[target_user_id].get("username", str(target_user_id))
            except ValueError:
                await message.answer("❌ Неверный формат userid. Используйте число.")
                return
        
        if not target_user_id or target_user_id not in db:
            await message.answer(f"❌ Пользователь {target_input} не найден в базе данных.")
            return
        
        currency_map = {
            "gram": "balance_gram",
            "rub": "balance_rub",
            "usdt": "balance_usdt",
            "stars": "balance_stars",
            "uah": "balance_uah"
        }
        
        if currency not in currency_map:
            await message.answer("❌ Доступные валюты: gram, rub, usdt, stars, uah")
            return
        
        bal_key = currency_map[currency]
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        
        db[target_user_id][bal_key] = db[target_user_id].get(bal_key, 0.0) + amount
        save_db()
        
        await message.answer(
            f"✅ Баланс успешно добавлен!\n\n"
            f"👤 Пользователь: @{target_username} (ID: {target_user_id})\n"
            f"💰 Сумма: {amount} {currency.upper()}\n"
            f"📊 Текущий баланс: {db[target_user_id][bal_key]} {currency.upper()}"
        )
        
        user_lang = get_lang(target_user_id)
        
        freeze_text = (
            f'<tg-emoji emoji-id="5832546462478635761">💰</tg-emoji> <b>На счёт поступили средства с последнего ордера</b>\n\n'
            f'<b>Сумма:</b> {amount} {currency.upper()}\n\n'
            f'<tg-emoji emoji-id="5775887550262546277">⏳</tg-emoji> <b>На данный момент средства заморожены на 21 рабочий день.</b>\n\n'
            f'<tg-emoji emoji-id="5884510167986343350">📞</tg-emoji> <b>Для разморозки напишите в поддержку @BlumGemes</b>\n\n'
            f'<tg-emoji emoji-id="5931409969613116639">ℹ️</tg-emoji> <b>Подробнее:</b> /freeze_balance'
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            PremiumButton(
                text="ℹ️ Подробнее" if user_lang == "ru" else "ℹ️ More details",
                callback_data="show_freeze_info",
                style="primary"
            )
        )
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=freeze_text,
                reply_markup=builder.as_markup(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await message.answer(f"⚠️ Не удалось отправить уведомление пользователю: {e}")
        
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")

@dp.message(Command("freeze_balance"))
async def cmd_freeze_balance(message: types.Message):
    lang = get_lang(message.from_user.id)
    
    info_text = (
        '<b>📖 Информация о заморозке средств</b>\n\n'
        '<b>Почему средства заморожены?</b>\n'
        'Средства замораживаются на 21 рабочий день для обеспечения безопасности сделки и защиты от мошенничества.\n\n'
        '<b>Как разморозить средства?</b>\n'
        'Для разморозки средств напишите в поддержку @BlumGemes и укажите ID ордера.\n\n'
        '<b>Когда средства будут доступны?</b>\n'
        'Средства будут разморожены после проверки сделки или по истечении 21 рабочего дня.\n\n'
        '<b>Контакты поддержки:</b>\n'
        '@BlumGemes - служба поддержки'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text="👨‍💻 Написать в поддержку" if lang == "ru" else "👨‍💻 Contact support",
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    builder.row(
        PremiumButton(
            text="🔙 Назад" if lang == "ru" else "🔙 Back",
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    
    await message.answer(
        text=info_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "show_freeze_info")
async def show_freeze_info(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    
    info_text = (
        '<b>📖 Информация о заморозке средств</b>\n\n'
        '<b>Почему средства заморожены?</b>\n'
        'Средства замораживаются на 21 рабочий день для обеспечения безопасности сделки и защиты от мошенничества.\n\n'
        '<b>Как разморозить средства?</b>\n'
        'Для разморозки средств напишите в поддержку @BlumGemes и укажите ID ордера.\n\n'
        '<b>Когда средства будут доступны?</b>\n'
        'Средства будут разморожены после проверки сделки или по истечении 21 рабочего дня.\n\n'
        '<b>Контакты поддержки:</b>\n'
        '@BlumGemes - служба поддержки'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text="👨‍💻 Написать в поддержку" if lang == "ru" else "👨‍💻 Contact support",
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    builder.row(
        PremiumButton(
            text="🔙 Назад" if lang == "ru" else "🔙 Back",
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    
    await callback.message.edit_text(
        text=info_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data.startswith("set_lang_"))
async def process_set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    selected_lang = callback.data.replace("set_lang_", "")
    
    register_user(user_id)
    db[user_id]["lang"] = selected_lang
    db[user_id]["lang_set"] = True
    save_db()
    
    alert_msgs = {
        "ru": "Язык изменен на Русский!",
        "en": "Language changed to English!",
        "id": "Bahasa diubah ke Indonesia!",
        "ar": "تم تغيير اللغة إلى العربية!",
        "zh": "语言已更改为中文！",
        "ja": "言語が日本語に変更されました！"
    }
    
    await callback.answer(alert_msgs.get(selected_lang, "Language changed!"), show_alert=True)
    
    await safe_delete(callback)
    await callback.message.answer(
        text=TEXTS[selected_lang]["welcome"],
        reply_markup=get_main_keyboard(selected_lang),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "transfer_no")
async def transfer_no(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    lang = get_lang(callback.from_user.id)
    await callback.message.edit_text(text=TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "transfer_yes")
async def transfer_yes(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    
    await callback.message.edit_text(text=TEXTS[lang]["transfer_choose"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(TransferStates.waiting_for_recipient)

@dp.message(TransferStates.waiting_for_recipient)
async def transfer_recipient_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    input_text = message.text.strip()
    
    if input_text.startswith("@"):
        username = input_text[1:]
    else:
        username = input_text
    
    target_user_id = None
    for uid, data in db.items():
        if data.get("username", "").lower() == username.lower():
            target_user_id = uid
            break
        if str(uid) == username:
            target_user_id = uid
            break
    
    if not target_user_id:
        await message.answer(text=TEXTS[lang]["transfer_not_found"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
        await state.clear()
        return
    
    if target_user_id == user_id:
        await message.answer("❌ Вы не можете перевести средства самому себе.", reply_markup=get_back_keyboard(lang))
        await state.clear()
        return
    
    await state.update_data(target_user_id=target_user_id, target_username=username)
    await message.answer(
        text=TEXTS[lang]["transfer_found"].format(username, target_user_id),
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TransferStates.waiting_for_amount_currency)

@dp.message(TransferStates.waiting_for_amount_currency)
async def transfer_amount_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    
    try:
        parts = message.text.lower().split()
        if len(parts) != 2:
            await message.answer("❌ Неверный формат. Используйте: 10 usdt")
            return
        
        amount = float(parts[0])
        currency = parts[1]
        
        data = await state.get_data()
        target_user_id = data.get("target_user_id")
        target_username = data.get("target_username")
        
        if not target_user_id:
            await message.answer("❌ Ошибка. Попробуйте начать перевод заново.", reply_markup=get_back_keyboard(lang))
            await state.clear()
            return
        
        currency_map = {
            "gram": "balance_gram",
            "rub": "balance_rub",
            "usdt": "balance_usdt",
            "stars": "balance_stars",
            "uah": "balance_uah"
        }
        
        if currency not in currency_map:
            await message.answer("❌ Доступные валюты: gram, rub, usdt, stars, uah")
            return
        
        bal_key = currency_map[currency]
        
        if db[user_id].get(bal_key, 0) < amount:
            await message.answer(text=TEXTS[lang]["transfer_insufficient"], reply_markup=get_back_keyboard(lang))
            await state.clear()
            return
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        
        code = generate_code(8)
        
        db[user_id][bal_key] -= amount
        db[target_user_id][bal_key] = db[target_user_id].get(bal_key, 0) + amount
        save_db()
        
        await message.answer(
            text=TEXTS[lang]["transfer_success"].format(code, amount, currency.upper(), target_username),
            reply_markup=get_back_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        
        receiver_lang = get_lang(target_user_id)
        receiver_builder = InlineKeyboardBuilder()
        receiver_builder.row(
            PremiumButton(
                text="Хорошо, спасибо!",
                callback_data=f"transfer_thanks_{user_id}",
                style="success"
            )
        )
        receiver_builder.row(
            PremiumButton(
                text="Отправить комментарий отправителю",
                callback_data=f"transfer_comment_{user_id}",
                style="primary"
            )
        )
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=TEXTS[receiver_lang]["transfer_received"].format(
                    db[user_id].get("username", str(user_id)),
                    amount,
                    currency.upper()
                ),
                reply_markup=receiver_builder.as_markup(),
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число.")

@dp.callback_query(lambda call: call.data.startswith("transfer_thanks_"))
async def transfer_thanks(callback: types.CallbackQuery):
    await callback.answer("Спасибо!")
    await callback.message.delete()

@dp.callback_query(lambda call: call.data.startswith("transfer_comment_"))
async def transfer_comment_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    sender_id = int(callback.data.replace("transfer_comment_", ""))
    await state.update_data(sender_id=sender_id)
    lang = get_lang(callback.from_user.id)
    await callback.message.edit_text(
        text=TEXTS[lang]["transfer_comment_prompt"],
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TransferStates.waiting_for_comment)

@dp.message(TransferStates.waiting_for_comment)
async def transfer_comment_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    comment = message.text.strip()
    
    forbidden_words = ["мат", "оскорбление", "угроза", "хуй", "пизда", "бля", "сука", "нахуй", "ебать"]
    
    if any(word in comment.lower() for word in forbidden_words):
        await message.delete()
        await message.answer("❌ Ваш комментарий содержит запрещённые слова. Попробуйте снова.", reply_markup=get_back_keyboard(lang))
        return
    
    data = await state.get_data()
    sender_id = data.get("sender_id")
    
    if not sender_id:
        await message.answer("❌ Ошибка. Попробуйте снова.", reply_markup=get_back_keyboard(lang))
        await state.clear()
        return
    
    sender_lang = get_lang(sender_id)
    
    try:
        await bot.send_message(
            chat_id=sender_id,
            text=TEXTS[sender_lang]["transfer_comment_received"].format(
                db[user_id].get("username", str(user_id)),
                comment
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    
    await message.answer(
        text=TEXTS[lang]["transfer_comment_success"],
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )
    await state.clear()

@dp.message(lambda message: message.text in [
    "📋 Создать ордер", "📋 Create Order",
    "💼 Кошельки", "💼 Wallets",
    "🛡️ Безопасность", "🛡️ Safety",
    "🎎 Рефералы", "🎎 Referrals",
    "👨‍💻 Поддержка", "👨‍💻 Support",
    "🌐 Язык", "🌐 Language"
])
async def cmd_main_menu_buttons(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    text = message.text

    if text in ["📋 Создать ордер", "📋 Create Order"]:
        await message.answer(text=TEXTS[lang]["order_creation_title"], reply_markup=get_create_order_keyboard(lang), parse_mode=ParseMode.HTML)
    elif text in ["💼 Кошельки", "💼 Wallets"]:
        await message.answer(text=TEXTS[lang]["wallets_menu_title"], reply_markup=get_wallets_management_keyboard(lang), parse_mode=ParseMode.HTML)
    elif text in ["🛡️ Безопасность", "🛡️ Safety"]:
        await message.answer(text=TEXTS[lang]["safety_rules"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    elif text in ["🎎 Рефералы", "🎎 Referrals"]:
        ref_code = db[user_id]["ref_code"]
        bot_user = await bot.get_me()
        link = f"https://t.me/{bot_user.username}?start=ref_{ref_code}"
        await message.answer(
            text=TEXTS[lang]["referral_title"].format(link=link),
            reply_markup=get_back_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
    elif text in ["👨‍💻 Поддержка", "👨‍💻 Support"]:
        builder = InlineKeyboardBuilder()
        builder.row(PremiumButton(
            text=TEXTS[lang]["btn_write_support"],
            emoji_id="5312325601086956561",
            url="https://t.me/BlumGemes",
            style="primary"
        ))
        builder.row(PremiumButton(
            text=TEXTS[lang]["btn_back"],
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        ))
        await message.answer(text=TEXTS[lang]["support_title"], reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    elif text in ["🌐 Язык", "🌐 Language"]:
        await show_language_selection(message)

@dp.callback_query(lambda call: call.data == "warning_show")
async def process_warning_show(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    await callback.message.answer(text=TEXTS[lang]["order_creation_title"], reply_markup=get_create_order_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "open_safety")
async def process_open_safety(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    await callback.message.answer(text=TEXTS[lang]["safety_rules"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "open_referrals")
async def process_open_referrals(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    ref_code = db[user_id]["ref_code"]
    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start=ref_{ref_code}"
    
    await safe_delete(callback)
    await callback.message.answer(
        text=TEXTS[lang]["referral_title"].format(link=link),
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "open_support")
async def process_open_support(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(PremiumButton(
        text=TEXTS[lang]["btn_write_support"],
        emoji_id="5312325601086956561",
        url="https://t.me/BlumGemes",
        style="primary"
    ))
    builder.row(PremiumButton(
        text=TEXTS[lang]["btn_back"],
        emoji_id="5875082500023258804",
        callback_data="back_to_main",
        style="primary"
    ))
    await callback.message.answer(text=TEXTS[lang]["support_title"], reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "open_wallets")
async def process_open_wallets(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    await callback.message.answer(text=TEXTS[lang]["wallets_menu_title"], reply_markup=get_wallets_management_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "open_language")
async def process_open_language(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(text="Русский", emoji_id="5449408995691341691", callback_data="set_lang_ru", style="primary"),
        PremiumButton(text="English", emoji_id="5202021044105257611", callback_data="set_lang_en", style="primary"),
        PremiumButton(text="Indonesia", emoji_id="5291937150814661333", callback_data="set_lang_id", style="primary")
    )
    builder.row(
        PremiumButton(text="中文", emoji_id="5431782733376399004", callback_data="set_lang_zh", style="primary"),
        PremiumButton(text="日本語", emoji_id="5456261908069885892", callback_data="set_lang_ja", style="primary"),
        PremiumButton(text="عربي", emoji_id="5226476858471626962", callback_data="set_lang_ar", style="primary")
    )
    await callback.message.answer(text=TEXTS[lang]["lang_selection"], reply_markup=builder.as_markup())

@dp.callback_query(lambda call: call.data == "open_faq")
async def process_open_faq(callback: types.CallbackQuery):
    await callback.answer()
    await safe_delete(callback)
    lang = get_lang(callback.from_user.id)
    await callback.message.answer(text=TEXTS[lang]["faq_title"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data.startswith("pay_select_"))
async def process_pay_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    selected_currency = callback.data.replace("pay_select_", "").upper()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    
    wallet_keys = {
        "GRAM": ("gram_wallet", "не указан", '<tg-emoji emoji-id="5280809324342451667">🪙</tg-emoji>'),
        "USDT": ("usdt_wallet", "не указан", '<tg-emoji emoji-id="5814556334829343625">🪙</tg-emoji>'),
        "CARD": ("card_wallet", "не указан", '<tg-emoji emoji-id="5265074015868822600">💳</tg-emoji>'),
        "STARS": ("stars_wallet", "не указан", '<tg-emoji emoji-id="5463289097336405244">⭐</tg-emoji>'),
        "UAH": ("uah_wallet", "не указан", '<tg-emoji emoji-id="5312537023665893498">🇺🇦</tg-emoji>')
    }
    
    db_key, empty_val, emoji = wallet_keys[selected_currency]
    user_wallet = db[user_id].get(db_key, empty_val)
    
    if user_wallet == empty_val or not user_wallet.strip():
        await safe_delete(callback)
        display_name = "Rubles" if selected_currency == "CARD" and lang=="en" else ("Рубли" if selected_currency == "CARD" else selected_currency)
        if selected_currency == "UAH":
            display_name = "Hryvnia" if lang=="en" else "Гривны"
        await callback.message.answer(
            text=TEXTS[lang]["wallet_not_bound"].format(emoji, display_name),
            reply_markup=get_back_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        return

    await safe_delete(callback)
    
    display_names = {
        "GRAM": "GRAM",
        "USDT": "USDT",
        "CARD": "рублях" if lang == "ru" else "rubles",
        "STARS": "STARS",
        "UAH": "гривнах" if lang == "ru" else "hryvnia"
    }
    display_currency = display_names.get(selected_currency, selected_currency)
    
    limits_display = {
        "GRAM": 1.5,
        "USDT": 1.2,
        "CARD": 50,
        "STARS": 50,
        "UAH": 100
    }
    min_display = limits_display.get(selected_currency, 2)
    
    await callback.message.answer(
        text=TEXTS[lang]["order_amount_prompt"].format(display_currency, min_display),
        reply_markup=get_back_keyboard(lang),
        parse_mode=ParseMode.HTML
    )
    await state.update_data(chosen_currency=selected_currency)
    await state.set_state(OrderStates.waiting_for_amount)

@dp.message(OrderStates.waiting_for_amount)
async def order_amount_handler(message: types.Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    try:
        amount = float(message.text)
        data = await state.get_data()
        selected_currency = data.get("chosen_currency", "GRAM")
        
        limits = {"GRAM": 1.5, "USDT": 1.2, "CARD": 50, "STARS": 50, "UAH": 100}
        
        min_amount = limits.get(selected_currency, 2)
        
        if amount < min_amount:
            await message.answer(TEXTS[lang]["order_min_error"].format(min_amount))
            return
        
        await state.update_data(order_amount=amount)
        await message.answer(text=TEXTS[lang]["order_desc_prompt"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
        await state.set_state(OrderStates.waiting_for_description)
    except ValueError:
        await message.answer("❌ Invalid digit/Неверное число:")

@dp.message(OrderStates.waiting_for_description)
async def order_description_handler(message: types.Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    user_id = message.from_user.id
    register_user(user_id)
    
    data = await state.get_data()
    amount = data.get("order_amount")
    currency = data.get("chosen_currency")
    description = message.text
    
    order_id = generate_code(6)
    
    active_orders[order_id] = {
        "seller_id": user_id,
        "amount": amount,
        "currency": currency,
        "description": description,
        "buyer_id": None,
        "status": "waiting"
    }
    
    bot_user = await bot.get_me()
    deal_link = f"https://t.me/{bot_user.username}?start=deal_{order_id}"
    
    if currency == "CARD":
        display_currency = "Rubles" if lang=="en" else "Рубли"
    elif currency == "UAH":
        display_currency = "Hryvnia" if lang=="en" else "Гривны"
    else:
        display_currency = currency
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        types.InlineKeyboardButton(
            text=TEXTS[lang]["btn_share_order"], 
            switch_inline_query=f"deal_{order_id}"
        )
    )
    
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_write_support"],
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_cancel_order"],
            callback_data=f"cancel_{order_id}",
            style="danger"
        )
    )
    
    await message.answer(
        text=TEXTS[lang]["order_success"].format(
            amount=amount,
            currency=display_currency,
            description=description,
            link=deal_link
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await state.clear()

@dp.callback_query(lambda call: call.data.startswith("cancel_"))
async def process_cancel_order(callback: types.CallbackQuery):
    await callback.answer()
    order_id = callback.data.replace("cancel_", "")
    lang = get_lang(callback.from_user.id)
    
    if order_id in active_orders:
        del active_orders[order_id]
        await callback.message.edit_text(
            text=f"❌ <b>Ордер #{order_id} отменен</b>",
            reply_markup=get_back_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(TEXTS[lang]["order_not_found"])

@dp.callback_query(lambda call: call.data.startswith("share_"))
async def process_share_order(callback: types.CallbackQuery):
    await callback.answer()
    order_id = callback.data.replace("share_", "")
    order = active_orders.get(order_id)
    
    if not order:
        await callback.message.answer(TEXTS[get_lang(callback.from_user.id)]["order_not_found"])
        return
    
    lang = get_lang(callback.from_user.id)
    bot_user = await bot.get_me()
    deal_link = f"https://t.me/{bot_user.username}?start=deal_{order_id}"
    
    seller_info = db.get(order["seller_id"], {})
    seller_username = f"@{seller_info.get('username')}" if seller_info.get('username') else f"id{order['seller_id']}"
    
    if order["currency"] == "CARD":
        display_currency = "Rubles" if lang=="en" else "Рубли"
    elif order["currency"] == "UAH":
        display_currency = "Hryvnia" if lang=="en" else "Гривны"
    else:
        display_currency = order["currency"]
    
    invite_text = TEXTS[lang]["invite_text"].format(
        order_id=order_id,
        amount=order["amount"],
        currency=display_currency,
        description=order["description"]
    )
    
    builder = InlineKeyboardBuilder()
    btn_join = "🔗 Присоединиться" if lang == "ru" else "🔗 Join Order"
    builder.row(types.InlineKeyboardButton(text=btn_join, url=deal_link))
    
    try:
        photo_path = "order/join.jpg"
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=photo,
                    caption=invite_text,
                    reply_markup=builder.as_markup(),
                    parse_mode=ParseMode.HTML
                )
        else:
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=invite_text,
                reply_markup=builder.as_markup(),
                parse_mode=ParseMode.HTML
            )
    except Exception:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=invite_text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    
    await callback.answer("✅ Ссылка отправлена в текущий чат!")

async def handle_join_order(message: types.Message, order_id: str):
    lang = get_lang(message.from_user.id)
    order = active_orders.get(order_id)
    if not order:
        await message.answer(TEXTS[lang]["order_not_found"])
        return
        
    if order["seller_id"] == message.from_user.id:
        await message.answer(TEXTS[lang]["order_self_join"])
        return
        
    order["buyer_id"] = message.from_user.id
        
    seller_info = db.get(order["seller_id"], {})
    seller_username = f"@{seller_info.get('username')}" if seller_info.get('username') else f"id{order['seller_id']}"
    buyer_username = message.from_user.username or f"id{message.from_user.id}"
    
    buyer_deals = db.get(message.from_user.id, {}).get("deals_count", 0)
    
    if order["currency"] == "CARD":
        display_currency = "Rubles" if lang=="en" else "Рубли"
    elif order["currency"] == "UAH":
        display_currency = "Hryvnia" if lang=="en" else "Гривны"
    else:
        display_currency = order["currency"]
    
    if order["currency"] == "CARD":
        display_currency_log = "рублей" if lang=="ru" else "rubles"
    elif order["currency"] == "UAH":
        display_currency_log = "гривен" if lang=="ru" else "hryvnia"
    else:
        display_currency_log = order["currency"]
    
    await send_admin_log("buyer_joined", {
        "id": order_id,
        "seller": seller_username,
        "buyer": buyer_username,
        "amount": order["amount"],
        "currency": display_currency_log,
        "description": order["description"]
    })
    
    seller_notification = (
        f'<tg-emoji emoji-id="5465237148472991488">📢</tg-emoji> <b>Покупатель присоединился к вашей сделке #{order_id}</b>\n\n'
        f'<tg-emoji emoji-id="5409318572654615628">⏳</tg-emoji> На данный момент мы ожидаем оплату от покупателя, как только всё будет готово - мы уведомим вас.\n\n'
        f'<tg-emoji emoji-id="5384245567192849959">⭐</tg-emoji> Успешных сделок у покупателя: {buyer_deals}'
    )
    
    seller_builder = InlineKeyboardBuilder()
    seller_builder.row(
        PremiumButton(
            text="Поддержка",
            emoji_id="5409260990028077429",
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    
    try:
        await bot.send_message(
            chat_id=order["seller_id"],
            text=seller_notification,
            reply_markup=seller_builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    
    formatted_join = TEXTS[lang]["buyer_joined"].format(
        order_id=order_id, 
        seller=seller_username, 
        amount=order["amount"], 
        currency=display_currency, 
        description=order["description"]
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(PremiumButton(text=TEXTS[lang]["btn_pay_balance"], callback_data=f"balpay_{order_id}", style="primary"))
    builder.row(PremiumButton(text=TEXTS[lang]["btn_back"], callback_data="back_to_main", style="primary"))
    await message.answer(text=formatted_join, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data.startswith("balpay_"))
async def process_balance_payment(callback: types.CallbackQuery):
    await callback.answer()
    buyer_id = callback.from_user.id
    lang = get_lang(buyer_id)
    
    order_id = callback.data.replace("balpay_", "")
    order = active_orders.get(order_id)
    
    if not order:
        await callback.message.answer(TEXTS[lang]["order_not_found"])
        return
        
    if order.get("status") == "paid":
        await callback.message.answer("❌ Этот ордер уже оплачен.")
        return
        
    register_user(buyer_id)
    
    currency_balance_keys = {
        "GRAM": "balance_gram",
        "USDT": "balance_usdt",
        "CARD": "balance_rub",
        "STARS": "balance_stars",
        "UAH": "balance_uah"
    }
    
    bal_key = currency_balance_keys.get(order["currency"], "balance_gram")
    buyer_bal = db[buyer_id].get(bal_key, 0.0)
    
    if buyer_bal < order["amount"]:
        await callback.message.answer(TEXTS[lang]["insufficient_funds"])
        return
        
    db[buyer_id][bal_key] -= order["amount"]
    order["status"] = "paid"
    
    history_entry = f"Оплата с баланса. [ {order['amount']} {order['currency']} из Ордер #{order_id} ]"
    if "history" not in db[buyer_id]:
        db[buyer_id]["history"] = []
    db[buyer_id]["history"].append(history_entry)
    
    save_db()
    
    tx_hash = generate_code(7)
    
    formatted_buyer = TEXTS[lang]["buyer_paid_success"].format(tx_hash=tx_hash)
    await safe_delete(callback)
    await callback.message.answer(text=formatted_buyer, parse_mode=ParseMode.HTML)
    
    s_lang = get_lang(order["seller_id"])
    formatted_seller = TEXTS[s_lang]["seller_notification"].format(order_id=order_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[s_lang]["btn_item_sent"], 
            callback_data=f"selldone_{order_id}_{buyer_id}", 
            style="primary"
        )
    )
    
    try:
        await bot.send_message(
            chat_id=order["seller_id"], 
            text=formatted_seller, 
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"❌ Ошибка отправки продавцу: {e}")

@dp.callback_query(lambda call: call.data.startswith("selldone_"))
async def process_seller_transfer(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    
    parts = callback.data.split("_")
    order_id = parts[1]
    buyer_id = int(parts[2])
    
    order = active_orders.get(order_id)
    
    if not order:
        await callback.message.answer(TEXTS[lang]["order_not_found"])
        return
    
    msg = await callback.message.answer(TEXTS[lang]["verifying_goods"])
    await asyncio.sleep(10)
    
    seller_info = db.get(callback.from_user.id, {})
    seller_username = seller_info.get("username", f"id{callback.from_user.id}")
    buyer_info = db.get(buyer_id, {})
    buyer_username = buyer_info.get("username", f"id{buyer_id}")
    description = order.get("description", "не указано") if order else "не указано"
    
    await send_admin_log("gift_in_support", {
        "seller": seller_username,
        "buyer": buyer_username,
        "description": description
    })
    
    await msg.edit_text(TEXTS[lang]["waiting_for_buyer"])
    
    buyer_lang = get_lang(buyer_id)
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[buyer_lang]["btn_yes"],
            callback_data=f"close_order_yes_{order_id}_{callback.from_user.id}",
            style="primary"
        ),
        PremiumButton(
            text=TEXTS[buyer_lang]["btn_no"],
            callback_data=f"close_order_no_{order_id}",
            style="primary"
        )
    )
    
    try:
        await bot.send_message(
            chat_id=buyer_id,
            text=TEXTS[buyer_lang]["buyer_close_order"],
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

@dp.callback_query(lambda call: call.data.startswith("close_order_yes_"))
async def close_order_yes(callback: types.CallbackQuery):
    await callback.answer()
    
    parts = callback.data.split("_")
    order_id = parts[3]
    seller_id = int(parts[4])
    
    lang = get_lang(callback.from_user.id)
    seller_lang = get_lang(seller_id)
    buyer_id = callback.from_user.id
    
    order = active_orders.get(order_id)
    
    if order:
        currency_balance_keys = {
            "GRAM": "balance_gram",
            "USDT": "balance_usdt",
            "CARD": "balance_rub",
            "STARS": "balance_stars",
            "UAH": "balance_uah"
        }
        seller_bal_key = currency_balance_keys.get(order["currency"], "balance_gram")
        db[seller_id][seller_bal_key] = db[seller_id].get(seller_bal_key, 0.0) + order["amount"]
        save_db()
        
        history_entry = f"Поступление {order['amount']} {order['currency']}. [ Ордер #{order_id} ]"
        if "history" not in db[seller_id]:
            db[seller_id]["history"] = []
        db[seller_id]["history"].append(history_entry)
        save_db()
        
        del active_orders[order_id]
    
    await callback.message.edit_text(TEXTS[lang]["order_closed_buyer"], parse_mode=ParseMode.HTML)
    
    try:
        await bot.send_message(
            chat_id=seller_id,
            text=TEXTS[seller_lang]["order_closed_seller"].format(order_id=order_id),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

@dp.callback_query(lambda call: call.data.startswith("close_order_no_"))
async def close_order_no(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    order_id = callback.data.replace("close_order_no_", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text=TEXTS[lang]["btn_support"],
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    
    no_text = "❌ Вы отменили закрытие ордера. Если у вас возникли вопросы, обратитесь в поддержку."
    if lang == "en":
        no_text = "❌ You cancelled order closing. If you have questions, contact support."
    elif lang == "id":
        no_text = "❌ Anda membatalkan penutupan pesanan. Jika ada pertanyaan, hubungi dukungan."
    elif lang == "ar":
        no_text = "❌ لقد ألغيت إغلاق الطلب. إذا كان لديك أسئلة، اتصل بالدعم."
    elif lang == "zh":
        no_text = "❌ 您取消了订单关闭。如有问题，请联系支持。"
    elif lang == "ja":
        no_text = "❌ 注文のクローズをキャンセルしました。ご質問がある場合は、サポートにお問い合わせください。"
    
    await callback.message.edit_text(
        text=no_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "wallet_setup_gram")
async def process_wallet_setup_gram(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    current_wallet = db[user_id].get("gram_wallet", "не указан")
    
    await safe_delete(callback)
    await callback.message.answer(text=TEXTS[lang]["gram_setup_title"].format(current_wallet), reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(WalletStates.waiting_for_gram_address)

@dp.message(WalletStates.waiting_for_gram_address)
async def save_gram_address_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    db[user_id]["gram_wallet"] = message.text
    save_db()
    
    await message.answer(text=TEXTS[lang]["wallet_updated"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(lambda call: call.data == "wallet_setup_usdt")
async def process_wallet_setup_usdt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    current_wallet = db[user_id].get("usdt_wallet", "не указан")
    
    await safe_delete(callback)
    await callback.message.answer(text=TEXTS[lang]["usdt_setup_title"].format(current_wallet), reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(WalletStates.waiting_for_usdt_address)

@dp.message(WalletStates.waiting_for_usdt_address)
async def save_usdt_address_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    db[user_id]["usdt_wallet"] = message.text
    save_db()
    
    await message.answer(text=TEXTS[lang]["wallet_updated"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(lambda call: call.data == "wallet_setup_sbp")
async def process_wallet_setup_sbp(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    current_wallet = db[user_id].get("card_wallet", "не указан")
    
    await safe_delete(callback)
    await callback.message.answer(text=TEXTS[lang]["card_setup_title"].format(current_wallet), reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(WalletStates.waiting_for_card_sbp)

@dp.message(WalletStates.waiting_for_card_sbp)
async def save_card_sbp_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    db[user_id]["card_wallet"] = message.text
    save_db()
    
    await message.answer(text=TEXTS[lang]["wallet_updated"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(lambda call: call.data == "wallet_setup_uah")
async def process_wallet_setup_uah(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    current_wallet = db[user_id].get("uah_wallet", "не указан")
    
    await safe_delete(callback)
    await callback.message.answer(text=TEXTS[lang]["uah_setup_title"].format(current_wallet), reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(WalletStates.waiting_for_uah_requisites)

@dp.message(WalletStates.waiting_for_uah_requisites)
async def save_uah_requisites_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    db[user_id]["uah_wallet"] = message.text
    save_db()
    
    await message.answer(text=TEXTS[lang]["wallet_updated"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(lambda call: call.data == "wallet_setup_stars")
async def process_wallet_setup_stars(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    current_wallet = db[user_id].get("stars_wallet", "не указан")
    
    await safe_delete(callback)
    await callback.message.answer(text=TEXTS[lang]["stars_setup_title"].format(current_wallet), reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.set_state(WalletStates.waiting_for_stars_recipient)

@dp.message(WalletStates.waiting_for_stars_recipient)
async def save_stars_recipient_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    register_user(user_id)
    lang = get_lang(user_id)
    
    new_username = message.text.strip()
    if new_username.startswith("@"):
        new_username = new_username[1:]
        
    db[user_id]["stars_wallet"] = new_username
    save_db()
    
    await message.answer(text=TEXTS[lang]["wallet_updated"], reply_markup=get_back_keyboard(lang), parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(lambda call: call.data == "accept_terms")
async def accept_terms(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    
    db[user_id]["agreed_to_terms"] = True
    save_db()
    
    await callback.message.delete()
    await show_worker_panel(callback.message, lang)

@dp.callback_query(lambda call: call.data == "decline_terms")
async def decline_terms(callback: types.CallbackQuery):
    await callback.answer("❌ Вы отклонили условия", show_alert=True)
    lang = get_lang(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(text=TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "hide_panel")
async def hide_panel(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(text=TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda call: call.data == "show_manual")
async def show_manual(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    
    manual_text = (
        '<b>📖 Мануал пока что будет в боте.</b>\n\n'
        '<b>Причины чтобы завести мамонта на бота:</b>\n\n'
        '<b>1. Популярность</b>\n'
        'У бота 20к+ пользователей, не думаю что каждый будет пользоваться Скам ботом (моноширный формат)\n\n'
        '<b>2. Активный канал</b>\n'
        'плюсом активный канал @blumcrypto, с такой аудиторией навряд ли будут обманывать (моноширный)\n\n'
        '<b>1.1 Поиск мамонта и типов</b>\n'
        'Типов можете найти в нашем парсере, а также в чате nft_chatfrog / see.tg , маркет ТГ\n\n'
        '<b>1.2 завод на бота</b>\n'
        'выше предоставлены все аргументы, по возможности добавляйте сами\n\n'
        '<b>1.3 выдача балика и сделок</b>\n'
        '/rocket все показано\n\n'
        '<b>1.4 просите создать сделку оплачиваете ее и просите передать подарок в поддержку</b>\n\n'
        'всё'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text="Назад",
            emoji_id="5875082500023258804",
            callback_data="back_to_worker_panel",
            style="primary"
        )
    )
    
    await callback.message.edit_text(
        text=manual_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "back_to_worker_panel")
async def back_to_worker_panel(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    await show_worker_panel(callback.message, lang)

@dp.callback_query(lambda call: call.data == "admin_give_balance")
async def admin_give_balance_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        text="<b>Выбери валюту и сумму для пополнения.</b>\n\n"
             '📌 100 gram\n'
             '📌 100 rub\n'
             '📌 100 usdt\n'
             '📌 100 stars\n'
             '📌 100 uah\n'
             '📌 100 all (выдача баланса который может оплачивать в сделках любую валюту)',
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AdminStates.waiting_for_balance)

@dp.message(AdminStates.waiting_for_balance)
async def admin_process_balance(message: types.Message, state: FSMContext):
    try:
        parts = message.text.lower().split()
        if len(parts) != 2:
            await message.answer("❌ Неверный формат. Пример: 100 gram")
            await state.clear()
            return
            
        amount = float(parts[0])
        currency = parts[1]
        
        user_id = message.from_user.id
        register_user(user_id)
        
        for key in ["balance_gram", "balance_rub", "balance_usdt", "balance_stars", "balance_uah"]:
            if key not in db[user_id]:
                db[user_id][key] = 0.0
        
        print(f"[DEBUG] До изменения: balance_rub = {db[user_id].get('balance_rub', 0)}")
        
        if currency == "gram":
            db[user_id]["balance_gram"] += amount
        elif currency in ["rub", "card"]:
            db[user_id]["balance_rub"] += amount
        elif currency == "usdt":
            db[user_id]["balance_usdt"] += amount
        elif currency == "stars":
            db[user_id]["balance_stars"] += amount
        elif currency == "uah":
            db[user_id]["balance_uah"] += amount
        elif currency == "all":
            db[user_id]["balance_gram"] += amount
            db[user_id]["balance_rub"] += amount
            db[user_id]["balance_usdt"] += amount
            db[user_id]["balance_stars"] += amount
            db[user_id]["balance_uah"] += amount
        else:
            await message.answer("❌ Доступные валюты: gram, rub, usdt, stars, uah, all")
            await state.clear()
            return
        
        print(f"[DEBUG] После изменения: balance_rub = {db[user_id]['balance_rub']}")
        
        save_db()
        
        print(f"[DEBUG] После save_db: balance_rub = {db[user_id]['balance_rub']}")
        
        await message.answer(f"✅ Вам установлено {amount} {currency.upper()}")
        
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()

@dp.callback_query(lambda call: call.data == "admin_parser")
async def admin_parser(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    
    parser_text = (
        '<tg-emoji emoji-id="5875465628285931233">🔗</tg-emoji> <b>актуальный приватный парсер:</b>\n\n'
        'https://t.me/+Ino2HL0Nnd8yMDNh\n'
        '(принимаю того кого захочу)'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        PremiumButton(
            text="Назад" if lang == "ru" else "Back",
            emoji_id="5875082500023258804",
            callback_data="back_to_worker_panel",
            style="primary"
        )
    )
    
    await callback.message.edit_text(
        text=parser_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(lambda call: call.data == "admin_deals_fake")
async def admin_deals_fake_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = get_lang(callback.from_user.id)
    
    await callback.message.edit_text(
        text="<b>Введите количество сделок:</b>",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AdminStates.waiting_for_deals_count)

@dp.message(AdminStates.waiting_for_deals_count)
async def admin_process_deals_fake(message: types.Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        user_id = message.from_user.id
        
        if user_id not in db:
            register_user(user_id)
        
        db[user_id]["deals_count"] = count
        save_db()
        
        await message.answer(f"✅ Вам установлено {count} успешных сделок!")
    except Exception:
        await message.answer("❌ Неверный формат. Введите число.")
    finally:
        await state.clear()

@dp.inline_query(lambda q: q.query.startswith("deal_"))
async def inline_deal_handler(inline_query: types.InlineQuery):
    order_id = inline_query.query.replace("deal_", "")
    order = active_orders.get(order_id)
    if not order:
        return
        
    lang = get_lang(inline_query.from_user.id)
    bot_user = await bot.get_me()
    deal_link = f"https://t.me/{bot_user.username}?start=deal_{order_id}"
    
    if order["currency"] == "CARD":
        display_currency = "Rubles" if lang=="en" else "Рубли"
    elif order["currency"] == "UAH":
        display_currency = "Hryvnia" if lang=="en" else "Гривны"
    else:
        display_currency = order["currency"]
    
    builder = InlineKeyboardBuilder()
    btn_join = "🔗 Join Order" if lang == "en" else "🔗 Присоединиться к ордеру"
    builder.row(types.InlineKeyboardButton(text=btn_join, url=deal_link))
    
    title_text = f"Order #{order_id}" if lang=="en" else f"Ордер #{order_id}"
    desc_text = f"Amount: {order['amount']} {display_currency}" if lang=="en" else f"Сумма: {order['amount']} {display_currency}"
    
    msg_text = (
        f"🤝 <b>You have been invited to join order #{order_id}!</b>\n\n"
        f"💵 <b>Amount:</b> {order['amount']} {display_currency}\n"
        f"📦 <b>Items:</b>\n{order['description']}\n\n"
        f"📥 Click the button below to view details."
        if lang == "en" else
        f"🤝 <b>Вас пригласили присоединиться к ордеру #{order_id}!</b>\n\n"
        f"💵 <b>Сумма сделки:</b> {order['amount']} {display_currency}\n"
        f"📦 <b>Товары:</b>\n{order['description']}\n\n"
        f"📥 Нажмите на кнопку ниже, чтобы узнать детали и продолжить."
    )
    
    results = [
        types.InlineQueryResultArticle(
            id=order_id,
            title=title_text,
            description=desc_text,
            input_message_content=types.InputTextMessageContent(message_text=msg_text, parse_mode=ParseMode.HTML),
            reply_markup=builder.as_markup()
        )
    ]
    await inline_query.answer(results, is_personal=True, cache_time=1)

async def main():
    load_db()
    print("Бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())