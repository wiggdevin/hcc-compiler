"""Deterministic tag-tightener tests."""
from scripts.curation.tighten_tags import (
    extract_age,
    extract_duration,
    extract_sex,
    extract_training_status,
    find_record,
    is_vague,
)


# ---- is_vague ------------------------------------------------------------

def test_is_vague_exact_match_only():
    assert is_vague("unspecified") is True
    assert is_vague("not specified") is True
    assert is_vague("  Varied  ") is True
    assert is_vague("N/A") is True


def test_is_vague_skips_fields_with_content():
    """Fields carrying real content should be left alone."""
    assert is_vague("healthy individuals (RCTs restricted to healthy populations)") is False
    assert is_vague("varied across included trials; literature searched through September 2024") is False
    assert is_vague("18-30 years") is False
    assert is_vague(None) is False


# ---- extract_sex ---------------------------------------------------------

def test_sex_mixed_when_both_mentioned():
    text = "We recruited 24 men and 24 women aged 22-30 years for the trial."
    assert extract_sex(text) == "both"


def test_sex_female_only_with_repeated_mentions():
    text = "Twenty-three women aged 18-35 completed the study. All female participants were premenopausal."
    assert extract_sex(text) == "female"


def test_sex_male_only_with_repeated_mentions():
    text = "Twelve male participants completed the trial. All men were resistance-trained."
    assert extract_sex(text) == "male"


def test_sex_returns_none_when_no_clear_signal():
    text = "The study examined the effects of supplementation on performance outcomes."
    assert extract_sex(text) is None


# ---- extract_training_status --------------------------------------------

def test_training_status_elite_athletes():
    assert extract_training_status(
        "We studied 18 elite athletes from a national rugby squad."
    ) == "elite athletes"


def test_training_status_resistance_trained():
    assert extract_training_status(
        "Sixteen resistance-trained men with ≥2 years of consistent training."
    ) == "trained"


def test_training_status_sedentary():
    assert extract_training_status(
        "Twenty sedentary adults aged 50-65 were randomized to either group."
    ) == "sedentary"


def test_training_status_recreational():
    assert extract_training_status(
        "Recreationally active individuals completed an 8-week intervention."
    ) == "recreational"


def test_training_status_returns_none_on_silence():
    assert extract_training_status("Effects of caffeine on cognition.") is None


def test_training_status_more_specific_label_wins():
    """When both 'elite athletes' and 'trained men' appear, elite athletes wins (more specific)."""
    text = "Eighteen elite athletes (12 trained men, 6 trained women) competing at national level."
    assert extract_training_status(text) == "elite athletes"


# ---- extract_age ---------------------------------------------------------

def test_age_explicit_range():
    assert extract_age("Participants aged 22-30 years were enrolled.") == "22-30 years"


def test_age_gte():
    assert extract_age("All subjects were aged ≥65.") == "≥65 years"


def test_age_older_adults_fallback():
    assert extract_age("Older adults completed a 12-week protocol.") == "older adults"


def test_age_returns_none_on_silence():
    assert extract_age("Effects of caffeine on resistance performance.") is None


def test_age_range_without_years_suffix():
    """Common in abstracts: 'adolescents aged 11-17' with no 'years' suffix."""
    assert extract_age("Adolescents aged 11-17 do not meet activity guidelines.") == "11-17 years"


def test_age_range_filters_implausible_numbers():
    """Don't match 'aged 1-5 servings' as an age range."""
    assert extract_age("Participants consumed aged 1-5 servings per day.") is None


# ---- extract_duration ---------------------------------------------------

def test_duration_weeks_with_context():
    assert extract_duration("Subjects completed an 8-week supplementation period.") == "8 weeks"


def test_duration_picks_longest_when_multiple():
    """Studies often mention multiple windows (4-week baseline + 12-week intervention) — take the longest."""
    assert extract_duration("A 4-week baseline preceded the 12-week training intervention.") == "12 weeks"


def test_duration_filters_absurd_short_or_long():
    """1-week is too short to count; 200-weeks is noise."""
    assert extract_duration("After a 1-week run-in, subjects completed the 200-week wash-out.") is None


def test_duration_acute_intake():
    assert extract_duration("Subjects ingested an acute dose of caffeine 60 minutes pre-exercise.") == "acute"


def test_duration_returns_none_on_silence():
    assert extract_duration("Effects of supplementation on performance outcomes.") is None


def test_duration_weeks_without_trailing_context():
    """Studies often end the duration mention with punctuation, not a context word."""
    assert extract_duration("Subjects trained for 8 weeks.") == "8 weeks"


# ---- find_record ---------------------------------------------------------

def test_find_record_by_doi():
    atom = {"citations": [{"id": "10.1234/abc"}]}
    index = {"10.1234/abc": {"abstract": "match", "doi": "10.1234/abc"}}
    assert find_record(atom, index) == {"abstract": "match", "doi": "10.1234/abc"}


def test_find_record_by_pmid():
    atom = {"citations": [{"id": "12345678"}]}
    index = {"12345678": {"abstract": "match", "pmid": "12345678"}}
    assert find_record(atom, index) == {"abstract": "match", "pmid": "12345678"}


def test_find_record_returns_none_when_no_citation_match():
    atom = {"citations": [{"id": "10.999/zzz"}]}
    index = {"10.1234/abc": {"abstract": "no match"}}
    assert find_record(atom, index) is None


def test_find_record_with_empty_citations():
    assert find_record({"citations": []}, {}) is None
    assert find_record({}, {}) is None
