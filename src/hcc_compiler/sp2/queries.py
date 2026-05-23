from __future__ import annotations

from hcc_compiler.models import Domain
from hcc_compiler.sp2.intake import ClientIntake

_CONDITIONING_GOALS = {"endurance", "weight_loss", "performance"}

_PER_DOMAIN_CAP = 5

_REGIMEN_KEYWORDS: dict[str, dict[Domain, list[str]]] = {
    "mediterranean": {
        Domain.NUTRITION: ["Mediterranean diet body composition trained adults"],
    },
    "kettlebell": {
        Domain.TRAINING: ["kettlebell strength programming"],
        Domain.CONDITIONING: ["kettlebell circuit conditioning"],
    },
    "peloton": {
        Domain.CONDITIONING: ["indoor cycling conditioning programming"],
    },
    "rower": {
        Domain.CONDITIONING: ["rowing ergometer interval conditioning"],
    },
    "hrv": {
        Domain.RECOVERY: ["HRV-guided recovery autoregulation"],
    },
    "yoga": {
        Domain.TRAINING: ["yoga mobility programming"],
        Domain.RECOVERY: ["yoga recovery active rest"],
    },
    "boxing": {
        Domain.CONDITIONING: ["boxing conditioning aerobic exposure"],
    },
    "smith machine": {
        Domain.TRAINING: ["Smith machine hypertrophy programming"],
    },
    "smith-machine": {
        Domain.TRAINING: ["Smith machine hypertrophy programming"],
    },
    "machine": {
        Domain.TRAINING: ["machine-based resistance training hypertrophy"],
    },
    "tempo": {
        Domain.TRAINING: ["tempo eccentric resistance training"],
    },
    "eccentric": {
        Domain.TRAINING: ["eccentric-emphasis hypertrophy programming"],
    },
    "neat": {
        Domain.BEHAVIORAL: ["NEAT step targets for sedentary adults"],
    },
    "chef": {
        Domain.NUTRITION: ["chef-prepared meal adherence weight management"],
        Domain.BEHAVIORAL: ["adherence with prepared-meal support"],
    },
    "meal prep": {
        Domain.NUTRITION: ["meal prep structure for adherence"],
        Domain.BEHAVIORAL: ["meal prep behavioral adherence"],
    },
    "trap-bar": {
        Domain.TRAINING: ["trap-bar deadlift hypertrophy low-back"],
    },
    "bulgarian split squat": {
        Domain.TRAINING: ["Bulgarian split squat unilateral hypertrophy"],
    },
    "front squat": {
        Domain.TRAINING: ["front squat hypertrophy axial loading"],
    },
    "ssb": {
        Domain.TRAINING: ["safety squat bar low-back-sparing squat"],
    },
    "landmine": {
        Domain.TRAINING: ["landmine press shoulder-friendly hypertrophy"],
    },
    "anti-rotation": {
        Domain.TRAINING: ["anti-rotation core training low-back"],
    },
    "luteal": {
        Domain.NUTRITION: ["luteal phase macronutrient adjustment trained females"],
    },
    "menstrual": {
        Domain.NUTRITION: ["menstrual cycle macros performance"],
    },
    "menstrual cycle": {
        Domain.NUTRITION: ["menstrual cycle nutrition periodization"],
    },
    "bmr": {
        Domain.NUTRITION: ["measured BMR-based caloric prescription"],
    },
    "hiit": {
        Domain.CONDITIONING: ["HIIT programming VO2max trained adults"],
    },
    "liss": {
        Domain.CONDITIONING: ["LISS aerobic base building trained adults"],
    },
    "treadmill": {
        Domain.CONDITIONING: ["treadmill HR-zone threshold prescription"],
    },
    "vt1": {
        Domain.CONDITIONING: ["VT1 ventilatory threshold zone-2 prescription"],
    },
    "vt2": {
        Domain.CONDITIONING: ["VT2 ventilatory threshold lactate threshold"],
    },
    "rmr": {
        Domain.NUTRITION: ["measured RMR-based caloric prescription"],
    },
    "ndt": {
        Domain.NUTRITION: ["NDT food-drug timing separation"],
    },
    "armour thyroid": {
        Domain.NUTRITION: ["Armour Thyroid food-drug timing"],
    },
    "post-lumbar-fusion": {
        Domain.TRAINING: ["post-lumbar-fusion training programming"],
    },
    "post-lumbar-spinal-fusion": {
        Domain.TRAINING: ["post-lumbar-fusion training programming"],
    },
    "spinal-fusion": {
        Domain.TRAINING: ["spinal fusion return-to-lifting programming"],
    },
    "spinal fusion": {
        Domain.TRAINING: ["spinal fusion return-to-lifting programming"],
    },
    "corrective": {
        Domain.TRAINING: ["corrective exercise low-back stability"],
    },
    "perimenopausal": {
        Domain.NUTRITION: ["perimenopausal nutrition body composition"],
        Domain.SUPPLEMENTS: ["perimenopausal supplementation evidence"],
    },
    "creatine": {
        Domain.SUPPLEMENTS: ["creatine monohydrate dosing trained adults"],
    },
    "vegan": {
        Domain.NUTRITION: ["vegan protein adequacy resistance trained"],
        Domain.SUPPLEMENTS: ["vegan supplementation B12 omega-3 creatine"],
    },
    "vegetarian": {
        Domain.NUTRITION: ["vegetarian protein adequacy resistance trained"],
        Domain.SUPPLEMENTS: ["vegetarian supplementation iron B12"],
    },
}


