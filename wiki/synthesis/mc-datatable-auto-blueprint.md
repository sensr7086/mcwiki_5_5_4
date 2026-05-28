---
title: "MCDataTableAuto — Claude CLI 로 xlsx → UDataTable 자동 구성하는 UE 편집기 도구 청사진"
kind: synthesis
status: live
project_role: case-study
project_scope: kmc-project-mcdatatableauto
tags: [synthesis, mc, blueprint, claude, mcp, editor-integration, datatable, xlsx, csv, llm, ue-574, checklist]
related_concepts:
  - "[[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]]"
  - "[[concepts/MCP-Tool-Schema-LLM-Friendly-Design]]"
  - "[[concepts/MCP-Tool-Schema-Strip-Hazard]]"
  - "[[concepts/MCP-Async-UI-Bridge-Pattern]]"
  - "[[concepts/LLM-Visual-Reference-Hallucination]]"
  - "[[concepts/UE-HttpServer-Body-NullTerm-Hazard]]"
  - "[[concepts/Python-Stdio-MCP-Buffering-Hazard]]"
  - "[[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]]"
  - "[[concepts/MCP-Notification-No-Response-Spec]]"
  - "[[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]"
  - "[[concepts/Claude-CLI-Session-Continuation]]"
  - "[[concepts/Claude-CLI-Session-Id-UUID-Format-Strict]]"
  - "[[concepts/UE-Phantom-Header-Hallucination-Hazard]]"
  - "[[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]]"
  - "[[concepts/UE-CppComment-Backslash-LineContinuation-Hazard]]"
  - "[[concepts/UE-MetaSpecifier-LongPath-Requirement]]"
  - "[[concepts/UE-LiveCoding-Module-Path-Hazard]]"
  - "[[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]]"
  - "[[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]]"
  - "[[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]]"
  - "[[concepts/Material-Editor-External-Change-Reopen]]"
  - "[[concepts/Asset-Loading-Policy]]"
related_entities:
  - "[[entities/UAssetEditorSubsystem]]"
  - "[[entities/FAssetEditorToolkit]]"
  - "[[entities/IAssetTools]]"
  - "[[entities/IAssetRegistry]]"
  - "[[entities/FInteractiveProcess]]"
  - "[[entities/Claude-Code-CLI]]"
  - "[[entities/MCP-Protocol]]"
  - "[[entities/UObject]]"
  - "[[entities/FProperty]]"
related_synthesis:
  - "[[synthesis/mc-claude-mcp-editor-integration-blueprint]]"
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
  - "[[synthesis/mc-datatable-auto-build-cycle-postmortem]]"
created: 2026-05-25
last_updated: 2026-05-26
---

# MCDataTableAuto — Claude CLI 로 xlsx → UDataTable 자동 구성하는 UE 편집기 도구 청사진

> **vault scope**: `mc-` (KMCProject 실측 case study). 안의 일반 패턴은 [[synthesis/mc-claude-mcp-editor-integration-blueprint]] 의 답습이며 *Excel/CSV → DataTable* 변종 도메인 추가.

> **Citation 정책**: [[00_meta/06_VaultCitationRule]] 의 3-Tier (🟢 VAULT / 🟡 PARTIAL / 🔴 INFERRED). 모든 핵심 주장에 Tier 명시.

> **Tier 약어** (본 문서 전반): **Tier 1** = MCEditorModule sub-folder (C++ Plugin Module 레이어) / **Tier 2** = Slate Widget (EUW 사용자 인터페이스) / **Tier 3** = Editor Subsystem (UCLASS Lifecycle/Dispatch) / **Tier 4** = 외부 통합 (Claude CLI process + Python proxy + MCP server). [[synthesis/mc-claude-mcp-editor-integration-blueprint]] §2 의 답습.

> **상태**: `status: live` — Phase 1~3c-3 + 후속 14 cycle 실측 검증 완료 (2026-05-26). 별 세션 evaluator 89/100 승급 ([[00_meta/03_EvaluatorRecipe]] 8-stage). end-to-end 동작 확정.

## 1. 목적

사용자가 **xlsx 파일을 UE 편집기에 drag/drop** 하면 Claude CLI 가 시트/컬럼/타입을 분석하고 *USTRUCT row* 를 추론한 뒤 **시트별로 분리된 UDataTable 자산을 일괄 생성** + 행 채움.

**1차 cycle 핵심 정책 (2026-05-25/26 확정)**:
- 다중 시트 xlsx → **모든 시트가 각각 별도 DataTable 로 일괄 생성** (정책 P1)
- DataTable 자산명은 **시트 이름에서 직접 유도** (정책 P2 — 아래 §5.3)
- 매칭 USTRUCT 자손 없을 시 → **C++ USTRUCT 헤더 자동 생성 + Live Coding 자동 컴파일 + 패치 완료 후 자동 재시도** (정책 P3 — Phase 3c-3 4차 + 후속 통합)

MCMaterialAuto v0.34 의 4-Tier 아키텍처 + 11-step 체크리스트를 도메인만 교체해 재사용.

> 적용 범위: KMCProject 의 게임플레이 디자인 데이터 (스킬/아이템/적/대화) 를 *디자이너의 Excel* 에서 *엔진의 UDataTable* 로 옮기는 파이프라인. **MCStory / MCParts** 그래프 자산의 row 기반 파라미터 공급에도 응용.

