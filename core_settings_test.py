"""
Test-specific Django settings for the T2S backend.

Uses the same Supabase Mumbai database as development. Test rows are isolated
via category='__test__' and cleaned up automatically after each test.
"""

from core.settings import *  # noqa: F401, F403

TEST_DATA_CATEGORY = "__test__"
TEST_LEMMA_PREFIX = "test_"

LOGGING["loggers"]["translation_api"]["level"] = "WARNING"  # noqa: F405

DATABASES["default"]["OPTIONS"]["options"] = "-c statement_timeout=5000"  # noqa: F405
DATABASES["default"]["TEST"] = {  # noqa: F405
    "MIRROR": "default",
}

import os  # noqa: E402

T2S_TEST_USE_MOCK_EMBEDDING = os.environ.get("T2S_TEST_USE_MOCK_EMBEDDING", "0") == "1"
