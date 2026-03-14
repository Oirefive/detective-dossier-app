import type {
  AIDossierResponse,
  AIPersonCardResponse,
  AISettings,
  ArchiveSearchResponse,
  AutoBriefResponse,
  CaseAssignmentCreatePayload,
  CaseCompatibilityResponse,
  CaseCreatePayload,
  CaseDetail,
  CaseExportBundle,
  CaseGraphResponse,
  CaseParticipant,
  CaseSummary,
  Dossier,
  DestinyMatrixData,
  Evidence,
  EvidenceCreatePayload,
  EventCreatePayload,
  EventItem,
  ImportCaseResponse,
  MatrixComparisonResponse,
  Person,
  PersonCreatePayload,
  Relation,
  RelationCreatePayload,
  RelationshipSearchResponse,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const response = await fetch(path, {
    headers: isFormData
      ? init?.headers
      : {
          "Content-Type": "application/json",
          ...(init?.headers ?? {}),
        },
    ...init,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  getAISettings: () => request<AISettings>("/api/settings/ai"),
  saveAISettings: (payload: AISettings) => request<AISettings>("/api/settings/ai", { method: "PUT", body: JSON.stringify(payload) }),
  aiPersonCard: (sourceText: string) => request<AIPersonCardResponse>("/api/ai/person-card", { method: "POST", body: JSON.stringify({ sourceText }) }),
  aiDossier: (payload: { participant?: CaseParticipant | null; person?: Person | null; case?: CaseDetail | null }) =>
    request<AIDossierResponse>("/api/ai/dossier", { method: "POST", body: JSON.stringify(payload) }),
  listCases: () => request<CaseSummary[]>("/api/cases"),
  createCase: (payload: CaseCreatePayload) => request<CaseDetail>("/api/cases", { method: "POST", body: JSON.stringify(payload) }),
  deleteCase: (caseId: string) => request<void>(`/api/cases/${caseId}`, { method: "DELETE" }),
  pinCase: (caseId: string, pinned: boolean) => request<CaseDetail>(`/api/cases/${caseId}/pin?pinned=${pinned}`, { method: "PUT" }),
  listPeople: () => request<Person[]>("/api/people"),
  createPerson: (payload: PersonCreatePayload) => request<Person>("/api/people", { method: "POST", body: JSON.stringify(payload) }),
  savePerson: (personId: string, payload: PersonCreatePayload) => request<Person>(`/api/people/${personId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deletePerson: (personId: string) => request<void>(`/api/people/${personId}`, { method: "DELETE" }),
  pinPerson: (personId: string, pinned: boolean) => request<Person>(`/api/people/${personId}/pin?pinned=${pinned}`, { method: "PUT" }),
  listCasePeople: (caseId: string) => request<CaseParticipant[]>(`/api/cases/${caseId}/people`),
  addPersonToCase: (caseId: string, payload: CaseAssignmentCreatePayload) => request<CaseParticipant>(`/api/cases/${caseId}/people`, { method: "POST", body: JSON.stringify(payload) }),
  getDossier: (participantId: string) => request<Dossier>(`/api/participants/${participantId}/dossier`),
  getDestinyMatrix: (birthDate: string) => request<DestinyMatrixData>(`/api/destiny-matrix?birth_date=${encodeURIComponent(birthDate)}`),
  saveParticipant: (payload: CaseParticipant) => request<CaseParticipant>(`/api/participants/${payload.id}`, { method: "PUT", body: JSON.stringify(payload) }),
  pinParticipant: (participantId: string, pinned: boolean) => request<CaseParticipant>(`/api/participants/${participantId}/pin?pinned=${pinned}`, { method: "PUT" }),
  addEvidence: (participantId: string, payload: EvidenceCreatePayload) => request<Evidence>(`/api/participants/${participantId}/evidence`, { method: "POST", body: JSON.stringify(payload) }),
  deleteEvidence: (evidenceId: string) => request<void>(`/api/evidence/${evidenceId}`, { method: "DELETE" }),
  addEvent: (participantId: string, payload: EventCreatePayload) => request<EventItem>(`/api/participants/${participantId}/events`, { method: "POST", body: JSON.stringify(payload) }),
  deleteEvent: (eventId: string) => request<void>(`/api/events/${eventId}`, { method: "DELETE" }),
  addRelation: (participantId: string, payload: RelationCreatePayload) => request<Relation>(`/api/participants/${participantId}/relations`, { method: "POST", body: JSON.stringify(payload) }),
  deleteRelation: (relationId: string) => request<void>(`/api/relations/${relationId}`, { method: "DELETE" }),
  generatePdf: (participantId: string, template: "dossier" | "board" = "dossier") => request<string>(`/api/participants/${participantId}/pdf?template=${template}`, { method: "POST" }),
  searchRelationships: (caseId: string, query: string) => request<RelationshipSearchResponse>(`/api/cases/${caseId}/relationship-search?q=${encodeURIComponent(query)}`),
  archiveSearch: (query: string) => request<ArchiveSearchResponse>(`/api/archive-search?q=${encodeURIComponent(query)}`),
  getCaseGraph: (caseId: string) => request<CaseGraphResponse>(`/api/cases/${caseId}/graph`),
  compareMatrices: (leftPersonId: string, rightPersonId: string) => request<MatrixComparisonResponse>(`/api/people/${leftPersonId}/matrix-compare/${rightPersonId}`),
  getCaseCompatibility: (personId: string, caseId: string) => request<CaseCompatibilityResponse>(`/api/people/${personId}/case-compatibility/${caseId}`),
  getAutoBrief: (caseId: string) => request<AutoBriefResponse>(`/api/cases/${caseId}/autobrief`),
  exportCase: (caseId: string) => request<CaseExportBundle>(`/api/cases/${caseId}/export`),
  importCase: (bundle: CaseExportBundle) => request<ImportCaseResponse>("/api/cases/import", { method: "POST", body: JSON.stringify(bundle) }),
  uploadPhoto: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<string>("/api/uploads/photo", { method: "POST", body: formData });
  },
};
