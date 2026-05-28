---
title: "Claude ↔ UE Editor MCP Integration Blueprint — MCMaterialAuto 누적 학습"
kind: synthesis
status: stable
project_role: case-study
project_scope: kmc-project-mcmaterialauto
tags: [synthesis, mc, blueprint, claude, mcp, editor-integration, llm, ue-574, checklist]
related_concepts:
  - "[[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]]"
  - "[[concepts/UE-Material-Pin-Name-Shortening]]"
  - "[[concepts/MCP-Tool-Schema-LLM-Friendly-Design]]"
  - "[[concepts/MCP-Async-UI-Bridge-Pattern]]"
  - "[[concepts/LLM-Visual-Reference-Hallucination]]"
  - "[[concepts/UE-Texture-Sampler-Type-Auto-Inference]]"
  - "[[concepts/Windows-Clipboard-Image-Paste-UE]]"
  - "[[concepts/Claude-CLI-Session-Continuation]]"
  - "[[concepts/Material-Editor-External-Change-Reopen]]"
  - "[[concepts/Python-Stdio-MCP-Buffering-Hazard]]"
  - "[[concepts/UE-HttpServer-Body-NullTerm-Hazard]]"
  - "[[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]"
related_entities:
  - "[[entities/IMaterialEditor]]"
  - "[[entities/IMaterialEditorModule]]"
  - "[[entities/UMaterialEditingLibrary]]"
  - "[[entities/UAssetEditorSubsystem]]"
  - "[[entities/FInteractiveProcess]]"
  - "[[entities/Claude-Code-CLI]]"
  - "[[entities/MCP-Protocol]]"
related_synthesis:
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
created: 2026-05-22
last_updated: 2026-05-25
---

# Claude ↔ UE Editor MCP Integration Blueprint — MCMaterialAuto 누적 학습

## 1. 목적

KMCProject 의 **MCMaterialAuto** 플러그인 v0.2 → v0.34 의 33+ cycle 동안 누적된 *Claude CLI ↔ UE Editor 통합* 패턴 / 함정 / 디자인 결정을 **재사용 청사진** 으로 정리. 다음 비슷한 기능 (AI-driven Animation 자동화 / MaterialFunction 라이브러리 생성 / Niagara 자동화 등) 시작 시 **체크리스트** 로 활용.

> **vault scope**: `mc-` prefix — KMCProject 실측 사례. 안의 *일반 패턴* 들은 `ue-` 일반 concept 으로 격상됨.

## 2. 4-Tier 아키텍처

```
┌────────────────────────────────────────────────────────────────┐
│  Tier 1 — Editor Module (C++) — MCEditorModule.cpp              │
│  · IMaterialEditorModule::OnMaterialEditorOpened delegate       │
│  · ToolBar entry 동적 add (FToolMenuEntry::InitToolBarButton)   │
│  · Build.cs: UnrealEd/MaterialEditor/ToolMenus/ImageWrapper     │
├────────────────────────────────────────────────────────────────┤
│  Tier 2 — Slate Widget (EUW) — SMCMaterialAutoWidget            │
│  · 채팅 UI (Claude desktop 미러)                                  │
│  · 입력창 하단 / 메시지 흐름 중앙 / inline button row 한 줄        │
│  · Enter=전송 / Shift+Enter=줄바꿈 / 전송 후 PromptBox clear      │
│  · plain log + prefix 색상 (박스 없음)                             │
│  · 클립보드 이미지 paste (Ctrl+V) → thumbnail 카드 (v0.30/v0.31)  │
│  · 선택지 카드 (ask_user_choice — 노랑 강조, v0.32)               │
│  · New Session 버튼 (v0.33)                                       │
├────────────────────────────────────────────────────────────────┤
│  Tier 3 — Editor Subsystem (UCLASS) — UMCMaterialAutoSubsystem  │
│  · Lifecycle / MCP server / Claude process / 풀 로그              │
│  · game thread marshalling (AsyncTask)                           │
│  · session 유지 (--session-id + --continue, v0.33)                │
│  · PendingChoicePromise (TPromise 비동기 UI bridge, v0.32)        │
├────────────────────────────────────────────────────────────────┤
│  Tier 4 — 외부 통합                                              │
│  · Claude CLI process (FInteractiveProcess spawn + stdio)        │
│  · Python stdio MCP proxy (stdlib only, 재생성 가능)             │
│  · UE-host MCP HTTP server (FHttpServerModule)                  │
│  · mcwiki MCP mirror (read-only, UE 자체 구현)                   │
└────────────────────────────────────────────────────────────────┘
```

