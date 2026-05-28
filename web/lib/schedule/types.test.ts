import { describe, expect, it } from "vitest";
import { validateSchedule, type Schedule } from "./types";

function makeDay(day: string) {
  return {
    day,
    training: { title: "Lower body", items: [{ name: "Squat" }] },
    nutrition: { protein_target_g: 150, meals: [] },
    recovery: ["7-9h sleep"],
  };
}

function makeValidSchedule(): Schedule {
  return {
    weekly_focus: "Build strength",
    days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) =>
      makeDay(d)
    ) as Schedule["days"],
    supplements: [
      { name: "Creatine", dose: "5g", timing: "AM", why_plain: "ATP" },
    ],
    recommendations: [
      {
        headline: "Eat 4 high-protein meals",
        why_plain: "Distribute MPS pulses",
        backing_atom_ids: ["EA-NUT-1234"],
      },
    ],
  };
}

describe("validateSchedule", () => {
  it("accepts a fully-formed schedule", () => {
    const out = validateSchedule(makeValidSchedule());
    expect(out).not.toHaveProperty("error");
  });

  it("rejects non-object root", () => {
    expect(validateSchedule(null)).toEqual({ error: "root must be object" });
    expect(validateSchedule("nope")).toEqual({ error: "root must be object" });
  });

  it("rejects missing weekly_focus", () => {
    const s = makeValidSchedule() as Record<string, unknown>;
    delete s.weekly_focus;
    expect(validateSchedule(s)).toEqual({ error: "weekly_focus must be string" });
  });

  it("rejects wrong number of days", () => {
    const s = makeValidSchedule() as unknown as { days: unknown[] };
    s.days = s.days.slice(0, 6);
    expect(validateSchedule(s)).toEqual({ error: "days must be array of length 7" });
  });

  it("rejects out-of-order day names", () => {
    const s = makeValidSchedule();
    s.days[2] = makeDay("Fri") as Schedule["days"][number];
    const out = validateSchedule(s);
    expect(out).toHaveProperty("error");
    expect((out as { error: string }).error).toMatch(/Wed/);
  });

  it("rejects recommendation missing backing_atom_ids", () => {
    const s = makeValidSchedule();
    (s.recommendations[0] as unknown as Record<string, unknown>).backing_atom_ids =
      undefined;
    const out = validateSchedule(s);
    expect(out).toEqual({
      error: "recommendations[].backing_atom_ids must be string[]",
    });
  });

  it("rejects supplements with missing dose", () => {
    const s = makeValidSchedule();
    (s.supplements[0] as unknown as Record<string, unknown>).dose = "";
    const out = validateSchedule(s);
    expect(out).toEqual({
      error: "supplements[] need name/dose/timing/why_plain strings",
    });
  });

  it("accepts null training (rest day)", () => {
    const s = makeValidSchedule();
    s.days[5].training = null;
    expect(validateSchedule(s)).not.toHaveProperty("error");
  });
});
