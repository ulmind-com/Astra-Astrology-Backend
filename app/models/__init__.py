"""Beanie document registry — every model listed here is registered on startup."""

from beanie import Document

from app.models.abuse_report import AbuseReport
from app.models.appointment import Appointment, AppointmentSlot, AvailabilityWindow, PrivateInviteLink
from app.models.astrologer import Astrologer
from app.models.call import CallSession, ZegoCallbackEvent
from app.models.chat import ChatMessage, ChatRead, ChatSession
from app.models.earning import EarningEntry
from app.models.payout import AstrologerPayout
from app.models.favorite import AstrologerFavorite
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
from app.models.face_reading import FaceReading, FaceRule
from app.models.palm_reading import PalmReading, PalmRule
from app.models.review import Review
from app.models.ai_astrologer import (
    AIChatFeedback,
    AIChatSession,
    AIUserMemory,
    AICustomRule,
    AIKnowledgeDoc,
)
from app.models.settings import CoinRateChange, PlatformSettings
from app.models.cms import HomePageCMS, ShopCMS
from app.models.passkey import PasskeyChallenge, PasskeyCredential
from app.models.support import SupportTicket
from app.models.user import User
from app.models.wallet import (
    PaymentOrder,
    Wallet,
    WalletTransaction,
    WebhookEvent,
)
from app.models.milan import MilanRoom
from app.models.whiteboard import CallWhiteboard
from app.models.shop import (
    Cart,
    Product,
    ProductCategory,
    ShopCoupon,
    ShopOrder,
    UserAddress,
)
from app.models.course import (
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseLessonProgress,
    CourseQuestion,
    CourseSection,
)

DOCUMENT_MODELS: list[type[Document]] = [
    User,
    Astrologer,
    OtpCode,
    PendingRegistration,
    PlatformSettings,
    HomePageCMS,
    ShopCMS,
    PasskeyCredential,
    PasskeyChallenge,
    CoinRateChange,
    Wallet,
    WalletTransaction,
    PaymentOrder,
    WebhookEvent,
    CallSession,
    ZegoCallbackEvent,
    Appointment,
    AppointmentSlot,
    AvailabilityWindow,
    PrivateInviteLink,
    ChatMessage,
    ChatRead,
    ChatSession,
    FaceReading,
    FaceRule,
    PalmReading,
    PalmRule,
    Review,
    AbuseReport,
    EarningEntry,
    AstrologerPayout,
    AstrologerFavorite,
    AIKnowledgeDoc,
    AICustomRule,
    AIChatSession,
    AIUserMemory,
    AIChatFeedback,
    SupportTicket,
    CallWhiteboard,
    MilanRoom,
    ProductCategory,
    Product,
    UserAddress,
    Cart,
    ShopOrder,
    ShopCoupon,
    Course,
    CourseSection,
    CourseLesson,
    CourseEnrollment,
    CourseLessonProgress,
    CourseQuestion,
]

__all__ = [
    "DOCUMENT_MODELS",
    "AbuseReport",
    "SupportTicket",
    "AIKnowledgeDoc",
    "AICustomRule",
    "AIChatSession",
    "AIChatFeedback",
    "Astrologer",
    "AstrologerFavorite",
    "CallSession",
    "CallWhiteboard",
    "MilanRoom",
    "Appointment",
    "AppointmentSlot",
    "AvailabilityWindow",
    "PrivateInviteLink",
    "ChatMessage",
    "ChatRead",
    "ChatSession",
    "FaceReading",
    "FaceRule",
    "PalmReading",
    "PalmRule",
    "Review",
    "EarningEntry",
    "AstrologerPayout",
    "CoinRateChange",
    "OtpCode",
    "PaymentOrder",
    "PendingRegistration",
    "PlatformSettings",
    "HomePageCMS",
    "ShopCMS",
    "PasskeyCredential",
    "PasskeyChallenge",
    "User",
    "Wallet",
    "WalletTransaction",
    "WebhookEvent",
    "ZegoCallbackEvent",
    "ProductCategory",
    "Product",
    "UserAddress",
    "Cart",
    "ShopOrder",
    "ShopCoupon",
    "Course",
    "CourseSection",
    "CourseLesson",
    "CourseEnrollment",
    "CourseLessonProgress",
    "CourseQuestion",
]
