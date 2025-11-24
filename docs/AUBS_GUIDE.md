# 🤖 AUBS - Your Personal Operations Assistant

## Who is AUBS?

**AUBS** (Auburn Hills Business System) is your friendly, intelligent assistant for Chili's #605 in Auburn Hills. She's not just a chatbot - she's your operational awareness system with complete visibility into emails, tasks, deadlines, and team performance.

---

## What AUBS Knows

### ✅ Complete Email Awareness
- Every email processed through the system
- Who sent it and when
- Current processing status
- Any extracted tasks or deadlines
- Email filtering ensures only relevant domains/senders

### ✅ All Your Tasks
- Current open tasks with priorities
- Due dates and deadlines
- Task status (pending, in progress, completed)
- Who assigned what and when

### ✅ Upcoming Deadlines
- Deadlines extracted from leadership emails
- HotSchedules due dates
- Corporate report deadlines
- Team-related commitments

### ✅ Agent Performance
- How each AI agent is performing
- Processing times and confidence scores
- Any failures or issues

### ✅ System Health
- All services running properly
- Connection status
- Processing queue depth

---

## How AUBS Talks to You

AUBS has been designed with a specific personality:

### Communication Style
- **Conversational and warm** - She's your partner, not a robot
- **Uses "we"** when talking about the restaurant
- **Celebrates wins** - If something's going well, she'll acknowledge it
- **Direct but supportive** when there are problems
- **Concise** unless you ask for details
- **Casual language** when appropriate ("Hey, looks like...", "Heads up...")

### Example Conversations

**You:** "What's urgent today?"

**AUBS:** "Hey John! Here's what needs your attention today:

1. **Leadership deadline** - Your DM needs the manager schedule by Friday 5pm
2. **Team issue** - Sarah called out for tonight's shift, you're down a server
3. **Guest feedback** - We got a complaint about slow service last night in section 3

The DM email just came in 20 minutes ago, so that's fresh. Want me to pull up the manager schedule to review?"

---

## AUBS Priority System

AUBS understands restaurant operations and knows what matters most. She prioritizes in this order:

1. **Deadlines from leadership** (DM, AMD, RVP emails) - CRITICAL
2. **Team issues** (callouts, no-shows, morale problems)
3. **Guest impact** (complaints, feedback, service issues)
4. **Performance metrics** (comp sales %, GWAP scores)
5. **Routine operations** (schedules, inventory, maintenance)

When you ask "What's urgent?" or "What needs my attention?", she'll automatically use this priority order.

---

## Restaurant Operations Knowledge

### RAP Mobile Metrics
AUBS understands your key performance indicators:
- **Comp Sales %** - Year-over-year sales comparison
- **GWAP Scores** - Guest Wait and Prep (speed of service)
- **Labor %** - Labor cost as percentage of sales
- **Food Cost %** - Food cost tracking
- **Daily Sales** - Revenue tracking
- **Guest Count** - Traffic patterns
- **Check Average** - Per-guest spending

### HotSchedules Context
- Manager schedules and shift coverage
- Team member availability and time-off
- Labor budget vs. actual hours
- Shift notes and communication

### Chili's-Specific Knowledge
- Store #605 in Auburn Hills
- Brinker corporate structure (DM → AMD → RVP)
- Chili's menu, operations, and standards
- The 5-pillar delegation system (coming soon)

---

## Questions You Can Ask AUBS

### Priority & Planning
- "What's urgent today?"
- "What needs my attention?"
- "Help me prioritize my next 2 hours"
- "What are my deadlines this week?"
- "Any issues I need to know about?"

### Email & Communication
- "Show me emails from my DM"
- "What did corporate send today?"
- "Any team callouts?"
- "What's the latest from leadership?"

### Tasks & Deadlines
- "What tasks are due soon?"
- "Show me high-priority items"
- "What did I assign to the team?"
- "When is the manager schedule due?"

### Performance & Metrics
- "How are we doing on sales?"
- "Any GWAP issues?"
- "Show me labor percentage"
- "What's our guest count trend?"

### System Status
- "Is everything running okay?"
- "Any failed email processing?"
- "Show me agent performance"
- "What's the system health?"

---

## Email Filtering (CRITICAL)

