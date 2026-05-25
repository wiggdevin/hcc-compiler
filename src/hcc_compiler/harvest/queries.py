from __future__ import annotations
import os
from urllib.parse import urlencode

from hcc_compiler.citation_gate.lookup import _get_json

DOMAIN_QUERIES: dict[str, list[str]] = {
    "nutrition": [
        '("protein intake" OR "dietary proteins"[MeSH]) AND ("resistance training" OR athletes) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("energy deficit" OR "caloric restriction") AND ("lean body mass" OR "fat-free mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("menstrual cycle" OR "luteal phase" OR "follicular phase") AND ("female athletes" OR "nutritional periodization" OR women) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("diet break" OR refeed OR "metabolic adaptation") AND ("body composition" OR "fat loss" OR "weight loss") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("protein distribution" OR "leucine threshold" OR "meal timing") AND ("muscle protein synthesis" OR MPS OR hypertrophy) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(hydration OR "fluid balance" OR "sodium intake" OR electrolyte) AND ("athletic performance" OR exercise OR training) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("post-exercise nutrition" OR "anabolic window" OR "post-workout recovery") AND ("muscle protein synthesis" OR glycogen OR resynthesis) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("plant-based protein" OR vegan OR vegetarian) AND ("resistance training" OR athletes OR "lean body mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("carbohydrate periodization" OR "train low" OR "carbohydrate timing") AND (performance OR endurance OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(("iron deficiency" OR ferritin) OR ("vitamin D status" OR "micronutrient status")) AND athletes AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(MASLD OR "non-alcoholic fatty liver" OR NAFLD) AND (diet OR nutrition OR "weight loss") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("chronic kidney disease" OR CKD) AND ("protein intake" OR "dietary intervention") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "supplements": [
        '(creatine[MeSH] OR "creatine monohydrate") AND ("athletic performance" OR "exercise") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(caffeine[MeSH] OR "caffeine supplementation") AND ("athletic performance" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("beta-alanine"[MeSH] OR "β-alanine") AND ("athletic performance" OR exercise OR "high-intensity") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(citrulline OR "L-citrulline" OR "citrulline malate") AND ("athletic performance" OR "exercise performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("omega-3"[MeSH] OR EPA OR DHA OR "fish oil") AND ("muscle recovery" OR inflammation OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("vitamin D"[MeSH] OR "vitamin D supplementation") AND (athletes OR "muscle function" OR "exercise performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(("whey protein" OR "casein protein") OR "milk protein") AND ("muscle protein synthesis" OR "lean body mass" OR hypertrophy) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(magnesium[MeSH] OR "magnesium supplementation") AND ("muscle function" OR "exercise recovery" OR athletes) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("sodium bicarbonate" OR "buffering agents") AND ("high-intensity exercise" OR "anaerobic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("pre-workout supplement" OR "multi-ingredient supplement") AND ("exercise performance" OR strength OR power) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '((tribulus OR fenugreek OR ashwagandha) OR "herbal supplement") AND (testosterone OR "athletic performance" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(HMB OR "β-hydroxy-β-methylbutyrate" OR "leucine metabolite") AND ("muscle protein" OR "lean mass" OR "resistance training") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "training": [
        '("resistance training"[MeSH] OR "strength training") AND (hypertrophy OR "lean body mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("training volume" OR "weekly sets") AND ("muscle hypertrophy" OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(deload OR "fatigue management" OR "training periodization") AND ("resistance training" OR athletes OR recovery) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(novice OR "untrained adults" OR beginner) AND ("resistance training" OR "strength training" OR "progressive overload") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("older adults"[MeSH] OR sarcopenia OR "frail older adults") AND ("resistance training" OR "muscle strength" OR "muscle mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("female athletes" OR women OR "female cohort") AND ("resistance training" OR "muscle hypertrophy" OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("velocity-based training" OR VBT OR "bar velocity") AND ("strength training" OR "power training") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("return to sport" OR "return to training" OR "post-injury rehabilitation") AND ("resistance training" OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(tendinopathy OR "patellofemoral pain" OR "Achilles tendinopathy") AND ("eccentric exercise" OR "isometric loading" OR strengthening) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("low back pain" OR lumbar OR "spinal stability") AND ("resistance training" OR "strength training" OR "core stability") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("bodyweight exercise" OR calisthenics OR "minimal equipment") AND ("muscle strength" OR hypertrophy) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("concurrent training" OR "concurrent endurance and resistance") AND (strength OR hypertrophy OR "interference effect") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "conditioning": [
        '("endurance training" OR "aerobic exercise"[MeSH]) AND ("VO2 max" OR "cardiorespiratory fitness") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("high-intensity interval training"[MeSH] OR HIIT) AND ("aerobic capacity" OR "endurance performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("zone 2" OR "aerobic base" OR "low-intensity endurance") AND (mitochondrial OR "fat oxidation" OR "aerobic capacity") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("sprint interval training" OR SIT OR "repeated sprint") AND ("aerobic capacity" OR "anaerobic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("polarized training" OR "training intensity distribution") AND (endurance OR "VO2 max" OR performance) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("running economy" OR "running performance" OR marathon) AND (training OR "endurance training") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(cycling OR "cycling performance") AND (training OR "power output" OR "endurance training") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("cardiac rehabilitation" OR "coronary artery disease") AND ("high-intensity interval training" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("hybrid athletes" OR "concurrent endurance and strength" OR "mixed training") AND (performance OR capacity OR adaptation) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("loaded carry" OR "sled push" OR "weighted vest") AND (conditioning OR "metabolic conditioning" OR "athletic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "recovery": [
        '("sleep"[MeSH] OR "sleep quality") AND (athletes OR "athletic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("cold water immersion" OR "cryotherapy"[MeSH] OR sauna) AND ("muscle recovery" OR "exercise recovery") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(sauna OR "heat acclimation" OR "passive heat") AND ("muscle recovery" OR "cardiovascular health" OR "athletic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(("sports massage" OR "foam rolling") OR "self-myofascial release") AND ("muscle soreness" OR recovery OR "delayed onset") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("active recovery" OR "low-intensity recovery") AND ("lactate clearance" OR "muscle damage" OR "perceived recovery") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("compression garments" OR "compression therapy") AND ("muscle recovery" OR "delayed onset muscle soreness" OR DOMS) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("heart rate variability" OR "autonomic recovery" OR HRV) AND ("training load" OR overtraining OR athletes) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("sleep duration" OR "sleep extension" OR "sleep deprivation") AND (athletes OR "athletic performance" OR "exercise performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(photobiomodulation OR "red light therapy" OR "low-level laser") AND ("muscle recovery" OR performance OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(("overtraining syndrome" OR "non-functional overreaching") OR "burnout in athletes") AND (recovery OR "training load") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "behavioral": [
        '("exercise adherence" OR "physical activity adherence") AND ("behavior change" OR motivation) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("goal setting" OR "self-monitoring" OR "habit formation") AND ("physical activity" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("habit formation" OR automaticity OR "cue-routine-reward") AND ("physical activity" OR "exercise behavior") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(("digital health coaching" OR mHealth OR "smartphone app")) AND ("physical activity" OR "exercise adherence") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(mindfulness OR "stress reduction" OR meditation) AND (athletes OR "exercise performance" OR "physical activity") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("autonomy support" OR "self-determination theory") AND ("physical activity" OR exercise OR adherence) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("group exercise" OR "social support" OR "exercise buddy") AND (adherence OR motivation OR retention) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("implementation intentions" OR "if-then planning") AND ("physical activity" OR "behavior change") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("coaching frequency" OR "personal training" OR "supervised exercise") AND (adherence OR outcomes OR retention) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("body image" OR "exercise dependence" OR "RED-S" OR "relative energy deficiency in sport") AND athletes AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
}


def build_query(base: str, since: int) -> str:
    return f'({base}) AND ("{since}"[dp]:"2030"[dp])'


def _email() -> str:
    return os.environ.get("HCC_CONTACT_EMAIL", "devin@zerosumsolutions.com")


def _esearch(query: str) -> list[str]:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
        + urlencode({"db": "pubmed", "term": query, "retmode": "json",
                     "retmax": "20", "tool": "hcc-compiler", "email": _email()})
    )
    data = _get_json(url)
    return data.get("esearchresult", {}).get("idlist", [])


def _summary(pmid: str) -> dict:
    from hcc_compiler.citation_gate.lookup import fetch_pubmed_abstract, fetch_pubmed_by_pmid
    r = fetch_pubmed_by_pmid(pmid)
    abstract = fetch_pubmed_abstract(pmid)
    return {
        "pmid": pmid, "doi": r.doi, "title": r.title,
        "year": r.year, "journal": r.journal, "abstract": abstract,
    }


def run_harvest(domain: str, since: int) -> list[dict]:
    queries = DOMAIN_QUERIES[domain]
    seen: set[str] = set()
    out: list[dict] = []
    for base in queries:
        for pmid in _esearch(build_query(base, since)):
            if pmid in seen:
                continue
            seen.add(pmid)
            out.append(_summary(pmid))
    return out
