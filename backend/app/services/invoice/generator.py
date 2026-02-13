"""Invoice generation service."""

import logging
from datetime import date
from typing import Optional

from app import db
from app.models.invoice import Invoice, InvoiceItem
from app.services.invoice.gst_utils import GSTValidator

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """Create and manage GST-compliant invoices."""

    def create_invoice(
        self,
        org_id: str,
        user_id: str,
        invoice_type: str,
        invoice_data: dict,
        items_data: list[dict],
    ) -> Invoice:
        """
        Create a new invoice with line items and tax calculations.

        Args:
            org_id: Organization ID
            user_id: Creating user ID
            invoice_type: tax_invoice, bill_of_supply, export, debit_note, credit_note, quotation
            invoice_data: Invoice header fields
            items_data: List of line item dicts
        """
        from app.models.user import Organization

        org = Organization.query.get(org_id)
        if not org:
            raise ValueError("Organization not found")

        # Generate invoice number
        invoice_number = self._generate_invoice_number(org, invoice_type)

        # Determine interstate status
        is_interstate = False
        if invoice_data.get("supplier_gstin") and invoice_data.get("customer_gstin"):
            is_interstate = GSTValidator.is_interstate(
                invoice_data["supplier_gstin"], invoice_data["customer_gstin"]
            )

        invoice = Invoice(
            org_id=org_id,
            created_by=user_id,
            invoice_number=invoice_number,
            invoice_type=invoice_type,
            invoice_date=invoice_data.get("invoice_date", date.today()),
            due_date=invoice_data.get("due_date"),
            supplier_name=invoice_data.get("supplier_name", org.name),
            supplier_gstin=invoice_data.get("supplier_gstin", org.gstin),
            supplier_address=invoice_data.get("supplier_address", self._format_org_address(org)),
            supplier_state=invoice_data.get("supplier_state", org.state),
            customer_name=invoice_data["customer_name"],
            customer_gstin=invoice_data.get("customer_gstin"),
            customer_address=invoice_data.get("customer_address"),
            customer_state=invoice_data.get("customer_state"),
            customer_email=invoice_data.get("customer_email"),
            customer_phone=invoice_data.get("customer_phone"),
            place_of_supply=invoice_data.get("place_of_supply", invoice_data.get("customer_state", "")),
            is_interstate=is_interstate,
            currency=invoice_data.get("currency", "INR"),
            exchange_rate=invoice_data.get("exchange_rate", 1.0),
            lut_number=invoice_data.get("lut_number"),
            shipping_bill_no=invoice_data.get("shipping_bill_no"),
            port_of_export=invoice_data.get("port_of_export"),
            country_of_destination=invoice_data.get("country_of_destination"),
            original_invoice_id=invoice_data.get("original_invoice_id"),
            reason=invoice_data.get("reason"),
            template_id=invoice_data.get("template_id", "professional_services"),
            notes=invoice_data.get("notes"),
            terms_conditions=invoice_data.get("terms_conditions"),
            status="draft",
        )

        # Create line items
        for idx, item_data in enumerate(items_data, 1):
            item = InvoiceItem(
                sr_no=idx,
                description=item_data["description"],
                hsn_sac=item_data.get("hsn_sac"),
                unit=item_data.get("unit", "NOS"),
                quantity=item_data.get("quantity", 1),
                rate=item_data["rate"],
                amount=0,
                discount_percent=item_data.get("discount_percent", 0),
                gst_rate=item_data.get("gst_rate", 18),
                cess_rate=item_data.get("cess_rate", 0),
            )
            item.calculate(is_interstate)
            invoice.items.append(item)

        # Calculate totals
        invoice.calculate_totals()
        invoice.amount_in_words = self._amount_to_words(invoice.total_amount, invoice.currency)

        # Validate
        errors = GSTValidator.validate_invoice(invoice)
        if errors:
            raise ValueError(f"Invoice validation failed: {'; '.join(errors)}")

        db.session.add(invoice)

        # Update org invoice counter
        org.invoice_next_number += 1
        db.session.commit()

        return invoice

    def _generate_invoice_number(self, org, invoice_type: str) -> str:
        """Generate sequential invoice number."""
        prefix_map = {
            "tax_invoice": org.invoice_prefix or "INV",
            "bill_of_supply": "BOS",
            "export": "EXP",
            "debit_note": "DN",
            "credit_note": "CN",
            "quotation": "QT",
        }
        prefix = prefix_map.get(invoice_type, "INV")
        number = org.invoice_next_number or 1
        fy = self._get_financial_year()
        return f"{prefix}/{fy}/{number:05d}"

    @staticmethod
    def _get_financial_year() -> str:
        """Get current financial year string."""
        today = date.today()
        if today.month >= 4:
            return f"{today.year}-{(today.year + 1) % 100:02d}"
        return f"{today.year - 1}-{today.year % 100:02d}"

    @staticmethod
    def _format_org_address(org) -> str:
        """Format organization address."""
        parts = [org.address_line1, org.address_line2, org.city, org.state, org.pincode]
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _amount_to_words(amount: float, currency: str = "INR") -> str:
        """Convert amount to words (Indian numbering system)."""
        if amount == 0:
            return "Zero"

        ones = [
            "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen",
        ]
        tens = [
            "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
            "Eighty", "Ninety",
        ]

        def _two_digits(n):
            if n < 20:
                return ones[n]
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")

        def _three_digits(n):
            if n >= 100:
                return ones[n // 100] + " Hundred" + (" and " + _two_digits(n % 100) if n % 100 else "")
            return _two_digits(n)

        rupees = int(amount)
        paise = round((amount - rupees) * 100)

        if rupees == 0:
            result = ""
        else:
            crores = rupees // 10000000
            remainder = rupees % 10000000
            lakhs = remainder // 100000
            remainder = remainder % 100000
            thousands = remainder // 1000
            remainder = remainder % 1000

            parts = []
            if crores:
                parts.append(_three_digits(crores) + " Crore")
            if lakhs:
                parts.append(_two_digits(lakhs) + " Lakh")
            if thousands:
                parts.append(_two_digits(thousands) + " Thousand")
            if remainder:
                parts.append(_three_digits(remainder))

            result = " ".join(parts)

        currency_name = "Rupees" if currency == "INR" else currency
        paise_name = "Paise" if currency == "INR" else "Cents"

        if paise:
            return f"{currency_name} {result} and {_two_digits(paise)} {paise_name} Only"
        return f"{currency_name} {result} Only"
