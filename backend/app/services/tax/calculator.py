"""Comprehensive income tax calculator with old vs new regime comparison."""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# FY 2025-26 Tax Slabs
OLD_REGIME_SLABS = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

NEW_REGIME_SLABS = [
    (300000, 0.00),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float("inf"), 0.30),
]

CESS_RATE = 0.04
STANDARD_DEDUCTION = 50000
REBATE_87A_LIMIT_NEW = 700000
REBATE_87A_MAX_NEW = 25000
REBATE_87A_LIMIT_OLD = 500000
REBATE_87A_MAX_OLD = 12500


@dataclass
class TaxInput:
    """All inputs needed for tax computation."""

    # Salary
    basic_salary: float = 0
    da: float = 0
    hra_received: float = 0
    lta: float = 0
    special_allowance: float = 0
    other_allowances: float = 0
    performance_bonus: float = 0

    # HRA inputs
    rent_paid: float = 0
    city_type: str = "NON_METRO"  # METRO or NON_METRO

    # Other income
    income_house_property: float = 0
    interest_savings: float = 0
    interest_fd: float = 0
    other_income: float = 0

    # Deductions
    sec_80c_total: float = 0
    sec_80ccc: float = 0
    sec_80ccd_1b: float = 0
    sec_80ccd_2: float = 0
    sec_80d_self: float = 0
    sec_80d_parents: float = 0
    sec_80e: float = 0
    sec_80g: float = 0
    sec_80gg: float = 0
    sec_80tta: float = 0
    sec_80u: float = 0
    sec_80ddb: float = 0

    # Home loan
    home_loan_interest: float = 0

    # Professional tax paid
    professional_tax: float = 0

    # TDS already deducted
    tds_deducted: float = 0


@dataclass
class TaxResult:
    """Computed tax results for both regimes."""

    # Income summary
    gross_salary: float = 0
    hra_exemption: float = 0
    lta_exemption: float = 0
    total_exemptions: float = 0
    net_salary: float = 0
    standard_deduction: float = STANDARD_DEDUCTION
    professional_tax: float = 0
    income_from_salary: float = 0

    income_house_property: float = 0
    income_other_sources: float = 0
    gross_total_income: float = 0

    # Old regime
    old_deductions: float = 0
    old_taxable_income: float = 0
    old_tax: float = 0
    old_rebate: float = 0
    old_tax_after_rebate: float = 0
    old_cess: float = 0
    old_total_tax: float = 0

    # New regime
    new_deductions: float = 0
    new_taxable_income: float = 0
    new_tax: float = 0
    new_rebate: float = 0
    new_tax_after_rebate: float = 0
    new_cess: float = 0
    new_total_tax: float = 0

    # Recommendation
    recommended_regime: str = ""
    savings: float = 0

    # Net payable/refund
    tds_deducted: float = 0
    old_payable_or_refund: float = 0
    new_payable_or_refund: float = 0


