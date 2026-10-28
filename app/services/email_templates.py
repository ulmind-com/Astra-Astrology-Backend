"""Hand-crafted, ultra-aesthetic, and animated email templates.

Inspired by the calm, mindful, human-centric design of Headspace and Linear:
- Pure inline SVG vector illustration with native SMIL & CSS keyframe animations
  (floating celestial sun character, twinkling sparkle stars, soft sunlight rays).
- Letterpress-style individual digit OTP cards and vibrant pill CTA buttons.
- Editorial-grade typography with generous whitespace and zero robotic AI feel.
- Bulletproof HTML table layout tested across Gmail, Apple Mail, Outlook, and mobile clients.
"""

from app.core.config import settings

_SOCIAL_LINKS = {
    "facebook": "https://facebook.com/divinlink",
    "instagram": "https://instagram.com/divinlink",
    "twitter": "https://twitter.com/divinlink",
    "youtube": "https://youtube.com/@divinlink",
}

# 4 Minimalist monochrome social icons matching the Headspace screenshot
_SOCIAL_ICONS_ROW = f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 22px;">
  <tr>
    <td style="padding:0 10px;">
      <a href="{_SOCIAL_LINKS['facebook']}" target="_blank" style="text-decoration:none;display:inline-block;color:#374151;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      </a>
    </td>
    <td style="padding:0 10px;">
      <a href="{_SOCIAL_LINKS['instagram']}" target="_blank" style="text-decoration:none;display:inline-block;color:#374151;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
        </svg>
      </a>
    </td>
    <td style="padding:0 10px;">
      <a href="{_SOCIAL_LINKS['twitter']}" target="_blank" style="text-decoration:none;display:inline-block;color:#374151;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      </a>
    </td>
    <td style="padding:0 10px;">
      <a href="{_SOCIAL_LINKS['youtube']}" target="_blank" style="text-decoration:none;display:inline-block;color:#374151;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      </a>
    </td>
  </tr>
</table>
"""


def _animated_hero_illustration_svg() -> str:
    """Returns an inline, animated SVG vector illustration matching the Headspace screenshot.

    Features:
    - Sunny yellow canvas with soft curved corners.
    - Arched sunlight beam sweeping from the left with glowing breathing opacity.
    - Creamy gentle rolling horizon hill.
    - Serene meditating sun character with closed smiling eyes that gently floats up and down.
    - Sparkling 4-point star that pulses and twinkles in real-time.
    - Embedded SMIL animations and CSS animations ensure it moves in Apple Mail & modern web clients,
      while rendering as a crisp, static illustration in Outlook.
    """
    return """
