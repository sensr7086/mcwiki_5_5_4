---
type: synthesis
title: "BP 컴포넌트 뷰포트(SCS Preview) Lifecycle + Editor World Tick 매트릭스"
slug: bp-scs-preview-viewport-lifecycle
created: 2026-05-12
last_updated: 2026-05-12
sources:
  - "[[sources/ue-components-actorcomponent]]"
  - "[[sources/ue-components-scenecomponent]]"
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-editor-leveleditor]]"
  - "[[sources/ue-editor-editorsubsystem]]"
entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
  - "[[entities/UWorld]]"
  - "[[entities/AActor]]"
concepts:
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Mobility]]"
status: living
tags: [synthesis, kmcproject, editor, scs, preview, lifecycle, worldtype, tick]
---

# BP 컴포넌트 뷰포트(SCS Preview) Lifecycle + Editor World Tick 매트릭스

> **목적**: KMCProject 의 `UMCSoftStaticMeshComponent` 디버깅 (2026-05-12) 에서 BP 컴포넌트 뷰포트의 `OnRegister` 호출 빈도 / Editor World tick 의 Realtime 동작 / SCS preview rebuild 패턴이 vault 에 없어 *추측 기반 수정이 반복되며 회귀가 누적된 사례* 의 후속 정리. 이 페이지는 그 영역에 대한 1차 정리이며, 본문 안 **🟢 VAULT / 🟡 PARTIAL / 🔴 INFERRED** 분류를 엄격히 준수한다 ([[00_meta/06_VaultCitationRule]]).
>
> **검증 상태**: 본 페이지의 다수 진술은 *🔴 INFERRED* — 일반 UE 5.x 지식 + KMCProject 디버깅에서의 *행동 관찰* 기반. 후속 검증 시 tier 승격 필요.

## 1. Thesis

BP 컴포넌트 뷰포트 = **Blueprint Editor 안에 표시되는 SCS preview viewport** — Actor 의 Simple Construction Script 가 생성한 컴포넌트 트리를 시각화. 일반 Level Editor / PIE / Game World 와 *서로 다른* World/Lifecycle 컨텍스트:

| 항목 | Level Editor | BP 컴포넌트 뷰포트 (SCS preview) | PIE / Game |
| -- | -- | -- | -- |
| `UWorld::WorldType` | `EWorldType::Editor` (2) | `EWorldType::EditorPreview` (4) 추정 🟡 | `EWorldType::PIE` (3) / `Game` (1) |
| `World->IsGameWorld()` | false | false | true |
| `World->IsEditorWorld()` | true | true | false |
| `World->bAllowAudioPlayback` | false | false | true |
| Tick 정지 가능 | Realtime OFF 시 yes 🔴 | Realtime OFF 시 yes 🔴 | no (게임 흐름) |
| `BeginPlay` 호출 | no | no | yes |
| `OnRegister` 호출 | yes | yes (잦음) | yes |
| `OnComponentCreated` | yes (placed 시) | no (SCS template — UE 표준) 🔴 | yes (SpawnActor) |

> 🟢 = vault 또는 UE 공식 docs 직접 확인 / 🟡 = 일반 UE 지식 정합 / 🔴 = 본 페이지 작성 시점 미검증

## 2. 🟢 VAULT — 직접 확인된 사실

### 2.1 EWorldType enum

[[sources/ue-gameframework-world]] 와 [[entities/UWorld]] 에 명시:

- `EWorldType::Editor` — Level Editor 의 메인 월드
- `EWorldType::EditorPreview` — Asset Editor / preview viewport
- `EWorldType::PIE` — Play In Editor
- `EWorldType::Game` — Cooked / standalone game
- `EWorldType::Inactive` — 종료 또는 대기 상태

### 2.2 컴포넌트 라이프사이클 진입점

[[concepts/Component-Lifecycle]] / [[sources/ue-components-actorcomponent]] §라이프사이클:

- `OnComponentCreated` — Actor 생성 시 한 번 (SpawnActor / Editor placement)
- `OnRegister` — RegisterComponent 시마다 (반복 호출 가능)
- `BeginPlay` — World 가 BeginPlay 진행 단계일 때만
- `EndPlay` / `OnUnregister` / `OnComponentDestroyed`

