# Wiki Index

> Last updated: 2026-05-28 · **5.5.4 active vault (forked from 5.7.4 archive)** · 인계 통계: 227 sources / 97 entities / 75 concepts / 63 synthesis (4 신규 — migration + Phase 2-A + Phase 2-B + Phase 2-C) · ✅ **Phase 2 audit 완료** (158 / 156 🟢 pass · 98.7%)

매 ingest 후 LLM 이 자동 갱신. CLAUDE.md §5.2 step 1 의 진입점.

---

## ⭐ Vault Scope

> **본 vault 는 UE 5.5.4 의 일반 지식 베이스다.** KMCProject 는 vault 의 일반 패턴을 *검증* 하는 case study.
>
> **분기 출처**: `E:\MCWiki` (5.7.4 frozen, 2026-05-27 fork). 인계된 wiki/ 콘텐츠는 **Phase 2 (A+B+C) audit 완료** (2026-05-28): 158 페이지 중 156 🟢 pass / 2 🟡 partial / 0 🔴. 자세히 [[synthesis/phase-2c-body-reconciliation]] · [[synthesis/migrated-from-5-7-4-to-5-5-4]].

| 슬러그 접두사 | 의미 | 비율 |
| -- | -- | -- |
| `ue-` / `ue-agent-` / `ue-meta-` / `ue-ref-` | UE 5.5.4 일반 지식 (Phase 2 audit 완료, 98.7% pass) | **96%** |
| **`mc-`** | **KMCProject 실측 사례** | **4%** |

→ 정책 전문: [[00_meta/08_VaultScopePolicy]]

---

## Governance (00_meta, 10)

- [[00_meta/00_QualityCriteria]] · [[00_meta/01_PolicyPriority]] · [[00_meta/02_FrontmatterStandard]]
- [[00_meta/03_EvaluatorRecipe]] · [[00_meta/04_AuditPolicy]] · [[00_meta/05_HandoffProtocol]]
- [[00_meta/06_VaultCitationRule]] · [[00_meta/07_AgentBoundaryProtocol]]
- [[00_meta/08_VaultScopePolicy]] · [[00_meta/09_StubVsEnrichedPolicy]]

---

## Sources (227)

### CoreUObject (14)
- [[sources/ue-coreuobject-skill]] · [[sources/ue-coreuobject-uobject]] · [[sources/ue-coreuobject-reflection]] · [[sources/ue-coreuobject-property]] · [[sources/ue-coreuobject-package]]
- [[sources/ue-coreuobject-interface]] · [[sources/ue-coreuobject-gc]] · [[sources/ue-coreuobject-serialization]] · [[sources/ue-coreuobject-network]]
- [[sources/ue-coreuobject-editor]] · [[sources/ue-coreuobject-cooking]]
- [[sources/ue-coreuobject-structutils]] · [[sources/ue-coreuobject-objecthandles]] · [[sources/ue-coreuobject-deprecateduproperty]]

### Components (17)
- [[sources/ue-components-skill]] · [[sources/ue-components-actorcomponent]] · [[sources/ue-components-scenecomponent]] · [[sources/ue-components-primitivecomponent]]
- [[sources/ue-components-meshcomponents]] · [[sources/ue-components-shapecomponents]] · [[sources/ue-components-lightcomponents]]
- [[sources/ue-components-physicscomponents]] · [[sources/ue-components-movementcomponents]] · [[sources/ue-components-cameracomponent]]
- [[sources/ue-components-audiocomponent]] · [[sources/ue-components-particlecomponents]] · [[sources/ue-components-renderingcomponents]]
- [[sources/ue-components-atmospherecomponents]] · [[sources/ue-components-systemcomponents]] · [[sources/ue-components-specialcomponents]]
- deep: [[sources/ue-components-charactermovementdeep]]

### GameFramework (8)
- [[sources/ue-gameframework-skill]] · [[sources/ue-gameframework-actor]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/ue-gameframework-controller]]
- [[sources/ue-gameframework-gamemode]] · [[sources/ue-gameframework-gameinstance]] · [[sources/ue-gameframework-world]]
- deep: [[sources/ue-gameframework-characteroptimization]]

