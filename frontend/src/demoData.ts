export type DemoOrganization = "campus" | "transport";
export type DemoStep = "events" | "dependencies" | "analysis" | "scenario";

type DemoEntity = {
  id: string;
  organization: DemoOrganization;
  key: string;
  name: string;
  type: string;
};

type DemoDependency = {
  id: string;
  organization: DemoOrganization;
  sourceId: string;
  sourceKey: string;
  targetId: string;
  targetKey: string;
  relationship: string;
  weight: number;
  reviewStatus: "reviewed" | "validated" | "draft";
};

type OrganizationSeed = {
  label: string;
  eventTitle: string;
  severity: number;
  triggerKey: string;
  entities: { key: string; name: string; type: string }[];
  dependencies: {
    sourceKey: string;
    targetKey: string;
    relationship: string;
    weight: number;
    reviewStatus: DemoDependency["reviewStatus"];
  }[];
};

export const DEMO_ORGANIZATIONS: Record<DemoOrganization, OrganizationSeed> = {
  campus: {
    label: "North Campus Demo",
    eventTitle: "Advanced Computing Laboratory unavailable",
    severity: 90,
    triggerKey: "AC-LAB",
    entities: [
      {
        key: "AC-LAB",
        name: "Advanced Computing Laboratory",
        type: "resource",
      },
      { key: "SESSION-A", name: "Practical Session A", type: "activity" },
      { key: "SESSION-B", name: "Practical Session B", type: "activity" },
      { key: "BATCH-1", name: "Student Batch 1", type: "group" },
      { key: "BATCH-2", name: "Student Batch 2", type: "group" },
      { key: "LAB-B", name: "Alternative Laboratory B", type: "resource" },
      { key: "LAB-C", name: "Alternative Laboratory C", type: "resource" },
      { key: "SLOT-1", name: "Afternoon Slot 1", type: "activity" },
      { key: "SLOT-2", name: "Afternoon Slot 2", type: "activity" },
      { key: "TIMETABLE", name: "Shared Timetable", type: "system" },
    ],
    dependencies: [
      {
        sourceKey: "AC-LAB",
        targetKey: "SESSION-A",
        relationship: "hosts",
        weight: 0.9,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "AC-LAB",
        targetKey: "SESSION-B",
        relationship: "hosts",
        weight: 0.85,
        reviewStatus: "validated",
      },
      {
        sourceKey: "SESSION-A",
        targetKey: "BATCH-1",
        relationship: "affects",
        weight: 0.8,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "SESSION-B",
        targetKey: "BATCH-2",
        relationship: "affects",
        weight: 0.8,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "SESSION-A",
        targetKey: "TIMETABLE",
        relationship: "updates",
        weight: 0.6,
        reviewStatus: "draft",
      },
      {
        sourceKey: "SESSION-B",
        targetKey: "TIMETABLE",
        relationship: "updates",
        weight: 0.6,
        reviewStatus: "draft",
      },
      {
        sourceKey: "LAB-B",
        targetKey: "SLOT-1",
        relationship: "provides_capacity_for",
        weight: 0.75,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "LAB-C",
        targetKey: "SLOT-2",
        relationship: "provides_capacity_for",
        weight: 0.7,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "TIMETABLE",
        targetKey: "SLOT-1",
        relationship: "schedules",
        weight: 0.5,
        reviewStatus: "draft",
      },
      {
        sourceKey: "TIMETABLE",
        targetKey: "SLOT-2",
        relationship: "schedules",
        weight: 0.5,
        reviewStatus: "draft",
      },
    ],
  },
  transport: {
    label: "City Transport Demo",
    eventTitle: "Road Segment X closed",
    severity: 80,
    triggerKey: "ROAD-X",
    entities: [
      { key: "ROAD-X", name: "Road Segment X", type: "location/resource" },
      { key: "ROUTE-1", name: "Bus Route 1", type: "activity/system" },
      { key: "ROUTE-2", name: "Bus Route 2", type: "activity/system" },
      { key: "STOP-A", name: "Stop A", type: "location" },
      { key: "STOP-B", name: "Stop B", type: "location" },
      { key: "COMMUTE-GROUP", name: "Commuter Group", type: "group" },
      { key: "CONNECTION", name: "Transfer Connection", type: "activity" },
      { key: "SCHEDULE", name: "Transport Schedule", type: "system" },
    ],
    dependencies: [
      {
        sourceKey: "ROAD-X",
        targetKey: "ROUTE-1",
        relationship: "affects",
        weight: 0.9,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "ROAD-X",
        targetKey: "ROUTE-2",
        relationship: "affects",
        weight: 0.7,
        reviewStatus: "draft",
      },
      {
        sourceKey: "ROUTE-1",
        targetKey: "STOP-A",
        relationship: "serves",
        weight: 0.8,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "ROUTE-2",
        targetKey: "STOP-B",
        relationship: "serves",
        weight: 0.8,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "STOP-A",
        targetKey: "CONNECTION",
        relationship: "enables",
        weight: 0.65,
        reviewStatus: "draft",
      },
      {
        sourceKey: "CONNECTION",
        targetKey: "COMMUTE-GROUP",
        relationship: "affects",
        weight: 0.75,
        reviewStatus: "reviewed",
      },
      {
        sourceKey: "ROUTE-1",
        targetKey: "SCHEDULE",
        relationship: "updates",
        weight: 0.5,
        reviewStatus: "draft",
      },
    ],
  },
};

