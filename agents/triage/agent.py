"""
ChiliHead OpsManager v2.1 - Triage Agent
Categorizes emails and determines processing requirements
Model: ollama:llama3.2:8b-instruct
"""

import json
from typing import Dict, Any, List
from loguru import logger

from shared.models import (
    AgentType, TriageInput, TriageOutput,
    EmailCategory, RiskLevel
)
from agents.base.agent_contract import BaseAgent
from agents.triage.prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_USER_TEMPLATE


class TriageAgent(BaseAgent):
    """
    Email triage and categorization agent

    Responsibilities:
    - Categorize email (vendor/staff/customer/system)
    - Assess urgency level (0-100)
    - Detect if vision processing needed
    - Identify potential deadlines
    - Determine email type (invoice, schedule, inquiry, etc.)
    """

    def __init__(self, config):
        """Initialize triage agent"""
        super().__init__(config, AgentType.TRIAGE)

    async def process(self, input_data: TriageInput) -> TriageOutput:
        """
        Process email for triage classification

        Args:
            input_data: TriageInput with email subject and body

        Returns:
            TriageOutput with categorization results
        """
        # Create checkpoint at start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="triage_start",
                data={
                    "email_id": input_data.email_id,
                    "subject": input_data.subject[:100]
                }
            )

        # Prepare messages for LLM
        messages = [
            {
                "role": "user",
                "content": TRIAGE_USER_TEMPLATE.format(
                    subject=input_data.subject,
                    body=input_data.body[:2000]  # Limit body to 2000 chars
                )
            }
        ]

        # Generate classification
        logger.info(f"Triaging email: {input_data.subject[:50]}")

        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=TRIAGE_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for consistent categorization
            max_tokens=500
        )

        # Parse response
        try:
            result = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse triage response: {e}")
            # Return default categorization on parse failure
            result = {
                "category": "system",
                "urgency": 50,
                "type": "unknown",
                "requires_vision": False,
                "has_deadline": False,
                "confidence": 0.5
            }

        # Validate and normalize result
        findings = self._normalize_findings(result)

        # Create analysis checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="triage_analysis",
                data=findings
            )

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Build output
        output = TriageOutput(
            findings=findings,
            confidence=findings.get("confidence", 0.8),
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base execute()
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

        return output

    def _normalize_findings(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate triage findings

        Args:
            result: Raw LLM output

        Returns:
            Normalized findings dictionary
        """
        # Validate category
        category = result.get("category", "system").lower()
        valid_categories = ["vendor", "staff", "customer", "system"]
        if category not in valid_categories:
            category = "system"

        # Validate urgency (0-100)
        urgency = result.get("urgency", 50)
        try:
            urgency = int(urgency)
            urgency = max(0, min(100, urgency))
        except (ValueError, TypeError):
            urgency = 50

        # Validate boolean flags
        requires_vision = bool(result.get("requires_vision", False))
        has_deadline = bool(result.get("has_deadline", False))

        # Extract type
        email_type = result.get("type", "general")

        # Extract reasoning
        reasoning = result.get("reasoning", "")

        # Calculate confidence
        confidence = result.get("confidence", 0.8)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.8

        return {
            "category": category,
            "urgency": urgency,
            "type": email_type,
            "requires_vision": requires_vision,
            "has_deadline": has_deadline,
            "reasoning": reasoning,
            "confidence": confidence
        }

    def _determine_next_actions(self, findings: Dict[str, Any]) -> List[str]:
        """
        Determine which agents should process this email next

        Args:
            findings: Normalized triage findings

        Returns:
            List of next agent names to invoke
        """
        actions = []

        # Always run deadline scanner if deadline detected
        if findings.get("has_deadline"):
            actions.append("deadline")

        # Run vision agent if attachments need processing
        if findings.get("requires_vision"):
            actions.append("vision")

        # Always run task categorizer
        actions.append("task")

        # Context agent runs last to synthesize all results
        actions.append("context")

        return actions

    async def batch_process(self, inputs: List[TriageInput]) -> List[TriageOutput]:
        """
        Process multiple emails in batch

        Args:
            inputs: List of triage inputs

        Returns:
            List of triage outputs
        """
        outputs = []

        for input_data in inputs:
            try:
                result = await self.execute(input_data)
                if result.success and result.output:
                    outputs.append(result.output)
                else:
                    logger.error(f"Triage failed for {input_data.email_id}: {result.error}")
            except Exception as e:
                logger.error(f"Exception processing {input_data.email_id}: {e}")

        logger.info(f"Batch processed {len(outputs)}/{len(inputs)} emails")

        return outputs