### AssetClasses (12)
- [[sources/ue-assetclasses-skill]] · [[sources/ue-assetclasses-mesh]] · [[sources/ue-assetclasses-material]] · [[sources/ue-assetclasses-texture]] · [[sources/ue-assetclasses-animation]]
- [[sources/ue-assetclasses-audio]] · [[sources/ue-assetclasses-vfx]] · [[sources/ue-assetclasses-camera]] · [[sources/ue-assetclasses-data]] · [[sources/ue-assetclasses-physics]]
- [[sources/ue-assetclasses-assetuserdata]]
- deep: [[sources/ue-assetclasses-audio-metasound]]

### Animation (9)
- [[sources/ue-animation-skill]] · [[sources/ue-animation-animinstance]] · [[sources/ue-animation-animgraph]] · [[sources/ue-animation-animnotify]]
- [[sources/ue-animation-sync]] · [[sources/ue-animation-rootmotion]] · [[sources/ue-animation-optimization]] · [[sources/ue-animation-ik]] · [[sources/ue-animation-ragdoll]]

### Input (6)
- [[sources/ue-input-skill]] · [[sources/ue-input-enhancedinput]] · [[sources/ue-input-action]] · [[sources/ue-input-subsystem]] · [[sources/ue-input-inputcore]] · [[sources/ue-input-legacy]]

### Editor (26)
- [[sources/ue-editor-skill]] · [[sources/ue-editor-unrealed]] · [[sources/ue-editor-editorframework]] · [[sources/ue-editor-editorsubsystem]] · [[sources/ue-editor-editorwidgets]]
- [[sources/ue-editor-assettools]] · [[sources/ue-editor-propertyeditor]] · [[sources/ue-editor-toolmenus]] · [[sources/ue-editor-mainframe]]
- [[sources/ue-editor-leveleditor]] · [[sources/ue-editor-assetregistry]]
- UnrealEd 깊이 (9): [[sources/ue-editor-unrealed-asseteditortoolkit]] · [[sources/ue-editor-unrealed-elements]] · [[sources/ue-editor-unrealed-factories]] · [[sources/ue-editor-unrealed-kismet2]]
- [[sources/ue-editor-unrealed-layers]] · [[sources/ue-editor-unrealed-materialeditor]] · [[sources/ue-editor-unrealed-misc]] · [[sources/ue-editor-unrealed-subsystems]]
- AssetEditorAPI (5): [[sources/ue-editor-asseteditorapi]] · [[sources/ue-editor-advancedpreviewscene]] · [[sources/ue-editor-eventbinding]] · [[sources/ue-editor-personatoolkit]] · [[sources/ue-editor-staticmesheditor]]
- Editor refs: [[sources/ue-editor-dependencies]] · [[sources/ue-editor-scenarios]]
- ⭐ pattern: [[sources/ue-fscopedtransaction-drag-1-entry]]

### Slate (15)
- [[sources/ue-slate-skill]] · [[sources/ue-slate-application]] · [[sources/ue-slate-editorapplication]] · [[sources/ue-slate-docking]] · [[sources/ue-slate-menu]] · [[sources/ue-slate-commands]]
- [[sources/ue-slate-grapheditor]] · [[sources/ue-slate-commonwidgets]] · [[sources/ue-slate-layoutwidgets]] · [[sources/ue-slate-liststrees]]
- [[sources/ue-slate-textinput]] · [[sources/ue-slate-miscwidgets]] · [[sources/ue-slate-animation]] · deep: [[sources/ue-slate-uedgraphapi]]
- ⭐ pattern: [[sources/ue-streeview-onexpansionchanged-pattern]]

### SlateCore (12)
- [[sources/ue-slatecore-skill]] · [[sources/ue-slatecore-swidget]] · [[sources/ue-slatecore-layout]] · [[sources/ue-slatecore-drawing]] · [[sources/ue-slatecore-styling]]
- [[sources/ue-slatecore-input]] · [[sources/ue-slatecore-application]] · [[sources/ue-slatecore-animation]] · [[sources/ue-slatecore-text]] · [[sources/ue-slatecore-types]] · [[sources/ue-slatecore-trace]]
- ⭐ [[sources/ue-slatecore-clipping]]

