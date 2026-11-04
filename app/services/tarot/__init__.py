"""Tarot Card Service Package."""

from app.services.tarot.cards_data import ALL_TAROT_CARDS, TAROT_DECK_BY_ID
from app.services.tarot.spreads_data import ALL_SPREADS, SPREADS_BY_ID
from app.services.tarot.engine import (
    get_all_cards,
    get_card_by_id,
    get_all_spreads,
    get_spread_by_id,
    draw_tarot_spread,
    get_daily_tarot_card,
)

__all__ = [
    "ALL_TAROT_CARDS",
    "TAROT_DECK_BY_ID",
    "ALL_SPREADS",
    "SPREADS_BY_ID",
    "get_all_cards",
    "get_card_by_id",
    "get_all_spreads",
    "get_spread_by_id",
    "draw_tarot_spread",
    "get_daily_tarot_card",
]