class TaxCalculator:
    """Income tax calculator supporting FY 2025-26."""

    def compute(self, inputs: TaxInput) -> TaxResult:
        """Compute full tax for both regimes."""
        result = TaxResult()

        # Step 1: Gross salary
        result.gross_salary = (
            inputs.basic_salary
            + inputs.da
            + inputs.hra_received
            + inputs.lta
            + inputs.special_allowance
            + inputs.other_allowances
            + inputs.performance_bonus
        )

        # Step 2: Exemptions (for old regime)
        result.hra_exemption = self.calculate_hra_exemption(
            inputs.hra_received,
            inputs.basic_salary + inputs.da,
            inputs.rent_paid,
            inputs.city_type,
        )
        result.lta_exemption = min(inputs.lta, inputs.lta)  # Actual claim
        result.total_exemptions = result.hra_exemption + result.lta_exemption

        # Step 3: Net salary and income from salary
        result.net_salary = result.gross_salary - result.total_exemptions
        result.professional_tax = min(inputs.professional_tax, 2500)
        result.income_from_salary = (
            result.net_salary - result.standard_deduction - result.professional_tax
        )

        # Step 4: Other income
        result.income_house_property = inputs.income_house_property
        if inputs.home_loan_interest > 0:
            result.income_house_property -= min(inputs.home_loan_interest, 200000)

        result.income_other_sources = (
            inputs.interest_savings + inputs.interest_fd + inputs.other_income
        )

        result.gross_total_income = (
            result.income_from_salary
            + max(result.income_house_property, -200000)
            + result.income_other_sources
        )

        # Step 5: OLD REGIME deductions
        sec_80c = min(inputs.sec_80c_total, 150000)
        sec_80ccc = min(inputs.sec_80ccc, 150000 - sec_80c) if inputs.sec_80ccc else 0
        total_80c_ccc_ccd = min(sec_80c + sec_80ccc, 150000)

        sec_80ccd_1b = min(inputs.sec_80ccd_1b, 50000)
        sec_80ccd_2 = inputs.sec_80ccd_2  # No cap (up to 10% of basic)

        sec_80d = min(inputs.sec_80d_self, 25000) + min(inputs.sec_80d_parents, 50000)
        sec_80tta = min(inputs.sec_80tta, 10000)

        result.old_deductions = (
            total_80c_ccc_ccd
            + sec_80ccd_1b
            + sec_80ccd_2
            + sec_80d
            + inputs.sec_80e
            + inputs.sec_80g
            + inputs.sec_80gg
            + sec_80tta
            + inputs.sec_80u
            + inputs.sec_80ddb
        )

        result.old_taxable_income = max(
            result.gross_total_income - result.old_deductions, 0
        )
        result.old_taxable_income = self._round_to_10(result.old_taxable_income)

        result.old_tax = self._compute_slab_tax(result.old_taxable_income, OLD_REGIME_SLABS)

        # Old regime rebate u/s 87A
        if result.old_taxable_income <= REBATE_87A_LIMIT_OLD:
            result.old_rebate = min(result.old_tax, REBATE_87A_MAX_OLD)
        result.old_tax_after_rebate = max(result.old_tax - result.old_rebate, 0)
        result.old_cess = round(result.old_tax_after_rebate * CESS_RATE, 0)
        result.old_total_tax = result.old_tax_after_rebate + result.old_cess

        # Step 6: NEW REGIME deductions (limited)
        # Only 80CCD(2) employer NPS is allowed
        result.new_deductions = inputs.sec_80ccd_2

        # New regime: no HRA/LTA exemptions, apply standard deduction on gross
        new_income_from_salary = (
            result.gross_salary - result.standard_deduction - result.professional_tax
        )
        new_gti = (
            new_income_from_salary
            + max(result.income_house_property, -200000)
            + result.income_other_sources
        )
        result.new_taxable_income = max(new_gti - result.new_deductions, 0)
        result.new_taxable_income = self._round_to_10(result.new_taxable_income)

        result.new_tax = self._compute_slab_tax(result.new_taxable_income, NEW_REGIME_SLABS)

        # New regime rebate u/s 87A
        if result.new_taxable_income <= REBATE_87A_LIMIT_NEW:
            result.new_rebate = min(result.new_tax, REBATE_87A_MAX_NEW)
        result.new_tax_after_rebate = max(result.new_tax - result.new_rebate, 0)
        result.new_cess = round(result.new_tax_after_rebate * CESS_RATE, 0)
        result.new_total_tax = result.new_tax_after_rebate + result.new_cess

        # Step 7: Recommendation
        if result.old_total_tax <= result.new_total_tax:
            result.recommended_regime = "old"
            result.savings = result.new_total_tax - result.old_total_tax
        else:
            result.recommended_regime = "new"
            result.savings = result.old_total_tax - result.new_total_tax

        # Step 8: Payable / Refund
        result.tds_deducted = inputs.tds_deducted
        result.old_payable_or_refund = result.old_total_tax - inputs.tds_deducted
        result.new_payable_or_refund = result.new_total_tax - inputs.tds_deducted

        return result

    @staticmethod
    def calculate_hra_exemption(
        hra_received: float,
        basic_da: float,
        rent_paid: float,
        city_type: str,
    ) -> float:
        """Calculate HRA exemption u/s 10(13A)."""
        if hra_received == 0 or rent_paid == 0:
            return 0

        metro_percent = 0.50 if city_type == "METRO" else 0.40
        exemption = min(
            hra_received,
            metro_percent * basic_da,
            max(0, rent_paid - 0.10 * basic_da),
        )
        return round(max(exemption, 0), 0)

    @staticmethod
    def _compute_slab_tax(income: float, slabs: list[tuple]) -> float:
        """Compute tax using progressive slab rates."""
        tax = 0.0
        prev_limit = 0

        for limit, rate in slabs:
            if income <= prev_limit:
                break
            taxable_in_slab = min(income, limit) - prev_limit
            tax += taxable_in_slab * rate
            prev_limit = limit

        return round(tax, 0)

    @staticmethod
    def _round_to_10(amount: float) -> float:
        """Round down to nearest 10 as per section 288A."""
        return float(int(amount / 10) * 10)
