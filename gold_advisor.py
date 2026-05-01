#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, requests
from datetime import datetime
from astrology import sun_sign, SIGN_FA

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_SEARCH_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# --- Currency detection ---
CURRENCY_MAP = {
    'ایران': ('IRR', 'تومان'), 'iran': ('IRR', 'تومان'),
    'تهران': ('IRR', 'تومان'), 'tehran': ('IRR', 'تومان'),
    'مشهد': ('IRR', 'تومان'), 'اصفهان': ('IRR', 'تومان'),
    'شیراز': ('IRR', 'تومان'), 'تبریز': ('IRR', 'تومان'),
    'امارات': ('AED', 'درهم'), 'دبی': ('AED', 'درهم'),
    'dubai': ('AED', 'AED'), 'uae': ('AED', 'AED'),
    'ترکیه': ('TRY', 'لیر'), 'turkey': ('TRY', 'TRY'),
    'آلمان': ('EUR', '€'), 'فرانسه': ('EUR', '€'),
    'اروپا': ('EUR', '€'), 'europe': ('EUR', '€'),
    'انگلیس': ('GBP', '£'), 'uk': ('GBP', '£'),
    'آمریکا': ('USD', '$'), 'usa': ('USD', '$'),
    'کانادا': ('CAD', 'CAD'), 'canada': ('CAD', 'CAD'),
    'استرالیا': ('AUD', 'AUD'), 'australia': ('AUD', 'AUD'),
    'عربستان': ('SAR', 'ریال'), 'saudi': ('SAR', 'SAR'),
    'کویت': ('KWD', 'دینار'), 'قطر': ('QAR', 'ریال'),
    'عراق': ('IQD', 'دینار'), 'iraq': ('IQD', 'IQD'),
    'افغانستان': ('AFN', 'افغانی'), 'afghanistan': ('AFN', 'AFN'),
}

# IRR approximate free-market rates (updated manually or via free API)
IRR_RATES = {
    'USD': 580000, 'EUR': 635000, 'GBP': 740000,
    'AED': 158000, 'TRY': 18000, 'CAD': 430000,
    'AUD': 378000, 'SAR': 154000, 'KWD': 1890000,
    'QAR': 159000, 'IQD': 443, 'AFN': 8400,
}


def detect_currency(location: str):
    loc = location.lower()
    for key, (code, sym) in CURRENCY_MAP.items():
        if key in loc:
            return code, sym
    return 'USD', '$'


def fetch_gold_price_free() -> dict:
    """Try multiple free gold price sources."""
    # Source 1: metals.live (no key needed)
    try:
        r = requests.get('https://api.metals.live/v1/spot/gold', timeout=8)
        if r.status_code == 200:
            data = r.json()
            price = data[0].get('gold', 0) if isinstance(data, list) else data.get('gold', 0)
            if price > 0:
                return {'usd_oz': price, 'usd_gram': price/31.1035, 'change': 0, 'source': 'metals.live'}
    except: pass

    # Source 2: frankfurter.app gives EUR rates; combine with fixed XAU/EUR
    # Fallback: approximate known price
    return {'usd_oz': 2320, 'usd_gram': 2320/31.1035, 'change': 0, 'source': 'تقریبی'}


def get_exchange_rate(currency: str) -> float:
    if currency == 'USD': return 1.0
    if currency == 'IRR': return IRR_RATES.get('USD', 580000)

    # Try free Frankfurter API
    try:
        r = requests.get(f'https://api.frankfurter.app/latest?from=USD&to={currency}', timeout=8)
        if r.status_code == 200:
            return r.json()['rates'].get(currency, 1.0)
    except: pass
    return 1.0