### UMG (9)
- [[sources/ue-umg-skill]] · [[sources/ue-umg-uwidget]] · [[sources/ue-umg-uuserwidget]] · [[sources/ue-umg-standardwidgets]] · [[sources/ue-umg-panelwidgets]]
- [[sources/ue-umg-listwidgets]] · [[sources/ue-umg-slot]] · [[sources/ue-umg-viewmodel]] · deep: [[sources/ue-umg-invalidationdeep]]

### Render (14)
- [[sources/ue-render-skill]] · [[sources/ue-render-materialexpression]] · [[sources/ue-render-shader]] · [[sources/ue-render-rdg]] · [[sources/ue-render-sceneviewextension]]
- [[sources/ue-render-postprocess]] · [[sources/ue-render-meshdrawing]] · [[sources/ue-render-lumennanite]]
- [[sources/ue-render-rhi]] · [[sources/ue-render-mobile]] · [[sources/ue-render-vr]] · [[sources/ue-render-material]] · [[sources/ue-render-vulkan]]
- ⭐ [[sources/ue-render-material-editing-library]] 🛠

### SpatialPartition (5)
- [[sources/ue-spatialpartition-skill]] · [[sources/ue-spatialpartition-toctree2]] · [[sources/ue-spatialpartition-tquadtree]] · [[sources/ue-spatialpartition-staticspatialindex]] · [[sources/ue-spatialpartition-worldpartitionruntime]]

### LevelSequence (12)
- [[sources/ue-levelsequence-skill]] · [[sources/ue-levelsequence-moviescene]] · [[sources/ue-levelsequence-tracks]] · [[sources/ue-levelsequence-levelsequenceplayer]]
- [[sources/ue-levelsequence-director]] · [[sources/ue-levelsequence-cinecamera]] · [[sources/ue-levelsequence-sequencer]] · [[sources/ue-levelsequence-movierenderpipeline]]
- [[sources/ue-levelsequence-entitysystemecs]] · [[sources/ue-levelsequence-sequencerscripting]] · [[sources/ue-levelsequence-templatesequence]]
- ⭐ pattern: [[sources/ue-floatchannel-9-mirror]]

### AI / Blueprint / Build / GAS / Networking / Niagara / Significance (7)
- [[sources/ue-ai-skill]] · [[sources/ue-blueprint-skill]] · [[sources/ue-build-skill]] · [[sources/ue-gas-skill]] · [[sources/ue-networking-skill]] · [[sources/ue-niagara-skill]] · [[sources/ue-significance-skill]]

### Subsystem (2)
- [[sources/ue-subsystem-skill]] · deep: [[sources/ue-subsystem-onlinesubsystem]]

