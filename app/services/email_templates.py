"""Branded HTML email templates."""

from app.core.config import settings

_PURPOSE_COPY = {
    "signup": "Use this code to finish creating your account.",
    "login": "Use this code to sign in to your account.",
    "email_verification": "Use this code to verify your email address.",
    "password_reset": "Use this code to reset your password.",
}


def render_email(title: str, body_html: str, *, preheader: str = "") -> str:
    """Wraps `body_html` in the standard Astra Astrology email shell."""
    hidden_preheader = (
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>'
        if preheader
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="color-scheme" content="light only" />
<title>{title}</title>
</head>
<body style="margin:0;padding:24px 12px;background:#0b0920;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
{hidden_preheader}
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 12px 32px rgba(11,9,32,.35);">
        <tr>
          <td style="background:linear-gradient(135deg,#2b1b6b 0%,#6d28d9 55%,#a855f7 100%);padding:30px 32px;">
            <p style="margin:0;color:#ffffff;font-size:21px;font-weight:700;letter-spacing:.4px;">
              &#10022; {settings.APP_NAME}
            </p>
            <p style="margin:6px 0 0;color:rgba(255,255,255,.72);font-size:12px;letter-spacing:1.4px;text-transform:uppercase;">
              Astrology &middot; Numerology &middot; Panchang
            </p>
          </td>
        </tr>
        <tr><td style="padding:32px;color:#1f2937;font-size:15px;line-height:1.65;">{body_html}</td></tr>
        <tr>
          <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #eef2f7;color:#6b7280;font-size:12px;line-height:1.6;">
            Need help? Write to
            <a href="mailto:{settings.SUPPORT_EMAIL}" style="color:#6d28d9;text-decoration:none;">{settings.SUPPORT_EMAIL}</a>.<br />
            &copy; {settings.APP_NAME}. All rights reserved.
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def otp_email_html(code: str, purpose: str, name: str | None = None) -> str:
    greeting = f"Hi {name}," if name else "Hi there,"
    reason = _PURPOSE_COPY.get(purpose, "Use this code to continue.")
    body = f"""
      <p style="margin:0 0 12px;">{greeting}</p>
      <p style="margin:0 0 26px;">{reason}</p>
      <div style="text-align:center;margin:0 0 26px;">
        <span style="display:inline-block;padding:18px 30px;background:#f5f3ff;border:1px solid #ddd6fe;border-radius:14px;color:#4c1d95;font-size:34px;font-weight:700;letter-spacing:12px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;">{code}</span>
      </div>
      <p style="margin:0 0 10px;">
        This code expires in <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong>.
      </p>
      <p style="margin:0;color:#6b7280;">
        If you didn't ask for this, you can safely ignore this email — nobody can
        get into your account without the code.
      </p>
    """
    return render_email(
        "Your verification code", body, preheader=f"{code} is your verification code"
    )


def welcome_email_html(name: str | None = None) -> str:
    greeting = f"Welcome, {name}!" if name else "Welcome!"
    body = f"""
      <p style="margin:0 0 10px;font-size:22px;font-weight:700;color:#2b1b6b;">{greeting}</p>
      <p style="margin:0 0 22px;">
        Your {settings.APP_NAME} account is ready. The stars have been waiting for you &#10022;
      </p>

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px;">
        <tr>
          <td style="padding:14px 16px;background:#faf5ff;border:1px solid #f3e8ff;border-radius:12px;">
            <p style="margin:0 0 6px;font-weight:600;color:#4c1d95;">&#9770; Your Kundli</p>
            <p style="margin:0;color:#4b5563;font-size:14px;">
              Your full birth chart, planetary positions and dasha periods.
            </p>
          </td>
        </tr>
        <tr><td style="height:10px;"></td></tr>
        <tr>
          <td style="padding:14px 16px;background:#faf5ff;border:1px solid #f3e8ff;border-radius:12px;">
            <p style="margin:0 0 6px;font-weight:600;color:#4c1d95;">&#128290; Numerology</p>
            <p style="margin:0;color:#4b5563;font-size:14px;">
              Your mulank, bhagyank, lucky numbers, colours and gemstones.
            </p>
          </td>
        </tr>
        <tr><td style="height:10px;"></td></tr>
        <tr>
          <td style="padding:14px 16px;background:#faf5ff;border:1px solid #f3e8ff;border-radius:12px;">
            <p style="margin:0 0 6px;font-weight:600;color:#4c1d95;">&#128197; Daily Panchang</p>
            <p style="margin:0;color:#4b5563;font-size:14px;">
              Tithi, nakshatra, shubh muhurat and rahukaal, every morning.
            </p>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 6px;color:#374151;">
        Add your birth date, time and place to unlock everything.
      </p>
      <p style="margin:0;color:#9ca3af;font-size:13px;">
        Clear skies ahead &#10022;
      </p>
    """
    return render_email(
        f"Welcome to {settings.APP_NAME}",
        body,
        preheader="Your account is ready — here's what you can do next.",
    )
