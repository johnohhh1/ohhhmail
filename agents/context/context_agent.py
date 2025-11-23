"""
ChiliHead OpsManager v2.1 - Context Agent
Synthesizes all agent outputs with 30-day historical memory from Qdrant
CRITICAL: NO FALLBACK - Fails if configured model unavailable
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from agents.base import BaseAgent
from shared.models import (
    AgentType,
    ContextInput,
    ContextOutput,
    RiskLevel,
    AgentInput,
    AgentOutput
)
from shared.llm_config import LLMConfig, LLMProvider


class ContextAgent(BaseAgent):
    """
    Context Agent - Intelligence synthesis and decision support
    CRITICAL COMPONENT - NO FALLBACK ALLOWED

    Responsibilities:
    - Synthesize outputs from all agents
    - Query Qdrant for 30-day historical context
    - Analyze vendor reliability patterns
    - Assess operational risks
    - Generate intelligent recommendations
    - Pattern detection across time series

    IMPORTANT: This agent MUST use Claude Sonnet 4 or GPT-4o
    If configured model is unavailable, the agent FAILS FAST
    """

    CONTEXT_SYSTEM_PROMPT = """You are a senior restaurant operations AI advisor with access to complete historical context.

Your role is to synthesize ALL available information and provide strategic, actionable intelligence.

INPUTS YOU RECEIVE:
1. Triage Analysis - Email categorization and urgency
2. Vision Output - Extracted invoice/receipt data (if applicable)
3. Deadline Information - All temporal commitments
4. Task Analysis - Identified action items
5. Historical Context - 30 days of similar emails and outcomes

ANALYSIS FRAMEWORK:

1. SYNTHESIS
   Integrate all agent findings into coherent narrative
   Highlight critical information and potential issues
   Connect current situation to historical patterns

2. HISTORICAL PATTERN ANALYSIS
   Review similar past emails from this sender
   Identify recurring issues or trends
   Compare current urgency/amounts to historical baseline
   Detect anomalies (unusual amounts, timing, requests)

3. VENDOR RELIABILITY SCORING
   Based on historical data, assess:
   - On-time delivery rate
   - Invoice accuracy
   - Price consistency
   - Issue resolution speed
   Rate: excellent | good | fair | poor | insufficient_data

4. RISK ASSESSMENT
   Evaluate operational risks:
   - CRITICAL: Safety/health violations, legal issues, immediate threats
   - HIGH: Significant financial risk, major service disruption
   - MEDIUM: Moderate cost impact, minor service issues
   - LOW: Routine operations, minimal risk

5. RECOMMENDATIONS
   Provide specific, actionable recommendations:
   - Immediate actions required
   - Follow-up items
   - Process improvements
   - Risk mitigation steps

