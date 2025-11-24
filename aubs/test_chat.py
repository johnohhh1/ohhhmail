#!/usr/bin/env python3
"""
AUBS Chat Integration Test
Tests all chat endpoints and functionality
"""

import asyncio
import json
import sys
from typing import Optional

import httpx


class ChatTester:
    """Test harness for AUBS chat functionality"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    async def test_health(self) -> bool:
        """Test health endpoint"""
        print("\n1. Testing health endpoint...")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Health check passed")
                print(f"   ✓ Chat service active: {data.get('chat_service_active')}")
                print(f"   ✓ Dolphin connected: {data.get('dolphin_connected')}")
                print(f"   ✓ NATS connected: {data.get('nats_connected')}")
                return True
            else:
                print(f"   ✗ Health check failed: {response.status_code}")
                return False

    async def test_create_session(self) -> bool:
        """Test session creation"""
        print("\n2. Testing session creation...")

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/chat/sessions")

            if response.status_code == 201:
                data = response.json()
                self.session_id = data["id"]
                print(f"   ✓ Session created: {self.session_id}")
                print(f"   ✓ User ID: {data.get('user_id')}")
                print(f"   ✓ Message count: {data.get('message_count')}")
                return True
            else:
                print(f"   ✗ Session creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    async def test_operational_context(self) -> bool:
        """Test operational context endpoint"""
        print("\n3. Testing operational context...")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/chat/context")

            if response.status_code == 200:
                data = response.json()
                stats = data.get("statistics", {})
                print(f"   ✓ Operational context retrieved")
                print(f"   ✓ Total emails processed: {stats.get('total_emails_processed')}")
                print(f"   ✓ Emails today: {stats.get('emails_today')}")
                print(f"   ✓ Active executions: {stats.get('active_executions')}")
                print(f"   ✓ Tasks created: {stats.get('total_tasks_created')}")
                print(f"   ✓ High-risk items: {data.get('high_risk_items_count')}")
                return True
            else:
                print(f"   ✗ Context retrieval failed: {response.status_code}")
                return False

    async def test_chat_non_streaming(self) -> bool:
        """Test non-streaming chat"""
        print("\n4. Testing non-streaming chat...")

        if not self.session_id:
            print("   ✗ No session ID available")
            return False

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "What's the current system status?",
                    "session_id": self.session_id,
                    "stream": False
                }
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Chat response received")
                print(f"   ✓ Session ID: {data.get('session_id')}")
                print(f"   ✓ Response length: {len(data.get('message', ''))} chars")
                print(f"\n   Response preview:")
                print(f"   {data.get('message', '')[:200]}...")
                return True
            else:
                print(f"   ✗ Chat failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    async def test_chat_streaming(self) -> bool:
        """Test streaming chat"""
        print("\n5. Testing streaming chat...")

        if not self.session_id:
            print("   ✗ No session ID available")
            return False

        chunks = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "message": "Give me a brief summary",
                    "session_id": self.session_id,
                    "stream": True
                }
            ) as response:
                if response.status_code == 200:
                    print(f"   ✓ Streaming started")
                    print(f"   ✓ Response chunks: ", end="", flush=True)

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]
                            chunks.append(chunk)
                            print(".", end="", flush=True)

                    print(f"\n   ✓ Streaming complete")
                    print(f"   ✓ Total chunks: {len(chunks)}")
                    print(f"   ✓ Total length: {sum(len(c) for c in chunks)} chars")
                    return True
                else:
                    print(f"   ✗ Streaming failed: {response.status_code}")
                    return False

    async def test_chat_history(self) -> bool:
        """Test chat history retrieval"""
        print("\n6. Testing chat history...")

        if not self.session_id:
            print("   ✗ No session ID available")
            return False

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/chat/history/{self.session_id}"
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ History retrieved")
                print(f"   ✓ Message count: {data.get('message_count')}")

                messages = data.get("messages", [])
                for i, msg in enumerate(messages[:5], 1):  # Show first 5
                    role = msg.get("role")
                    content = msg.get("content", "")[:50]
                    print(f"   ✓ Message {i}: [{role}] {content}...")

                return True
            else:
                print(f"   ✗ History retrieval failed: {response.status_code}")
                return False

    async def test_list_sessions(self) -> bool:
        """Test session listing"""
        print("\n7. Testing session listing...")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/chat/sessions")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Sessions retrieved")
                print(f"   ✓ Session count: {data.get('session_count')}")

                sessions = data.get("sessions", [])
                for session in sessions[:3]:  # Show first 3
                    print(f"   ✓ Session: {session.get('id')} ({session.get('message_count')} messages)")

                return True
            else:
                print(f"   ✗ Session listing failed: {response.status_code}")
                return False

    async def test_delete_session(self) -> bool:
        """Test session deletion"""
        print("\n8. Testing session deletion...")

        if not self.session_id:
            print("   ✗ No session ID available")
            return False

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/chat/sessions/{self.session_id}"
            )

            if response.status_code == 204:
                print(f"   ✓ Session deleted: {self.session_id}")
                self.session_id = None
                return True
            else:
                print(f"   ✗ Session deletion failed: {response.status_code}")
                return False

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("AUBS Chat Integration Tests")
        print("=" * 60)

        tests = [
            ("Health Check", self.test_health),
            ("Create Session", self.test_create_session),
            ("Operational Context", self.test_operational_context),
            ("Non-Streaming Chat", self.test_chat_non_streaming),
            ("Streaming Chat", self.test_chat_streaming),
            ("Chat History", self.test_chat_history),
            ("List Sessions", self.test_list_sessions),
            ("Delete Session", self.test_delete_session),
        ]

        results = []

        for name, test_func in tests:
            try:
                result = await test_func()
                results.append((name, result))
            except Exception as e:
                print(f"   ✗ Test failed with exception: {e}")
                results.append((name, False))

        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")

        print("=" * 60)
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 60)

        return passed == total


async def main():
    """Main entry point"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"\nTesting AUBS Chat at: {base_url}\n")

    tester = ChatTester(base_url)

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
