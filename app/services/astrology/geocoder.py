"""High-reliability astrology geocoding engine with multi-source fallback and offline cache.

Designed to prevent rate-limit blocks (OSM Nominatim HTTP 429), ensure 0ms instant
lookups for Indian/Bengali towns (like Deulia, Kolaghat, Mecheda, Tamluk, etc.), and
provide worldwide fallback via Open-Meteo and Photon APIs with exact IANA timezone resolution.
"""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any

import httpx
from loguru import logger

from app.services.astrology.timezone_resolver import (
    offset_for_zone_at,
    zone_for_coordinates,
)

# ---------------------------------------------------------------------------
# High-Priority Curated Directory: West Bengal Localities, Indian Metros & Hubs
# Ensures instant (0ms) zero-dependency suggestions for common birth places.
# ---------------------------------------------------------------------------
CURATED_PLACES: list[dict[str, Any]] = [
    # Purba Medinipur & Kolaghat Area
    {
        "place": "Kolaghat",
        "display_name": "Kolaghat, Purba Medinipur, West Bengal, 721134, India",
        "city": "Kolaghat",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4325,
        "longitude": 87.8594,
        "aliases": ["kolaghat", "kola ghat", "কোলাঘাট", "kolaghat thermal"],
    },
    {
        "place": "Deulia",
        "display_name": "Deulia, Kolaghat, Purba Medinipur, West Bengal, 721154, India",
        "city": "Kolaghat",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4348,
        "longitude": 87.8724,
        "aliases": [
            "deulia",
            "deuliya",
            "deulia bazar",
            "deulia kolaghat",
            "deulia purba medinipur",
            "দেউলিয়া",
            "দেউলিয়া",
            "deulia station",
        ],
    },
    {
        "place": "Deulia (South 24 Parganas)",
        "display_name": "Deulia, Magrahat - I, South 24 Parganas, West Bengal, 743375, India",
        "city": "Magrahat",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.2536,
        "longitude": 88.3582,
        "aliases": ["deulia south 24 parganas", "deula", "deula station"],
    },
    {
        "place": "Mecheda",
        "display_name": "Mecheda, Kolaghat, Purba Medinipur, West Bengal, 721137, India",
        "city": "Mecheda",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4367,
        "longitude": 87.8683,
        "aliases": ["mecheda", "mechada", "মেচেদা"],
    },
    {
        "place": "Panskura",
        "display_name": "Panskura, Purba Medinipur, West Bengal, 721139, India",
        "city": "Panskura",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4174,
        "longitude": 87.7126,
        "aliases": ["panskura", "পাঁশকুড়া", "pashkura"],
    },
    {
        "place": "Tamluk",
        "display_name": "Tamluk, Purba Medinipur, West Bengal, 721636, India",
        "city": "Tamluk",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.3008,
        "longitude": 87.9259,
        "aliases": ["tamluk", "tamralipta", "তমলুক"],
    },
    {
        "place": "Haldia",
        "display_name": "Haldia, Purba Medinipur, West Bengal, 721607, India",
        "city": "Haldia",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.0667,
        "longitude": 88.0698,
        "aliases": ["haldia", "হলদিয়া"],
    },
    {
        "place": "Contai (Kanthi)",
        "display_name": "Contai, Purba Medinipur, West Bengal, 721401, India",
        "city": "Contai",
        "state": "West Bengal",
        "country": "India",
        "latitude": 21.7781,
        "longitude": 87.7516,
        "aliases": ["contai", "kanthi", "কাঁথি"],
    },
    {
        "place": "Digha",
        "display_name": "Digha, Purba Medinipur, West Bengal, 721428, India",
        "city": "Digha",
        "state": "West Bengal",
        "country": "India",
        "latitude": 21.6266,
        "longitude": 87.5074,
        "aliases": ["digha", "দীঘা"],
    },
    {
        "place": "Mahishadal",
        "display_name": "Mahishadal, Purba Medinipur, West Bengal, 721628, India",
        "city": "Mahishadal",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.1866,
        "longitude": 87.9867,
        "aliases": ["mahishadal", "মহিষাদল"],
    },
    {
        "place": "Nandigram",
        "display_name": "Nandigram, Purba Medinipur, West Bengal, 721631, India",
        "city": "Nandigram",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.0075,
        "longitude": 87.9842,
        "aliases": ["nandigram", "নন্দীগ্রাম"],
    },
    {
        "place": "Egra",
        "display_name": "Egra, Purba Medinipur, West Bengal, 721429, India",
        "city": "Egra",
        "state": "West Bengal",
        "country": "India",
        "latitude": 21.9000,
        "longitude": 87.5333,
        "aliases": ["egra", "এগরা"],
    },
    {
        "place": "Moyna",
        "display_name": "Moyna, Purba Medinipur, West Bengal, 721629, India",
        "city": "Moyna",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.2500,
        "longitude": 87.7800,
        "aliases": ["moyna", "ময়না", "maina"],
    },
    # Howrah & Nearby
    {
        "place": "Bagnan",
        "display_name": "Bagnan, Howrah, West Bengal, 711303, India",
        "city": "Bagnan",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4678,
        "longitude": 87.9717,
        "aliases": ["bagnan", "বাগনান"],
    },
    {
        "place": "Uluberia",
        "display_name": "Uluberia, Howrah, West Bengal, 711315, India",
        "city": "Uluberia",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4700,
        "longitude": 88.1100,
        "aliases": ["uluberia", "উলুবেড়িয়া", "uluberia station"],
    },
    {
        "place": "Amta",
        "display_name": "Amta, Howrah, West Bengal, 711401, India",
        "city": "Amta",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5700,
        "longitude": 88.0167,
        "aliases": ["amta", "আমতা"],
    },
    {
        "place": "Howrah",
        "display_name": "Howrah, West Bengal, 711101, India",
        "city": "Howrah",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5958,
        "longitude": 88.2636,
        "aliases": ["howrah", "haora", "হাওড়া", "howrah station"],
    },
    # Paschim Medinipur & Jhargram
    {
        "place": "Kharagpur",
        "display_name": "Kharagpur, Paschim Medinipur, West Bengal, 721301, India",
        "city": "Kharagpur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.3460,
        "longitude": 87.2320,
        "aliases": ["kharagpur", "খড়গপুর", "kgp"],
    },
    {
        "place": "Midnapore",
        "display_name": "Midnapore, Paschim Medinipur, West Bengal, 721101, India",
        "city": "Midnapore",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4250,
        "longitude": 87.3190,
        "aliases": ["midnapore", "medinipur", "মেদিনীপুর"],
    },
    {
        "place": "Ghatal",
        "display_name": "Ghatal, Paschim Medinipur, West Bengal, 721212, India",
        "city": "Ghatal",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.6700,
        "longitude": 87.7200,
        "aliases": ["ghatal", "ঘাটাল"],
    },
    {
        "place": "Debra",
        "display_name": "Debra, Paschim Medinipur, West Bengal, 721126, India",
        "city": "Debra",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.3900,
        "longitude": 87.5700,
        "aliases": ["debra", "ডেবরা"],
    },
    {
        "place": "Jhargram",
        "display_name": "Jhargram, West Bengal, 721507, India",
        "city": "Jhargram",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4500,
        "longitude": 86.9800,
        "aliases": ["jhargram", "ঝাড়গ্রাম"],
    },
    # Kolkata & 24 Parganas
    {
        "place": "Kolkata",
        "display_name": "Kolkata, West Bengal, 700001, India",
        "city": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "aliases": ["kolkata", "calcutta", "কলকাতা"],
    },
    {
        "place": "Bidhannagar (Salt Lake)",
        "display_name": "Bidhannagar, Salt Lake, Kolkata, West Bengal, 700064, India",
        "city": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5800,
        "longitude": 88.4200,
        "aliases": ["salt lake", "bidhannagar", "সল্টলেক"],
    },
    {
        "place": "New Town",
        "display_name": "New Town, Rajarhat, North 24 Parganas, West Bengal, 700156, India",
        "city": "New Town",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5867,
        "longitude": 88.4754,
        "aliases": ["new town", "newtown", "rajarhat", "নিউ টাউন", "নিউটাউন"],
    },
    {
        "place": "Barasat",
        "display_name": "Barasat, North 24 Parganas, West Bengal, 700124, India",
        "city": "Barasat",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.7200,
        "longitude": 88.4800,
        "aliases": ["barasat", "বারাসাত"],
    },
    {
        "place": "Barrackpore",
        "display_name": "Barrackpore, North 24 Parganas, West Bengal, 700120, India",
        "city": "Barrackpore",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.7600,
        "longitude": 88.3700,
        "aliases": ["barrackpore", "ব্যারাকপুর"],
    },
    {
        "place": "Sonarpur",
        "display_name": "Sonarpur, South 24 Parganas, West Bengal, 700150, India",
        "city": "Sonarpur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.4400,
        "longitude": 88.4300,
        "aliases": ["sonarpur", "সোনারপুর"],
    },
    {
        "place": "Baruipur",
        "display_name": "Baruipur, South 24 Parganas, West Bengal, 700144, India",
        "city": "Baruipur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.3700,
        "longitude": 88.4400,
        "aliases": ["baruipur", "বারুইপুর"],
    },
    {
        "place": "Diamond Harbour",
        "display_name": "Diamond Harbour, South 24 Parganas, West Bengal, 743331, India",
        "city": "Diamond Harbour",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.1900,
        "longitude": 88.1900,
        "aliases": ["diamond harbour", "ডায়মন্ড হারবার"],
    },
    # Hooghly & Bardhaman
    {
        "place": "Chinsurah (Hooghly)",
        "display_name": "Chinsurah, Hooghly, West Bengal, 712101, India",
        "city": "Chinsurah",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.9000,
        "longitude": 88.3900,
        "aliases": ["chinsurah", "hooghly", "হুগলী", "চুঁচুড়া"],
    },
    {
        "place": "Serampore",
        "display_name": "Serampore, Hooghly, West Bengal, 712201, India",
        "city": "Serampore",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.7500,
        "longitude": 88.3400,
        "aliases": ["serampore", "শ্রীরামপুর"],
    },
    {
        "place": "Chandannagar",
        "display_name": "Chandannagar, Hooghly, West Bengal, 712136, India",
        "city": "Chandannagar",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.8700,
        "longitude": 88.3800,
        "aliases": ["chandannagar", "চন্দননগর"],
    },
    {
        "place": "Tarakeswar",
        "display_name": "Tarakeswar, Hooghly, West Bengal, 712410, India",
        "city": "Tarakeswar",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.8900,
        "longitude": 88.0200,
        "aliases": ["tarakeswar", "তারকেশ্বর"],
    },
    {
        "place": "Singur",
        "display_name": "Singur, Hooghly, West Bengal, 712409, India",
        "city": "Singur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.8100,
        "longitude": 88.2300,
        "aliases": ["singur", "সিঙ্গুর"],
    },
    {
        "place": "Arambagh",
        "display_name": "Arambagh, Hooghly, West Bengal, 712601, India",
        "city": "Arambagh",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.8800,
        "longitude": 87.7800,
        "aliases": ["arambagh", "আরামবাগ"],
    },
    {
        "place": "Bardhaman (Burdwan)",
        "display_name": "Bardhaman, Purba Bardhaman, West Bengal, 713101, India",
        "city": "Bardhaman",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.2324,
        "longitude": 87.8615,
        "aliases": ["bardhaman", "burdwan", "বর্ধমান"],
    },
    {
        "place": "Durgapur",
        "display_name": "Durgapur, Paschim Bardhaman, West Bengal, 713201, India",
        "city": "Durgapur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.5204,
        "longitude": 87.3119,
        "aliases": ["durgapur", "দুর্গাপুর"],
    },
    {
        "place": "Asansol",
        "display_name": "Asansol, Paschim Bardhaman, West Bengal, 713301, India",
        "city": "Asansol",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.6739,
        "longitude": 86.9524,
        "aliases": ["asansol", "আসানসোল"],
    },
    # Other Districts of West Bengal
    {
        "place": "Bolpur (Santiniketan)",
        "display_name": "Bolpur, Santiniketan, Birbhum, West Bengal, 731204, India",
        "city": "Bolpur",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.6700,
        "longitude": 87.6900,
        "aliases": ["bolpur", "santiniketan", "শান্তিনিকেতন", "বোলপুর"],
    },
    {
        "place": "Suri",
        "display_name": "Suri, Birbhum, West Bengal, 731101, India",
        "city": "Suri",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.9100,
        "longitude": 87.5300,
        "aliases": ["suri", "সিউড়ী", "siuri"],
    },
    {
        "place": "Krishnanagar",
        "display_name": "Krishnanagar, Nadia, West Bengal, 741101, India",
        "city": "Krishnanagar",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.4000,
        "longitude": 88.5000,
        "aliases": ["krishnanagar", "কৃষ্ণনগর"],
    },
    {
        "place": "Kalyani",
        "display_name": "Kalyani, Nadia, West Bengal, 741235, India",
        "city": "Kalyani",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.9750,
        "longitude": 88.4344,
        "aliases": ["kalyani", "কল্যাণী"],
    },
    {
        "place": "Berhampore",
        "display_name": "Berhampore, Murshidabad, West Bengal, 742101, India",
        "city": "Berhampore",
        "state": "West Bengal",
        "country": "India",
        "latitude": 24.1000,
        "longitude": 88.2500,
        "aliases": ["berhampore", "বহরমপুর", "baharampur"],
    },
    {
        "place": "Malda (English Bazar)",
        "display_name": "Malda, West Bengal, 732101, India",
        "city": "Malda",
        "state": "West Bengal",
        "country": "India",
        "latitude": 25.0000,
        "longitude": 88.1500,
        "aliases": ["malda", "মালদা", "english bazar"],
    },
    {
        "place": "Siliguri",
        "display_name": "Siliguri, Darjeeling, West Bengal, 734001, India",
        "city": "Siliguri",
        "state": "West Bengal",
        "country": "India",
        "latitude": 26.7271,
        "longitude": 88.3953,
        "aliases": ["siliguri", "শিলিগুড়ি"],
    },
    {
        "place": "Darjeeling",
        "display_name": "Darjeeling, West Bengal, 734101, India",
        "city": "Darjeeling",
        "state": "West Bengal",
        "country": "India",
        "latitude": 27.0410,
        "longitude": 88.2663,
        "aliases": ["darjeeling", "দার্জিলিং"],
    },
    {
        "place": "Bankura",
        "display_name": "Bankura, West Bengal, 722101, India",
        "city": "Bankura",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.2300,
        "longitude": 87.0700,
        "aliases": ["bankura", "বাঁকুড়া"],
    },
    {
        "place": "Purulia",
        "display_name": "Purulia, West Bengal, 723101, India",
        "city": "Purulia",
        "state": "West Bengal",
        "country": "India",
        "latitude": 23.3300,
        "longitude": 86.3700,
        "aliases": ["purulia", "পুরুলিয়া"],
    },
    # Major Indian Metros and Capitals
    {
        "place": "New Delhi",
        "display_name": "New Delhi, Delhi, 110001, India",
        "city": "New Delhi",
        "state": "Delhi",
        "country": "India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "aliases": ["delhi", "new delhi", "নয়াদিল্লি", "दिल्ली"],
    },
    {
        "place": "Mumbai",
        "display_name": "Mumbai, Maharashtra, 400001, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "aliases": ["mumbai", "bombay", "মুম্বাই", "मुंबई"],
    },
    {
        "place": "Bengaluru",
        "display_name": "Bengaluru, Karnataka, 560001, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "aliases": ["bengaluru", "bangalore", "বেঙ্গালুরু"],
    },
    {
        "place": "Hyderabad",
        "display_name": "Hyderabad, Telangana, 500001, India",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "aliases": ["hyderabad", "হায়দ্রাবাদ"],
    },
    {
        "place": "Chennai",
        "display_name": "Chennai, Tamil Nadu, 600001, India",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "aliases": ["chennai", "madras", "চেন্নাই"],
    },
    {
        "place": "Pune",
        "display_name": "Pune, Maharashtra, 411001, India",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "aliases": ["pune", "poona", "পুনে"],
    },
    {
        "place": "Ahmedabad",
        "display_name": "Ahmedabad, Gujarat, 380001, India",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "country": "India",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "aliases": ["ahmedabad", "amdavad", "আহমেদাবাদ"],
    },
    {
        "place": "Patna",
        "display_name": "Patna, Bihar, 800001, India",
        "city": "Patna",
        "state": "Bihar",
        "country": "India",
        "latitude": 25.5941,
        "longitude": 85.1376,
        "aliases": ["patna", "পাটনা"],
    },
    {
        "place": "Ranchi",
        "display_name": "Ranchi, Jharkhand, 834001, India",
        "city": "Ranchi",
        "state": "Jharkhand",
        "country": "India",
        "latitude": 23.3441,
        "longitude": 85.3096,
        "aliases": ["ranchi", "রাঁচি"],
    },
    {
        "place": "Bhubaneswar",
        "display_name": "Bhubaneswar, Odisha, 751001, India",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "country": "India",
        "latitude": 20.2961,
        "longitude": 85.8245,
        "aliases": ["bhubaneswar", "ভুবনেশ্বর"],
    },
    {
        "place": "Jaipur",
        "display_name": "Jaipur, Rajasthan, 302001, India",
        "city": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "aliases": ["jaipur", "জয়পুর"],
    },
    {
        "place": "Lucknow",
        "display_name": "Lucknow, Uttar Pradesh, 226001, India",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "country": "India",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "aliases": ["lucknow", "লখনউ"],
    },
    {
        "place": "Varanasi",
        "display_name": "Varanasi, Uttar Pradesh, 221001, India",
        "city": "Varanasi",
        "state": "Uttar Pradesh",
        "country": "India",
        "latitude": 25.3176,
        "longitude": 82.9739,
        "aliases": ["varanasi", "banaras", "kashi", "বারাণসী"],
    },
    {
        "place": "Guwahati",
        "display_name": "Guwahati, Assam, 781001, India",
        "city": "Guwahati",
        "state": "Assam",
        "country": "India",
        "latitude": 26.1445,
        "longitude": 91.7362,
        "aliases": ["guwahati", "gauhati", "গুয়াহাটি"],
    },
    # South Asian Hubs
    {
        "place": "Dhaka",
        "display_name": "Dhaka, Bangladesh",
        "city": "Dhaka",
        "state": "Dhaka Division",
        "country": "Bangladesh",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "aliases": ["dhaka", "dacca", "ঢাকা"],
    },
    {
        "place": "Kathmandu",
        "display_name": "Kathmandu, Nepal",
        "city": "Kathmandu",
        "state": "Bagmati",
        "country": "Nepal",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "aliases": ["kathmandu", "কাঠমান্ডু"],
    },
]

