---
type: source
title: "UE refs — 03 WikiHarness (vault 단일 진입점)"
slug: ue-ref-03-wikiharness
source_path: raw/ue-wiki-llm/references/03_WikiHarness.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B remaining audit
tags: [ue, reference, wiki-meta, vault-structure, harness, governance]
---

# UE refs — 03 WikiHarness 🚨

> Source: [[raw/ue-wiki-llm/references/03_WikiHarness.md]] · CLAUDE.md §0.1 / §5.2 진입점

## 1. Summary

Wiki 전체의 **단일 진입점** — 작업 시나리오 → 필수 sub-skill 묶음 (하네스) 매트릭스. CLAUDE.md 가 본 문서를 참조하고, Claude는 코드 작성 전에 시나리오에 맞는 sub-skill 묶음을 사전에 모두 Read. 분석 범위: `Engine/Source/Runtime/` + `Editor/` + `Developer/`. 신규 sub-skill 추가 시 본 문서도 동기화.

## 2. 사용 규칙 🟢

1. 사용자 요청 → **카테고리 + 시나리오 식별**
2. §4 시나리오 표의 **필수 묶음** sub-skill 을 **모두 Read** 후 코드 작성
3. 시나리오 불명확 → §5 카테고리 기본 묶음 + 사용자 확인
4. 작업 중 신영역 필요 → 해당 sub-skill 추가 Read
5. sub-skill 의존 관계는 §6 그래프 참조

## 3. 교차 참조 인덱스 (Cross-cutting Indexes) 🟢

특정 sub-skill 만 봐서는 안 보이는 **횡단 관심사** 모음. 작업 시작 전 시나리오에 따라 추가 Read:

| 인덱스 | 다루는 횡단 관심사 | 언제 |
| -- | -- | -- |
| [[sources/ue-ref-04-overrideindex]] | virtual 함수 통합 표 + RebuildWidget 사이클 + Super 호출 의무 | 새 클래스 작성 / override 결정 시 |
| [[sources/ue-ref-05-editoronlyindex]] | 🛠 항목 + **4단 분리 원칙** + 게임 모듈 금지 의존 | 에디터 콜백 / 인하우스 툴 / 플러그인 분리 |
| [[sources/ue-ref-06-invalidationhotspots]] | 위젯별 인밸리데이션 케이스 + InvalidationBox / ForceVolatile 결정 + NativeTick 회피 | UMG / SWidget 성능 |
| 🚨 [[sources/ue-ref-07-profilingscopeRule]] | **모든 sub-skill 공통 의무** — Tick / Timer / 람다 / UFunction / OnRep_* 스코프 부착 | **모든 코드 작성 시** |
| [[sources/ue-ref-08-overlaphotspots]] | PrimitiveComponent Overlap 핫스팟 + Collision Profile/Channel 매트릭스 + UpdateOverlaps 빈도 | 트리거 / 캡슐 / 메시 콜리전 |
| 🚨 [[sources/ue-ref-09-globaliteratorpolicy]] | **TActorIterator / TObjectIterator 금지** + 대안 7종 + 결정 트리 | **전역 객체 검색 의도 시** |
| 🚨 [[sources/ue-ref-10-componentpolicies]] | **Components 6대 의무** — Mobility / NewObject / GC / GetOwner / Tick / CDO | **컴포넌트 작성 시** |
| 🚨 [[sources/ue-ref-11-assetloadingpolicy]] | **SpawnActor 히칭 방지** — 4단 메커니즘 + Soft/Hard 6종 + Streamable + Bundle | **모든 어셋 멤버 + Cooked Build 검증** |
| 🎯 [[sources/ue-ref-12-assetoptimizationpolicy]] | **5대 영역** — SkM Bone LOD / SM LOD+Nanite / Merging / Audio / Niagara + NPC LOD 매트릭스 | **모든 자산 + 다수 NPC + 60fps** |
| [[sources/ue-ref-14-taskhandofftemplate]] 📋 | **멀티 세션 인계** — Sprint Contract + Decision Log + Progress + Evaluator + Brief 5섹션 | 멀티 세션 / 컨텍스트 60% 도달 시 |
| [[sources/ue-ref-15-evaluatorrecipe]] 🔍 | **Generator/Evaluator 분리** — 8단계 회의 평가 + Cooked 검증 + 100점 채점 | 코드 리뷰 / PR 검토 / 배포 직전 |
| [[sources/ue-ref-16-policypriority]] ⚖ | **5단 우선순위** — Compile > GC > Runtime > Performance > Maintainability | 정책 충돌 시 |
| [[sources/ue-ref-17-qualitycriteria]] 📊 | **4종 가중** — Performance 35% + Memory 25% + Network 15% + Maintainability 25% + 플랫폼 임계 매트릭스 | 코드 리뷰 / 성능 회귀 / 플랫폼 검증 |
| [[sources/ue-ref-18-modelevolutionaudit]] 🕰 | **분기별 staleness 감사 2축** — UE 진화 + Anthropic 모델 진화 + 8단계 + 6 결정 | 분기별 / UE 마이너 / Anthropic 메이저 변경 |
| [[sources/ue-ref-19-externalsourcesguide]] | 외부 source 신뢰성 평가 (UE 공식 / EpicGames 문서 / 커뮤니티) | 외부 자료 인용 시 |

## 4. vault 카테고리별 sub-skill 묶음 🟢