<svg width="340" height="180" viewBox="0 0 340 180" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:340px;height:auto;border-radius:22px;display:block;margin:0 auto;box-shadow:0 8px 24px -6px rgba(255,160,0,0.25);">
  <defs>
    <!-- Background Sunny Gradient -->
    <linearGradient id="headspaceSky" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFD12A"/>
      <stop offset="60%" stop-color="#FFBD14"/>
      <stop offset="100%" stop-color="#FFA800"/>
    </linearGradient>

    <!-- Sunbeam Gradient Arc -->
    <linearGradient id="headspaceBeam" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFF37A" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="#FFE84D" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#FFD700" stop-opacity="0"/>
    </linearGradient>

    <!-- Character Radiant Gradient -->
    <linearGradient id="characterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF7600"/>
      <stop offset="100%" stop-color="#FF4D00"/>
    </linearGradient>
  </defs>

  <!-- 1. Rounded Sunny Yellow Canvas -->
  <rect width="340" height="180" rx="22" fill="url(#headspaceSky)"/>

  <!-- 2. Arched Sunlight Beam (matching the Headspace screenshot ray arc) -->
  <path d="M-10 35 C100 20, 220 65, 350 150 L350 180 L-10 180 Z" fill="url(#headspaceBeam)">
    <animate attributeName="opacity" values="0.7;0.95;0.7" dur="4s" repeatCount="indefinite"/>
  </path>

  <!-- 3. Gentle Rolling White Horizon Hill -->
  <path d="M-15 180 C65 110, 275 110, 355 180 Z" fill="#FFFFFF"/>

  <!-- 4. Peaceful Meditating Sun Character with Smooth Floating Motion -->
  <g class="celestial-float">
    <!-- Native SVG SMIL floating animation -->
    <animateTransform attributeName="transform" type="translate" values="0,0; 0,-6; 0,0" dur="3.6s" repeatCount="indefinite" additive="sum"/>

    <!-- Orange Character Body with soft drop shadow -->
    <circle cx="218" cy="94" r="41" fill="url(#characterGrad)" style="filter:drop-shadow(0 4px 10px rgba(255,80,0,0.3));"/>

    <!-- Subtle Soft Blush on Cheeks -->
    <circle cx="199" cy="99" r="4.5" fill="#FF8C38" opacity="0.55"/>
    <circle cx="237" cy="99" r="4.5" fill="#FF8C38" opacity="0.55"/>

    <!-- Signature Headspace Curved Smiling Eyes -->
    <path d="M201 92 C201 87, 211 87, 211 92" stroke="#421400" stroke-width="2.8" stroke-linecap="round" fill="none"/>
    <path d="M225 92 C225 87, 235 87, 235 92" stroke="#421400" stroke-width="2.8" stroke-linecap="round" fill="none"/>

    <!-- Gentle Serene Smile Line -->
    <path d="M214 101 C214 105, 222 105, 222 101" stroke="#421400" stroke-width="2.4" stroke-linecap="round" fill="none"/>

    <!-- Subtle Forehead Sparkle Dot -->
    <circle cx="218" cy="81" r="2" fill="#FFEAA0"/>
  </g>

  <!-- 5. Big Radiant 4-Point Sparkle Star (Twinkling & Breathing) -->
  <g transform="translate(156, 72)" class="star-twinkle">
    <!-- SVG SMIL scale animation -->
    <animateTransform attributeName="transform" type="scale" values="1;1.22;1" dur="2.6s" repeatCount="indefinite" transform-origin="156 72" additive="sum"/>
    <path d="M0 -17 C0 -7, -7 0, -17 0 C-7 0, 0 7, 0 17 C0 7, 7 0, 17 0 C7 0, 0 -7, 0 -17 Z" fill="#FFFFFF">
      <animate attributeName="opacity" values="0.8;1;0.8" dur="2.6s" repeatCount="indefinite"/>
    </path>
  </g>

  <!-- 6. Secondary Starlet (Near Character) -->
  <g transform="translate(178, 98)">
    <path d="M0 -8 C0 -3.5, -3.5 0, -8 0 C-3.5 0, 0 3.5, 0 8 C0 3.5, 3.5 0, 8 0 C3.5 0, 0 -3.5, 0 -8 Z" fill="#FFFFFF">
      <animate attributeName="opacity" values="0.45;0.95;0.45" dur="3s" repeatCount="indefinite"/>
    </path>
  </g>

  <!-- 7. Ambient Twinkling Cosmic Sparkles -->
  <circle cx="106" cy="46" r="2.5" fill="#FFFFFF">
    <animate attributeName="opacity" values="0.25;0.9;0.25" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="272" cy="54" r="2.2" fill="#FFFFFF">
    <animate attributeName="opacity" values="0.3;0.95;0.3" dur="2.8s" repeatCount="indefinite"/>
  </circle>
  <circle cx="290" cy="100" r="1.8" fill="#FFFFFF">
    <animate attributeName="opacity" values="0.2;0.8;0.2" dur="3.4s" repeatCount="indefinite"/>
  </circle>
  <circle cx="74" cy="92" r="2" fill="#FFFFFF">
    <animate attributeName="opacity" values="0.3;0.85;0.3" dur="3.8s" repeatCount="indefinite"/>
  </circle>
