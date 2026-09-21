"use client";

import React from "react";
import { Activity } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function ActivityPage() {
  return (
    <ShellLayout pageTitle="Activity" breadcrumb="System & Governance">
      <PhaseBoundaryCard
        title="Activity & Historical Audit Trail"
        phaseNumber={13}
        phaseName="Event Streaming, Agent Logs & Audit Records"
        icon={Activity}
        docSection="17"
        description="The Activity section provides an immutable record of all company events, agent delegations, tool executions, approval actions, and system lifecycle changes."
        plannedFeatures={[
          "Live event streaming and chronological activity feed",
          "Agent run timelines and decision logs",
          "Tool execution audits with input/output capture",
          "Search, filter by agent, department, or date range",
        ]}
      />
    </ShellLayout>
  );
}
