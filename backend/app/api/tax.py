"""Tax calculator API endpoints."""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db, limiter
from app.models.tax import TaxComputation, TaxDeclaration

tax_bp = Blueprint("tax", __name__)
logger = logging.getLogger(__name__)


@tax_bp.route("/compute", methods=["POST"])
@jwt_required()
@limiter.limit("30/minute")
def compute_tax():
    """
    Compute income tax for both old and new regimes.
    Returns comparison and recommendation.
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    from app.services.tax.calculator import TaxCalculator, TaxInput

    inputs = TaxInput(
        basic_salary=data.get("basic_salary", 0),
        da=data.get("da", 0),
        hra_received=data.get("hra_received", 0),
        lta=data.get("lta", 0),
        special_allowance=data.get("special_allowance", 0),
        other_allowances=data.get("other_allowances", 0),
        performance_bonus=data.get("performance_bonus", 0),
        rent_paid=data.get("rent_paid", 0),
        city_type=data.get("city_type", "NON_METRO"),
        income_house_property=data.get("income_house_property", 0),
        interest_savings=data.get("interest_savings", 0),
        interest_fd=data.get("interest_fd", 0),
        other_income=data.get("other_income", 0),
        sec_80c_total=data.get("sec_80c_total", 0),
        sec_80ccc=data.get("sec_80ccc", 0),
        sec_80ccd_1b=data.get("sec_80ccd_1b", 0),
        sec_80ccd_2=data.get("sec_80ccd_2", 0),
        sec_80d_self=data.get("sec_80d_self", 0),
        sec_80d_parents=data.get("sec_80d_parents", 0),
        sec_80e=data.get("sec_80e", 0),
        sec_80g=data.get("sec_80g", 0),
        sec_80gg=data.get("sec_80gg", 0),
        sec_80tta=data.get("sec_80tta", 0),
        sec_80u=data.get("sec_80u", 0),
        sec_80ddb=data.get("sec_80ddb", 0),
        home_loan_interest=data.get("home_loan_interest", 0),
        professional_tax=data.get("professional_tax", 0),
        tds_deducted=data.get("tds_deducted", 0),
    )

    calculator = TaxCalculator()
    result = calculator.compute(inputs)

    return jsonify({
        "income_summary": {
            "gross_salary": result.gross_salary,
            "hra_exemption": result.hra_exemption,
            "total_exemptions": result.total_exemptions,
            "net_salary": result.net_salary,
            "standard_deduction": result.standard_deduction,
            "income_from_salary": result.income_from_salary,
            "income_house_property": result.income_house_property,
            "income_other_sources": result.income_other_sources,
            "gross_total_income": result.gross_total_income,
        },
        "old_regime": {
            "deductions": result.old_deductions,
            "taxable_income": result.old_taxable_income,
            "tax": result.old_tax,
            "rebate": result.old_rebate,
            "cess": result.old_cess,
            "total_tax": result.old_total_tax,
            "payable_or_refund": result.old_payable_or_refund,
        },
        "new_regime": {
            "deductions": result.new_deductions,
            "taxable_income": result.new_taxable_income,
            "tax": result.new_tax,
            "rebate": result.new_rebate,
            "cess": result.new_cess,
            "total_tax": result.new_total_tax,
            "payable_or_refund": result.new_payable_or_refund,
        },
        "recommendation": {
            "regime": result.recommended_regime,
            "savings": result.savings,
        },
        "disclaimer": (
            "This tool is provided for convenience. Aypa TaxAI does not guarantee "
            "accuracy for all scenarios. Users are responsible for verifying "
            "calculations before submission to tax authorities."
        ),
    })


@tax_bp.route("/hra-exemption", methods=["POST"])
@jwt_required()
def calculate_hra():
    """Calculate HRA exemption u/s 10(13A)."""
    data = request.get_json()
    from app.services.tax.calculator import TaxCalculator

    calc = TaxCalculator()
    exemption = calc.calculate_hra_exemption(
        hra_received=data.get("hra_received", 0),
        basic_da=data.get("basic_da", 0),
        rent_paid=data.get("rent_paid", 0),
        city_type=data.get("city_type", "NON_METRO"),
    )

    return jsonify({
        "hra_received": data.get("hra_received", 0),
        "exemption": exemption,
        "taxable_hra": data.get("hra_received", 0) - exemption,
    })


@tax_bp.route("/form16-upload", methods=["POST"])
@jwt_required()
@limiter.limit("10/minute")
def upload_form16():
    """Upload Form 16 PDF and auto-extract data."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    try:
        from app.services.tax.form16_parser import Form16Parser

        parser = Form16Parser()
        extracted_data = parser.parse(file.read())

        return jsonify({
            "status": "success",
            "data": extracted_data,
            "message": "Data extracted. Please verify before computing tax.",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Form 16 parsing error: {e}", exc_info=True)
        return jsonify({"error": "Failed to parse Form 16"}), 500


@tax_bp.route("/gst-rates", methods=["GET"])
def get_gst_rates():
    """Get GST rates and HSN/SAC codes (public endpoint)."""
    from app.services.invoice.gst_utils import GST_RATES, HSN_CODES

    hsn_code = request.args.get("hsn")
    if hsn_code:
        from app.services.invoice.gst_utils import GSTValidator
        suggested_rate = GSTValidator.suggest_gst_rate(hsn_code)
        info = HSN_CODES.get(hsn_code, {})
        return jsonify({
            "hsn_code": hsn_code,
            "description": info.get("description", "Unknown"),
            "suggested_gst_rate": suggested_rate,
        })

    return jsonify({"gst_rates": GST_RATES})
