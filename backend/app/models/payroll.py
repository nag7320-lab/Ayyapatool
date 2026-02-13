"""Payroll system models."""

import uuid
from datetime import datetime

from app import db


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)

    # Personal details
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True)
    mobile = db.Column(db.String(15))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))

    # Identity (should be encrypted at application level)
    pan = db.Column(db.String(10))
    aadhaar_last_4 = db.Column(db.String(4))
    uan = db.Column(db.String(12))
    esic_number = db.Column(db.String(20))

    # Employment
    date_of_joining = db.Column(db.Date, nullable=False)
    date_of_exit = db.Column(db.Date)
    resignation_date = db.Column(db.Date)
    confirmation_date = db.Column(db.Date)
    employment_type = db.Column(db.String(20), default="PERMANENT")
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    reporting_manager_id = db.Column(db.String(36), db.ForeignKey("employees.id"))
    work_location = db.Column(db.String(100))
    cost_center = db.Column(db.String(50))

    # Statutory compliance
    pf_applicable = db.Column(db.Boolean, default=True)
    esic_applicable = db.Column(db.Boolean, default=False)
    pt_applicable = db.Column(db.Boolean, default=True)
    lwf_applicable = db.Column(db.Boolean, default=False)
    tax_regime = db.Column(db.String(10), default="NEW")

    # Bank details
    bank_name = db.Column(db.String(100))
    bank_account_number = db.Column(db.String(20))
    ifsc_code = db.Column(db.String(11))

    # Notice period
    notice_period_days = db.Column(db.Integer, default=30)

    # Status
    status = db.Column(db.String(20), default="ACTIVE")  # ACTIVE, ON_NOTICE, EXITED, SUSPENDED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship("Organization", back_populates="employees")
    salary_structure = db.relationship(
        "SalaryStructure", back_populates="employee", uselist=False
    )
    payslips = db.relationship("Payslip", back_populates="employee", lazy="dynamic")
    attendance_records = db.relationship(
        "Attendance", back_populates="employee", lazy="dynamic"
    )
    loans = db.relationship("EmployeeLoan", back_populates="employee", lazy="dynamic")
    reporting_manager = db.relationship("Employee", remote_side=[id])

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class SalaryStructure(db.Model):
    __tablename__ = "salary_structures"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(
        db.String(36), db.ForeignKey("employees.id"), nullable=False, unique=True
    )

    # CTC
    annual_ctc = db.Column(db.Float, nullable=False)
    monthly_ctc = db.Column(db.Float, nullable=False)

    # Earnings (monthly)
    basic = db.Column(db.Float, default=0)
    da = db.Column(db.Float, default=0)
    hra = db.Column(db.Float, default=0)
    conveyance = db.Column(db.Float, default=0)
    lta = db.Column(db.Float, default=0)
    special_allowance = db.Column(db.Float, default=0)
    medical_allowance = db.Column(db.Float, default=0)
    performance_bonus = db.Column(db.Float, default=0)

    # Employer contributions (monthly)
    employer_pf = db.Column(db.Float, default=0)
    employer_esic = db.Column(db.Float, default=0)
    gratuity_provision = db.Column(db.Float, default=0)

    # Template used
    template = db.Column(db.String(50))

    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = db.relationship("Employee", back_populates="salary_structure")


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(db.String(36), db.ForeignKey("employees.id"), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    total_days = db.Column(db.Integer, nullable=False)
    present_days = db.Column(db.Float, nullable=False)
    lop_days = db.Column(db.Float, default=0)
    paid_leave = db.Column(db.Float, default=0)
    sick_leave = db.Column(db.Float, default=0)
    casual_leave = db.Column(db.Float, default=0)
    holidays = db.Column(db.Integer, default=0)
    weekoffs = db.Column(db.Integer, default=0)

    is_locked = db.Column(db.Boolean, default=False)
    locked_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship("Employee", back_populates="attendance_records")

    __table_args__ = (
        db.UniqueConstraint("employee_id", "month", "year", name="uq_employee_month_year"),
    )


class Payslip(db.Model):
    __tablename__ = "payslips"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(db.String(36), db.ForeignKey("employees.id"), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    # Attendance
    working_days = db.Column(db.Integer)
    present_days = db.Column(db.Float)
    lop_days = db.Column(db.Float, default=0)

    # Earnings
    basic = db.Column(db.Float, default=0)
    da = db.Column(db.Float, default=0)
    hra = db.Column(db.Float, default=0)
    conveyance = db.Column(db.Float, default=0)
    lta = db.Column(db.Float, default=0)
    special_allowance = db.Column(db.Float, default=0)
    medical_allowance = db.Column(db.Float, default=0)
    performance_bonus = db.Column(db.Float, default=0)
    arrears = db.Column(db.Float, default=0)
    reimbursements = db.Column(db.Float, default=0)
    gross_earnings = db.Column(db.Float, default=0)

    # Deductions
    pf_employee = db.Column(db.Float, default=0)
    esic_employee = db.Column(db.Float, default=0)
    professional_tax = db.Column(db.Float, default=0)
    income_tax = db.Column(db.Float, default=0)
    loan_emi = db.Column(db.Float, default=0)
    advance_recovery = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    total_deductions = db.Column(db.Float, default=0)

    # Net pay
    net_pay = db.Column(db.Float, default=0)

    # Employer contributions
    employer_pf = db.Column(db.Float, default=0)
    employer_esic = db.Column(db.Float, default=0)

    # Status
    status = db.Column(db.String(20), default="DRAFT")  # DRAFT, APPROVED, PAID, LOCKED
    approved_by = db.Column(db.String(36))
    approved_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)

    # PDF
    pdf_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = db.relationship("Employee", back_populates="payslips")

    __table_args__ = (
        db.UniqueConstraint("employee_id", "month", "year", name="uq_payslip_employee_month"),
    )


class EmployeeLoan(db.Model):
    __tablename__ = "employee_loans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(db.String(36), db.ForeignKey("employees.id"), nullable=False)

    loan_type = db.Column(db.String(30))  # salary_advance, personal_loan, etc.
    loan_amount = db.Column(db.Float, nullable=False)
    outstanding_amount = db.Column(db.Float, nullable=False)
    emi_amount = db.Column(db.Float, nullable=False)
    tenure_months = db.Column(db.Integer)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)

    status = db.Column(db.String(20), default="ACTIVE")  # ACTIVE, CLOSED, WRITTEN_OFF
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship("Employee", back_populates="loans")


