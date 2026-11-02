"""Integration adapters package."""

from .base import BaseIntegration
from .discord import DiscordIntegration
from .email import EmailIntegration
from .slack import SlackIntegration
from .webhook import WebhookIntegration

__all__ = [
    "BaseIntegration",
    "SlackIntegration",
    "DiscordIntegration",
    "EmailIntegration",
    "WebhookIntegration",
]
