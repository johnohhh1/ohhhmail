# AUBS Chat - Example Conversations

## Example 1: Daily Summary

**User**: "Give me a summary of today's email activity"

**Assistant**: "Today we've processed 12 emails so far. Here's the breakdown:

- **Vendor emails**: 7 (including 2 invoices)
- **Staff requests**: 3
- **Customer inquiries**: 2

**Key highlights:**
- Created 5 new tasks (3 high-priority)
- Scheduled 2 calendar events
- Extracted 3 deadlines
- 1 failed execution (network timeout with invoice processing)

**Urgent items requiring attention:**
1. High-priority task: Fire extinguisher inspection due tomorrow
2. Failed execution: Invoice from Sysco Foods - needs manual review

Would you like more details on any of these items?"

---

## Example 2: Failed Executions

**User**: "Show me failed email executions"

**Assistant**: "I found 3 failed executions in our records:

**1. Failed Today (2 hours ago)**
- Email: Invoice from Sysco Foods
- Error: Network timeout during Vision Agent processing
- Attachments: 1 PDF invoice
- Recommendation: Retry processing or manual review needed

**2. Failed Yesterday**
- Email: Staff scheduling request from Maria
- Error: Deadline Agent parsing error
- Issue: Ambiguous date format in email body
- Status: Needs human review

**3. Failed 2 days ago**
- Email: Health inspection notice
- Error: High-risk keyword detected, automatic escalation failed
- Status: Escalated to manager, awaiting response

Would you like me to help you retry any of these or get more details?"

---

## Example 3: Task Status

**User**: "What tasks need attention?"

**Assistant**: "Based on the current task list, here are items needing attention:

**HIGH PRIORITY (3 tasks)**
1. Fire extinguisher inspection
   - Due: Tomorrow (Jan 16)
   - Created from: Safety email on Jan 14
   - Status: Pending

2. Order produce for weekend
   - Due: Today before 3 PM
   - Created from: Inventory alert
   - Status: In progress

3. Review health inspection checklist
   - Due: Jan 18
   - Created from: County health dept email
   - Status: Pending

**MEDIUM PRIORITY (5 tasks)**
- Schedule staff meeting (Due: Jan 20)
- Update menu pricing (Due: Jan 22)
- Contact HVAC repair (Due: Jan 19)
- Process vendor invoices (Due: Jan 17)
- Order cleaning supplies (Due: Jan 21)

The produce order is most urgent - it's due in 4 hours. Would you like me to provide more details on any task?"

---

## Example 4: Specific Email Query

**User**: "What happened with the fire inspection email?"

**Assistant**: "Let me look that up for you.

**Email: Fire Safety Inspection Notice**
- Received: Jan 14, 2025 at 9:23 AM
- From: fire_marshal@county.gov
- Status: Successfully processed

**Processing Results:**
- Triage Agent: Classified as HIGH urgency vendor communication
- Deadline Agent: Extracted deadline - Jan 16, 2025
- Task Agent: Created high-priority task
- Vision Agent: No attachments to process
- Context Agent: Flagged as critical - fire safety compliance

**Actions Taken:**
1. Created task: 'Fire extinguisher inspection' (High priority)
2. Set deadline: Tomorrow, Jan 16
3. Sent SMS notification to manager
4. Added to Google Calendar

**Current Status:**
- Task is still pending
- Due in 24 hours
- Assigned to: Manager (auto-assigned based on safety category)

The email mentioned annual inspection of fire extinguishers and exit signs. Would you like me to help you complete this task or reschedule?"

---

## Example 5: Agent Performance

**User**: "How are the agents performing?"

**Assistant**: "Here's the current agent performance overview:

**TRIAGE AGENT**
- Executions: 145
- Avg execution time: 1,234 ms
- Avg confidence: 0.94
- Model: llama3.2:8b-instruct
- Status: Performing well

**VISION AGENT**
- Executions: 42 (only runs when attachments present)
- Avg execution time: 3,567 ms
- Avg confidence: 0.87
- Model: gpt-4o
- Status: Good, some timeout issues

**DEADLINE AGENT**
- Executions: 145
- Avg execution time: 1,456 ms
- Avg confidence: 0.91
- Model: llama3.2:8b-instruct
- Status: Excellent

**TASK AGENT**
- Executions: 98
- Avg execution time: 1,678 ms
- Avg confidence: 0.89
- Model: llama3.2:8b-instruct
- Status: Performing well

**CONTEXT AGENT (CRITICAL)**
- Executions: 145
- Avg execution time: 2,890 ms
- Avg confidence: 0.96
- Model: claude-sonnet-4
- Status: Excellent, no fallback needed

