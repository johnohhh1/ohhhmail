"""
ChiliHead OpsManager v2.1 - Vision Agent
OCR processing, invoice extraction, and receipt parsing
"""

import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
import io
from loguru import logger

from agents.base import BaseAgent
from shared.models import (
    AgentType,
    VisionInput,
    VisionOutput,
    EmailAttachment,
    AgentInput,
    AgentOutput
)
from shared.llm_config import LLMConfig, LLMProvider


class VisionAgent(BaseAgent):
    """
    Vision Agent - Document and image processing

    Responsibilities:
    - OCR on PDFs and images
    - Invoice data extraction
    - Receipt parsing
    - Table/structured data extraction
    - GPU-accelerated processing (if available)
    """

    VISION_SYSTEM_PROMPT = """You are an expert document analysis AI for restaurant operations.

Your task is to extract structured data from invoices, receipts, and other business documents.

For INVOICES, extract:
- Vendor name and contact
- Invoice number and date
- Due date and payment terms
- Line items (product, quantity, unit price, total)
- Subtotal, tax, total amount
- Account/reference numbers

For RECEIPTS, extract:
- Merchant name
- Transaction date and time
- Items purchased
- Payment method
- Total amount

For OTHER DOCUMENTS, extract:
- Document type
- Key entities (names, dates, amounts)
- Action items or requirements
- Important dates/deadlines

Respond with valid JSON matching this schema:
{
  "document_type": "invoice|receipt|statement|other",
  "vendor_info": {
    "name": "<vendor name>",
    "contact": "<email/phone>",
    "address": "<address if available>"
  },
  "document_number": "<invoice/receipt number>",
  "date": "<document date>",
  "due_date": "<due date if applicable>",
  "line_items": [
    {
      "description": "<item description>",
      "quantity": <number>,
      "unit_price": <price>,
      "total": <total>
    }
  ],
  "amounts": {
    "subtotal": <amount>,
    "tax": <amount>,
    "total": <amount>
  },
  "payment_terms": "<payment terms>",
  "notes": "<any special notes or requirements>"
}"""

    def __init__(self, config: LLMConfig):
        """
        Initialize Vision Agent

        Args:
            config: LLM configuration (should support vision)
        """
        super().__init__(config, AgentType.VISION)

        # Verify vision support
        if config.provider == LLMProvider.OLLAMA:
            if "vision" not in config.model.lower():
                logger.warning(f"Model {config.model} may not support vision")

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process attachments for OCR and extraction

        Args:
            input_data: VisionInput with attachments

        Returns:
            VisionOutput with extracted data
        """
        if not isinstance(input_data, VisionInput):
            raise ValueError("Input must be VisionInput")

        logger.info(f"Processing {len(input_data.attachments)} attachments")

        # Create checkpoint for vision start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="vision_start",
                data={"attachment_count": len(input_data.attachments)}
            )

        extracted_text = {}
        invoice_data = []
        receipt_data = []
        images_processed = 0

        # Process each attachment
        for attachment in input_data.attachments:
            try:
                result = await self._process_attachment(attachment)

                if result:
                    extracted_text[attachment.filename] = result.get("text", "")

                    # Categorize extracted data
                    if result.get("document_type") == "invoice":
                        invoice_data.append(result)
                    elif result.get("document_type") == "receipt":
                        receipt_data.append(result)

                    images_processed += 1

            except Exception as e:
                logger.error(f"Failed to process {attachment.filename}: {e}")
                extracted_text[attachment.filename] = f"ERROR: {str(e)}"

        # Build findings
        findings = {
            "extracted_text": extracted_text,
            "invoice_data": invoice_data if invoice_data else None,
            "receipt_data": receipt_data if receipt_data else None,
            "images_processed": images_processed
        }

        # Calculate confidence
        confidence = min(1.0, images_processed / len(input_data.attachments)) if input_data.attachments else 0.0

        # Create checkpoint for vision completion
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="vision_complete",
                data=findings
            )

        logger.success(f"Vision processing complete: {images_processed}/{len(input_data.attachments)} processed")

        return VisionOutput(
            agent_type=AgentType.VISION,
            findings=findings,
            confidence=confidence,
            next_actions=["context_agent"],
            execution_time_ms=0,
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

    async def _process_attachment(self, attachment: EmailAttachment) -> Optional[Dict[str, Any]]:
        """
        Process a single attachment

        Args:
            attachment: EmailAttachment to process

        Returns:
            Extracted data dictionary or None
        """
        logger.info(f"Processing attachment: {attachment.filename}")

        # Determine file type
        if attachment.content_type.startswith("image/"):
            return await self._process_image(attachment)
        elif attachment.content_type == "application/pdf":
            return await self._process_pdf(attachment)
        else:
            logger.warning(f"Unsupported content type: {attachment.content_type}")
            return None

    async def _process_image(self, attachment: EmailAttachment) -> Optional[Dict[str, Any]]:
        """
        Process image file with vision model

        Args:
            attachment: Image attachment

        Returns:
            Extracted data
        """
        try:
            # Download image if URL provided
            if attachment.url:
                image_data = await self._download_attachment(attachment.url)
            else:
                logger.warning(f"No URL for attachment {attachment.filename}")
                return None

            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Build vision prompt
            if self.config.provider == LLMProvider.OPENAI:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all information from this document and provide as JSON."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{attachment.content_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            else:
                # Ollama vision format
                messages = [
                    {
                        "role": "user",
                        "content": "Extract all information from this document and provide as JSON.",
                        "images": [image_base64]
                    }
                ]

            # Generate analysis
            response = await self._generate_with_llm(
                messages=messages,
                system_prompt=self.VISION_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2000
            )

            # Parse response
            data = self._extract_json_from_response(response.content)
            data["text"] = response.content  # Store raw text too

            return data

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {"text": f"ERROR: {str(e)}", "document_type": "error"}

    async def _process_pdf(self, attachment: EmailAttachment) -> Optional[Dict[str, Any]]:
        """
        Process PDF file (convert to images then process)

        Args:
            attachment: PDF attachment

        Returns:
            Extracted data
        """
        try:
            # Download PDF
            if attachment.url:
                pdf_data = await self._download_attachment(attachment.url)
            else:
                logger.warning(f"No URL for PDF {attachment.filename}")
                return None

            # Convert PDF to images using pdf2image
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(pdf_data, dpi=200)
            logger.info(f"Converted PDF to {len(images)} images")

            # Process first page (or combine multiple pages)
            if images:
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                # Create temporary attachment for image processing
                image_attachment = EmailAttachment(
                    filename=f"{attachment.filename}_page1.png",
                    content_type="image/png",
                    size=len(img_byte_arr.getvalue()),
                    url=None  # Will use data directly
                )

                # Process as image
                return await self._process_image_data(img_byte_arr.getvalue(), image_attachment)

            return None

        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {"text": f"ERROR: {str(e)}", "document_type": "error"}

    async def _process_image_data(self, image_data: bytes, attachment: EmailAttachment) -> Optional[Dict[str, Any]]:
        """
        Process raw image data

        Args:
            image_data: Raw image bytes
            attachment: Attachment metadata

        Returns:
            Extracted data
        """
        # Encode to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Build vision prompt
        if self.config.provider == LLMProvider.OPENAI:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all information from this document and provide as JSON."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{attachment.content_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        else:
            messages = [
                {
                    "role": "user",
                    "content": "Extract all information from this document and provide as JSON.",
                    "images": [image_base64]
                }
            ]

        # Generate analysis
        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=self.VISION_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2000
        )

        # Parse response
        data = self._extract_json_from_response(response.content)
        data["text"] = response.content

        return data

    async def _download_attachment(self, url: str) -> bytes:
        """
        Download attachment from URL

        Args:
            url: Attachment URL

        Returns:
            Attachment data as bytes
        """
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download attachment: HTTP {response.status}")
