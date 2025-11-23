"""
ChiliHead OpsManager v2.1 - Deadline Scanner Agent
Extracts dates, deadlines, and recurring events from email content
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import re

from agents.base import BaseAgent
from shared.models import (
    AgentType,
    DeadlineInput,
    DeadlineOutput,
    AgentInput,
    AgentOutput
)
from shared.llm_config import LLMConfig


class DeadlineAgent(BaseAgent):
    """
    Deadline Scanner Agent - Temporal information extraction

    Responsibilities:
    - Extract specific dates and deadlines
    - Identify recurring events
    - Parse relative time references
    - Handle timezone information
    - Detect urgency indicators
    """

    DEADLINE_SYSTEM_PROMPT = """You are an expert at extracting temporal information from restaurant operations emails.

Your task is to identify ALL dates, deadlines, and time-sensitive information.

Extract:
1. SPECIFIC DATES/TIMES
   - Explicit dates (e.g., "March 15", "3/15/2024", "next Tuesday")
   - Delivery times (e.g., "delivery by 2pm Friday")
   - Payment deadlines (e.g., "due on the 30th", "net 30")
   - Appointment times (e.g., "meeting at 10am")

2. RECURRING EVENTS
   - Weekly deliveries (e.g., "every Tuesday", "weekly on Mondays")
   - Monthly obligations (e.g., "monthly on the 1st")
   - Regular schedules (e.g., "daily at 6am")

3. RELATIVE REFERENCES
   - Soon (e.g., "ASAP", "urgent", "today", "tomorrow")
   - Vague timeframes (e.g., "end of week", "next month", "Q1")

4. TIME ZONES
   - Explicit (e.g., "3pm EST", "10am PST")
   - Implied from context

