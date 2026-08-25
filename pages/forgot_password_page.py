"""
MOVED — this page object now lives at pages/common/forgot_password_page.py as part of the
channel-based architecture reorg's final batch (see docs/ARCHITECTURE.md).
The remote-device bridge used to deliver this refactor cannot delete
files, so this old path was overwritten with this thin re-export shim
instead of being removed outright — any code still importing
`pages.forgot_password_page` keeps working unchanged. Update those imports to
`pages.common.forgot_password_page` when convenient, then delete this file
(pages/forgot_password_page.py).
"""
from pages.common.forgot_password_page import *  # noqa: F401,F403
