from __future__ import annotations

from hcc_compiler.models import Domain
from hcc_compiler.sp2.intake import ClientIntake

_CONDITIONING_GOALS = {"endurance", "weight_loss", "performance"}


def derive_queries(intake: ClientIntake) -> dict[Domain, list[str]]:
    """Return per-domain text queries derived from intake goals, training_status, and constraints.

    Each domain gets 1–3 query strings. Total across all domains is capped at 18 (3 per domain).
    """
    ts = intake.training_status
    goals = intake.goals
    # Use the first goal as the primary goal for single-query templates
    primary = goals[0]

    result: dict[Domain, list[str]] = {}

    # --- NUTRITION ---
    nut: list[str] = []
    for g in goals:
        nut.append(f"protein intake for {g} in {ts} adults")
        if len(nut) >= 3:
            break
    if len(nut) < 3:
        nut.append(f"macronutrient timing for {ts} adults")
    result[Domain.NUTRITION] = nut[:3]

    # --- TRAINING ---
    tra: list[str] = [
        f"resistance training program for {primary}",
        f"training volume {ts}",
    ]
    result[Domain.TRAINING] = tra[:3]

    # --- CONDITIONING ---
    con: list[str] = [f"cardiovascular conditioning for {primary}"]
    for g in goals:
        if g in _CONDITIONING_GOALS:
            con.append(f"HIIT for {g}")
            break
    result[Domain.CONDITIONING] = con[:3]

    # --- SUPPLEMENTS ---
    sup: list[str] = [f"supplements for {primary} {ts}"]
    result[Domain.SUPPLEMENTS] = sup[:3]

    # --- RECOVERY ---
    rec: list[str] = [
        f"recovery between sessions {ts}",
        f"sleep for {primary}",
    ]
    result[Domain.RECOVERY] = rec[:3]

    # --- BEHAVIORAL ---
    beh: list[str] = [f"adherence in {ts} adults pursuing {primary}"]
    result[Domain.BEHAVIORAL] = beh[:3]

    # --- Constraints ---
    for constraint in intake.constraints:
        ctype = constraint.type
        detail = constraint.detail
        if ctype == "injury":
            avoidance = f"avoiding {detail}"
            if len(result[Domain.TRAINING]) < 3:
                result[Domain.TRAINING].append(avoidance)
            if len(result[Domain.CONDITIONING]) < 3:
                result[Domain.CONDITIONING].append(avoidance)
        elif ctype == "dietary":
            if len(result[Domain.NUTRITION]) < 3:
                result[Domain.NUTRITION].append(f"avoiding {detail}")
        elif ctype == "schedule":
            if len(result[Domain.TRAINING]) < 3:
                result[Domain.TRAINING].append(f"training with {detail}")

    # Enforce per-domain cap (already applied above, but enforce defensively)
    for domain in Domain:
        result[domain] = result[domain][:3]

    return result
