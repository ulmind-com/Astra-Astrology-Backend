"""Tests for Purohit Onboarding, Catalog Management, and Puja Booking."""

import pytest
from app.models.enums import PujaBookingStatus, UserRole
from app.models.purohit import Purohit, PurohitPujaItem
from app.schemas.purohit import (
    PurohitCreate,
    PurohitPujaItemCreate,
    PurohitPujaItemUpdate,
)
from app.services import purohit_service


def test_generate_initial_password():
    pwd = purohit_service.generate_initial_password(12)
    assert len(pwd) == 12
    assert any(c.isdigit() for c in pwd) or any(c.isalpha() for c in pwd)


def test_purohit_starting_price():
    p = Purohit.model_construct(
        display_name="Acharya Sharma",
        slug="acharya-sharma",
        phone="9876543210",
        email="sharma@example.com",
        pujas=[
            PurohitPujaItem(puja_name="Lakshmi Puja", description="", price_inr=150.0, is_active=True),
            PurohitPujaItem(puja_name="Satyanarayan", description="", price_inr=500.0, is_active=True),
            PurohitPujaItem(puja_name="Inactive Puja", description="", price_inr=50.0, is_active=False),
        ],
    )
    # Starts at 150 because 50 is inactive
    price = purohit_service._get_starting_price(p)
    assert price == 150.0


def test_purohit_default_starting_price_when_empty():
    p = Purohit.model_construct(
        display_name="Acharya Sharma",
        slug="acharya-sharma",
        phone="9876543210",
        email="sharma@example.com",
        pujas=[],
    )
    price = purohit_service._get_starting_price(p)
    assert price == 0.0