class FnFSettlement(db.Model):
    __tablename__ = "fnf_settlements"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(db.String(36), db.ForeignKey("employees.id"), nullable=False)
    exit_date = db.Column(db.Date, nullable=False)

    # Final salary
    final_salary = db.Column(db.Float, default=0)

    # Leave encashment
    leave_balance = db.Column(db.Float, default=0)
    leave_encashment_gross = db.Column(db.Float, default=0)
    leave_encashment_exempt = db.Column(db.Float, default=0)
    leave_encashment_taxable = db.Column(db.Float, default=0)

    # Gratuity
    years_of_service = db.Column(db.Float, default=0)
    gratuity_gross = db.Column(db.Float, default=0)
    gratuity_exempt = db.Column(db.Float, default=0)
    gratuity_taxable = db.Column(db.Float, default=0)

    # Notice period
    notice_period_days = db.Column(db.Integer, default=30)
    notice_served_days = db.Column(db.Integer, default=0)
    notice_pay_recovery = db.Column(db.Float, default=0)

    # Loans
    pending_loans = db.Column(db.Float, default=0)

    # Totals
    gross_settlement = db.Column(db.Float, default=0)
    total_deductions = db.Column(db.Float, default=0)
    net_settlement = db.Column(db.Float, default=0)

    # Status
    status = db.Column(db.String(20), default="PENDING")  # PENDING, APPROVED, PAID
    approved_by = db.Column(db.String(36))
    approved_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
