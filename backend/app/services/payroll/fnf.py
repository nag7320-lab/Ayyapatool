"""Full & Final settlement calculator."""

import logging
from datetime import date, datetime
from typing import Optional

from app import db
from app.models.payroll import Employee, EmployeeLoan, FnFSettlement, SalaryStructure

logger = logging.getLogger(__name__)


class FnFCalculator:
    """Calculate Full & Final settlement for exiting employees."""

    def calculate(self, employee: Employee, last_working_day: date) -> FnFSettlement:
        """
        Full & Final settlement components:
        1. Final month salary (pro-rata)
        2. Leave encashment
        3. Gratuity (if eligible - 5+ years)
        4. Notice pay recovery (if applicable)
        5. Loan/advance recovery
        """
        structure = employee.salary_structure
        if not structure:
            raise ValueError("No salary structure found for employee")

        # 1. Final month pro-rata salary
        month_start = date(last_working_day.year, last_working_day.month, 1)
        if last_working_day.month == 12:
            next_month = date(last_working_day.year + 1, 1, 1)
        else:
            next_month = date(last_working_day.year, last_working_day.month + 1, 1)
        total_days_in_month = (next_month - month_start).days
        days_worked = (last_working_day - month_start).days + 1

        monthly_gross = (
            structure.basic
            + structure.da
            + structure.hra
            + structure.conveyance
            + structure.lta
            + structure.special_allowance
            + structure.medical_allowance
        )
        final_salary = round((monthly_gross / total_days_in_month) * days_worked, 0)

        # 2. Leave encashment
        leave_balance = self._get_leave_balance(employee)
        daily_rate = structure.basic / 30
        leave_encashment_gross = round(leave_balance * daily_rate, 0)

        # Exemption u/s 10(10AA) - max Rs. 3 lakhs
        leave_encashment_exempt = min(
            leave_encashment_gross,
            300000,
            round(structure.basic * 10, 0),  # 10 months basic
        )
        leave_encashment_taxable = max(leave_encashment_gross - leave_encashment_exempt, 0)

        # 3. Gratuity (eligible after 5 years)
        years_of_service = (last_working_day - employee.date_of_joining).days / 365.25

        if years_of_service >= 5:
            gratuity_gross = round((structure.basic * 15 * years_of_service) / 26, 0)
            gratuity_gross = min(gratuity_gross, 2000000)  # Cap at Rs. 20 lakhs
            gratuity_exempt = gratuity_gross
            gratuity_taxable = 0
        else:
            gratuity_gross = 0
            gratuity_exempt = 0
            gratuity_taxable = 0

        # 4. Notice pay recovery
        notice_period_days = employee.notice_period_days or 30
        notice_served = 0
        notice_pay_recovery = 0

        if employee.resignation_date:
            notice_served = max((last_working_day - employee.resignation_date).days, 0)
            notice_short = max(notice_period_days - notice_served, 0)
            notice_pay_recovery = round((monthly_gross / 30) * notice_short, 0)

        # 5. Pending loan recovery
        pending_loans = (
            db.session.query(db.func.coalesce(db.func.sum(EmployeeLoan.outstanding_amount), 0))
            .filter(EmployeeLoan.employee_id == employee.id, EmployeeLoan.status == "ACTIVE")
            .scalar()
        ) or 0

        # Totals
        gross_settlement = final_salary + leave_encashment_gross + gratuity_gross
        total_deductions = notice_pay_recovery + pending_loans
        net_settlement = gross_settlement - total_deductions

        fnf = FnFSettlement(
            employee_id=employee.id,
            exit_date=last_working_day,
            final_salary=final_salary,
            leave_balance=leave_balance,
            leave_encashment_gross=leave_encashment_gross,
            leave_encashment_exempt=leave_encashment_exempt,
            leave_encashment_taxable=leave_encashment_taxable,
            years_of_service=round(years_of_service, 2),
            gratuity_gross=gratuity_gross,
            gratuity_exempt=gratuity_exempt,
            gratuity_taxable=gratuity_taxable,
            notice_period_days=notice_period_days,
            notice_served_days=notice_served,
            notice_pay_recovery=notice_pay_recovery,
            pending_loans=pending_loans,
            gross_settlement=gross_settlement,
            total_deductions=total_deductions,
            net_settlement=net_settlement,
            status="PENDING",
        )

        db.session.add(fnf)
        db.session.commit()
        return fnf

    @staticmethod
    def _get_leave_balance(employee: Employee) -> float:
        """Get accumulated leave balance (simplified). Override for actual leave system."""
        # Default: 1.5 earned leave per month of service
        if not employee.date_of_joining:
            return 0
        months = (date.today() - employee.date_of_joining).days / 30.44
        max_accumulation = 30  # Max 30 days accumulation
        return min(round(months * 1.5, 1), max_accumulation)