### 2.3 Editor-Only 4-Tier 분리

[[concepts/Editor-Only-4-Tier-Separation]] / [[sources/ue-ref-05-editoronlyindex]]:

- Tier 1 — `WITH_EDITOR` 매크로
- Tier 2 — `EWorldType::Editor / EditorPreview` 분기
- Tier 3 — `GIsEditor` 전역
- Tier 4 — Editor 모듈 분리

→ Soft 컴포넌트가 Editor World 분기 시 `World->IsGameWorld() == false` (음성 리스트) 가 *Editor + EditorPreview + Inactive* 모두 포함하는 가장 안전한 패턴.

### 2.4 KMCProject 의 디자이너 워크플로 (자체 검증)

[[synthesis/mc-soft-asset-component-pattern]] §7.4 에 기록된 디자이너 워크플로 매트릭스 — BP 컴포넌트 뷰포트 / Level Editor placed / PIE 세 컨텍스트 모두 hook 의무.

## 3. 🟡 PARTIAL — vault 근거 일부 + 외삽

### 3.1 BP 컴포넌트 뷰포트의 World Type

vault 의 [[sources/ue-editor-leveleditor]] / [[sources/ue-editor-editorsubsystem]] 가 *Asset Editor / Preview Scene* 을 다루지만 **BP 컴포넌트 뷰포트가 정확히 어떤 `EWorldType`** 인지 명시 안 됨.

- vault 근거: [[sources/ue-editor-asseteditorapi]] §AssetEditor Toolkit 에 `FAdvancedPreviewScene` 사용 패턴 언급 → preview scene 은 `EWorldType::EditorPreview`
- 외삽: BP Editor 의 SCS preview viewport 도 동일한 PreviewScene 인프라 사용 → `EditorPreview` 가능성 높음
- 이번 KMCProject 디버깅에서 사용자 Output Log 의 `WorldType=4` 확인 → `EditorPreview` 와 일치 (2026-05-12)

→ **🟡 결론: BP 컴포넌트 뷰포트의 SCS preview World = `EditorPreview`** (vault 근거 + 행동 관찰).

### 3.2 OnRegister 호출 빈도

[[sources/ue-components-actorcomponent]] §라이프사이클은 OnRegister 가 RegisterComponent 마다 호출됨을 명시하지만, *BP 컴포넌트 뷰포트에서 어떤 사용자 액션이 RegisterComponent 를 다시 트리거하는지* 는 vault 에 정밀하지 않음.

이번 디버깅 (KMCProject MCSoftStaticMesh) 의 행동 관찰 — *동일 컴포넌트 인스턴스에 대해 `OnRegister` 가 한 BP 컴파일에 1회 이상* 호출되는 패턴 추정. 정확한 트리거 매트릭스는 미검증.

행동 관찰 기반 가설 (🟡):
- BP Compile → SCS reconstruction → 컴포넌트 instance 재생성 → OnRegister 1회
- 컴포넌트 디테일 변경 (PostEditChangeProperty) → SCS 일부 reconstruction → OnRegister 추가 1회
- Live Coding patch 적용 → 컴포넌트 archetype 갱신 → OnRegister 추가 1회

## 4. 🔴 INFERRED — vault 미확인, 일반 지식 / 코드 베이스 추론

### 4.1 Editor World 의 Tick 동작

**일반 UE 5.x 지식 (vault 미확인)**:

- Editor World / EditorPreview World 의 tick 은 *Editor Viewport Realtime 설정* 에 의존
- Realtime ON → 매 frame tick (`UEditorEngine::EditorTick` 가 PreviewScene tick)
- Realtime OFF → 정지, *카메라 이동 / 마우스 클릭 / 디테일 변경* 등 사용자 인터랙션 시에만 redraw 1회
- BP 컴포넌트 뷰포트는 **기본 Realtime ON** (디자이너 viewport 사용성)
- Asset Editor (StaticMesh / SkeletalMesh Editor) preview 도 **기본 Realtime ON**
- Level Editor 는 사용자 토글 (디폴트는 Realtime ON, Performance 메뉴에서 OFF)