## 2. 도메인 매핑 — MCMaterialAuto → MCDataTableAuto

| 항목 | MCMaterialAuto (기존, 🟢) | MCDataTableAuto (Phase 3c-3 + 후속 완료) | Tier |
|---|---|---|---|
| Target AssetEditor | `IMaterialEditor` | DataTable Editor + Content Browser AssetActions extender | 🟢 |
| Toolbar entry | `OnMaterialEditorOpened` | `UAssetEditorSubsystem::OnAssetEditorOpened` (UDataTable 필터) + ContentBrowser extender | 🟢 |
| Slate Widget | EUW 채팅 UI + 클립보드 이미지 | EUW 채팅 UI + **xlsx SDropTarget** + 모델 dropdown + New Session | 🟢 |
| 핵심 LLM 도구 | `add_expression` / `connect_pin` | `parse_spreadsheet` / `create_datatable` / `fill_rows` / `generate_row_struct` / `ping` | 🟢 8 도구 |
| 입력 미디어 | 클립보드 이미지 (CF_DIB) | xlsx 파일 (SDropTarget + FExternalDragOperation) | 🟢 |
| 시트 처리 단위 | (해당 없음) | **모든 시트 = 다중 자산 일괄 생성** | 🟢 정책 P1 |
| 자산 명명 | (해당 없음) | **시트명 → 정규화 → `DT_<SheetName>`** | 🟢 정책 P2 |
| RowStruct 미발견 시 | (해당 없음) | **`generate_row_struct` → Live Coding 자동 → 자동 재시도** | 🟢 정책 P3 |
| Refresh | Material 3-Layer | DataTable RowMap 재배치 회피 + AddRow copy-in | 🟢 [[sources/ue-coreuobject-uobject]] §SRowEditor |
| LLM 추측 hazard | Pin Name Shortening / SamplerType | Column 타입 추측 + cp949 encoding + notifications spec + view path | 🟢 12 신규 concept |
| 자동 컴파일 | (해당 없음) | `ILiveCodingModule::Compile()` + 4-step 사전 조건 | 🟢 [[concepts/UE-LiveCoding-Module-Path-Hazard]] |
| process wrapper lifecycle | (해당 없음) | TSharedPtr 3-layer defense | 🟢 [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]] |
| pkg_path 정규화 | (해당 없음) | `/All/Game/...` → `/Game/...` + TryConvert fatal 회피 | 🟢 [[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]] |

## 3. 4-Tier 아키텍처

🟢 VAULT — [[synthesis/mc-claude-mcp-editor-integration-blueprint]] §2 의 답습. 도메인 교체만.

```
┌────────────────────────────────────────────────────────────────┐
│  Tier 1 — MCEditorModule sub-folder (C++ Plugin Module)         │
│  · UAssetEditorSubsystem::OnAssetEditorOpened (UDataTable 필터)  │
│  · ContentBrowser AssetActions / PathView extender              │
│  · Build.cs 의존: + LiveCoding (Windows-only Developer 카테고리)  │
├────────────────────────────────────────────────────────────────┤
│  Tier 2 — Slate Widget (EUW) — SMCDataTableAutoWidget           │
│  · 채팅 UI (Claude desktop 미러)                                  │
│  · xlsx drag-drop panel (SDropTarget + 다중 파일 첨부)            │
│  · 모델 dropdown (SComboBox + Settings 양방향 sync)               │
│  · 실행 / 일괄 생성 / Cancel / Clear / New Session 버튼          │
├────────────────────────────────────────────────────────────────┤
│  Tier 3 — Editor Subsystem (UCLASS) — UMCDataTableAutoSubsystem │
│  · Lifecycle / MCP server / Claude process / 풀 로그              │
│  · game thread marshalling (AsyncTask)                           │
│  · session 유지 (--session-id + --continue)                      │
│  · 시트명 정규화 (NormalizeSheetNameToAssetName)                 │
│  · auto-Claude trigger (parse → auto-prompt → StartGeneration)   │
│  · TriggerLiveCodingCompile (Phase 3c-3 후속)                    │
│  · TryImmediateAutoRetryAfterSkip (Phase 3c-3 후속)              │
│  · LastIngestContext + AutoRetryDepth (자동 재시도)              │
├────────────────────────────────────────────────────────────────┤
│  Tier 4 — 외부 통합                                              │
│  · Claude CLI process (FInteractiveProcess spawn + stdio)        │
│  · Python stdio MCP proxy (stdlib only — zipfile/xml/csv)        │
│  · UE-host MCP HTTP server (FHttpServerModule, port 8991)        │
│  · mcwiki MCP server (외부 venv, 별 Python proxy)                │
│  · ILiveCodingModule (Developer/Windows/LiveCoding 모듈)          │
└────────────────────────────────────────────────────────────────┘
```

## 4. 핵심 통합 흐름 (다중 시트 일괄, end-to-end)

