"""Bulk invoice generation from Excel upload."""

import io
import logging
import zipfile

import pandas as pd

from app.services.invoice.generator import InvoiceGenerator

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "Invoice Date",
    "Customer Name",
    "Billing Address",
    "State",
    "Item Description",
    "HSN/SAC",
    "Quantity",
    "Rate",
    "GST Rate",
]


class BulkInvoiceProcessor:
    """Process bulk invoice generation from Excel."""

    def __init__(self):
        self.generator = InvoiceGenerator()

    def process(self, excel_file, org_id: str, user_id: str) -> dict:
        """
        Generate multiple invoices from uploaded Excel file.
        Returns dict with results and a ZIP of PDFs.
        """
        df = pd.read_excel(excel_file)

        # Validate columns
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        from app.services.invoice.pdf_generator import InvoicePDFGenerator

        pdf_gen = InvoicePDFGenerator()
        invoice_pdfs = []
        errors = []

        for index, row in df.iterrows():
            try:
                invoice_data = {
                    "invoice_date": pd.to_datetime(row["Invoice Date"], format="%d-%m-%Y").date(),
                    "customer_name": str(row["Customer Name"]),
                    "customer_gstin": str(row.get("Customer GSTIN", "")) if pd.notna(row.get("Customer GSTIN")) else "",
                    "customer_address": str(row["Billing Address"]),
                    "customer_state": str(row["State"]),
                    "place_of_supply": str(row["State"]),
                }

                items_data = [
                    {
                        "description": str(row["Item Description"]),
                        "hsn_sac": str(row["HSN/SAC"]),
                        "quantity": float(row["Quantity"]),
                        "rate": float(row["Rate"]),
                        "gst_rate": float(row["GST Rate"]),
                        "discount_percent": float(row.get("Discount %", 0)) if pd.notna(row.get("Discount %")) else 0,
                    }
                ]

                invoice = self.generator.create_invoice(
                    org_id=org_id,
                    user_id=user_id,
                    invoice_type="tax_invoice",
                    invoice_data=invoice_data,
                    items_data=items_data,
                )

                pdf_bytes = pdf_gen.generate(invoice)
                invoice_pdfs.append((invoice.invoice_number, pdf_bytes))

            except Exception as e:
                errors.append({"row": index + 2, "errors": [str(e)]})

        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for inv_num, pdf_bytes in invoice_pdfs:
                safe_name = inv_num.replace("/", "_")
                zf.writestr(f"{safe_name}.pdf", pdf_bytes)

            if errors:
                error_log = "\n".join(
                    f"Row {e['row']}: {', '.join(e['errors'])}" for e in errors
                )
                zf.writestr("errors.txt", error_log)

        zip_buffer.seek(0)

        return {
            "total_rows": len(df),
            "successful": len(invoice_pdfs),
            "failed": len(errors),
            "errors": errors,
            "zip_file": zip_buffer,
        }
