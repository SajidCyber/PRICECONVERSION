"""Product Matching Engine with Multi-Factor Similarity and Confidence Scoring."""

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.logging_config import logger
from app.models import Product, ProductListing, ProductMatch
from app.schemas.matching import BatchMatchResponse
from app.services.matcher.text_utils import (
    extract_model_numbers,
    jaccard_similarity,
    levenshtein_ratio,
    normalize_title,
    tokenize,
)


class ProductMatchingEngine:
    """Computes cross-marketplace product similarity and creates match records."""

    CONFIRMED_THRESHOLD = Decimal("85.00")
    PROBABLE_THRESHOLD = Decimal("65.00")
    MIN_MATCH_THRESHOLD = Decimal("50.00")

    @classmethod
    def compute_similarity(
        cls,
        product: Product,
        listing: ProductListing,
    ) -> Tuple[Decimal, str, Dict[str, Any], str]:
        """Calculates multi-factor similarity between a canonical product and listing.

        Returns:
            (confidence_score, match_type, evidence_dict, status_tier)
        """
        norm_p = normalize_title(product.title)
        norm_l = normalize_title(listing.listing_title)

        # 1. Exact SKU / External ID match
        if product.sku and (product.sku.lower() in norm_l or product.sku.lower() == listing.external_id.lower()):
            evidence = {
                "brand_match": True,
                "exact_sku_match": True,
                "model_number_overlap": [product.sku],
                "token_jaccard_score": 1.0,
                "levenshtein_similarity": 1.0,
                "matched_tokens": list(tokenize(product.title)),
            }
            return Decimal("100.00"), "exact_sku", evidence, "confirmed"

        # 2. Brand Alignment Check
        brand_p = (product.brand or "").strip().lower()
        brand_match = False
        brand_conflict = False

        if brand_p and brand_p in norm_l:
            brand_match = True
        elif brand_p and listing.seller_name and brand_p in listing.seller_name.lower():
            brand_match = True

        # Check known major brand contradictions
        known_brands = {"apple", "sony", "samsung", "logitech", "bose", "dyson", "dell", "lenovo", "asus", "hp"}
        present_in_prod = {b for b in known_brands if b in norm_p or (product.brand and b in product.brand.lower())}
        present_in_listing = {b for b in known_brands if b in norm_l or (listing.seller_name and b in listing.seller_name.lower())}

        if present_in_prod and present_in_listing and not present_in_prod.intersection(present_in_listing):
            brand_conflict = True

        if brand_conflict:
            # Major brand mismatch -> automatic rejection
            evidence = {
                "brand_match": False,
                "exact_sku_match": False,
                "model_number_overlap": [],
                "token_jaccard_score": 0.0,
                "levenshtein_similarity": 0.0,
                "matched_tokens": [],
                "rejection_reason": f"Conflicting brands: {present_in_prod} vs {present_in_listing}",
            }
            return Decimal("10.00"), "brand_conflict", evidence, "rejected"

        # 3. Model Number Overlap
        models_p = extract_model_numbers(product.title)
        models_l = extract_model_numbers(listing.listing_title)
        model_overlap = list(models_p.intersection(models_l))

        # 4. Token Jaccard Similarity
        tokens_p = tokenize(product.title)
        tokens_l = tokenize(listing.listing_title)
        jaccard = jaccard_similarity(tokens_p, tokens_l)
        matched_tokens = list(tokens_p.intersection(tokens_l))

        # 5. Fuzzy Levenshtein Distance
        lev = levenshtein_ratio(norm_p, norm_l)

        # 6. Weighted Confidence Score Computation
        # Base weights: Jaccard (40%), Levenshtein (30%), Brand (15%), Model Overlap (15%)
        brand_score = 1.0 if brand_match else (0.5 if not brand_p else 0.0)
        model_score = 1.0 if model_overlap else 0.0

        raw_score = (
            (jaccard * 0.40) +
            (lev * 0.30) +
            (brand_score * 0.15) +
            (model_score * 0.15)
        ) * 100

        # Model overlap strong booster if title similarity is also moderate
        if model_overlap and raw_score >= 50.0:
            raw_score = min(100.0, raw_score + 15.0)

        confidence = Decimal(f"{raw_score:.2f}")

        # Determine Tier & Type
        if confidence >= cls.CONFIRMED_THRESHOLD:
            status = "confirmed"
            match_type = "model_number" if model_overlap else "token_cosine"
        elif confidence >= cls.PROBABLE_THRESHOLD:
            status = "probable"
            match_type = "fuzzy_levenshtein"
        elif confidence >= cls.MIN_MATCH_THRESHOLD:
            status = "uncertain"
            match_type = "token_overlap"
        else:
            status = "rejected"
            match_type = "low_similarity"

        evidence = {
            "brand_match": brand_match,
            "exact_sku_match": False,
            "model_number_overlap": model_overlap,
            "token_jaccard_score": round(jaccard, 4),
            "levenshtein_similarity": round(lev, 4),
            "matched_tokens": matched_tokens,
        }

        return confidence, match_type, evidence, status

    @classmethod
    def match_listing(cls, db: Session, listing: ProductListing) -> Optional[ProductMatch]:
        """Evaluates a listing against all canonical products and records the highest match."""
        canonical_products = db.query(Product).all()
        best_match: Optional[Tuple[Product, Decimal, str, Dict[str, Any], str]] = None

        for prod in canonical_products:
            conf, m_type, evidence, status = cls.compute_similarity(prod, listing)
            if status != "rejected":
                if best_match is None or conf > best_match[1]:
                    best_match = (prod, conf, m_type, evidence, status)

        if not best_match:
            return None

        matched_prod, confidence, m_type, evidence, status = best_match

        # Locate or create ProductMatch record
        match_record = (
            db.query(ProductMatch)
            .filter(
                ProductMatch.product_id == matched_prod.id,
                ProductMatch.listing_id == listing.id,
            )
            .first()
        )

        if not match_record:
            match_record = ProductMatch(
                product_id=matched_prod.id,
                listing_id=listing.id,
                confidence_score=confidence,
                match_type=m_type,
                match_evidence=evidence,
                status=status,
            )
            db.add(match_record)
        else:
            match_record.confidence_score = confidence
            match_record.match_type = m_type
            match_record.match_evidence = evidence
            match_record.status = status

        # Link listing to canonical product if confirmed or probable
        if status in {"confirmed", "probable"} and not listing.product_id:
            listing.product_id = matched_prod.id

        db.commit()
        db.refresh(match_record)
        return match_record

    @classmethod
    def run_batch_matching(cls, db: Session) -> BatchMatchResponse:
        """Runs the matching engine across all active product listings."""
        start_time = time.perf_counter()
        listings = db.query(ProductListing).all()

        confirmed = 0
        probable = 0
        uncertain = 0
        new_matches = 0

        for listing in listings:
            match = cls.match_listing(db, listing)
            if match:
                new_matches += 1
                if match.status == "confirmed":
                    confirmed += 1
                elif match.status == "probable":
                    probable += 1
                elif match.status == "uncertain":
                    uncertain += 1

        exec_time = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Batch matching finished in %.2f ms. Inspected %d, Matches: %d (Confirmed: %d, Probable: %d, Uncertain: %d)",
            exec_time,
            len(listings),
            new_matches,
            confirmed,
            probable,
            uncertain,
        )

        return BatchMatchResponse(
            total_listings_inspected=len(listings),
            new_matches_found=new_matches,
            confirmed_count=confirmed,
            probable_count=probable,
            uncertain_count=uncertain,
            execution_time_ms=round(exec_time, 2),
        )
