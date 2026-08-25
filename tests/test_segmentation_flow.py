"""
MOVED — this file's tests now live at tests/common/test_segmentation_flow.py as part of
the channel-based architecture reorg's final batch (see
docs/ARCHITECTURE.md and docs/ADDING_A_CHANNEL.md). The remote-device
bridge used to deliver this refactor cannot delete files, so this old path
was overwritten with this empty stub instead of being removed outright —
deliberately EMPTY (no test functions) so pytest never double-collects the
same tests from both the old and new location.

Verify the new location collects correctly:
    pytest tests/common/test_segmentation_flow.py --collect-only -q

Then delete this file (tests/test_segmentation_flow.py) — it serves no further purpose.
"""
