"""Channel factory — resolves a channel key ("sms", "whatsapp", "rcs",
"email", ...) to its BaseChannel subclass, so fixtures/tooling that need to
work generically across channels (e.g. a CLI arg, a data-driven test) don't
need an if/elif chain. Adding a new channel = one new entry here."""
from channels.base_channel import BaseChannel
from channels.email_channel import EmailChannel
from channels.rcs_channel import RCSChannel
from channels.sms_channel import SMSChannel
from channels.whatsapp_channel import WhatsAppChannel

_REGISTRY = {
    "sms": SMSChannel,
    "whatsapp": WhatsAppChannel,
    "rcs": RCSChannel,
    "email": EmailChannel,
}


def get_channel(name: str, page=None, env: str = None) -> BaseChannel:
    """Factory: get_channel("sms", page=module_logged_in_page) -> SMSChannel(...)"""
    try:
        cls = _REGISTRY[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown channel {name!r}. Registered channels: {sorted(_REGISTRY)}. "
            "Register a new channel by adding it to channels/__init__.py's _REGISTRY."
        )
    return cls(page=page, env=env)


def register_channel(name: str, cls) -> None:
    """Called by a future channel's own module (or a plugin) to register
    itself without editing this file, e.g. from a Telegram channel package:
        from channels import register_channel
        register_channel("telegram", TelegramChannel)
    """
    _REGISTRY[name.lower()] = cls