| 카테고리 | main + sub | 핵심 sub-skill 묶음 |
| -- | -- | -- |
| **CoreUObject** | 1 + 13 | UObject / Reflection / GC / Serialization / Network + Editor 🛠 + Cooking 🛠 |
| **Components** (Tier 1) | 1 + 15 + 1 deep | ActorComponent / SceneComponent / PrimitiveComponent + 13 자손 + CharacterMovement deep |
| **GameFramework** (Tier 1) | 1 + 6 + 1 deep | Actor / PawnCharacter / Controller / GameMode / GameInstance / World + CharacterOptimization deep |
| **AssetClasses** (Tier 1) | 1 + 10 + 1 deep | Mesh / Material / Texture / Animation / Audio / VFX / Camera / Data / Physics + AssetUserData + Audio MetaSound deep |
| **Animation** | 1 + 8 | AnimInstance / AnimGraph / AnimNotify / Sync / RootMotion / Optimization / IK + Ragdoll |
| **Input** (Tier 1) | 1 + 5 | EnhancedInput / Action / Subsystem / InputCore / Legacy |
| **Editor** 🛠 | 1 + 9 + UnrealEd 9 + AssetEditorAPI 5 + refs 2 = 26 | UnrealEd / EditorFramework / EditorSubsystem / AssetTools / PropertyEditor / ToolMenus / MainFrame / LevelEditor / AssetRegistry / EditorWidgets |
| **Slate** | 1 + 12 + 1 deep | EditorApplication 🛠 / Docking 🛠 / Menu 🛠 / Commands 🛠 / GraphEditor 🛠 + Application / CommonWidgets / LayoutWidgets / ListsTrees / TextInput / MiscWidgets / Animation |
| **SlateCore** | 1 + 10 | SWidget / Layout / Drawing / Styling / Input / Application / Animation / Text / Types + Trace 🛠 |
| **UMG** | 1 + 7 + 1 deep | UWidget / UUserWidget / StandardWidgets / PanelWidgets / ListWidgets / Slot / ViewModel + InvalidationDeep |
| **Render** | 1 + 12 | RDG / Shader / Material / SceneViewExtension / MeshDrawing / PostProcess / Lumen+Nanite / RHI / Vulkan / Mobile / VR / MaterialExpression 🛠 |
| **AI / BP / Build / GAS / Net / Niagara / Significance** | 7 × 1 main | 각 카테고리 main |
| **SpatialPartition** (5.x, 20th) | 1 + 4 | TOctree2 / TQuadtree / StaticSpatialIndex / WorldPartitionRuntime |
| **Subsystem** | 1 + 1 deep | 5종 비교 + OnlineSubsystem deep |

## 5. 시나리오 → 필수 묶음 (대표 6) 🟢

| 시나리오 | 필수 묶음 |
| -- | -- |
| 새 Actor / Character 작성 | GameFramework/actor + GameFramework/pawncharacter + Components 6대 + 11_AssetLoading + 10_ComponentPolicies + 07_ProfilingScope |
| 새 컴포넌트 작성 | Components/skill + 6대 정책 hub + 04_Override + 07_Profiling |
| 새 UMG 위젯 / HUD | UMG/uwidget + UMG/uuserwidget + 04_Override §3 RebuildWidget + 06_Invalidation + 07_Profiling |
| 인하우스 자산 에디터 작성 | Editor/skill + asseteditortoolkit + assettools + propertyeditor + factories + 04_Override §2.5 + 05_EditorOnly |
| 다수 NPC 환경 최적화 | 12_AssetOptimization + Significance + Animation/optimization + 08_Overlap + 09_GlobalIterator + character-many-npc-5-fold-optimization |
| 멀티플레이 복제 | CoreUObject/network + Networking/skill + GameFramework + 07_Profiling (OnRep_*) + replication-graph-bandwidth-management |

## 6. sub-skill 의존 그래프 (Top 5 의존 흐름)

```
Core
 └─ CoreUObject (L2)
     └─ Engine (L5) ──┬─> Slate (L6/UI) ──> UMG (L7)
                      ├─> Renderer (L4) ──> RHI ──> {D3D12RHI, VulkanRHI, OpenGLDrv}
                      ├─> AudioMixer ──> AudioMixerCore
                      ├─> Networking ──> Sockets
                      └─> AIModule ──> NavigationSystem
```

자세히 → [[sources/ue-ref-01-layermap]] L1-L7.

## 7. KMCProject 시나리오 매트릭스 (예시)

| 작업 | 필수 묶음 |
| -- | -- |
| `MCStoryAsset` 그래프 작성 | Editor/asseteditortoolkit + assettools + factories + kismet2 + Slate/grapheditor + 05_EditorOnly |
| `UMCSoftSkeletalMeshComponent` Ragdoll | Components/meshcomponents + Animation/ragdoll + 10_ComponentPolicies + 11_AssetLoading + mc-soft-skeletalmesh-ragdoll |
| `UMCActorSpawnSubsystem` | Subsystem/skill + 09_GlobalIterator + 11_AssetLoading + SpatialPartition/toctree2 + Significance + mc-actor-spawn-subsystem-implementation |

## 8. Cross-link

- Manifests: [[sources/ue-readme]] · [[sources/ue-manifest]]
- Layer 구조: [[sources/ue-ref-01-layermap]] (L1-L7) · [[sources/ue-ref-02-verificationlog]]
- 교차 인덱스 18개: §3 표 — 04-19 모든 ref (정책 hub 5 + override / 4단 분리 / hotspot 2)
- Governance: [[00_meta/00_QualityCriteria]] · [[00_meta/01_PolicyPriority]] · [[00_meta/02_FrontmatterStandard]] · [[00_meta/03_EvaluatorRecipe]] · [[00_meta/04_AuditPolicy]] · [[00_meta/05_HandoffProtocol]] · [[00_meta/06_VaultCitationRule]] · [[00_meta/07_AgentBoundaryProtocol]]
- 작업 메모: [[sources/ue-meta-honest-limits]] · [[sources/ue-meta-improvement-roadmap]]
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 1 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/references/03_WikiHarness.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/references/03_WikiHarness.md`