**Observations:**
- Vision Agent has 2 timeout failures - might need timeout increase
- All agents maintaining high confidence scores
- Context Agent (Claude) showing highest reliability

Would you like detailed stats on a specific agent?"

---

## Example 6: System Health

**User**: "Is everything running okay?"

**Assistant**: "System health check:

**Overall Status: HEALTHY** ✓

**Core Services:**
- AUBS Orchestrator: Running
- Dolphin Server: Connected ✓
- NATS Message Broker: Connected ✓
- Chat Service: Active (3 sessions, 142 messages)

**Processing Stats (Last 24 hours):**
- Emails processed: 12
- Success rate: 91.7% (11/12 successful)
- Average processing time: 5.2 seconds
- Active executions: 2

**Agent Health:**
- All 5 agent types operational
- No fallback activations needed
- Average confidence: 0.91

**Alerts:**
- 1 recent failure (Vision Agent timeout)
- 2 high-risk items flagged
- No system errors

**Resource Usage:**
- CPU: Normal
- Memory: Normal
- Network: Stable

Everything is running smoothly. The one failed execution was a timeout issue with an invoice PDF - likely a temporary network issue. Would you like me to elaborate on anything?"

---

## Example 7: Historical Pattern

**User**: "Do we have a pattern with vendor emails?"

**Assistant**: "Based on the historical data in our Context Agent's 30-day memory:

**Vendor Email Patterns:**

**Volume:**
- Average: 15-20 vendor emails per week
- Peak days: Mondays and Thursdays
- Most common time: 8-10 AM

**Common Vendors:**
1. Sysco Foods (invoices, delivery confirmations)
2. US Foods (weekly orders)
3. Utility companies (monthly bills)
4. Cleaning supplies vendors
5. Equipment maintenance companies

**Processing Trends:**
- 95% successfully auto-processed
- 3% require human review (pricing discrepancies)
- 2% fail processing (attachment issues)

**Deadline Patterns:**
- Invoice payments: Typically 30-day terms
- Delivery notifications: 1-2 days advance notice
- Inspection notices: 7-14 days advance notice

**Action Patterns:**
- 60% create tasks (mostly payment processing)
- 25% create calendar events (deliveries, inspections)
- 15% trigger notifications (urgent/high-value)

**Reliability Scores:**
- Sysco Foods: 98% reliable (rarely missed deadlines)
- US Foods: 95% reliable
- Local vendors: More variable (80-90%)

The Context Agent has learned these patterns over time and uses them for better decision-making. Need more specific vendor analysis?"

---

## Example 8: Proactive Insights

**User**: "Anything I should know about?"

**Assistant**: "Yes! I've identified several items that need your attention:

**URGENT (Next 24 hours):**
1. **Produce order** - Due today at 3 PM (4 hours left)
   - Source: Inventory alert email
   - Action needed: Place order or mark complete

2. **Fire extinguisher inspection** - Due tomorrow
   - Source: County fire marshal email
   - Action needed: Schedule inspector or self-inspect

**ATTENTION REQUIRED:**
3. **Failed invoice processing** - Sysco Foods invoice
   - Issue: Vision Agent timeout
   - Action needed: Manual review or retry
   - Amount: Unknown (PDF not processed)

4. **Staff scheduling conflict** - Maria's request
   - Issue: Ambiguous date parsing failed
   - Action needed: Review original email

**UPCOMING (Next 7 days):**
5. Health inspection checklist review (Jan 18)
6. HVAC repair scheduling (Jan 19)
7. Staff meeting needs scheduling (Jan 20)

**POSITIVE NOTES:**
- 91.7% email processing success rate
- All critical agents performing well
- No system errors or outages

**RECOMMENDATION:**
Focus on the produce order first (most time-sensitive), then address the fire inspection. The failed invoice can wait until after these urgent items.

Would you like help with any of these?"

---

## Best Practices for Interacting with AUBS Chat

### Be Specific
- ✓ "Show me high-priority tasks due this week"
- ✗ "What's going on?"

### Ask for Context
- ✓ "What's the history of emails from Sysco Foods?"
- ✓ "Why did the deadline extraction fail?"

### Request Actions
- ✓ "Help me prioritize today's tasks"
- ✓ "What should I focus on first?"

### Deep Dive
- ✓ "Show me details on execution ID abc-123"
- ✓ "What did the Context Agent decide for the fire inspection email?"

### Monitoring
- ✓ "Alert me to any failures"
- ✓ "What's the system health?"
- ✓ "How are the agents performing?"

The assistant has complete operational awareness and can answer questions about any aspect of your email processing pipeline!