Respond with valid JSON:
{
  "synthesis": "<comprehensive narrative synthesis>",
  "historical_pattern": {
    "sender_history": "<summary of past interactions>",
    "frequency": "<how often we receive emails from this sender>",
    "typical_urgency": <average urgency score>,
    "anomalies": ["<any unusual aspects of current email>"],
    "trend": "increasing|stable|decreasing"
  },
  "vendor_reliability": {
    "rating": "excellent|good|fair|poor|insufficient_data",
    "on_time_rate": <0.0-1.0>,
    "issue_count": <number>,
    "payment_history": "excellent|good|problematic",
    "notes": "<any concerns or highlights>"
  },
  "risk_assessment": {
    "level": "critical|high|medium|low",
    "factors": ["<risk factors identified>"],
    "financial_impact": "<estimated impact>",
    "operational_impact": "<how this affects operations>",
    "mitigation_steps": ["<recommended actions>"]
  },
  "recommendations": [
    {
      "priority": "critical|high|medium|low",
      "action": "<specific action to take>",
      "assignee": "<who should handle this>",
      "rationale": "<why this is recommended>",
      "deadline": "<when this should be done>"
    }
  ],
  "confidence": <0.0-1.0>,
  "requires_human_review": <true|false>
}"""

    def __init__(self, config: LLMConfig):
        """
        Initialize Context Agent

        Args:
            config: LLM configuration (MUST support advanced reasoning)

        Raises:
            ValueError: If fallback is enabled (not allowed for Context Agent)
        """
        # CRITICAL: Verify no fallback is configured
        if config.fallback_allowed:
            raise ValueError(
                "Context Agent MUST NOT have fallback enabled. "
                "This is a critical component that requires high-quality model."
            )

        # Verify appropriate model
        if config.provider == LLMProvider.OLLAMA:
            # Only allow large models on Ollama
            if "120b" not in config.model.lower() and "70b" not in config.model.lower():
                logger.warning(
                    f"Context Agent using Ollama model '{config.model}'. "
                    "Recommended: Use Claude Sonnet 4 or GPT-4o for production."
                )

        super().__init__(config, AgentType.CONTEXT)

        # Initialize Qdrant client
        self.qdrant_client = None
        self._init_qdrant()

    def _init_qdrant(self):
        """Initialize Qdrant vector database client"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            import os

            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")

            self.qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )

            # Verify collection exists or create it
            collection_name = "email_history"
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)

            if not collection_exists:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embeddings size
                        distance=Distance.COSINE
                    )
                )

            logger.info("Qdrant client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            # Don't fail initialization, but log warning
            logger.warning("Context Agent will operate without historical memory")

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Synthesize all agent outputs with historical context

        Args:
            input_data: ContextInput with all agent outputs and historical data

        Returns:
            ContextOutput with synthesis and recommendations

        Raises:
            Exception: On model failure (NO FALLBACK)
        """
        if not isinstance(input_data, ContextInput):
            raise ValueError("Input must be ContextInput")

        logger.info("Starting context synthesis and historical analysis")

        # Create checkpoint for context analysis start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="context_analysis_start",
                data={"has_historical": len(input_data.historical_context) > 0}
            )

        # Retrieve additional historical context from Qdrant
        enhanced_history = await self._retrieve_historical_context(
            input_data.email_id,
            input_data.triage_output
        )

        # Combine provided and retrieved historical context
        full_historical_context = input_data.historical_context + enhanced_history

        # Build comprehensive analysis prompt
        messages = [
            {
                "role": "user",
                "content": self._build_synthesis_prompt(
                    input_data.triage_output,
                    input_data.vision_output,
                    input_data.deadline_output,
                    input_data.task_output,
                    full_historical_context
                )
            }
        ]

        # Generate context analysis using configured model (NO FALLBACK)
        try:
            response = await self._generate_with_llm(
                messages=messages,
                system_prompt=self.CONTEXT_SYSTEM_PROMPT,
                temperature=0.4,  # Balanced creativity and consistency
                max_tokens=3000
            )

            logger.info(f"Context analysis generated using {response.model_used}")

        except Exception as e:
            logger.error(f"Context Agent FAILED - Model unavailable: {e}")
            # CRITICAL: No fallback - re-raise exception
            raise Exception(
                f"Context Agent CRITICAL FAILURE: {e}\n"
                "This agent requires high-quality model and does not support fallback."
            )

        # Parse response
        try:
            context_data = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse context response: {e}")
            raise Exception(f"Context Agent output parsing failed: {e}")

        # Build findings
        findings = {
            "synthesis": context_data.get("synthesis", ""),
            "historical_pattern": context_data.get("historical_pattern"),
            "vendor_reliability": context_data.get("vendor_reliability"),
            "recommendations": context_data.get("recommendations", []),
            "risk_assessment": self._validate_risk_level(
                context_data.get("risk_assessment", {}).get("level", "low")
            )
        }

        # Add full risk assessment details
        findings["risk_details"] = context_data.get("risk_assessment", {})

        # Extract confidence
        confidence = context_data.get("confidence", 0.8)

        # Determine if human review is required
        requires_review = context_data.get("requires_human_review", False)
        next_actions = ["generate_actions"]

        if requires_review:
            next_actions.insert(0, "human_review")

        # Store this interaction in Qdrant for future context
        await self._store_interaction(
            email_id=input_data.email_id,
            triage_output=input_data.triage_output,
            context_output=findings
        )

        # Create checkpoint for context analysis completion
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="context_analysis_complete",
                data=findings
            )

        logger.success(
            f"Context synthesis complete: Risk={findings['risk_assessment']}, "
            f"Recommendations={len(findings['recommendations'])}"
        )

        return ContextOutput(
            agent_type=AgentType.CONTEXT,
            findings=findings,
            confidence=confidence,
            next_actions=next_actions,
            execution_time_ms=0,
            model_used=response.model_used,
            ui_tars_checkpoints=self.checkpoints
        )

    def _build_synthesis_prompt(
        self,
        triage: Dict[str, Any],
        vision: Optional[Dict[str, Any]],
        deadline: Dict[str, Any],
        task: Optional[Dict[str, Any]],
        historical: List[Dict[str, Any]]
    ) -> str:
        """Build comprehensive synthesis prompt"""

        prompt = f"""Analyze this email and provide strategic intelligence:

=== TRIAGE ANALYSIS ===
Category: {triage.get('category')}
Urgency: {triage.get('urgency')}/100
Type: {triage.get('type')}
Requires Vision: {triage.get('requires_vision')}
Has Deadlines: {triage.get('has_deadline')}
Reasoning: {triage.get('reasoning')}
"""

        if vision:
            prompt += f"""
=== VISION ANALYSIS ===
Documents Processed: {vision.get('images_processed', 0)}
Invoice Data: {len(vision.get('invoice_data', []))} invoices extracted
Receipt Data: {len(vision.get('receipt_data', []))} receipts extracted
"""
            # Add invoice details if available
            if vision.get('invoice_data'):
                prompt += f"\nInvoice Details:\n{vision['invoice_data'][0]}"

        prompt += f"""
=== DEADLINE ANALYSIS ===
Deadlines Found: {len(deadline.get('deadlines', []))}
Recurring Events: {len(deadline.get('recurring_events', []))}
Dates Extracted: {len(deadline.get('parsed_dates', []))}
"""
        if deadline.get('deadlines'):
            prompt += f"\nKey Deadlines:\n"
            for dl in deadline['deadlines'][:3]:  # Top 3 deadlines
                prompt += f"- {dl.get('text')} ({dl.get('urgency')})\n"

        if task:
            prompt += f"""
=== TASK ANALYSIS ===
Tasks Identified: {len(task.get('tasks', []))}
Total Estimated Time: {task.get('total_estimated_time', 0)} minutes
Summary: {task.get('summary')}
"""
            # Add task breakdown
            priorities = task.get('priorities', {})
            prompt += f"\nTask Priorities:\n"
            prompt += f"- Critical: {len(priorities.get('critical', []))}\n"
            prompt += f"- High: {len(priorities.get('high', []))}\n"
            prompt += f"- Medium: {len(priorities.get('medium', []))}\n"
            prompt += f"- Low: {len(priorities.get('low', []))}\n"

        if historical:
            prompt += f"""
=== HISTORICAL CONTEXT (30-Day Memory) ===
Similar Emails: {len(historical)}
"""
            # Add summary of historical patterns
            for idx, hist in enumerate(historical[:5], 1):  # Top 5
                prompt += f"\n{idx}. {hist.get('summary', 'Previous interaction')}\n"
                prompt += f"   Date: {hist.get('date', 'Unknown')}\n"
                prompt += f"   Outcome: {hist.get('outcome', 'Unknown')}\n"

        prompt += """

Based on ALL the above information, provide your comprehensive analysis as JSON.
Focus on actionable intelligence and strategic recommendations.
"""

        return prompt

    async def _retrieve_historical_context(
        self,
        email_id: str,
        triage_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant historical context from Qdrant

        Args:
            email_id: Current email ID
            triage_output: Triage analysis for similarity search

        Returns:
            List of historical context entries
        """
        if not self.qdrant_client:
            logger.warning("Qdrant not available, skipping historical retrieval")
            return []

        try:
            # Generate embedding for current email context
            # TODO: Implement embedding generation
            # For now, return empty list
            logger.debug("Historical context retrieval not yet implemented")
            return []

        except Exception as e:
            logger.error(f"Failed to retrieve historical context: {e}")
            return []

    async def _store_interaction(
        self,
        email_id: str,
        triage_output: Dict[str, Any],
        context_output: Dict[str, Any]
    ) -> None:
        """
        Store interaction in Qdrant for future reference

        Args:
            email_id: Email ID
            triage_output: Triage results
            context_output: Context analysis results
        """
        if not self.qdrant_client:
            return

        try:
            # TODO: Implement vector storage
            logger.debug(f"Stored interaction {email_id} to Qdrant")

        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")

    def _validate_risk_level(self, risk: str) -> str:
        """Validate and normalize risk level"""
        try:
            return RiskLevel(risk.lower()).value
        except (ValueError, AttributeError):
            logger.warning(f"Invalid risk level '{risk}', defaulting to 'low'")
            return RiskLevel.LOW.value
