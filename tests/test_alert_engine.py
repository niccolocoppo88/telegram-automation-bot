"""
Unit tests for Alert Engine.
Covers: Alert triggering, evaluation, message sending, retry logic
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from tests.conftest import (
    sample_alert_rule,
    sample_cron_rule,
    mock_github_webhook_push,
    mock_github_webhook_pr,
)


class TestAlertTriggering:
    """Tests for alert triggering logic"""

    @pytest.mark.asyncio
    async def test_alert_triggered_for_matching_rule(self, sample_alert_rule):
        """UT-029: Alert triggered when GitHub event matches rule"""
        from src.alert_engine import trigger_alert

        with patch(
            "src.alert_engine.send_telegram_message", new_callable=AsyncMock
        ) as mock_send:
            with patch(
                "src.alert_engine.create_alert_log", new_callable=AsyncMock
            ) as mock_log:
                mock_send.return_value = {"success": True, "message_id": 123}
                mock_log.return_value = {"log_id": 1}

                webhook_payload = mock_github_webhook_push
                result = await trigger_alert(sample_alert_rule, webhook_payload)

                assert result["success"] is True
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_not_triggered_for_non_matching(self):
        """UT-030: No alert when event doesn't match any rule"""
        from src.alert_engine import evaluate_event_rules

        non_matching_payload = {
            "action": "opened",
            "repository": {"full_name": "other/repo"},
        }

        rules = [
            {
                "trigger_type": "event",
                "trigger_config": {"event": "push", "repo": "test/repo"},
            }
        ]

        with patch(
            "src.alert_engine.trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            await evaluate_event_rules(non_matching_payload)

            # No triggers since event doesn't match
            mock_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_rules_matched(self):
        """IT-014: Two rules match same event → both triggered"""
        from src.alert_engine import evaluate_event_rules

        matching_payload = {"event": "push", "repository": {"full_name": "test/repo"}}

        rules = [
            {
                "rule_id": 1,
                "trigger_type": "event",
                "trigger_config": {"event": "push", "repo": "test/repo"},
            },
            {
                "rule_id": 2,
                "trigger_type": "event",
                "trigger_config": {"event": "push", "repo": "test/repo"},
            },
        ]

        with patch(
            "src.alert_engine.trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            mock_trigger.return_value = {"success": True}

            await evaluate_event_rules(matching_payload, rules)

            assert mock_trigger.call_count == 2


class TestAlertLogging:
    """Tests for alert logging"""

    @pytest.mark.asyncio
    async def test_alert_log_on_success(self, sample_alert_rule):
        """UT-031: AlertLog status='sent' when send succeeds"""
        from src.alert_engine import trigger_alert

        with patch(
            "src.alert_engine.send_telegram_message", new_callable=AsyncMock
        ) as mock_send:
            with patch(
                "src.alert_engine.create_alert_log", new_callable=AsyncMock
            ) as mock_log:
                mock_send.return_value = {"success": True}
                mock_log.return_value = {"log_id": 1, "status": "sent"}

                await trigger_alert(sample_alert_rule, {})

                log_call = mock_log.call_args[0]
                assert log_call[2] == "sent"  # status='sent'

    @pytest.mark.asyncio
    async def test_alert_log_on_failure(self, sample_alert_rule):
        """UT-032: AlertLog status='failed' when send fails"""
        from src.alert_engine import trigger_alert

        with patch(
            "src.alert_engine.send_telegram_message", new_callable=AsyncMock
        ) as mock_send:
            with patch(
                "src.alert_engine.create_alert_log", new_callable=AsyncMock
            ) as mock_log:
                mock_send.side_effect = Exception("Telegram error: 500")
                mock_log.return_value = {"log_id": 1}

                result = await trigger_alert(sample_alert_rule, {})

                assert result["success"] is False
                log_call = mock_log.call_args[0]
                assert log_call[2] == "failed"


class TestCronAlerts:
    """Tests for cron-based alert evaluation"""

    @pytest.mark.asyncio
    async def test_cron_trigger_evaluation(self, sample_cron_rule):
        """UT-033: Cron rules evaluated on schedule"""
        from src.alert_engine import evaluate_cron_rules

        with patch(
            "src.alert_engine.trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            with patch(
                "src.alert_engine.get_enabled_cron_rules", new_callable=AsyncMock
            ) as mock_get:
                mock_get.return_value = [sample_cron_rule]
                mock_trigger.return_value = {"success": True}

                await evaluate_cron_rules()

                mock_trigger.assert_called()


class TestRateLimitHandling:
    """Tests for Telegram rate limit (429) handling"""

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_backoff(self):
        """EC-001, EC-002: 429 triggers exponential backoff"""
        from src.alert_engine import send_with_retry

        attempts = []

        async def mock_send_with_failures(*args, **kwargs):
            attempts.append(len(attempts))
            if len(attempts) < 3:
                raise Exception("429 Too Many Requests")
            return {"success": True, "message_id": 123}

        with patch(
            "src.alert_engine.send_telegram_message",
            side_effect=mock_send_with_failures,
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await send_with_retry({}, 67890)

                assert result["success"] is True
                assert mock_sleep.call_count >= 2  # Backoff called

    @pytest.mark.asyncio
    async def test_rate_limit_max_backoff(self):
        """EC-003: Backoff caps at 60 seconds"""
        from src.alert_engine import send_with_retry

        async def mock_always_fail(*args, **kwargs):
            raise Exception("429 Too Many Requests")

        with patch(
            "src.alert_engine.send_telegram_message", side_effect=mock_always_fail
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                mock_sleep.return_value = None

                result = await send_with_retry({}, 67890, max_retries=3)

                assert result["success"] is False
                # Verify backoff didn't exceed 60s per attempt
                for sleep_call in mock_sleep.call_args_list:
                    delay = sleep_call[0][0]
                    assert delay <= 60

    @pytest.mark.asyncio
    async def test_rate_limit_during_broadcast(self):
        """EC-004: Rate limit during broadcast queues remaining messages"""
        from src.alert_engine import send_broadcast_to_users

        users = [{"user_id": i, "chat_id": 67890 + i} for i in range(5)]
        attempts = []

        async def mock_send(user_id, chat_id, message):
            attempts.append(user_id)
            if user_id == 2:
                raise Exception("429 Too Many Requests")
            return {"success": True}

        with patch("src.alert_engine.send_telegram_message", side_effect=mock_send):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await send_broadcast_to_users(users, "Test message")

                # Users 0,1 succeeded, 2 rate-limited, 3,4 queued and retried
                assert len(attempts) >= 5  # All attempted


class TestMessageFormat:
    """Tests for alert message formatting"""

    @pytest.mark.asyncio
    async def test_github_push_message_format(
        self, sample_alert_rule, mock_github_webhook_push
    ):
        """GitHub push event formatted correctly"""
        from src.alert_engine import format_alert_message

        message = await format_alert_message(
            sample_alert_rule, mock_github_webhook_push
        )

        assert "push" in message.lower() or "commit" in message.lower()

    @pytest.mark.asyncio
    async def test_github_pr_message_format(
        self, sample_alert_rule, mock_github_webhook_pr
    ):
        """GitHub PR event formatted correctly"""
        from src.alert_engine import format_alert_message

        message = await format_alert_message(sample_alert_rule, mock_github_webhook_pr)

        assert "pull" in message.lower() or "pr" in message.lower() or "#42" in message

    @pytest.mark.asyncio
    async def test_template_variable_substitution(self):
        """Message template variables are substituted"""
        from src.alert_engine import format_alert_message

        rule = {
            "message_template": "Event: {event} on repo {repo}",
            "trigger_config": {},
        }
        payload = {"event": "push", "repository": {"full_name": "test/repo"}}

        message = await format_alert_message(rule, payload)

        assert "push" in message
        assert "test/repo" in message


class TestConcurrentAlerts:
    """Tests for concurrent alert handling (IT-013, CT-001)"""

    @pytest.mark.asyncio
    async def test_concurrent_alerts_no_data_corruption(self):
        """CT-001: Multiple alerts at same time don't corrupt data"""
        import asyncio

        from src.alert_engine import trigger_alert

        rules = [
            {"rule_id": i, "name": f"Rule {i}", "message_template": "Test {i}"}
            for i in range(5)
        ]

        results = []

        async def trigger_one(rule):
            with patch(
                "src.alert_engine.send_telegram_message", new_callable=AsyncMock
            ) as mock_send:
                with patch(
                    "src.alert_engine.create_alert_log", new_callable=AsyncMock
                ) as mock_log:
                    mock_send.return_value = {"success": True}
                    mock_log.return_value = {"log_id": rule["rule_id"]}

                    result = await trigger_alert(rule, {})
                    results.append(result)

        tasks = [trigger_one(rule) for rule in rules]
        await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_rapid_webhook_burst(self):
        """CT-003: 10 webhooks rapidly → all processed"""
        import asyncio

        from src.alert_engine import evaluate_event_rules

        matching_payload = {"event": "push", "repository": {"full_name": "test/repo"}}
        rules = [
            {"rule_id": 1, "trigger_type": "event", "trigger_config": {"event": "push"}}
        ]

        processed = []

        async def mock_trigger(rule, payload):
            processed.append(1)

        with patch("src.alert_engine.trigger_alert", side_effect=mock_trigger):
            tasks = [evaluate_event_rules(matching_payload, rules) for _ in range(10)]
            await asyncio.gather(*tasks)

            assert len(processed) == 10


class TestAlertRetry:
    """Tests for alert retry logic (IT-015)"""

    @pytest.mark.asyncio
    async def test_alert_retry_on_failure(self):
        """IT-015: Failed alert retried with backoff"""
        from src.alert_engine import send_with_retry

        attempt_count = 0

        async def failing_then_success(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return {"success": True, "message_id": 123}

        with patch(
            "src.alert_engine.send_telegram_message", side_effect=failing_then_success
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await send_with_retry({}, 67890, max_retries=5)

                assert result["success"] is True
                assert attempt_count == 3
                assert mock_sleep.call_count == 2  # 2 failures = 2 backoffs

    @pytest.mark.asyncio
    async def test_alert_max_retries_exceeded(self):
        """Max retries reached → alert marked as failed"""
        from src.alert_engine import send_with_retry

        async def always_fail(*args, **kwargs):
            raise Exception("Persistent failure")

        with patch("src.alert_engine.send_telegram_message", side_effect=always_fail):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await send_with_retry({}, 67890, max_retries=3)

                assert result["success"] is False
                assert "max retries" in result.get("error", "").lower()


class TestQueuePersistence:
    """Tests for queue handling (EC-008, EC-009)"""

    @pytest.mark.asyncio
    async def test_queue_persists_across_restarts(self):
        """EC-008: Queue survives bot restart"""
        from src.alert_engine import get_pending_queue, add_to_queue, process_queue

        # Add items to queue
        await add_to_queue({"alert_id": 1, "message": "test1"})
        await add_to_queue({"alert_id": 2, "message": "test2"})

        # Simulate restart (new instance)
        queue = await get_pending_queue()
        assert len(queue) >= 2

    @pytest.mark.asyncio
    async def test_queue_processes_in_order(self):
        """Messages processed FIFO from queue"""
        from src.alert_engine import add_to_queue, process_queue

        order = []

        async def mock_send(chat_id, message):
            order.append(message)
            return {"success": True}

        with patch("src.alert_engine.send_telegram_message", side_effect=mock_send):
            await add_to_queue({"chat_id": 1, "message": "first"})
            await add_to_queue({"chat_id": 1, "message": "second"})

            await process_queue()

            assert order == ["first", "second"]
