"use client";

import React from "react";
import { ShieldAlert } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function ApprovalsPage() {
  return (
    <ShellLayout pageTitle="Approvals" breadcrumb="Work Management">
      <PhaseBoundaryCard
        title="Approvals & Human Authority Gate"
        phaseNumber={10}
        phaseName="Human-in-the-Loop Governance & Risk Tiers"
        icon={ShieldAlert}
        docSection="14"
        description="The Approvals center enforces human control over high-risk actions. External communications, budget commitments, code deployments, and major decisions require owner sign-off."
        plannedFeatures={[
          "Risk-tiered policy evaluation (Low, Medium, High, Critical)",
          "Human-in-the-loop approval queues and notification gates",
          "Approval decision auditing (Approve, Reject, Request Revisions)",
          "Execution pause and resumption upon human authorization",
        ]}
      />
    </ShellLayout>
  );
}
