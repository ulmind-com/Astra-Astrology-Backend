"""Script to wipe all appointment slots, availability windows, and bookings.
Provides a 100% clean, fresh start across all astrologers in MongoDB Atlas.
"""
import asyncio
from app.db.mongodb import connect_to_mongo
from app.models.appointment import AvailabilityWindow, AppointmentSlot, Appointment

async def main():
    await connect_to_mongo()
    print("=== Clearing all appointment slots and windows across all astrologers ===")
    
    # 1. Count before deletion
    aw_count = await AvailabilityWindow.count()
    as_count = await AppointmentSlot.count()
    ap_count = await Appointment.count()
    print(f"Existing AvailabilityWindow documents: {aw_count}")
    print(f"Existing AppointmentSlot documents: {as_count}")
    print(f"Existing Appointment documents: {ap_count}")
    
    # 2. Perform clean deletion
    del_aw = await AvailabilityWindow.get_pymongo_collection().delete_many({})
    del_as = await AppointmentSlot.get_pymongo_collection().delete_many({})
    del_ap = await Appointment.get_pymongo_collection().delete_many({})
    
    print(f"\nDeleted AvailabilityWindow records: {del_aw.deleted_count}")
    print(f"Deleted AppointmentSlot records: {del_as.deleted_count}")
    print(f"Deleted Appointment records: {del_ap.deleted_count}")
    
    # 3. Verify clean state
    aw_after = await AvailabilityWindow.count()
    as_after = await AppointmentSlot.count()
    ap_after = await Appointment.count()
    
    print("\n--- Verification After Wiping ---")
    print(f"Remaining AvailabilityWindow: {aw_after}")
    print(f"Remaining AppointmentSlot: {as_after}")
    print(f"Remaining Appointment: {ap_after}")
    
    if aw_after == 0 and as_after == 0 and ap_after == 0:
        print("\n✅ Database is now completely fresh! 0 slots, 0 windows, 0 appointments.")
    else:
        print("\n⚠️ Warning: Some documents remained!")

if __name__ == "__main__":
    asyncio.run(main())
