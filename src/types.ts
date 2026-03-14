export type CaseSummary = {
  id: string;
  title: string;
  classification: string;
  status: string;
  updatedAt: string;
  suspectCount: number;
  pinned: boolean;
};

export type CaseDetail = {
  id: string;
  title: string;
  classification: string;
  status: string;
  summary: string;
  updatedAt: string;
  pinned: boolean;
};

export type Person = {
  id: string;
  fullName: string;
  aliasName: string;
  birthDate: string | null;
  age: number | null;
  biography: string;
  documentsSummary: string;
  knownPlaces: string;
  habits: string;
  photoPath: string | null;
  updatedAt: string;
  pinned: boolean;
};

export type PersonCreatePayload = {
  fullName: string;
  aliasName: string;
  birthDate: string | null;
  age: number | null;
  biography: string;
  documentsSummary: string;
  knownPlaces: string;
  habits: string;
  photoPath: string | null;
  pinned: boolean;
};

export type CaseParticipant = {
  id: string;
  caseId: string;
  personId: string;
  fullName: string;
  aliasName: string;
  birthDate: string | null;
  age: number | null;
  biography: string;
  documentsSummary: string;
  knownPlaces: string;
  habits: string;
  photoPath: string | null;
  role: string;
  suspicionLevel: number;
  status: string;
  location: string;
  description: string;
  notes: string;
  updatedAt: string;
  pinned: boolean;
};

export type CaseAssignmentCreatePayload = {
  personId: string;
  role: string;
  suspicionLevel: number;
  status: string;
  location: string;
  description: string;
  notes: string;
  pinned: boolean;
};

export type Evidence = {
  id: string;
  participantId: string;
  title: string;
  category: string;
  status: string;
  details: string;
};

export type EvidenceCreatePayload = {
  title: string;
  category: string;
  status: string;
  details: string;
};

export type EventItem = {
  id: string;
  participantId: string;
  eventDate: string;
  title: string;
  details: string;
};

export type EventCreatePayload = {
  eventDate: string;
  title: string;
  details: string;
};

export type Relation = {
  id: string;
  participantId: string;
  targetType: string;
  targetLabel: string;
  relationType: string;
  confidence: number;
};

export type RelationCreatePayload = {
  targetType: string;
  targetLabel: string;
  relationType: string;
  confidence: number;
};

export type Dossier = {
  participant: CaseParticipant;
  case: CaseDetail;
  evidence: Evidence[];
  events: EventItem[];
  relations: Relation[];
  matrix: MatrixProfile | null;
};

export type MatrixProfile = {
  lifePath: number;
  mission: number;
  dominantNumbers: number[];
  missingNumbers: number[];
  matrixRows: number[][];
  character: number;
  energy: number;
  interests: number;
  health: number;
  logic: number;
  labor: number;
  luck: number;
  duty: number;
  memory: number;
  purposeLine: number;
  familyLine: number;
  stabilityLine: number;
  temperament: number;
  spirituality: number;
  grounding: number;
  strengths: string[];
  risks: string[];
  relationshipStyle: string;
  socialVector: string;
  shadowPattern: string;
  interpretation: string;
  warning: string;
};

export type DestinyMatrixRow = {
  name: string;
  tone: string;
  physics: number;
  energy: number;
  emotion: number;
};

export type DestinyMatrixTotals = {
  physics: number;
  energy: number;
  emotion: number;
};

export type DestinyMatrixData = {
  svgHtml: string;
  chakraRows: DestinyMatrixRow[];
  totals: DestinyMatrixTotals;
};

export type RelationshipHit = {
  participant: CaseParticipant;
  score: number;
  confidence: string;
  summary: string;
  matchedOn: string[];
  highlights: string[];
  topLinks: string[];
};

export type RelationshipSearchResponse = {
  query: string;
  caseId: string;
  total: number;
  hits: RelationshipHit[];
};

export type ArchiveSearchResult = {
  entityType: "case" | "person" | "participant";
  entityId: string;
  title: string;
  subtitle: string;
  caseId: string | null;
  participantId: string | null;
  personId: string | null;
  status: string;
  score: number;
  pinned: boolean;
  highlights: string[];
};

export type ArchiveSearchResponse = {
  query: string;
  total: number;
  results: ArchiveSearchResult[];
};

export type MatrixComparisonResponse = {
  leftPerson: Person;
  rightPerson: Person;
  leftMatrix: MatrixProfile | null;
  rightMatrix: MatrixProfile | null;
  compatibilityScore: number;
  resonance: string;
  sharedStrengths: string[];
  tensionPoints: string[];
  summary: string;
};

export type CaseCompatibilityResponse = {
  person: Person;
  case: CaseDetail;
  matrix: MatrixProfile | null;
  compatibilityScore: number;
  matchReasons: string[];
  riskFactors: string[];
  summary: string;
};

export type GraphNode = {
  id: string;
  label: string;
  nodeType: "person" | "participant" | "place" | "event" | "evidence" | "relation" | "case";
  status: string;
  pinned: boolean;
  meta: Record<string, unknown>;
};

export type GraphEdge = {
  source: string;
  target: string;
  label: string;
  weight: number;
};

export type CaseGraphResponse = {
  caseId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type AutoBriefResponse = {
  caseId: string;
  headline: string;
  summary: string;
  keyPeople: string[];
  keyPlaces: string[];
  keyRisks: string[];
  recommendations: string[];
};

export type CaseExportBundle = {
  case: CaseDetail;
  participants: CaseParticipant[];
  people: Person[];
  evidence: Evidence[];
  events: EventItem[];
  relations: Relation[];
};

export type ImportCaseResponse = {
  case: CaseDetail;
  importedPeople: number;
  importedParticipants: number;
  importedEvidence: number;
  importedEvents: number;
  importedRelations: number;
};

export type CaseCreatePayload = {
  title: string;
  classification: string;
  status: string;
  summary: string;
  pinned: boolean;
};

export type AISettings = {
  provider: string;
  model: string;
  apiKey: string;
  baseUrl: string;
  cardPrompt: string;
  dossierPrompt: string;
};

export type AIPersonCardResponse = {
  fullName: string;
  aliasName: string;
  birthDate: string | null;
  biography: string;
  documentsSummary: string;
  knownPlaces: string;
  habits: string;
};

export type AIDossierResponse = {
  summary: string;
  description: string;
  notes: string;
  status: string;
  suspicionLevel: number;
  keyFacts: string[];
  redFlags: string[];
  recommendations: string[];
};
