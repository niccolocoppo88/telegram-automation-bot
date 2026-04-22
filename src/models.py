"""SQLAlchemy models for the Telegram Automation Bot."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """User model for registered bot users."""

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)

    # Relationships
    alert_rules = relationship("AlertRule", back_populates="creator", foreign_keys="AlertRule.created_by")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, is_admin={self.is_admin})>"


class AlertRule(Base):
    """Alert rule model for configuring automated alerts."""

    __tablename__ = "alert_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    trigger_type = Column(String(20), nullable=False)  # 'cron', 'event', 'manual'
    trigger_config = Column(JSON, nullable=False)
    message_template = Column(Text, nullable=False)
    target_chat_id = Column(Integer, nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="alert_rules", foreign_keys=[created_by])
    logs = relationship("AlertLog", back_populates="rule")

    def __repr__(self):
        return f"<AlertRule(rule_id={self.rule_id}, name={self.name}, trigger_type={self.trigger_type})>"


class AlertLog(Base):
    """Alert log model for tracking alert executions."""

    __tablename__ = "alert_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.rule_id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # 'pending', 'sent', 'failed'
    error_msg = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)

    # Relationships
    rule = relationship("AlertRule", back_populates="logs")

    def __repr__(self):
        return f"<AlertLog(log_id={self.log_id}, rule_id={self.rule_id}, status={self.status})>"