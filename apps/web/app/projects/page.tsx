"use client";

import React from "react";
import { FolderGit2 } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function ProjectsPage() {
  return (
    <ShellLayout pageTitle="Projects" breadcrumb="Work Management">
      <PhaseBoundaryCard
        title="Projects & Initiatives"
        phaseNumber={6}
        phaseName="Projects, Tasks & Work Breakdown Structure"
        icon={FolderGit2}
        docSection="10"
        description="Projects group strategic objectives, roadmaps, and tasks across departments. They provide progress tracking, dependency management, and milestone verification."
        plannedFeatures={[
          "Project creation, lifecycle, and priority assignment",
          "Cross-department project ownership and milestones",
          "Work breakdown graphs and dependency tracking",
          "PostgreSQL schema 'projects' with status transitions",
        ]}
      />
    </ShellLayout>
  );
}