Respond with valid JSON:
{
  "deadlines": [
    {
      "text": "<original deadline text>",
      "parsed_date": "<ISO 8601 date if parseable>",
      "deadline_type": "payment|delivery|appointment|submission|other",
      "urgency": "critical|high|medium|low",
      "confidence": <0.0-1.0>
    }
  ],
  "recurring_events": [
    {
      "description": "<event description>",
      "frequency": "daily|weekly|monthly|quarterly|yearly",
      "day_of_week": "<day name if weekly>",
      "day_of_month": <number if monthly>,
      "time_of_day": "<time if specified>"
    }
  ],
  "parsed_dates": [
    {
      "text": "<original date reference>",
      "iso_date": "<ISO 8601 date>",
      "confidence": <0.0-1.0>
    }
  ],
  "timezone": "<detected timezone or null>"
}"""

    def __init__(self, config: LLMConfig):
        """
        Initialize Deadline Scanner Agent

        Args:
            config: LLM configuration
        """
        super().__init__(config, AgentType.DEADLINE)

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process email body for deadline extraction

        Args:
            input_data: DeadlineInput with email body

        Returns:
            DeadlineOutput with extracted temporal information
        """
        if not isinstance(input_data, DeadlineInput):
            raise ValueError("Input must be DeadlineInput")

        logger.info("Scanning for deadlines and temporal information")

        # Create checkpoint for deadline scan start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="deadline_scan_start",
                data={"body_length": len(input_data.body)}
            )

        # First pass: Use dateparser for quick extraction
        quick_dates = await self._quick_date_extraction(input_data.body)

        # Second pass: Use LLM for comprehensive analysis
        llm_analysis = await self._llm_deadline_extraction(input_data.body)

        # Merge results
        findings = self._merge_deadline_findings(quick_dates, llm_analysis)

        # Calculate confidence
        confidence = self._calculate_confidence(findings)

        # Create checkpoint for deadline scan completion
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="deadline_scan_complete",
                data=findings
            )

        logger.success(
            f"Deadline scan complete: {len(findings['deadlines'])} deadlines, "
            f"{len(findings['recurring_events'])} recurring events"
        )

        return DeadlineOutput(
            agent_type=AgentType.DEADLINE,
            findings=findings,
            confidence=confidence,
            next_actions=["context_agent"],
            execution_time_ms=0,
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

    async def _quick_date_extraction(self, text: str) -> Dict[str, Any]:
        """
        Quick date extraction using dateparser library

        Args:
            text: Email body text

        Returns:
            Dictionary with extracted dates
        """
        import dateparser
        from dateutil import parser as dateutil_parser

        dates = []

        # Common date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY, MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_text = match.group()
                try:
                    # Try dateparser first
                    parsed = dateparser.parse(
                        date_text,
                        settings={
                            'PREFER_DATES_FROM': 'future',
                            'RELATIVE_BASE': datetime.now()
                        }
                    )

                    if parsed:
                        dates.append({
                            "text": date_text,
                            "iso_date": parsed.isoformat(),
                            "confidence": 0.9
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse date '{date_text}': {e}")

        # Relative date keywords
        relative_patterns = {
            r'\btoday\b': datetime.now(),
            r'\btomorrow\b': datetime.now() + timedelta(days=1),
            r'\bnext week\b': datetime.now() + timedelta(weeks=1),
            r'\bnext month\b': datetime.now() + timedelta(days=30),
            r'\bend of week\b': datetime.now() + timedelta(days=(4 - datetime.now().weekday())),
            r'\bend of month\b': datetime.now().replace(day=28) + timedelta(days=4),
        }

        for pattern, date_value in relative_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                dates.append({
                    "text": pattern.strip('\\b'),
                    "iso_date": date_value.isoformat(),
                    "confidence": 0.7
                })

        return {"parsed_dates": dates}

    async def _llm_deadline_extraction(self, text: str) -> Dict[str, Any]:
        """
        Use LLM for comprehensive deadline extraction

        Args:
            text: Email body text

        Returns:
            Dictionary with extracted deadlines and events
        """
        # Limit text size for LLM
        text_sample = text[:3000]

        messages = [
            {
                "role": "user",
                "content": f"""Analyze this email and extract ALL temporal information:

{text_sample}

Provide complete analysis as JSON."""
            }
        ]

        # Generate analysis
        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=self.DEADLINE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1500
        )

        # Parse response
        try:
            return self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse LLM deadline response: {e}")
            return {
                "deadlines": [],
                "recurring_events": [],
                "parsed_dates": [],
                "timezone": None
            }

    def _merge_deadline_findings(
        self,
        quick_dates: Dict[str, Any],
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge quick extraction and LLM analysis results

        Args:
            quick_dates: Results from quick date extraction
            llm_analysis: Results from LLM analysis

        Returns:
            Merged findings dictionary
        """
        # Start with LLM analysis as base
        merged = {
            "deadlines": llm_analysis.get("deadlines", []),
            "recurring_events": llm_analysis.get("recurring_events", []),
            "parsed_dates": llm_analysis.get("parsed_dates", []),
            "timezone": llm_analysis.get("timezone")
        }

        # Add quick dates that aren't already in LLM results
        llm_date_texts = {d.get("text", "").lower() for d in merged["parsed_dates"]}

        for quick_date in quick_dates.get("parsed_dates", []):
            if quick_date["text"].lower() not in llm_date_texts:
                merged["parsed_dates"].append(quick_date)

        # Sort dates chronologically
        merged["parsed_dates"] = sorted(
            merged["parsed_dates"],
            key=lambda x: x.get("iso_date", "9999-99-99")
        )

        # Sort deadlines by urgency
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        merged["deadlines"] = sorted(
            merged["deadlines"],
            key=lambda x: urgency_order.get(x.get("urgency", "low"), 3)
        )

        return merged

    def _calculate_confidence(self, findings: Dict[str, Any]) -> float:
        """
        Calculate overall confidence in deadline extraction

        Args:
            findings: Merged findings

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence

        # Boost for finding deadlines
        if findings["deadlines"]:
            confidence += 0.2

        # Boost for specific dates
        if findings["parsed_dates"]:
            confidence += 0.15

        # Boost for recurring events
        if findings["recurring_events"]:
            confidence += 0.1

        # Average confidence from individual findings
        deadline_confidences = [d.get("confidence", 0.5) for d in findings["deadlines"]]
        date_confidences = [d.get("confidence", 0.5) for d in findings["parsed_dates"]]

        all_confidences = deadline_confidences + date_confidences
        if all_confidences:
            avg_confidence = sum(all_confidences) / len(all_confidences)
            confidence = (confidence + avg_confidence) / 2

        return min(1.0, confidence)
