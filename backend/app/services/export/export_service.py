"""Structured Report and Dataset Export Service (CSV / JSON formatters)."""

import csv
import io
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundError
from app.models import Product
from app.services.analytics.history_service import PriceHistoryService
from app.services.analytics.positioning import MarketPositioningService
from app.services.pricing.landed_cost import LandedCostService


class ExportService:
    """Generates structured CSV files for cross-border pricing, history series, and arbitrage opportunities."""

    @classmethod
    def export_comparison_matrix_csv(
        cls,
        db: Session,
        destination_country: str = "US",
        reporting_currency: str = "USD",
    ) -> str:
        """Exports full cross-border landed cost comparison matrix across all products as a CSV string."""
        products = db.query(Product).all()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Product SKU",
            "Product Title",
            "Marketplace ID",
            "Marketplace Name",
            "Country",
            "Original Price",
            "Original Currency",
            "FX Rate",
            "Converted Price",
            "CIF Value",
            "Customs Duty",
            "Import Tax",
            "Handling Fee",
            "Total Landed Cost",
            "Reporting Currency",
            "Is Cheapest",
            "Observed At",
        ])

        for prod in products:
            try:
                matrix = LandedCostService.get_product_comparison_matrix(
                    db=db,
                    product_id=prod.id,
                    destination_country_id=destination_country,
                    reporting_currency=reporting_currency,
                )
                for item in matrix.listings:
                    b = item.breakdown
                    writer.writerow([
                        prod.sku or "",
                        prod.title,
                        item.marketplace_id,
                        item.marketplace_name,
                        item.country_id,
                        float(item.original_price),
                        item.original_currency,
                        float(b.fx_rate),
                        float(b.converted_price),
                        float(b.cif_value),
                        float(b.customs_duty_amount),
                        float(b.import_tax_amount),
                        float(b.handling_fee),
                        float(b.total_landed_cost),
                        reporting_currency.upper(),
                        "YES" if item.is_cheapest_landed else "NO",
                        item.last_observed_at.isoformat() if item.last_observed_at else "",
                    ])
            except Exception:
                continue

        return output.getvalue()

    @classmethod
    def export_product_history_csv(
        cls,
        db: Session,
        product_id: str,
        reporting_currency: str = "USD",
        days: int = 30,
    ) -> str:
        """Exports historical price observations and currency conversions for a product as a CSV string."""
        history = PriceHistoryService.get_product_history(
            db=db,
            product_id=product_id,
            reporting_currency=reporting_currency,
            days=days,
        )

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Product SKU",
            "Product Title",
            "Marketplace ID",
            "Marketplace Name",
            "Country",
            "Observation ID",
            "Observed At",
            "Listed Price",
            "Currency",
            "Converted Price",
            "Reporting Currency",
            "Shipping Price",
            "Availability",
            "Discount Pct",
            "Data Provenance",
        ])

        for listing in history.listings_history:
            for pt in listing.price_points:
                writer.writerow([
                    history.product_sku or "",
                    history.product_title,
                    listing.marketplace_id,
                    listing.marketplace_name,
                    listing.country_id,
                    pt.observation_id,
                    pt.observed_at.isoformat(),
                    float(pt.listed_price),
                    pt.currency_code,
                    float(pt.converted_price),
                    pt.reporting_currency,
                    float(pt.shipping_price),
                    pt.availability_status,
                    float(pt.discount_pct),
                    pt.data_provenance,
                ])

        return output.getvalue()

    @classmethod
    def export_opportunities_csv(
        cls,
        db: Session,
        min_margin_pct: Decimal = Decimal("15.0"),
        reporting_currency: str = "USD",
    ) -> str:
        """Exports detected cross-border export arbitrage opportunities as a CSV string."""
        opps = MarketPositioningService.detect_export_opportunities(
            db=db,
            min_margin_pct=min_margin_pct,
            reporting_currency=reporting_currency,
        )

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Product ID",
            "Product Title",
            "Source Marketplace",
            "Source Country",
            "Source Price",
            "Source Currency",
            "Target Marketplace",
            "Target Country",
            "Target Market Price",
            "Target Currency",
            "Landed Cost in Target",
            "Reporting Currency",
            "Net Profit Margin",
            "Net Margin Pct",
            "Opportunity Score",
            "Feasibility",
        ])

        for opp in opps.opportunities:
            writer.writerow([
                opp.product_id,
                opp.product_title,
                opp.source_marketplace,
                opp.source_country,
                float(opp.source_price),
                opp.source_currency,
                opp.target_marketplace,
                opp.target_country,
                float(opp.target_market_price),
                opp.target_currency,
                float(opp.landed_cost_in_target),
                opp.reporting_currency,
                float(opp.net_profit_margin),
                float(opp.net_margin_pct),
                opp.opportunity_score,
                opp.feasibility_rating.upper(),
            ])

        return output.getvalue()
