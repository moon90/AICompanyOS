"use client";

import React from "react";
import { Building2 } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function CompanyPage() {
  return (
    <ShellLayout pageTitle="Company" breadcrumb="Organization">
      <PhaseBoundaryCard
        title="Company & Organization"
        phaseNumber={3}
        phaseName="Company Model & Department Structures"
        icon={Building2}
        docSection="7"
        description="The company organizational model provides persistent structure for mission statements, business domains, departmental hierarchy (CTO, CMO, Sales), and operational policies."
        plannedFeatures={[
          "Company profile & mission statement model",
          "Department definitions (CTO, CMO, Sales)",
          "Organizational hierarchy & departmental policies",
          "PostgreSQL schema 'companies' and 'departments'",
        ]}
      />
    </ShellLayout>
  );
}
