"""Master multilingual translation dictionary for all 108 Lal Kitab combinations."""

from app.services.astrology.translations.sun import SUN_TRANSLATIONS
from app.services.astrology.translations.moon import MOON_TRANSLATIONS
from app.services.astrology.translations.mars import MARS_TRANSLATIONS
from app.services.astrology.translations.mercury import MERCURY_TRANSLATIONS
from app.services.astrology.translations.jupiter import JUPITER_TRANSLATIONS
from app.services.astrology.translations.venus import VENUS_TRANSLATIONS
from app.services.astrology.translations.saturn import SATURN_TRANSLATIONS
from app.services.astrology.translations.rahu import RAHU_TRANSLATIONS
from app.services.astrology.translations.ketu import KETU_TRANSLATIONS

LAL_KITAB_TRANSLATIONS: dict[str, dict[str, list[str]]] = {
    **SUN_TRANSLATIONS,
    **MOON_TRANSLATIONS,
    **MARS_TRANSLATIONS,
    **MERCURY_TRANSLATIONS,
    **JUPITER_TRANSLATIONS,
    **VENUS_TRANSLATIONS,
    **SATURN_TRANSLATIONS,
    **RAHU_TRANSLATIONS,
    **KETU_TRANSLATIONS,
}
