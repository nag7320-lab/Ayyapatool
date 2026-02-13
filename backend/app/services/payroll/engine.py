"""Payroll calculation engine - India-compliant (PF, ESI, PT, TDS)."""

import logging
from datetime import date
from typing import Optional

from app import db
from app.models.payroll import (
    Attendance,
    Employee,
    EmployeeLoan,
    Payslip,
    SalaryStructure,
)

logger = logging.getLogger(__name__)

# Professional Tax slabs by state (monthly)
PT_SLABS = {
    "Maharashtra": [
        (0, 7500, 0),
        (7501, 10000, 175),
        (10001, float("inf"), 200),
    ],
    "Karnataka": [
        (0, 15000, 0),
        (15001, float("inf"), 200),
    ],
    "Telangana": [
        (0, 15000, 0),
        (15001, 20000, 150),
        (20001, float("inf"), 200),
    ],
    "Andhra Pradesh": [
        (0, 15000, 0),
        (15001, 20000, 150),
        (20001, float("inf"), 200),
    ],
    "Tamil Nadu": [
        (0, 21000, 0),
        (21001, 30000, 135),
        (30001, 45000, 315),
        (45001, 60000, 690),
        (60001, 75000, 1025),
        (75001, float("inf"), 1250),
    ],
    "West Bengal": [
        (0, 10000, 0),
        (10001, 15000, 110),
        (15001, 25000, 130),
        (25001, 40000, 150),
        (40001, float("inf"), 200),
    ],
}

# Salary structure templates
SALARY_TEMPLATES = {
    "it_startup": {
        "basic": 0.40,
        "hra": 0.20,
        "special_allowance": 0.27,
        "employer_pf": 0.12,
        "gratuity": 0.01,
    },
    "manufacturing": {
        "basic": 0.50,
        "da": 0.05,
        "hra": 0.15,
        "conveyance": 0.02,
        "special_allowance": 0.15,
        "employer_pf": 0.12,
        "gratuity": 0.01,
    },
    "services": {
        "basic": 0.45,
        "hra": 0.18,
        "lta": 0.02,
        "special_allowance": 0.22,
        "employer_pf": 0.12,
        "gratuity": 0.01,
    },
}


