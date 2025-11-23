# MCP Tools Integration

Complete MCP tools suite for task management, calendar, SMS, and email operations.

## Features

- **Task Manager** - Todoist integration for task management
- **Calendar** - Google Calendar integration for scheduling
- **SMS** - Twilio SMS notifications
- **Email Client** - Gmail operations (reply, forward, archive)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with the following variables:

```env
# Task Manager (Todoist)
TODOIST_API_TOKEN=your_todoist_token
TODOIST_DEFAULT_PROJECT_ID=your_project_id

# Calendar (Google)
GOOGLE_CALENDAR_API_KEY=your_api_key
GOOGLE_CALENDAR_ID=primary

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Email (Gmail)
GMAIL_API_KEY=your_gmail_api_key
GMAIL_USER_ID=me
```

## Usage

### Basic Setup

```python
from mcp_tools import MCPToolsManager

# Initialize manager
manager = MCPToolsManager(
    task_manager_config={
        "enabled": True,
        "api_token": "your_todoist_token",
    },
    calendar_config={
        "enabled": True,
        "api_key": "your_google_api_key",
    },
    sms_config={
        "enabled": True,
        "account_sid": "your_twilio_sid",
        "auth_token": "your_twilio_token",
        "from_number": "+1234567890",
    },
    email_config={
        "enabled": True,
        "api_key": "your_gmail_api_key",
    },
)

# Initialize all tools
await manager.initialize()

# Check health
health = await manager.health_check()
print(health)
```

### Task Manager

```python
from mcp_tools import TaskManager, TaskPriority

task_manager = TaskManager({
    "enabled": True,
    "api_token": "your_todoist_token",
})

await task_manager.initialize()

# Create a task
result = await task_manager.create_task(
    title="Review pull request",
    description="Check code quality and tests",
    due_date="tomorrow",
    priority=TaskPriority.HIGH,
    labels=["code-review", "urgent"],
)

if result.success:
    task_id = result.data["task_id"]
    print(f"Created task: {task_id}")

# Update task
await task_manager.update_task(
    task_id=task_id,
    priority=TaskPriority.MEDIUM,
)

# Complete task
await task_manager.complete_task(task_id)
```

### Calendar

```python
from mcp_tools import CalendarManager
from datetime import datetime, timedelta

calendar = CalendarManager({
    "enabled": True,
    "api_key": "your_google_api_key",
})

await calendar.initialize()

# Create event
start_time = datetime.now() + timedelta(days=1)

result = await calendar.create_event(
    title="Team Meeting",
    start_time=start_time,
    duration_minutes=60,
    description="Weekly sync",
    attendees=[
        {"email": "team@example.com", "displayName": "Team"}
    ],
    location="Conference Room A",
    send_invitations=True,
)

if result.success:
    event_id = result.data["event_id"]
    print(f"Created event: {event_id}")

# Check for conflicts
conflicts = await calendar.check_conflicts(
    start_time=start_time,
    end_time=start_time + timedelta(hours=2),
)
```

### SMS

```python
from mcp_tools import SMSManager, UrgencyLevel

sms = SMSManager({
    "enabled": True,
    "account_sid": "your_twilio_sid",
    "auth_token": "your_twilio_token",
    "from_number": "+1234567890",
})

await sms.initialize()

# Send SMS
result = await sms.send_sms(
    to="+1987654321",
    message="Your verification code is 123456",
    urgency=UrgencyLevel.HIGH,
)

if result.success:
    message_sid = result.data["message_sid"]
    print(f"Sent SMS: {message_sid}")

# Send bulk SMS
await sms.send_bulk_sms(
    recipients=["+1111111111", "+2222222222"],
    message="Service maintenance scheduled for tonight",
    urgency=UrgencyLevel.NORMAL,
)

# Check delivery status
status = await sms.get_message_status(message_sid)
```

### Email Client

```python
from mcp_tools import EmailClient, EmailFolder

email = EmailClient({
    "enabled": True,
    "api_key": "your_gmail_api_key",
})

await email.initialize()

# Reply to email
result = await email.send_reply(
    message_id="message_id_here",
    body="Thanks for your email. I'll get back to you soon.",
    html=False,
)

# Forward email
await email.forward_email(
    message_id="message_id_here",
    to=["colleague@example.com"],
    body="FYI - please review this",
)

# Mark as read
await email.mark_as_read("message_id_here")

# Archive email
await email.archive("message_id_here")

# Move to folder
await email.move_to_folder(
    message_id="message_id_here",
    folder=EmailFolder.ARCHIVE,
)
```

## Architecture

### Base Class

All tools inherit from `MCPToolBase` which provides:

- HTTP client setup with retry logic
- Standardized error handling
- Response validation
- Logging with rotation
- Health check functionality

### Result Format

All operations return `MCPToolResult`:

```python
@dataclass
class MCPToolResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Error Handling

Errors are wrapped in `MCPToolError`:

```python
class MCPToolError(Exception):
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        ...
```

### Retry Logic

Uses `tenacity` for automatic retries:

- 3 retry attempts
- Exponential backoff (1s, 2s, 4s)
- Retries on timeout and network errors
- Configurable via `max_retries` config

## File Structure

```
mcp-tools/
├── __init__.py           # Package exports and MCPToolsManager
├── base.py              # Base classes and common functionality
├── task_manager.py      # Todoist integration
├── calendar.py          # Google Calendar integration
├── sms.py              # Twilio SMS integration
├── email_client.py     # Gmail integration
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Error Codes

Common error codes:

- `TOOL_DISABLED` - Tool is disabled in config
- `CLIENT_NOT_INITIALIZED` - HTTP client not initialized
- `HTTP_XXX` - HTTP status error (e.g., HTTP_404)
- `TIMEOUT` - Request timeout
- `NETWORK_ERROR` - Network connectivity issue
- `UNEXPECTED_ERROR` - Unexpected exception
- `NO_UPDATES` - No update fields provided
- `TEMPLATE_ERROR` - Template variable missing

## Testing

Run health checks:

```python
# Check all tools
health = await manager.health_check()
print(health)
# {'task_manager': True, 'calendar': True, 'sms': True, 'email': True}

# Check individual tool
is_healthy = await task_manager.health_check()
```

## Logging

Logs are stored in `logs/` directory:

- `logs/taskmanager.log`
- `logs/calendarmanager.log`
- `logs/smsmanager.log`
- `logs/emailclient.log`

Logs rotate daily and are retained for 7 days.

## License

MIT
