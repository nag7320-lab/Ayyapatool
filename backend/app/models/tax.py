"""Tax declaration and computation models."""

import uuid
from datetime import datetime

from app import db


class TaxDeclaration(db.Model):
    """Employee tax declarations for a financial year."""

    __tablename__ = "tax_declarations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    employee_id = db.Column(db.String(36), db.ForeignKey("employees.id"), nullable=True)
    financial_year = db.Column(db.String(7), nullable=False)  # e.g., "2025-26"
    tax_regime = db.Column(db.String(10), default="new")  # old, new

    # Salary details
    basic_salary = db.Column(db.Float, default=0)
    da = db.Column(db.Float, default=0)
    hra_received = db.Column(db.Float, default=0)
    lta = db.Column(db.Float, default=0)
    special_allowance = db.Column(db.Float, default=0)
    other_allowances = db.Column(db.Float, default=0)
    performance_bonus = db.Column(db.Float, default=0)

    # HRA calculation inputs
    rent_paid = db.Column(db.Float, default=0)
    city_type = db.Column(db.String(10), default="NON_METRO")  # METRO, NON_METRO

    # Other income
    income_house_property = db.Column(db.Float, default=0)
    interest_savings = db.Column(db.Float, default=0)
    interest_fd = db.Column(db.Float, default=0)
    other_income = db.Column(db.Float, default=0)

    # Chapter VI-A Deductions
    sec_80c_epf = db.Column(db.Float, default=0)
    sec_80c_ppf = db.Column(db.Float, default=0)
    sec_80c_life_insurance = db.Column(db.Float, default=0)
    sec_80c_elss = db.Column(db.Float, default=0)
    sec_80c_home_loan_principal = db.Column(db.Float, default=0)
    sec_80c_children_tuition = db.Column(db.Float, default=0)
    sec_80c_other = db.Column(db.Float, default=0)

    sec_80ccc_pension = db.Column(db.Float, default=0)
    sec_80ccd_1b_nps = db.Column(db.Float, default=0)
    sec_80ccd_2_employer_nps = db.Column(db.Float, default=0)

    sec_80d_self = db.Column(db.Float, default=0)
    sec_80d_parents = db.Column(db.Float, default=0)
    sec_80d_preventive_health = db.Column(db.Float, default=0)

    sec_80e_education_loan = db.Column(db.Float, default=0)
    sec_80g_donations = db.Column(db.Float, default=0)
    sec_80gg_rent = db.Column(db.Float, default=0)
    sec_80tta_interest = db.Column(db.Float, default=0)
    sec_80u_disability = db.Column(db.Float, default=0)
    sec_80ddb_medical = db.Column(db.Float, default=0)

    # Home loan
    home_loan_interest = db.Column(db.Float, default=0)

    # Status
    status = db.Column(db.String(20), default="draft")  # draft, submitted, verified
    submitted_at = db.Column(db.DateTime)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.String(36))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def total_80c(self):
        """Total Section 80C deductions (capped at 1,50,000)."""
        raw = (
            self.sec_80c_epf
            + self.sec_80c_ppf
            + self.sec_80c_life_insurance
            + self.sec_80c_elss
            + self.sec_80c_home_loan_principal
            + self.sec_80c_children_tuition
            + self.sec_80c_other
        )
        return min(raw, 150000)

    def total_80d(self):
        """Total Section 80D deductions."""
        self_limit = min(self.sec_80d_self + self.sec_80d_preventive_health, 25000)
        parents_limit = min(self.sec_80d_parents, 50000)  # 50k if senior citizen
        return self_limit + parents_limit


class TaxComputation(db.Model):
    """Computed tax report for a declaration."""

    __tablename__ = "tax_computations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    declaration_id = db.Column(
        db.String(36), db.ForeignKey("tax_declarations.id"), nullable=False
    )
    financial_year = db.Column(db.String(7), nullable=False)

    # Income summary
    gross_salary = db.Column(db.Float, default=0)
    exemptions = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    standard_deduction = db.Column(db.Float, default=50000)
    professional_tax = db.Column(db.Float, default=0)
    income_from_salary = db.Column(db.Float, default=0)

    income_house_property = db.Column(db.Float, default=0)
    income_other_sources = db.Column(db.Float, default=0)
    gross_total_income = db.Column(db.Float, default=0)

    # Deductions summary
    total_deductions = db.Column(db.Float, default=0)
    taxable_income = db.Column(db.Float, default=0)

    # Old regime
    old_regime_tax = db.Column(db.Float, default=0)
    old_regime_cess = db.Column(db.Float, default=0)
    old_regime_total = db.Column(db.Float, default=0)

    # New regime
    new_regime_tax = db.Column(db.Float, default=0)
    new_regime_cess = db.Column(db.Float, default=0)
    new_regime_total = db.Column(db.Float, default=0)

    # Recommendation
    recommended_regime = db.Column(db.String(10))
    savings = db.Column(db.Float, default=0)

    # TDS
    tds_deducted = db.Column(db.Float, default=0)
    tax_payable_or_refund = db.Column(db.Float, default=0)

    # PDF
    report_pdf_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