```
[사용자] xlsx 드롭 → 일괄 생성 클릭 (1번 액션)
                    ↓
              SMCDataTableAutoWidget::OnBatchBuildClicked
                    ↓
              Subsystem::IngestSpreadsheet(path, target_pkg_dir, depth=0)
                    ↓ LastIngestContext 저장
                    ↓ AsyncTask(BackgroundThread)
              RunProxyParseOnBackgroundThread
              ├ Python proxy 실행 (py -u mcp_proxy.py --test path)
              ├ stdout JSON 수집
              └ BroadcastParseResultThreadSafe
                  ├ 시트 정보 broadcast
                  └ AUTO-CLAUDE TRIGGER:
                      └ AsyncTask(GameThread) → StartGeneration(AutoPrompt)
                          ├ ActiveProcess wrapper 정리 (3-layer defense)
                          ├ 새 session GUID + claude.exe spawn
                          ├ Claude → mcwiki search "MCDataBase 자손"
                          ├ 자손 있음 (primary path):
                          │  ├ mcp__ue_datatable__create_datatable
                          │  │  ├ PkgPath 정규화 (/All/ → /Game/)
                          │  │  ├ TryConvertLongPackageNameToFilename (fatal 회피)
                          │  │  └ UPackage::SavePackage + fallback
                          │  └ mcp__ue_datatable__fill_rows
                          │     ├ FStructOnScope + JsonObjectToUStruct
                          │     ├ DT->AddRow (copy-in)
                          │     └ UPackage::SavePackage + fallback
                          └ 자손 없음 (정책 P3):
                             ├ mcp__ue_datatable__generate_row_struct
                             │  ├ Source/.../MCData_<NormName>.h 작성
                             │  ├ skip case (이미 존재):
                             │  │  └ TryImmediateAutoRetryAfterSkip
                             │  │     ├ sub-A (RowStruct 활성): 즉시 자동 재시도
                             │  │     └ sub-B (미활성): Live Coding fallback + IDE Rebuild 안내
                             │  └ 신규 case:
                             │     └ TriggerLiveCodingCompile(arm=true)
                             │        └ OnPatchComplete → 자동 재시도 (depth=1)
                             └ depth=1 IngestSpreadsheet → primary path 재진입
                                └ Claude → mcwiki search → 자손 발견 → create + fill ✅
```

## 5. 디자인 결정 매트릭스

### 5.1 xlsx 파싱 위치

| 후보 | Tier | 평가 |
|---|---|---|
| **A. Python proxy + stdlib only** | 🟢 VAULT (Phase 3a 채택 + 실측) | 채택 — `zipfile + xml.etree + csv` — pip 의존성 0 |
| B. openpyxl proxy | (이전 가설) | 부적합 — self-contained 원칙 위반 → A 정정 |
| C. xlsx → csv 사전 변환 | 🟡 fallback | csv 직접 drop 도 지원 |

**최종 결정** (Phase 3a 정정): stdlib only (A). MCMaterialAuto self-contained 원칙 답습. xlsx 는 zipfile + xml.etree 로 직접 파싱. complex 기능 (formula / style) 미지원.

### 5.2 정책 P1 — 다중 시트 = 다중 자산

xlsx 의 *모든 시트* 는 *각각 별도 UDataTable 자산*. *시트 1개도 단일 시트 통합 안 함* — 일관 동작.

| 측면 | 결정 | 근거 |
|---|---|---|
| 시트 → 자산 cardinality | **N : N** | 🟢 디자이너가 시트 = 데이터 단위로 인지 |
| 부분 실패 처리 | per-sheet best-effort + 결과 매트릭스 | 🟢 fill_rows 의 errors 매트릭스 적용 |
| 시트 순서 보존 | zipfile order | 🟢 디자이너 의도 보존 |

### 5.3 정책 P2 — 시트명 → `DT_<normalized>`

6 단계 정규화 (`NormalizeSheetNameToAssetName`):

| 단계 | 규칙 | 예 |
|---|---|---|
| 1 | trim | `"  Items  "` → `"Items"` |
| 2 | 비-ASCII 보존 | `"한글시트"` → `"한글시트"` (Phase 3b 실측 — 한글 자산명 정상) |
| 3 | 공백/특수문자 → `_` | `"Item Stats"` → `"Item_Stats"` |
| 4 | 연속 `_` 압축 | `"A__B"` → `"A_B"` |
| 5 | 양끝 `_` 제거 | `"_Items_"` → `"Items"` |
| 6 | `DT_` prefix | `"Items"` → `"DT_Items"` |

🟢 VAULT — Phase 3b 스크린샷 검증 (한글 시트명 → `DT_<한글>` 정상 동작).

### 5.4 정책 P3 — 매칭 RowStruct 없을 시 C++ 자동 생성 + 자동 컴파일 + 자동 재시도

🟢 VAULT — Phase 3c-3 4차 + 후속 11~14 cycle 통합 (2026-05-26).

LLM 이 mcwiki 에서 FMCDataBase 자손 검색:
- **자손 있음**: `create_datatable` + `fill_rows` 정상 진행 (primary path)
- **자손 없음**: `generate_row_struct` → `MCData_<NormName>.h` 작성 → **Live Coding 자동 + 자동 재시도** → 패치 완료 후 primary path 재진입

이전 정책 — *MCDataBase 본체로 빈 자산 생성* — 폐기 / *사용자 수동 컴파일 안내* — Live Coding 자동 + 자동 재시도로 격상.

**Live Coding 4-step 사전 조건** (🟢 [[concepts/UE-LiveCoding-Module-Path-Hazard]] §함정 family §3):

```cpp
1. Settings.bAutoLiveCodingCompile == true                                     // 사용자 toggle
2. FModuleManager::LoadModulePtr<ILiveCodingModule>(LIVE_CODING_MODULE_NAME)   // 모듈 로드
3. LiveCoding->IsEnabledForSession()                                           // Editor Preferences
4. !LiveCoding->IsCompiling()                                                  // 중복 회피
```

