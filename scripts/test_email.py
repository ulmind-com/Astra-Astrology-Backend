"""Test Resend email delivery dynamically.

Usage:
    # Interactive prompt:
    uv run python -m scripts.test_email

    # Or pass recipient directly as an argument:
    uv run python -m scripts.test_email your-email@gmail.com
"""

import asyncio
import re
import sys
from datetime import datetime, timezone

from app.core.config import settings
from app.services.email import send_email, send_otp_email, send_welcome_email


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:7]}...{key[-4:]}"


async def main() -> int:
    print("\n" + "=" * 60)
    print("      DivinLink / Resend Email Delivery Test Tool")
    print("=" * 60)

    # 1. Verify Configuration
    api_key = settings.RESEND_API_KEY
    from_email = settings.RESEND_FROM_EMAIL
    from_name = settings.RESEND_FROM_NAME

    print(f"• Resend API Key:  {mask_key(api_key) if api_key else '❌ NOT CONFIGURED'}")
    print(f"• From Address:    {from_name} <{from_email}>")

    if not api_key:
        print("\n❌ Error: RESEND_API_KEY is missing in your .env file.")
        print("Please ensure RESEND_API_KEY is set in Astra-Astrology-Backend/.env")
        return 1

    # 2. Get recipient email (CLI arg or interactive prompt)
    if len(sys.argv) > 1 and sys.argv[1].strip():
        recipient = sys.argv[1].strip()
    else:
        try:
            recipient = input("\nEnter recipient email address: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1

    if not recipient or not EMAIL_REGEX.match(recipient):
        print(f"❌ Invalid email address: '{recipient}'")
        return 1

    print(f"\nTarget Recipient: {recipient}")
    print("-" * 60)
    print("Select email template type to test:")
    print("  1) Standard Test Email (Detailed Resend Diagnostics)")
    print("  2) 6-Digit OTP Verification Email (Registration/Login template)")
    print("  3) Welcome to DivinLink Onboarding Email")
    print("  4) Send ALL of the above (Full Suite Test)")

    try:
        choice = input("\nEnter choice [1-4] (default 1): ").strip() or "1"
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        return 1

    sent_count = 0
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Type 1: Standard Diagnostics Email
    if choice in ("1", "4"):
        print(f"\n[1/3] Sending Diagnostic Test Email to {recipient}...")
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #f3e8d2; border-radius: 16px; background: #fffcf8;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #92400e; font-size: 26px; margin: 0;">✨ DivinLink Email Test</h1>
                <p style="color: #78716c; font-size: 14px; margin-top: 4px;">Resend Production Verification</p>
            </div>
            <div style="background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #fef3c7; margin-bottom: 20px;">
                <p style="font-size: 15px; color: #1c1917; margin: 0 0 12px 0;">Hello!</p>
                <p style="font-size: 14px; color: #44403c; line-height: 1.6; margin: 0 0 16px 0;">
                    This is an automated test email confirming that your Resend transactional email integration is <strong>active and working flawlessly</strong> with your verified domain.
                </p>
                <table style="width: 100%; font-size: 13px; color: #57534e; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold; width: 140px;">Sender:</td>
                        <td style="padding: 6px 0;">{from_name} &lt;{from_email}&gt;</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Recipient:</td>
                        <td style="padding: 6px 0;">{recipient}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Timestamp:</td>
                        <td style="padding: 6px 0;">{now_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Domain Status:</td>
                        <td style="padding: 6px 0; color: #15803d; font-weight: bold;">divinlink.com (Verified & Active)</td>
                    </tr>
                </table>
            </div>
            <p style="text-align: center; font-size: 12px; color: #a8a29e; margin: 0;">
                DivinLink Vedic Astrology • All Rights Reserved
            </p>
        </div>
        """
        try:
            res = await send_email(
                to=recipient,
                subject="✨ DivinLink Resend Test — Email Service is Active!",
                html=html_content,
                text=f"DivinLink Email Test.\nSent to: {recipient}\nTimestamp: {now_str}\nStatus: Active.",
            )
            print(f"   ✅ Successfully sent! Resend Response ID: {res.get('id') if isinstance(res, dict) else res}")
            sent_count += 1
        except Exception as e:
            print(f"   ❌ Failed to send: {e}")

    # Type 2: OTP Verification
    if choice in ("2", "4"):
        print(f"\n[2/3] Sending OTP Verification Email (6-digit code) to {recipient}...")
        try:
            await send_otp_email(
                to=recipient,
                code="784920",
                purpose="signup",
                name="Valued Seeker",
            )
            print("   ✅ Successfully sent OTP template email!")
            sent_count += 1
        except Exception as e:
            print(f"   ❌ Failed to send OTP email: {e}")

    # Type 3: Welcome Email
    if choice in ("3", "4"):
        print(f"\n[3/3] Sending Welcome Onboarding Email to {recipient}...")
        try:
            await send_welcome_email(
                to=recipient,
                name="Valued Seeker",
            )
            print("   ✅ Successfully sent Welcome template email!")
            sent_count += 1
        except Exception as e:
            print(f"   ❌ Failed to send Welcome email: {e}")

    print("\n" + "=" * 60)
    if sent_count > 0:
        print(f"🎉 SUCCESS: {sent_count} email(s) dispatched successfully to {recipient}!")
        print("Please check your Inbox (and Spam/Junk folder if testing for the first time).")
    else:
        print("❌ Test failed: No emails were dispatched.")
    print("=" * 60 + "\n")
    return 0 if sent_count > 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