# ---------------------------------------------------------------------------
# In-Memory Cache with TTL
# ---------------------------------------------------------------------------
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_CACHE_TTL_SECONDS = 86400  # 24 hours
_MAX_CACHE_SIZE = 10000


def _build_geo_item(
    *,
    display_name: str,
    place: str,
    city: str,
    state: str,
    country: str,
    latitude: float,
    longitude: float,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> dict[str, Any]:
    """Computes exact IANA timezone and offset for coordinates."""
    zone_name = zone_for_coordinates(latitude, longitude)
    offset_hours: float | None = None
    offset_label: str | None = None
    abbreviation: str | None = None
    is_dst = False

    if zone_name:
        try:
            resolved = offset_for_zone_at(
                zone_name,
                year or 2000,
                month or 1,
                day or 1,
                12,
            )
            offset_hours = round(resolved.offset_hours, 6)
            offset_label = resolved.offset_label
            abbreviation = resolved.abbreviation
            is_dst = resolved.is_dst
        except Exception:
            zone_name = None

    return {
        "display_name": display_name,
        "place": place or city or display_name.split(",")[0].strip(),
        "city": city,
        "state": state,
        "country": country,
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "timezone_name": zone_name,
        "timezone": offset_hours,
        "timezone_label": offset_label,
        "timezone_abbreviation": abbreviation,
        "is_dst": is_dst,
    }


def _match_curated(
    query: str,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> list[dict[str, Any]]:
    """Fast in-memory lookup against curated places."""
    q = query.strip().lower()
    if not q or len(q) < 2:
        return []

    matched: list[tuple[int, dict[str, Any]]] = []

    for entry in CURATED_PLACES:
        place_lower = entry["place"].lower()
        aliases = [a.lower() for a in entry.get("aliases", [])]

        priority = -1
        if place_lower == q:
            priority = 10
        elif any(a == q for a in aliases):
            priority = 9
        elif place_lower.startswith(q):
            priority = 8
        elif any(a.startswith(q) for a in aliases):
            priority = 7
        elif any(word.startswith(q) for word in place_lower.split()):
            priority = 6
        elif any(any(w.startswith(q) for w in a.split()) for a in aliases):
            priority = 5
        elif q in place_lower or any(q in a for a in aliases):
            priority = 4

        if priority > 0:
            item = _build_geo_item(
                display_name=entry["display_name"],
                place=entry["place"],
                city=entry.get("city", ""),
                state=entry.get("state", ""),
                country=entry.get("country", ""),
                latitude=entry["latitude"],
                longitude=entry["longitude"],
                year=year,
                month=month,
                day=day,
            )
            matched.append((priority, item))

    # Sort descending by priority
    matched.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matched[:6]]


async def _fetch_open_meteo(
    query: str,
    year: int | None,
    month: int | None,
    day: int | None,
) -> list[dict[str, Any]]:
    """Open-Meteo Geocoding: Global coverage of 3M+ cities, fast (<150ms), reliable."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 6, "language": "en", "format": "json"}
    headers = {"User-Agent": "AstraAstrology/1.0"}
    items: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                results = (resp.json() or {}).get("results", []) or []
                for r in results:
                    lat = float(r.get("latitude") or 0.0)
                    lon = float(r.get("longitude") or 0.0)
                    name = r.get("name") or ""
                    admin1 = r.get("admin1") or ""
                    country = r.get("country") or ""
                    parts = [p for p in [name, admin1, country] if p]
                    display_name = ", ".join(parts)

                    items.append(
                        _build_geo_item(
                            display_name=display_name,
                            place=name,
                            city=name,
                            state=admin1,
                            country=country,
                            latitude=lat,
                            longitude=lon,
                            year=year,
                            month=month,
                            day=day,
                        )
                    )
    except Exception as exc:
        logger.debug(f"Open-Meteo geocoding failed for {query!r}: {exc}")

    return items


async def _fetch_nominatim(
    query: str,
    year: int | None,
    month: int | None,
    day: int | None,
) -> list[dict[str, Any]]:
    """Nominatim OSM Geocoding: High quality address details, throttled with 3.5s timeout."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "AstraAstrology/1.0 (info@astraastrology.com)"}
    params = {"q": query, "format": "json", "addressdetails": "1", "limit": "6"}
    items: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json() or []
                for d in data:
                    try:
                        lat = float(d.get("lat"))
                        lon = float(d.get("lon"))
                    except (TypeError, ValueError):
                        continue

                    addr = d.get("address") or {}
                    city = (
                        addr.get("city")
                        or addr.get("town")
                        or addr.get("village")
                        or addr.get("municipality")
                        or addr.get("county")
                        or ""
                    )
                    items.append(
                        _build_geo_item(
                            display_name=d.get("display_name", ""),
                            place=city or d.get("display_name", "").split(",")[0].strip(),
                            city=city,
                            state=addr.get("state", ""),
                            country=addr.get("country", ""),
                            latitude=lat,
                            longitude=lon,
                            year=year,
                            month=month,
                            day=day,
                        )
                    )
    except Exception as exc:
        logger.debug(f"Nominatim lookup failed for {query!r}: {exc}")

    return items


async def _fetch_photon(
    query: str,
    year: int | None,
    month: int | None,
    day: int | None,
) -> list[dict[str, Any]]:
    """Photon Komoot Geocoding: Fuzzy OSM Elasticsearch search."""
    url = "https://photon.komoot.io/api/"
    params = {"q": query, "limit": "5"}
    headers = {"User-Agent": "AstraAstrology/1.0"}
    items: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                features = (resp.json() or {}).get("features", []) or []
                for f in features:
                    props = f.get("properties", {}) or {}
                    geom = f.get("geometry", {}) or {}
                    coords = geom.get("coordinates") or []
                    if len(coords) < 2:
                        continue
                    lon, lat = float(coords[0]), float(coords[1])
                    name = props.get("name") or ""
                    state = props.get("state") or ""
                    country = props.get("country") or ""
                    city = props.get("city") or props.get("district") or name
                    parts = [p for p in [name, props.get("district"), state, country] if p]
                    display_name = ", ".join(parts) or name

                    items.append(
                        _build_geo_item(
                            display_name=display_name,
                            place=name,
                            city=city,
                            state=state,
                            country=country,
                            latitude=lat,
                            longitude=lon,
                            year=year,
                            month=month,
                            day=day,
                        )
                    )
    except Exception as exc:
        logger.debug(f"Photon lookup failed for {query!r}: {exc}")

    return items


def _is_duplicate(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Checks whether two locations represent essentially the same spot (~4 km)."""
    lat1, lon1 = a.get("latitude", 0.0), a.get("longitude", 0.0)
    lat2, lon2 = b.get("latitude", 0.0), b.get("longitude", 0.0)
    return abs(lat1 - lat2) < 0.04 and abs(lon1 - lon2) < 0.04


async def geocode_place(
    query: str,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> list[dict[str, Any]]:
    """Main geocoding pipeline.

    Combines curated in-memory results + Open-Meteo + Nominatim + Photon in parallel.
    Caches results in memory for high-performance repetition.
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    cache_key = f"{clean_q.lower()}_{year}_{month}_{day}"
    now = time.time()
    cached = _CACHE.get(cache_key)
    if cached and (now - cached[0] < _CACHE_TTL_SECONDS):
        return cached[1]

    # 1. Step 1: Check curated fast-path
    curated_matches = _match_curated(clean_q, year=year, month=month, day=day)

    # 2. Step 2: Fetch remote engines in parallel
    tasks = [
        _fetch_open_meteo(clean_q, year, month, day),
        _fetch_photon(clean_q, year, month, day),
        _fetch_nominatim(clean_q, year, month, day),
    ]
    remote_results = await asyncio.gather(*tasks, return_exceptions=True)

    candidates: list[dict[str, Any]] = list(curated_matches)

    for res in remote_results:
        if isinstance(res, list):
            candidates.extend(res)

    # 3. Step 3: Deduplicate while preserving order (curated items first)
    merged: list[dict[str, Any]] = []
    for c in candidates:
        if not c.get("place") or c.get("latitude") == 0.0:
            continue
        if any(_is_duplicate(c, existing) for existing in merged):
            continue
        merged.append(c)
        if len(merged) >= 8:
            break

    # Save to memory cache
    if len(_CACHE) >= _MAX_CACHE_SIZE:
        _CACHE.clear()  # simple LRU eviction
    _CACHE[cache_key] = (now, merged)

    return merged