def derive_queries(intake: ClientIntake) -> dict[Domain, list[str]]:
    """Return per-domain text queries derived from intake goals, training_status, constraints, and regimen.

    Each domain gets 1–5 query strings. Total across all domains is capped at 30 (5 per domain).
    """
    ts = intake.training_status
    goals = intake.goals
    primary = goals[0]

    result: dict[Domain, list[str]] = {}

    nut: list[str] = []
    for g in goals:
        nut.append(f"protein intake for {g} in {ts} adults")
        if len(nut) >= 3:
            break
    if len(nut) < 3:
        nut.append(f"macronutrient timing for {ts} adults")
    result[Domain.NUTRITION] = nut

    result[Domain.TRAINING] = [
        f"resistance training program for {primary}",
        f"training volume {ts}",
    ]

    con: list[str] = [f"cardiovascular conditioning for {primary}"]
    for g in goals:
        if g in _CONDITIONING_GOALS:
            con.append(f"HIIT for {g}")
            break
    result[Domain.CONDITIONING] = con

    result[Domain.SUPPLEMENTS] = [f"supplements for {primary} {ts}"]

    result[Domain.RECOVERY] = [
        f"recovery between sessions {ts}",
        f"sleep for {primary}",
    ]

    result[Domain.BEHAVIORAL] = [f"adherence in {ts} adults pursuing {primary}"]

    for constraint in intake.constraints:
        ctype = constraint.type
        detail = constraint.detail
        if ctype == "injury":
            avoidance = f"avoiding {detail}"
            if len(result[Domain.TRAINING]) < _PER_DOMAIN_CAP:
                result[Domain.TRAINING].append(avoidance)
            if len(result[Domain.CONDITIONING]) < _PER_DOMAIN_CAP:
                result[Domain.CONDITIONING].append(avoidance)
        elif ctype == "dietary":
            if len(result[Domain.NUTRITION]) < _PER_DOMAIN_CAP:
                result[Domain.NUTRITION].append(f"avoiding {detail}")
        elif ctype == "schedule":
            if len(result[Domain.TRAINING]) < _PER_DOMAIN_CAP:
                result[Domain.TRAINING].append(f"training with {detail}")

    regimen_lower = intake.current_regimen.lower()
    if regimen_lower:
        for keyword, domain_queries in _REGIMEN_KEYWORDS.items():
            if keyword in regimen_lower:
                for domain, queries in domain_queries.items():
                    for query in queries:
                        if (
                            len(result[domain]) < _PER_DOMAIN_CAP
                            and query not in result[domain]
                        ):
                            result[domain].append(query)

    for domain in Domain:
        result[domain] = result[domain][:_PER_DOMAIN_CAP]

    return result
