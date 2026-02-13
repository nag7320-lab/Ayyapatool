"""Form 16 PDF parser using PyPDF2 and optional LLM extraction."""

import io
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Form16Parser:
    """Extract structured data from Form 16 PDF."""

    def parse(self, pdf_file, llm_client=None) -> dict:
        """
        Extract Form 16 data from PDF.

        Methods:
        1. PyPDF2 text extraction
        2. Regex pattern matching
        3. Optional LLM-based intelligent parsing
        """
        text = self._extract_text(pdf_file)

        if not text.strip():
            raise ValueError("Could not extract text from PDF. The file may be scanned/image-based.")

        # Try regex extraction first
        data = self._regex_extract(text)

        # If LLM available and data is incomplete, use LLM
        if llm_client and not self._is_complete(data):
            llm_data = self._llm_extract(text, llm_client)
            # Merge: prefer LLM data where regex failed
            for key, value in llm_data.items():
                if not data.get(key) and value:
                    data[key] = value

        return data

    @staticmethod
    def _extract_text(pdf_file) -> str:
        """Extract text from PDF using PyPDF2."""
        import PyPDF2

        if isinstance(pdf_file, bytes):
            pdf_file = io.BytesIO(pdf_file)

        reader = PyPDF2.PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts)

    @staticmethod
    def _regex_extract(text: str) -> dict:
        """Extract fields using regex patterns."""
        data = {
            "employee_name": "",
            "employee_pan": "",
            "financial_year": "",
            "employer_name": "",
            "employer_tan": "",
            "gross_salary": 0,
            "allowances_exempt": 0,
            "standard_deduction": 0,
            "professional_tax": 0,
            "income_house_property": 0,
            "income_other_sources": 0,
            "sec_80c": 0,
            "sec_80ccd_1b": 0,
            "sec_80ccd_2": 0,
            "sec_80d": 0,
            "total_deductions": 0,
            "total_income": 0,
            "tax_payable": 0,
            "tds_deducted": 0,
        }

        # PAN pattern
        pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
        if pan_match:
            data["employee_pan"] = pan_match.group()

        # TAN pattern
        tan_match = re.search(r"[A-Z]{4}[0-9]{5}[A-Z]", text)
        if tan_match:
            data["employer_tan"] = tan_match.group()

        # Financial year
        fy_match = re.search(r"(20\d{2})\s*-\s*(20\d{2}|[\d]{2})", text)
        if fy_match:
            data["financial_year"] = f"{fy_match.group(1)}-{fy_match.group(2)}"

        # Amounts: look for patterns like "1,23,456" or "123456.00"
        def find_amount(pattern, text):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "").strip()
                try:
                    return float(amount_str)
                except ValueError:
                    return 0
            return 0

        data["gross_salary"] = find_amount(
            r"gross\s+salary[^\d]*([\d,]+\.?\d*)", text
        )
        data["standard_deduction"] = find_amount(
            r"standard\s+deduction[^\d]*([\d,]+\.?\d*)", text
        )
        data["tds_deducted"] = find_amount(
            r"tax\s+deducted[^\d]*([\d,]+\.?\d*)", text
        )
        data["total_income"] = find_amount(
            r"total\s+income[^\d]*([\d,]+\.?\d*)", text
        )

        return data

    @staticmethod
    def _llm_extract(text: str, llm_client) -> dict:
        """Use LLM to extract structured data from Form 16 text."""
        prompt = f"""Extract the following information from this Form 16 document.
Return ONLY valid JSON with these exact field names:

- employee_name
- employee_pan
- financial_year
- employer_name
- employer_tan
- gross_salary (number)
- allowances_exempt (number)
- standard_deduction (number)
- professional_tax (number)
- income_house_property (number)
- income_other_sources (number)
- sec_80c (number)
- sec_80ccd_1b (number)
- sec_80ccd_2 (number)
- sec_80d (number)
- total_deductions (number)
- total_income (number)
- tax_payable (number)
- tds_deducted (number)

Use 0 for any field not found.

Form 16 Text:
{text[:3000]}"""

        try:
            response = llm_client.generate_content(prompt)
            # Extract JSON from response
            response_text = response.text
            # Find JSON in response
            json_match = re.search(r"\{[^}]+\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"LLM Form 16 extraction failed: {e}")

        return {}

    @staticmethod
    def _is_complete(data: dict) -> bool:
        """Check if extracted data has minimum required fields."""
        required = ["employee_pan", "gross_salary", "tds_deducted"]
        return all(data.get(k) for k in required)
