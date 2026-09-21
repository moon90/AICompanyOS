"use client";

import React from "react";
import { Settings } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";
import { PhaseBoundaryCard } from "@/components/shell/PhaseBoundaryCard";

export default function SettingsPage() {
  return (
    <ShellLayout pageTitle="Settings" breadcrumb="System & Governance">
      <PhaseBoundaryCard
        title="Settings & System Configuration"
        phaseNumber={23}
        phaseName="Security Hardening, Integrations & Environment Settings"
        icon={Settings}
        docSection="27"
        description="Settings manages production security configurations, API key vaults, notification webhooks, rate limits, theme preferences, and system backup policies."
        plannedFeatures={[
          "Operator profile and credential management",
          "API key vault and third-party integration settings",
          "Security policies, session timeouts, and MFA",
          "Theme toggle (Dark / Light executive theme)",
        ]}
      />
    </ShellLayout>
  );
}
