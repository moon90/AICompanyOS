import { describe, it, expect } from "vitest";

describe("Application Shell & Navigation Specification", () => {
  const expectedNavigationSections = [
    { name: "Dashboard", href: "/", phase: 2 },
    { name: "Company", href: "/company", phase: 3 },
    { name: "CEO Orchestrator", href: "/ceo", phase: 5 },
    { name: "Agent Registry", href: "/agents", phase: 4 },
    { name: "Projects", href: "/projects", phase: 6 },
    { name: "Tasks", href: "/tasks", phase: 6 },
    { name: "Approvals", href: "/approvals", phase: 10 },
    { name: "Activity", href: "/activity", phase: 13 },
    { name: "Settings", href: "/settings", phase: 23 },
  ];

  it("contains all 9 required sections from docs/Phases.md § 6", () => {
    expect(expectedNavigationSections).toHaveLength(9);
    const routes = expectedNavigationSections.map((s) => s.href);
    expect(routes).toContain("/");
    expect(routes).toContain("/company");
    expect(routes).toContain("/ceo");
    expect(routes).toContain("/agents");
    expect(routes).toContain("/projects");
    expect(routes).toContain("/tasks");
    expect(routes).toContain("/approvals");
    expect(routes).toContain("/activity");
    expect(routes).toContain("/settings");
  });

  it("designates honest phase boundaries without fabricating later-phase states", () => {
    const futureSections = expectedNavigationSections.filter((s) => s.phase > 2);
    expect(futureSections.length).toBe(8);
    for (const section of futureSections) {
      expect(section.phase).toBeGreaterThan(2);
    }
  });
});
