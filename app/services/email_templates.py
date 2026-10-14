"""Branded HTML email layout (no template engine needed yet)."""

from app.core.config import settings


def render_email(title: str, body_html: str) -> str:
    """Wraps `body_html` in the standard Astra Astrology email shell."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
</head>
<body style="margin:0;padding:24px;background:#0b0920;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;">
    <tr>
      <td style="background:linear-gradient(135deg,#2b1b6b,#6d28d9);padding:28px 32px;">
        <p style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:.3px;">
          &#10022; {settings.APP_NAME}
        </p>
      </td>
    </tr>
    <tr><td style="padding:32px;color:#1f2937;font-size:15px;line-height:1.6;">{body_html}</td></tr>
    <tr>
      <td style="padding:20px 32px;background:#f8fafc;color:#6b7280;font-size:12px;line-height:1.6;">
        Need help? Write to
        <a href="mailto:{settings.SUPPORT_EMAIL}" style="color:#6d28d9;">{settings.SUPPORT_EMAIL}</a>.<br />
        &copy; {settings.APP_NAME}. All rights reserved.
      </td>
    </tr>
  </table>
</body>
</html>"""
