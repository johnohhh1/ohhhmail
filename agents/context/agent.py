"""
ChiliHead OpsManager v2.1 - Context Agent
Synthesizes all agent outputs with 30-day historical memory
Model: anthropic:claude-sonnet-4 (NO FALLBACK - CRITICAL)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from shared.models import (
    AgentType, ContextInput, ContextOutput, RiskLevel
)
from agents.base.agent_contract import BaseAgent
from agents.context.memory import ContextMemory
from agents.context.prompts import (
    CONTEXT_SYSTEM_PROMPT,
    CONTEXT_USER_TEMPLATE,
    VENDOR_ANALYSIS_TEMPLATE
)


class ContextAgent(BaseAgent):
    """
    Context synthesis and historical analysis agent - CRITICAL COMPONENT

    Responsibilities:
    - Synthesize outputs from all other agents
    - Retrieve 30-day historical context from Qdrant
    - Analyze vendor reliability patterns
    - Assess operational risks
    - Generate actionable recommendations
    - Provide executive summary

    CRITICAL: This agent MUST use Claude Sonnet 4 - NO FALLBACK ALLOWED
    If model unavailable, fail fast rather than use inferior model
    """

    def __init__(self, config):
        """Initialize context agent"""
        super().__init__(config, AgentType.CONTEXT)

        # Verify no fallback is configured (critical requirement)
        if config.fallback_allowed:
            logger.critical("Context agent configured with fallback - this violates system requirements!")
            raise ValueError("Context agent must have fallback_allowed=False")

        # Initialize memory system
        self.memory = ContextMemory()

        logger.info("Context agent initialized with NO FALLBACK")

    async def process(self, input_data: ContextInput) -> ContextOutput:
        """
        Process all agent outputs and synthesize context

        Args:
            input_data: ContextInput with all agent outputs

        Returns:
            ContextOutput with synthesis and recommendations
        """
        # Create checkpoint at start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="context_start",
                data={"email_id": input_data.email_id}
            )

        # Retrieve historical context from Qdrant
        historical_context = await self._retrieve_historical_context(
            input_data.triage_output,
            input_data.email_id
        )

        # Build comprehensive context document
        context_document = self._build_context_document(
            input_data,
            historical_context
        )

        # Create memory retrieval checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="context_memory_retrieved",
                data={
                    "historical_items": len(historical_context),
                    "context_size": len(context_document)
                }
            )

        # Prepare messages for Claude
        messages = [
            {
                "role": "user",
                "content": CONTEXT_USER_TEMPLATE.format(
                    context_document=context_document
                )
            }
        ]

        # Generate synthesis with Claude Sonnet 4
        logger.info(f"Synthesizing context for email {input_data.email_id}")

        try:
            response = await self._generate_with_llm(
                messages=messages,
                system_prompt=CONTEXT_SYSTEM_PROMPT,
                temperature=0.6,  # Moderate creativity for insights
                max_tokens=2000
            )
        except Exception as e:
            # NO FALLBACK - fail fast if Claude unavailable
            logger.critical(f"Context agent failed - Claude Sonnet 4 unavailable: {e}")
            raise RuntimeError(
                f"Context agent requires Claude Sonnet 4 which is unavailable. "
                f"System cannot proceed without context synthesis. Error: {e}"
            )

        # Parse response
        try:
            result = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse context response: {e}")
            # Even on parse failure, don't use fallback - return error state
            raise RuntimeError(f"Failed to parse context synthesis from Claude: {e}")

        # Build findings
        findings = self._build_findings(result, historical_context)

        # Create synthesis checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="context_synthesized",
                data={
                    "risk_level": findings["risk_assessment"],
                    "recommendations": len(findings["recommendations"])
                }
            )

        # Store this interaction in memory for future context
        await self._store_interaction(input_data, findings)

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Build output
        output = ContextOutput(
            findings=findings,
            confidence=findings.get("confidence", 0.9),
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base execute()
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

        return output

    async def _retrieve_historical_context(
        self,
        triage_output: Dict[str, Any],
        email_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant historical context from Qdrant vector store

        Args:
            triage_output: Triage classification results
            email_id: Current email ID

        Returns:
            List of relevant historical interactions (30-day window)
        """
        category = triage_output.get("category", "system")
        email_type = triage_output.get("type", "general")

        # Build search query
        query = f"{category} {email_type} email"

        try:
            # Retrieve from Qdrant (30-day window)
            results = await self.memory.search_similar(
                query=query,
                limit=10,
                days_back=30
            )

            logger.info(f"Retrieved {len(results)} historical items for context")

            return results

        except Exception as e:
            logger.warning(f"Failed to retrieve historical context: {e}")
            return []

    def _build_context_document(
        self,
        input_data: ContextInput,
        historical_context: List[Dict[str, Any]]
    ) -> str:
        """
        Build comprehensive context document for Claude

        Args:
            input_data: All agent inputs
            historical_context: Historical interactions

        Returns:
            Formatted context document string
        """
        doc_parts = []

        # Triage results
        doc_parts.append("=== EMAIL TRIAGE ===")
        triage = input_data.triage_output
        doc_parts.append(f"Category: {triage.get('category')}")
        doc_parts.append(f"Type: {triage.get('type')}")
        doc_parts.append(f"Urgency: {triage.get('urgency')}/100")
        doc_parts.append(f"Reasoning: {triage.get('reasoning', 'N/A')}")
        doc_parts.append("")

        # Vision results (if available)
        if input_data.vision_output:
            doc_parts.append("=== VISION ANALYSIS ===")
            vision = input_data.vision_output
            if vision.get("invoice_data"):
                doc_parts.append(f"Invoices found: {len(vision['invoice_data'])}")
                for inv in vision["invoice_data"]:
                    doc_parts.append(f"  - {inv.get('vendor_name')}: ${inv.get('total_amount')}")
            if vision.get("receipt_data"):
                doc_parts.append(f"Receipts found: {len(vision['receipt_data'])}")
            doc_parts.append("")

        # Deadline results
        doc_parts.append("=== DEADLINES ===")
        deadline = input_data.deadline_output
        deadlines = deadline.get("deadlines", [])
        if deadlines:
            for dl in deadlines:
                doc_parts.append(f"  - {dl.get('description')}: {dl.get('date')} [{dl.get('urgency')}]")
        else:
            doc_parts.append("No deadlines detected")
        doc_parts.append("")

        # Task results (if available)
        if input_data.task_output:
            doc_parts.append("=== TASKS ===")
            tasks = input_data.task_output.get("tasks", [])
            if tasks:
                for task in tasks:
                    assignee = task.get("assignee", "Unassigned")
                    doc_parts.append(
                        f"  - [{task.get('priority')}] {task.get('description')} "
                        f"({assignee})"
                    )
            else:
                doc_parts.append("No tasks identified")
            doc_parts.append("")

        # Historical context
        if historical_context:
            doc_parts.append("=== HISTORICAL CONTEXT (30-day window) ===")
            doc_parts.append(f"Found {len(historical_context)} similar past interactions:")
            for i, item in enumerate(historical_context[:5], 1):  # Top 5
                doc_parts.append(
                    f"  {i}. {item.get('date', 'Unknown date')}: "
                    f"{item.get('summary', 'No summary')[:100]}"
                )
            doc_parts.append("")

        return "\n".join(doc_parts)

    def _build_findings(
        self,
        result: Dict[str, Any],
        historical_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build findings from Claude synthesis

        Args:
            result: Parsed Claude response
            historical_context: Historical context used

        Returns:
            Findings dictionary
        """
        # Extract synthesis
        synthesis = result.get("synthesis", "")

        # Analyze historical patterns
        historical_pattern = self._analyze_patterns(historical_context)

        # Extract vendor reliability (if applicable)
        vendor_reliability = result.get("vendor_reliability")

        # Extract recommendations
        recommendations = result.get("recommendations", [])

        # Assess risk
        risk_assessment = self._normalize_risk(result.get("risk_assessment", "low"))

        # Extract confidence
        confidence = result.get("confidence", 0.9)

        return {
            "synthesis": synthesis,
            "historical_pattern": historical_pattern,
            "vendor_reliability": vendor_reliability,
            "recommendations": recommendations,
            "risk_assessment": risk_assessment,
            "confidence": confidence,
            "historical_items_used": len(historical_context)
        }

    def _analyze_patterns(
        self,
        historical_context: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze patterns in historical context

        Args:
            historical_context: Historical interactions

        Returns:
            Pattern analysis or None
        """
        if not historical_context:
            return None

        # Count categories
        categories = {}
        for item in historical_context:
            cat = item.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        # Find most common category
        most_common = max(categories.items(), key=lambda x: x[1]) if categories else None

        return {
            "total_interactions": len(historical_context),
            "categories": categories,
            "most_common_category": most_common[0] if most_common else None,
            "frequency": most_common[1] if most_common else 0
        }

    def _normalize_risk(self, risk: str) -> str:
        """
        Normalize risk level to standard values

        Args:
            risk: Raw risk string

        Returns:
            Normalized risk level
        """
        risk = str(risk).lower().strip()

        if risk in ["critical", "severe"]:
            return RiskLevel.CRITICAL
        elif risk in ["high", "elevated"]:
            return RiskLevel.HIGH
        elif risk in ["medium", "moderate"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_next_actions(self, findings: Dict[str, Any]) -> List[str]:
        """
        Determine final actions based on synthesis

        Args:
            findings: Context findings

        Returns:
            List of next actions
        """
        actions = []

        risk = findings.get("risk_assessment")

        # High/critical risk needs human review
        if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            actions.append("human_review_required")

        # Always create summary report
        actions.append("generate_executive_summary")

        # If recommendations exist, create action plan
        if findings.get("recommendations"):
            actions.append("create_action_plan")

        return actions

    async def _store_interaction(
        self,
        input_data: ContextInput,
        findings: Dict[str, Any]
    ) -> None:
        """
        Store this interaction in memory for future context

        Args:
            input_data: Context input
            findings: Synthesis findings
        """
        try:
            await self.memory.store_interaction(
                email_id=input_data.email_id,
                category=input_data.triage_output.get("category"),
                summary=findings.get("synthesis", "")[:500],
                metadata={
                    "risk_level": findings.get("risk_assessment"),
                    "recommendations_count": len(findings.get("recommendations", []))
                }
            )
            logger.debug(f"Stored interaction {input_data.email_id} in memory")
        except Exception as e:
            logger.warning(f"Failed to store interaction in memory: {e}")
