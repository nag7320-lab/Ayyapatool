# AYPA TAXAI - Invoice, Tax Calculators & Payroll System

## Part 3: Complete Specifications

**Document Version:** 1.0
**Date:** February 13, 2026

---

## SECTION A: GST INVOICE GENERATOR

### A.1 Invoice Types (6)

| Type | Use Case | Key Fields |
|------|----------|------------|
| Tax Invoice (B2B) | Taxable supplies to registered businesses | Both GSTINs, HSN/SAC, CGST+SGST or IGST |
| Bill of Supply | Exempted/nil-rated supplies | No GST amount shown |
| Export Invoice | Exports under LUT/Bond | Currency, exchange rate, LUT number, shipping bill |
| Debit Note | Post-sale price increase | Reference to original invoice |
| Credit Note | Sales returns, discounts | Reference to original invoice |
| Quotation/Proforma | Pre-sale estimates | Not for GST reporting |

### A.2 Key Features

- **Auto-fill from GST Portal:** Fetch taxpayer details by GSTIN
- **12+ Industry Templates:** Professional Services, IT/Software, Restaurant, Retail, Manufacturing, Construction, Healthcare, Education, Hospitality, E-commerce, Freelancer, Trading
- **HSN/SAC Code Helper:** Auto-suggest GST rates from 1000+ codes
- **Bulk Generation:** Upload Excel, generate multiple invoices as ZIP
- **GSTR-1 Export:** B2B, B2CL, B2CS, CDNR, EXP tables
- **UPI QR Code:** Auto-generated for payment collection
- **PDF Generation:** Professional ReportLab-based PDFs

### A.3 Tax Logic

```
Intra-state (same state):  CGST + SGST (each = GST rate / 2)
Inter-state (different):   IGST (= full GST rate)
```

### A.4 GSTIN Validation
- 15-character format: `[2-digit state][5-char PAN][4-digit entity][1-char check]`
- Regex: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`

---

## SECTION B: TAX CALCULATORS

### B.1 Income Tax Calculator

**Supports FY 2025-26 slabs for both regimes:**

**Old Regime:**
| Slab | Rate |
|------|------|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 - ₹5,00,000 | 5% |
| ₹5,00,001 - ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

**New Regime:**
| Slab | Rate |
|------|------|
| Up to ₹3,00,000 | Nil |
| ₹3,00,001 - ₹6,00,000 | 5% |
| ₹6,00,001 - ₹9,00,000 | 10% |
| ₹9,00,001 - ₹12,00,000 | 15% |
| ₹12,00,001 - ₹15,00,000 | 20% |
| Above ₹15,00,000 | 30% |

### B.2 Features
- HRA Exemption Calculator u/s 10(13A)
- Section 80C/80D/80CCD deductions
- Old vs New regime comparison with recommendation
- Form 16 PDF upload and auto-parsing
- Professional tax computation report (E&Y style)
- Standard deduction: ₹50,000
- Health & Education Cess: 4%
- Rebate u/s 87A

### B.3 Form 16 Parser
- PyPDF2 text extraction
- Regex pattern matching for PAN, TAN, amounts
- Optional LLM-based intelligent parsing via Gemini

---

## SECTION C: PAYROLL SYSTEM

### C.1 Employee Master
- Personal details, identity (PAN, Aadhaar, UAN)
- Employment details (joining, department, designation)
- Statutory flags (PF, ESI, PT)
- Bank details for salary transfer

### C.2 Salary Components

**Earnings:** Basic, DA, HRA, Conveyance, LTA, Special Allowance, Medical, Performance Bonus

**Deductions:** Employee PF, ESI, Professional Tax, TDS, Loan EMI

**Employer Contributions:** Employer PF (12%), Employer ESI (3.25%), Gratuity

### C.3 Statutory Compliance

| Statute | Rate | Ceiling |
|---------|------|---------|
| Employee PF | 12% of Basic+DA | ₹15,000/month |
| Employer PF | 12% (3.67% EPF + 8.33% EPS) | ₹15,000/month |
| Employee ESI | 0.75% of gross | ₹21,000/month |
| Employer ESI | 3.25% of gross | ₹21,000/month |
| Professional Tax | State-wise slabs | ₹200/month typical |

### C.4 Salary Templates
- **IT Startup:** Basic 40%, HRA 20%, Special 27%
- **Manufacturing:** Basic 50%, DA 5%, HRA 15%
- **Services:** Basic 45%, HRA 18%, LTA 2%

### C.5 Payroll Flow
1. Attendance Lock (by 5th)
2. Salary Revisions
3. Tax Declaration Updates
4. Payroll Run (Calculations)
5. Review & Corrections
6. Payroll Approval
7. Payslip Generation
8. Salary Transfer
9. Payroll Lock

### C.6 Full & Final Settlement
- Pro-rata final salary
- Leave encashment (exemption u/s 10(10AA), max ₹3L)
- Gratuity (eligible after 5 years, formula: Basic × 15 × years / 26, max ₹20L)
- Notice pay recovery
- Loan/advance recovery

---

*Implementation: See `backend/app/services/invoice/`, `backend/app/services/tax/`, `backend/app/services/payroll/`*
