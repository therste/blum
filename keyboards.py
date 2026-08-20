# keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class PremiumButton(InlineKeyboardButton):
    def __init__(self, text: str, emoji_id: str = None, callback_data: str = None, url: str = None, style: str = "default"):
        super().__init__(
            text=text,
            callback_data=callback_data,
            url=url,
            icon_custom_emoji_id=emoji_id
        )
        self.style = style

def get_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    texts = {
        "create_order": {"ru": "Создать ордер", "en": "Create order", "id": "Buat Pesanan", "ar": "إنشاء طلب", "zh": "创建订单", "ja": "注文を作成"},
        "balance": {"ru": "Баланс", "en": "Balance", "id": "Saldo", "ar": "الرصيد", "zh": "余额", "ja": "残高"},
        "wallets": {"ru": "Кошельки", "en": "Wallets", "id": "Dompet", "ar": "المحافظ", "zh": "钱包", "ja": "ウォレット"},
        "rules": {"ru": "Правила", "en": "Rules", "id": "Aturan", "ar": "القواعد", "zh": "规则", "ja": "ルール"},
        "referrals": {"ru": "Рефералы", "en": "Referrals", "id": "Referral", "ar": "الإحالات", "zh": "推荐", "ja": "紹介"},
        "channel": {"ru": "Канал", "en": "Channel", "id": "Saluran", "ar": "القناة", "zh": "频道", "ja": "チャンネル"},
        "support": {"ru": "Агент поддержки", "en": "Support Agent", "id": "Agen Dukungan", "ar": "وكيل الدعم", "zh": "支持代理", "ja": "サポートエージェント"},
        "language": {"ru": "Язык", "en": "Language", "id": "Bahasa", "ar": "اللغة", "zh": "语言", "ja": "言語"},
        "faq": {"ru": "F.A.Q", "en": "F.A.Q", "id": "F.A.Q", "ar": "الأسئلة الشائعة", "zh": "常见问题", "ja": "F.A.Q"},
    }
    
    builder.row(
        PremiumButton(
            text=texts["create_order"].get(lang, "Создать ордер"),
            emoji_id="5983399041197675256",
            callback_data="warning_show",
            style="success"
        )
    )
    
    builder.row(
        PremiumButton(
            text=texts["balance"].get(lang, "Баланс"),
            emoji_id="5778311685638984859",
            callback_data="balance",
            style="primary"
        ),
        PremiumButton(
            text=texts["wallets"].get(lang, "Кошельки"),
            emoji_id="5769126056262898415",
            callback_data="open_wallets",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text=texts["rules"].get(lang, "Правила"),
            emoji_id="5778299625370817409",
            callback_data="open_safety",
            style="primary"
        ),
        PremiumButton(
            text=texts["referrals"].get(lang, "Рефералы"),
            emoji_id="5877465816030515018",
            callback_data="open_referrals",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text=texts["channel"].get(lang, "Канал"),
            emoji_id="5938252440926163756",
            url="https://t.me/BlumCrypto",
            style="primary"
        ),
        PremiumButton(
            text=texts["support"].get(lang, "Агент поддержки"),
            emoji_id="5988023995125993550",
            url="https://t.me/BlumGemes",
            style="primary"
        )
    )
    
    builder.row(
        PremiumButton(
            text=texts["language"].get(lang, "Язык"),
            emoji_id="5778184941154078090",
            callback_data="open_language",
            style="primary"
        ),
        PremiumButton(
            text=texts["faq"].get(lang, "F.A.Q"),
            emoji_id="5467461928647399673",
            callback_data="open_faq",
            style="primary"
        )
    )
    
    return builder.as_markup()

def get_back_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    texts = {
        "back": {"ru": "Вернутся в меню", "en": "Back to menu", "id": "Kembali ke menu", "ar": "العودة إلى القائمة", "zh": "返回菜单", "ja": "メニューに戻る"}
    }
    btn_back_text = texts["back"].get(lang, "Вернутся в меню")
    builder.row(
        PremiumButton(
            text=btn_back_text,
            emoji_id="5875082500023258804",
            callback_data="back_to_main",
            style="primary"
        )
    )
    return builder.as_markup()