### Phase 4G — references (19) + Deep (5)
- [[sources/ue-ref-00-readme]] · [[sources/ue-ref-01-layermap]] · [[sources/ue-ref-02-verificationlog]] · [[sources/ue-ref-03-wikiharness]]
- [[sources/ue-ref-04-overrideindex]] · [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-06-invalidationhotspots]] · [[sources/ue-ref-08-overlaphotspots]]
- [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- [[sources/ue-ref-14-taskhandofftemplate]] · [[sources/ue-ref-15-evaluatorrecipe]] · [[sources/ue-ref-16-policypriority]] · [[sources/ue-ref-17-qualitycriteria]]
- [[sources/ue-ref-18-modelevolutionaudit]] · [[sources/ue-ref-19-externalsourcesguide]]
- Deep: [[sources/ue-ref-deep-assetloading]] · [[sources/ue-ref-deep-assetoptimization]] · [[sources/ue-ref-deep-componentpolicies]] · [[sources/ue-ref-deep-invalidationhotspots]] · [[sources/ue-ref-deep-overridetables]]

### Phase 4G — catalog / docs / meta (9)
- catalog: [[sources/ue-catalog-runtimeindex]] · [[sources/ue-catalog-editordevindex]]
- docs: [[sources/ue-docs-claude]] · [[sources/ue-docs-install]]
- meta: [[sources/ue-meta-confidence-tags]] · [[sources/ue-meta-corrections]] · [[sources/ue-meta-governance]] · [[sources/ue-meta-honest-limits]] · [[sources/ue-meta-improvement-roadmap]] · [[sources/ue-meta-baseline-grep-system]]

### Agents (15)
- [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- [[sources/ue-agent-animation]] · [[sources/ue-agent-asset]] · [[sources/ue-agent-components]]
- [[sources/ue-agent-editor]] · [[sources/ue-agent-gameframework]] · [[sources/ue-agent-input]]
- [[sources/ue-agent-plugin]] · [[sources/ue-agent-render]] · [[sources/ue-agent-slate-umg]]
- [[sources/ue-agent-spatial-partition]] · [[sources/ue-agent-levelsequence]]

### Measurements (5)
- [[sources/ue-measure-readme]] · [[sources/ue-measure-summary]] · [[sources/ue-measure-mcsoftstaticmesh-2026-05-08]] · [[sources/ue-measure-renderpostprocess-2026-05-08]] · [[sources/ue-measure-instancedsubobject-2026-05-12]]

### MC 시리즈 — KMCProject 실측 사례 (2)
- [[sources/mc-asset-validation-policy]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Manifests (2)
- [[sources/ue-readme]] · [[sources/ue-manifest]]

---

## Entities (97)

### CoreUObject / Foundation (9)
- [[entities/UObject]] · [[entities/UClass]] · [[entities/FProperty]] · [[entities/UPackage]] · [[entities/UInterface]]
- [[entities/FName]] · [[entities/UEnum]] · [[entities/FStructProperty]] · [[entities/TFieldIterator]]

### Components 베이스 + 주요 (7)
- [[entities/UActorComponent]] · [[entities/USceneComponent]] · [[entities/UPrimitiveComponent]]
- [[entities/UStaticMeshComponent]] · [[entities/USkeletalMeshComponent]] · [[entities/UCharacterMovementComponent]] · [[entities/UNiagaraComponent]]

### GameFramework — Actor 게임 흐름 (9)
- [[entities/AActor]] · [[entities/APawn]] · [[entities/ACharacter]] · [[entities/AController]] · [[entities/APlayerController]]
- [[entities/AGameModeBase]] · [[entities/AGameStateBase]] · [[entities/UGameInstance]] · [[entities/UWorld]]

### AssetClasses 자산 (9)
- [[entities/UStaticMesh]] · [[entities/USkeletalMesh]] · [[entities/UMaterial]] · [[entities/UTexture]]
- [[entities/UAnimSequence]] · [[entities/UAnimMontage]] · [[entities/UBlendSpace]] · [[entities/USoundBase]] · [[entities/UNiagaraSystem]]

### Animation 런타임 (6)
- [[entities/UAnimInstance]] · [[entities/FAnimInstanceProxy]] · [[entities/FAnimNode-Base]] · [[entities/UAnimNotify]] · [[entities/UIKRigDefinition]] · [[entities/UIKRetargeter]]

### Editor (14)
- [[entities/IToolkit]] · [[entities/UEdMode]] · [[entities/UToolMenus]] · [[entities/IDetailCustomization]] · [[entities/IAssetTools]] · [[entities/IAssetRegistry]]
- [[entities/UEdGraph]] · [[entities/UBlueprintGeneratedClass]] · [[entities/IMainFrameModule]]
- [[entities/UMaterialGraph]] · [[entities/UAssetEditorSubsystem]] · [[entities/FAssetEditorToolkit]]
- [[entities/IMaterialEditor]] · [[entities/IMaterialEditorModule]]

### Render / Material (5)
- [[entities/UMaterialExpression]] · [[entities/UMaterialEditingLibrary]] · [[entities/FMaterialUpdateContext]] · [[entities/FExpressionInput]] · [[entities/EMaterialProperty]]

### Slate / SlateCore (8)
- [[entities/SWidget]] · [[entities/FSlateApplication]] · [[entities/FTabManager]] · [[entities/FUICommandList]]
- [[entities/FGeometry]] · [[entities/FSlateDrawElement]] · [[entities/FSlateBrush]] · [[entities/FSlateStyleSet]]

### UMG (4)
- [[entities/UWidget]] · [[entities/UUserWidget]] · [[entities/UPanelWidget]] · [[entities/UPanelSlot]]

### Input (5)
- [[entities/UInputAction]] · [[entities/UInputMappingContext]] · [[entities/UEnhancedInputLocalPlayerSubsystem]] · [[entities/UEnhancedInputComponent]] · [[entities/FKey]]

### AI (5)
- [[entities/AAIController]] · [[entities/UBehaviorTree]] · [[entities/UBlackboardComponent]] · [[entities/UNavigationSystemV1]] · [[entities/UAIPerceptionComponent]]

### Blueprint / Build (3)
- [[entities/UBlueprint]] · [[entities/UnrealBuildTool]] · [[entities/UnrealAutomationTool]]

### GAS (5)
- [[entities/UAbilitySystemComponent]] · [[entities/UAttributeSet]] · [[entities/UGameplayAbility]] · [[entities/FGameplayEffect]] · [[entities/FGameplayTag]]

### Networking / Significance / Subsystem (5)
- [[entities/UNetDriver]] · [[entities/UNetConnection]] · [[entities/USignificanceManager]] · [[entities/USubsystem]] · [[entities/UEngineSubsystem]]

### Core HAL (1)
- [[entities/FInteractiveProcess]]

### ⭐⭐ Integration / External (2)
- [[entities/Claude-Code-CLI]] · [[entities/MCP-Protocol]]

---

## Concepts (75)

### Foundation (9)
- [[concepts/Reflection-System]] · [[concepts/Garbage-Collection]] · [[concepts/UPROPERTY-Markup]] · [[concepts/Object-Handles]] · [[concepts/Object-Lifecycle]] · [[concepts/Pimpl-TUniquePtr-Destructor]]
- [[concepts/UE-FStructProperty-Cast-Type-Safety]] (MMA-37)
- [[concepts/UEnum-GetValueByName-FullyQualified]] (MMA-32)
- [[concepts/UE-NameHiding-Override-Hazard]] (MMA-40)

### Lifecycle (3)
- [[concepts/Component-Lifecycle]] · [[concepts/Actor-Lifecycle]] · [[concepts/Asset-Lifecycle]]

### UE 횡단 의무 정책 (4)
- [[concepts/Component-Policies-6]] · [[concepts/Profiling-Scope-Rule]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Asset-Optimization-Policy]]

### GameFramework (3)
- [[concepts/Possession]] · [[concepts/Match-State]] · [[concepts/SeamlessTravel]]

### Components / Asset (5)
- [[concepts/Mobility]] · [[concepts/Tick-Group]] · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/Cooked-vs-Uncooked]] · [[concepts/BulkData]]

