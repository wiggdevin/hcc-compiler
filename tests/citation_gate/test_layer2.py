from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.layer2 import verify_faithfulness


def _cite(quote: str) -> Citation:
    return Citation(
        id="10.1186/s12970-017-0177-8",
        locator_quote=quote,
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="ISSN Position Stand: protein and exercise",
    )


SOURCE = (
    "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of "
    "lean body mass in resistance-trained subjects during hypocaloric periods."
)


def test_verified_when_quote_in_source_and_numbers_match():
    quote = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed"
    claim = "Protein intakes of 2.3-3.1 g/kg/day may be needed"
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "VERIFIED"


def test_unsupported_when_quote_not_in_source():
    quote = "completely different sentence not present anywhere"
    claim = "Protein intakes of 2.3-3.1 g/kg/day may be needed"
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "UNSUPPORTED"


def test_major_distortion_when_claim_number_off():
    quote = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed"
    claim = "Protein intakes of 5.0 g/kg/day may be needed"  # wildly different
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "MAJOR_DISTORTION"


def test_access_limited_when_source_text_none():
    quote = "Higher protein intakes"
    assert verify_faithfulness("anything", _cite(quote), source_text=None) == "ACCESS_LIMITED"
