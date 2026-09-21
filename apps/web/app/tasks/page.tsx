"use client";

import React from "react";
import { CheckSquare } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function TasksPage() {
  return (
    <ShellLayout pageTitle="Tasks" breadcrumb="Work Management">
      <PhaseBoundaryCard
        title="Tasks & Execution DAG"
        phaseNumber={6}
        phaseName="Task Engine, State Machine & Execution Graphs"
        icon={CheckSquare}
        docSection="10"
        description="The Task Engine manages atomic, verifiable units of work. It enforces state machines, assigns tasks to specialists, resolves dependencies, and records execution output."
        plannedFeatures={[
          "Task lifecycle (Created, Planned, In Progress, Review, Done)",
          "Directed Acyclic Graph (DAG) dependency resolution",
          "Specialist agent task assignment and tool execution",
          "Verification gates and execution audit trail",
        ]}
      />
    </ShellLayout>
  );
}
