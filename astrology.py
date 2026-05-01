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
    """Calculate accurate sun sign from birth date."""
    m, d = dt.month, dt.day
    
    # Accurate tropical zodiac dates
    if (m == 3 and d >= 21) or (m == 4 and d <= 19): return 'Aries'
    if (m == 4 and d >= 20) or (m == 5 and d <= 20): return 'Taurus'
    if (m == 5 and d >= 21) or (m == 6 and d <= 20): return 'Gemini'
    if (m == 6 and d >= 21) or (m == 7 and d <= 22): return 'Cancer'
    if (m == 7 and d >= 23) or (m == 8 and d <= 22): return 'Leo'
    if (m == 8 and d >= 23) or (m == 9 and d <= 22): return 'Virgo'
    if (m == 9 and d >= 23) or (m == 10 and d <= 22): return 'Libra'
    if (m == 10 and d >= 23) or (m == 11 and d <= 21): return 'Scorpio'
    if (m == 11 and d >= 22) or (m == 12 and d <= 21): return 'Sagittarius'
    if (m == 12 and d >= 22) or (m == 1 and d <= 19): return 'Capricorn'
    if (m == 1 and d >= 20) or (m == 2 and d <= 18): return 'Aquarius'
    if (m == 2 and d >= 19) or (m == 3 and d <= 20): return 'Pisces'
    
    return 'Libra'  # fallback


def moon_sign(dt: datetime, hour: int) -> str:
    """Calculate moon sign with improved accuracy."""
    # Moon completes zodiac in ~27.3 days (sidereal month)
    # Reference: Moon in Aries at J2000.0 (Jan 1, 2000, 12:00 UTC)
    ref = datetime(2000, 1, 6, 18, 14)  # More accurate J2000 moon position
    
    # Calculate days since reference
    days_diff = (dt - ref).days + (hour / 24.0)
    
    # Moon's mean motion: ~13.176° per day
    moon_cycle = 27.321661  # Sidereal month in days
    moon_degrees = (days_diff / moon_cycle * 360) % 360
    
    # Each sign is 30 degrees
    sign_index = int(moon_degrees / 30) % 12
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    return signs[sign_index]


def rising_sign(dt: datetime, hour: int, minute: int, birth_place: str) -> str:
    """Calculate rising sign (ascendant) using local sidereal time approximation."""
    # Approximate latitude for major cities (will be refined later)
    # This is simplified - real ascendant needs exact lat/lon
    
    # Tehran: 35.6892°N, London: 51.5074°N, NYC: 40.7128°N, Dubai: 25.2048°N
    lat = 35.0  # Default to Tehran latitude
    if 'london' in birth_place.lower() or 'uk' in birth_place.lower():
        lat = 51.5
    elif 'new york' in birth_place.lower() or 'nyc' in birth_place.lower():
        lat = 40.7
    elif 'dubai' in birth_place.lower() or 'uae' in birth_place.lower():
        lat = 25.2
    elif 'los angeles' in birth_place.lower() or 'la' in birth_place.lower():
        lat = 34.0
    
    # Local sidereal time calculation (simplified)
    decimal_time = hour + minute / 60.0
    
    # Sun sign position as base
    sun = sun_sign(dt)
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    sun_index = signs.index(sun)
    
    # Ascendant rises ~1 sign every 2 hours (simplified)
    # Adjust for time of day
    hour_offset = int((decimal_time - 6) / 2)  # 6 AM as reference (sun rise)
    
    # Additional adjustment for latitude
    lat_factor = int((lat - 30) / 20)  # Rough latitude correction
    
    asc_index = (sun_index + hour_offset + lat_factor) % 12
    
    return signs[asc_index]


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
    bp = profile.get('birth_place', 'تهران')
    ss = SIGN_FA.get(sun_sign(bd), '')
    ms = SIGN_FA.get(moon_sign(bd, bh), '')
    rs = SIGN_FA.get(rising_sign(bd, bh, bm, bp), '')
    return (f"نام: {profile.get('name','؟')}\n"
            f"تاریخ تولد: {profile.get('birth_date_str','؟')} ساعت {bh:02d}:{bm:02d}\n"
            f"محل تولد: {bp}\n"
            f"☀️ برج خورشید: {ss}\n🌙 برج ماه: {ms}\n⬆️ طالع: {rs}")


async def calculate_natal_chart(profile: dict) -> str:
    bd = profile.get('birth_date', datetime.now())
    bh = profile.get('birth_hour', 12)
    bm = profile.get('birth_minute', 0)
    bp = profile.get('birth_place', 'تهران')
    
    sun = sun_sign(bd)
    moon = moon_sign(bd, bh)
    rising = rising_sign(bd, bh, bm, bp)
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
