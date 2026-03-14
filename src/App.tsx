import { useEffect, useMemo, useState } from "react";

import { AISettingsPanel } from "./components/AISettingsPanel";
import { ArchiveSearchPanel } from "./components/ArchiveSearchPanel";
import { AutoBriefPanel } from "./components/AutoBriefPanel";
import { CaseGraphPanel } from "./components/CaseGraphPanel";
import { DossierCard } from "./components/DossierCard";
import { LiveBoardPanel } from "./components/LiveBoardPanel";
import { MatrixComparePanel } from "./components/MatrixComparePanel";
import { PeopleRegistryPanel } from "./components/PeopleRegistryPanel";
import { RelationshipSearchPanel } from "./components/RelationshipSearchPanel";
import { Sidebar } from "./components/Sidebar";
import { CaseParticipantsPanel } from "./components/SuspectList";
import { api } from "./tauri";
import type {
  AIDossierResponse,
  AISettings,
  ArchiveSearchResult,
  AutoBriefResponse,
  CaseAssignmentCreatePayload,
  CaseCompatibilityResponse,
  CaseCreatePayload,
  CaseGraphResponse,
  CaseParticipant,
  CaseSummary,
  Dossier,
  EvidenceCreatePayload,
  EventCreatePayload,
  MatrixComparisonResponse,
  Person,
  PersonCreatePayload,
  RelationCreatePayload,
  RelationshipHit,
} from "./types";

type ViewMode = "cases" | "people";

