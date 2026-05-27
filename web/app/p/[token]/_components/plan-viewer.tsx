"use client";

import { useState } from "react";
import { BottomNav, type TabKey } from "./bottom-nav";
import { TodayTab } from "./today-tab";
import { WeekTab } from "./week-tab";
import { WhyTab } from "./why-tab";
import { CoachTab } from "./coach-tab";
import type { Schedule } from "@/lib/schedule/types";
import type { CoachBrand } from "@/lib/data/share-loader";

export function PlanViewer({
  schedule,
  coach,
}: {
  schedule: Schedule;
  coach: CoachBrand;
}) {
  const [tab, setTab] = useState<TabKey>("today");

  return (
    <>
      {tab === "today" && <TodayTab schedule={schedule} />}
      {tab === "week" && <WeekTab schedule={schedule} />}
      {tab === "why" && <WhyTab schedule={schedule} />}
      {tab === "coach" && <CoachTab coach={coach} schedule={schedule} />}

      <BottomNav active={tab} onChange={setTab} />
    </>
  );
}
