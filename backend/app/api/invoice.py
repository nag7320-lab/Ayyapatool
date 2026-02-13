"""Invoice management API endpoints."""

import logging
from datetime import date

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db, limiter
from app.models.invoice import BankDetail, Invoice
from app.models.user import OrgMembership

invoice_bp = Blueprint("invoice", __name__)
logger = logging.getLogger(__name__)


def _get_user_org(user_id: str, org_id: str = None):
    """Get the user's active organization."""
    if org_id:
        membership = OrgMembership.query.filter_by(user_id=user_id, org_id=org_id).first()
    else:
        membership = OrgMembership.query.filter_by(user_id=user_id, is_default=True).first()
    return membership


@invoice_bp.route("/", methods=["POST"])
@jwt_required()
@limiter.limit("60/minute")
def create_invoice():
    """Create a new invoice."""
    user_id = get_jwt_identity()
    data = request.get_json()

    org_id = data.get("org_id")
    membership = _get_user_org(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    try:
        from app.services.invoice.generator import InvoiceGenerator

        generator = InvoiceGenerator()
        invoice = generator.create_invoice(
            org_id=membership.org_id,
            user_id=user_id,
            invoice_type=data.get("invoice_type", "tax_invoice"),
            invoice_data=data.get("invoice_data", {}),
            items_data=data.get("items", []),
        )

        return jsonify({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Invoice creation error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create invoice"}), 500


@invoice_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    """List invoices for an organization."""
    user_id = get_jwt_identity()
    org_id = request.args.get("org_id")

    membership = _get_user_org(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status = request.args.get("status")
    invoice_type = request.args.get("type")

    query = Invoice.query.filter_by(org_id=membership.org_id)
    if status:
        query = query.filter_by(status=status)
    if invoice_type:
        query = query.filter_by(invoice_type=invoice_type)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_type": inv.invoice_type,
                "invoice_date": inv.invoice_date.isoformat(),
                "customer_name": inv.customer_name,
                "total_amount": inv.total_amount,
                "status": inv.status,
            }
            for inv in pagination.items
        ],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@invoice_bp.route("/<invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(invoice_id):
    """Get full invoice details."""
    user_id = get_jwt_identity()
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    membership = _get_user_org(user_id, invoice.org_id)
    if not membership:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_type": invoice.invoice_type,
        "invoice_date": invoice.invoice_date.isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "supplier": {
            "name": invoice.supplier_name,
            "gstin": invoice.supplier_gstin,
            "address": invoice.supplier_address,
            "state": invoice.supplier_state,
        },
        "customer": {
            "name": invoice.customer_name,
            "gstin": invoice.customer_gstin,
            "address": invoice.customer_address,
            "state": invoice.customer_state,
        },
        "place_of_supply": invoice.place_of_supply,
        "is_interstate": invoice.is_interstate,
        "items": [
            {
                "sr_no": item.sr_no,
                "description": item.description,
                "hsn_sac": item.hsn_sac,
                "quantity": item.quantity,
                "rate": item.rate,
                "amount": item.amount,
                "gst_rate": item.gst_rate,
                "cgst": item.cgst,
                "sgst": item.sgst,
                "igst": item.igst,
                "total": item.total,
            }
            for item in invoice.items
        ],
        "subtotal": invoice.subtotal,
        "discount_amount": invoice.discount_amount,
        "taxable_value": invoice.taxable_value,
        "cgst": invoice.cgst,
        "sgst": invoice.sgst,
        "igst": invoice.igst,
        "total_tax": invoice.total_tax,
        "total_amount": invoice.total_amount,
        "amount_in_words": invoice.amount_in_words,
        "currency": invoice.currency,
        "status": invoice.status,
        "notes": invoice.notes,
    })


@invoice_bp.route("/<invoice_id>/pdf", methods=["GET"])
@jwt_required()
def download_invoice_pdf(invoice_id):
    """Generate and download invoice PDF."""
    user_id = get_jwt_identity()
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    membership = _get_user_org(user_id, invoice.org_id)
    if not membership:
        return jsonify({"error": "Access denied"}), 403

    from app.services.invoice.pdf_generator import InvoicePDFGenerator
    import io

    bank_detail = BankDetail.query.filter_by(org_id=invoice.org_id, is_default=True).first()
    pdf_gen = InvoicePDFGenerator()
    pdf_bytes = pdf_gen.generate(invoice, bank_detail)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{invoice.invoice_number.replace('/', '_')}.pdf",
    )


@invoice_bp.route("/bulk", methods=["POST"])
@jwt_required()
@limiter.limit("5/minute")
def bulk_generate():
    """Bulk generate invoices from Excel upload."""
    user_id = get_jwt_identity()
    org_id = request.form.get("org_id")

    membership = _get_user_org(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith((".xlsx", ".xls")):
        return jsonify({"error": "Only Excel files are accepted"}), 400

    try:
        from app.services.invoice.bulk import BulkInvoiceProcessor

        processor = BulkInvoiceProcessor()
        result = processor.process(file, membership.org_id, user_id)

        if result["successful"] > 0:
            return send_file(
                result["zip_file"],
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"invoices_bulk_{date.today().isoformat()}.zip",
            )
        else:
            return jsonify({
                "error": "All invoices failed",
                "total": result["total_rows"],
                "errors": result["errors"],
            }), 400

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@invoice_bp.route("/gstr1-export", methods=["GET"])
@jwt_required()
def export_gstr1():
    """Export invoices in GSTR-1 format."""
    user_id = get_jwt_identity()
    org_id = request.args.get("org_id")
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    if not all([month, year]):
        return jsonify({"error": "month and year are required"}), 400

    membership = _get_user_org(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    from app.services.invoice.gstr1_export import GSTR1Exporter

    exporter = GSTR1Exporter()
    output = exporter.export(membership.org_id, month, year)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"GSTR1_{year}_{month:02d}.xlsx",
    )
