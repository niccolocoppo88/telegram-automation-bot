"""Tests for SQLAlchemy models."""
import pytest
from datetime import datetime

from src.models import User, AlertRule, AlertLog


def test_user_model():
    """Test User model creation."""
    user = User(
        user_id=123456,
        username="testuser",
        is_admin=False,
        is_active=True,
    )
    assert user.user_id == 123456
    assert user.username == "testuser"
    assert user.is_admin is False
    assert user.is_active is True
    assert user.registered_at is None or isinstance(user.registered_at, datetime)


def test_user_model_admin():
    """Test User model with admin flag."""
    admin = User(
        user_id=999,
        username="admin",
        is_admin=True,
    )
    assert admin.is_admin is True


def test_alert_rule_model():
    """Test AlertRule model creation."""
    rule = AlertRule(
        name="Test Rule",
        trigger_type="event",
        trigger_config={"event": "push"},
        message_template="New push to {repo}",
        target_chat_id=123456,
        is_enabled=True,
        created_by=123456,
    )
    assert rule.name == "Test Rule"
    assert rule.trigger_type == "event"
    assert rule.trigger_config == {"event": "push"}
    assert rule.is_enabled is True


def test_alert_log_model():
    """Test AlertLog model creation."""
    log = AlertLog(
        rule_id=1,
        status="pending",
        payload={"message": "test"},
    )
    assert log.rule_id == 1
    assert log.status == "pending"
    assert log.payload == {"message": "test"}
    assert log.triggered_at is None or isinstance(log.triggered_at, datetime)


def test_alert_log_statuses():
    """Test AlertLog with different statuses."""
    for status in ("pending", "sent", "failed"):
        log = AlertLog(rule_id=1, status=status)
        assert log.status == status


def test_alert_rule_trigger_types():
    """Test AlertRule with different trigger types."""
    for trigger_type in ("cron", "event", "manual"):
        rule = AlertRule(
            name=f"Test {trigger_type}",
            trigger_type=trigger_type,
            trigger_config={},
            message_template="Test",
            target_chat_id=1,
            created_by=1,
        )
        assert rule.trigger_type == trigger_type
