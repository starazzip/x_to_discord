"""Unit tests for translate_en_to_zh_tw_ultra."""

import os
import unittest
from unittest.mock import patch

from app.translate_ultra import translate_en_to_zh_tw_ultra


class TranslateUltraTests(unittest.TestCase):
    def test_returns_original_for_blank_text(self):
        with patch("app.translate_ultra._translate_once") as mock_translate:
            result = translate_en_to_zh_tw_ultra("   ")
        self.assertEqual(result, "   ")
        mock_translate.assert_not_called()

    def test_single_chunk_translation(self):
        with patch("app.translate_ultra._translate_once", return_value="translated") as mock_translate:
            result = translate_en_to_zh_tw_ultra("Hello")
        self.assertEqual(result, "translated")
        mock_translate.assert_called_once_with("Hello")

    def test_chunking_respects_limit_and_whitespace(self):
        text = "Hello world"
        with patch.dict(os.environ, {"ULTRA_FREE_LIMIT": "3"}):
            with patch("app.translate_ultra._translate_once", side_effect=["T1", "T2", "T3", "T4"]) as mock_translate:
                result = translate_en_to_zh_tw_ultra(text)
        self.assertEqual(result, "T1T2 T3T4")
        called_with = [call.args[0] for call in mock_translate.call_args_list]
        self.assertEqual(called_with, ["Hel", "lo", "wor", "ld"])

    def test_returns_original_when_translation_missing(self):
        with patch("app.translate_ultra._translate_once", return_value=None):
            result = translate_en_to_zh_tw_ultra("Hello")
        self.assertEqual(result, "Hello")

    def test_limit_is_capped_at_default(self):
        text = "a" * 500
        with patch.dict(os.environ, {"ULTRA_FREE_LIMIT": "1000"}):
            with patch("app.translate_ultra._translate_once", side_effect=["X", "Y"]) as mock_translate:
                result = translate_en_to_zh_tw_ultra(text)
        first_chunk = mock_translate.call_args_list[0].args[0]
        second_chunk = mock_translate.call_args_list[1].args[0]
        self.assertEqual(len(first_chunk), 400)
        self.assertEqual(len(second_chunk), 100)
        self.assertEqual(result, "XY")


if __name__ == "__main__":
    unittest.main()