### Animation 최적화 (5)
- [[concepts/URO]] · [[concepts/Inertialization]] · [[concepts/RootMotion]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[concepts/Bone-LOD]]

### Editor / UI (9)
- [[concepts/Editor-Only-4-Tier-Separation]] · [[concepts/Slate-Editor-Runtime-Separation]] · [[concepts/Slate-Invalidation]] · [[concepts/Slate-Paint-Cycle]] · [[concepts/UMG-Super-Call-Convention]]
- [[concepts/Material-Editor-External-Change-Reopen]] (MMA-33+34)
- ⭐⭐⭐ [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] (MMA-38/39)
- ⭐⭐ [[concepts/Windows-Clipboard-Image-Paste-UE]] (MMA-52)
- ⭐⭐ [[concepts/UE-LiveCoding-Module-Path-Hazard]] (2026-05-26)

### Input (2)
- [[concepts/Enhanced-Input-Standard]] · [[concepts/IMC-Stack]]

### Blueprint / Build + UE migration (6)
- [[concepts/CPP-BP-Boundary]] · [[concepts/Build-Configurations]] · [[concepts/Unity-Build-Include-Cascade]]
- [[concepts/LOCTEXT-Namespace-Macro-Position-Hazard]] (MMA-41)
- ⭐ [[concepts/UE-MetaSpecifier-LongPath-Requirement]] (2026-05-26)
- ⭐⭐ [[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]] — **신규 (2026-05-26)** (Phase 3c-3 후속 — Live Coding 의 .cpp trigger 의무 + .h-only USTRUCT 무시 회피)

### Networking (4)
- [[concepts/Replication]] · [[concepts/RPC]] · [[concepts/Authority-NetMode]] · [[concepts/PushModel]]

