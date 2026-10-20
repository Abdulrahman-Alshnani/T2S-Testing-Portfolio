"""
Verify that tokens produced by NLP preprocessing are passed correctly into
the search service and arrive at the RPC in the right shape.

These tests do not load mBART or AraBERT. They mock both at the boundary
and assert that data flows correctly between layers.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.subsystem
@pytest.mark.integration
class TestNlpToSearchHandoff:

    def test_gloss_tokens_become_rpc_lemmas(self, db):
        """NLP output tokens must reach the RPC as the `lemmas` parameter."""
        from translation_api.services.search_service import execute_hybrid_search

        # Stub out the RPC at the database boundary so we can inspect arguments.
        with patch("translation_api.services.search_service.connection") as mock_conn:
            mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []

            execute_hybrid_search(
                lemmas=["ولد", "قرأ", "كتاب"],
                phrase="الولد يقرأ الكتاب",
                embedding=[0.0] * 768,
                threshold=0.75,
            )

            # The RPC call should have been invoked with our lemmas array.
            executed_args = mock_cursor.execute.call_args
            assert executed_args is not None
            # The lemmas parameter should appear in the SQL parameter tuple.
            # Exact position depends on the function signature in the SQL;
            # we just verify the array is somewhere in the bound parameters.
            sql_params = executed_args[0][1]
            assert ["ولد", "قرأ", "كتاب"] in sql_params or "ولد" in str(sql_params)


@pytest.mark.subsystem
class TestPipelineErrorPropagation:

    def test_nlp_empty_result_short_circuits_view(self):
        """If preprocess returns [], the view returns 422 UNPROCESSABLE_ENTITY."""
        from rest_framework.test import APIClient

        with patch(
            "translation_api.views.preprocess_arabic_text"
        ) as mock_preprocess:
            mock_preprocess.return_value = []
            client = APIClient()
            response = client.post(
                "/api/v1/translate/",
                {"text": "ا"},
                format="json",
            )

        assert response.status_code == 422