def get_create_order_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    texts = {
        "rubles": {"ru": "Рубли", "en": "Rubles", "id": "Rubel", "ar": "روبل", "zh": "卢布", "ja": "ルーブル"},
        "uah": {"ru": "Гривны", "en": "Hryvnia", "id": "Hryvnia", "ar": "هريفنيا", "zh": "格里夫纳", "ja": "フリヴニャ"},
        "back": {"ru": "Вернутся в меню", "en": "Back to menu", "id": "Kembali ke menu", "ar": "العودة إلى القائمة", "zh": "返回菜单", "ja": "メニューに戻る"}
    }
    btn_card_text = texts["rubles"].get(lang, "Рубли")
    btn_uah_text = texts["uah"].get(lang, "Гривны")
    btn_back_text = texts["back"].get(lang, "Вернутся в меню")
    
    builder.row(
        PremiumButton(text="GRAM", emoji_id="5280809324342451667", callback_data="pay_select_gram", style="primary"),
        PremiumButton(text="USDT", emoji_id="5814556334829343625", callback_data="pay_select_usdt", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_card_text, emoji_id="5265074015868822600", callback_data="pay_select_card", style="primary"),
        PremiumButton(text="STARS", emoji_id="5463289097336405244", callback_data="pay_select_stars", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_uah_text, emoji_id="5312537023665893498", callback_data="pay_select_uah", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_back_text, emoji_id="5875082500023258804", callback_data="back_to_main", style="primary")
    )
    
    return builder.as_markup()

def get_wallets_management_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    texts = {
        "gram": {"ru": "Gram", "en": "Gram", "id": "Gram", "ar": "جرام", "zh": "Gram", "ja": "Gram"},
        "card": {"ru": "Рубли", "en": "Rubles", "id": "Rubel", "ar": "روبل", "zh": "卢布", "ja": "ルーブル"},
        "usdt": {"ru": "Usdt", "en": "Usdt", "id": "Usdt", "ar": "Usdt", "zh": "Usdt", "ja": "Usdt"},
        "stars": {"ru": "Stars", "en": "Stars", "id": "Stars", "ar": "نجوم", "zh": "Stars", "ja": "Stars"},
        "uah": {"ru": "Uah", "en": "Uah", "id": "Uah", "ar": "Uah", "zh": "Uah", "ja": "Uah"},
        "back": {"ru": "Вернутся в меню", "en": "Back to menu", "id": "Kembali ke menu", "ar": "العودة إلى القائمة", "zh": "返回菜单", "ja": "メニューに戻る"}
    }
    
    btn_gram = texts["gram"].get(lang, "Gram")
    btn_card = texts["card"].get(lang, "Рубли")
    btn_usdt = texts["usdt"].get(lang, "Usdt")
    btn_stars = texts["stars"].get(lang, "Stars")
    btn_uah = texts["uah"].get(lang, "Uah")
    btn_back = texts["back"].get(lang, "Вернутся в меню")
    
    builder.row(
        PremiumButton(text=btn_gram, emoji_id="5296742257146241213", callback_data="wallet_setup_gram", style="primary"),
        PremiumButton(text=btn_usdt, emoji_id="5010651410363057397", callback_data="wallet_setup_usdt", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_card, emoji_id="5967548335542767952", callback_data="wallet_setup_sbp", style="primary"),
        PremiumButton(text=btn_stars, emoji_id="5197598752503795445", callback_data="wallet_setup_stars", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_uah, emoji_id="5447309366568953338", callback_data="wallet_setup_uah", style="primary")
    )
    builder.row(
        PremiumButton(text=btn_back, emoji_id="5875082500023258804", callback_data="back_to_main", style="primary")
    )
    return builder.as_markup()