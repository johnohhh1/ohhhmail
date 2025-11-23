"""
ChiliHead OpsManager v2.1 - Vision Agent
OCR and image processing for attachments
Model: openai:gpt-4o (with vision support)
Fallback: ollama:llama3.2-vision:11b (if GPU available)
"""

import base64
import mimetypes
from typing import Dict, Any, List, Optional
from loguru import logger

from shared.models import (
    AgentType, VisionInput, VisionOutput,
    EmailAttachment
)
from agents.base.agent_contract import BaseAgent
from agents.vision.extractors import InvoiceExtractor, ReceiptExtractor


class VisionAgent(BaseAgent):
    """
    Vision-enabled agent for processing email attachments

    Responsibilities:
    - OCR text extraction from images and PDFs
    - Invoice data extraction (vendor, amount, due date, line items)
    - Receipt parsing
    - Image analysis and description
    - Document classification
    """

    def __init__(self, config):
        """Initialize vision agent"""
        super().__init__(config, AgentType.VISION)
        self.invoice_extractor = InvoiceExtractor()
        self.receipt_extractor = ReceiptExtractor()

    async def process(self, input_data: VisionInput) -> VisionOutput:
        """
        Process email attachments with vision analysis

        Args:
            input_data: VisionInput with attachments list

        Returns:
            VisionOutput with extracted data
        """
        # Create checkpoint at start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="vision_start",
                data={
                    "email_id": input_data.email_id,
                    "attachment_count": len(input_data.attachments)
                }
            )

        # Filter processable attachments
        processable = self._filter_processable_attachments(input_data.attachments)

        logger.info(f"Processing {len(processable)}/{len(input_data.attachments)} attachments")

        # Process each attachment
        extracted_text = {}
        invoice_data = []
        receipt_data = []
        images_processed = 0

        for attachment in processable:
            try:
                result = await self._process_attachment(attachment)

                if result:
                    extracted_text[attachment.filename] = result.get("text", "")

                    # Extract invoice data if detected
                    if result.get("document_type") == "invoice":
                        invoice = self.invoice_extractor.extract(result)
                        if invoice:
                            invoice_data.append(invoice)

                    # Extract receipt data if detected
                    elif result.get("document_type") == "receipt":
                        receipt = self.receipt_extractor.extract(result)
                        if receipt:
                            receipt_data.append(receipt)

                    images_processed += 1

            except Exception as e:
                logger.error(f"Failed to process {attachment.filename}: {e}")
                extracted_text[attachment.filename] = f"ERROR: {str(e)}"

        # Create processing checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="vision_processed",
                data={
                    "images_processed": images_processed,
                    "invoices_found": len(invoice_data),
                    "receipts_found": len(receipt_data)
                }
            )

        # Build findings
        findings = {
            "extracted_text": extracted_text,
            "invoice_data": invoice_data if invoice_data else None,
            "receipt_data": receipt_data if receipt_data else None,
            "images_processed": images_processed
        }

        # Calculate confidence
        confidence = self._calculate_confidence(findings)

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Build output
        output = VisionOutput(
            findings=findings,
            confidence=confidence,
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base execute()
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

        return output

    def _filter_processable_attachments(
        self,
        attachments: List[EmailAttachment]
    ) -> List[EmailAttachment]:
        """
        Filter attachments that can be processed with vision

        Args:
            attachments: List of all attachments

        Returns:
            List of processable attachments
        """
        processable_types = [
            "image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp",
            "application/pdf"
        ]

        processable = [
            att for att in attachments
            if att.content_type in processable_types
        ]

        return processable

    async def _process_attachment(
        self,
        attachment: EmailAttachment
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single attachment with vision model

        Args:
            attachment: Attachment to process

        Returns:
            Extracted data dictionary or None
        """
        logger.info(f"Processing attachment: {attachment.filename}")

        # Download attachment content (if URL provided)
        content = await self._download_attachment(attachment)

        if not content:
            logger.warning(f"Could not download: {attachment.filename}")
            return None

        # Encode for vision model
        if attachment.content_type == "application/pdf":
            # For PDF, extract first page as image
            # Note: This requires pdf2image or similar
            logger.warning("PDF processing not fully implemented - using text extraction only")
            return {"text": "PDF content extraction pending", "document_type": "pdf"}

        # Encode image
        base64_image = base64.b64encode(content).decode('utf-8')

        # Prepare vision prompt
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self._get_vision_prompt()
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{attachment.content_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        # Generate analysis
        response = await self._generate_with_llm(
            messages=messages,
            temperature=0.2,  # Low temperature for accurate extraction
            max_tokens=2000
        )

        # Parse response
        try:
            result = self._extract_json_from_response(response.content)
            result["filename"] = attachment.filename
            return result
        except Exception as e:
            logger.error(f"Failed to parse vision response: {e}")
            return {
                "text": response.content,
                "document_type": "unknown",
                "filename": attachment.filename
            }

    async def _download_attachment(self, attachment: EmailAttachment) -> Optional[bytes]:
        """
        Download attachment content from URL

        Args:
            attachment: Attachment with URL

        Returns:
            Attachment bytes or None
        """
        if not attachment.url:
            logger.warning(f"No URL for attachment: {attachment.filename}")
            return None

        # TODO: Implement actual download logic
        # For now, return None to indicate not implemented
        logger.warning("Attachment download not implemented - requires integration with email storage")
        return None

    def _get_vision_prompt(self) -> str:
        """
        Get vision analysis prompt

        Returns:
            Prompt string
        """
        return """Analyze this image and extract all text and structured data.

Identify the document type (invoice, receipt, schedule, menu, other) and extract relevant information.

For invoices, extract:
- Vendor name
- Invoice number
- Date
- Due date
- Total amount
- Line items (description, quantity, price)

For receipts, extract:
- Merchant name
- Date/time
- Items purchased
- Total amount

For schedules, extract:
- Dates and times
- Events or shifts
- People mentioned

Return your analysis as JSON:
{
  "document_type": "invoice|receipt|schedule|menu|other",
  "text": "full extracted text",
  "structured_data": {
    // document-specific fields
  },
  "confidence": 0.0-1.0
}"""

    def _calculate_confidence(self, findings: Dict[str, Any]) -> float:
        """
        Calculate overall confidence in vision extraction

        Args:
            findings: Vision findings

        Returns:
            Confidence score 0.0-1.0
        """
        images_processed = findings.get("images_processed", 0)

        if images_processed == 0:
            return 0.0

        # Base confidence on successful extractions
        has_invoices = bool(findings.get("invoice_data"))
        has_receipts = bool(findings.get("receipt_data"))
        has_text = bool(findings.get("extracted_text"))

        confidence = 0.5  # Base confidence

        if has_invoices or has_receipts:
            confidence += 0.3  # Structured data extracted

        if has_text:
            confidence += 0.2  # Text extracted

        return min(1.0, confidence)

    def _determine_next_actions(self, findings: Dict[str, Any]) -> List[str]:
        """
        Determine next processing steps

        Args:
            findings: Vision findings

        Returns:
            List of next actions
        """
        actions = []

        # If invoices found, create tasks for payment processing
        if findings.get("invoice_data"):
            actions.append("create_invoice_tasks")

        # If receipts found, log expenses
        if findings.get("receipt_data"):
            actions.append("log_expenses")

        return actions