## 3. 핵심 통합 흐름 (도구 호출)

```
[사용자] Enter → SMCMaterialAutoWidget
                    ↓
                 OnGenerateClicked → Subsystem::StartGeneration(prompt)
                    ↓
                 FInteractiveProcess::Launch (claude -p ... --session-id ...)
                    ↓
                 stdio ← stdout (NDJSON stream-json)
                    ↓
                 Subsystem::PrettifyStreamJsonLine → OnLogLine broadcast
                    ↓
                 Widget::HandleLogLine → AppendLog (prefix 필터)
                    ↓ (병렬)
                 Claude CLI → 도구 호출
                    ↓
                 Python proxy (stdio ↔ HTTP)
                    ↓
                 UE MCP Server (FHttpServerModule)
                    ↓
                 Subsystem::DispatchToolCall
                    ├── 일반 도구 → AsyncTask GameThread → 동기 응답
                    └── ask_user_choice → PendingPromise + Widget broadcast (v0.32)
                                              ↓
                                           사용자 클릭 → SetValue → Future 해제
                    ↓
                 UMCMaterialAutoLibrary::Tool_* → UMaterialEditingLibrary
                    ↓
                 RefreshMaterialEditor (3-Layer)
                    ↓
                 JSON 응답 → Python proxy → Claude CLI
```

## 4. 디자인 결정 매트릭스

### 4.1 MCP transport
| 후보 | 선택 | 근거 |
|---|---|---|
| HTTP only | ❌ | Claude CLI 의 MCP client 가 stdio 우선 |
| stdio only | ❌ | UE-host server 가 HTTP 자연스러움 |
| **stdio + Python proxy → HTTP** | ✅ | 양쪽 최적 |

### 4.2 mcwiki 통합
| 후보 | 선택 | 근거 |
|---|---|---|
| 외부 mcwiki MCP (Python venv) | ❌ | venv 관리 비용 |
| Plugin merge | ❌ | claude CLI 가 mcwiki 별도 mount 안 됨 |
| **UE-host mcwiki mirror (read-only)** | ✅ | 의존성 0 + vault citation 유지 |

### 4.3 Claude CLI 인자 (v0.33 session 포함)
| 옵션 | 값 | 근거 |
|---|---|---|
| `-p <prompt>` | non-interactive | 자동화 필수 |
| `--mcp-config <json>` | runtime 생성 | proxy + UE port + auth token |
| `--allowed-tools <csv>` | 사전 명시 | Cowork deferred 우회 |
| `--disallowed-tools "ToolSearch,..."` | 차단 | vault read-only 강제 |
| `--permission-mode bypassPermissions` | 자동 허용 | non-interactive 의무 |
| `--model opus/sonnet/haiku/default` | UI dropdown | 사용자 선택 |
| **`--session-id <UUID>`** (v0.33) | 첫 호출 | session 명시 ID 생성 |
| **`--continue`** (v0.33) | 이후 호출 | 이전 대화 이어서 (또는 같은 session-id 재사용) |
| `--max-turns 30` | budget | 무한 루프 방지 |
| `--output-format stream-json --verbose` | NDJSON | 실시간 표시 |

### 4.4 Editor 메뉴 노출
| 후보 | 선택 | 근거 |
|---|---|---|
| `LevelEditor.MainMenu.Tools` | ❌ | Material Editor context 무관 |
| `AssetEditor.<App>.MainMenu.*` | ❌ | TabManager 시스템 → ExtendMenu stub (vault §2.9) |
| **`AssetEditor.MaterialEditorApp.ToolBar` via OnMaterialEditorOpened** | ✅ | [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] |

## 5. Tier 별 핵심 패턴

### 5.1 Tier 1 — Editor Module

`IMaterialEditorModule::OnMaterialEditorOpened` delegate + 1-arg `GetToolMenuToolbarName(FName&)` (C2660 hazard) + `NSLOCTEXT` (LOCTEXT_NAMESPACE 위치 무관) + 중복 add 방어 `FindEntry`.

### 5.2 Tier 2 — Slate Widget (v0.24-v0.34 UI 진화 누적)

