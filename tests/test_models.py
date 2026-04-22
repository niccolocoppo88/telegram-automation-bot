"""
Unit tests for SQLAlchemy models.
Covers: User, AlertRule, AlertLog
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, User, AlertRule, AlertLog


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create session for testing"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestUserModel:
    """Tests for User model"""

    def test_user_creation(self, session):
        """UT-035: User model creation with valid data"""
        user = User(
            user_id=12345,
            username="testuser",
            is_admin=False,
            is_active=True
        )
        session.add(user)
        session.commit()

        result = session.query(User).filter_by(user_id=12345).first()
        assert result is not None
        assert result.username == "testuser"
        assert result.is_admin is False
        assert result.is_active is True

    def test_user_uniqueness_constraint(self, session):
        """UT-036: Duplicate username raises error"""
        user1 = User(user_id=1, username="testuser")
        session.add(user1)
        session.commit()

        user2 = User(user_id=2, username="testuser")
        session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            session.commit()

    def test_user_is_active_flag(self, session):
        """UT-041: User with is_active=False excluded from broadcasts"""
        active_user = User(user_id=1, username="active", is_active=True)
        inactive_user = User(user_id=2, username="inactive", is_active=False)
        session.add_all([active_user, inactive_user])
        session.commit()

        active_users = session.query(User).filter_by(is_active=True).all()
        assert len(active_users) == 1
        assert active_users[0].username == "active"

    def test_user_default_values(self, session):
        """Default values are set correctly"""
        user = User(user_id=99999, username="defaults")
        session.add(user)
        session.commit()

        result = session.query(User).filter_by(user_id=99999).first()
        assert result.is_admin is False
        assert result.is_active is True
        assert result.registered_at is not None


class TestAlertRuleModel:
    """Tests for AlertRule model"""

    def test_alert_rule_creation(self, session):
        """UT-037: AlertRule model creation with valid data"""
        rule = AlertRule(
            name="Test Rule",
            trigger_type="event",
            trigger_config={"event": "push"},
            message_template="Test alert",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        result = session.query(AlertRule).filter_by(name="Test Rule").first()
        assert result is not None
        assert result.trigger_type == "event"
        assert result.is_enabled is True

    def test_alert_rule_trigger_types(self, session):
        """Valid trigger types accepted"""
        for trigger_type in ["cron", "event", "manual"]:
            rule = AlertRule(
                name=f"Rule_{trigger_type}",
                trigger_type=trigger_type,
                trigger_config={},
                message_template="Test",
                target_chat_id=67890,
                created_by=12345
            )
            session.add(rule)
            session.commit()
            assert rule.trigger_type == trigger_type

    def test_alert_rule_invalid_trigger_type(self, session):
        """UT-014: Invalid trigger_type rejected"""
        rule = AlertRule(
            name="Invalid Rule",
            trigger_type="invalid",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)

        with pytest.raises(Exception):  # CheckConstraint violation
            session.commit()

    def test_alert_rule_cron_config(self, session):
        """Cron rules store schedule config"""
        rule = AlertRule(
            name="Daily Report",
            trigger_type="cron",
            trigger_config={"schedule": "0 9 * * *"},
            message_template="Good morning",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        result = session.query(AlertRule).filter_by(name="Daily Report").first()
        assert result.trigger_config["schedule"] == "0 9 * * *"

    def test_alert_rule_fk_constraint(self, session):
        """UT-038: Invalid created_by raises FK error"""
        rule = AlertRule(
            name="Orphan Rule",
            trigger_type="event",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=99999  # Non-existent user
        )
        session.add(rule)

        with pytest.raises(Exception):
            session.commit()


class TestAlertLogModel:
    """Tests for AlertLog model"""

    def test_alert_log_creation(self, session):
        """UT-039: AlertLog model creation"""
        # Create a rule first
        rule = AlertRule(
            name="Log Test Rule",
            trigger_type="event",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        log = AlertLog(
            rule_id=rule.rule_id,
            status="pending",
            payload={"test": "data"}
        )
        session.add(log)
        session.commit()

        result = session.query(AlertLog).filter_by(rule_id=rule.rule_id).first()
        assert result is not None
        assert result.status == "pending"

    def test_alert_log_status_sent(self, session):
        """UT-031: AlertLog on success has status='sent'"""
        rule = AlertRule(
            name="Sent Log Test",
            trigger_type="event",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        log = AlertLog(
            rule_id=rule.rule_id,
            status="sent",
            sent_at=datetime.now()
        )
        session.add(log)
        session.commit()

        result = session.query(AlertLog).filter_by(rule_id=rule.rule_id).first()
        assert result.status == "sent"
        assert result.sent_at is not None

    def test_alert_log_status_failed(self, session):
        """UT-032: AlertLog on failure has status='failed' and error_msg"""
        rule = AlertRule(
            name="Failed Log Test",
            trigger_type="event",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        log = AlertLog(
            rule_id=rule.rule_id,
            status="failed",
            error_msg="Telegram API error: 429"
        )
        session.add(log)
        session.commit()

        result = session.query(AlertLog).filter_by(rule_id=rule.rule_id).first()
        assert result.status == "failed"
        assert "429" in result.error_msg

    def test_alert_log_invalid_status(self, session):
        """Invalid status values rejected"""
        rule = AlertRule(
            name="Status Test",
            trigger_type="event",
            trigger_config={},
            message_template="Test",
            target_chat_id=67890,
            created_by=12345
        )
        session.add(rule)
        session.commit()

        log = AlertLog(
            rule_id=rule.rule_id,
            status="invalid_status"
        )
        session.add(log)

        with pytest.raises(Exception):  # CheckConstraint violation
            session.commit()

    def test_alert_log_fk_constraint(self, session):
        """UT-040: Invalid rule_id raises FK error"""
        log = AlertLog(
            rule_id=99999,  # Non-existent rule
            status="pending"
        )
        session.add(log)

        with pytest.raises(Exception):
            session.commit()