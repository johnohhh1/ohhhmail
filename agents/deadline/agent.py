"""
ChiliHead OpsManager v2.1 - Deadline Scanner Agent
Extracts dates, deadlines, and recurring events from email content
Model: ollama:llama3.2:8b-instruct
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from shared.models import AgentType, DeadlineInput, DeadlineOutput
from agents.base.agent_contract import BaseAgent
from agents.deadline.prompts import DEADLINE_SYSTEM_PROMPT, DEADLINE_USER_TEMPLATE


class DeadlineAgent(BaseAgent):
    """
    Deadline detection and date parsing agent

    Responsibilities:
    - Extract explicit dates (12/25/2024, Dec 25, etc.)
    - Parse relative dates (tomorrow, next week, in 3 days)
    - Identify deadlines and due dates
    - Detect recurring events (weekly, monthly, etc.)
    - Normalize dates to ISO format
    """

    def __init__(self, config):
        """Initialize deadline agent"""
        super().__init__(config, AgentType.DEADLINE)

    async def process(self, input_data: DeadlineInput) -> DeadlineOutput:
        """
        Process email body for deadline extraction

        Args:
            input_data: DeadlineInput with email body text

        Returns:
            DeadlineOutput with extracted deadlines and dates
        """
        # Create checkpoint at start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="deadline_start",
                data={"email_id": input_data.email_id}
            )

        # First pass: Extract obvious date patterns with regex
        regex_dates = self._extract_dates_regex(input_data.body)

        # Prepare messages for LLM
        messages = [
            {
                "role": "user",
                "content": DEADLINE_USER_TEMPLATE.format(
                    body=input_data.body[:3000]  # Limit to 3000 chars
                )
            }
        ]

        # Generate deadline analysis
        logger.info(f"Analyzing deadlines for email {input_data.email_id}")

        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=DEADLINE_SYSTEM_PROMPT,
            temperature=0.2,  # Low temperature for consistent date extraction
            max_tokens=800
        )

        # Parse response
        try:
            result = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse deadline response: {e}")
            result = {
                "deadlines": [],
                "recurring_events": [],
                "parsed_dates": []
            }

        # Combine regex and LLM results
        findings = self._merge_date_findings(result, regex_dates)

        # Create analysis checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="deadline_analysis",
                data={
                    "deadlines_found": len(findings["deadlines"]),
                    "recurring_found": len(findings["recurring_events"])
                }
            )

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Calculate confidence
        confidence = self._calculate_confidence(findings)

        # Build output
        output = DeadlineOutput(
            findings=findings,
            confidence=confidence,
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base execute()
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

        return output

    def _extract_dates_regex(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract dates using regex patterns

        Args:
            text: Text to parse

        Returns:
            List of date matches with context
        """
        date_patterns = [
            # MM/DD/YYYY or MM-DD-YYYY
            (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', 'explicit'),
            # Month DD, YYYY
            (r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', 'explicit'),
            # Month DD
            (r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2})\b', 'explicit'),
            # Relative dates
            (r'\b(tomorrow|today|tonight)\b', 'relative'),
            (r'\b(next\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b', 'relative'),
            (r'\b(in\s+\d+\s+(?:days?|weeks?|months?))\b', 'relative'),
        ]

        matches = []
        for pattern, date_type in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append({
                    "raw_text": match.group(1),
                    "type": date_type,
                    "position": match.start(),
                    "context": text[max(0, match.start()-50):match.end()+50]
                })

        return matches

    def _parse_relative_date(self, text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
        """
        Parse relative date expressions into ISO format

        Args:
            text: Relative date text (e.g., "tomorrow", "in 3 days")
            reference_date: Reference date (defaults to now)

        Returns:
            ISO formatted date string or None
        """
        if not reference_date:
            reference_date = datetime.now()

        text = text.lower().strip()

        # Today/tonight
        if text in ["today", "tonight"]:
            return reference_date.date().isoformat()

        # Tomorrow
        if text == "tomorrow":
            return (reference_date + timedelta(days=1)).date().isoformat()

        # Next week
        if text == "next week":
            return (reference_date + timedelta(weeks=1)).date().isoformat()

        # Next month
        if text == "next month":
            return (reference_date + timedelta(days=30)).date().isoformat()

        # In X days/weeks/months
        match = re.match(r'in\s+(\d+)\s+(days?|weeks?|months?)', text)
        if match:
            count = int(match.group(1))
            unit = match.group(2)

            if 'day' in unit:
                return (reference_date + timedelta(days=count)).date().isoformat()
            elif 'week' in unit:
                return (reference_date + timedelta(weeks=count)).date().isoformat()
            elif 'month' in unit:
                return (reference_date + timedelta(days=count*30)).date().isoformat()

        # Next [day of week]
        days_of_week = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        for day_name, day_num in days_of_week.items():
            if day_name in text:
                current_day = reference_date.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week's occurrence
                target_date = reference_date + timedelta(days=days_ahead)
                return target_date.date().isoformat()

        return None

    def _merge_date_findings(
        self,
        llm_result: Dict[str, Any],
        regex_dates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge LLM and regex date findings

        Args:
            llm_result: LLM extraction result
            regex_dates: Regex extracted dates

        Returns:
            Merged findings
        """
        # Start with LLM results
        deadlines = llm_result.get("deadlines", [])
        recurring = llm_result.get("recurring_events", [])
        parsed_dates = llm_result.get("parsed_dates", [])

        # Add regex dates not found by LLM
        llm_date_texts = {d.get("raw_text", "").lower() for d in parsed_dates}

        for regex_date in regex_dates:
            if regex_date["raw_text"].lower() not in llm_date_texts:
                # Try to parse the date
                iso_date = None
                if regex_date["type"] == "relative":
                    iso_date = self._parse_relative_date(regex_date["raw_text"])
                else:
                    # Try to parse explicit date
                    try:
                        parsed = datetime.strptime(regex_date["raw_text"], "%m/%d/%Y")
                        iso_date = parsed.date().isoformat()
                    except ValueError:
                        pass

                parsed_dates.append({
                    "raw_text": regex_date["raw_text"],
                    "iso_date": iso_date,
                    "context": regex_date["context"],
                    "type": regex_date["type"],
                    "source": "regex"
                })

        return {
            "deadlines": deadlines,
            "recurring_events": recurring,
            "parsed_dates": parsed_dates
        }

    def _calculate_confidence(self, findings: Dict[str, Any]) -> float:
        """
        Calculate confidence in deadline extraction

        Args:
            findings: Deadline findings

        Returns:
            Confidence score 0.0-1.0
        """
        deadlines = findings.get("deadlines", [])
        parsed_dates = findings.get("parsed_dates", [])

        if not deadlines and not parsed_dates:
            return 0.0

        # Base confidence
        confidence = 0.6

        # Increase for explicit deadlines with ISO dates
        valid_deadlines = [d for d in deadlines if d.get("date")]
        if valid_deadlines:
            confidence += 0.2

        # Increase for multiple date formats parsed
        if len(parsed_dates) > 1:
            confidence += 0.1

        # Increase for recurring events detected
        if findings.get("recurring_events"):
            confidence += 0.1

        return min(1.0, confidence)

    def _determine_next_actions(self, findings: Dict[str, Any]) -> List[str]:
        """
        Determine next actions based on deadlines found

        Args:
            findings: Deadline findings

        Returns:
            List of next actions
        """
        actions = []

        deadlines = findings.get("deadlines", [])
        recurring = findings.get("recurring_events", [])

        # Create calendar events for deadlines
        if deadlines:
            actions.append("create_calendar_events")

        # Set up recurring tasks
        if recurring:
            actions.append("create_recurring_tasks")

        # Check for urgent deadlines (within 48 hours)
        now = datetime.now()
        for deadline in deadlines:
            if deadline.get("date"):
                try:
                    deadline_date = datetime.fromisoformat(deadline["date"])
                    if (deadline_date - now).days <= 2:
                        actions.append("send_urgent_notification")
                        break
                except (ValueError, TypeError):
                    pass

        return actions
