"""SQLAlchemy models. Importing this package registers all tables on Base.metadata."""
from app.models.audit_log import AuditLog
from app.models.device import Device
from app.models.otp_code import OTPCode
from app.models.reputation_data import ReputationData
from app.models.scan import AIReport, Scan, ScanResult
from app.models.session import UserSession
from app.models.threat_indicator import ThreatIndicator
from app.models.user import User

__all__ = [
    "AuditLog", "Device", "OTPCode", "ReputationData",
    "Scan", "ScanResult", "AIReport", "UserSession",
    "ThreatIndicator", "User",
]
