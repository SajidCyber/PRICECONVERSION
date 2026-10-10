"""Market Positioning Intelligence, Competitive Analysis, and Arbitrage Service."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import EntityNotFoundError
from app.core.logging_config import logger
from app.models import Country, PriceObservation, Product, ProductListing
from app.schemas.intelligence import (
    ExportOpportunitiesResponse,
    ExportOpportunityDTO,
    MarketplacePositionDTO,
    PriceAnomalyDTO,
    ProductPositioningResponse,
)
from app.services.pricing.fx_service import FXService
from app.services.pricing.landed_cost import LandedCostService


class MarketPositioningService:
    """Computes competitive market positions, pricing recommendations, price anomalies, and cross-border arbitrage opportunities."""

    @classmethod
    def analyze_product_positioning(
        cls,
        db: Session,
        product_id: str,
        destination_country_id: str = "US",
        reporting_currency: Optional[str] = None,
    ) -> ProductPositioningResponse:
        """Evaluates competitive landed-cost positioning and strategic pricing recommendations."""
        product = (
            db.query(Product)
            .options(
                joinedload(Product.listings)
                .joinedload(ProductListing.marketplace),
                joinedload(Product.listings)
                .joinedload(ProductListing.observations),
            )
            .filter(Product.id == product_id)
            .first()
        )
        if not product:
            raise EntityNotFoundError("Product", product_id)

        dest_country = destination_country_id.upper()
        country_obj = db.query(Country).filter(Country.id == dest_country).first()
        dest_currency = country_obj.currency_code if country_obj else "USD"
        rep_currency = (reporting_currency or dest_currency).upper()

        # FX rate from destination currency to reporting currency if different
        fx_to_rep, _, _, _ = FXService.get_rate(db, dest_currency, rep_currency)

        # 1. Compute Our Landed Cost if target_base_price is configured
        our_landed_cost: Optional[Decimal] = None
        if product.target_base_price is not None:
            our_calc = LandedCostService.calculate_landed_cost(
                db=db,
                price=product.target_base_price,
                source_currency=product.base_currency,
                destination_country_id=dest_country,
                product_category=product.category,
            )
            # Convert to reporting currency
            our_landed_cost = Decimal(f"{(our_calc.total_landed_cost * fx_to_rep):.2f}")

        # 2. Gather latest price for each listing and compute landed cost
        listing_positions: List[MarketplacePositionDTO] = []
        landed_costs_list: List[Decimal] = []

        for listing in product.listings:
            if not listing.observations:
                continue

            latest_obs = max(listing.observations, key=lambda o: o.observed_at)
            calc = LandedCostService.calculate_landed_cost(
                db=db,
                price=latest_obs.listed_price,
                source_currency=listing.currency_code,
                destination_country_id=dest_country,
                product_category=product.category,
            )
            landed_in_rep = Decimal(f"{(calc.total_landed_cost * fx_to_rep):.2f}")
            landed_costs_list.append(landed_in_rep)

            pos_dto = MarketplacePositionDTO(
                listing_id=listing.id,
                marketplace_id=listing.marketplace_id,
                marketplace_name=listing.marketplace.name if listing.marketplace else listing.marketplace_id,
                country_id=listing.marketplace.country_id if listing.marketplace else "US",
                original_price=latest_obs.listed_price,
                original_currency=listing.currency_code,
                landed_cost=landed_in_rep,
                reporting_currency=rep_currency,
                rank=0,  # Computed after sorting
                position_tier="competitive",
                is_our_product=False,
                is_cheapest=False,
            )
            listing_positions.append(pos_dto)

        # Sort listings by landed cost ASC
        listing_positions.sort(key=lambda p: p.landed_cost)
        for idx, pos in enumerate(listing_positions, start=1):
            pos.rank = idx
            pos.is_cheapest = idx == 1

        # 3. Compute Competitor Statistics
        if landed_costs_list:
            sorted_costs = sorted(landed_costs_list)
            comp_min = sorted_costs[0]
            comp_max = sorted_costs[-1]
            n = len(sorted_costs)
            if n % 2 == 1:
                comp_median = sorted_costs[n // 2]
            else:
                comp_median = Decimal(f"{((sorted_costs[n // 2 - 1] + sorted_costs[n // 2]) / 2):.2f}")
        else:
            comp_min = None
            comp_max = None
            comp_median = None

        # 4. Compare Our Landed Cost vs Market Median
        price_gap_vs_median: Optional[Decimal] = None
        positioning_idx: Optional[Decimal] = None
        market_comp = "moderately_competitive"
        recommendation = "maintain_price"
        reasoning = "Market prices are stable."

        if our_landed_cost is not None and comp_median is not None and comp_median > 0:
            positioning_idx = Decimal(f"{(our_landed_cost / comp_median):.4f}")
            price_gap_vs_median = Decimal(f"{(((our_landed_cost - comp_median) / comp_median) * 100):.2f}")

            # Assign price gap per listing vs our product
            for pos in listing_positions:
                pos.price_gap_vs_our_product_pct = Decimal(
                    f"{(((pos.landed_cost - our_landed_cost) / our_landed_cost) * 100):.2f}"
                )
                if pos.landed_cost == comp_min:
                    pos.position_tier = "cheapest"
                elif pos.landed_cost <= comp_median * Decimal("1.05"):
                    pos.position_tier = "competitive"
                elif pos.landed_cost <= comp_median * Decimal("1.25"):
                    pos.position_tier = "premium"
                else:
                    pos.position_tier = "overpriced"

            # Strategic Recommendation Engine
            if comp_min is not None and our_landed_cost < comp_min * Decimal("0.90"):
                recommendation = "raise_price_to_maximize_margin"
                market_comp = "dominant"
                reasoning = (
                    f"Our landed cost ({rep_currency} {our_landed_cost}) is significantly below the lowest competitor "
                    f"({rep_currency} {comp_min}). Increase base price by 5-8% to capture higher gross margin while retaining lowest-price positioning."
                )
            elif our_landed_cost <= comp_median * Decimal("0.95"):
                recommendation = "maintain_price"
                market_comp = "highly_competitive"
                reasoning = (
                    f"Our landed cost is competitive ({abs(float(price_gap_vs_median)):.1f}% below market median). "
                    "Maintain current pricing strategy to preserve market share and search ranking."
                )
            elif our_landed_cost <= comp_median * Decimal("1.05"):
                recommendation = "differentiate_or_match_leader"
                market_comp = "moderately_competitive"
                reasoning = (
                    f"Our landed cost is within ±5% of the market median ({rep_currency} {comp_median}). "
                    "Consider matching the price leader or leveraging value-add services (e.g. faster fulfillment/extended returns)."
                )
            else:
                recommendation = "lower_price_to_compete"
                market_comp = "uncompetitive"
                reasoning = (
                    f"Our landed cost is {float(price_gap_vs_median):.1f}% above the market median ({rep_currency} {comp_median}). "
                    "Consider lowering base export price or negotiating logistics rates to regain competitiveness."
                )

        # 5. Check Anomalies for Product
        anomalies = cls.detect_anomalies(db, product_id=product_id)

        return ProductPositioningResponse(
            product_id=product.id,
            product_title=product.title,
            destination_country=dest_country,
            reporting_currency=rep_currency,
            our_target_landed_cost=our_landed_cost,
            competitor_median_landed_cost=comp_median,
            competitor_min_landed_cost=comp_min,
            competitor_max_landed_cost=comp_max,
            price_gap_vs_median_pct=price_gap_vs_median,
            positioning_index=positioning_idx,
            market_competitiveness=market_comp,
            strategic_recommendation=recommendation,
            recommendation_reasoning=reasoning,
            total_competitors=len(listing_positions),
            rankings=listing_positions,
            anomalies=anomalies,
        )

    @classmethod
    def detect_export_opportunities(
        cls,
        db: Session,
        min_margin_pct: Decimal = Decimal("15.0"),
        reporting_currency: str = "USD",
    ) -> ExportOpportunitiesResponse:
        """Scans catalog across all source-target pairs to find high-margin cross-border price arbitrage opportunities."""
        rep_currency = reporting_currency.upper()
        products = db.query(Product).options(
            joinedload(Product.listings)
            .joinedload(ProductListing.marketplace),
            joinedload(Product.listings)
            .joinedload(ProductListing.observations),
        ).all()

        opportunities: List[ExportOpportunityDTO] = []

        for product in products:
            valid_listings = [l for l in product.listings if l.observations]
            if len(valid_listings) < 2:
                continue

            # Compare every source listing against every target listing in different countries
            for src in valid_listings:
                src_country = src.marketplace.country_id if src.marketplace else "US"
                src_obs = max(src.observations, key=lambda o: o.observed_at)
                src_price = src_obs.listed_price

                for tgt in valid_listings:
                    if src.id == tgt.id:
                        continue
                    tgt_country = tgt.marketplace.country_id if tgt.marketplace else "US"
                    if src_country == tgt_country:
                        continue  # Only cross-border opportunities

                    tgt_obs = max(tgt.observations, key=lambda o: o.observed_at)
                    tgt_market_price = tgt_obs.listed_price

                    # Compute landed cost of exporting src into tgt's country
                    landed_calc = LandedCostService.calculate_landed_cost(
                        db=db,
                        price=src_price,
                        source_currency=src.currency_code,
                        destination_country_id=tgt_country,
                        product_category=product.category,
                    )
                    landed_in_tgt_currency = landed_calc.total_landed_cost

                    # Convert both to reporting currency for normalized profit evaluation
                    fx_tgt_to_rep, _, _, _ = FXService.get_rate(db, tgt.currency_code, rep_currency)
                    landed_in_rep = Decimal(f"{(landed_in_tgt_currency * fx_tgt_to_rep):.2f}")
                    tgt_price_in_rep = Decimal(f"{(tgt_market_price * fx_tgt_to_rep):.2f}")

                    if tgt_price_in_rep <= landed_in_rep:
                        continue

                    net_profit = Decimal(f"{(tgt_price_in_rep - landed_in_rep):.2f}")
                    margin_pct = Decimal(f"{((net_profit / tgt_price_in_rep) * 100):.2f}")

                    if margin_pct >= min_margin_pct:
                        opp_score = min(100.0, max(0.0, float(margin_pct) * 2.5))
                        feasibility = "high" if margin_pct >= Decimal("25.0") else "medium"

                        opp = ExportOpportunityDTO(
                            product_id=product.id,
                            product_title=product.title,
                            source_marketplace=src.marketplace.name if src.marketplace else src.marketplace_id,
                            source_country=src_country,
                            source_currency=src.currency_code,
                            source_price=src_price,
                            target_marketplace=tgt.marketplace.name if tgt.marketplace else tgt.marketplace_id,
                            target_country=tgt_country,
                            target_currency=tgt.currency_code,
                            target_market_price=tgt_market_price,
                            landed_cost_in_target=landed_in_rep,
                            reporting_currency=rep_currency,
                            net_profit_margin=net_profit,
                            net_margin_pct=margin_pct,
                            opportunity_score=round(opp_score, 1),
                            feasibility_rating=feasibility,
                        )
                        opportunities.append(opp)

        # Sort opportunities by net_margin_pct DESC
        opportunities.sort(key=lambda o: o.net_margin_pct, reverse=True)

        return ExportOpportunitiesResponse(
            reporting_currency=rep_currency,
            min_margin_pct_filter=min_margin_pct,
            total_opportunities_found=len(opportunities),
            opportunities=opportunities,
        )

    @classmethod
    def detect_anomalies(
        cls,
        db: Session,
        product_id: Optional[str] = None,
        threshold_pct: Decimal = Decimal("15.0"),
    ) -> List[PriceAnomalyDTO]:
        """Detects price drops or spikes exceeding threshold percentage between consecutive observations."""
        query = db.query(ProductListing).options(
            joinedload(ProductListing.product),
            joinedload(ProductListing.marketplace),
            joinedload(ProductListing.observations),
        )
        if product_id:
            query = query.filter(ProductListing.product_id == product_id)

        listings = query.all()
        anomalies: List[PriceAnomalyDTO] = []

        for listing in listings:
            if len(listing.observations) < 2:
                continue

            sorted_obs = sorted(listing.observations, key=lambda o: o.observed_at)
            for i in range(1, len(sorted_obs)):
                prev = sorted_obs[i - 1].listed_price
                curr = sorted_obs[i].listed_price
                if prev <= 0:
                    continue

                pct_diff = Decimal(f"{(((curr - prev) / prev) * 100):.2f}")
                if abs(pct_diff) >= threshold_pct:
                    anomaly_type = "price_drop" if pct_diff < 0 else "price_spike"
                    abs_diff = abs(pct_diff)
                    if abs_diff >= Decimal("30.0"):
                        severity = "critical"
                    elif abs_diff >= Decimal("20.0"):
                        severity = "high"
                    else:
                        severity = "medium"

                    dto = PriceAnomalyDTO(
                        listing_id=listing.id,
                        marketplace_id=listing.marketplace_id,
                        marketplace_name=listing.marketplace.name if listing.marketplace else listing.marketplace_id,
                        product_id=listing.product_id,
                        product_title=listing.product.title if listing.product else "Unknown Product",
                        previous_price=prev,
                        current_price=curr,
                        pct_change=pct_diff,
                        anomaly_type=anomaly_type,
                        detected_at=sorted_obs[i].observed_at,
                        severity=severity,
                    )
                    anomalies.append(dto)

        # Sort by detected_at DESC
        anomalies.sort(key=lambda a: a.detected_at, reverse=True)
        return anomalies
