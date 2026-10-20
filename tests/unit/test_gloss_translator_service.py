"""Unit tests for GlossTranslator — verifies mBART output shape and bypass logic."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.conf import settings

from translation_api.services import gloss_translator
from translation_api.services.gloss_translator import (
    _get_model,
    gloss_to_words,
    translate_to_gloss,
)

_MODULE = "translation_api.services.gloss_translator"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class FakeBatchEncoding(dict):
    def to(self, device):
        self.moved_to = device
        return self


def _reset_module_cache():
    gloss_translator._tokenizer = None
    gloss_translator._model = None
    gloss_translator._device = None


def _build_fake_tokenizer_model(decoded_text="ولد قرأ كتاب"):
    encoding = FakeBatchEncoding(
        input_ids=MagicMock(name="input_ids"),
        attention_mask=MagicMock(name="attention_mask"),
    )
    tokenizer = MagicMock(name="tokenizer")
    tokenizer.return_value = encoding
    tokenizer.convert_tokens_to_ids.return_value = 250_001
    tokenizer.batch_decode.return_value = [decoded_text]
    model = MagicMock(name="model")
    model.generate.return_value = MagicMock(name="output_ids")
    device = MagicMock(name="device")
    return tokenizer, model, device, encoding


class TestGlossToWords(unittest.TestCase):
    def test_basic_three_words(self):
        self.assertEqual(gloss_to_words("ولد قرأ كتاب"), ["ولد", "قرأ", "كتاب"])

    def test_extra_spaces_yields_no_empty_tokens(self):
        result = gloss_to_words("   ولد   قرأ    كتاب   ")
        self.assertEqual(result, ["ولد", "قرأ", "كتاب"])
        self.assertNotIn("", result)

    def test_empty_string_returns_empty_list(self):
        self.assertEqual(gloss_to_words(""), [])

    def test_only_whitespace_returns_empty_list(self):
        self.assertEqual(gloss_to_words("   \t  \n "), [])

    def test_none_is_handled_gracefully(self):
        self.assertEqual(gloss_to_words(None), [])

    def test_order_is_preserved(self):
        self.assertEqual(gloss_to_words("أ ب ج د"), ["أ", "ب", "ج", "د"])


class TestTranslateToGlossMocked(unittest.TestCase):
    def setUp(self):
        _reset_module_cache()

    def tearDown(self):
        _reset_module_cache()

    def test_returns_decoded_gloss_string(self):
        tokenizer, model, device, _ = _build_fake_tokenizer_model("ولد قرأ كتاب")
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            result = translate_to_gloss("الولد يقرأ الكتاب")
        self.assertEqual(result, "ولد قرأ كتاب")

    def test_src_lang_is_set_to_ar_AR(self):
        tokenizer, model, device, _ = _build_fake_tokenizer_model()
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            translate_to_gloss("جملة عربية")
        self.assertEqual(tokenizer.src_lang, "ar_AR")

    def test_forced_bos_token_id_uses_ar_AR(self):
        tokenizer, model, device, _ = _build_fake_tokenizer_model()
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            translate_to_gloss("جملة")
        tokenizer.convert_tokens_to_ids.assert_called_with("ar_AR")

    def test_generate_receives_expected_kwargs(self):
        tokenizer, model, device, _ = _build_fake_tokenizer_model()
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            translate_to_gloss("اختبار")
        kwargs = model.generate.call_args.kwargs
        self.assertEqual(kwargs.get("max_length"), gloss_translator.MAX_LEN)
        self.assertEqual(kwargs.get("num_beams"), gloss_translator.NUM_BEAMS)

    def test_encoding_moved_to_device(self):
        tokenizer, model, device, encoding = _build_fake_tokenizer_model()
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            translate_to_gloss("جملة")
        self.assertEqual(getattr(encoding, "moved_to", None), device)

    def test_output_is_stripped(self):
        tokenizer, model, device, _ = _build_fake_tokenizer_model("   ولد قرأ كتاب   ")
        with patch(f"{_MODULE}._get_model", return_value=(tokenizer, model, device)):
            result = translate_to_gloss("الولد يقرأ الكتاب")
        self.assertEqual(result, "ولد قرأ كتاب")

    def test_empty_input_short_circuits_without_model(self):
        with patch(f"{_MODULE}._get_model") as get_model_mock:
            self.assertEqual(translate_to_gloss(""), "")
            self.assertEqual(translate_to_gloss("   "), "")
            self.assertEqual(translate_to_gloss(None), "")
        get_model_mock.assert_not_called()


class TestModelLoadedOnce(unittest.TestCase):
    def setUp(self):
        _reset_module_cache()

    def tearDown(self):
        _reset_module_cache()

    def test_from_pretrained_called_only_once_across_two_calls(self):
        fake_tokenizer = MagicMock(name="cached_tokenizer")
        fake_model = MagicMock(name="cached_model")
        fake_model.to.return_value = fake_model
        fake_model.eval.return_value = fake_model

        with tempfile.TemporaryDirectory() as tmp_model_dir, patch.object(
            settings, "T2S_MBART_MODEL_PATH", tmp_model_dir
        ), patch(
            f"{_MODULE}.MBart50TokenizerFast.from_pretrained",
            return_value=fake_tokenizer,
        ) as tok_from_pretrained, patch(
            f"{_MODULE}.MBartForConditionalGeneration.from_pretrained",
            return_value=fake_model,
        ) as model_from_pretrained:
            t1, m1, d1 = _get_model()
            t2, m2, d2 = _get_model()

        self.assertEqual(tok_from_pretrained.call_count, 1)
        self.assertEqual(model_from_pretrained.call_count, 1)
        self.assertIs(t1, t2)
        self.assertIs(m1, m2)
        self.assertIs(d1, d2)


class TestMissingModelFolder(unittest.TestCase):
    def setUp(self):
        _reset_module_cache()

    def tearDown(self):
        _reset_module_cache()

    def test_missing_folder_raises_filenotfounderror(self):
        bogus_path = str(
            Path(tempfile.gettempdir()) / "definitely_not_a_real_model_dir_t2s_xyz_98765"
        )
        self.assertFalse(Path(bogus_path).exists())

        with patch.object(settings, "T2S_MBART_MODEL_PATH", bogus_path):
            with self.assertRaises(FileNotFoundError) as ctx:
                _get_model()

        self.assertIn("mBART", str(ctx.exception))
        self.assertIn(bogus_path, str(ctx.exception))


_MODEL_DIR = Path(settings.T2S_MBART_MODEL_PATH)


class TestLiveTranslation(unittest.TestCase):
    @unittest.skipUnless(_MODEL_DIR.is_dir(), "model folder missing, skipping live test")
    def test_live_translation_basic_sentence(self):
        out = translate_to_gloss("الولد يقرأ الكتاب")
        self.assertIsInstance(out, str)
        self.assertTrue(out)
        self.assertIn("ولد", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
