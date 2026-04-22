"""Tests for database models."""

import pytest
from datetime import datetime

from sqlalchemy import select

from src.models import User, AlertRule, AlertLog, Base


# Test User model
def test_user_model_creation():
    """Test that User model can be instantiated."""
    user = User(
        user_id=12345,
        username="testuser",
        first_name="Test",
        is_active=True,
        is_admin=False,
    )
    assert user.user_id == 12345
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.is_admin is False


def test_user_default_values():
    """Test User default values."""
    user = User(user_id=99999)
    assert user.is_active is True
    assert user.is_admin is False
    assert user.registered_at is not None


# Test AlertRule model
def test_alert_rule_creation():
    """Test that AlertRule model can be instantiated."""
    rule = AlertRule(
        name="GitHub Push Alert",
        trigger_type="push",
        trigger_config='{"repo": "test/repo"}',
        action_type="telegram",
        action_config='{"chat_id": 12345}',
    )
    assert rule.name == "GitHub Push Alert"
    assert rule.trigger_type == "push"
    assert rule.is_enabled is True


def test_alert_rule_defaults():
    """Test AlertRule default values."""
    rule = AlertRule(
        name="Test",
        trigger_type="push",
        trigger_config="{}",
        action_type="telegram",
        action_config="{}",
    )
    assert rule.is_enabled is True
    assert rule.created_at is not None
    assert rule.updated_at is not None


# Test AlertLog model
def test_alert_log_creation():
    """Test that AlertLog model can be instantiated."""
    log = AlertLog(
        rule_id=1,
        status="pending",
    )
    assert log.rule_id == 1
    assert log.status == "pending"
    assert log.triggered_at is not None


def test_alert_log_status_values():
    """Test that AlertLog accepts valid status values."""
    for status in ["pending", "sent", "failed"]:
        log = AlertLog(rule_id=1, status=status)
        assert log.status == status