### Subsystem (2)
- [[concepts/Subsystem-5-Types]] · [[concepts/Global-Iterator-Avoidance]]

### MC-시리즈 — KMCProject 실측 사례 (1)
- [[concepts/MC-Asset-Validation-Policy]]

### Render / Material (6)
- [[concepts/PSO-Precache]] · [[concepts/Motion-To-Photon-Latency]] · [[concepts/Render-Thread-Safety]] · [[concepts/RDG-Pass]]
- ⭐⭐⭐ [[concepts/UE-Material-Pin-Name-Shortening]] (MMA-48)
- ⭐⭐ [[concepts/UE-Texture-Sampler-Type-Auto-Inference]] (MMA-51)

### CoreUObject Package / PackageName (1)
- ⭐⭐⭐ [[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]] — **신규 (2026-05-26)** (`/All/Game/...` view path vs `/Game/...` mount root + LongPackageNameToFilename fatal + TryConvert 회피)

### ⭐⭐ Claude / MCP Integration + AI Hallucination Hazards (15)
- [[concepts/Python-Stdio-MCP-Buffering-Hazard]] (MMA-29)
- [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] (MMA-31)
- [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]] (MMA-24/27)
- [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] (MMA-42/43/44/46)
- ⭐⭐⭐ [[concepts/MCP-Async-UI-Bridge-Pattern]] (MMA-49)
- ⭐⭐⭐ [[concepts/LLM-Visual-Reference-Hallucination]] (MMA-50)
- ⭐ [[concepts/Claude-CLI-Session-Continuation]] (MMA-53)
- ⭐⭐ [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (2026-05-25, MMA-DT-04)
- ⭐⭐ [[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]] (2026-05-26, MMA-DT-05)
- ⭐ [[concepts/UE-CppComment-Backslash-LineContinuation-Hazard]] (2026-05-26, MMA-DT-06)
- ⭐⭐ [[concepts/Claude-CLI-Session-Id-UUID-Format-Strict]] (2026-05-26, MMA-DT-07)
- ⭐⭐⭐ [[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]] (2026-05-26, MMA-DT-08) — 9 cycle 결정적 fix
- ⭐⭐ [[concepts/MCP-Notification-No-Response-Spec]] (2026-05-26, MMA-DT-09)
- ⭐⭐ [[concepts/MCP-Tool-Schema-Strip-Hazard]] — **신규 (2026-05-26)** (Phase 3c-3 후속 — schema 미선언 인자 strip 함정)
- ⭐⭐ [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]] — **신규 (2026-05-26)** (Phase 3c-3 후속 — TSharedPtr wrapper exit 후 정리 의무 + 3-layer defense)

---

## Synthesis (63)

### Migration / Schema-change / Audit (4) ⭐⭐⭐
- [[synthesis/migrated-from-5-7-4-to-5-5-4]] — **2026-05-27 fork 기록** · UE 5.7.4 → 5.5.4 vault 분기 · 인계 자산 + audit 로드맵 + Phase 1~3 계획
- [[synthesis/phase-2-audit-14-concepts]] — **2026-05-27 Phase 2-A audit** · 14 concept tier 재검토 · 🟢 12 pass / 🟡 2 partial / 0 🔴
- [[synthesis/phase-2b-sources-audit]] — **2026-05-28 Phase 2-B sources audit** · 142 wiki/sources/ × 5.5.4 raw 충돌 검토 · 75 cosmetic + 67 content-change 자동 분류
- [[synthesis/phase-2c-body-reconciliation]] — **2026-05-28 Phase 2-C body recon** · 43 partial 모두 🟢 promote · Phase 2 (A+B+C) 158 / 156 pass (98.7%)

### Actor / Lifecycle (3)
- [[synthesis/actor-lifecycle-edge-cases]] · [[synthesis/component-vs-actor-lifecycle-table]] · [[synthesis/spawnactor-hitching-4-step-pattern]]

### Multi-NPC / Character / Animation (5)
- [[synthesis/character-many-npc-5-fold-optimization]] · [[synthesis/ai-npc-ragdoll-coordination]] · [[synthesis/ragdoll-getup-anim-recovery]] · [[synthesis/ragdoll-multiplayer-replication]] · [[synthesis/ai-npc-squad-coordination-tick-budget]]

