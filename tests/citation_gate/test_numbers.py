from hcc_compiler.citation_gate.text import numbers_match, extract_numbers


def test_scalar_within_relative_tolerance():
    assert numbers_match(300.0, 300.0)
    assert numbers_match(305.0, 300.0)        # within 5% rel-tol
    assert not numbers_match(400.0, 300.0)    # outside


def test_range_membership_with_margin():
    assert numbers_match(2800.0, (2750.0, 2850.0))
    assert numbers_match(2750.0, (2750.0, 2850.0))
    assert not numbers_match(2000.0, (2750.0, 2850.0))


def test_percentage_mismatch_rejected():
    # spec example: "40% carbs" vs source "25%" — MAJOR
    assert not numbers_match(40.0, 25.0)


def test_extract_numbers_finds_floats_and_ints():
    assert extract_numbers("dose 2.5 g/kg/day for 12 weeks") == [2.5, 12.0]
    assert extract_numbers("no numbers here") == []


def test_extract_numbers_handles_ranges_and_commas():
    nums = extract_numbers("intake 2,800 kcal across 1.6-2.2 g/kg/d")
    # Range "1.6-2.2" yields both endpoints; thousands separators handled.
    assert 2800.0 in nums
    assert 1.6 in nums
    assert 2.2 in nums


def test_extract_numbers_detects_english_number_words():
    nums = extract_numbers("three times per week at one-repetition maximum")
    assert 3.0 in nums
    assert 1.0 in nums


def test_extract_numbers_number_words_with_digits():
    nums = extract_numbers("three sessions at 60-80% of one-repetition maximum")
    assert 3.0 in nums
    assert 60.0 in nums
    assert 80.0 in nums
    assert 1.0 in nums


def test_extract_numbers_word_boundary_avoids_substrings():
    # 'one' inside 'bone' or 'stone' must not match
    assert extract_numbers("bone density stone fruit") == []