채팅 UI 구조 (위→아래):
1. 메시지 흐름 — `SScrollBox` → `SVerticalBox` LogContent, FillHeight 1.0
2. **첨부 이미지 thumbnail 카드 panel** (v0.31) — `SHorizontalBox` 가로 배열, paste 시 동적 add, 빈 상태 0 height
3. 하단 입력창 — `SBorder` AutoHeight:
   - `SMultiLineEditableTextBox` PromptBox (MinDesiredHeight 80)
     - `.OnKeyDownHandler(&OnPromptKeyDown)` — Enter=전송 / Shift+Enter=줄바꿈 / **Ctrl+V=image paste** (v0.30)
     - `.HintText("메시지를 입력하세요... (Enter=전송, Shift+Enter=줄바꿈)")`
   - 한 줄 inline 버튼 row (v0.28): `[▷실행][Cancel][Clear][New Session](spacer)[Refresh][Login][API Key][Model▼]`

### 5.3 Tier 3 — Subsystem

| 책임 | API |
|---|---|
| Lifecycle | `Initialize` → MCP server start / `Deinitialize` → server stop + Cancel + 풀 로그 close |
| Dispatch (일반) | `AsyncTask(ENamedThreads::GameThread, ...)` 마샬링 |
| Dispatch (비동기 UI) | `ask_user_choice` 분기 → PendingPromise + Widget broadcast (v0.32, [[concepts/MCP-Async-UI-Bridge-Pattern]]) |
| 풀 로그 IO | `Saved/<plugin>/run-<ts>.log` + UTF-8 BOM + `\r\n` + flush per line |
| Stream prettify | NDJSON → `[claude]/[tool]/[tool_result:ERROR]/[done]/...` |
| Session 유지 | `bSessionStarted` + `CurrentSessionId` UUID + `ResetSession()` (v0.33) |

### 5.4 Tier 4 — MCP server + Python proxy

**UE-host HTTP server**: `/rpc/ue_material` (Material 도구) + `/rpc/mcwiki` (read-only mirror). Body **null-terminate 의무** ([[concepts/UE-HttpServer-Body-NullTerm-Hazard]]).

**Python stdio proxy**: `python -u` + `sys.stdin.reconfigure(line_buffering=True)` + `readline()` 3-Layer ([[concepts/Python-Stdio-MCP-Buffering-Hazard]]).

## 6. LLM-friendly Tool Schema (4 패턴 + 자동 정규화)

vault [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] 의 4 패턴:

| 패턴 | 적용 사례 |
|---|---|
| 1. 식별자 양식 양쪽 허용 | `expression_class` short/full / `dst_input` property/축약 |
| 2. Multi-source ID Resolver | `ResolveExpression` — local_id + GUID fallback |
| 3. Valid-list error response | `Valid dst_input on Power: [Base, Exp]` + HINT |
| 4. Tool result detail in log | `[tool_result:ERROR] <text>` 풀 로그 |

**+ 자동 정규화** (LLM 추측 hazard 의 정답 — [[synthesis/ue-llm-assumption-hazard-family]]):
- **Pin Name Shortening** ([[concepts/UE-Material-Pin-Name-Shortening]]) — 9개 매핑 자동 변환 (MMA-48)
- **TextureSample SamplerType** ([[concepts/UE-Texture-Sampler-Type-Auto-Inference]]) — CompressionSettings + SRGB → 자동 추론 (MMA-51)

## 7. UI Refresh — 3-Layer 의무

[[concepts/Material-Editor-External-Change-Reopen]]:
1. `Material->PostEditChange()` (셰이더만)
2. `MaterialGraph->RebuildGraph() + NotifyGraphChanged()` (그래프 노드만)
3. `AssetEditorSubsystem::CloseAllEditorsForAsset + OpenEditorForAsset` (완전 sync — 깜빡임)

가벼운 변경 — Layer 1+2 / 구조적 변경 — 1+2+3.

## 8. 활성 자산 자동 주입 + 풀 로그 + UI 필터

(기존 본문 유지) `UAssetEditorSubsystem::GetAllEditedAssets` → `[활성 머티리얼 컨텍스트]` block 자동 prefix. 풀 로그 모든 prefix 기록 / UI 는 `[claude] [log] [warn] [error] [done] [cancel] [tool_result:ERROR]` 만 노출.

## 9. ★ 이미지 입력 (v0.30/v0.31) + 선택지 UI (v0.32) ★

### 9.1 클립보드 이미지 paste — Windows 한정 ([[concepts/Windows-Clipboard-Image-Paste-UE]])

| 형식 | 처리 |
|---|---|
| CF_HDROP (파일 복사) | `DragQueryFile` → 이미지 확장자 검사 → path 그대로 |
| CF_DIBV5 / CF_DIB (스크린샷) | DIB → BGRA 변환 → ImageWrapper PNG 인코딩 → `Saved/<plugin>/clipboard-<ts>.png` |

