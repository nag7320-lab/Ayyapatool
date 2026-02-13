"""GST validation utilities, HSN/SAC codes, and rate lookups."""

import re

# GST rate options
GST_RATES = [
    {"value": 0, "label": "0% (Exempted)"},
    {"value": 0.25, "label": "0.25% (Gold/Precious stones)"},
    {"value": 3, "label": "3% (Gold ornaments)"},
    {"value": 5, "label": "5% (Essential goods)"},
    {"value": 12, "label": "12% (Standard goods)"},
    {"value": 18, "label": "18% (Standard goods/Services)"},
    {"value": 28, "label": "28% (Luxury goods)"},
]

# Common HSN/SAC codes with suggested GST rates
HSN_CODES = {
    "998311": {"description": "Management consulting services", "gst_rate": 18},
    "998312": {"description": "Management consulting and project management", "gst_rate": 18},
    "998313": {"description": "Software development services", "gst_rate": 18},
    "998314": {"description": "IT consulting services", "gst_rate": 18},
    "998315": {"description": "Cloud and hosting services", "gst_rate": 18},
    "998316": {"description": "IT infrastructure provisioning", "gst_rate": 18},
    "998319": {"description": "Other IT services", "gst_rate": 18},
    "997331": {"description": "Licensing services for software", "gst_rate": 18},
    "9973": {"description": "Professional services", "gst_rate": 18},
    "9971": {"description": "Financial and related services", "gst_rate": 18},
    "9972": {"description": "Real estate services", "gst_rate": 18},
    "9982": {"description": "Legal services", "gst_rate": 18},
    "9983": {"description": "Other professional services", "gst_rate": 18},
    "9984": {"description": "Telecommunications services", "gst_rate": 18},
    "9985": {"description": "Transport services", "gst_rate": 5},
    "9986": {"description": "Support and auxiliary services", "gst_rate": 18},
    "9987": {"description": "Maintenance and repair services", "gst_rate": 18},
    "9988": {"description": "Manufacturing services", "gst_rate": 18},
    "9991": {"description": "Public administration services", "gst_rate": 0},
    "9992": {"description": "Education services", "gst_rate": 0},
    "9993": {"description": "Health care services", "gst_rate": 0},
    "9994": {"description": "Sewage and waste collection", "gst_rate": 12},
    "9995": {"description": "Membership organization services", "gst_rate": 18},
    "9996": {"description": "Recreational and sporting services", "gst_rate": 18},
    "9997": {"description": "Other services", "gst_rate": 18},
}

# State codes
STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
}


class GSTValidator:
    """Validate GST-related data."""

    GSTIN_PATTERN = re.compile(
        r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    )

    @classmethod
    def is_valid_gstin(cls, gstin: str) -> bool:
        """Validate GSTIN format (15 characters)."""
        if not gstin or len(gstin) != 15:
            return False
        return bool(cls.GSTIN_PATTERN.match(gstin.upper()))

    @staticmethod
    def extract_state_code(gstin: str) -> str:
        """Extract 2-digit state code from GSTIN."""
        return gstin[:2] if gstin and len(gstin) >= 2 else ""

    @staticmethod
    def extract_state_name(gstin: str) -> str:
        """Get state name from GSTIN."""
        code = gstin[:2] if gstin and len(gstin) >= 2 else ""
        return STATE_CODES.get(code, "Unknown")

    @staticmethod
    def is_interstate(supplier_gstin: str, customer_gstin: str) -> bool:
        """Determine if supply is interstate (IGST) or intra-state (CGST+SGST)."""
        if not supplier_gstin or not customer_gstin:
            return False
        return supplier_gstin[:2] != customer_gstin[:2]

    @classmethod
    def validate_invoice(cls, invoice) -> list[str]:
        """Validate a tax invoice for GST compliance."""
        errors = []

        if not invoice.invoice_number:
            errors.append("Invoice number is required")

        if not invoice.invoice_date:
            errors.append("Invoice date is required")

        if not invoice.supplier_name:
            errors.append("Supplier name is required")

        if not invoice.customer_name:
            errors.append("Customer name is required")

        if not invoice.place_of_supply:
            errors.append("Place of supply is required")

        # GSTIN validation
        if invoice.supplier_gstin and not cls.is_valid_gstin(invoice.supplier_gstin):
            errors.append("Invalid supplier GSTIN")

        if invoice.customer_gstin and not cls.is_valid_gstin(invoice.customer_gstin):
            errors.append("Invalid customer GSTIN")

        # Tax type validation
        if invoice.supplier_gstin and invoice.customer_gstin:
            is_inter = cls.is_interstate(invoice.supplier_gstin, invoice.customer_gstin)
            if is_inter:
                if invoice.cgst > 0 or invoice.sgst > 0:
                    errors.append("Inter-state supply must have IGST only, not CGST/SGST")
            else:
                if invoice.igst > 0:
                    errors.append("Intra-state supply must have CGST+SGST, not IGST")

        # Items validation
        if not invoice.items:
            errors.append("At least one line item is required")

        for i, item in enumerate(invoice.items, 1):
            if not item.description:
                errors.append(f"Item {i}: Description is required")
            if item.quantity <= 0:
                errors.append(f"Item {i}: Quantity must be positive")
            if item.rate < 0:
                errors.append(f"Item {i}: Rate cannot be negative")

        return errors

    @staticmethod
    def suggest_gst_rate(hsn_code: str) -> int:
        """Auto-suggest GST rate based on HSN/SAC code."""
        if hsn_code in HSN_CODES:
            return HSN_CODES[hsn_code]["gst_rate"]
        # Check prefix matches
        for code, info in HSN_CODES.items():
            if hsn_code.startswith(code[:4]):
                return info["gst_rate"]
        return 18  # Default for services