const additionalEntitiesPerOrganization = 5_000;
const relationshipsPerEntity = 3;
let nextUuid = 1;

function stableUuid(sequence: number) {
  const suffix = sequence.toString(16).padStart(12, "0");
  return `00000000-0000-4000-8000-${suffix}`;
}

function nextId() {
  return stableUuid(nextUuid++);
}

function buildSyntheticGraph() {
  const entities: DemoEntity[] = [];
  const dependencies: DemoDependency[] = [];

  for (const organization of Object.keys(
    DEMO_ORGANIZATIONS,
  ) as DemoOrganization[]) {
    const seed = DEMO_ORGANIZATIONS[organization];
    const keyToId = new Map<string, string>();

    for (const entity of seed.entities) {
      const id = nextId();
      keyToId.set(entity.key, id);
      entities.push({ id, organization, ...entity });
    }

    for (const dependency of seed.dependencies) {
      const sourceId = keyToId.get(dependency.sourceKey);
      const targetId = keyToId.get(dependency.targetKey);
      if (!sourceId || !targetId) {
        throw new Error(
          `Invalid synthetic fixture edge: ${dependency.sourceKey} -> ${dependency.targetKey}`,
        );
      }
      dependencies.push({
        id: nextId(),
        organization,
        sourceId,
        sourceKey: dependency.sourceKey,
        targetId,
        targetKey: dependency.targetKey,
        relationship: dependency.relationship,
        weight: dependency.weight,
        reviewStatus: dependency.reviewStatus,
      });
    }

    const generated: DemoEntity[] = [];
    for (let index = 0; index < additionalEntitiesPerOrganization; index += 1) {
      const id = nextId();
      const key = `${organization.toUpperCase()}-${String(index + 1).padStart(5, "0")}`;
      const entity: DemoEntity = {
        id,
        organization,
        key,
        name: `${organization === "campus" ? "Campus" : "Transit"} Synthetic Node ${index + 1}`,
        type: ["activity", "resource", "system", "group"][index % 4],
      };
      generated.push(entity);
      entities.push(entity);
      keyToId.set(key, id);
    }

    for (let index = 0; index < generated.length; index += 1) {
      for (let offset = 1; offset <= relationshipsPerEntity; offset += 1) {
        const source = generated[index];
        const target = generated[(index + offset * 37) % generated.length];
        dependencies.push({
          id: nextId(),
          organization,
          sourceId: source.id,
          sourceKey: source.key,
          targetId: target.id,
          targetKey: target.key,
          relationship: ["affects", "requires", "updates"][
            (index + offset) % 3
          ],
          weight: (((index * 17 + offset * 13) % 91) + 5) / 100,
          reviewStatus: index % 5 === 0 ? "draft" : "reviewed",
        });
      }
    }
  }

  return { entities, dependencies };
}

const syntheticGraph = buildSyntheticGraph();

export const SYNTHETIC_ENTITIES = syntheticGraph.entities;
export const SYNTHETIC_DEPENDENCIES = syntheticGraph.dependencies;

export const DEMO_SCALE = {
  entities: SYNTHETIC_ENTITIES.length,
  dependencies: SYNTHETIC_DEPENDENCIES.length,
};