이번 KMCProject 디버깅에서 *5번 반복 spawn/destroy* 가 관찰됨 → BP 컴포넌트 뷰포트가 Realtime 이지만 우리 `ProcessAssetUserDataAfterMeshLoadedEditorSync` 가 *매 OnRegister 마다 호출* + *내부 DeactivateAll + SpawnAllNow 반복* 의 결과.

### 4.2 `FTimerManager` vs `FTSTicker` 의 Editor 컨텍스트

**일반 UE 5.x 지식 (vault 미확인)**:

- `UWorld::GetTimerManager()` — World 가 tick 될 때만 timer 발화. Editor World Realtime OFF 면 timer paused.
- `FTSTicker::GetCoreTicker()` — Engine 레벨 tick, World pause 무관. Editor / EditorPreview / Game 모두 동작.
- BP 컴포넌트 뷰포트에서 *지연 실행이 필요한 Editor-only hook* 은 `FTSTicker` 가 더 안전.

이번 KMCProject 디버깅 — OnRegister 안에서 Niagara 처리를 next-tick 으로 지연할 때 `FTSTicker::GetCoreTicker()` 채택 (2026-05-12).

### 4.3 SCS Template vs Instance

**일반 UE 5.x 지식 (vault 미확인)**:

- BP 의 SCS 노드 = *template 컴포넌트* (UPROPERTY archetype) — 디테일 패널 편집 대상
- BP recompile 시 SCS template 의 UPROPERTY 가 BP archetype 에 저장 + 모든 인스턴스 (BP 컴포넌트 뷰포트 preview / Level Editor placed) 에 propagate
- SCS template 의 `CreationMethod == EComponentCreationMethod::SimpleConstructionScript` 에서 `OnComponentCreated` 가 호출 안 됨 (디자인 의도)
- BP 컴포넌트 뷰포트의 preview Actor 는 BP class 로부터 `SpawnActor` 와 비슷한 경로로 생성 — 하지만 **`BeginPlay` 는 호출 안 됨** (Editor 컨텍스트)
- **OnRegister 는 정상 호출** — Super::OnRegister() 가 RegisterComponentWithScene 호출 → SceneProxy 생성

### 4.4 BP 컴포넌트 archetype 의 부모 UPROPERTY Save 위험

**일반 UE 5.x 지식 (vault 미확인)** + KMCProject 코드 검증 일부 🟡:

- `UStaticMeshComponent::SetStaticMesh(NewMesh)` 가 내부에서 `Modify()` 호출 → archetype dirty
- 디자이너가 BP 를 Save → 부모 `StaticMesh` UPROPERTY 가 BP .uasset 에 hard ref 로 저장
- KMCProject 의 Soft 컴포넌트 의도와 충돌 — SoftStaticMesh 만 archetype 저장이어야

→ [[synthesis/mc-soft-asset-component-pattern]] §7.8 함정 #9 로 기록됨 — 후속 BP archetype 검사 도구 후보.

### 4.5 SCS preview Actor 가 Static Mesh Asset Editor preview 와 다른 점

**일반 UE 5.x 지식 (vault 미확인)**:

| 항목 | StaticMesh Asset Editor preview | BP 컴포넌트 뷰포트 SCS preview |
| -- | -- | -- |
| Preview Scene 종류 | `FAdvancedPreviewScene` 또는 `FPersonaToolkit` 의 preview scene | BP Editor 의 자체 SCS preview scene |
| 호스트 Actor | 메시 단일 Actor (engine-internal) | BP class 의 archetype Actor |
| SCS 트리 | 없음 (메시 자체만) | BP SCS 트리 전체 |
| `UMCNiagaraSocketPreviewSubsystem` hook | ✅ — `OnAssetOpenedInEditor` 구독 가능 | ❌ — BP Editor 는 별도 path |
| 디자이너 변경 시 | Asset Editor Save | BP Compile + Save |

→ KMCProject 의 `UMCNiagaraSocketPreviewSubsystem` 이 StaticMesh Asset Editor 안에서만 Niagara preview 처리하고, BP 컴포넌트 뷰포트에는 적용 안 되는 이유. Soft 컴포넌트가 자기 OnRegister 에서 직접 처리해야 했던 디자인 결정의 *근거* ([[synthesis/mc-soft-asset-component-pattern]] §7.1 의 race 분석에서 한 줄로 언급).

