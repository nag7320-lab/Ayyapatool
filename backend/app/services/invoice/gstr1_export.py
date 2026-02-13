"""GSTR-1 export in filing-ready Excel format."""

import io
import logging

import pandas as pd
from sqlalchemy import extract

from app import db
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)


class GSTR1Exporter:
    """Export invoices in GSTR-1 filing format."""

    def export(self, org_id: str, month: int, year: int) -> io.BytesIO:
        """
        Export invoices for a given month in GSTR-1 format.

        Tables:
        - B2B (Table 4A): Invoices to registered businesses
        - B2CL (Table 5): Large invoices to unregistered (>2.5L)
        - B2CS (Table 7): Small invoices to unregistered (<2.5L)
        - CDNR (Table 9B): Credit/Debit notes to registered
        - EXP (Table 6A): Exports
        """
        invoices = Invoice.query.filter(
            Invoice.org_id == org_id,
            extract("month", Invoice.invoice_date) == month,
            extract("year", Invoice.invoice_date) == year,
            Invoice.status != "cancelled",
            Invoice.invoice_type.in_(["tax_invoice", "export", "debit_note", "credit_note"]),
        ).all()

        b2b_data = []
        b2cl_data = []
        b2cs_summary = {}
        cdnr_data = []
        export_data = []

        for inv in invoices:
            if inv.invoice_type == "export":
                export_data.append(self._format_export(inv))
            elif inv.invoice_type in ("debit_note", "credit_note") and inv.customer_gstin:
                cdnr_data.append(self._format_cdnr(inv))
            elif inv.customer_gstin:
                b2b_data.append(self._format_b2b(inv))
            elif inv.total_amount > 250000:
                b2cl_data.append(self._format_b2cl(inv))
            else:
                key = (inv.place_of_supply, inv.items[0].gst_rate if inv.items else 0)
                if key not in b2cs_summary:
                    b2cs_summary[key] = {"taxable_value": 0, "igst": 0, "cgst": 0, "sgst": 0}
                b2cs_summary[key]["taxable_value"] += inv.taxable_value
                b2cs_summary[key]["igst"] += inv.igst
                b2cs_summary[key]["cgst"] += inv.cgst
                b2cs_summary[key]["sgst"] += inv.sgst

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if b2b_data:
                pd.DataFrame(b2b_data).to_excel(writer, sheet_name="B2B", index=False)
            if b2cl_data:
                pd.DataFrame(b2cl_data).to_excel(writer, sheet_name="B2CL", index=False)
            if b2cs_summary:
                b2cs_rows = [
                    {
                        "Place of Supply": pos,
                        "Rate": rate,
                        "Taxable Value": s["taxable_value"],
                        "IGST": s["igst"],
                        "CGST": s["cgst"],
                        "SGST": s["sgst"],
                    }
                    for (pos, rate), s in b2cs_summary.items()
                ]
                pd.DataFrame(b2cs_rows).to_excel(writer, sheet_name="B2CS", index=False)
            if cdnr_data:
                pd.DataFrame(cdnr_data).to_excel(writer, sheet_name="CDNR", index=False)
            if export_data:
                pd.DataFrame(export_data).to_excel(writer, sheet_name="EXPORTS", index=False)

            # If no data, write an empty summary
            if not any([b2b_data, b2cl_data, b2cs_summary, cdnr_data, export_data]):
                pd.DataFrame({"Message": ["No invoices found for this period"]}).to_excel(
                    writer, sheet_name="Summary", index=False
                )

        output.seek(0)
        return output

    @staticmethod
    def _format_b2b(inv: Invoice) -> dict:
        return {
            "GSTIN of Recipient": inv.customer_gstin,
            "Receiver Name": inv.customer_name,
            "Invoice Number": inv.invoice_number,
            "Invoice date": inv.invoice_date.strftime("%d-%m-%Y"),
            "Invoice Value": round(inv.total_amount, 2),
            "Place Of Supply": inv.place_of_supply,
            "Reverse Charge": "N",
            "Invoice Type": "Regular",
            "Rate": inv.items[0].gst_rate if inv.items else 0,
            "Taxable Value": round(inv.taxable_value, 2),
            "Cess Amount": round(inv.cess, 2),
            "IGST Amount": round(inv.igst, 2),
            "CGST Amount": round(inv.cgst, 2),
            "SGST/UTGST Amount": round(inv.sgst, 2),
        }

    @staticmethod
    def _format_b2cl(inv: Invoice) -> dict:
        return {
            "Invoice Number": inv.invoice_number,
            "Invoice date": inv.invoice_date.strftime("%d-%m-%Y"),
            "Invoice Value": round(inv.total_amount, 2),
            "Place Of Supply": inv.place_of_supply,
            "Rate": inv.items[0].gst_rate if inv.items else 0,
            "Taxable Value": round(inv.taxable_value, 2),
            "Cess Amount": round(inv.cess, 2),
        }

    @staticmethod
    def _format_cdnr(inv: Invoice) -> dict:
        return {
            "GSTIN of Recipient": inv.customer_gstin,
            "Note Number": inv.invoice_number,
            "Note Date": inv.invoice_date.strftime("%d-%m-%Y"),
            "Note Type": "D" if inv.invoice_type == "debit_note" else "C",
            "Note Value": round(inv.total_amount, 2),
            "Place Of Supply": inv.place_of_supply,
            "Rate": inv.items[0].gst_rate if inv.items else 0,
            "Taxable Value": round(inv.taxable_value, 2),
            "IGST Amount": round(inv.igst, 2),
            "CGST Amount": round(inv.cgst, 2),
            "SGST/UTGST Amount": round(inv.sgst, 2),
            "Cess Amount": round(inv.cess, 2),
        }

    @staticmethod
    def _format_export(inv: Invoice) -> dict:
        return {
            "Export Type": "WPAY" if inv.igst > 0 else "WOPAY",
            "Invoice Number": inv.invoice_number,
            "Invoice date": inv.invoice_date.strftime("%d-%m-%Y"),
            "Invoice Value": round(inv.total_amount, 2),
            "Port Code": inv.port_of_export or "",
            "Shipping Bill Number": inv.shipping_bill_no or "",
            "Shipping Bill Date": inv.shipping_bill_date.strftime("%d-%m-%Y") if inv.shipping_bill_date else "",
            "Rate": inv.items[0].gst_rate if inv.items else 0,
            "Taxable Value": round(inv.taxable_value, 2),
            "IGST Amount": round(inv.igst, 2),
            "Cess Amount": round(inv.cess, 2),
        }
