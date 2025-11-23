"""
ChiliHead OpsManager v2.1 - NATS JetStream Client
Handles event publishing, streaming, and replay
"""

import os
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

import nats
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, ConsumerConfig, DeliverPolicy

from shared.models import Event, EventType


class NATSClient:
    """NATS JetStream client for event streaming"""

    def __init__(
        self,
        servers: Optional[List[str]] = None,
        stream_name: str = "OPSMANAGER",
        subjects_prefix: str = "opsmanager"
    ):
        """
        Initialize NATS JetStream client

        Args:
            servers: List of NATS server URLs (default: env NATS_SERVERS)
            stream_name: JetStream stream name
            subjects_prefix: Prefix for all subjects
        """
        nats_servers = servers or os.getenv("NATS_SERVERS", "nats://localhost:4222").split(",")
        self.servers = [s.strip() for s in nats_servers]
        self.stream_name = stream_name
        self.subjects_prefix = subjects_prefix

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

        logger.info(f"NATSClient initialized: {self.servers}")

    async def connect(self):
        """Connect to NATS server and initialize JetStream"""
        try:
            self.nc = await nats.connect(servers=self.servers)
            self.js = self.nc.jetstream()

            # Ensure stream exists
            await self._ensure_stream()

            logger.info(f"Connected to NATS: {self.servers}")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def _ensure_stream(self):
        """Ensure JetStream stream exists with proper configuration"""
        try:
            # Check if stream exists
            stream_info = None
            try:
                stream_info = await self.js.stream_info(self.stream_name)
            except:
                pass

            if not stream_info:
                # Create stream
                config = StreamConfig(
                    name=self.stream_name,
                    subjects=[f"{self.subjects_prefix}.>"],
                    retention="limits",  # Retention by limits (time/size)
                    max_age=30 * 24 * 60 * 60 * 1_000_000_000,  # 30 days in nanoseconds
                    max_msgs=-1,  # No message limit
                    max_bytes=10 * 1024 * 1024 * 1024,  # 10GB max storage
                    storage="file",  # Persistent storage
                    num_replicas=1,
                    discard="old"  # Discard old messages when limits reached
                )

                await self.js.add_stream(config)
                logger.info(f"Created JetStream stream: {self.stream_name}")
            else:
                logger.info(f"JetStream stream already exists: {self.stream_name}")

        except Exception as e:
            logger.error(f"Failed to ensure stream: {e}")
            raise

    async def publish_event(
        self,
        event: Event,
        subject_suffix: Optional[str] = None
    ) -> str:
        """
        Publish an event to NATS JetStream

        Args:
            event: Event object to publish
            subject_suffix: Optional suffix for subject (uses event_type if not provided)

        Returns:
            Message sequence number

        Example:
            event = Event(
                event_type=EventType.EMAIL_RECEIVED,
                event_source="gmail_connector",
                event_data={"email_id": "123"},
                correlation_id=execution_id
            )
            seq = await nats_client.publish_event(event)
        """
        if not self.js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        try:
            # Determine subject
            suffix = subject_suffix or event.event_type.replace(".", "_")
            subject = f"{self.subjects_prefix}.{suffix}"

            # Serialize event
            payload = event.model_dump_json().encode()

            # Publish to JetStream
            ack = await self.js.publish(subject, payload)

            logger.debug(
                f"Published event: {event.event_type} "
                f"(seq: {ack.seq}, subject: {subject})"
            )

            return str(ack.seq)

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise

    async def subscribe(
        self,
        subject_pattern: str,
        callback: Callable[[Event], None],
        consumer_name: Optional[str] = None,
        deliver_policy: str = "new",
        durable: bool = True
    ) -> str:
        """
        Subscribe to events from JetStream

        Args:
            subject_pattern: Subject pattern to subscribe to (e.g., "emails.*")
            callback: Async callback function to process events
            consumer_name: Consumer name (auto-generated if None)
            deliver_policy: Delivery policy (new, all, last, by_start_sequence, by_start_time)
            durable: Whether to create durable consumer

        Returns:
            Subscription ID

        Example:
            async def handle_email(event: Event):
                print(f"Received: {event.event_type}")

            sub_id = await nats_client.subscribe(
                "emails.*",
                handle_email,
                consumer_name="email_processor"
            )
        """
        if not self.js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        try:
            # Build full subject
            full_subject = f"{self.subjects_prefix}.{subject_pattern}"

            # Consumer name
            consumer = consumer_name or f"consumer_{subject_pattern.replace('.', '_')}"

            # Deliver policy mapping
            policy_map = {
                "new": DeliverPolicy.NEW,
                "all": DeliverPolicy.ALL,
                "last": DeliverPolicy.LAST,
                "by_start_sequence": DeliverPolicy.BY_START_SEQUENCE,
                "by_start_time": DeliverPolicy.BY_START_TIME
            }

            # Create consumer config
            consumer_config = ConsumerConfig(
                durable_name=consumer if durable else None,
                deliver_policy=policy_map.get(deliver_policy, DeliverPolicy.NEW),
                ack_policy="explicit",
                ack_wait=30,  # 30 seconds to ack
                max_deliver=3,  # Max 3 delivery attempts
                filter_subject=full_subject
            )

            # Message handler wrapper
            async def message_handler(msg):
                try:
                    # Deserialize event
                    event_data = json.loads(msg.data.decode())
                    event = Event(**event_data)

                    # Call user callback
                    await callback(event)

                    # Acknowledge message
                    await msg.ack()

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Negative acknowledgment (will be redelivered)
                    await msg.nak()

            # Subscribe
            subscription = await self.js.subscribe(
                full_subject,
                cb=message_handler,
                stream=self.stream_name,
                config=consumer_config
            )

            logger.info(f"Subscribed to {full_subject} (consumer: {consumer})")
            return str(id(subscription))

        except Exception as e:
            logger.error(f"Failed to subscribe to {subject_pattern}: {e}")
            raise

    async def replay_events(
        self,
        subject_pattern: str,
        start_time: Optional[datetime] = None,
        start_sequence: Optional[int] = None,
        callback: Optional[Callable[[Event], None]] = None
    ) -> List[Event]:
        """
        Replay historical events

        Args:
            subject_pattern: Subject pattern to replay
            start_time: Replay from this timestamp
            start_sequence: Replay from this sequence number
            callback: Optional callback to process each event

        Returns:
            List of replayed events (if no callback provided)

        Example:
            # Replay last 24 hours
            events = await nats_client.replay_events(
                "emails.*",
                start_time=datetime.now() - timedelta(days=1)
            )
        """
        if not self.js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        try:
            full_subject = f"{self.subjects_prefix}.{subject_pattern}"

            # Determine deliver policy
            if start_sequence:
                deliver_policy = DeliverPolicy.BY_START_SEQUENCE
                opt_start_seq = start_sequence
                opt_start_time = None
            elif start_time:
                deliver_policy = DeliverPolicy.BY_START_TIME
                opt_start_seq = None
                opt_start_time = start_time
            else:
                deliver_policy = DeliverPolicy.ALL
                opt_start_seq = None
                opt_start_time = None

            # Create pull consumer for replay
            consumer_config = ConsumerConfig(
                deliver_policy=deliver_policy,
                opt_start_seq=opt_start_seq,
                opt_start_time=opt_start_time,
                ack_policy="explicit",
                filter_subject=full_subject
            )

            psub = await self.js.pull_subscribe(
                full_subject,
                stream=self.stream_name,
                config=consumer_config
            )

            events = []
            batch_size = 100
            timeout = 2.0  # 2 second timeout for no more messages

            while True:
                try:
                    # Fetch batch of messages
                    msgs = await psub.fetch(batch_size, timeout=timeout)

                    if not msgs:
                        break

                    for msg in msgs:
                        try:
                            # Deserialize event
                            event_data = json.loads(msg.data.decode())
                            event = Event(**event_data)

                            if callback:
                                await callback(event)
                            else:
                                events.append(event)

                            await msg.ack()

                        except Exception as e:
                            logger.error(f"Error processing replay message: {e}")

                except nats.errors.TimeoutError:
                    # No more messages available
                    break

            logger.info(f"Replayed {len(events)} events from {full_subject}")
            return events

        except Exception as e:
            logger.error(f"Failed to replay events: {e}")
            raise

    async def get_stream_info(self) -> Dict[str, Any]:
        """
        Get JetStream stream information

        Returns:
            Stream statistics and configuration
        """
        if not self.js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        try:
            info = await self.js.stream_info(self.stream_name)

            return {
                "name": info.config.name,
                "subjects": info.config.subjects,
                "messages": info.state.messages,
                "bytes": info.state.bytes,
                "first_seq": info.state.first_seq,
                "last_seq": info.state.last_seq,
                "consumer_count": info.state.consumer_count,
                "num_subjects": info.state.num_subjects
            }

        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            raise

    async def delete_consumer(self, consumer_name: str):
        """Delete a consumer"""
        if not self.js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        try:
            await self.js.delete_consumer(self.stream_name, consumer_name)
            logger.info(f"Deleted consumer: {consumer_name}")

        except Exception as e:
            logger.error(f"Failed to delete consumer {consumer_name}: {e}")
            raise

    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