## 5. 적용 사례 — 2026-05-12 MCSoftStaticMesh 디버깅

| 단계 | 시도 | 결과 | tier |
| -- | -- | -- | -- |
| 1 | `BeginPlay → ApplyLoadedAssets` 에 Niagara hook | PIE 에서만 동작, BP 뷰포트 무반응 | 🟢 일치 (BeginPlay 가 Editor 컨텍스트에서 호출 안 됨) |
| 2 | `PostEditChangeProperty` 에 Editor sync path | 디테일 변경 시점에는 OK, BP 컴파일 자동 spawn 케이스 무반응 | 🟢 일치 (PostEditChangeProperty 는 디테일 변경 시점 한정) |
| 3 | `OnRegister` 에 동기 path 추가 | 메시 잘 보임, Niagara 안 보임 (가드 과보호) | 🟡 (OnRegister 진입 검증되지 않음 — Verbose 로그가 안 보임) |
| 4 | 가드 분리 | Niagara 잘 보임, 메시 안 보임 (호스트 RenderState race?) | 🔴 race 가설은 미검증 |
| 5 | `FTSTicker` next-tick 지연 | 메시 + Niagara 둘 다 안 보임 (회귀) | 🔴 가설 빗나감 |
| 6 | World 분기 완화 (`!IsGameWorld()`) + `MarkRenderStateDirty` | 진행 중 — Log Display 로 verbosity 올린 후 진단 | 🟡 |
| 7 | 동일 메타 skip + `RecreateRenderState_Concurrent` | 진행 중 — 사용자 빌드 후 검증 대기 | 🔴 |

→ *진단 결정* 이 부족한 상태에서 *코드 수정* 을 반복한 패턴. 위 §4 의 미검증 영역이 vault 에 정리되어 있었다면 더 빠른 정확한 진단이 가능.

## 6. 후속 검증 / vault 편입 후보

🔴 INFERRED 항목들이 후속 검증되어 🟢 로 승격 가능:

- [ ] §3.1 — BP 컴포넌트 뷰포트의 `EWorldType` (`UEdGraphSchema_K2` 또는 BlueprintEditor 모듈 코드 직접 확인)
- [ ] §3.2 — OnRegister 호출 트리거 매트릭스 (UE 5.7.4 코드: `USCS_Node`, `USimpleConstructionScript::ExecuteConstruction`)
- [ ] §4.1 — Editor Realtime ON/OFF 매트릭스 (`UEditorEngine::EditorTick`, `FEditorViewportClient::bRealtime`)
- [ ] §4.2 — `FTSTicker` vs `FTimerManager` 동작 차이 검증 (실제 Editor 컨텍스트 측정)
- [ ] §4.5 — `UMCNiagaraSocketPreviewSubsystem` hook 범위 (이미 KMCProject 코드에 있음, 별도 sub-skill 작성 후보)

후속 작업으로 [[sources/ue-editor-leveleditor]] / [[sources/ue-editor-editorsubsystem]] 의 BP Editor 부분을 보강하거나, *neue* `sources/ue-editor-blueprinteditor-scs` 신설.

## 7. cross-link

### Sources

[[sources/ue-components-actorcomponent]] · [[sources/ue-components-scenecomponent]] · [[sources/ue-gameframework-actor]] · [[sources/ue-editor-leveleditor]] · [[sources/ue-editor-editorsubsystem]] · [[sources/ue-editor-asseteditorapi]] · [[sources/ue-editor-advancedpreviewscene]]

### Entities

[[entities/UActorComponent]] · [[entities/USceneComponent]] · [[entities/UWorld]] · [[entities/AActor]]

### Concepts

[[concepts/Component-Lifecycle]] · [[concepts/Actor-Lifecycle]] · [[concepts/Editor-Only-4-Tier-Separation]] · [[concepts/Mobility]]

### Related synthesis

[[synthesis/mc-soft-asset-component-pattern]] §7 (이번 디버깅의 적용 사례 모음) · [[synthesis/component-renderstate-and-spawn-side-effects]] (RenderState / spawn 부수 효과의 자매 페이지) · [[synthesis/editor-preview-scene-runtime-handoff]] (Editor preview 와 런타임 분리)