</svg>
"""


def render_email(
    title: str,
    content_html: str,
    *,
    preheader: str = "",
    headline: str = "",
    lead_text: str = "",
) -> str:
    """Wraps body content in the ultra-aesthetic, Headspace-inspired layout."""
    hidden_preheader = (
        f'<div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">{preheader}</div>'
        if preheader
        else ""
    )
    frontend_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
    app_name = settings.APP_NAME or "DivinLink"
    support_email = settings.SUPPORT_EMAIL or "help@divinlink.com"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <meta name="supported-color-schemes" content="light" />
  <title>{title}</title>
  <style type="text/css">
    @keyframes floatCelestial {{
      0% {{ transform: translateY(0px); }}
      50% {{ transform: translateY(-6px); }}
      100% {{ transform: translateY(0px); }}
    }}
    @keyframes pulseSparkle {{
      0% {{ opacity: 0.75; transform: scale(1); }}
      50% {{ opacity: 1; transform: scale(1.15); }}
      100% {{ opacity: 0.75; transform: scale(1); }}
    }}
    @keyframes ctaHover {{
      0% {{ box-shadow: 0 6px 18px rgba(255,107,0,0.35); }}
      50% {{ box-shadow: 0 10px 24px rgba(255,107,0,0.48); }}
      100% {{ box-shadow: 0 6px 18px rgba(255,107,0,0.35); }}
    }}
    .celestial-float {{
      animation: floatCelestial 3.6s ease-in-out infinite;
    }}
    .star-twinkle {{
      animation: pulseSparkle 2.6s ease-in-out infinite;
    }}
    .cta-button:hover {{
      background: linear-gradient(135deg, #FF851A 0%, #FF4500 100%) !important;
      transform: translateY(-1px);
    }}
    .digit-box:hover {{
      border-color: #EA580C !important;
      background-color: #FFF3E6 !important;
    }}
  </style>
  <!--[if mso]>
  <style type="text/css">
    body, table, td, p, a, span {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif !important; }}
  </style>
  <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#FAF8F5;font-family:-apple-system,BlinkMacSystemFont,'Plus Jakarta Sans','Inter',Roboto,'Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;">
  {hidden_preheader}

  <!-- Main Viewport Table -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#FAF8F5;min-height:100vh;">
    <tr>
      <td align="center" style="padding:28px 14px 56px;">

        <!-- Outer Card (Max Width 520px matching Headspace proportions) -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;background:#ffffff;border-radius:28px;overflow:hidden;box-shadow:0 8px 32px rgba(26,18,8,0.04);border:1px solid #F3EFEA;">

          <!-- 1. Header with Headspace-styled Brand Logo -->
          <tr>
            <td align="center" style="padding:36px 32px 24px;">
              <a href="{frontend_url}" target="_blank" style="text-decoration:none;display:inline-block;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="vertical-align:middle;padding-right:9px;">
                      <!-- Warm Orange Sun Circle (Matching Headspace Icon Style) -->
                      <div style="width:34px;height:34px;border-radius:50%;background:#FF6B00;background:linear-gradient(135deg,#FF7A00 0%,#FF5000 100%);text-align:center;line-height:34px;color:#ffffff;font-size:16px;box-shadow:0 3px 10px rgba(255,107,0,0.35);">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;display:inline-block;">
                          <circle cx="12" cy="12" r="4.5" fill="#FFFFFF"/>
                          <path d="M12 2V5M12 19V22M2 12H5M19 12H22M4.93 4.93L7.05 7.05M16.95 16.95L19.07 19.07M4.93 19.07L7.05 16.95M16.95 7.05L19.07 4.93" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                      </div>
                    </td>
                    <td style="vertical-align:middle;">
                      <span style="font-size:23px;font-weight:800;color:#18181B;letter-spacing:-0.5px;font-family:-apple-system,BlinkMacSystemFont,'Plus Jakarta Sans','Inter',sans-serif;">
                        {app_name.lower()}
                      </span>
                    </td>
                  </tr>
                </table>
              </a>
            </td>
          </tr>

          <!-- 2. Hero Vector Illustration (Warm Sunny Arched Art with Floating Sun) -->
          <tr>
            <td align="center" style="padding:0 32px;">
              {_animated_hero_illustration_svg()}
            </td>
          </tr>

          <!-- 3. Headline & Human-Crafted Lead Copy -->
          <tr>
            <td align="center" style="padding:28px 36px 0;">
              {f'<h1 style="margin:0 0 14px;font-size:31px;font-weight:800;color:#111827;line-height:1.25;letter-spacing:-0.7px;text-align:center;font-family:-apple-system,BlinkMacSystemFont,\'Plus Jakarta Sans\',sans-serif;">{headline}</h1>' if headline else ''}
              {f'<p style="margin:0 auto 26px;font-size:15px;line-height:1.68;color:#4B5563;text-align:center;max-width:430px;font-weight:400;">{lead_text}</p>' if lead_text else ''}
            </td>
          </tr>

          <!-- 4. Action Section (Tiles / Pill Button) -->
          <tr>
            <td align="center" style="padding:0 36px 36px;">
              {content_html}

              <!-- Support Text Box (Matching Headspace Screenshot Wording) -->
              <p style="margin:36px auto 0;font-size:13px;line-height:1.65;color:#6B7280;text-align:center;max-width:420px;font-weight:400;">
                If you have any questions, please visit our
                <a href="{frontend_url}" target="_blank" style="color:#EA580C;font-weight:700;text-decoration:none;">FAQs</a>
                or email us at
                <a href="mailto:{support_email}" style="color:#EA580C;font-weight:700;text-decoration:none;">{support_email}</a>.
                Our team can answer questions about your account or help you with your Vedic astrology practice.
              </p>

              <!-- Subtle Divider -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:32px 0 22px;">
                <tr>
                  <td align="center">
                    <div style="width:56px;height:1px;background-color:#E5E7EB;"></div>
                  </td>
                </tr>
              </table>

              <!-- Minimalist Social Icons -->
              {_SOCIAL_ICONS_ROW}

              <!-- Footer Sub-Navigation Links -->
              <p style="margin:0 0 14px;font-size:12px;font-weight:500;color:#6B7280;text-align:center;letter-spacing:0.2px;">
                <a href="{frontend_url}/account" target="_blank" style="color:#6B7280;text-decoration:none;">My {app_name}</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="{frontend_url}" target="_blank" style="color:#6B7280;text-decoration:none;">How it works</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="{frontend_url}" target="_blank" style="color:#6B7280;text-decoration:none;">FAQs</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="{frontend_url}" target="_blank" style="color:#6B7280;text-decoration:none;">T&amp;Cs</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="{frontend_url}" target="_blank" style="color:#6B7280;text-decoration:none;">Privacy Policy</a>
              </p>

              <!-- Legal / Brand Note -->
              <p style="margin:0;font-size:11px;line-height:1.65;color:#9CA3AF;text-align:center;">
                You have received this email as a registered user of {app_name}&reg;<br />
                {app_name}, Inc. &bull; Authentic Vedic Wisdom &amp; Ephemeris Calculations<br />
                &copy; 2026 {app_name}. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
        <!-- End Outer Card -->

      </td>
    </tr>
  </table>
</body>
</html>"""


