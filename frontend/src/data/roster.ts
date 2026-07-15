import type { AgentBalance } from "../types";

type RosterEntry = Pick<AgentBalance, "id" | "displayName" | "companyRole" | "role" | "capabilities" | "personality">;

export const companyRoster: RosterEntry[] = [
  {
    id: "atlas",
    displayName: "Atlas",
    companyRole: "Product manager",
    role: "product",
    capabilities: ["Objective framing", "Acceptance criteria", "Task auctions"],
    personality: "Turns founder intent into bounded, testable work.",
  },
  {
    id: "forge",
    displayName: "Forge",
    companyRole: "Backend engineer",
    role: "backend",
    capabilities: ["FastAPI contracts", "Event sourcing", "Python tests"],
    personality: "Optimizes for explicit contracts and reversible changes.",
  },
  {
    id: "prism",
    displayName: "Prism",
    companyRole: "Frontend engineer",
    role: "frontend",
    capabilities: ["React interfaces", "Accessibility", "Browser verification"],
    personality: "Makes dense operational evidence legible and interactive.",
  },
  {
    id: "rivet",
    displayName: "Rivet",
    companyRole: "Platform engineer",
    role: "platform",
    capabilities: ["CI pipelines", "Containers", "Runtime instrumentation"],
    personality: "Connects code, checks, and deployable infrastructure.",
  },
  {
    id: "aegis",
    displayName: "Aegis",
    companyRole: "Adversarial reviewer",
    role: "reviewer",
    capabilities: ["Correctness review", "Threat modeling", "Regression analysis"],
    personality: "Challenges every claim until evidence survives scrutiny.",
  },
  {
    id: "sentinel",
    displayName: "Sentinel",
    companyRole: "QA and saboteur",
    role: "qa",
    capabilities: ["Test design", "Fault injection", "Production monitoring"],
    personality: "Breaks the release safely before customers can.",
  },
  {
    id: "shipwright",
    displayName: "Shipwright",
    companyRole: "Release and recovery",
    role: "release",
    capabilities: ["Release gates", "Canary rollout", "Rollback recovery"],
    personality: "Ships only with a known-good route home.",
  },
  {
    id: "chronicle",
    displayName: "Chronicle",
    companyRole: "Historian",
    role: "historian",
    capabilities: ["Change narratives", "Decision memory", "Changelog evidence"],
    personality: "Preserves why the company changed, not only what changed.",
  },
];

export const mergeCompanyRoster = (agents: AgentBalance[]): AgentBalance[] => {
  const byId = new Map(agents.map((agent) => [agent.id, agent]));
  const rosterIds = new Set(companyRoster.map((agent) => agent.id));
  const roster = companyRoster.map((entry) => {
    const reported = byId.get(entry.id);
    if (!reported) {
      return {
        ...entry,
        balance: 0,
        state: "dormant" as const,
        memoryCount: 0,
        memoryReferences: [],
        completedActions: 0,
        reported: false,
      };
    }
    return {
      ...entry,
      ...reported,
      companyRole: reported.companyRole ?? entry.companyRole,
      capabilities: reported.capabilities?.length ? reported.capabilities : entry.capabilities,
      personality: reported.personality || entry.personality,
      reported: true,
    };
  });
  return [...roster, ...agents.filter((agent) => !rosterIds.has(agent.id))];
};
