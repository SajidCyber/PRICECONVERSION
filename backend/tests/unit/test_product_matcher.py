"""Unit tests for Product Matching Engine and Text Similarity utilities."""

from decimal import Decimal
import pytest
from app.models import Product, ProductListing
from app.services.matcher.engine import ProductMatchingEngine
from app.services.matcher.text_utils import (
    extract_model_numbers,
    jaccard_similarity,
    levenshtein_ratio,
    normalize_title,
    tokenize,
)


def test_text_normalization_and_tokenization():
    """Verify title normalization strips punctuation and stop words."""
    raw = "Apple MacBook Pro 14-inch (M3 Chip, 512GB SSD, Space Gray) - New Edition!"
    clean = normalize_title(raw)
    assert "apple macbook pro 14 inch m3 chip 512gb ssd space gray new edition" in clean

    tokens = tokenize(raw)
    assert "apple" in tokens
    assert "macbook" in tokens
    assert "m3" in tokens
    assert "512gb" in tokens
    # Stopwords should be removed
    assert "the" not in tokens
    assert "in" not in tokens
    assert "new" not in tokens


def test_model_number_extraction():
    """Verify extraction of alphanumeric model numbers and chipset codes."""
    text1 = "Apple 2023 MacBook Pro Laptop M3 chip 512GB SSD"
    models1 = extract_model_numbers(text1)
    assert "M3" in models1
    assert "512GB" in models1

    text2 = "Sony WH-1000XM5 Wireless Noise Canceling Headphones"
    models2 = extract_model_numbers(text2)
    assert "WH1000XM5" in models2 or "1000XM5" in models2 or any("1000XM5" in m for m in models2)


def test_levenshtein_and_jaccard_similarity():
    """Verify fuzzy Levenshtein ratio and Jaccard token overlap metrics."""
    s1 = "sony wh 1000xm5 noise canceling headphones"
    s2 = "sony wh 1000xm5 noise cancelling wireless headphones"

    lev = levenshtein_ratio(s1, s2)
    assert lev > 0.80

    tok1 = tokenize(s1)
    tok2 = tokenize(s2)
    jaccard = jaccard_similarity(tok1, tok2)
    assert jaccard > 0.60


def test_exact_sku_match():
    """Verify exact SKU match produces 100% confidence score and confirmed status."""
    prod = Product(
        sku="TECH-APL-MBP14",
        title="Apple MacBook Pro 14 M3",
        brand="Apple",
        category="Electronics",
    )
    listing = ProductListing(
        marketplace_id="amazon_us",
        external_id="TECH-APL-MBP14",
        listing_title="Apple MacBook Pro 14 M3 512GB Space Gray",
        currency_code="USD",
    )

    conf, m_type, evidence, status = ProductMatchingEngine.compute_similarity(prod, listing)
    assert conf == Decimal("100.00")
    assert m_type == "exact_sku"
    assert status == "confirmed"
    assert evidence["exact_sku_match"] is True


def test_cross_marketplace_fuzzy_matching():
    """Verify multi-factor fuzzy matching on realistic cross-border titles."""
    prod = Product(
        sku="AUDIO-SNY-WH1000",
        title="Sony WH-1000XM5 Wireless Noise Canceling Headphones",
        brand="Sony",
        category="Electronics",
    )
    listing_uk = ProductListing(
        marketplace_id="amazon_uk",
        external_id="B09XS7JWHH",
        listing_title="Sony WH-1000XM5 Noise Cancelling Over-Ear Headphones, Black",
        currency_code="GBP",
        seller_name="Sony UK",
    )

    conf, m_type, evidence, status = ProductMatchingEngine.compute_similarity(prod, listing_uk)
    assert conf >= Decimal("80.00")
    assert status in {"confirmed", "probable"}
    assert evidence["brand_match"] is True


def test_brand_conflict_rejection():
    """Verify contradictory brands (Apple vs Samsung) are strictly rejected."""
    prod = Product(
        sku="TECH-APL-01",
        title="Apple iPhone 15 Pro Max 256GB Titanium",
        brand="Apple",
        category="Smartphones",
    )
    listing_samsung = ProductListing(
        marketplace_id="amazon_us",
        external_id="SAM-S24U-01",
        listing_title="Samsung Galaxy S24 Ultra 256GB Titanium Gray",
        currency_code="USD",
        seller_name="Samsung Store",
    )

    conf, m_type, evidence, status = ProductMatchingEngine.compute_similarity(prod, listing_samsung)
    assert status == "rejected"
    assert conf <= Decimal("20.00")
    assert m_type == "brand_conflict"
