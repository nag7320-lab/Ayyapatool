"""Invoice PDF generation using ReportLab."""

import io
import logging
from datetime import date

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class InvoicePDFGenerator:
    """Generate professional PDF invoices."""

    BRAND_COLOR = colors.HexColor("#1E3A8A")
    ACCENT_COLOR = colors.HexColor("#10B981")
    LIGHT_BG = colors.HexColor("#F9FAFB")

    def generate(self, invoice, bank_detail=None) -> bytes:
        """Generate a PDF invoice and return bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=self.BRAND_COLOR,
            alignment=1,
        )
        type_labels = {
            "tax_invoice": "TAX INVOICE",
            "bill_of_supply": "BILL OF SUPPLY",
            "export": "EXPORT INVOICE",
            "debit_note": "DEBIT NOTE",
            "credit_note": "CREDIT NOTE",
            "quotation": "QUOTATION",
        }
        elements.append(Paragraph(type_labels.get(invoice.invoice_type, "INVOICE"), title_style))
        elements.append(Spacer(1, 5 * mm))

        # Invoice info table
        info_data = [
            ["Invoice No:", invoice.invoice_number, "Date:", str(invoice.invoice_date)],
            ["Place of Supply:", invoice.place_of_supply or "", "Due Date:", str(invoice.due_date or "")],
        ]
        info_table = Table(info_data, colWidths=[80, 150, 80, 150])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 5 * mm))

        # Supplier / Customer
        party_data = [
            [
                Paragraph("<b>Supplier Details</b>", styles["Normal"]),
                Paragraph("<b>Customer Details</b>", styles["Normal"]),
            ],
            [
                Paragraph(
                    f"{invoice.supplier_name}<br/>"
                    f"GSTIN: {invoice.supplier_gstin or 'N/A'}<br/>"
                    f"{invoice.supplier_address or ''}<br/>"
                    f"State: {invoice.supplier_state or ''}",
                    styles["Normal"],
                ),
                Paragraph(
                    f"{invoice.customer_name}<br/>"
                    f"GSTIN: {invoice.customer_gstin or 'N/A'}<br/>"
                    f"{invoice.customer_address or ''}<br/>"
                    f"State: {invoice.customer_state or ''}",
                    styles["Normal"],
                ),
            ],
        ]
        party_table = Table(party_data, colWidths=[240, 240])
        party_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), self.LIGHT_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(party_table)
        elements.append(Spacer(1, 5 * mm))

        # Items table
        if invoice.is_interstate:
            header = ["#", "Description", "HSN/SAC", "Qty", "Rate", "Amount", "IGST", "Total"]
            col_widths = [20, 130, 50, 35, 55, 60, 55, 60]
        else:
            header = ["#", "Description", "HSN/SAC", "Qty", "Rate", "Amount", "CGST", "SGST", "Total"]
            col_widths = [20, 110, 50, 30, 50, 55, 50, 50, 55]

        items_data = [header]
        for item in invoice.items:
            if invoice.is_interstate:
                row = [
                    str(item.sr_no),
                    item.description[:40],
                    item.hsn_sac or "",
                    str(item.quantity),
                    f"{item.rate:,.2f}",
                    f"{item.taxable_value:,.2f}",
                    f"{item.igst:,.2f}",
                    f"{item.total:,.2f}",
                ]
            else:
                row = [
                    str(item.sr_no),
                    item.description[:40],
                    item.hsn_sac or "",
                    str(item.quantity),
                    f"{item.rate:,.2f}",
                    f"{item.taxable_value:,.2f}",
                    f"{item.cgst:,.2f}",
                    f"{item.sgst:,.2f}",
                    f"{item.total:,.2f}",
                ]
            items_data.append(row)

        items_table = Table(items_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 5 * mm))

        # Totals
        totals_data = [
            ["Subtotal", f"{invoice.currency} {invoice.subtotal:,.2f}"],
            ["Discount", f"(-) {invoice.currency} {invoice.discount_amount:,.2f}"],
            ["Taxable Value", f"{invoice.currency} {invoice.taxable_value:,.2f}"],
        ]
        if invoice.is_interstate:
            totals_data.append(["IGST", f"{invoice.currency} {invoice.igst:,.2f}"])
        else:
            totals_data.append(["CGST", f"{invoice.currency} {invoice.cgst:,.2f}"])
            totals_data.append(["SGST", f"{invoice.currency} {invoice.sgst:,.2f}"])
        if invoice.cess:
            totals_data.append(["Cess", f"{invoice.currency} {invoice.cess:,.2f}"])
        totals_data.append(["Total Amount", f"{invoice.currency} {invoice.total_amount:,.2f}"])

        totals_table = Table(totals_data, colWidths=[350, 130])
        totals_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LINEABOVE", (0, -1), (-1, -1), 1, self.BRAND_COLOR),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 3 * mm))

        # Amount in words
        if invoice.amount_in_words:
            elements.append(
                Paragraph(f"<b>Amount in words:</b> {invoice.amount_in_words}", styles["Normal"])
            )
            elements.append(Spacer(1, 5 * mm))

        # Bank details
        if bank_detail:
            bank_data = [
                ["Bank Details"],
                [f"Bank: {bank_detail.bank_name}"],
                [f"A/C No: {bank_detail.account_number}"],
                [f"IFSC: {bank_detail.ifsc_code}"],
                [f"Branch: {bank_detail.branch or ''}"],
            ]
            bank_table = Table(bank_data, colWidths=[250])
            bank_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(bank_table)
            elements.append(Spacer(1, 5 * mm))

        # Notes & Terms
        if invoice.notes:
            elements.append(Paragraph(f"<b>Notes:</b> {invoice.notes}", styles["Normal"]))
        if invoice.terms_conditions:
            elements.append(Paragraph(f"<b>Terms:</b> {invoice.terms_conditions}", styles["Normal"]))

        elements.append(Spacer(1, 10 * mm))

        # Footer
        footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
        elements.append(
            Paragraph(
                "This is a computer-generated invoice. Generated by Aypa TaxAI (aypa.taxai)",
                footer_style,
            )
        )

        doc.build(elements)
        return buffer.getvalue()

    @staticmethod
    def generate_upi_qr(upi_id: str, amount: float, invoice_number: str, payee_name: str) -> bytes:
        """Generate UPI QR code as PNG bytes."""
        upi_string = (
            f"upi://pay?"
            f"pa={upi_id}&"
            f"pn={payee_name}&"
            f"am={amount:.2f}&"
            f"tn=Invoice {invoice_number}&"
            f"cu=INR"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(upi_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
