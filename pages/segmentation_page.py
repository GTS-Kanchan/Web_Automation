"""
MOVED — this page object now lives at pages/common/segmentation_page.py as part of the
channel-based architecture reorg's final batch (see docs/ARCHITECTURE.md).
The remote-device bridge used to deliver this refactor cannot delete
files, so this old path was overwritten with this thin re-export shim
instead of being removed outright — any code still importing
`pages.segmentation_page` keeps working unchanged. Update those imports to
`pages.common.segmentation_page` when convenient, then delete this file
(pages/segmentation_page.py).
"""
from pages.common.segmentation_page import *  # noqa: F401,F403
