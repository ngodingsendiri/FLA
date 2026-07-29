"""Unit tests untuk src/utils.py"""
import sys
from pathlib import Path

# Tambah src/ ke sys.path agar bisa import langsung
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import generate_toc, get_human_limits, get_model_name, provider_meta


class TestGetModelName:
    def test_known_model_returns_friendly_name(self):
        name = get_model_name("gemma2-9b-it")
        assert name == "Gemma 2 9B Instruct"

    def test_unknown_model_returns_id(self):
        name = get_model_name("some-unknown-model-xyz")
        assert name == "some-unknown-model-xyz"

    def test_case_insensitive_lookup(self):
        name = get_model_name("GEMMA2-9B-IT")
        assert name == "Gemma 2 9B Instruct"


class TestGetHumanLimits:
    def test_empty_model_returns_empty(self):
        assert get_human_limits(None) == ""
        assert get_human_limits({}) == ""

    def test_model_without_limits_key(self):
        assert get_human_limits({"id": "test"}) == ""

    def test_single_limit(self):
        model = {"limits": {"requests/day": 100}}
        result = get_human_limits(model)
        assert "100" in result
        assert "req/hari" in result

    def test_multiple_limits_joined(self):
        model = {"limits": {"requests/day": 50, "requests/minute": 20}}
        result = get_human_limits(model, separator=" | ")
        assert "|" in result

    def test_none_values_filtered(self):
        model = {"limits": {"requests/day": 100, "tokens/minute": None}}
        result = get_human_limits(model)
        assert "None" not in result
        assert "req/hari" in result

    def test_large_number_uses_dot_separator(self):
        model = {"limits": {"tokens/minute": 250000}}
        result = get_human_limits(model)
        # Indonesian formatting: 250.000 not 250,000
        assert "250.000" in result


class TestGenerateToc:
    def test_h2_heading_generates_entry(self):
        md = "# Judul Utama\n\n## Bagian Satu\n\nIsi konten."
        toc = generate_toc(md)
        assert "Bagian Satu" in toc
        assert "#bagian-satu" in toc

    def test_h3_indented(self):
        md = "## Parent\n\n### Child\n\nIsi."
        toc = generate_toc(md)
        lines = toc.split("\n")
        child_line = next(line for line in lines if "Child" in line)
        assert child_line.startswith("  -")

    def test_h1_ignored(self):
        md = "# Judul\n\n## Bagian"
        toc = generate_toc(md)
        assert "Judul" not in toc

    def test_empty_markdown(self):
        assert generate_toc("") == ""

    def test_special_chars_stripped_from_anchor(self):
        md = "## Provider: Groq (Cepat!)"
        toc = generate_toc(md)
        # Anchor should not contain : or !
        assert ":" not in toc.split("(#")[1]


class TestProviderMeta:
    def test_basic_output(self):
        result = provider_meta("🟢 Gratis")
        assert "**Jenis:** 🟢 Gratis" in result

    def test_with_batas_and_catatan(self):
        result = provider_meta("🟢 Gratis", batas="100 req/hari", catatan="Perlu verifikasi")
        assert "**Batas:** 100 req/hari" in result
        assert "**Catatan:** Perlu verifikasi" in result

    def test_none_catatan_not_included(self):
        result = provider_meta("🟢 Gratis", catatan=None)
        assert "Catatan" not in result