AUBS only processes emails from approved sources to prevent spam and noise:

### Allowed Domains
- `chilis.com` - Brinker corporate emails
- `brinker.com` - Corporate communications
- `gmail.com` - Your personal Gmail

### Customizing Filters
Edit `infrastructure/docker/.env`:

```env
# Only process emails from these domains
ALLOWED_DOMAINS=chilis.com,brinker.com,gmail.com

# Optionally specify exact senders
ALLOWED_SENDERS=dm@chilis.com,regional@brinker.com

# Block specific domains or senders
BLOCKED_DOMAINS=spam.com,marketing.com
BLOCKED_SENDERS=noreply@spam.com
```

**Important:** Restart the email-ingestion service after changing filters:
```bash
docker-compose restart email-ingestion
```

---

## How to Chat with AUBS

### Via Open-WebUI
1. Open http://localhost:3040
2. Click the chat button (bottom-right floating button)
3. Start chatting!

### Via API (for developers)
```bash
# Create a new chat session
curl -X POST http://localhost:8000/api/chat/session

# Send a message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "What's urgent today?",
    "stream": false
  }'
```

---

## Technical Details

### AI Model
AUBS uses **Claude Sonnet 4** (the latest, most capable Claude model) for all conversations.

### Context Window
- Maintains last 10 messages in conversation history
- Has access to ALL operational data in real-time
- Can reference any email, task, or deadline processed by the system

### Streaming Responses
- Supports real-time streaming for faster perceived response time
- Each word appears as AUBS "thinks"

### Session Management
- Sessions persist across page refreshes
- All conversations stored in database
- Can resume previous conversations

---

## Privacy & Security

### What AUBS Knows
- Only emails that pass through the filtering system
- Only data from Chili's #605 operations
- No access to external data sources

### What AUBS Doesn't Share
- Your operational data stays within the system
- No data sent to third parties
- All processing happens within your infrastructure
- Claude API calls are encrypted and ephemeral

### Access Control
- Currently single-user system (you)
- Can be extended with user authentication if needed

---

## Tips for Best Results

### 1. Be Specific
❌ "What about emails?"
✅ "Show me emails from my DM this week"

### 2. Ask Follow-Up Questions
AUBS remembers context, so you can have natural conversations:
- "What's urgent?"
- "Tell me more about that DM email"
- "When's that deadline?"

### 3. Use Natural Language
No need for commands or keywords - just talk:
- "Hey, what should I focus on today?"
- "I have 30 minutes before my meeting, what's critical?"
- "Did I get any team callouts?"

### 4. Request Summaries
- "Give me a quick rundown of today"
- "What happened overnight?"
- "Brief me on this week's priorities"

### 5. Ask for Help Planning
- "Help me plan my next 2 hours"
- "What should I tackle first?"
- "I'm overwhelmed, where do I start?"

---

## Coming Soon

### Planned Features
- **ChiliHead 5-Pillar Delegations** - Track team development using the proven delegation framework
- **Calendar Integration** - Google Calendar sync for deadlines and events
- **Performance Trend Analysis** - AI-powered insights into sales, labor, and operational trends
- **Proactive Alerts** - AUBS will message you about critical issues
- **Voice Interface** - Talk to AUBS hands-free during service

---

## Troubleshooting

### AUBS Not Responding
1. Check system status: `cd infrastructure/docker && docker-compose ps`
2. Verify AUBS service is running
3. Check logs: `docker-compose logs -f aubs`

### Emails Not Being Processed
1. Check email filtering configuration in `.env`
2. Verify Gmail credentials are correct
3. Check email-ingestion logs: `docker-compose logs -f email-ingestion`

### Chat History Lost
- Sessions are currently stored in memory
- Restart of AUBS service will clear sessions
- PostgreSQL persistence coming in next update

---

## Support

If you encounter issues or have questions:

1. **Check the logs** - Most issues show up in service logs
2. **Review BUILD_STATUS.md** - See what's implemented vs. planned
3. **GitHub Issues** - https://github.com/johnohhh1/ohhhmail/issues

---

**Built with ❤️ specifically for John at Chili's #605 Auburn Hills**

*AUBS - Your trusted partner in running an excellent restaurant*