def otp_email_html(code: str, purpose: str, name: str | None = None) -> str:
    """Renders the aesthetic OTP verification email with letterpress digit cards and pill button."""
    frontend_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
    app_name = settings.APP_NAME or "DivinLink"

    headlines = {
        "signup": "Verify your email address",
        "login": "Sign in to DivinLink",
        "email_verification": "Verify your email address",
        "password_reset": "Reset your password",
    }
    headline = headlines.get(purpose, "Verify your email address")

    lead_copies = {
        "signup": (
            f"You’re so close to starting your {app_name} journey. To finish signing up, "
            f"just click the button below or enter the verification code. "
            f"The link will be valid for the next {settings.OTP_EXPIRE_MINUTES} minutes."
        ),
        "login": (
            f"Welcome back! Enter the verification code below to securely sign in to your "
            f"{app_name} account. The code will be valid for the next {settings.OTP_EXPIRE_MINUTES} minutes."
        ),
        "email_verification": (
            f"Please verify your email address to keep your {app_name} account secure. "
            f"Use the verification code below or click the button to continue."
        ),
        "password_reset": (
            f"We received a request to reset your {app_name} password. "
            f"Use the verification code below to choose a new password."
        ),
    }
    lead_text = lead_copies.get(
        purpose,
        f"You’re so close to starting your {app_name} journey. Use the code below to continue.",
    )

    action_button_label = "Verify my email" if purpose in ("signup", "email_verification") else "Continue to DivinLink"
    action_url = f"{frontend_url}/login" if purpose == "login" else f"{frontend_url}/register"

    # Split 6-digit code into individual letterpress cards for maximum bespoke feel
    digits = [c for c in code.strip() if c.isalnum()][:6]
    while len(digits) < 6:
        digits.append(" ")

    digit_cards_html = "".join(
        f"""
        <td style="padding:0 4px;">
          <div class="digit-box" style="width:42px;height:54px;line-height:54px;text-align:center;background:#FFF9F2;border:1.5px solid #FDBA74;border-radius:12px;font-size:26px;font-weight:800;color:#C2410C;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;box-shadow:0 2px 6px rgba(234,88,12,0.06);transition:all .2s ease;">
            {d}
          </div>
        </td>
        """
        for d in digits
    )

    content = f"""
      <!-- Bespoke 6-Digit Letterpress Cards -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 22px;">
        <tr>
          {digit_cards_html}
        </tr>
      </table>

      <!-- Headspace-Style Vibrant Rounded Pill Button -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 16px;">
        <tr>
          <td align="center">
            <a href="{action_url}" target="_blank" class="cta-button" style="display:inline-block;background:#FF6B00;background:linear-gradient(135deg,#FF7A00 0%,#FF5500 100%);color:#ffffff;font-size:16px;font-weight:700;padding:16px 44px;border-radius:9999px;text-decoration:none;text-align:center;box-shadow:0 6px 20px rgba(255,107,0,0.38);letter-spacing:-0.2px;">
              {action_button_label}
            </a>
          </td>
        </tr>
      </table>

      <!-- Expiry Notice -->
      <p style="margin:0 auto;font-size:12.5px;color:#9CA3AF;text-align:center;font-weight:500;">
        The code will be valid for the next {settings.OTP_EXPIRE_MINUTES} minutes.
      </p>
    """

    return render_email(
        title=headline,
        content_html=content,
        preheader=f"{code} is your {app_name} verification code",
        headline=headline,
        lead_text=lead_text,
    )