function saveJson(bundle: unknown, fileName: string) {
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [view, setView] = useState<ViewMode>("cases");
  const [liveBoard, setLiveBoard] = useState(false);
  const [creatingPerson, setCreatingPerson] = useState(false);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [participants, setParticipants] = useState<CaseParticipant[]>([]);
  const [activeParticipantId, setActiveParticipantId] = useState<string | null>(null);
  const [activePersonId, setActivePersonId] = useState<string | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [draftParticipant, setDraftParticipant] = useState<CaseParticipant | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<RelationshipHit[]>([]);
  const [archiveQuery, setArchiveQuery] = useState("");
  const [archiveResults, setArchiveResults] = useState<ArchiveSearchResult[]>([]);
  const [graph, setGraph] = useState<CaseGraphResponse | null>(null);
  const [brief, setBrief] = useState<AutoBriefResponse | null>(null);
  const [comparison, setComparison] = useState<MatrixComparisonResponse | null>(null);
  const [compatibility, setCompatibility] = useState<CaseCompatibilityResponse | null>(null);
  const [comparePersonId, setComparePersonId] = useState<string | null>(null);
  const [photoUploading, setPhotoUploading] = useState(false);
  const [notice, setNotice] = useState("Архив готов к работе");
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [aiSettings, setAiSettings] = useState<AISettings | null>(null);
  const [aiSaving, setAiSaving] = useState(false);
  const [aiCardBusy, setAiCardBusy] = useState(false);
  const [aiDossierBusy, setAiDossierBusy] = useState(false);

  const activeCase = useMemo(() => cases.find((item) => item.id === activeCaseId) ?? null, [cases, activeCaseId]);
  const activePerson = useMemo(
    () => (creatingPerson ? null : people.find((item) => item.id === activePersonId) ?? null),
    [creatingPerson, people, activePersonId]
  );
  const highRisk = participants.filter((item) => item.suspicionLevel >= 75).length;

  async function loadCases() {
    const items = await api.listCases();
    setCases(items);
    setActiveCaseId((current) => current ?? items[0]?.id ?? null);
  }

  async function loadPeople() {
    const items = await api.listPeople();
    setPeople(items);
    setActivePersonId((current) => current ?? items[0]?.id ?? null);
  }

  async function loadAISettings() {
    const payload = await api.getAISettings();
    setAiSettings(payload);
  }

  async function loadParticipants(caseId: string) {
    const items = await api.listCasePeople(caseId);
    setParticipants(items);
    setActiveParticipantId((current) => (current && items.some((item) => item.id === current) ? current : items[0]?.id ?? null));
    if (!items.length) {
      setDossier(null);
      setDraftParticipant(null);
    }
  }

  async function loadDossier(participantId: string) {
    const payload = await api.getDossier(participantId);
    setDossier(payload);
    setDraftParticipant(payload.participant);
  }

  async function loadCaseAnalytics(caseId: string) {
    const [graphPayload, briefPayload] = await Promise.all([api.getCaseGraph(caseId), api.getAutoBrief(caseId)]);
    setGraph(graphPayload);
    setBrief(briefPayload);
  }

  async function refreshParticipantData(participantId: string) {
    await loadDossier(participantId);
    if (activeCaseId) {
      await Promise.all([loadParticipants(activeCaseId), loadCases(), loadCaseAnalytics(activeCaseId)]);
    }
  }

  async function handleArchiveSearch(query: string) {
    setArchiveQuery(query);
    if (!query.trim()) {
      setArchiveResults([]);
      return;
    }
    const response = await api.archiveSearch(query);
    setArchiveResults(response.results);
  }

  async function createCase(payload: CaseCreatePayload) {
    const created = await api.createCase(payload);
    await loadCases();
    setActiveCaseId(created.id);
    setNotice(`Создано дело: ${created.title}`);
  }

  async function removeCase(caseId: string) {
    await api.deleteCase(caseId);
    await loadCases();
    setNotice("Дело удалено");
  }

  async function pinCase(caseId: string, pinned: boolean) {
    await api.pinCase(caseId, pinned);
    await loadCases();
  }

  async function createPerson(payload: PersonCreatePayload) {
    const created = await api.createPerson(payload);
    await loadPeople();
    setCreatingPerson(false);
    setActivePersonId(created.id);
    setNotice(`Добавлен человек: ${created.fullName}`);
  }

  async function savePerson(personId: string, payload: PersonCreatePayload) {
    const saved = await api.savePerson(personId, payload);
    await loadPeople();
    setCreatingPerson(false);
    setActivePersonId(saved.id);
    if (activeCaseId) await loadParticipants(activeCaseId);
    setNotice(`Карточка обновлена: ${saved.fullName}`);
  }

  async function removePerson(personId: string) {
    await api.deletePerson(personId);
    await loadPeople();
    setCreatingPerson(false);
    if (activeCaseId) await loadParticipants(activeCaseId);
    setNotice("Человек удалён");
  }

  async function pinPerson(personId: string, pinned: boolean) {
    await api.pinPerson(personId, pinned);
    await loadPeople();
  }

  async function addPersonToCase(payload: CaseAssignmentCreatePayload) {
    if (!activeCaseId) return;
    const added = await api.addPersonToCase(activeCaseId, payload);
    await Promise.all([loadParticipants(activeCaseId), loadCases(), loadCaseAnalytics(activeCaseId)]);
    setActiveParticipantId(added.id);
    setView("cases");
    setNotice(`Человек добавлен в дело: ${added.fullName}`);
  }

  async function pinParticipant(participantId: string, pinned: boolean) {
    await api.pinParticipant(participantId, pinned);
    if (activeCaseId) await loadParticipants(activeCaseId);
    if (activeParticipantId === participantId) await loadDossier(participantId);
  }

  async function saveParticipant() {
    if (!draftParticipant) return;
    const saved = await api.saveParticipant(draftParticipant);
    setDraftParticipant(saved);
    await refreshParticipantData(saved.id);
    setNotice(`Карточка участника обновлена: ${saved.fullName}`);
  }

  async function addEvidence(payload: EvidenceCreatePayload) {
    if (!draftParticipant) return;
    await api.addEvidence(draftParticipant.id, payload);
    await refreshParticipantData(draftParticipant.id);
  }

  async function removeEvidence(id: string) {
    if (!draftParticipant) return;
    await api.deleteEvidence(id);
    await refreshParticipantData(draftParticipant.id);
  }

  async function addEvent(payload: EventCreatePayload) {
    if (!draftParticipant) return;
    await api.addEvent(draftParticipant.id, payload);
    await refreshParticipantData(draftParticipant.id);
  }

  async function removeEvent(id: string) {
    if (!draftParticipant) return;
    await api.deleteEvent(id);
    await refreshParticipantData(draftParticipant.id);
  }

  async function addRelation(payload: RelationCreatePayload) {
    if (!draftParticipant) return;
    await api.addRelation(draftParticipant.id, payload);
    await refreshParticipantData(draftParticipant.id);
  }

  async function removeRelation(id: string) {
    if (!draftParticipant) return;
    await api.deleteRelation(id);
    await refreshParticipantData(draftParticipant.id);
  }

  async function generatePdf() {
    if (!draftParticipant) return;
    const path = await api.generatePdf(draftParticipant.id, "dossier");
    const fileName = path.split(/[\\/]/).pop();
    if (fileName) window.open(`/exports/${fileName}`, "_blank", "noopener,noreferrer");
  }

  async function generateBoardPdf() {
    if (!draftParticipant) return;
    const path = await api.generatePdf(draftParticipant.id, "board");
    const fileName = path.split(/[\\/]/).pop();
    if (fileName) window.open(`/exports/${fileName}`, "_blank", "noopener,noreferrer");
  }

  async function uploadPhoto(file: File) {
    setPhotoUploading(true);
    try {
      return await api.uploadPhoto(file);
    } finally {
      setPhotoUploading(false);
    }
  }

  async function persistParticipantPhoto(path: string | null) {
    if (!draftParticipant) return;
    const payload = { ...draftParticipant, photoPath: path };
    const saved = await api.saveParticipant(payload);
    setDraftParticipant(saved);
    await refreshParticipantData(saved.id);
  }

  async function persistPersonPhoto(path: string | null) {
    if (!activePerson) return;
    await api.savePerson(activePerson.id, { ...activePerson, photoPath: path });
    await loadPeople();
  }

  async function runSearch(query: string) {
    if (!activeCaseId) return;
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    const response = await api.searchRelationships(activeCaseId, query);
    setSearchResults(response.hits);
  }

  async function handleArchivePick(item: ArchiveSearchResult) {
    if (item.caseId) setActiveCaseId(item.caseId);
    if (item.personId) {
      setCreatingPerson(false);
      setActivePersonId(item.personId);
      if (item.entityType === "person") setView("people");
    }
    if (item.participantId) {
      setView("cases");
      setActiveParticipantId(item.participantId);
    }
  }

  async function handleExportCase() {
    if (!activeCaseId || !activeCase) return;
    const bundle = await api.exportCase(activeCaseId);
    saveJson(bundle, `${activeCase.title.replace(/[^\p{L}\p{N}_-]+/gu, "_")}.json`);
    setNotice("Дело экспортировано");
  }

  async function handleImportCase(file: File) {
    const text = await file.text();
    const bundle = JSON.parse(text);
    const response = await api.importCase(bundle);
    await loadCases();
    setActiveCaseId(response.case.id);
    setNotice(`Импортировано дело: ${response.case.title}`);
  }

  async function saveAISettings(payload: AISettings) {
    setAiSaving(true);
    try {
      const saved = await api.saveAISettings(payload);
      setAiSettings(saved);
      setAiSettingsOpen(false);
      setNotice(`Настройки ИИ сохранены: ${saved.provider} / ${saved.model}`);
    } finally {
      setAiSaving(false);
    }
  }

  async function generatePersonCardWithAI(sourceText: string) {
    setAiCardBusy(true);
    try {
      const generated = await api.aiPersonCard(sourceText);
      setNotice("ИИ собрал черновик карточки. Проверьте факты перед сохранением.");
      return generated;
    } finally {
      setAiCardBusy(false);
    }
  }

  async function generateParticipantDossierWithAI(): Promise<AIDossierResponse> {
    if (!draftParticipant) throw new Error("participant not selected");
    setAiDossierBusy(true);
    try {
      const generated = await api.aiDossier({ participant: draftParticipant, case: dossier?.case ?? null });
      setNotice("ИИ собрал краткое досье. Проверьте фактуру перед сохранением.");
      return generated;
    } finally {
      setAiDossierBusy(false);
    }
  }

  useEffect(() => {
    void Promise.all([loadCases(), loadPeople(), loadAISettings()]);
  }, []);

  useEffect(() => {
    if (activeCaseId) void Promise.all([loadParticipants(activeCaseId), loadCaseAnalytics(activeCaseId)]);
  }, [activeCaseId]);

  useEffect(() => {
    if (activeParticipantId) void loadDossier(activeParticipantId);
  }, [activeParticipantId]);

  useEffect(() => {
    if (!activePersonId || !comparePersonId) {
      setComparison(null);
      return;
    }
    void api.compareMatrices(activePersonId, comparePersonId).then(setComparison);
  }, [activePersonId, comparePersonId]);

  useEffect(() => {
    if (!activePersonId || !activeCaseId) {
      setCompatibility(null);
      return;
    }
    void api.getCaseCompatibility(activePersonId, activeCaseId).then(setCompatibility);
  }, [activePersonId, activeCaseId]);

  return (
    <main className="app-shell">
      <Sidebar
        view={view}
        onViewChange={setView}
        cases={cases}
        activeCaseId={activeCaseId}
        onSelectCase={setActiveCaseId}
        onCreateCase={createCase}
        onDeleteCase={removeCase}
        onPinCase={pinCase}
      />

      <section className="workspace">
        <header className="workspace-header workspace-header--stacked">
          <div>
            <p className="eyebrow">Архив расследований</p>
            <h1>{view === "cases" ? activeCase?.title ?? "Выберите дело" : "Люди и профильные карты"}</h1>
            <p className="workspace-subtitle">
              {view === "cases"
                ? activeCase
                  ? `${activeCase.classification} · ${activeCase.status}`
                  : "Сначала выберите дело"
                : "Реестр людей, сравнение матриц, ИИ-черновики и аккуратная ручная работа без визуального мусора"}
            </p>
          </div>

          <div className="workspace-actions">
            {view === "cases" ? (
              <button className="ghost" onClick={() => setLiveBoard((current) => !current)}>
                {liveBoard ? "Скрыть доску" : "Живая доска"}
              </button>
            ) : null}
            <button className="ghost" onClick={() => setAiSettingsOpen(true)}>
              Настройки
            </button>
          </div>

          <div className="workspace-status">
            <div className="metric-strip">
              <span>Людей в реестре: {people.length}</span>
              <span>Участников в деле: {participants.length}</span>
              <span>Высокий риск: {highRisk}</span>
            </div>
            <div className="status-box">{notice}</div>
          </div>
        </header>

        <ArchiveSearchPanel
          query={archiveQuery}
          results={archiveResults}
          onQueryChange={(value) => void handleArchiveSearch(value)}
          onPickResult={(item) => void handleArchivePick(item)}
        />

        {view === "people" ? (
          <>
            <PeopleRegistryPanel
              people={people}
              activePersonId={activePersonId}
              activePerson={activePerson}
              cases={cases}
              activeCaseId={activeCaseId}
              onSelectPerson={(id) => {
                setCreatingPerson(false);
                setActivePersonId(id);
              }}
              onStartCreate={() => {
                setCreatingPerson(true);
                setActivePersonId(null);
              }}
              onCreatePerson={createPerson}
              onSavePerson={savePerson}
              onDeletePerson={removePerson}
              onPinPerson={pinPerson}
              onAssignToCase={addPersonToCase}
              onUploadPhoto={uploadPhoto}
              onPersistPhoto={persistPersonPhoto}
              photoUploading={photoUploading}
              onGenerateWithAI={generatePersonCardWithAI}
              aiBusy={aiCardBusy}
            />
            <MatrixComparePanel
              people={people}
              activePersonId={activePersonId}
              comparePersonId={comparePersonId}
              onComparePersonIdChange={setComparePersonId}
              comparison={comparison}
              compatibility={compatibility}
            />
          </>
        ) : (
          <>
            <section className="top-grid top-grid--wide">
              <RelationshipSearchPanel
                query={searchQuery}
                loading={false}
                results={searchResults}
                onQueryChange={setSearchQuery}
                onSubmit={runSearch}
                onPickParticipant={setActiveParticipantId}
              />
              <CaseParticipantsPanel
                caseTitle={activeCase?.title ?? "Дело не выбрано"}
                participants={participants}
                activeParticipantId={activeParticipantId}
                onSelectParticipant={setActiveParticipantId}
                onPinParticipant={pinParticipant}
              />
            </section>

            <LiveBoardPanel active={liveBoard} graph={graph} brief={brief} participants={participants} />

            <section className="analytics-grid">
              <CaseGraphPanel graph={graph} />
              <AutoBriefPanel brief={brief} />
            </section>

            <DossierCard
              dossier={dossier}
              draft={draftParticipant}
              onChange={(patch) => setDraftParticipant((current) => (current ? { ...current, ...patch } : current))}
              onSave={saveParticipant}
              onPin={(pinned) => {
                if (draftParticipant) void pinParticipant(draftParticipant.id, pinned);
              }}
              onGeneratePdf={generatePdf}
              onGenerateBoardPdf={generateBoardPdf}
              onUploadPhoto={uploadPhoto}
              onPersistPhoto={persistParticipantPhoto}
              onAddEvidence={addEvidence}
              onDeleteEvidence={removeEvidence}
              onAddEvent={addEvent}
              onDeleteEvent={removeEvent}
              onAddRelation={addRelation}
              onDeleteRelation={removeRelation}
              photoUploading={photoUploading}
              onGenerateAIDossier={generateParticipantDossierWithAI}
              aiBusy={aiDossierBusy}
            />
          </>
        )}
      </section>

      <AISettingsPanel
        open={aiSettingsOpen}
        settings={aiSettings}
        saving={aiSaving}
        activeCaseTitle={activeCase?.title ?? null}
        onClose={() => setAiSettingsOpen(false)}
        onSave={saveAISettings}
        onExportCase={handleExportCase}
        onImportCase={handleImportCase}
      />
    </main>
  );
}

export default App;
