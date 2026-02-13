"""Invoice and billing models."""

import uuid
from datetime import datetime

from app import db


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # Invoice identification
    invoice_number = db.Column(db.String(50), nullable=False, index=True)
    invoice_type = db.Column(
        db.String(30), nullable=False
    )  # tax_invoice, bill_of_supply, export, debit_note, credit_note, quotation
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)

    # Supplier (auto-filled from org)
    supplier_name = db.Column(db.String(200), nullable=False)
    supplier_gstin = db.Column(db.String(15))
    supplier_address = db.Column(db.Text)
    supplier_state = db.Column(db.String(100))
    supplier_state_code = db.Column(db.String(2))

    # Customer
    customer_name = db.Column(db.String(200), nullable=False)
    customer_gstin = db.Column(db.String(15))
    customer_address = db.Column(db.Text)
    customer_state = db.Column(db.String(100))
    customer_state_code = db.Column(db.String(2))
    customer_email = db.Column(db.String(255))
    customer_phone = db.Column(db.String(15))

    # Place of supply (determines IGST vs CGST+SGST)
    place_of_supply = db.Column(db.String(100), nullable=False)
    is_interstate = db.Column(db.Boolean, default=False)

    # Export-specific fields
    currency = db.Column(db.String(3), default="INR")
    exchange_rate = db.Column(db.Float, default=1.0)
    lut_number = db.Column(db.String(50))
    shipping_bill_no = db.Column(db.String(50))
    shipping_bill_date = db.Column(db.Date)
    port_of_export = db.Column(db.String(100))
    country_of_destination = db.Column(db.String(100))

    # Reference (for debit/credit notes)
    original_invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"))
    reason = db.Column(db.Text)

    # Amounts
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    taxable_value = db.Column(db.Float, default=0.0)
    cgst = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    igst = db.Column(db.Float, default=0.0)
    cess = db.Column(db.Float, default=0.0)
    total_tax = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    amount_in_words = db.Column(db.Text)

    # Template
    template_id = db.Column(db.String(50), default="professional_services")

    # Notes
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)

    # PDF
    pdf_url = db.Column(db.String(500))

    # Status
    status = db.Column(
        db.String(20), default="draft"
    )  # draft, sent, paid, overdue, cancelled

    # GSTR-1 filing
    gstr1_filed = db.Column(db.Boolean, default=False)
    gstr1_period = db.Column(db.String(7))  # YYYY-MM

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship("Organization", back_populates="invoices")
    items = db.relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", lazy="joined"
    )
    original_invoice = db.relationship("Invoice", remote_side=[id])

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"

    def calculate_totals(self):
        """Recalculate invoice totals from line items."""
        self.subtotal = sum(item.amount for item in self.items)
        self.discount_amount = sum(item.discount_amount for item in self.items)
        self.taxable_value = self.subtotal - self.discount_amount

        self.cgst = 0.0
        self.sgst = 0.0
        self.igst = 0.0
        self.cess = 0.0

        for item in self.items:
            if self.is_interstate:
                self.igst += item.igst
            else:
                self.cgst += item.cgst
                self.sgst += item.sgst
            self.cess += item.cess

        self.total_tax = self.cgst + self.sgst + self.igst + self.cess
        self.total_amount = self.taxable_value + self.total_tax


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)

    # Item details
    sr_no = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False)
    hsn_sac = db.Column(db.String(8))
    unit = db.Column(db.String(20), default="NOS")  # NOS, HRS, KGS, MTR, etc.
    quantity = db.Column(db.Float, nullable=False, default=1)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    # Discount
    discount_percent = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    taxable_value = db.Column(db.Float, default=0.0)

    # Tax
    gst_rate = db.Column(db.Float, nullable=False)  # 0, 5, 12, 18, 28
    cgst_rate = db.Column(db.Float, default=0.0)
    cgst = db.Column(db.Float, default=0.0)
    sgst_rate = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    igst_rate = db.Column(db.Float, default=0.0)
    igst = db.Column(db.Float, default=0.0)
    cess_rate = db.Column(db.Float, default=0.0)
    cess = db.Column(db.Float, default=0.0)

    # Total
    total = db.Column(db.Float, default=0.0)

    # Relationship
    invoice = db.relationship("Invoice", back_populates="items")

    def calculate(self, is_interstate: bool):
        """Calculate item totals and taxes."""
        self.amount = round(self.quantity * self.rate, 2)
        self.discount_amount = round(self.amount * self.discount_percent / 100, 2)
        self.taxable_value = round(self.amount - self.discount_amount, 2)

        tax_amount = round(self.taxable_value * self.gst_rate / 100, 2)

        if is_interstate:
            self.igst_rate = self.gst_rate
            self.igst = tax_amount
            self.cgst_rate = 0.0
            self.cgst = 0.0
            self.sgst_rate = 0.0
            self.sgst = 0.0
        else:
            half_rate = self.gst_rate / 2
            half_tax = round(tax_amount / 2, 2)
            self.cgst_rate = half_rate
            self.cgst = half_tax
            self.sgst_rate = half_rate
            self.sgst = tax_amount - half_tax  # Adjust for rounding
            self.igst_rate = 0.0
            self.igst = 0.0

        self.total = round(self.taxable_value + tax_amount + self.cess, 2)


class BankDetail(db.Model):
    __tablename__ = "bank_details"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False)

    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    ifsc_code = db.Column(db.String(11), nullable=False)
    account_holder_name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100))

    upi_id = db.Column(db.String(50))
    upi_qr_enabled = db.Column(db.Boolean, default=True)

    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    organization = db.relationship("Organization", back_populates="bank_details")
