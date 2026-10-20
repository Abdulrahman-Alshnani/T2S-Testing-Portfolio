"""Verify the _enforce_exact_lexicon_hit fix for compounds."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from translation_api.views import _enforce_exact_lexicon_hit
from translation_api.services.search_service import get_all_known_lemmas

known_lemmas = get_all_known_lemmas()

# Simulate the compound prescan result for "وزارة المالية"
compound_result = [{
    'sequence_order': 1,
    'matched_lemma': 'وزارة المالية',
    'storage_url': 'https://example.com/Ministry%20of%20Finance.mp4',
    'match_type': 'compound',
    'confidence': 1.0,
    'gloss_id': 'GLOSS_MINISTRY_OF_FINANCE',
}]

fixed = _enforce_exact_lexicon_hit(['وزارة المالية'], compound_result, known_lemmas)
print("Result after fix:")
for r in fixed:
    print(f"  lemma={r['matched_lemma']} type={r['match_type']} url={bool(r.get('storage_url'))}")

assert fixed[0]['match_type'] == 'compound', "FAILED: compound still rejected!"
assert fixed[0]['storage_url'] is not None, "FAILED: storage_url is None!"
print("\nPASSED: compound match is correctly accepted!")