→ PromptBox 안 cursor 위치에 path 삽입 + AttachedImagesPanel 에 96x96 thumbnail 카드 add.

### 9.2 선택지 카드 — `ask_user_choice` MCP tool ([[concepts/MCP-Async-UI-Bridge-Pattern]])

```
Claude → tools/call ask_user_choice(question, options[])
   → DispatchToolCall 비동기 분기 → PendingPromise 보관
   → OnAskUserChoice broadcast → Widget 의 노랑 카드 add
   → 사용자 option 클릭 → RespondToUserChoice → Promise SetValue
   → Claude 응답 turn 재개
```

### 9.3 LLM 추측 hazard 회피 ([[synthesis/ue-llm-assumption-hazard-family]])

vision 입력은 *인식 자체는 성공* 하지만 *세부 정밀도 한계* → LLM 학습 prior (ORM/ARM packing) 가 우선 채택. 4-Layer Defense:
1. Server 측 자동 정규화 (Pin Name / SamplerType)
2. Valid-list error response
3. 메타데이터 자동 노출 (`list_textures.recommended_sampler_type`)
4. `ask_user_choice` 강제 사용자 확인

## 10. 함정 카탈로그 (MMA-01 ~ MMA-53 — 100+ 항목)

### 10.1 Build / C++ (6건)
MMA-13/22/37/40/41 + Unity-Build-Include-Cascade

### 10.2 Claude CLI / MCP integration (14건)
MMA-19/23/24/27/25/26/29/31/42/43/44/46 + **MMA-49** (Async UI Bridge) + **MMA-53** (Session continuation)

### 10.3 Material Editor UI refresh (3건)
MMA-32/33+34/45+48

### 10.4 LLM 추측 family (3건) ⭐ 신규 인식
**MMA-45/48/50** — [[synthesis/ue-llm-assumption-hazard-family]] 로 통합

### 10.5 Texture / Asset (1건)
**MMA-51** — SamplerType auto inference

### 10.6 Editor UI / 클립보드 (1건)
**MMA-52** — Windows clipboard image paste

### 10.7 Editor 메뉴 / 환경 (4건)
MMA-14/15/38/39

### 10.8 권한 / 인증 (3건) / 도구 동작 (10건+)
(기존 본문 유지)

## 11. 재사용 청사진 — 11단계 체크리스트 ⭐

### Phase 0 — 설계
- [ ] vault 검색 + AssetEditor 종류 식별 + 도구 catalog 결정 + MCP transport

