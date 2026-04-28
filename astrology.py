#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, requests
from datetime import datetime, timedelta

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SIGN_FA = {
    'Aries': 'حمل ♈', 'Taurus': 'ثور ♉', 'Gemini': 'جوزا ♊',
    'Cancer': 'سرطان ♋', 'Leo': 'اسد ♌', 'Virgo': 'سنبله ♍',
    'Libra': 'میزان ♎', 'Scorpio': 'عقرب ♏', 'Sagittarius': 'قوس ♐',
    'Capricorn': 'جدی ♑', 'Aquarius': 'دلو ♒', 'Pisces': 'حوت ♓',
}

PLANET_FA = {
    'Sun': '☀️ خورشید', 'Moon': '🌙 ماه', 'Mercury': '☿ عطارد',
    'Venus': '♀ زهره', 'Mars': '♂ مریخ', 'Jupiter': '♃ مشتری',
    'Saturn': '♄ زحل', 'Uranus': '♅ اورانوس', 'Neptune': '♆ نپتون',
    'Pluto': '♇ پلوتو',
}


def ask_gemini(prompt: str, max_tokens: int = 1500) -> str:
    """Call Google Gemini 1.5 Flash (free tier)."""
    if not GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY تنظیم نشده است."
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}
            },
            timeout=45
        )
        if resp.status_code == 200:
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        return f"❌ خطای Gemini: {resp.status_code}"
    except Exception as e:
        return f"❌ خطای اتصال: {e}"


def sun_sign(dt: datetime) -> str:
    m, d = dt.month, dt.day
    table = [
        (3,21,'Aries'),(4,20,'Taurus'),(5,21,'Gemini'),(6,21,'Cancer'),
        (7,23,'Leo'),(8,23,'Virgo'),(9,23,'Libra'),(10,23,'Scorpio'),
        (11,22,'Sagittarius'),(12,22,'Capricorn'),(1,20,'Aquarius'),(2,19,'Pisces'),
    ]
    for sm, sd, sign in table:
        if (m == sm and d >= sd) or (m == (sm % 12)+1 and d < sd):
            return sign
    return 'Capricorn'


def moon_sign(dt: datetime, hour: int) -> str:
    ref = datetime(2000, 1, 1)
    days = (dt - ref).days + hour / 24.0
    idx = int((days % 27.321582) / 27.321582 * 12)
    signs = list(SIGN_FA.keys())
    return signs[idx % 12]


