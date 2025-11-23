"""
ChiliHead OpsManager v2.1 - Vision Agent Data Extractors
Specialized extractors for invoices, receipts, and other documents
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
import re


class InvoiceExtractor:
    """Extract structured data from invoice images"""

    def extract(self, vision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract invoice data from vision analysis result

        Args:
            vision_result: Output from vision model

        Returns:
            Structured invoice data or None
        """
        if vision_result.get("document_type") != "invoice":
            return None

        structured = vision_result.get("structured_data", {})
        text = vision_result.get("text", "")

        # Extract core fields
        invoice_data = {
            "vendor_name": structured.get("vendor_name") or self._extract_vendor(text),
            "invoice_number": structured.get("invoice_number") or self._extract_invoice_number(text),
            "invoice_date": structured.get("date") or self._extract_date(text),
            "due_date": structured.get("due_date") or self._extract_due_date(text),
            "total_amount": structured.get("total_amount") or self._extract_amount(text),
            "currency": structured.get("currency", "USD"),
            "line_items": structured.get("line_items", []),
            "raw_text": text[:500],  # First 500 chars
            "confidence": vision_result.get("confidence", 0.7)
        }

        # Validate required fields
        if not invoice_data["vendor_name"] or not invoice_data["total_amount"]:
            logger.warning("Invoice missing required fields")
            return None

        return invoice_data

    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name from text"""
        # Simple heuristic: first line that looks like a company name
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and not line.startswith('#'):
                return line
        return None

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text"""
        patterns = [
            r'invoice\s*#?\s*:?\s*(\w+)',
            r'inv\s*#?\s*:?\s*(\w+)',
            r'#(\d{4,})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract invoice date from text"""
        patterns = [
            r'date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        patterns = [
            r'due\s*date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'payment\s*due\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        patterns = [
            r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'amount\s*due\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)'
        ]

        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    continue

        # Return largest amount found (likely the total)
        return max(amounts) if amounts else None


class ReceiptExtractor:
    """Extract structured data from receipt images"""

    def extract(self, vision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract receipt data from vision analysis result

        Args:
            vision_result: Output from vision model

        Returns:
            Structured receipt data or None
        """
        if vision_result.get("document_type") != "receipt":
            return None

        structured = vision_result.get("structured_data", {})
        text = vision_result.get("text", "")

        # Extract core fields
        receipt_data = {
            "merchant_name": structured.get("merchant_name") or self._extract_merchant(text),
            "date": structured.get("date") or self._extract_date(text),
            "time": structured.get("time") or self._extract_time(text),
            "total_amount": structured.get("total_amount") or self._extract_total(text),
            "items": structured.get("items", []),
            "payment_method": structured.get("payment_method"),
            "raw_text": text[:500],
            "confidence": vision_result.get("confidence", 0.7)
        }

        # Validate required fields
        if not receipt_data["merchant_name"] or not receipt_data["total_amount"]:
            logger.warning("Receipt missing required fields")
            return None

        return receipt_data

    def _extract_merchant(self, text: str) -> Optional[str]:
        """Extract merchant name from text"""
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if len(line) > 3:
                return line
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text"""
        pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_total(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        patterns = [
            r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'amount\s*:?\s*\$?\s*([\d,]+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue

        return None


class ScheduleExtractor:
    """Extract structured data from schedule/calendar images"""

    def extract(self, vision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract schedule data from vision analysis result

        Args:
            vision_result: Output from vision model

        Returns:
            Structured schedule data or None
        """
        if vision_result.get("document_type") != "schedule":
            return None

        structured = vision_result.get("structured_data", {})

        schedule_data = {
            "events": structured.get("events", []),
            "date_range": structured.get("date_range"),
            "people": structured.get("people", []),
            "confidence": vision_result.get("confidence", 0.7)
        }

        return schedule_data
