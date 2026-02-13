"""Payroll management API endpoints."""

import logging
from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db, limiter
from app.models.payroll import Attendance, Employee, Payslip, SalaryStructure
from app.models.user import OrgMembership

payroll_bp = Blueprint("payroll", __name__)
logger = logging.getLogger(__name__)


def _get_org_membership(user_id, org_id=None):
    if org_id:
        return OrgMembership.query.filter_by(user_id=user_id, org_id=org_id).first()
    return OrgMembership.query.filter_by(user_id=user_id, is_default=True).first()


# --- Employee Management ---

@payroll_bp.route("/employees", methods=["POST"])
@jwt_required()
def create_employee():
    """Add a new employee."""
    user_id = get_jwt_identity()
    data = request.get_json()
    org_id = data.get("org_id")

    membership = _get_org_membership(user_id, org_id)
    if not membership or membership.role not in ("owner", "admin"):
        return jsonify({"error": "Insufficient permissions"}), 403

    employee = Employee(
        org_id=membership.org_id,
        employee_code=data["employee_code"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data.get("email"),
        mobile=data.get("mobile"),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender"),
        date_of_joining=data["date_of_joining"],
        employment_type=data.get("employment_type", "PERMANENT"),
        department=data.get("department"),
        designation=data.get("designation"),
        work_location=data.get("work_location"),
        pan=data.get("pan"),
        uan=data.get("uan"),
        pf_applicable=data.get("pf_applicable", True),
        esic_applicable=data.get("esic_applicable", False),
        pt_applicable=data.get("pt_applicable", True),
        tax_regime=data.get("tax_regime", "NEW"),
        bank_name=data.get("bank_name"),
        bank_account_number=data.get("bank_account_number"),
        ifsc_code=data.get("ifsc_code"),
    )
    db.session.add(employee)
    db.session.commit()

    return jsonify({"id": employee.id, "employee_code": employee.employee_code}), 201


@payroll_bp.route("/employees", methods=["GET"])
@jwt_required()
def list_employees():
    """List all employees in an organization."""
    user_id = get_jwt_identity()
    org_id = request.args.get("org_id")

    membership = _get_org_membership(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    status = request.args.get("status", "ACTIVE")
    employees = Employee.query.filter_by(org_id=membership.org_id, status=status).all()

    return jsonify({
        "employees": [
            {
                "id": e.id,
                "employee_code": e.employee_code,
                "name": e.full_name,
                "email": e.email,
                "department": e.department,
                "designation": e.designation,
                "date_of_joining": e.date_of_joining.isoformat(),
                "status": e.status,
            }
            for e in employees
        ]
    })


# --- Salary Structure ---

@payroll_bp.route("/employees/<employee_id>/salary", methods=["POST"])
@jwt_required()
def set_salary_structure(employee_id):
    """Create/update salary structure from CTC."""
    user_id = get_jwt_identity()
    data = request.get_json()

    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    membership = _get_org_membership(user_id, employee.org_id)
    if not membership or membership.role not in ("owner", "admin"):
        return jsonify({"error": "Insufficient permissions"}), 403

    from app.services.payroll.engine import PayrollEngine

    engine = PayrollEngine()
    structure = engine.create_salary_structure(
        employee_id=employee_id,
        annual_ctc=data["annual_ctc"],
        template=data.get("template", "it_startup"),
        effective_from=date.fromisoformat(data["effective_from"]) if data.get("effective_from") else None,
    )

    return jsonify({
        "annual_ctc": structure.annual_ctc,
        "monthly_ctc": structure.monthly_ctc,
        "basic": structure.basic,
        "hra": structure.hra,
        "special_allowance": structure.special_allowance,
        "employer_pf": structure.employer_pf,
    }), 201


# --- Attendance ---

@payroll_bp.route("/attendance", methods=["POST"])
@jwt_required()
def record_attendance():
    """Record monthly attendance for an employee."""
    user_id = get_jwt_identity()
    data = request.get_json()

    employee = Employee.query.get(data["employee_id"])
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    attendance = Attendance(
        employee_id=data["employee_id"],
        month=data["month"],
        year=data["year"],
        total_days=data["total_days"],
        present_days=data["present_days"],
        lop_days=data.get("lop_days", 0),
        paid_leave=data.get("paid_leave", 0),
        sick_leave=data.get("sick_leave", 0),
        casual_leave=data.get("casual_leave", 0),
        holidays=data.get("holidays", 0),
        weekoffs=data.get("weekoffs", 0),
    )
    db.session.add(attendance)
    db.session.commit()

    return jsonify({"id": attendance.id}), 201


# --- Payroll Processing ---

@payroll_bp.route("/run", methods=["POST"])
@jwt_required()
@limiter.limit("5/minute")
def run_payroll():
    """Run payroll for an organization for a given month."""
    user_id = get_jwt_identity()
    data = request.get_json()
    org_id = data.get("org_id")

    membership = _get_org_membership(user_id, org_id)
    if not membership or membership.role not in ("owner", "admin"):
        return jsonify({"error": "Insufficient permissions"}), 403

    month = data.get("month")
    year = data.get("year")

    if not all([month, year]):
        return jsonify({"error": "month and year required"}), 400

    from app.services.payroll.engine import PayrollEngine

    engine = PayrollEngine()
    results = engine.run_org_payroll(membership.org_id, month, year)

    return jsonify({
        "month": month,
        "year": year,
        "successful": len(results["successful"]),
        "failed": len(results["failed"]),
        "details": results,
    })


@payroll_bp.route("/payslips", methods=["GET"])
@jwt_required()
def list_payslips():
    """List payslips for an organization."""
    user_id = get_jwt_identity()
    org_id = request.args.get("org_id")
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    membership = _get_org_membership(user_id, org_id)
    if not membership:
        return jsonify({"error": "Organization not found"}), 404

    query = (
        Payslip.query.join(Employee)
        .filter(Employee.org_id == membership.org_id)
    )
    if month:
        query = query.filter(Payslip.month == month)
    if year:
        query = query.filter(Payslip.year == year)

    payslips = query.order_by(Payslip.created_at.desc()).all()

    return jsonify({
        "payslips": [
            {
                "id": p.id,
                "employee_code": p.employee.employee_code,
                "employee_name": p.employee.full_name,
                "month": p.month,
                "year": p.year,
                "gross_earnings": p.gross_earnings,
                "total_deductions": p.total_deductions,
                "net_pay": p.net_pay,
                "status": p.status,
            }
            for p in payslips
        ]
    })


# --- Full & Final ---

@payroll_bp.route("/fnf", methods=["POST"])
@jwt_required()
def calculate_fnf():
    """Calculate Full & Final settlement."""
    user_id = get_jwt_identity()
    data = request.get_json()

    employee = Employee.query.get(data["employee_id"])
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    membership = _get_org_membership(user_id, employee.org_id)
    if not membership or membership.role not in ("owner", "admin"):
        return jsonify({"error": "Insufficient permissions"}), 403

    from app.services.payroll.fnf import FnFCalculator

    calculator = FnFCalculator()
    last_working_day = date.fromisoformat(data["last_working_day"])
    fnf = calculator.calculate(employee, last_working_day)

    return jsonify({
        "id": fnf.id,
        "employee": employee.full_name,
        "exit_date": fnf.exit_date.isoformat(),
        "final_salary": fnf.final_salary,
        "leave_encashment": fnf.leave_encashment_gross,
        "gratuity": fnf.gratuity_gross,
        "notice_pay_recovery": fnf.notice_pay_recovery,
        "pending_loans": fnf.pending_loans,
        "gross_settlement": fnf.gross_settlement,
        "total_deductions": fnf.total_deductions,
        "net_settlement": fnf.net_settlement,
        "years_of_service": fnf.years_of_service,
        "status": fnf.status,
    })
