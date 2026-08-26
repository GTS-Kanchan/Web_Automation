# Adding a new channel (worked example: Telegram)

None of this touches SMS, WhatsApp, RCS, or Email — that's the point of
the architecture in `docs/ARCHITECTURE.md`. Every step below is a new file
or one new line in a registry; nothing existing is edited except step 6.

## 1. Page objects

Every existing channel (SMS/RCS/WhatsApp/Email) now lives in its own
`pages/<channel>/` subfolder — that's the current convention to match:

```
pages/telegram/telegram_overview_page.py
pages/telegram/telegram_message_page.py
```

Each subclasses `pages.common.base_page.BasePage`, same as every other
page object in the suite — no changes needed there.

## 2. Channel class

```python
# channels/telegram_channel.py
from channels.base_channel import BaseChannel
from utils.config import Config


class TelegramChannel(BaseChannel):
    NAME = "telegram"

    @property
    def bot_token_alias(self) -> str:
        return Config.TELEGRAM_BOT_ALIAS  # add to utils/config.py when needed
```

## 3. Register it

```python
# channels/__init__.py
from channels.telegram_channel import TelegramChannel
_REGISTRY["telegram"] = TelegramChannel
```

(Or call `register_channel("telegram", TelegramChannel)` from
`channels/telegram_channel.py` itself if you'd rather not edit the
registry file at all.)

## 4. Fixtures

```python
# fixtures/telegram_fixtures.py
import pytest
from channels.telegram_channel import TelegramChannel


@pytest.fixture
def telegram_channel(logged_in_page) -> TelegramChannel:
    return TelegramChannel(page=logged_in_page)
```

## 5. Config (only if the channel needs its own test data)

```bash
# .env / config/environments/qa.env
TELEGRAM_BOT_ALIAS=qa_test_bot
```

```python
# utils/config.py, inside class Config:
TELEGRAM_BOT_ALIAS = os.getenv("TELEGRAM_BOT_ALIAS", "")
```

## 6. The one shared-file edit

```python
# conftest.py
pytest_plugins = [
    "fixtures.common_fixtures",
    "fixtures.sms_fixtures",
    "fixtures.whatsapp_fixtures",
    "fixtures.rcs_fixtures",
    "fixtures.email_fixtures",
    "fixtures.telegram_fixtures",   # <- the only line touched in an existing file
]
```

## 7. Tests

```python
# tests/telegram/messaging/test_telegram_message_flow.py
import pytest
from channels.telegram_channel import TelegramChannel
from pages.telegram.telegram_message_page import TelegramMessagePage

pytestmark = [pytest.mark.telegram, pytest.mark.messaging]


@pytest.mark.smoke
def test_send_message(logged_in_page, correlation_id):
    telegram = TelegramChannel(page=logged_in_page)
    msg_page = TelegramMessagePage(logged_in_page)
    name = telegram.unique("MESSAGE")
    telegram.log.info("Sending test message", name=name, correlation_id=correlation_id)
    # ... real interaction here ...
```

Add the marker to `pytest.ini`'s `markers =` block (one line):

```
telegram: Telegram channel
```

## 8. Run it

```bash
pytest tests/telegram
pytest -m telegram
PLAYWRIGHT_WORKERS=4 python scripts/run_tests.py tests/telegram
```

That's the entire surface area. No existing channel's test files, page
objects, or fixtures change.
