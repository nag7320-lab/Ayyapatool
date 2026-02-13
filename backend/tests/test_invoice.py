"""Tests for the invoice module."""

import pytest

from app.services.invoice.gst_utils import GSTValidator, HSN_CODES


class TestGSTINValidation:
    def test_valid_gstin(self):
        assert GSTValidator.is_valid_gstin("29AABCT1332L1ZS") is True
        assert GSTValidator.is_valid_gstin("36AAACT4158E1ZG") is True

    def test_invalid_gstin(self):
        assert GSTValidator.is_valid_gstin("INVALID") is False
        assert GSTValidator.is_valid_gstin("") is False
        assert GSTValidator.is_valid_gstin("12345678901234") is False

    def test_state_extraction(self):
        assert GSTValidator.extract_state_code("29AABCT1332L1ZS") == "29"
        assert GSTValidator.extract_state_code("36AAACT4158E1ZG") == "36"

    def test_interstate_detection(self):
        # Same state
        assert GSTValidator.is_interstate("29AABCT1332L1ZS", "29XXXXX0000X1Z5") is False
        # Different states
        assert GSTValidator.is_interstate("29AABCT1332L1ZS", "36AAACT4158E1ZG") is True


class TestHSNCodes:
    def test_software_services(self):
        assert HSN_CODES["998313"]["gst_rate"] == 18

    def test_suggest_rate(self):
        assert GSTValidator.suggest_gst_rate("998313") == 18
        assert GSTValidator.suggest_gst_rate("000000") == 18  # Default

    def test_education_exempt(self):
        assert HSN_CODES["9992"]["gst_rate"] == 0
