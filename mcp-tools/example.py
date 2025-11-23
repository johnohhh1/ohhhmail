"""
Example usage of MCP Tools

Demonstrates how to use the MCP tools integration suite.
"""

import asyncio
from datetime import datetime, timedelta
from mcp_tools import MCPToolsManager, TaskPriority, UrgencyLevel, EmailFolder


async def main():
    """Main example function."""

    # Initialize manager with all tools
    manager = MCPToolsManager(
        task_manager_config={
            "enabled": True,
            "api_token": "your_todoist_token",
            "default_project_id": "2203306141",
        },
        calendar_config={
            "enabled": True,
            "api_key": "your_google_api_key",
            "calendar_id": "primary",
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
    print("Initializing MCP tools...")
    await manager.initialize()

    # Check health
    print("\nChecking health...")
    health = await manager.health_check()
    print(f"Health status: {health}")

    # Example 1: Create a task
    print("\n=== Task Manager Example ===")
    task_result = await manager.task_manager.create_task(
        title="Review MCP integration",
        description="Test all MCP tools and verify functionality",
        due_date="tomorrow",
        priority=TaskPriority.HIGH,
        labels=["development", "testing"],
    )

    if task_result.success:
        task_id = task_result.data["task_id"]
        print(f"Created task: {task_id}")
        print(f"Task URL: {task_result.data['url']}")
    else:
        print(f"Failed to create task: {task_result.error}")

    # Example 2: Schedule a calendar event
    print("\n=== Calendar Example ===")
    start_time = datetime.now() + timedelta(days=1, hours=10)

    event_result = await manager.calendar.create_event(
        title="MCP Tools Review Meeting",
        start_time=start_time,
        duration_minutes=60,
        description="Review MCP tools implementation and discuss next steps",
        attendees=[
            {"email": "team@example.com", "displayName": "Development Team"}
        ],
        location="Conference Room B",
        send_invitations=True,
    )

    if event_result.success:
        event_id = event_result.data["event_id"]
        print(f"Created event: {event_id}")
        print(f"Event link: {event_result.data['html_link']}")
    else:
        print(f"Failed to create event: {event_result.error}")

    # Example 3: Check for calendar conflicts
    print("\n=== Checking Calendar Conflicts ===")
    conflicts_result = await manager.calendar.check_conflicts(
        start_time=start_time,
        end_time=start_time + timedelta(hours=2),
    )

    if conflicts_result.success:
        if conflicts_result.data["has_conflicts"]:
            print(f"Found {conflicts_result.data['conflict_count']} conflicts:")
            for conflict in conflicts_result.data["conflicts"]:
                print(f"  - {conflict['title']} ({conflict['start']} - {conflict['end']})")
        else:
            print("No conflicts found")

    # Example 4: Send SMS notification
    print("\n=== SMS Example ===")
    sms_result = await manager.sms.send_sms(
        to="+1987654321",
        message="MCP Tools integration is now active. Your calendar event has been scheduled.",
        urgency=UrgencyLevel.NORMAL,
    )

    if sms_result.success:
        message_sid = sms_result.data["message_sid"]
        print(f"Sent SMS: {message_sid}")
        print(f"Status: {sms_result.data['status']}")

        # Check delivery status
        status_result = await manager.sms.get_message_status(message_sid)
        if status_result.success:
            print(f"Delivery status: {status_result.data['status']}")
    else:
        print(f"Failed to send SMS: {sms_result.error}")

    # Example 5: Send bulk SMS
    print("\n=== Bulk SMS Example ===")
    bulk_result = await manager.sms.send_bulk_sms(
        recipients=["+1111111111", "+2222222222", "+3333333333"],
        message="System maintenance completed successfully",
        urgency=UrgencyLevel.LOW,
    )

    if bulk_result.success:
        print(f"Sent to {bulk_result.data['sent']}/{bulk_result.data['total']} recipients")
        if bulk_result.data['failures']:
            print(f"Failed: {bulk_result.data['failures']}")

    # Example 6: Email operations (if you have a message ID)
    print("\n=== Email Example ===")
    # Note: Replace with actual message ID
    message_id = "example_message_id"

    # Mark as read
    read_result = await manager.email.mark_as_read(message_id)
    if read_result.success:
        print("Marked email as read")

    # Archive email
    archive_result = await manager.email.archive(message_id)
    if archive_result.success:
        print("Archived email")

    # Example 7: Using task manager templates
    print("\n=== Task Update Example ===")
    if task_result.success:
        update_result = await manager.task_manager.update_task(
            task_id=task_result.data["task_id"],
            description="Updated: Completed testing and documentation",
            priority=TaskPriority.MEDIUM,
        )

        if update_result.success:
            print(f"Updated task fields: {update_result.data['updated_fields']}")

        # Add labels
        label_result = await manager.task_manager.add_labels(
            task_id=task_result.data["task_id"],
            labels=["completed", "verified"],
        )

        if label_result.success:
            print("Added labels to task")

        # Complete the task
        complete_result = await manager.task_manager.complete_task(
            task_id=task_result.data["task_id"]
        )

        if complete_result.success:
            print("Task marked as completed")

    # Cleanup
    print("\n=== Cleanup ===")
    await manager.close()
    print("All tools closed successfully")


if __name__ == "__main__":
    asyncio.run(main())
