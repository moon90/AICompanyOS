"use client";

import React from "react";
import { Users } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function AgentsPage() {
  return (
    <ShellLayout pageTitle="Agent Registry" breadcrumb="Organization">
      <PhaseBoundaryCard
        title="Agent Registry & Runtime"
        phaseNumber={4}
        phaseName="Agent Definitions, Prompts & Autonomy Levels"
        icon={Users}
        docSection="8"
        description="The Agent Registry maintains the directory of all AI agents in the company, including their specialized roles, system prompts, tool assignments, and autonomy permissions."
        plannedFeatures={[
          "Agent profiles, department assignments, and roles",
          "System prompts and operational memory scopes",
          "Autonomy levels (Advisory, Semi-Autonomous, Autonomous)",
          "Agent capability and tool gateway permissions",
        ]}
      />
    </ShellLayout>
  );
}