### MC-시리즈 — KMCProject 실측 사례 (15)
- [[synthesis/mc-character-hit-reaction-pipeline]] · [[synthesis/mc-soft-asset-component-pattern]]
- [[synthesis/mc-combo-section-levelsequence-style-upgrade]]
- [[synthesis/mc-validation-automation-tooling]] · [[synthesis/mc-validation-policy-rollout]] · [[synthesis/actor-pool-reset-pattern]]
- [[synthesis/mc-actor-spawn-subsystem-implementation]] · [[synthesis/mc-actor-spawn-subsystem-h1-measurement]]
- [[synthesis/mc-combo-editor-levelsequence-lite]]
- ⭐⭐⭐ [[synthesis/mc-combo-editor-phase-5g-5l-drag-ux-suite]]
- ⭐⭐⭐ [[synthesis/mc-combo-editor-phase-6-7-inhouse-master]]
- ⭐⭐⭐ [[synthesis/mc-combo-editor-phase-8-channel-iterator]]
- ⭐⭐⭐ [[synthesis/mc-claude-mcp-editor-integration-blueprint]] (v0.30-v0.34 흡수)
- ⭐⭐⭐ [[synthesis/mc-datatable-auto-blueprint]] (2026-05-26 — end-to-end 동작 검증)
- ⭐⭐⭐ [[synthesis/mc-datatable-auto-build-cycle-postmortem]] (2026-05-26 — Phase 1~3c-3 + 후속 14 cycle 회고)

### GAS (4)
- [[synthesis/gameplaycue-cosmetic-boundary]] · [[synthesis/gas-advanced-runtime-patterns]] · [[synthesis/gas-pawn-vs-playerstate-decision]] · [[synthesis/gameplaycue-prediction-modifier-cdr]]

### Subsystem (4)
- [[synthesis/subsystem-5-types-decision-tree]] · [[synthesis/subsystem-advanced-patterns]] · [[synthesis/subsystem-graph-online-wrapper]] · [[synthesis/online-crossplay-gas-lobby]]

### Networking / Multiplayer (3)
- [[synthesis/late-join-reconnect-state-sync]] · [[synthesis/server-vs-client-rpc-decision-tree]] · [[synthesis/replication-graph-bandwidth-management]]

### Render / VFX / Cooked (5)
- [[synthesis/cooked-first-frame-stability]] · [[synthesis/pso-precache-platform-matrix]] · [[synthesis/vfx-audio-soft-pool-significance]] · [[synthesis/pso-streaming-livepatch-tools]] · [[synthesis/render-rdg-pass-standard-pattern]]

### Live Ops / Lint (3)
- [[synthesis/runtime-dlc-livepatch-rollout]] · [[synthesis/lint-2026-05-10-mcsoft-components]] · [[synthesis/dlc-asset-migration-edge-cases]]

### Actor Pool / Validation Tooling (2)
- [[synthesis/actor-pool-multiplayer-gc-integration]] · [[synthesis/validation-static-analysis-ide-integration]]

### SpatialPartition (1)
- [[synthesis/toctree2-worldpartition-pair-pattern]]

### Governance / Phase II Gate (2)
- [[synthesis/agent-boundary-cycles-2026-q2]]
- [[synthesis/cycle-5p-postmortem-remediation]]

### Editor / PropertyEditor / Custom Slate Widget Pattern (9)
- [[synthesis/bp-scs-preview-viewport-lifecycle]] · [[synthesis/component-renderstate-and-spawn-side-effects]] · [[synthesis/editor-preview-scene-runtime-handoff]] · [[synthesis/instanced-subobject-customization-bypass]]
- [[synthesis/cycle-5m-audit-report-2026-q2]]
- ⭐⭐ [[synthesis/ue-paint-hittest-shared-rowmap]]
- ⭐⭐ [[synthesis/ue-tree-uobject-expansion-bidirectional-sync]]
- ⭐⭐⭐ [[synthesis/timeline-custom-slate-widget-pattern]]
- ⭐⭐ [[synthesis/ue-slate-custom-onpaint-layer-strategy]]
- ⭐⭐⭐ [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]]
- ⭐⭐⭐ [[synthesis/ue-track-area-section-paint-anatomy]]