def welcome_email_html(name: str | None = None) -> str:
    """Welcome onboarding email introducing the user to DivinLink with visual feature cards."""
    frontend_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
    app_name = settings.APP_NAME or "DivinLink"
    greeting_name = f", {name}" if name else ""

    headline = f"Welcome to {app_name}{greeting_name}!"
    lead_text = (
        f"You’re officially part of the {app_name} family. Discover authentic Vedic astrology, "
        f"Swiss Ephemeris precision charts, and daily spiritual guidance curated for your journey."
    )

    content = f"""
      <!-- Lifestyle Feature Cards -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px;">
        <tr>
          <td style="padding:15px 18px;background:#FFFBF5;border:1px solid #FED7AA;border-radius:16px;text-align:left;">
            <p style="margin:0 0 4px;font-size:14px;font-weight:700;color:#9A3412;">
              &#10022; Authentic Vedic Kundli &amp; Dasha
            </p>
            <p style="margin:0;font-size:13px;line-height:1.55;color:#4B5563;">
              Full birth chart, planetary degrees, divisional charts and Vimshottari Mahadasha predictions.
            </p>
          </td>
        </tr>
        <tr><td style="height:10px;"></td></tr>
        <tr>
          <td style="padding:15px 18px;background:#FFFBF5;border:1px solid #FED7AA;border-radius:16px;text-align:left;">
            <p style="margin:0 0 4px;font-size:14px;font-weight:700;color:#9A3412;">
              &#10022; Numerology &amp; Lo Shu Grid
            </p>
            <p style="margin:0;font-size:13px;line-height:1.55;color:#4B5563;">
              Discover your Mulank, Bhagyank, lucky colors, business numerology and name correction.
            </p>
          </td>
        </tr>
        <tr><td style="height:10px;"></td></tr>
        <tr>
          <td style="padding:15px 18px;background:#FFFBF5;border:1px solid #FED7AA;border-radius:16px;text-align:left;">
            <p style="margin:0 0 4px;font-size:14px;font-weight:700;color:#9A3412;">
              &#10022; AI Astrologer &amp; Daily Panchang
            </p>
            <p style="margin:0;font-size:13px;line-height:1.55;color:#4B5563;">
              24/7 authentic Vedic AI consultation, auspicious Muhurat timings, and daily planetary hora.
            </p>
          </td>
        </tr>
      </table>

      <!-- Pill Button -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 16px;">
        <tr>
          <td align="center">
            <a href="{frontend_url}" target="_blank" class="cta-button" style="display:inline-block;background:#FF6B00;background:linear-gradient(135deg,#FF7A00 0%,#FF5500 100%);color:#ffffff;font-size:16px;font-weight:700;padding:16px 44px;border-radius:9999px;text-decoration:none;text-align:center;box-shadow:0 6px 20px rgba(255,107,0,0.38);letter-spacing:-0.2px;">
              Explore your journey &rarr;
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:0 auto;font-size:12.5px;color:#9CA3AF;text-align:center;font-weight:500;">
        Add your birth date, time, and location to generate your complete chart.
      </p>
    """

    return render_email(
        title=f"Welcome to {app_name}",
        content_html=content,
        preheader=f"Your {app_name} account is ready. Discover your personalized charts.",
        headline=headline,
        lead_text=lead_text,
    )