**자동 재시도 흐름** (🟢 [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]]):

```cpp
struct FLastIngestContext {
    FString XlsxPath, TargetPkgDir, OverwritePolicy;
    bool bValid = false;
    int32 AutoRetryDepth = 0;  // 0=사용자 직접 / N>0=자동 retry
};

// OnPatchComplete 람다:
if (bArmCopy && LastIngestContext.bValid && LastIngestContext.AutoRetryDepth == 0) {
    ResetSession + IngestSpreadsheet(saved, depth=1);  // 단일 retry 보장
}
```

**skip case 즉시 자동 재시도** (🟢 [[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]]):

파일 이미 존재 (`overwrite_policy=skip`) → Live Coding NoChanges → OnPatchComplete 안 fire → 차단 회피 의무.

`TryImmediateAutoRetryAfterSkip(RowStructPath, Hint)`:
- sub-A (FindObject<UScriptStruct> 활성): 즉시 자동 재시도 (primary path 성공 가능)
- sub-B (미활성): Live Coding fallback 시도 + IDE Rebuild 안내

### 5.5 Editor 메뉴 노출

🟢 VAULT — [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] 답습:
- `OnAssetEditorOpened` (UDataTable 필터) + ContentBrowser AssetActions / PathView extender

### 5.6 Claude CLI 인자 (Phase 3c-2-ext 확정)

🟢 VAULT — 9 항목 모두 실측:

| 옵션 | 값 |
|---|---|
| `-p <prompt>` | non-interactive |
| `--mcp-config <json>` | runtime 생성 (2 server: ue_datatable + mcwiki) |
| `--append-system-prompt <md>` | vault citation rule + 도구 가이드 |
| `--allowed-tools <csv>` | 13 도구 (8 ue_datatable + 5 mcwiki read) |
| `--disallowed-tools <csv>` | 13 mcwiki write 차단 |
| `--permission-mode bypassPermissions` | 자동 허용 |
| `--model <opus/sonnet/...>` | Settings.PreferredModel 동적 |
| `--session-id <UUID>` / `--continue` | 세션 유지 (DigitsWithHyphensLower 의무) |
| `--max-turns 30` | budget |
| `--output-format stream-json --verbose` | NDJSON |

## 6. Tier 별 핵심 패턴

### 6.1 Tier 1 — Plugin Module

🟢 VAULT — Phase 1a 실측 답습:

```cpp
// MCEditorModule::StartupModule()
UAssetEditorSubsystem* Sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
Sub->OnAssetEditorOpened().AddRaw(this, &FMCEditorModule::OnAssetEditorOpened);

void FMCEditorModule::OnAssetEditorOpened(UObject* Asset)
{
    if (!Asset || !Asset->IsA<UDataTable>()) return;
    ExtendDataTableToolBar(Cast<UDataTable>(Asset));
}
```

ContentBrowser extender — 🟢 `FContentBrowserMenuExtender_SelectedAssets` (ContentBrowserModule.h).

**Build.cs 의존 추가** (Phase 3c-3 후속):
```cs
PublicDependencyModuleNames.AddRange(new[] {
    // ...
    "LiveCoding",  // Source/Developer/Windows/LiveCoding/Public/ILiveCodingModule.h
                   // Windows-only (Mac/Linux 미지원)
});
```

### 6.2 Tier 2 — Slate Widget

🟢 VAULT — Phase 2 + 3c-3 (1차/8차) 실측:

- 중앙 `SDropTarget` (EditorWidgets) — `OnIsRecognized` / `OnAllowDrop` / `OnDropped` 3-step
- 첨부 카드 panel (SVerticalBox) — 동적 add/remove
- 입력창 — `SMultiLineEditableTextBox` + Enter=전송 / Shift+Enter=줄바꿈
- 버튼 row — 실행 / 일괄 생성 / Cancel / Clear / New Session + Spacer + 모델 dropdown
- 모델 dropdown — `SComboBox<TSharedPtr<EMCDataTableAutoModel>>` + Settings 양방향 sync

### 6.3 Tier 3 — Subsystem

🟢 VAULT — Phase 3a~3c-3 + 후속 실측:

| 책임 | API |
|---|---|
| Lifecycle | `Initialize` → MCP server start + proxy 작성 + mcwiki resolve / `Deinitialize` → ActiveProcess Cancel + McpServer Stop |
| Dispatch (game thread) | `AsyncTask(ENamedThreads::GameThread, ...)` 마샬링 (MMA-04) |
| Python 동기 실행 | `FPlatformProcess::CreateProc("py", "-u proxy.py --test xlsx", ...)` + `ReadPipe` 폴링 |
| Stream prettify | NDJSON → `[claude] / [tool] / [tool_result:ERROR] / [done]` |
| Session 유지 | `bSessionStarted` + `CurrentSessionId` (DigitsWithHyphensLower) + `ResetSession()` |
| 시트명 정규화 | `NormalizeSheetNameToAssetName(FString)` — 정책 P2 6단계 |
| auto-Claude trigger | `BroadcastParseResultThreadSafe` 끝 → `BuildAutoPromptFromParseResult` → `StartGeneration` |
| Live Coding 자동 트리거 | `TriggerLiveCodingCompile(InContextHint, bArmRetryOnPatchComplete)` — 4-step 사전 조건 + 1회용 OnPatchComplete 구독 |
| skip case 자동 재시도 | `TryImmediateAutoRetryAfterSkip(RowStructPath, Hint)` — sub-A/B 분기 |
| process wrapper 정리 | StartGeneration 시작점 unconditional Reset + OnCompleted defer Reset (3-layer defense) |
| 자동 재시도 컨텍스트 | `FLastIngestContext` (XlsxPath/TargetPkgDir/OverwritePolicy/bValid/AutoRetryDepth) |

