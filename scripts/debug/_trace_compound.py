"""Trace exactly why وزارة المالية fails in the backend pipeline."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from translation_api.services.lexicon_input import normalize_gloss_input, has_arabic
from translation_api.services.nlp_pipeline import preprocess_arabic_text, align_tokens_to_lexicon
from translation_api.services.search_service import get_all_known_lemmas, execute_hybrid_search
from translation_api.services.lemma_cache import is_known_compound, contains_exact_lexicon_phrase

input_text = "وزارة المالية"
print(f"=== Tracing pipeline for: '{input_text}' ===")

# Step 1: Normalize
normalized = normalize_gloss_input(input_text)
print(f"\n1. normalize_gloss_input: '{normalized}'")

# Step 2: Check compounds
print(f"\n2. is_known_compound('{normalized}'): {is_known_compound(normalized)}")
print(f"   contains_exact_lexicon_phrase('{normalized}'): {contains_exact_lexicon_phrase(normalized)}")

# Step 3: Preprocess
tokens = preprocess_arabic_text(normalized)
print(f"\n3. preprocess_arabic_text: {tokens}")

# Step 4: Get known lemmas
known_lemmas = get_all_known_lemmas()
print(f"\n4. Known lemmas count: {len(known_lemmas)}")
is_in_known = "وزارة المالية" in known_lemmas
print(f"   'وزارة المالية' in known_lemmas: {is_in_known}")
# Check what known_lemmas look like for وزارة
wazara_lemmas = [l for l in known_lemmas if "وزارة" in l]
print(f"   Known lemmas containing وزارة: {wazara_lemmas}")

# Step 5: Align tokens
aligned = align_tokens_to_lexicon(tokens, known_lemmas)
print(f"\n5. align_tokens_to_lexicon: {aligned}")

# Step 6: Try compound prescan
from translation_api.services.embedding_service import get_embedding_service
embedding_service = get_embedding_service()
query_embedding = embedding_service.embed_query(normalized)

from translation_api.views import _try_compound_prescan_pipeline, _greedy_compound_spans
from django.conf import settings

spans = _greedy_compound_spans(normalized)
print(f"\n6. _greedy_compound_spans: {spans}")

compound_hit = _try_compound_prescan_pipeline(normalized, query_embedding, settings.T2S_SIMILARITY_THRESHOLD)
print(f"   _try_compound_prescan_pipeline result: {compound_hit}")

# Step 7: Direct hybrid search
print(f"\n7. Direct hybrid search (per_token=False):")
results = execute_hybrid_search(
    lemmas=[normalized],
    phrase=normalized,
    embedding=query_embedding,
    threshold=settings.T2S_SIMILARITY_THRESHOLD,
    per_token_mode=False,
)
for r in results:
    print(f"   {r}")

print(f"\n8. Direct hybrid search (per_token=True):")
results2 = execute_hybrid_search(
    lemmas=aligned if aligned else tokens,
    phrase=normalized,
    embedding=query_embedding,
    threshold=settings.T2S_SIMILARITY_THRESHOLD,
    per_token_mode=True,
)
for r in results2:
    print(f"   {r}")