def astrologer_welcome_email_html(name: str, email: str, password: str) -> str:
    """Sent when an astrologer account is created with temporary credentials."""
    frontend_url = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app")
    app_name = settings.APP_NAME or "DivinLink"

    headline = f"Welcome to {app_name}"
    lead_text = (
        f"Welcome, {name}! An astrologer account has been created for you on {app_name}. "
        f"Below are your temporary sign-in credentials to access the portal:"
    )

    content = f"""
      <!-- Credentials Card -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 24px;background:#FFF9F2;border:1.5px solid #FED7AA;border-radius:18px;">
        <tr>
          <td style="padding:22px 24px;text-align:left;">
            <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9A3412;text-transform:uppercase;letter-spacing:1px;">
              Email Address
            </p>
            <p style="margin:0 0 16px;font-size:15px;font-weight:600;color:#1F2937;">
              {email}
            </p>
            <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9A3412;text-transform:uppercase;letter-spacing:1px;">
              Temporary Password
            </p>
            <p style="margin:0;font-size:22px;font-weight:800;letter-spacing:2px;color:#C2410C;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;">
              {password}
            </p>
          </td>
        </tr>
      </table>

      <!-- Pill Button -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 16px;">
        <tr>
          <td align="center">
            <a href="{frontend_url}/login" target="_blank" class="cta-button" style="display:inline-block;background:#FF6B00;background:linear-gradient(135deg,#FF7A00 0%,#FF5500 100%);color:#ffffff;font-size:16px;font-weight:700;padding:16px 44px;border-radius:9999px;text-decoration:none;text-align:center;box-shadow:0 6px 20px rgba(255,107,0,0.38);letter-spacing:-0.2px;">
              Sign in to Astrologer Portal &rarr;
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:0 auto;font-size:12px;color:#9A3412;background:#FEF3C7;padding:8px 14px;border-radius:8px;display:inline-block;text-align:center;">
        &#9888; <strong>Security notice:</strong> Please change this password immediately after your first sign-in.
      </p>
    """

    return render_email(
        title=f"Your {app_name} astrologer account",
        content_html=content,
        preheader=f"Welcome to {app_name}, {name}. Here are your credentials.",
        headline=headline,
        lead_text=lead_text,
    )