### Phase 1 — Tier 1/2 골격
- [ ] MCEditorModule + Build.cs 의존 (UnrealEd/MaterialEditor/ToolMenus/**ImageWrapper**)
- [ ] OnXxxEditorOpened delegate + ToolBar ExtendMenu
- [ ] EUW 채팅 UI (입력 하단 / 메시지 흐름 / inline 버튼 / Enter=전송)
- [ ] **클립보드 이미지 paste** (Ctrl+V → CF_HDROP/CF_DIB → thumbnail 카드) — Windows only

### Phase 2 — Tier 3 (Subsystem)
- [ ] EditorSubsystem Lifecycle / MCP server / Claude process / 풀 로그
- [ ] game thread marshalling
- [ ] **Session 유지** (`--session-id` + `--continue`)
- [ ] **PendingPromise** (ask_user_choice 비동기 UI bridge)

### Phase 3 — Tier 4 (MCP + Python proxy)
- [ ] tool catalog + 4 패턴 + 자동 정규화 + 메타데이터 노출

### Phase 4 — UI Refresh
- [ ] 3-Layer 의무 + 활성 자산 자동 주입

### Phase 5 — Claude CLI 인자 (8 항목)
(기존 본문 유지 + `--session-id` + `--continue`)

### Phase 6 — 환경 검증 UI
- [ ] Refresh / Login / API Key 버튼

### Phase 7 — vault filing-back
- [ ] 매 cycle 새 함정 → MMA-N 카탈로그
- [ ] Citation Disclosure (🟢/🟡/🔴)
- [ ] index + log + lint 0

### Phase 8 — Evaluator
- [ ] vault `[[00_meta/03_EvaluatorRecipe]]` 8-stage self-report
- [ ] find_claim_conflict / find_stale_baseline 격리 검증

## 12. 핵심 의존 entity / concept

### Entities (각각 `[[entities/<Name>]]` 참조 — frontmatter related_entities 의 7개 + 아래 추가)
- IMaterialEditor / IMaterialEditorModule / UMaterialEditingLibrary / UAssetEditorSubsystem / FAssetEditorToolkit
- FInteractiveProcess / Claude-Code-CLI / MCP-Protocol
- UMaterial / UMaterialExpression / FExpressionInput / EMaterialProperty

### Concepts (Tier 별 정렬)
- ⭐⭐⭐ Editor 메뉴: [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]]
- ⭐⭐⭐ 도구 정규화: [[concepts/UE-Material-Pin-Name-Shortening]] / [[concepts/UE-Texture-Sampler-Type-Auto-Inference]]
- ⭐⭐⭐ LLM 추측 family: [[synthesis/ue-llm-assumption-hazard-family]] / [[concepts/LLM-Visual-Reference-Hallucination]]
- ⭐⭐⭐ 비동기 UI: [[concepts/MCP-Async-UI-Bridge-Pattern]]
- ⭐⭐⭐ UI Refresh: [[concepts/Material-Editor-External-Change-Reopen]]
- ⭐⭐ Tool schema: [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]]
- ⭐⭐ Session: [[concepts/Claude-CLI-Session-Continuation]]
- ⭐⭐ 클립보드: [[concepts/Windows-Clipboard-Image-Paste-UE]]
- ⭐⭐ Proxy / HTTP: [[concepts/Python-Stdio-MCP-Buffering-Hazard]] / [[concepts/UE-HttpServer-Body-NullTerm-Hazard]]
- ⭐⭐ Cowork: [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]
- ⭐ Reflection / Build: 5건

## 13. 시나리오 검증 매트릭스 (v0.34 기준)

| 시나리오 | 결과 |
|---|---|
| 빈 머티리얼 + "red base color" prompt | ✅ |
| Half-Lambert wrap diffuse 추가 | ✅ |
| Ambient Cube (6면 환경광) 추가 | ✅ 35+ 노드 + 30+ connect |
| 기존 머티리얼 분석 | ✅ input_pins / is_single_input |
| MIC / MaterialFunction | ✅ Phase B/C |
| Power.Exponent ScalarParameter 연결 | ✅ v0.23 fix 후 (Pin Name Shortening) |
| **참조 이미지 paste + vision 인식** | ⚠ vision OK / 세부 정밀도 한계 (MMA-50) |
| **이미지 thumbnail 카드** | ✅ v0.31 |
| **선택지 카드 (ask_user_choice)** | ✅ v0.32 — LLM 호출 시 동작 |
| **세션 유지 (--continue)** | ✅ v0.33 |
| **T_Nana_Armor_Specular SamplerType ERROR** | ✅ v0.34 자동 추론 |

## 14. 후속 가능 cycle

- **v0.35+ 후보**:
  - 마크다운 / code highlight (SRichTextBlock + decorator)
  - 메시지 grouping (한 turn 의 여러 [claude] 라인 → 한 카드)
  - Turn budget 정량 측정 dashboard
  - 다른 AssetEditor 지원 (Persona / Niagara / Blueprint)
  - vision 정밀도 보강 (`list_textures` 의 channel 통계 / histogram 노출)

## 15. Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 4-Tier 아키텍처 | 🟢 VAULT | v0.2-v0.34 실측 |
| 11단계 체크리스트 | 🟢 VAULT | 실측 채택 |
| Vision 인식 성공 / 정밀도 한계 (v0.34 cycle) | 🟢 VAULT | run-20260525-145408.log 직접 분석 |
| LLM 추측 hazard family 통합 | 🟢 VAULT | [[synthesis/ue-llm-assumption-hazard-family]] |
| 다른 AssetEditor 도메인 적용 | 🔴 INFERRED | Persona/Niagara/Blueprint 미검증 |
| Turn budget 정량 효과 | 🔴 INFERRED | 측정 미수집 |

## 16. 변경 이력

- 2026-05-22: 초안 작성 — v0.2 → v0.29 누적 학습, 11단계 + 47+ 함정
- 2026-05-25: v0.30-v0.34 흡수 — 8 concept cross-link 추가 (clipboard image / thumbnail / ask_user_choice / session / SamplerType / hazard family). 함정 카탈로그 MMA-49~53 통합. § 5.2 Widget UI 진화 v0.24-v0.34 반영. § 9 신설 (이미지 입력 + 선택지 UI). frontmatter `last_updated` 추가.
- 2026-05-25: § 12 의 literal `[[entities/...]]` wikilink → `[[entities/<Name>]]` 표현으로 변경 (broken link fix)
