"""
ChiliHead OpsManager v2.1 - Email Analyzer
Direct LLM analysis for email triage - NO Dolphin needed
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import anthropic
from openai import AsyncOpenAI

from shared.models import EmailData


class EmailAnalyzer:
    """Analyzes emails using LLM and returns structured triage results"""

    TRIAGE_PROMPT = """You are an expert restaurant operations AI analyzing emails for Chili's #605 Auburn Hills.

Analyze this email and provide a detailed triage report in JSON format.

Email Details:
Subject: {subject}
From: {sender}
Body:
{body}

Provide your analysis as JSON with this exact structure:
{{
  "executive_summary": "Brief 1-2 sentence summary of the most critical item",
  "emergency_items": [
    {{
      "description": "Description of emergency/critical item",
      "severity": "HIGH|MEDIUM|LOW",
      "action_required": "What needs to be done immediately"
    }}
  ],
  "action_items": [
    {{
      "description": "Specific action needed",
      "due_date": "YYYY-MM-DD or null",
      "priority": "HIGH|MEDIUM|LOW",
      "estimated_time": "e.g. '30 minutes', '1 hour'",
      "assigned_to": "Team member name or null"
    }}
  ],
  "deadlines": [
    {{
      "description": "What the deadline is for",
      "date": "YYYY-MM-DD",
      "time": "HH:MM or null",
      "recurring": false
    }}
  ],
  "dashboard_insights": [
    "Insight or observation about operations"
  ],
  "operational_insights": [
    "Pattern detected or operational recommendation"
  ],
  "quick_links": [
    {{
      "name": "Link name",
      "url": "URL if applicable"
    }}
  ],
  "category": "vendor|staff|customer|system",
  "urgency_score": 0-100,
  "confidence": 0.0-1.0
}}

Focus on:
- Staffing gaps (Devon, Carmen, Blake, Tiffany, etc.)
- Deadlines from leadership (DM, AMD, RVP)
- Guest complaints or feedback
- Vendor issues or deliveries
- HotSchedules or RAP Mobile references
"""

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        if self.anthropic_key:
            self.client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
            self.provider = "anthropic"
        elif self.openai_key:
            self.client = AsyncOpenAI(api_key=self.openai_key)
            self.provider = "openai"
        else:
            raise ValueError("No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    async def analyze(self, email: EmailData) -> Dict[str, Any]:
        """
        Analyze email with LLM and return structured triage results

        Args:
            email: Email data to analyze

        Returns:
            Structured triage analysis
        """
        prompt = self.TRIAGE_PROMPT.format(
            subject=email.subject,
            sender=email.sender,
            body=email.body[:4000]  # Limit body length
        )

        if self.provider == "anthropic":
            return await self._analyze_anthropic(prompt)
        else:
            return await self._analyze_openai(prompt)

    async def _analyze_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Analyze with Claude"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        return self._parse_json_response(content)

    async def _analyze_openai(self, prompt: str) -> Dict[str, Any]:
        """Analyze with GPT-4"""
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        import json
        import re

        # Remove markdown code blocks if present
        content = content.strip()
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Find JSON object
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            content = content[start:end]

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Return default structure if parsing fails
            return {
                "executive_summary": "Failed to parse LLM response",
                "emergency_items": [],
                "action_items": [],
                "deadlines": [],
                "dashboard_insights": [],
                "operational_insights": [],
                "quick_links": [],
                "category": "system",
                "urgency_score": 50,
                "confidence": 0.5,
                "error": str(e)
            }
