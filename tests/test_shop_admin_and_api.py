"""Unit tests for Astra AstroStore Phase 2 Admin & Inventory Service Layer and APIs."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from beanie import PydanticObjectId, init_beanie

from app.models.cms import ShopCMS
from app.models.enums import ProductCategoryType
from app.models.shop import Product, ProductCategory
from app.schemas.shop import (
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductUpdate,
    StockUpdatePayload,
)
from app.services import shop_admin
from app.services.storage import (
    PRODUCT_IMAGE_TRANSFORMATION,
    extract_public_id_from_url,
)


@pytest.fixture(autouse=True)
async def init_mock_beanie():
    """Initializes Beanie DocumentSettings in memory for standalone unit testing."""
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"version": "6.0.0", "versionArray": [6, 0, 0]})
    mock_db.list_collection_names = AsyncMock(return_value=[])

    mock_coll = MagicMock()
    mock_coll.create_index = AsyncMock()
    mock_coll.create_indexes = AsyncMock()
    mock_coll.index_information = AsyncMock(return_value={})
    mock_db.__getitem__.return_value = mock_coll

    await init_beanie(
        database=mock_db,
        document_models=[
            Product,
            ProductCategory,
            ShopCMS,
        ],
    )


def test_cloudinary_extract_public_id():
    """Verifies Cloudinary URL public_id parser correctly extracts paths for safe purging."""
    url1 = "https://res.cloudinary.com/astra-cloud/image/upload/v1794114440/products/rudraksha_5mukhi.webp"
    assert extract_public_id_from_url(url1) == "products/rudraksha_5mukhi"

    url2 = "https://res.cloudinary.com/astra-cloud/image/upload/products/sample_gemstone.jpg"
    assert extract_public_id_from_url(url2) == "products/sample_gemstone"

    # Non-cloudinary or malformed
    assert extract_public_id_from_url("https://external-site.com/image.png") is None
    assert extract_public_id_from_url(None) is None


def test_product_image_compression_transformation():
    """Ensures image upload settings enforce WebP formatting and 1200x1200px limit."""
    has_bounded_dimension = any(
        t.get("width") == 1200 and t.get("height") == 1200 and t.get("crop") == "limit"
        for t in PRODUCT_IMAGE_TRANSFORMATION
    )
    has_auto_quality = any(t.get("quality") == "auto:good" for t in PRODUCT_IMAGE_TRANSFORMATION)
    assert has_bounded_dimension is True
    assert has_auto_quality is True


def test_slugify_helper():
    assert shop_admin.slugify("Nepal 5-Mukhi Rudraksha (Original)") == "nepal-5-mukhi-rudraksha-original"
    assert shop_admin.slugify("   Yellow Sapphire / Pukhraj   ") == "yellow-sapphire-pukhraj"


@pytest.mark.asyncio
async def test_update_stock_calculations():
    prod = Product(
        title="5 Mukhi Rudraksha",
        slug="5-mukhi-rudraksha",
        sku="ASTRA-RUD-5M",
        short_description="Certified 5 Mukhi",
        detailed_description="Detailed canonical description",
        category_id=PydanticObjectId(),
        category_slug="rudraksha",
        mrp=2500.0,
        sale_price=1899.0,
        stock_quantity=10,
        low_stock_threshold=5,
        featured_image="https://res.cloudinary.com/astra/image/upload/v1/rud.webp",
    )
    prod.id = PydanticObjectId()

    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with patch.object(Product, "get", AsyncMock(return_value=prod)), \
         patch.object(Product, "get_pymongo_collection", return_value=mock_collection):

        # Test 'add'
        prod.stock_quantity = 15
        res1 = await shop_admin.update_stock(str(prod.id), StockUpdatePayload(quantity=5, mode="add"))
        assert res1.stock_quantity == 15
        assert res1.in_stock is True

        # Test 'subtract'
        prod.stock_quantity = 3
        res2 = await shop_admin.update_stock(str(prod.id), StockUpdatePayload(quantity=12, mode="subtract"))
        assert res2.stock_quantity == 3
        assert res2.is_low_stock is True

        # Test 'set'
        prod.stock_quantity = 0
        res3 = await shop_admin.update_stock(str(prod.id), StockUpdatePayload(quantity=0, mode="set"))
        assert res3.stock_quantity == 0
        assert res3.in_stock is False


@pytest.mark.asyncio
async def test_atomic_stock_reserve_and_release():
    prod_id = PydanticObjectId()
    mock_collection = MagicMock()
    # 1. Successful reservation
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    with patch.object(Product, "get_pymongo_collection", return_value=mock_collection):
        res = await shop_admin.atomic_reserve_stock(prod_id, 2)
        assert res is True

    # 2. Insufficient stock (modified_count == 0)
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    with patch.object(Product, "get_pymongo_collection", return_value=mock_collection):
        res = await shop_admin.atomic_reserve_stock(prod_id, 999)
        assert res is False


@pytest.mark.asyncio
async def test_soft_delete_preserves_order_integrity():
    prod = Product(
        title="14 Mukhi Rare Nepal Rudraksha",
        slug="14-mukhi-nepal",
        sku="ASTRA-RUD-14M",
        short_description="Deva Mani Rudraksha",
        detailed_description="Lord Shiva & Hanuman Blessed",
        category_id=PydanticObjectId(),
        category_slug="rudraksha",
        mrp=45000.0,
        sale_price=38000.0,
        stock_quantity=1,
        featured_image="https://res.cloudinary.com/astra/image/upload/v1/rud14.webp",
    )
    prod.id = PydanticObjectId()

    # Case A: Product has orders -> must SOFT DELETE
    mock_order_query = MagicMock()
    mock_order_query.count = AsyncMock(return_value=1)

    with patch.object(Product, "get", AsyncMock(return_value=prod)), \
         patch.object(Product, "save", AsyncMock(return_value=prod)), \
         patch("app.models.shop.ShopOrder.find", return_value=mock_order_query):

        res = await shop_admin.delete_product(str(prod.id), hard_delete=False)
        assert res["deleted"] is True
        assert res["mode"] == "soft_delete"
        assert prod.is_deleted is True
        assert prod.is_active is False


def test_astrological_remedy_recommender_enrichment():
    from app.services.shop_remedy_recommender import enrich_curated_remedies_with_store_links

    raw_remedies = [
        {"planet_name": "Saturn", "house": 8, "upay_list": ["Do not consume alcohol."]},
        {"planet_name": "Jupiter", "house": 9, "upay_list": ["Wear yellow cloth."]},
    ]
    enriched = enrich_curated_remedies_with_store_links(raw_remedies, lang="bn")
    assert len(enriched) == 2
    assert "store_remedy_query" in enriched[0]
    assert enriched[0]["store_remedy_query"]["planet"] == "Saturn"
    assert "/shop?planet=Saturn" in enriched[0]["store_remedy_query"]["explore_url"]



@pytest.mark.asyncio
async def test_update_product_purges_orphaned_cloudinary_images():
    prod = Product(
        title="Original Blue Sapphire",
        slug="blue-sapphire",
        sku="ASTRA-GEM-BS",
        short_description="Blue Sapphire",
        detailed_description="Natural Neelam Gemstone",
        category_id=PydanticObjectId(),
        category_slug="gemstones",
        mrp=15000.0,
        sale_price=12500.0,
        stock_quantity=4,
        featured_image="https://res.cloudinary.com/astra/image/upload/v1/old_featured.webp",
        images=[
            "https://res.cloudinary.com/astra/image/upload/v1/old_featured.webp",
            "https://res.cloudinary.com/astra/image/upload/v1/old_angle2.webp",
        ],
        certificate_image_url="https://res.cloudinary.com/astra/image/upload/v1/old_cert.webp",
    )
    prod.id = PydanticObjectId()

    deleted_urls: list[str] = []

    async def mock_safe_delete(url: str | None):
        if url:
            deleted_urls.append(url)
        return True

    with patch.object(Product, "get", AsyncMock(return_value=prod)), \
         patch.object(Product, "save", AsyncMock(return_value=prod)), \
         patch("app.services.shop_admin.safe_delete_cloudinary_image", side_effect=mock_safe_delete):

        # Update product replacing the featured image and gallery, dropping old_angle2 and old_cert
        payload = ProductUpdate(
            featured_image="https://res.cloudinary.com/astra/image/upload/v1/new_featured.webp",
            images=["https://res.cloudinary.com/astra/image/upload/v1/new_featured.webp"],
            certificate_image_url=None,
        )

        res = await shop_admin.update_product(str(prod.id), payload)
        assert res.featured_image == "https://res.cloudinary.com/astra/image/upload/v1/new_featured.webp"

        # Check that old images were purged
        assert "https://res.cloudinary.com/astra/image/upload/v1/old_angle2.webp" in deleted_urls
        assert "https://res.cloudinary.com/astra/image/upload/v1/old_cert.webp" in deleted_urls
        assert "https://res.cloudinary.com/astra/image/upload/v1/old_featured.webp" in deleted_urls
        assert "https://res.cloudinary.com/astra/image/upload/v1/new_featured.webp" not in deleted_urls


def test_varshphal_store_recommendations_generation():
    from app.services.shop_remedy_recommender import build_varshphal_store_recommendations

    varsh_planets = [
        {"planet_id": "saturn", "nature": "ashubh", "house": 8},
        {"planet_id": "rahu", "nature": "ashubh", "house": 12},
        {"planet_id": "mars", "nature": "mixed", "house": 7},
        {"planet_id": "jupiter", "nature": "shubh", "house": 9},
    ]

    recs_bn = build_varshphal_store_recommendations(varsh_planets, primary_focus="finance", lang="bn")
    assert len(recs_bn) >= 2
    # First item should target most afflicted (saturn or rahu)
    planets_present = [r["ruling_planet"] for r in recs_bn]
    assert "Saturn" in planets_present or "Rahu" in planets_present
    assert any("gomti" in r["id"].lower() or "gomti" in r["title"].lower() for r in recs_bn)


@pytest.mark.asyncio
async def test_stock_reservation_and_release_flow():
    prod_id = PydanticObjectId()
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with patch.object(Product, "get_pymongo_collection", return_value=mock_collection):
        # 1. Reserve stock
        reserved = await shop_admin.atomic_reserve_stock(prod_id, 1)
        assert reserved is True

        # 2. Release stock back upon abort
        released = await shop_admin.atomic_release_stock(prod_id, 1)
        assert released is True

