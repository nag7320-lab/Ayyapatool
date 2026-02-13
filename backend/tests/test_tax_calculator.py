"""Tests for the income tax calculator."""

import pytest

from app.services.tax.calculator import TaxCalculator, TaxInput


class TestHRAExemption:
    def test_metro_city(self):
        calc = TaxCalculator()
        exemption = calc.calculate_hra_exemption(
            hra_received=180000,
            basic_da=720000,
            rent_paid=240000,
            city_type="METRO",
        )
        # min(180000, 50% of 720000=360000, 240000 - 10% of 720000=168000)
        assert exemption == 168000

    def test_non_metro_city(self):
        calc = TaxCalculator()
        exemption = calc.calculate_hra_exemption(
            hra_received=180000,
            basic_da=720000,
            rent_paid=240000,
            city_type="NON_METRO",
        )
        # min(180000, 40% of 720000=288000, 240000 - 72000=168000)
        assert exemption == 168000

    def test_zero_rent(self):
        calc = TaxCalculator()
        exemption = calc.calculate_hra_exemption(
            hra_received=180000,
            basic_da=720000,
            rent_paid=0,
            city_type="METRO",
        )
        assert exemption == 0


class TestTaxComputation:
    def test_basic_computation(self):
        calc = TaxCalculator()
        inputs = TaxInput(
            basic_salary=600000,
            hra_received=180000,
            special_allowance=220000,
        )
        result = calc.compute(inputs)

        assert result.gross_salary == 1000000
        assert result.recommended_regime in ("old", "new")
        assert result.new_total_tax >= 0
        assert result.old_total_tax >= 0

    def test_new_regime_rebate(self):
        """Income <= 7L in new regime should get full rebate."""
        calc = TaxCalculator()
        inputs = TaxInput(basic_salary=550000)  # Under 7L after std deduction
        result = calc.compute(inputs)

        # With 5.5L gross, after 50k std deduction = 5L taxable
        # New regime: under 7L gets rebate
        assert result.new_total_tax == 0 or result.new_rebate > 0

    def test_old_regime_with_deductions(self):
        calc = TaxCalculator()
        inputs = TaxInput(
            basic_salary=1200000,
            hra_received=360000,
            special_allowance=440000,
            rent_paid=300000,
            city_type="METRO",
            sec_80c_total=150000,
            sec_80d_self=25000,
            sec_80ccd_1b=50000,
        )
        result = calc.compute(inputs)

        # Old regime should have higher deductions
        assert result.old_deductions > result.new_deductions
        assert result.savings > 0


class TestSlabTax:
    def test_zero_income(self):
        calc = TaxCalculator()
        from app.services.tax.calculator import NEW_REGIME_SLABS
        tax = calc._compute_slab_tax(0, NEW_REGIME_SLABS)
        assert tax == 0

    def test_known_amount(self):
        calc = TaxCalculator()
        from app.services.tax.calculator import NEW_REGIME_SLABS
        # 10,00,000 income under new regime:
        # 0-3L: 0, 3-6L: 15000, 6-9L: 30000, 9-10L: 15000 = 60000
        tax = calc._compute_slab_tax(1000000, NEW_REGIME_SLABS)
        assert tax == 60000