def rising_sign(dt: datetime, hour: int) -> str:
    signs = list(SIGN_FA.keys())
    base = list(SIGN_FA.keys()).index(sun_sign(dt))
    return signs[(base + hour // 2) % 12]


def planet_positions(dt: datetime) -> dict:
    ref = datetime(2000, 1, 1)
    days = (dt - ref).days
    periods = {'Mercury':87.97,'Venus':224.7,'Mars':686.97,'Jupiter':4332.59,
               'Saturn':10759.22,'Uranus':30688.5,'Neptune':60182.0,'Pluto':90560.0}
    starts  = {'Mercury':75,'Venus':181,'Mars':316,'Jupiter':34,
               'Saturn':50,'Uranus':312,'Neptune':302,'Pluto':252}
    signs = list(SIGN_FA.keys())
    result = {}
    for p, period in periods.items():
        deg = (starts[p] + days / period * 360) % 360
        result[p] = {'sign': signs[int(deg/30)%12], 'deg': round(deg%30, 1)}
    return result


def profile_summary(profile: dict) -> str:
    bd = profile.get('birth_date', datetime.now())
    bh = profile.get('birth_hour', 12)
    bm = profile.get('birth_minute', 0)
    ss = SIGN_FA.get(sun_sign(bd), '')
    ms = SIGN_FA.get(moon_sign(bd, bh), '')
    rs = SIGN_FA.get(rising_sign(bd, bh), '')
    return (f"نام: {profile.get('name','؟')}\n"
            f"تاریخ تولد: {profile.get('birth_date_str','؟')} ساعت {bh:02d}:{bm:02d}\n"
            f"محل تولد: {profile.get('birth_place','؟')}\n"
            f"☀️ برج خورشید: {ss}\n🌙 برج ماه: {ms}\n⬆️ طالع: {rs}")


async def calculate_natal_chart(profile: dict) -> str:
    bd = profile.get('birth_date', datetime.now())
    bh = profile.get('birth_hour', 12)
    bm = profile.get('birth_minute', 0)
    planets = planet_positions(bd)
    planet_text = "\n".join(
        f"• {PLANET_FA[p]}: {SIGN_FA.get(v['sign'], v['sign'])} — {v['deg']}°"
        for p, v in planets.items()
    )
    prompt = f"""تو یک منجم و طالع‌بین حرفه‌ای هستی. به فارسی روان و دقیق بنویس.

اطلاعات تولد:
{profile_summary(profile)}

موقعیت سیارات:
{planet_text}

یک تحلیل چارت تولد کامل، حرفه‌ای و انگیزشی بنویس شامل:
1. ✨ شخصیت کلی (بر اساس سه رکن اصلی)
2. 💪 نقاط قوت برجسته
3. ⚡ چالش‌های اصلی زندگی
4. 💼 شغل و مسیر حرفه‌ای مناسب
5. 💕 ویژگی‌های عاشقانه
6. 💰 رابطه با پول و ثروت
7. 🌟 استعداد پنهان و پیشنهاد رشد

از ایموجی استفاده کن. پاسخ باید کاربردی، دلگرم‌کننده و دقیق باشد."""

    result = ask_gemini(prompt, 1800)
    header = (f"⭐ *چارت تولد {profile.get('name','')}* ⭐\n\n"
              f"{profile_summary(profile)}\n\n"
              f"🪐 *موقعیت سیارات:*\n{planet_text}\n\n"
              f"━━━━━━━━━━━━━━━━━━━━\n\n")
    return header + result


async def get_daily_chart(profile: dict) -> str:
    today = datetime.now().strftime('%Y/%m/%d')
    prompt = f"""تو یک منجم حرفه‌ای هستی. به فارسی روان بنویس.

{profile_summary(profile)}
تاریخ امروز: {today}

تحلیل روزانه دقیق و کاربردی بنویس:
1. 🌅 انرژی کلی امروز
2. 💼 کار و شغل (پیشنهاد عملی)
3. 💕 عشق و روابط
4. 💰 وضعیت مالی
5. 🏃 سلامت و انرژی بدنی
6. ⚠️ نکات مهم — چه کاری نکنم؟
7. 🍀 ساعت خوش‌یمن امروز
8. 🎯 توصیه اصلی روز در یک جمله

کوتاه، دقیق، کاربردی. از ایموجی استفاده کن."""

    result = ask_gemini(prompt, 1200)
    return f"📊 *تحلیل روزانه — {today}*\n👤 {profile.get('name','')} | {SIGN_FA.get(sun_sign(profile.get('birth_date', datetime.now())),'' )}\n\n━━━━━━━━━━━━━━━━\n\n{result}"


async def get_weekly_chart(profile: dict) -> str:
    today = datetime.now()
    end = (today + timedelta(days=7)).strftime('%Y/%m/%d')
    prompt = f"""تو یک منجم حرفه‌ای هستی. به فارسی بنویس.

{profile_summary(profile)}
این هفته: {today.strftime('%Y/%m/%d')} تا {end}

تحلیل هفتگی کامل بنویس:
1. 🗓 نمای کلی هفته
2. ✅ بهترین روزهای هفته (با تاریخ)
3. ⚠️ روزهای چالش‌برانگیز (با تاریخ)
4. 💼 روند شغلی هفته
5. 💕 روند عاطفی هفته
6. 💰 وضعیت مالی هفته
7. 🏥 سلامت
8. 🎯 هدف اصلی این هفته
9. 🌟 فرصت طلایی هفته را از دست نده!

جامع، دقیق و انگیزشی باشد."""

    result = ask_gemini(prompt, 1500)
    return f"📈 *تحلیل هفتگی*\n📅 {today.strftime('%Y/%m/%d')} تا {end}\n👤 {profile.get('name','')}\n\n━━━━━━━━━━━━━━━━\n\n{result}"


async def get_monthly_chart(profile: dict) -> str:
    today = datetime.now()
    prompt = f"""تو یک منجم حرفه‌ای هستی. به فارسی بنویس.

{profile_summary(profile)}
ماه: {today.strftime('%B %Y')}

تحلیل ماهیانه جامع بنویس:
1. 🌟 تم اصلی این ماه
2. 📊 روند کلی (صعودی/نزولی/متعادل)
3. 💼 شغل و کار: فرصت‌ها و چالش‌ها
4. 💕 عشق: پیش‌بینی کلی ماه
5. 💰 مالی: بهترین زمان سرمایه‌گذاری
6. 🏥 سلامت: نکات مهم
7. 📅 تاریخ‌های کلیدی این ماه
8. 🔑 کلیدهای موفقیت ماه
9. ⚡ هشدارهای مهم
10. 🎯 استراتژی پیشنهادی برای این ماه

بسیار جامع، حرفه‌ای و کاربردی باش."""

    result = ask_gemini(prompt, 1800)
    return f"🗓 *تحلیل ماهیانه — {today.strftime('%B %Y')}*\n👤 {profile.get('name','')}\n\n━━━━━━━━━━━━━━━━\n\n{result}"