def ask_gemini_gold(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return None
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": 1200, "temperature": 0.7}
        }
        resp = requests.post(f"{GEMINI_SEARCH_URL}?key={GEMINI_API_KEY}", json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        # Fallback without search
        payload.pop('tools')
        resp2 = requests.post(f"{GEMINI_SEARCH_URL}?key={GEMINI_API_KEY}", json=payload, timeout=45)
        if resp2.status_code == 200:
            return resp2.json()['candidates'][0]['content']['parts'][0]['text']
    except: pass
    return None


async def get_gold_recommendation(profile: dict) -> str:
    location = profile.get('current_location', 'ایران')
    name = profile.get('name', 'کاربر')
    bd = profile.get('birth_date', datetime.now())

    currency_code, currency_sym = detect_currency(location)
    gold = fetch_gold_price_free()

    usd_oz = gold['usd_oz']
    usd_gram = gold['usd_gram']
    change = gold['change']
    price_source = gold['source']

    # Calculate local price
    if currency_code == 'IRR':
        # IRR free-market rate
        irr_per_usd = IRR_RATES['USD']
        toman_per_gram = usd_gram * irr_per_usd / 10
        toman_per_mesghal = toman_per_gram * 4.608
        local_display = f"{toman_per_gram:,.0f} تومان/گرم | {toman_per_mesghal:,.0f} تومان/مثقال"
    else:
        rate = get_exchange_rate(currency_code)
        local_gram = usd_gram * rate
        local_display = f"{local_gram:.2f} {currency_sym}/گرم"

    # Get astrological signs
    from astrology import sun_sign, moon_sign, rising_sign, SIGN_FA
    sun = sun_sign(bd)
    moon = moon_sign(bd, bh)
    rising = rising_sign(bd, bh, bm, bp)
    
    sun_fa = SIGN_FA.get(sun, sun)
    moon_fa = SIGN_FA.get(moon, moon)
    rising_fa = SIGN_FA.get(rising, rising)
    
    today = datetime.now().strftime('%Y/%m/%d')

    prompt = f"""تو یک مشاور مالی و متخصص بازار طلا هستی که تحلیل نجومی هم داری. به فارسی روان بنویس.

اطلاعات کاربر:
- نام: {name}
- برج خورشید: {sun_fa}
- برج ماه: {moon_fa}
- طالع: {rising_fa}
- موقعیت: {location}
- تاریخ امروز: {today}

قیمت‌های فعلی طلا (منبع: {price_source}):
- قیمت جهانی: ${usd_oz:,.0f} دلار/اونس
- هر گرم طلای 24 عیار: ${usd_gram:.2f} دلار
- قیمت محلی: {local_display}
- تغییر امروز: {change:.2f}%

با جستجو در اینترنت، آخرین اخبار بازار طلا را بررسی کن و پیشنهاد دقیق بده:

🥇 *مشاور طلا — {today}*

1. 📊 وضعیت فعلی بازار جهانی طلا
2. 📰 مهم‌ترین اخبار مؤثر بر قیمت طلا (امروز)
3. 💹 روند کوتاه‌مدت (صعودی/نزولی/رنجی)
4. 📍 وضعیت بازار طلا در {location}
5. 🌟 **تحلیل نجومی**: بر اساس برج {sun_fa} (خورشید)، {moon_fa} (ماه) و طالع {rising_fa}، آیا امروز برای این شخص روز مناسبی برای خرید/فروش طلاست؟
6. 🎯 **پیشنهاد نهایی**: خرید / فروش / نگهداری (صریح و روشن)
7. 💡 دلایل پیشنهاد (هم از نظر بازار هم از نظر نجومی)
8. ⚠️ ریسک‌های موجود
9. 📅 بهترین زمان اقدام (امروز/این هفته/صبر کنید)
10. 💰 اگر {currency_sym if currency_code != 'IRR' else '10 میلیون تومان'} دارم چه کنم؟

پیشنهاد باید مشخص باشد: **خرید**، **فروش**، یا **نگهداری/صبر کنید**.
تحلیل نجومی باید با تحلیل بازار ترکیب شود تا پیشنهاد عملی باشد.
از ایموجی استفاده کن."""

    ai = ask_gemini_gold(prompt)

    header = (f"🥇 *مشاور طلا — {today}*\n"
              f"👤 {name} | 📍 {location}\n"
              f"🌟 {sun_fa} ☀️ | {moon_fa} 🌙 | {rising_fa} ⬆️\n\n"
              f"💵 قیمت جهانی: ${usd_oz:,.0f}/اونس\n"
              f"⚖️ {local_display}\n"
              f"📊 تغییر: {'📈' if change >= 0 else '📉'} {change:.2f}%\n"
              f"🔗 منبع: {price_source}\n\n"
              f"━━━━━━━━━━━━━━━━\n\n")

    if ai:
        return header + ai
    else:
        rec = "⏸ نگهداری — بازار نامشخص"
        if change > 0.5: rec = "📈 خرید تدریجی — روند صعودی"
        elif change < -0.5: rec = "📉 صبر کنید — روند نزولی"
        return header + f"🎯 *پیشنهاد:* {rec}\n\n⚠️ برای تحلیل دقیق‌تر GEMINI_API_KEY را تنظیم کنید.\n\n📌 این پیشنهاد صرفاً اطلاعاتی است و مشاوره مالی رسمی نیست."
