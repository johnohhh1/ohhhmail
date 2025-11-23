"""
ChiliHead OpsManager v2.1 - Triage Agent
Categorizes emails, assesses urgency, and determines processing requirements
"""

from typing import Dict, Any
from loguru import logger

from agents.base import BaseAgent
from shared.models import (
    AgentType,
    TriageInput,
    TriageOutput,
    EmailCategory,
    AgentInput,
    AgentOutput
)
from shared.llm_config import LLMConfig


class TriageAgent(BaseAgent):
    """
    Triage Agent - First line email processor

    Responsibilities:
    - Categorize emails (vendor/staff/customer/system)
    - Score urgency (0-100)
    - Detect if Vision Agent is needed
    - Detect if email contains deadlines
    """

    TRIAGE_SYSTEM_PROMPT = """You are an expert email triage assistant for ChiliHead restaurant operations.

Your task is to analyze emails and provide structured categorization and urgency assessment.

Categories:
- vendor: Emails from suppliers, distributors, service providers
- staff: Internal staff communications, scheduling, HR matters
- customer: Customer inquiries, complaints, reservations, feedback
- system: Automated notifications, receipts, confirmations

Urgency Scoring (0-100):
- 90-100: CRITICAL - Immediate safety/health issues, critical outages, urgent vendor deadlines
- 70-89: HIGH - Time-sensitive orders, staff emergencies, important customer complaints
- 40-69: MEDIUM - Regular vendor communications, routine staff matters, general customer inquiries
- 20-39: LOW - Promotional emails, non-urgent notifications
- 0-19: MINIMAL - Spam, marketing, informational only

Vision Required Indicators:
- Email mentions attachments (PDF, images, invoices, receipts)
- References visual content (scan, photo, screenshot)
- Contains invoice/receipt keywords

Deadline Indicators:
- Contains dates (specific dates, due dates, deadlines)
- Time-sensitive language (ASAP, urgent, by EOD, before)
- Event scheduling (delivery times, appointments, reservations)

Respond ONLY with valid JSON matching this schema:
{
  "category": "vendor|staff|customer|system",
  "urgency": <0-100>,
  "type": "<specific type like 'vendor_invoice', 'staff_schedule', etc>",
  "requires_vision": <true|false>,
  "has_deadline": <true|false>,
  "reasoning": "<brief explanation>",
  "key_entities": ["<extracted entities>"]
}"""

    def __init__(self, config: LLMConfig):
        """
        Initialize Triage Agent

        Args:
            config: LLM configuration
        """
        super().__init__(config, AgentType.TRIAGE)

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process email for triage classification

        Args:
            input_data: TriageInput with email subject and body

        Returns:
            TriageOutput with categorization and assessment
        """
        if not isinstance(input_data, TriageInput):
            raise ValueError("Input must be TriageInput")

        logger.info(f"Triaging email: {input_data.subject[:50]}...")

        # Create checkpoint for triage start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="triage_start",
                data={"subject": input_data.subject}
            )

        # Build analysis prompt
        messages = [
            {
                "role": "user",
                "content": f"""Analyze this email and provide triage classification:

Subject: {input_data.subject}

Body:
{input_data.body[:2000]}  # Limit to first 2000 chars

Provide your analysis as JSON."""
            }
        ]

        # Generate triage analysis
        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=self.TRIAGE_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent categorization
            max_tokens=500
        )

        # Parse response
        triage_data = self._extract_json_from_response(response.content)

        # Validate and normalize
        category = self._validate_category(triage_data.get("category"))
        urgency = self._validate_urgency(triage_data.get("urgency", 50))

        # Build findings
        findings = {
            "category": category,
            "urgency": urgency,
            "type": triage_data.get("type", "unknown"),
            "requires_vision": triage_data.get("requires_vision", False),
            "has_deadline": triage_data.get("has_deadline", False),
            "reasoning": triage_data.get("reasoning", ""),
            "key_entities": triage_data.get("key_entities", [])
        }

        # Calculate confidence based on response quality
        confidence = self._calculate_confidence(triage_data, response)

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Create checkpoint for triage completion
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="triage_complete",
                data=findings
            )

        logger.info(
            f"Triage complete: category={category}, urgency={urgency}, "
            f"vision={findings['requires_vision']}, deadline={findings['has_deadline']}"
        )

        return TriageOutput(
            agent_type=AgentType.TRIAGE,
            findings=findings,
            confidence=confidence,
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base class
            model_used=response.model_used,
            ui_tars_checkpoints=self.checkpoints
        )

    def _validate_category(self, category: str) -> str:
        """Validate and normalize email category"""
        try:
            # Try to match to EmailCategory enum
            return EmailCategory(category.lower()).value
        except (ValueError, AttributeError):
            logger.warning(f"Invalid category '{category}', defaulting to 'system'")
            return EmailCategory.SYSTEM.value

    def _validate_urgency(self, urgency: int) -> int:
        """Validate and clamp urgency score"""
        try:
            urgency = int(urgency)
            return max(0, min(100, urgency))
        except (ValueError, TypeError):
            logger.warning(f"Invalid urgency '{urgency}', defaulting to 50")
            return 50

    def _calculate_confidence(self, triage_data: Dict[str, Any], response: Any) -> float:
        """Calculate confidence score based on response quality"""
        confidence = 0.7  # Base confidence

        # Bonus for having reasoning
        if triage_data.get("reasoning"):
            confidence += 0.1

        # Bonus for entity extraction
        if triage_data.get("key_entities") and len(triage_data["key_entities"]) > 0:
            confidence += 0.1

        # Bonus for clear categorization
        if triage_data.get("type") and triage_data["type"] != "unknown":
            confidence += 0.1

        return min(1.0, confidence)

    def _determine_next_actions(self, findings: Dict[str, Any]) -> list:
        """Determine which agents should run next"""
        actions = []

        # Vision agent if attachments detected
        if findings.get("requires_vision"):
            actions.append("vision_agent")

        # Deadline scanner if time-sensitive
        if findings.get("has_deadline"):
            actions.append("deadline_scanner")

        # Task categorizer for actionable emails
        if findings.get("urgency", 0) >= 40:
            actions.append("task_categorizer")

        # Context agent always runs last
        actions.append("context_agent")

        return actions
