"""
test_sms_webengage_dlr.py (MOVED)

This test was relocated to tests/sms/api/test_sms_webengage_dlr.py.

It needs the api_client/test_data/env_config fixtures and the --env CLI
flag, all registered by tests/sms/api/conftest.py -- pytest only loads a
conftest's fixtures/options for paths actually on the collection path,
so those weren't available here. A real run against this file's original
location failed at fixture setup with "fixture 'api_client' not found".

No tests remain in this file. See tests/sms/api/test_sms_webengage_dlr.py
for the current, working version.
"""
