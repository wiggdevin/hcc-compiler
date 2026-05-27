"""Deterministic evidence-level reclassifier tests."""
from scripts.curation.regrade_atoms import classify_atom, classify_title


def test_systematic_review_is_L1():
    assert classify_title(
        "Comparing exercise modalities during caloric restriction: "
        "a systematic review and network meta-analysis on body composition"
    ) == "L1"


def test_meta_analysis_alone_is_L1():
    assert classify_title("Caffeine and resistance exercise: a meta-analysis") == "L1"


def test_meta_analytic_review_is_L1():
    assert classify_title("Caffeine mouth rinse: a meta-analytic review") == "L1"


def test_meta_regression_is_L1():
    assert classify_title("Resistance training dose response: meta-regressions of volume") == "L1"


def test_meta_synthesis_is_L1():
    assert classify_title("Rehab adherence: a qualitative meta-synthesis") == "L1"


def test_pooled_analysis_is_L1():
    assert classify_title("Beta-alanine: a pooled analysis of 9 trials") == "L1"


def test_randomized_controlled_trial_is_L2():
    assert classify_title(
        "Creatine monohydrate supplementation in trained men: a randomized controlled trial"
    ) == "L2"


def test_cohort_is_L3():
    assert classify_title(
        "Long-term protein intake and renal function: a prospective cohort study"
    ) == "L3"


def test_case_report_is_L4():
    assert classify_title("Rhabdomyolysis after creatine loading: a case report") == "L4"


def test_no_taxonomy_match_returns_none():
    assert classify_title("Effects of dietary nitrate on performance") is None
    assert classify_title("") is None


def test_l1_keywords_take_precedence_over_l2():
    """A review of RCTs is still a systematic review (L1), not an RCT (L2)."""
    assert classify_title(
        "Effects of beta-alanine: a systematic review of randomized controlled trials"
    ) == "L1"


def test_l2_beats_l3_when_both_present():
    """A randomized trial nested inside a longitudinal study is still an RCT."""
    assert classify_title(
        "A longitudinal randomized clinical trial of vitamin D in athletes"
    ) == "L2"


def test_atom_takes_strongest_grade_across_citations():
    """An atom backed by an SR + an RCT is as strong as the SR."""
    atom = {
        "citations": [
            {"cited_title": "Single-blind randomized trial of caffeine"},
            {"cited_title": "Caffeine: a systematic review and meta-analysis"},
        ]
    }
    assert classify_atom(atom) == "L1"


def test_atom_with_only_observational_citations_is_l3():
    atom = {
        "citations": [
            {"cited_title": "Protein intake and mortality: a prospective cohort"},
            {"cited_title": "Diet quality: a cross-sectional analysis"},
        ]
    }
    assert classify_atom(atom) == "L3"


def test_atom_with_no_signal_returns_none():
    """Caller (the script) preserves the existing grade rather than downgrading."""
    atom = {"citations": [{"cited_title": "Effects of training"}]}
    assert classify_atom(atom) is None


def test_atom_with_empty_citations_returns_none():
    assert classify_atom({"citations": []}) is None
    assert classify_atom({}) is None
