"""Seed availability windows for active astrologers for the next 45 days.
Ensures real, active consultation showtimes exist in MongoDB Atlas.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.db.mongodb import connect_to_mongo
from app.models.appointment import AvailabilityWindow
from app.models.astrologer import Astrologer

IST = ZoneInfo("Asia/Kolkata")
UTC = timezone.utc

async def seed_windows_for_astrologer(astrologer: Astrologer, start_date: date, days: int = 45):
    print(f"--- Seeding windows for {astrologer.display_name} ({astrologer.id}) ---")
    created_count = 0
    
    for i in range(days):
        current_day = start_date + timedelta(days=i)
        
        # Check existing windows for this astrologer and day
        existing = await AvailabilityWindow.find({
            "astrologer_id": astrologer.id,
            "day": current_day,
        }).count()
        
        if existing > 0:
            print(f"Day {current_day}: already has {existing} windows. Skipping.")
            continue
            
        # 1. Morning Session: 10:00 AM IST to 01:30 PM IST (04:30 to 08:00 UTC)
        # 10:00 IST = 04:30 UTC
        m_start = datetime(current_day.year, current_day.month, current_day.day, 4, 30, tzinfo=UTC)
        m_end = datetime(current_day.year, current_day.month, current_day.day, 8, 0, tzinfo=UTC)
        w_morning = AvailabilityWindow(
            astrologer_id=astrologer.id,
            day=current_day,
            starts_at=m_start,
            ends_at=m_end,
            is_tatkal=False,
            custom_title="Morning Vedic Consultation",
        )
        await w_morning.insert()
        created_count += 1
        
        # 2. Evening Peak Session: 03:30 PM IST to 07:30 PM IST (10:00 to 14:00 UTC)
        e_start = datetime(current_day.year, current_day.month, current_day.day, 10, 0, tzinfo=UTC)
        e_end = datetime(current_day.year, current_day.month, current_day.day, 14, 0, tzinfo=UTC)
        w_evening = AvailabilityWindow(
            astrologer_id=astrologer.id,
            day=current_day,
            starts_at=e_start,
            ends_at=e_end,
            is_tatkal=False,
            custom_title="Evening Consultation Chamber",
        )
        await w_evening.insert()
        created_count += 1
        
        # 3. VIP Tatkal Session: 08:00 PM IST to 09:30 PM IST (14:30 to 16:00 UTC)
        t_start = datetime(current_day.year, current_day.month, current_day.day, 14, 30, tzinfo=UTC)
        t_end = datetime(current_day.year, current_day.month, current_day.day, 16, 0, tzinfo=UTC)
        w_tatkal = AvailabilityWindow(
            astrologer_id=astrologer.id,
            day=current_day,
            starts_at=t_start,
            ends_at=t_end,
            is_tatkal=True,
            tatkal_multiplier=1.5,
            custom_title="VIP Tatkal Consultation",
        )
        await w_tatkal.insert()
        created_count += 1

    print(f"Successfully created {created_count} windows for {astrologer.display_name}.")

async def main():
    await connect_to_mongo()
    today_ist = datetime.now(IST).date()
    print(f"Today IST: {today_ist}")
    
    astros = await Astrologer.find_all().to_list()
    for a in astros:
        # Enable appointment card for Kanu if disabled
        if a.slug == "astrologer-kanu":
            if not a.appointment or not a.appointment.enabled:
                print("Enabling appointment card for Astrologer Kanu...")
                a.appointment.enabled = True
                a.appointment.price_paise = 45000  # ₹450 / 30m
                a.appointment.block_minutes = 30
                a.appointment.tatkal_enabled = True
                a.appointment.tatkal_default_multiplier = 1.5
                await a.save()
                print("Astrologer Kanu appointment card enabled!")

        if a.is_listed:
            await seed_windows_for_astrologer(a, today_ist, days=45)

if __name__ == "__main__":
    asyncio.run(main())