### ⭐⭐⭐ LLM / MCP Hazard Family (1)
- ⭐⭐⭐ [[synthesis/ue-llm-assumption-hazard-family]] (MMA-45/48/50 통합 + phantom header + encoding + LiveCoding + PackageName view path 변종 흡수)

---

## Ingest 진척도

raw/ue-wiki-llm/ — 9 phase 완료 + Cycle 5a~5p+7 + Phase 5a-8.2.2 + MCMaterialAuto v0.13-v0.34 누적 filing-back + **MCDataTableAuto Phase 1~3c-3 + 후속 14 cycle 누적 filing-back (2026-05-25~2026-05-26)**.

| 카테고리 | main + sub | 상태 |
| -- | -- | -- |
| CoreUObject | 1 + 13 | ✅ |
| Components | 1 + 15 + 1 deep | ✅ |
| GameFramework | 1 + 6 + 1 deep | ✅ |
| AssetClasses | 1 + 10 + 1 deep | ✅ |
| Animation | 1 + 8 | ✅ |
| Input | 1 + 5 | ✅ |
| Editor | 1 + 9 + UnrealEd 9 + AssetEditorAPI 5 + refs 2 = 26 | ✅ |
| Slate | 1 + 12 + 1 deep | ✅ |
| SlateCore | 1 + 10 + 1 pattern | ✅ |
| UMG | 1 + 7 + 1 deep | ✅ |
| Render | 1 + 12 + 1 editor | ✅ |
| AI / BP / Build / GAS / Net / Niagara / Significance | 7 × 1 main | ✅ |
| SpatialPartition | 1 + 4 | ✅ |
| LevelSequence | 1 + 10 | ✅ |
| Subsystem | 1 + 1 deep | ✅ |
| references (정책 + governance + 권위 hub) | 19 + 5 | ✅ |
| catalog / docs / meta | 2 / 2 / 6 | ✅ |
| meta/measurements | 5 | ✅ |
| agents (운영) | 15 | ✅ |
| README / manifest | 2 | ✅ |

### Phase 3c-3 후속 (11~14 cycle) — end-to-end 완전 동작 (2026-05-26) ⭐⭐⭐ NEW

[[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]] (★★★) — `/All/Game/...` view path → `/Game/...` mount root + LongPackageNameToFilename fatal + TryConvert 회피.

[[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]] (★★) — Live Coding 의 .cpp trigger 의무 + .h-only USTRUCT 무시 case (sub-B 흐름).

[[concepts/MCP-Tool-Schema-Strip-Hazard]] (★★) — tools/list schema 미선언 파라미터 strip + properties 완전 매니페스트 의무.

[[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]] (★★) — TSharedPtr wrapper exit 후 정리 의무 + 3-layer defense.

### Phase 3c-3 9 cycle 끝 결정적 함정 2 concept (2026-05-26) ⭐⭐⭐

[[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]] (★★★) — 9 cycle 끝 결정적 fix.

[[concepts/MCP-Notification-No-Response-Spec]] (★★) — JSON-RPC 2.0 spec.

### MCDataTableAuto Phase 1~3c-3 + 후속 14 cycle 누적 (2026-05-25~2026-05-26)

[[synthesis/mc-datatable-auto-build-cycle-postmortem]] — 14 cycle 회고. 신규 12 concept (5 LLM hallucination 변종 + 3 MCP integration + 4 UE Engine API/spec 함정).

다음 ingest 후보: raw/articles/ · raw/papers/ · raw/youtube/ · raw/notes/.

---

## 통계

```
sources:    227
entities:    97
concepts:    75
synthesis:   63
orphans:      0
broken:       0
stale (>90d): 0
```

> **Last verification** (2026-05-26): Phase 3c-3 후속 14 cycle **end-to-end 완전 동작 확정** (사용자: "응 잘 돌아간다"). 누적 12 신규 concept + 2 갱신 synthesis. lint **0 broken** ✅. 함정 카탈로그 **109+** (MMA-DT-01~14). 신뢰도 격상 누적 **27+ 건**. Article 1 evaluator 시행 예정.
