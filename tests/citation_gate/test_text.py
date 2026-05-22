from hcc_compiler.citation_gate.text import title_similarity, normalize_title


def test_identical_titles_score_one():
    assert title_similarity("Foo Bar", "Foo Bar") == 1.0


def test_casing_and_punctuation_ignored():
    a = "Dose-response relationship between RT volume and hypertrophy."
    b = "dose response relationship between rt volume and hypertrophy"
    assert title_similarity(a, b) >= 0.95


def test_minor_word_difference_above_threshold():
    # Trailing period + subtitle truncation are typical citation drift; should clear the 0.70 gate.
    a = "Dose-response relationship between weekly resistance training volume and increases in muscle mass: a systematic review and meta-analysis."
    b = "Dose-response relationship between weekly resistance training volume and increases in muscle mass"
    assert title_similarity(a, b) >= 0.70


def test_unrelated_titles_below_threshold():
    a = "Effects of creatine supplementation on muscle"
    b = "Quantum entanglement in superconductors"
    assert title_similarity(a, b) < 0.50


def test_normalize_strips_punctuation_and_lowercases():
    assert normalize_title("Foo, Bar! Baz?") == "foo bar baz"