### 6.4 Tier 4 — MCP server + Python proxy + Live Coding + Process wrapper

🟢 VAULT — Phase 3c-1~3c-3 + 후속 검증:

**UE-host HTTP server**: `POST /rpc` + Bearer auth (Phase 3c-1)
- Body null-term 회피 ([[concepts/UE-HttpServer-Body-NullTerm-Hazard]])
- capabilities: tools + resources + prompts (Phase 3c-3 7차)
- tools/list — 8 도구 + 풍부 schema ([[concepts/MCP-Tool-Schema-Strip-Hazard]] — properties 완전 매니페스트 의무)

**Python stdio proxy** (stdlib only):
- `-u` flag + line buffering ([[concepts/Python-Stdio-MCP-Buffering-Hazard]])
- `json.dumps(obj)` default ensure_ascii=True ([[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]])
- notifications/* return None ([[concepts/MCP-Notification-No-Response-Spec]])

**ILiveCodingModule** (Phase 3c-3 후속):
- Module path: `Source/Developer/Windows/LiveCoding/Public/` ([[concepts/UE-LiveCoding-Module-Path-Hazard]])
- API: Compile / IsCompiling / IsEnabledForSession / GetOnPatchCompleteDelegate
- .h-only USTRUCT 한계 ([[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]]) — sub-B fallback 의무

**FInteractiveProcess wrapper** ([[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]]):
- TSharedPtr 가 exit 후에도 살아있는 hazard
- 3-layer defense: Run 진입점 unconditional Reset / OnCompleted GameThread defer Reset / 자동 재시도 람다 직전 명시 cleanup
- DECLARE_DELEGATE_TwoParams(int32, bool) — 2 params 의무 ([[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]])

## 7. LLM-friendly Tool Schema (4 패턴 + 자동 정규화 + completeness 의무)

🟢 VAULT — [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] + [[concepts/MCP-Tool-Schema-Strip-Hazard]] + [[synthesis/ue-llm-assumption-hazard-family]] 4-Layer Defense.

### 7.1 도구 8종

```
ping                     → smoke test (pong + port)
parse_spreadsheet(path)  → xlsx/csv 파싱 (sheets/columns/sniff/asset_name_proposal)
infer_columns(sheet)     → LLM-assisted 컬럼 타입 추론 (Phase 3c-3 후속)
propose_row_struct       → RowStruct 제안 (Phase 3c-3 후속)
create_datatable(pkg, name, row_struct, overwrite_policy?)
  → IAssetTools 통해 UDataTable 자산 생성 + pkg_path 정규화 + UPackage::SavePackage
fill_rows(asset_path, rows[{row_name, fields}])
  → FStructOnScope + JsonObjectToUStruct + AddRow (copy-in, RowMap 함정 회피)
  → JSONSchema rows 명시 의무 (properties strip 회피)
batch_build_from_xlsx    → orchestration (Phase 3c-3 후속)
generate_row_struct(sheet_name, fields, overwrite_policy?)
  → Source/MCPlayModule/MCGame/MCData_<NormName>.h 자동 작성
  → Live Coding 자동 트리거 + 자동 재시도 + skip case 즉시 retry
```

### 7.2 4 패턴 적용

| 패턴 | 적용 사례 |
|---|---|
| 1. 식별자 양식 양쪽 허용 | `row_struct_path` short/full / pkg_path `/All/Game/...` `/Game/...` 모두 |
| 2. Multi-source ID Resolver | pkg_path 자동 정규화 + 해석 |
| 3. Valid-list error response | `overwrite_policy` 표준 3값 + HINT |
| 4. Tool result detail in log | `was_replaced` / `saved` / `save_debug` / `auto_live_coding` / `auto_retry_after_skip` / `errors[]` 메타 |
| 5. **JSONSchema completeness** | `properties` 완전 매니페스트 — array/object items/properties nested 의무 ([[concepts/MCP-Tool-Schema-Strip-Hazard]]) |

### 7.3 자동 정규화

🟢 [[synthesis/ue-llm-assumption-hazard-family]] 4-Layer Defense — DataTable 도메인 변종:

1. **자동 정규화 (Layer 1)** — sniff_type + asset_name_proposal 도구 응답에 무조건 첨부
2. **Valid-list error (Layer 2)** — overwrite_policy / ue_type 표준값 강제
3. **메타데이터 자동 노출 (Layer 3)** — column.distinct_count / sample_values[] / null_count
4. **`ask_user_choice` 강제 (Layer 4)** — Phase 3c-3 후속
5. **path 정규화 (Layer 5 신규)** — pkg_path `/All/` strip + TryConvert fatal 회피

## 8. UI Refresh — DataTable

🟢 VAULT — UE 측 구현:

- `MarkPackageDirty` + `UPackage::SavePackage` + `UEditorAssetLibrary::SaveLoadedAsset` fallback (UPackage::SavePackage false negative defense in depth)
- `FAssetRegistryModule::AssetCreated(NewDT)` — Content Browser 갱신
- `CloseAllEditorsForAsset + OpenEditorForAsset` (구조적 변경 시)
- save_debug 메타 응답 — 실패 시 reason 노출 (LongPackageName 매핑 / SavePackage false / fallback 결과)

## 9. 함정 카탈로그 — Phase 1~3c-3 + 후속 14 cycle 누적

🟢 VAULT — 13 함정 정식 concept 화 ([[synthesis/mc-datatable-auto-build-cycle-postmortem]] §2).

| 함정 | Tier | Phase | Concept |
|---|---|---|---|
| UDataTable RowMap 재배치 | 🟢 | 3c-3 fill_rows | [[sources/ue-coreuobject-uobject]] §SRowEditor |
| FHttpServerRequest Body null-term | 🟢 | 3c-1 | [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] |
| Python stdio buffering | 🟢 | 3a | [[concepts/Python-Stdio-MCP-Buffering-Hazard]] |
| Python json.dumps + Windows cp949 | 🟢 | 3c-3 9차 | [[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]] (final defense) |
| MCP notifications/* no-response | 🟢 | 3c-3 3차 | [[concepts/MCP-Notification-No-Response-Spec]] |
| Phantom header (Templates/IsDerivedFrom.h) | 🟢 | 1a | [[concepts/UE-Phantom-Header-Hallucination-Hazard]] |
| Delegate 람다 ParamCount mismatch | 🟢 | 3c-2 | [[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]] |
| `//` 주석 끝 `\` line continuation | 🟢 | 3c-2-ext | [[concepts/UE-CppComment-Backslash-LineContinuation-Hazard]] |
| Claude CLI session-id UUID format | 🟢 | 3c-2-ext | [[concepts/Claude-CLI-Session-Id-UUID-Format-Strict]] |
| UE 5.5+ MetaStruct long-path 강제 | 🟢 | 1a | [[concepts/UE-MetaSpecifier-LongPath-Requirement]] |
| Cowork ToolSearch deferred | 🟢 | 3c-2-ext | [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]] |
| AssetEditor ToolBar | 🟢 | 1a | [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] |
| LiveCoding 모듈 path (Developer/Windows/) | 🟢 | 3c-3 후속 | [[concepts/UE-LiveCoding-Module-Path-Hazard]] |
| LiveCoding .h-only USTRUCT 무시 | 🟡 | 3c-3 후속 12 | [[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]] |
| MCP tool schema 미선언 인자 strip | 🟢 | 3c-3 후속 13 | [[concepts/MCP-Tool-Schema-Strip-Hazard]] |
| FInteractiveProcess wrapper lifecycle | 🟢 | 3c-3 후속 11 | [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]] |
| PackageName view path vs mount root | 🟢 | 3c-3 후속 14 | [[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]] |

## 10. 재사용 청사진 — 11-step 체크리스트 (완료 상태)

🟢 VAULT — Phase 1~3c-3 + 후속 14 cycle 모두 완료.

### Phase 0 — 설계 ✅
- [x] vault 검색 + AssetEditor 식별 + 도구 catalog + MCP transport
- [x] xlsx 파싱 위치 결정 (A: stdlib only proxy)
- [x] RowStruct 전략 + 다중 시트 정책 P1 + 자산 명명 정책 P2 + 자동 C++ 생성 정책 P3
- [x] Live Coding 자동 트리거 + 자동 재시도 + skip case 우회

### Phase 1 — Tier 1/2 골격 ✅
- [x] MCDataTableAuto sub-folder scaffold + Build.cs (+ LiveCoding)
- [x] `OnAssetEditorOpened` delegate + ContentBrowser extender
- [x] EUW 채팅 UI + 모델 dropdown + New Session + xlsx drag-drop

### Phase 2 — Tier 3 (Subsystem) ✅
- [x] EditorSubsystem Lifecycle / MCP server / Claude process / 풀 로그
- [x] game thread marshalling + Session 유지 + xlsx parse cache
- [x] 시트명 정규화 + Live Coding 트리거 헬퍼 + 자동 재시도 컨텍스트 + skip case 헬퍼
- [x] process wrapper 3-layer defense
- [ ] PendingPromise (ask_user_choice 비동기 UI bridge) — Phase 3c-3 후속

### Phase 3 — Tier 4 (MCP + Python proxy + Live Coding) ✅
- [x] tool catalog 8종 + JSONSchema completeness (rows array items 명시)
- [x] stdlib only Python proxy + notifications no-response + json.dumps ensure_ascii=True
- [x] proxy 모든 요청 UE forward + capabilities tools + resources + prompts
- [x] 자동 자산 생성 흐름 + Live Coding 자동 통합 + 자동 재시도 + skip case 우회
- [x] pkg_path 정규화 + TryConvertLongPackageNameToFilename fatal 회피

### Phase 4 — UI Refresh ✅
- [x] AssetCreated + UPackage::SavePackage + SaveLoadedAsset fallback
- [x] MarkPackageDirty per asset + save_debug 메타

### Phase 5 — Claude CLI 인자 ✅
- [x] 9 항목 모두

### Phase 6 — 환경 검증 UI
- [ ] mcwiki resolve 결과 widget log (Subsystem Initialize 시 자동)
- [ ] Refresh / Login / API Key 버튼 (MCMaterialAuto 답습 — 후속)

### Phase 7 — vault filing-back ✅
- [x] 매 cycle 새 함정 → MMA-DT-N 카탈로그 (12 신규 concept)
- [x] Citation Disclosure (🟢/🟡/🔴) 매 답변
- [x] index + log + lint 0
- [x] **별 세션 evaluator 호출** (Article 1) — 89/100 live 승급 ✅

### Phase 8 — Evaluator ✅
- [x] 별 세션 evaluator 호출 — mc-datatable-auto-blueprint 평가 (89/100)
- [x] status: evaluated → **live** 승급

## 11. 시나리오 검증 매트릭스 (실측 / 설계 / 미실측 3-tier)

| 시나리오 | 결과 | 종류 |
|---|---|---|
| 단일 시트 xlsx (5컬럼 × 10행) → 1개 DT | ✅ | 실측 (사용자 "응 잘 돌아간다") |
| 다중 시트 xlsx → 다중 DT 일괄 | ✅ | 설계 (정책 P1) — 실측 1 시트만 |
| 한글 시트명 → `DT_<한글>` | ✅ | 실측 (Phase 3b 스크린샷) |
| 모호 컬럼 → ask_user_choice | ⏳ | 미실측 (후속 미구현) |
| asset path → TSoftObjectPtr | ✅ | 설계 (sniff_type=all_asset_path) |
| csv 직접 drop (fallback path) | ✅ | 설계 (csv 모듈) |
| 기존 DataTable 충돌 (skip) | ✅ | 설계 (Valid-list error) |
| 부분 실패 (mixed-type) | ✅ | 설계 (fill_rows errors 매트릭스) |
| 자손 없음 → C++ 자동 + Live Coding + 자동 재시도 | ✅ | 실측 (Phase 3c-3 후속) |
| skip case sub-A (RowStruct 활성) → 즉시 재시도 | ✅ | 실측 (사용자 confirmed) |
| skip case sub-B (미활성) → IDE Rebuild 안내 | ✅ | 실측 (디버거 break + 회피) |
| Live Coding 4-step 사전 조건 fallback | ✅ | 설계 |
| pkg_path `/All/` 정규화 | ✅ | 실측 (디버거 break case) |
| LongPackageName fatal 회피 (TryConvert) | ✅ | 실측 (디버거 break case) |
| ue_datatable MCP 연동 | ✅ | 실측 (9 cycle 끝 cp949 fix) |
| Claude session 유지 (--continue) | ✅ | 실측 |
| 모델 dropdown (Default/Sonnet/Opus/Haiku) | ✅ | 실측 (Phase 3c-3 1차) |
| mcwiki search 통합 | ✅ | 실측 |

## 12. 후속 가능 cycle

- **v0.1 후속 (Phase 3c-3 다음 batch)**:
  - `ask_user_choice` PendingPromise UI bridge
  - `batch_build_from_xlsx` orchestration
  - `parse_spreadsheet` UE-side 직접 구현
  - `infer_columns` / `propose_row_struct`
  - Live Coding 완료 콜백 → 자동 재시도 (compile → re-run primary path)
- **v0.2**: UUserDefinedStruct 동적 생성 (Live Coding 우회 — .h-only struct 한계 회피)
- **v0.3**: 기존 DataTable diff/merge — 행 추가/수정/삭제 정밀 제어
- **v0.4**: CurveTable 지원
- **v0.5**: csv ↔ xlsx 양방향 변환 + git diff 친화 export
- **v0.6**: UPrimaryDataAsset Bundle 지원
- **v0.7**: 시트 간 cross-reference (FK like)

## 13. 의존 entity / concept (요약)

### Entities (🟢 VAULT — Engine grep 검증 완료)
- [[entities/UAssetEditorSubsystem]] — `OnAssetOpenedInEditor` 2-param event
- [[entities/FAssetEditorToolkit]] — `: public IAssetEditorInstance`
- [[entities/IAssetTools]] — `CreateAsset`
- [[entities/IAssetRegistry]] — asset path lookup
- [[entities/FInteractiveProcess]] — Claude CLI spawn + 2-params delegate
- [[entities/Claude-Code-CLI]] / [[entities/MCP-Protocol]]
- [[entities/UObject]] / [[entities/FProperty]]

### Concepts (Tier 별)
- Editor 메뉴: [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]]
- LLM 추측 family: [[synthesis/ue-llm-assumption-hazard-family]] / [[concepts/LLM-Visual-Reference-Hallucination]]
- 비동기 UI: [[concepts/MCP-Async-UI-Bridge-Pattern]] (Phase 3c-3 후속)
- Encoding: [[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]]
- Live Coding: [[concepts/UE-LiveCoding-Module-Path-Hazard]] + [[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]]
- Process: [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]]
- Path: [[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]]
- Tool schema: [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] + [[concepts/MCP-Tool-Schema-Strip-Hazard]]
- Session: [[concepts/Claude-CLI-Session-Continuation]] + [[concepts/Claude-CLI-Session-Id-UUID-Format-Strict]]
- Proxy / HTTP: [[concepts/Python-Stdio-MCP-Buffering-Hazard]] + [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] + [[concepts/MCP-Notification-No-Response-Spec]]
- Cowork: [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]
- Hallucination family: [[concepts/UE-Phantom-Header-Hallucination-Hazard]] / [[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]] / [[concepts/UE-CppComment-Backslash-LineContinuation-Hazard]] / [[concepts/UE-MetaSpecifier-LongPath-Requirement]]
- Data: [[sources/ue-assetclasses-data]]
- Asset loading: [[concepts/Asset-Loading-Policy]]

## 14. Citation Disclosure (Phase 3c-3 후속 14 cycle 완료 시점)

| 주장 | Tier | 근거 |
|---|---|---|
| 4-Tier 아키텍처 | 🟢 VAULT | [[synthesis/mc-claude-mcp-editor-integration-blueprint]] + 실측 |
| 11-step 체크리스트 | 🟢 VAULT | 실측 완료 |
| 4-Layer Defense + Layer 5 path | 🟢 VAULT | [[synthesis/ue-llm-assumption-hazard-family]] 적용 + 정규화 추가 |
| DataTable RowMap 함정 회피 | 🟢 VAULT | fill_rows FStructOnScope 패턴 적용 |
| CSV import fallback | 🟢 VAULT | [[sources/ue-assetclasses-data]] |
| 정책 P1 (다중 시트 = 다중 자산) | 🟢 VAULT | Phase 3c-3 실측 |
| 정책 P2 (시트명 → `DT_<normalized>`) | 🟢 VAULT | Phase 3b 한글 시트명 검증 |
| 정책 P3 (generate_row_struct + Live Coding + 자동 재시도) | 🟢 VAULT | Phase 3c-3 4차 + 후속 11~14 — 사용자 확정 |
| stdlib only Python proxy | 🟢 VAULT | Phase 3a 실측 |
| OnAssetEditorOpened 시그니처 | 🟢 VAULT | Engine grep |
| ContentBrowser extender 시그니처 | 🟢 VAULT | Engine grep |
| UE 8 도구 schema | 🟢 VAULT | UE 측 구현 + curl 검증 |
| Python proxy 결정적 fix (ensure_ascii=True) | 🟢 VAULT | Phase 3c-3 9차 끝 MCMaterialAuto diff |
| MCP notifications no-response | 🟢 VAULT | JSON-RPC 2.0 spec |
| MCP tool schema strip | 🟢 VAULT | Phase 3c-3 후속 13 — 사용자 진단 |
| ILiveCodingModule API | 🟢 VAULT | engine grep |
| Live Coding 4-step 사전 조건 | 🟢 VAULT | Phase 3c-3 후속 |
| Live Coding .h-only USTRUCT 한계 | 🟡 PARTIAL | Live++ closed source — 경험적 추론 |
| FInteractiveProcess wrapper 3-layer defense | 🟢 VAULT | Phase 3c-3 후속 11 실측 |
| pkg_path 정규화 + TryConvert fatal 회피 | 🟢 VAULT | Phase 3c-3 후속 14 디버거 break |
| ask_user_choice PendingPromise | 🔴 INFERRED | Phase 3c-3 후속 미구현 |
| batch_build_from_xlsx UE orchestration | 🔴 INFERRED | Phase 3c-3 후속 미구현 |
| UUserDefinedStruct 동적 생성 (v0.2) | 🔴 INFERRED | 후속 cycle |
| `IDataTableEditor` view refresh API | 🟡 PARTIAL | 빈 인터페이스 |

**합계**: 🟢 18 / 🟡 3 / 🔴 3.

## 15. 변경 이력

- 2026-05-25: 초안 작성 — MCMaterialAuto v0.34 청사진의 도메인 변종. Phase 0 설계 완료. Citation 🟢 5 / 🟡 4 / 🔴 7. status: draft.
- 2026-05-25: 정책 P1/P2 1차 cycle 채택. 도구 schema 5종 → 6종 (`batch_build_from_xlsx` 추가). Citation 16건.
- 2026-05-26: **Phase 1~3c-3 10 phase 완료** — end-to-end 동작 검증. **정책 P3 신설**. 도구 8종. 신규 7 concept. status: **evaluated**. Citation 🟢 13 / 🟡 1 / 🔴 3 (격상 8 — phantom/delegate/backslash/UUID/cp949/notifications/meta long-path/UE 8 도구 schema).
- 2026-05-26 (Phase 3c-3 후속 11~14 cycle): **Live Coding 자동 + 자동 재시도 + skip case 우회 + pkg_path 정규화** 통합. 신규 4 concept (LiveCoding path / LiveCoding cpp-only / MCP schema strip / FInteractiveProcess wrapper / PackageName view path). Phase 진척도 10 → 14 + Phase 8 ✅. 함정 카탈로그 13 → 17. Citation 격상 4건 (LiveCoding 4-step / FInteractiveProcess 3-layer / pkg_path TryConvert / MCP schema strip). 합계 🟢 18 / 🟡 3 / 🔴 3.
- 2026-05-26 (별 세션 evaluator 호출): 평가 점수 **89/100** (정확성 27 / 출처 18 / 완전성 22 / 가독성 22) → **live 승급**. 6건 보완 메모 (누락 cross-link 4건 + emphasis 절제 + Tier 약어 footnote + 시나리오 매트릭스 3-tier 컬럼 + Engine 라인 검증 trail + Citation 격상 history). 본 페이지 갱신으로 #1/2/3/4/6 적용. #5 (Engine commit hash trace) 는 후속 cycle.