class PayrollEngine:
    """Complete payroll calculation engine for Indian payroll."""

    # Statutory constants FY 2025-26
    PF_WAGE_CEILING = 15000
    ESI_WAGE_CEILING = 21000
    PF_RATE_EMPLOYEE = 0.12
    PF_RATE_EMPLOYER = 0.12
    ESI_RATE_EMPLOYEE = 0.0075
    ESI_RATE_EMPLOYER = 0.0325

    def create_salary_structure(
        self,
        employee_id: str,
        annual_ctc: float,
        template: str = "it_startup",
        effective_from: Optional[date] = None,
    ) -> SalaryStructure:
        """Create salary structure from CTC using a template."""
        tpl = SALARY_TEMPLATES.get(template, SALARY_TEMPLATES["it_startup"])
        monthly_ctc = annual_ctc / 12

        structure = SalaryStructure(
            employee_id=employee_id,
            annual_ctc=annual_ctc,
            monthly_ctc=monthly_ctc,
            basic=round(monthly_ctc * tpl.get("basic", 0.40), 0),
            da=round(monthly_ctc * tpl.get("da", 0), 0),
            hra=round(monthly_ctc * tpl.get("hra", 0.20), 0),
            conveyance=round(monthly_ctc * tpl.get("conveyance", 0), 0),
            lta=round(monthly_ctc * tpl.get("lta", 0), 0),
            medical_allowance=round(monthly_ctc * tpl.get("medical_allowance", 0), 0),
            employer_pf=round(min(monthly_ctc * tpl.get("basic", 0.40), self.PF_WAGE_CEILING) * self.PF_RATE_EMPLOYER, 0),
            gratuity_provision=round(monthly_ctc * tpl.get("gratuity", 0.01), 0),
            template=template,
            effective_from=effective_from or date.today(),
        )

        # Special allowance is the balancing figure
        fixed_components = (
            structure.basic
            + structure.da
            + structure.hra
            + structure.conveyance
            + structure.lta
            + structure.medical_allowance
            + structure.employer_pf
            + structure.gratuity_provision
        )
        structure.special_allowance = round(monthly_ctc - fixed_components, 0)

        db.session.add(structure)
        db.session.commit()
        return structure

    def process_payroll(self, employee: Employee, month: int, year: int) -> Payslip:
        """Run payroll for a single employee for a given month."""
        structure = employee.salary_structure
        if not structure:
            raise ValueError(f"No salary structure for employee {employee.employee_code}")

        attendance = Attendance.query.filter_by(
            employee_id=employee.id, month=month, year=year
        ).first()

        if not attendance:
            raise ValueError(f"No attendance record for {employee.employee_code} {month}/{year}")

        # 1. Earnings
        earnings = self._calculate_earnings(structure, attendance)

        # 2. Deductions
        deductions = self._calculate_deductions(employee, earnings, month, year)

        # 3. Employer contributions
        employer = self._calculate_employer_contributions(employee, earnings)

        # 4. Net pay
        net_pay = round(earnings["total"] - deductions["total"], 0)

        payslip = Payslip(
            employee_id=employee.id,
            month=month,
            year=year,
            working_days=attendance.total_days,
            present_days=attendance.present_days,
            lop_days=attendance.lop_days,
            basic=earnings["basic"],
            da=earnings["da"],
            hra=earnings["hra"],
            conveyance=earnings["conveyance"],
            lta=earnings["lta"],
            special_allowance=earnings["special_allowance"],
            medical_allowance=earnings["medical_allowance"],
            performance_bonus=earnings["performance_bonus"],
            arrears=earnings["arrears"],
            reimbursements=earnings["reimbursements"],
            gross_earnings=earnings["total"],
            pf_employee=deductions["pf_employee"],
            esic_employee=deductions["esic_employee"],
            professional_tax=deductions["professional_tax"],
            income_tax=deductions["income_tax"],
            loan_emi=deductions["loan_emi"],
            other_deductions=deductions["other_deductions"],
            total_deductions=deductions["total"],
            net_pay=net_pay,
            employer_pf=employer["employer_pf"],
            employer_esic=employer["employer_esic"],
            status="DRAFT",
        )

        db.session.add(payslip)
        db.session.commit()
        return payslip

    def run_org_payroll(self, org_id: str, month: int, year: int) -> dict:
        """Run payroll for all active employees in an organization."""
        employees = Employee.query.filter_by(org_id=org_id, status="ACTIVE").all()

        results = {"successful": [], "failed": []}
        for emp in employees:
            try:
                payslip = self.process_payroll(emp, month, year)
                results["successful"].append({
                    "employee_code": emp.employee_code,
                    "name": emp.full_name,
                    "net_pay": payslip.net_pay,
                })
            except Exception as e:
                results["failed"].append({
                    "employee_code": emp.employee_code,
                    "name": emp.full_name,
                    "error": str(e),
                })

        return results

    def _calculate_earnings(self, structure: SalaryStructure, attendance: Attendance) -> dict:
        """Calculate all earnings with LOP adjustment."""
        if attendance.lop_days > 0:
            payable_factor = attendance.present_days / attendance.total_days
        else:
            payable_factor = 1.0

        earnings = {
            "basic": round(structure.basic * payable_factor, 0),
            "da": round(structure.da * payable_factor, 0),
            "hra": round(structure.hra * payable_factor, 0),
            "conveyance": round(structure.conveyance * payable_factor, 0),
            "lta": round(structure.lta * payable_factor, 0),
            "special_allowance": round(structure.special_allowance * payable_factor, 0),
            "medical_allowance": round(structure.medical_allowance * payable_factor, 0),
            "performance_bonus": round(structure.performance_bonus or 0, 0),
            "arrears": 0,
            "reimbursements": 0,
        }
        earnings["total"] = sum(earnings.values())
        return earnings

    def _calculate_deductions(
        self, employee: Employee, earnings: dict, month: int, year: int
    ) -> dict:
        """Calculate all statutory and other deductions."""
        deductions = {
            "pf_employee": self._calc_pf(employee, earnings),
            "esic_employee": self._calc_esic(employee, earnings),
            "professional_tax": self._calc_pt(employee, earnings, month),
            "income_tax": self._calc_tds(employee, earnings, month, year),
            "loan_emi": self._get_loan_emi(employee),
            "other_deductions": 0,
        }
        deductions["total"] = sum(deductions.values())
        return deductions

    def _calc_pf(self, employee: Employee, earnings: dict) -> float:
        """Employee PF = 12% of (Basic + DA), capped at Rs. 15,000."""
        if not employee.pf_applicable:
            return 0
        pf_wage = min(earnings["basic"] + earnings["da"], self.PF_WAGE_CEILING)
        return round(pf_wage * self.PF_RATE_EMPLOYEE, 0)

    def _calc_esic(self, employee: Employee, earnings: dict) -> float:
        """Employee ESI = 0.75% of gross (if gross <= Rs. 21,000)."""
        if not employee.esic_applicable:
            return 0
        if earnings["total"] > self.ESI_WAGE_CEILING:
            return 0
        return round(earnings["total"] * self.ESI_RATE_EMPLOYEE, 0)

    def _calc_pt(self, employee: Employee, earnings: dict, month: int) -> float:
        """Professional Tax based on work location state."""
        if not employee.pt_applicable:
            return 0

        state = employee.work_location or "Maharashtra"
        gross = earnings["total"]
        slabs = PT_SLABS.get(state, PT_SLABS["Maharashtra"])

        for min_amt, max_amt, pt in slabs:
            if min_amt <= gross <= max_amt:
                # Maharashtra February adjustment
                if state == "Maharashtra" and month == 2 and gross > 10000:
                    return 300
                return pt
        return 0

    def _calc_tds(
        self, employee: Employee, earnings: dict, month: int, year: int
    ) -> float:
        """
        Monthly TDS calculation:
        1. Project annual income
        2. Apply regime-specific deductions
        3. Calculate annual tax
        4. Divide by remaining months, adjust for YTD TDS
        """
        from app.services.tax.calculator import (
            NEW_REGIME_SLABS,
            OLD_REGIME_SLABS,
            CESS_RATE,
            STANDARD_DEDUCTION,
            REBATE_87A_LIMIT_NEW,
            REBATE_87A_MAX_NEW,
            TaxCalculator,
        )

        monthly_gross = earnings["total"]

        # Calculate remaining months in FY
        if month >= 4:
            remaining = 12 - (month - 4)
            months_elapsed = month - 4
        else:
            remaining = 4 - month
            months_elapsed = month + 8

        remaining = max(remaining, 1)

        # Get YTD TDS already deducted
        fy_start_year = year if month >= 4 else year - 1
        ytd_tds = (
            db.session.query(db.func.coalesce(db.func.sum(Payslip.income_tax), 0))
            .filter(
                Payslip.employee_id == employee.id,
                Payslip.year >= fy_start_year,
                Payslip.status != "CANCELLED",
            )
            .scalar()
        ) or 0

        # Project annual income
        projected_annual = monthly_gross * 12
        annual_after_std_ded = projected_annual - STANDARD_DEDUCTION

        # Choose regime
        calc = TaxCalculator()
        if employee.tax_regime == "OLD":
            slabs = OLD_REGIME_SLABS
        else:
            slabs = NEW_REGIME_SLABS

        annual_tax = calc._compute_slab_tax(max(annual_after_std_ded, 0), slabs)

        # Apply rebate for new regime
        if employee.tax_regime == "NEW" and annual_after_std_ded <= REBATE_87A_LIMIT_NEW:
            annual_tax = max(annual_tax - REBATE_87A_MAX_NEW, 0)

        annual_tax_with_cess = annual_tax + round(annual_tax * CESS_RATE, 0)

        monthly_tds = max(0, (annual_tax_with_cess - ytd_tds) / remaining)
        return round(monthly_tds, 0)

    def _get_loan_emi(self, employee: Employee) -> float:
        """Get active loan EMI for the month."""
        active_loans = EmployeeLoan.query.filter_by(
            employee_id=employee.id, status="ACTIVE"
        ).all()
        return sum(loan.emi_amount for loan in active_loans)

    def _calculate_employer_contributions(self, employee: Employee, earnings: dict) -> dict:
        """Employer PF, ESI."""
        contrib = {"employer_pf": 0, "employer_esic": 0}

        if employee.pf_applicable:
            pf_wage = min(earnings["basic"] + earnings["da"], self.PF_WAGE_CEILING)
            contrib["employer_pf"] = round(pf_wage * self.PF_RATE_EMPLOYER, 0)

        if employee.esic_applicable and earnings["total"] <= self.ESI_WAGE_CEILING:
            contrib["employer_esic"] = round(earnings["total"] * self.ESI_RATE_EMPLOYER, 0)

        return contrib
