# LLM_Wiki Harness — 작업 시나리오별 sub-skill 묶음

> Wiki 전체의 **단일 진입점**. CLAUDE.md 가 이 문서를 참조하고, Claude는 코드 작성 전에 작업 시나리오에 맞는 sub-skill 묶음(하네스)을 사전에 모두 읽는다.
> **분석 범위**: `Engine/Source/Runtime/` + `Engine/Source/Editor/` + `Engine/Source/Developer/` (`Programs/` 제외).
> 갱신 이력은 §9. 신규 sub-skill 추가 시 본 문서도 동기화.

---

## 0. 사용 규칙

1. 사용자 요청을 받으면 **먼저 카테고리(Render/Slate/Components)와 시나리오를 식별**한다.
2. 아래 §3 의 시나리오 표에서 **필수 묶음** 컬럼의 sub-skill 을 **모두 Read** 한 뒤 코드 작성을 시작한다.
3. 시나리오가 명확하지 않으면 [§4 카테고리 기본 묶음](#4-카테고리별-기본-묶음) 을 로드하고 사용자에게 시나리오를 한 번 확인한다.
4. 작업 중 새 영역(예: 복제 추가, 직렬화 추가)이 필요해지면 해당 sub-skill 을 **추가로 로드**한다.
5. **sub-skill 간 의존 관계**는 §7 그래프 참조 — 한 sub-skill 을 읽을 때 자주 함께 참조되는 묶음을 미리 알 수 있다.

### 0.1 교차 참조 인덱스 (Cross-cutting Indexes)

특정 sub-skill 만 읽어서는 보이지 않는 **횡단 관심사**를 한곳에 모은 인덱스. 작업 시작 전 시나리오에 따라 추가로 Read.

| 인덱스 | 다루는 횡단 관심사 | 언제 읽나 |
|--------|-------------------|-----------|
| [`04_OverrideIndex.md`](./04_OverrideIndex.md) | CoreUObject·SlateCore·Slate·UMG **virtual 함수 통합 표** + **RebuildWidget 사이클(§5)** + Super 호출 의무 | 새 클래스 작성·override 결정 시 |
| [`05_EditorOnlyIndex.md`](./05_EditorOnlyIndex.md) | sub-skill별 🛠 항목 + **런타임/에디터 4단 분리 원칙** + 게임 모듈 금지 의존성 + **체크리스트** | 에디터 콜백·인하우스 툴·플러그인 분리 시 |
| [`06_InvalidationHotspots.md`](./06_InvalidationHotspots.md) | 위젯별 인밸리데이션 다발 케이스(STextBlock·RichText·EditableText·ListView·Throbber·NativeOnPaint·TAttribute 람다 등) + InvalidationBox/ForceVolatile 결정 트리 + **NativeTick 회피 계층** | UMG·SWidget 성능/리프레시 이슈, RichText 대량 갱신 |
| [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) 🚨 | **모든 sub-skill 공통 의무** — Tick / TimerManager / FTSTicker / 람다 / 바인딩된 UFunction / OnRep_\* 에 `TRACE_CPUPROFILER_EVENT_SCOPE` / `SCOPED_NAMED_EVENT` / `QUICK_SCOPE_CYCLE_COUNTER` 부착 규약 + 8단 체크리스트 | **모든 코드 작성 시** (특히 매 프레임·시간 기반·델리게이트 진입점) |
| [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) | PrimitiveComponent 자손별 Overlap 핫스팟 (Shape·Static·Skeletal·Character·ISM/HISM) + CollisionEnabled/Channel/Profile 매트릭스 + UpdateOverlaps 호출 빈도 + Begin/End 콜백 비용 절감 + **8단 체크리스트** | 트리거 / 캡슐 / 메시 콜리전 작성 / 매 프레임 이동 컴포넌트 |
| [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) 🚨 | **TActorIterator·TObjectIterator·TObjectRange·TActorRange 사용 금지 정책** — 매 프레임/콜백 안 사용 즉시 폭사. 대안 7종 (Subsystem 등록·AssetRegistry·UWorld::Actors·Tag·캐시·SpatialHash·OverlapMulti) + 결정 트리 + 최후의 수단 5조건 + 7허용 예외 + 5단 체크리스트 | **모든 코드 작성 시 우선 검토** (전역 객체 검색 의도 발견 시) |
| [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) 🚨 | **Components 6대 의무 — 모든 컴포넌트 본문 시작부 의무 블록** — (1) Mobility (런타임 SetMobility 금지) + (2) NewObject·DuplicateObject (Outer 검증) + (3) GC 방어 (UPROPERTY+TObjectPtr/TStrongObjectPtr/FGCObject) + (4) GetOwner 캐싱 (BeginPlay TWeakObjectPtr) + (5) PrimaryComponentTick (false 기본·TickInterval 우선·매 프레임 마지막 수단) + (6) CDO (GetMutableDefault 금지·RF_ClassDefaultObject 검사·CreateDefaultSubobject Constructor 안만) + 통합 체크리스트 | **`[Components]` 카테고리 전체 + 컴포넌트 작성 시** |
| [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) 🚨 | **어셋 로드 정책 — SpawnActor 히칭 방지 표준** — SpawnActor 히칭 4단 원인 (Class CDO·Subobject·재귀 어셋·Material PSO) + Soft/Hard Reference 6종 비교 + FStreamableManager API (RequestAsyncLoad / FStreamableHandle Pin·Release) + UAssetManager Primary Asset / Bundle 시스템 (UPrimaryDataAsset / FPrimaryAssetId / LoadPrimaryAsset / PreloadPrimaryAssets / ChangeBundleStateForPrimaryAssets) + **SpawnActor 히칭 방지 4단 표준 패턴 (PreLoad → Wait → SpawnActorDeferred → FinishSpawning)** + PreLoadAsset 5대 정책 + sub-skill 적용 매트릭스 14종 | **모든 어셋 멤버 추가 시 + Cooked Build 검증 시** (특히 GameFramework / Components / UMG / Render — 자주 Spawn 되는 Actor / 큰 Mesh·Texture·Material) |
| [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) 🎯 | **어셋 최적화 5대 영역 — 60fps + 메모리 한계 회피 표준** — (§1) SkeletalMesh Bone LOD (USkeletalMeshLODSettings + BonesToRemove/Prioritize + LODHysteresis + 5.x SkinCacheUsage) + (§2) StaticMesh LOD (ScreenSize 표준 + 5.x Nanite vs Traditional 결정) + (§3) Actor Merging 4종 (HISM / Mesh Merge / HLOD / 5.x WorldPartition HLOD) + (§4) Audio Culling (Attenuation MaxDistance + Concurrency StopFarthest + SoundMix + Significance) + (§5) Niagara Quality Scaling (UNiagaraEffectType + 품질 레벨 5종 매트릭스 + Pool + Scalability API) + **§6 다수 NPC 통합 매트릭스 (LOD 5단계 9개 항목)** + 함정 15종 + 6대 체크리스트 + sub-skill 적용 매트릭스 10종 | **모든 자산 멤버 + 다수 NPC 환경 + 60fps 유지 검증 시** (특히 AssetClasses / Components / Significance / Niagara / GameFramework — 자주 사용 자산 / 매 프레임 다수 객체) |
| [`14_TaskHandoffTemplate.md`](./14_TaskHandoffTemplate.md) 🆕📋 | **멀티 세션 작업 인계 표준 — Article 1 "context reset > compaction"** — Sprint Contract (목표/범위/제약/기간) + Decision Log (선택지·결정·근거) + Progress (완료/진행/차단) + Evaluator Findings (회의적 평가 결과) + Next Session Brief (재개용 압축 요약) 5섹션 + `<외부>/{...}_{작업명}_{단계}.md` 명명 규약 + 세션 종료 직전 / 컨텍스트 60% 도달 시 작성 의무 | **모든 멀티 세션 / 다중 일자 작업 시작 시 + 종료 직전 + 컨텍스트 한계 접근 시** |
| [`15_EvaluatorRecipe.md`](./15_EvaluatorRecipe.md) 🆕🔍 | **Generator/Evaluator 분리 — Article 1 self-evaluation bias 방지** — 8단계 회의적 평가 (Policy 위반 → Compile → Runtime → Performance 4기준 → Edge cases → Replicated integrity → GC leak → External verification) + Cooked Build 검증 명령 (Build.bat / stat unit / stat slate / stat anim) + 100점 채점 (Performance 35 + Memory 25 + Network 15 + Maintainability 25) + 평가자는 작성자와 다른 Claude 인스턴스 / 사용자 의무 | **모든 코드 리뷰 / Pull Request 검토 / 프로덕션 배포 직전 + 다른 Claude 인스턴스 호출 시** |
| [`16_PolicyPriority.md`](./16_PolicyPriority.md) 🆕⚖ | **정책 충돌 해결 5단 우선순위** — Tier 1 Compile (UCLASS / GENERATED_BODY / Build.cs / 매크로) > Tier 2 GC (UPROPERTY / TStrongObjectPtr / FGCObject) > Tier 3 Runtime (Super 호출 / RF_ClassDefaultObject / Mobility) > Tier 4 Performance (Tick / 어셋 로드 / Iterator / Profiling Scope) > Tier 5 Maintainability (명명·구조·문서) + 5개 자주 충돌 예시 (Constructor 어셋 로드 vs CreateDefaultSubobject / Tick vs 매 프레임 / Hard vs Soft / TActorIterator vs Editor 1회성 / Cooked vs 작은 변경) + 결정 트리 | **정책 간 충돌 발견 시 + 50+ 규칙 우선순위 결정 시** |
| [`17_QualityCriteria.md`](./17_QualityCriteria.md) 🆕📊 | **측정 가능한 품질 기준 4종 가중 — Article 1 subjective quality scoring** — Performance 35% (frame budget·CPU·GPU·thread) + Memory 25% (heap·BulkData·streaming) + Network 15% (bandwidth·RTT·packet loss) + Maintainability 25% (명명·구조·테스트 가능성·문서) + 플랫폼별 임계 매트릭스 (PC High 8ms/Mid 12ms/Low 16ms / Console 16ms / Mobile 33ms / VR 11ms) + 95점 Good vs 32점 Bad few-shot calibration | **코드 리뷰 / 성능 회귀 / 플랫폼 별 임계 검증 시** |
| [`18_ModelEvolutionAudit.md`](./18_ModelEvolutionAudit.md) 🆕🕰 | **위키 staleness 감사 2축 — Article 1 load-bearing component verification** — UE 진화 (5.x 신규 API / Deprecated / 변경) + Anthropic 모델 진화 (instruction following 개선 → 규약 명시 vs 자율 판단) + 8단계 감사 (Inventory / Source Validation grep / Load-Bearing Test / Cross-Reference / Real-World 사용 / Decision / Implementation / Communication) + 6종 결정 (Continue / Update / Simplify / Merge / Deprecate / Remove) + 분기별 정기 감사 + UE 마이너 버전 업그레이드 시 트리거 | **분기별 정기 감사 + UE 마이너 버전 업그레이드 시 + Anthropic 모델 메이저 변경 시** |

---

## 1. Wiki 구조 한눈에

```
C:\Unreal\UnrealEngine\LLM_Wiki\
├── 00_Overview\
│   ├── 00_README.md              위키 진입점, Tier 분류
│   ├── 01_LayerMap.md            L1~L7 의존 계층
│   ├── 02_VerificationLog.md     검증 로그·작업 인계 메모
│   ├── 03_WikiHarness.md         이 문서 (시나리오별 하네스)
│   ├── 04_OverrideIndex.md       virtual + RebuildWidget 통합 인덱스 ✅ 신규
│   ├── 05_EditorOnlyIndex.md     🛠 항목 + 4단 분리 원칙 통합 ✅ 신규
│   ├── 06_InvalidationHotspots.md 위젯별 인밸리데이션 다발 케이스 ✅ 신규
│   ├── 07_ProfilingScopeRule.md   Tick/Timer/람다/UFunction 프로파일링 스코프 의무 ✅ 신규
│   ├── 08_OverlapHotspots.md      PrimitiveComponent 자손 Overlap 비용/핫스팟 ✅ 신규
│   ├── 09_GlobalIteratorPolicy.md TActorIterator/TObjectIterator/TObjectRange 사용 금지 정책 ✅ 신규
│   ├── 10_ComponentPolicies.md    Components 6대 의무 (Mobility/NewObject/GC/GetOwner/Tick/CDO) ✅ 신규
│   ├── 11_AssetLoadingPolicy.md   SpawnActor 히칭 방지 + Soft/Hard ref + FStreamableManager + Bundle ✅ 신규
│   ├── 12_AssetOptimizationPolicy.md SkeletalMesh Bone LOD + StaticMesh LOD + Merging + Audio + Niagara 5대 영역 ✅ 신규
│   ├── 14_TaskHandoffTemplate.md  멀티 세션 작업 인계 표준 (Article 1 context reset) ✅ 신규
│   ├── 15_EvaluatorRecipe.md      Generator/Evaluator 분리 — 회의적 평가 표준 ✅ 신규
│   ├── 16_PolicyPriority.md       정책 충돌 해결 5단 우선순위 ✅ 신규
│   ├── 17_QualityCriteria.md      측정 가능한 품질 기준 4종 (Performance/Memory/Network/Maintainability) ✅ 신규
│   └── 18_ModelEvolutionAudit.md  위키 staleness 감사 2축 (UE 진화 + Anthropic 모델 진화) ✅ 신규
├── 01_Catalog\
│   ├── RuntimeIndex.md           Engine/Source/Runtime 189개 모듈 카탈로그
│   ├── EditorDevIndex.md         Engine/Source/Editor + Developer 카탈로그 ✅ 신규
│   └── runtime_meta.json         의존성 원시 데이터
├── 02_Skills\                    Tier별 모듈 sub-skill
│   ├── CoreUObject\              Tier 1 · 메인 + 13 sub-skill ✅ 완료
│   ├── SlateCore\                Tier 3 · 메인 + 10 sub-skill ✅ 완료
│   ├── Slate\                    Tier 3 · 메인 + 12 sub-skill (인하우스 툴 5 + 게임/에디터 공통 7) ✅ 완료
│   ├── UMG\                      Tier 3 · 메인 + 7 sub-skill ⏳ 진행 중
│   ├── Editor\                   🆕 Editor 모듈 통합 카테고리 — 메인 + 10 sub-skill (Option A 통합)
│   │   ├── UnrealEd\                 Editor 메인 모듈 · 9개 sub-skill (AssetEditorToolkit/Subsystems/Kismet2/Factories/Elements/Layers/MaterialEditor/Misc)
│   │   ├── EditorFramework\          IToolkit/UEdMode 베이스
│   │   ├── EditorSubsystem\          UEditorSubsystem 베이스 모듈
│   │   ├── EditorWidgets\            공통 Editor 위젯
│   │   ├── AssetTools\               IAssetTypeActions
│   │   ├── PropertyEditor\           Details 패널 커스터마이징
│   │   ├── ToolMenus\                5.x 모던 메뉴 (FMenuBuilder 후속)
│   │   ├── MainFrame\                메인 윈도우/메뉴
│   │   ├── LevelEditor\              레벨 에디터 본체
│   │   └── AssetRegistry\            에셋 메타 캐시 (Runtime 이지만 Editor 에서 주로 사용)
│   ├── Components\               Tier 1 · 메인 + 15 sub-skill ✅ 완료 (베이스 3 + 시각/메시 5 + 콜리전/물리 2 + 게임플레이 3 + 오디오 1 + 특수 1)
│   ├── GameFramework\            Tier 1 · 메인 + 6 sub-skill (Actor/PawnCharacter/Controller/GameMode/GameInstance/World)
│   ├── AssetClasses\             Tier 1 · 메인 + 9 sub-skill (Mesh/Material/Texture/Animation/Audio/Data/VFX/Camera/Physics)
│   ├── Input\                    Tier 1 · 메인 + 5 sub-skill (EnhancedInput/Action/Subsystem/InputCore/Legacy)
│   ├── Subsystem\                🆕 통합 가이드 (5종 비교 + 작성 표준 + 결정 트리)
│   ├── Significance\             Plugin · SKILL (USignificanceManager + 거리 LOD)
│   ├── GAS\                      Plugin · SKILL (UAbilitySystemComponent + 5종 핵심)
│   └── Niagara\                  Plugin · SKILL (UNiagaraComponent + 5.x VFX 표준)
└── CLAUDE.md                     프로젝트 작업 가이드 (이 문서를 참조)
```

다른 모듈(`Core`/`Engine`/`ApplicationCore`/`Renderer` 등)은 본 위키에 아직 추가되지 않았다 — 향후 같은 sub-skill 분할 패턴으로 채워질 예정. §8 참조.

---

## 2. sub-skill 한 줄 요약 (30개 + 메인 4개)

### 2.1 CoreUObject (Tier 1, 13개) — `skills/CoreUObject/`

| sub-skill | 한 줄 요약 |
|-----------|-----------|
| `UObject` | UObject 베이스 사슬·라이프사이클 (PostInit/PostLoad/BeginDestroy/FinishDestroy) |
| `Reflection` | UClass/UStruct/UFunction/UEnum 메타 + UCLASS/UPROPERTY/UFUNCTION 매크로 + UObjectIterator |
| `Property` | FField/FProperty 사슬 + CastField + TFieldIterator + PropertyWrapper |
| `Package` | UPackage·LinkerLoad/Save·SavePackage·FPackagePath/FPackageName |
| `Interface` | UInterface/IInterface 패턴·TScriptInterface |
| `GC` | CollectGarbage·MarkAsGarbage·FGCObject·FReferenceCollector·클러스터 |
| `Serialization` | FArchive 확장·BulkData·AsyncLoading2·Serialize/PreSave virtual |
| `Network` | UPackageMap·복제 virtual·DOREPLIFETIME·ProcessEvent |
| `Editor` 🛠 | PostEditChange/Modify/Undo virtual·IsDataValid·GetAssetRegistryTags |
| `Cooking` 🛠 | NeedsLoadFor*·BeginCacheForCookedPlatformData·CookedMetaData·UObjectRedirector |
| `StructUtils` | FInstancedStruct·FSharedStruct·FStructView·FInstancedPropertyBag·UUserDefinedStruct |
| `ObjectHandles` | TObjectPtr/TWeakObjectPtr/TSoftObjectPtr/TStrongObjectPtr·SoftObjectPath·TopLevelAssetPath·PrimaryAssetId·FObjectKey |
| `DeprecatedUProperty` | UnrealTypePrivate.h의 옛 UProperty 33개 + FProperty 마이그레이션 가이드 |

### 2.2 SlateCore (Tier 3, 10개) — `skills/SlateCore/`

| sub-skill | 한 줄 요약 |
|-----------|-----------|
| `SWidget` | 위젯 베이스 사슬(SWidget/SCompoundWidget/SLeafWidget/SPanel) + SLATE_BEGIN_ARGS/SLATE_DECLARE_WIDGET + Construct + **TSlateAttribute 자동 인밸리데이션** |
| `Layout` | FGeometry/FArrangedChildren/FMargin/FChildren/EVisibility/SlotBase + TPanelChildren |
| `Drawing` | FSlateDrawElement/FSlateBrush/FSlateRenderTransform/Invalidation + **`OnPaint` LayerId 단조 증가 / DrawCall 배치 / 아틀라스** |
| `Styling` | FSlateStyleSet/FSlateColor/FSlateBrush/FSlateWidgetStyle/USlateWidgetStyleAsset 🛠 |
| `Input` | FReply/FInputEvent/FPointerEvent/FKeyEvent/FFocusEvent/FNavigationConfig/FHittestGrid/Drag-and-Drop |
| `Application` | ISlateApplicationBase/FSlateApplicationBase/FSlateUser/SWindow 베이스/FSlateThrottleManager |
| `Animation` | Slate 자체 트위닝 — FCurveSequence/FCurveHandle/FSlateSprings (MovieScene 무관) |
| `Text` | FSlateFontInfo/FCompositeFont/FSlateFontCache/HarfBuzz/FreeType/ICU 통합 |
| `Types` | TAttribute/TSlateAttribute/SlateEnums/SlateStructs/PaintArgs/ISlateMetaData/WidgetActiveTimer |
| `Trace` 🛠 | FSlateTrace/FSlateDebugging/Slate Insights/Widget Reflector |

### 2.3 Slate (Tier 3, 12개 + 메인) — `skills/Slate/`

> 🚨 **메인 SKILL.md §8 에 인하우스 툴 묶음 표준 규약** (런타임/에디터 분리 4단 방어).

| sub-skill | 한 줄 요약 |
|-----------|-----------|
| `EditorApplication` 🛠 | FSlateApplication 본체·정적 진입점(Create/InitHighDPI/Shutdown)·Tick/PumpMessages/TickAndDrawWidgets·IInputProcessor·FGlobalTabmanager·FSlateUser |
| `Docking` 🛠 | SDockTab·FTabManager·FGlobalTabmanager·SDockingArea·FWorkspaceItem·FLayoutExtender·FLayoutSaveRestore·FSpawnTabArgs·탭 등록/호출/레이아웃 |
| `Menu` 🛠 | FMenuBuilder/FToolBarBuilder/FMenuBarBuilder + FExtender + MultiBox + ToolMenuBase + SMenuAnchor + 메인 메뉴 통합 |
| `Commands` 🛠 | TCommands<T>/FUICommandInfo/FUICommandList/FInputChord/FUIAction/FInputBindingManager/FGenericCommands + 단축키 시스템 |
| `GraphEditor` 🛠 | **EdGraph 런타임 (Engine 모듈)** + **GraphEditor 위젯 (Editor 모듈, 본 위키 분석 범위 예외)** + 인하우스 노드 에디터 작성 패턴 |
| `Application` | FSlateApplication 게임 측면 + FSlateUser 멀티사용자 + IInputProcessor 전역 후크 + NavigationConfig 게임패드 + AnalogCursor + GestureDetector + MenuStack |
| `CommonWidgets` | SButton·SCheckBox·SComboBox·SHyperlink·SSlider·SSpinBox·SInputKeySelector·SSegmentedControl·SVectorInputBox·SMenuAnchor 등 표준 입력 |
| `LayoutWidgets` | SBox·SBorder·SOverlay·SHorizontalBox·SVerticalBox·SScrollBox·SSplitter·SExpandableArea·SSafeZone·SScaleBox·SDPIScaler·SGridPanel·SUniformGridPanel·SConstraintCanvas·SBackgroundBlur·SRadialBox·SLinkedBox |
| `ListsTrees` | SListView<T>·STreeView<T>·STileView<T>·STableViewBase·STableRow<T>·SHeaderRow·SExpanderArrow·IItemsSource (가상 풀링) |
| `TextInput` | SEditableText·SEditableTextBox·SMultiLineEditableTextBox·SSearchBox·SSuggestionTextBox·STextEntryPopup·STextBlock·SRichTextBlock·SInlineEditableTextBlock |
| `MiscWidgets` | FSlateNotificationManager·SNotificationList·SColorPicker·SColorBlock·SImage·SThrobber·SBreadcrumbTrail·SWidgetSwitcher·SViewport·SProgressBar |
| `Animation` | FAnimatedAttribute<T>·FAnimatedAttributeManager·FAttributeInterpolator (5.x 어트리뷰트 자동 보간) |

> ⏸ `Notifications` 🛠 (FSlateNotificationManager 등) — 사용자 보류 (`MiscWidgets` §2 에 통합 작성됨).
> ✅ **게임/에디터 공통 7개 작성 완료** (2026-05-05) — `Application`(SlateApplication 게임 측면) / `CommonWidgets`(SButton·SCheckBox·SSlider 등) / `LayoutWidgets`(SBox·SBorder·SOverlay·SScrollBox·SSplitter 등) / `ListsTrees`(SListView/STreeView/STileView) / `TextInput`(SEditableText·SRichTextBlock 등) / `MiscWidgets`(Notifications·Colors·Images·Throbber·SViewport) / `Animation`(FAnimatedAttribute).

🛠 표시 sub-skill 은 에디터 빌드 의존이 큰 영역. **인하우스 툴 묶음 5개**(EditorApplication/Docking/Menu/Commands/GraphEditor)는 모두 메인 §8 분리 원칙 의무 준수.

### 2.4 UMG (Tier 3, 7개 + 메인) — `skills/UMG/`

| sub-skill | 한 줄 요약 |
|-----------|-----------|
| `UWidget` | UMG 위젯 베이스(UWidget/UPanelWidget/UContentWidget) + RebuildWidget + **§4.4 Super 호출 규약** + **§5 인밸리데이션 의무 섹션** + **§6 Focus/Navigation 시스템 (게임패드·키보드 내비)** + EWidgetTickFrequency |
| `UUserWidget` | UUserWidget 30+ Native* 콜백 + **§4.1.1 Super 호출 + 구획별 초기화 책임 (InputComponent / Extensions / DesiredFocus / InputScriptDelegates / OnNativeDestruct broadcast)** + **NativeOnPaint 함정** + BindWidget(Optional)/PreConstruct/Animation 안전 종료 + Tree 빌드 라이프사이클 |
| `StandardWidgets` | Button/CheckBox/Image/TextBlock/RichTextBlock/ProgressBar/Throbber/Slider/SpinBox/EditableText/ComboBox + 위젯별 핫스팟 회피 |
| `PanelWidgets` | VerticalBox/HorizontalBox/StackBox/WrapBox/CanvasPanel/Overlay/Grid/UniformGrid/ScrollBox + ScaleBox/SizeBox/SafeZone/Border + InvalidationBox/RetainerBox |
| `ListWidgets` | ListView/TreeView/TileView (UListViewBase) + IUserListEntry/IUserObjectListEntry + EntryWidget 풀링 패턴 |
| `Slot` | UPanelSlot 베이스 + 18개 자손 (UVerticalBoxSlot/UCanvasPanelSlot/UGridSlot 등) + 슬롯 setter 자동 인밸리데이션 |
| `ViewModel` | INotifyFieldValueChanged + UPROPERTY(FieldNotify) + UE_FIELD_NOTIFICATION_DECLARE_* + Legacy Binding 회피 + UMVVM 플러그인 연결고리 |

### 2.5 UnrealEd (Editor, 8개 + 메인) 🛠 — `skills/UnrealEd/`

> 🚨 **Editor 모듈** — 게임 빌드 의존 금지. 4단 분리 의무 ([`05_EditorOnlyIndex.md`](./05_EditorOnlyIndex.md)).

| sub-skill | 한 줄 요약 |
|-----------|-----------|
| `AssetEditorToolkit` 🛠 | **인하우스 에셋 에디터 표준** — FAssetEditorToolkit·BaseToolkit·SimpleAssetEditor·FWorkflowCentricApplication·FExtensibilityManager + Toolbar/Tabs/Modes |
| `Subsystems` 🛠 | UAssetEditorSubsystem·UEditorActorSubsystem·UEditorAssetSubsystem·UImportSubsystem 12개 + UEditorSubsystem 베이스 |
| `Kismet2` 🛠 | FBlueprintEditorUtils·FKismetEditorUtilities·FCompilerResultsLog·FKismetReinstanceUtilities + UUserDefinedStruct |
| `Factories` 🛠 | UFactory·UActorFactory·UExporter + Reimport (FReimportHandler) + Interchange 5.x 통합 |
| `Elements` 🛠 | 5.x Element Selection System — FTypedElementHandle·UTypedElementSelectionSet + ITypedElement* 인터페이스 |
| `Layers` 🛠 | ULayersSubsystem (레이어) + Bookmarks (카메라 슬롯) + WorldPartition 빌더 |
| `MaterialEditor` 🛠 | UMaterialGraph·UMaterialGraphNode + UDEditor*ParameterValue 13종 |
| `Misc` 🛠 | Settings·Preferences·ImportUtils·Tools·ViewportToolbar·Dialogs·Animation·Builders·CookOnTheSide·ThumbnailRendering 기타 유틸 |

### 2.6 Editor/Developer 단일 SKILL 모듈 (9개) 🛠

> 각각 `skills/<Module>/SKILL.md` 단일 파일. 인하우스 툴 작성 시 자주 등장하는 모듈들.

| 모듈 | 위치 | 한 줄 요약 |
|------|------|-----------|
| `ToolMenus` 🛠 | Developer | 5.x 모던 메뉴 — UToolMenus·UToolMenu·FToolMenuEntry·FToolMenuSection·FToolMenuContext + `RegisterMenu`/`ExtendMenu`/`FToolMenuOwnerScoped` |
| `EditorFramework` 🛠 | Editor | `IToolkit`/`IToolkitHost`/`UEdMode`/`UPlacementSubsystem`/`UEditorElementSubsystem` + InteractiveToolsFramework 통합 |
| `EditorSubsystem` 🛠 | Editor | `UEditorSubsystem` 베이스 1개 (UDynamicSubsystem 자손) + 자손 작성 시 의존만 추가 |
| `MainFrame` 🛠 | Editor | `IMainFrameModule` (메인 윈도우)·`OnMainFrameCreationFinished`·`SetApplicationTitleOverride` + 표준 `MainFrame.MainMenu.*` |
| `LevelEditor` 🛠 | Editor | `FLevelEditorModule`·`ILevelEditor`·`SLevelViewport`·`ULevelEditorSubsystem`·`FLevelEditorCommands` + 표준 `LevelEditor.*` 메뉴 |
| `EditorWidgets` 🛠 | Editor | `SAssetSearchBox`·`SAssetDropTarget`·`SDropTarget`·`SEnumCombo`·`ITransportControl`·`SAssetFilterBar`·`SInputChord` 공통 위젯 |
| `AssetTools` 🛠 | Developer | `IAssetTools`·`IAssetTypeActions`·`FAssetTypeActions_Base`·`EAssetTypeCategories` + 5.x ToolMenus 통합 |
| `AssetRegistry` 🛠 | Runtime | `IAssetRegistry`·`FAssetData`·`FARFilter`·`IAssetDependencyGatherer` + `OnAssetAdded`/`OnFilesLoaded` 등 콜백 |
| `PropertyEditor` 🛠 | Editor | `IDetailCustomization`·`IPropertyTypeCustomization`·`IDetailLayoutBuilder`·`IPropertyHandle`·`FPropertyEditorModule` + `RegisterCustomClassLayout` |

---

## 3. 시나리오별 하네스 (필수 묶음)

> **3단 분류 의무**:
> - 🚨 **정책 (Must)**: 모든 시나리오 강제 로드 — 횡단 인덱스 (07/09/10/11/12/13)
> - 📌 **필수 (Should)**: 코드 시작 전 반드시 Read — 카테고리 메인 + 핵심 sub-skill
> - 🟡 **선택 (Optional)**: 시나리오 변형 있을 때만 — 추가 sub-skill
>
> ### 🎯 토큰 효율 가이드 (시나리오별 평균)
>
> | 로드 깊이 | 항목 | 평균 토큰 | 200K 사용률 |
> |-----------|------|-----------|-------------|
> | **최소 (정책 + 필수만)** | CLAUDE.md (4K) + 카테고리 메인 (5-8K) + 핵심 sub-skill 1-2개 (8-15K) + 정책 인덱스 2-3개 (12-18K) | **30~45K** | 15~22% |
> | **표준 (정책 + 필수 + 선택 일부)** | 위 + 선택 sub-skill 1-2개 (5-10K) | **40~55K** | 20~27% |
> | **최대 (전체 묶음)** | 위 + 선택 모두 + 횡단 인덱스 4-6개 | **60~80K** | 30~40% |
>
> ### 💡 토큰 절약 패턴
>
> 1. **첫 작업 = 최소만 로드** (정책 + 필수). 막히면 선택 lazy load
> 2. **메인 SKILL.md 인덱스 표 먼저** — sub-skill 본문은 필요한 것만 (Article 3 progressive disclosure)
> 3. **횡단 인덱스 cherry-pick** — 시나리오 표의 🚨 정책 컬럼만 먼저, 추가는 코드 작성 중 lazy
> 4. **30KB+ 큰 sub-skill** = 메인만 (Level 3 references 는 깊이 필요 시만 — Task #186/187 분리 진행 중)



### 3.1 [Components] 새 ActorComponent / SceneComponent 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 (모든 Components 의무) | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 정책) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Tick 스코프) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (전역 이터레이터 금지) |
| 필수 (Components) | [`Components/SKILL.md`](../skills/Components/SKILL.md) (메인) + [`ActorComponent`](../skills/Components/references/ActorComponent.md) (트랜스폼 무관) 또는 [`SceneComponent`](../skills/Components/references/SceneComponent.md) (트랜스폼·부착) |
| 필수 (CoreUObject) | `CoreUObject/UObject`, `CoreUObject/Reflection`, `CoreUObject/GC`, `CoreUObject/ObjectHandles` |
| 선택 | `CoreUObject/Network`(복제 시), `CoreUObject/Editor`(디테일 패널 콜백), `CoreUObject/Property`(런타임 리플렉션 사용) |

라이프사이클(생성자→PostInitProperties→BeginPlay→BeginDestroy)·UPROPERTY 마킹·GC 추적·핸들 선택(TObjectPtr vs TWeakObjectPtr)을 같이 결정해야 한다. **6대 정책 (Mobility / NewObject / GC / GetOwner / Tick / CDO) 의무 준수**.

### 3.2 [Components] 컴포넌트에 네트워크 복제 추가

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (특히 §3 GC 방어 — Replicated UObject = UPROPERTY 필수) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (OnRep_* 스코프) |
| 필수 (Components) | [`ActorComponent §6 Replication 패턴`](../skills/Components/references/ActorComponent.md) + 자식 sub-skill (해당 시) |
| 필수 (CoreUObject) | `CoreUObject/Network`, `CoreUObject/Property`, `CoreUObject/UObject` |
| 선택 | `CoreUObject/Reflection`(매크로 메타), `CoreUObject/Serialization`(NetSerialize 커스텀) |

`GetLifetimeReplicatedProps` override + `DOREPLIFETIME*` + `ReplicatedUsing=OnRep_*` 패턴. **OnRep_* 콜백 첫 줄 프로파일링 스코프 의무**.

### 3.3 [Components] AbilitySystem / GAS 통합 컴포넌트

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 정책) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) |
| 필수 (Components) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) (UAbilitySystemComponent 베이스) + [`Components/SKILL.md §4`](../skills/Components/SKILL.md) |
| 필수 (CoreUObject) | `CoreUObject/UObject`, `CoreUObject/Reflection`, `CoreUObject/GC`, `CoreUObject/ObjectHandles`, `CoreUObject/Network` |
| 선택 | `CoreUObject/StructUtils`(FGameplayAbilityActorInfo 등 USTRUCT), `CoreUObject/Property`(어트리뷰트 리플렉션) |

### 3.4 새 UDataAsset / 데이터 객체 작성

| 묶음 | sub-skill |
|------|-----------|
| 🎯 정책 | [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**`UPrimaryDataAsset` 자식 + `meta=(AssetBundles=)` + DefaultEngine.ini `PrimaryAssetTypesToScan`**) |
| 필수 | `CoreUObject/UObject`, `CoreUObject/Reflection`, `CoreUObject/Serialization`, `CoreUObject/ObjectHandles` |
| 선택 | `CoreUObject/Editor`(IsDataValid·GetAssetRegistryTags), `CoreUObject/Cooking`, `CoreUObject/Package`, [`AssetRegistry`](../skills/AssetRegistry/SKILL.md) |

**Primary Asset 표준** = `UPrimaryDataAsset` 자식 + `GetPrimaryAssetId()` override (Type+Name) + Bundle 명시 (`meta=(AssetBundles="Visual"/"Audio"/...)`) + DefaultEngine.ini 자동 스캔 등록.

### 3.5 에디터 콜백 (PostEditChangeProperty/Modify/Undo) 추가

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/Editor`, `CoreUObject/Property`, `CoreUObject/UObject` |
| 선택 | `CoreUObject/StructUtils`(중첩 USTRUCT 변경), `CoreUObject/Reflection`(메타 키 활용) |

### 3.6 에셋 로드 / TSoftObjectPtr 비동기 처리

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 (가장 중요) | [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**SpawnActor 히칭 4단 원인 + Soft/Hard 6종 비교 + FStreamableManager + UAssetManager Primary Asset/Bundle + PreLoad 5대 정책 + 4단 표준 패턴**) |
| 필수 | `CoreUObject/ObjectHandles` (TSoftObjectPtr §8 통합), `CoreUObject/Package`, `CoreUObject/Serialization` |
| 선택 | `CoreUObject/Cooking`, `CoreUObject/GC`(콜백 동안 보호), [`AssetRegistry`](../skills/AssetRegistry/SKILL.md) (FAssetData / FARFilter) |

### 3.7 인터페이스 (UINTERFACE) 정의

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/Interface`, `CoreUObject/Reflection`, `CoreUObject/UObject` |
| 선택 | `CoreUObject/ObjectHandles`(`TScriptInterface<T>` 멤버), `CoreUObject/Network` |

### 3.8 GC 보호가 필요한 비-UObject 매니저 / 캐시

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/GC`, `CoreUObject/ObjectHandles`, `CoreUObject/UObject` |
| 선택 | `CoreUObject/Property` |

### 3.9 USTRUCT 동적 변형 (FInstancedStruct 등)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/StructUtils`, `CoreUObject/Reflection`, `CoreUObject/Property` |
| 선택 | `CoreUObject/Serialization`, `CoreUObject/Editor` |

### 3.10 레거시 코드 마이그레이션 (UProperty → FProperty)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/DeprecatedUProperty`, `CoreUObject/Property`, `CoreUObject/Reflection` |
| 선택 | `CoreUObject/Serialization` |

### 3.11 결정론적 직렬화 / 쿠킹 회귀 디버그

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `CoreUObject/Serialization`, `CoreUObject/Cooking`, `CoreUObject/Package` |
| 선택 | `CoreUObject/GC`(`FReferenceChainSearch`) |

### 3.12 [Slate] 새 SWidget 작성 (단일 위젯)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `SlateCore/SWidget`, `SlateCore/Layout`, `SlateCore/Drawing`, `SlateCore/Types` |
| 선택 | `SlateCore/Styling`(스타일셋 자원 사용), `SlateCore/Input`(인터랙션), `SlateCore/Animation`(트위닝), `SlateCore/Text`(폰트) |

`SCompoundWidget`/`SLeafWidget` 베이스 + `SLATE_BEGIN_ARGS` + `Construct` + `OnPaint`/`OnArrangeChildren`. **TSlateAttribute 자동 인밸리데이션** 활용.

### 3.13 [Slate] 위젯 인터랙션 / 입력 처리

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `SlateCore/Input`, `SlateCore/SWidget`, `SlateCore/Layout` |
| 선택 | `SlateCore/Application`(캡처/포커스), `SlateCore/Drawing`(인밸리데이션) |

`OnMouseButtonDown/Up/Move`/`OnKeyDown` + `FReply` 체이닝(CaptureMouse/SetUserFocus/BeginDragDrop).

### 3.14 [Slate] 사용자 정의 스타일셋 등록

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `SlateCore/Styling`, `SlateCore/Drawing` |
| 선택 | `SlateCore/Text`(폰트 스타일) |

`FSlateStyleSet` + `FSlateStyleRegistry` + 모듈 Initialize/Shutdown 패턴.

### 3.15 [Slate] OnPaint LayerId·DrawCall 최적화 / 인밸리데이션 디버깅

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `SlateCore/Drawing`, `SlateCore/SWidget`, `SlateCore/Trace` |
| 선택 | `SlateCore/Application`(Tick 사이클) |

LayerId 단조 증가 / `FSlateElementBatcher` 배치 / 텍스처 아틀라스 / `SInvalidationPanel` / `Slate.DrawElementsStats`.

### 3.16 [Slate] 인하우스 툴 시작 (모듈·도킹·메뉴·단축키 통합 골격)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/EditorApplication`, `Slate/Docking`, `Slate/Menu`, `Slate/Commands` |
| 선택 | `Slate/Notifications`(향후), `SlateCore/Application`, `SlateCore/Styling`, `SlateCore/Input`, `CoreUObject/Editor` |

🚨 **메인 `Slate/SKILL.md §8` 의 런타임/에디터 분리 원칙 필수 준수.** Build.cs 분기 + `Type=Editor` 모듈 + `#if WITH_EDITOR` 가드 4단 방어. `IModuleInterface::StartupModule` 4단(명령 등록 → 액션 매핑 → 메인 메뉴 Extender → 도킹 탭 등록).

### 3.17 [Slate] 도킹 탭만 추가 (기존 에디터에 패널 추가)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/Docking`, `Slate/EditorApplication` |
| 선택 | `Slate/Menu`(메인 메뉴 항목), `Slate/Commands`(단축키) |

`FGlobalTabmanager::Get()->RegisterNomadTabSpawner` + `WorkspaceMenu::GetMenuStructure` 카테고리.

### 3.18 [Slate] 메뉴/툴바 항목만 추가 (Extender)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/Menu`, `Slate/Commands` |
| 선택 | `Slate/EditorApplication` |

`FExtender::AddMenuExtension` 또는 `AddToolBarExtension` + `IExtensibilityManager`.

### 3.19 [Slate] 단축키만 추가 (전역 또는 패널)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/Commands`, `SlateCore/Input` |
| 선택 | `Slate/EditorApplication`(IInputProcessor 등록) |

`TCommands<T>` + `UI_COMMAND` + `FUICommandList::MapAction` + 위젯의 `OnKeyDown` 에서 `ProcessCommandBindings`.

### 3.20 [Slate] 노드 그래프 에디터 (인하우스 비주얼 스크립트 / 머티리얼 같은 도구)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/GraphEditor`, `Slate/EditorApplication`, `Slate/Docking`, `Slate/Menu`, `Slate/Commands` |
| 선택 | `CoreUObject/UObject`(노드 라이프사이클), `CoreUObject/Editor`(노드 편집 콜백), `CoreUObject/Serialization`(그래프 호환성) |

🚨 **EdGraph 런타임 (Engine 모듈, 게임 빌드 OK)** + **GraphEditor 위젯 (Editor 모듈, 게임 빌드 X)** 모듈 분리가 핵심. 본 위키 분석 범위 외 GraphEditor 모듈 예외 처리 명시.

### 3.21 [Slate] standalone 인하우스 툴 (별도 .exe — UnrealHeaderTool 패턴)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `Slate/EditorApplication`, `SlateCore/Application` |
| 선택 | `Slate/Docking`, `Slate/Menu`, `Slate/Commands` |

`FSlateApplication::InitializeAsStandaloneApplication` + 자체 메인 루프 (`Tick`/`PumpMessages`/`DrawWindows`).

### 3.22 [Slate] 위젯 트리 디버깅 / 성능 측정

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `SlateCore/Trace`, `SlateCore/Drawing`, `SlateCore/Application` |
| 선택 | `SlateCore/SWidget`, `SlateCore/Types` |

Widget Reflector / Slate Insights / `Slate.InvalidationDebugging.*` cvar / `stat SlateRendering`.

### 3.23 [Slate] 새 UUserWidget / UMG 위젯 작성 (BP 노출)

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `UMG/UWidget`, `UMG/UUserWidget`, `SlateCore/SWidget`, `SlateCore/Layout`, `SlateCore/Drawing` |
| 선택 | `SlateCore/Input`(인터랙션), `SlateCore/Styling`(테마), `04_OverrideIndex.md`(Native* 사슬), `06_InvalidationHotspots.md`(NativeOnPaint·NativeTick 회피) |

`Native*` 사슬(NativeOnInitialized → NativePreConstruct → NativeConstruct → NativeTick → NativeDestruct)·`BindWidget` 메타·`RebuildWidget` 5단계.

### 3.24 [Slate/UMG] RichText/EditableText/ListView 인밸리데이션 다발 디버깅

| 묶음 | sub-skill |
|------|-----------|
| 필수 | `06_InvalidationHotspots.md`, `UMG/UWidget`, `SlateCore/Drawing`, `SlateCore/Trace` |
| 선택 | `UMG/UUserWidget`(NativeOnPaint 함정), `SlateCore/SWidget`(SInvalidationPanel) |

`UInvalidationBox` 결정 트리(§3) + `bIsVolatile`/`ForceVolatile` 결정 트리(§4) + `NativeTick` 회피 계층(§5) + `Slate.InvalidationDebugging.*` cvar.

### 3.25 [Render] 새 SWidget·UMG 위젯 작성 (현재 부분 커버)

| 묶음 | sub-skill |
|------|-----------|
| 필수 (CoreUObject 한정) | `CoreUObject/UObject`(MaterialController UCLASS), `CoreUObject/ObjectHandles`(머티리얼 인스턴스 핸들) |
| 미작성 | `RHI`/`RenderCore`/`Renderer` sub-skill — 향후 Tier 2에서 추가. 그 전엔 코드 컨벤션은 `CLAUDE.md §4` 만 따른다. |

### 3.26 [Components] 새 PrimitiveComponent (콜리전 + 렌더 자식)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대) + [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) (Overlap 비용) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) |
| 필수 (Components 베이스 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) (3단 베이스 모두) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` |
| 선택 | `Network`(복제), `Editor`(PostEditChange) |

콜리전 채널/프로필/응답 + Overlap/Hit 이벤트 + RenderProxy + HLOD + Material 동적. **PrimitiveComponent 자손은 거의 모든 시각/콜리전 클래스의 베이스 — 필수 체인**.

### 3.27 [Components] 새 ShapeComponent (트리거·콜라이더 — Box/Sphere/Capsule)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + 🚨 [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) (트리거 = 가장 큰 Overlap 발생원) |
| 필수 (Components 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) → [`ShapeComponents`](../skills/Components/references/ShapeComponents.md) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC` |
| 선택 | `Network` (트리거 결과 복제), `Editor` |

`UBoxComponent` / `USphereComponent` / `UCapsuleComponent` (Pawn 표준 Capsule). **OnComponentBeginOverlap 콜백 = 프로파일링 스코프 의무 + TActorIterator 절대 금지**.

### 3.28 [Components] 새 MeshComponent (Static/Skeletal/ISM/HISM)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) (Skeletal Capsule overlap) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) |
| 필수 (Components 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) → [`MeshComponents`](../skills/Components/references/MeshComponents.md) (§7 SkeletalMesh Tick 최적화 깊이) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (Mesh asset SoftObjectPtr) |
| 선택 (SkeletalMesh) | [`Significance`](../skills/Significance/SKILL.md) (거리 기반 LOD), `Network` |

SkeletalMesh 의 경우 EVisibilityBasedAnimTickOption 5종 + URO + AnimationBudgetAllocator 통합 결정. **다수 NPC 환경 = Significance 통합 필수**.

### 3.29 [Components] 새 LightComponent (Point/Spot/Rect/Directional/Sky)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (특히 §1 Mobility — 비용의 핵심) |
| 필수 (Components 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`LightComponents`](../skills/Components/references/LightComponents.md) (Mobility × Type 비용 매트릭스) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC` |
| 선택 | [`Significance`](../skills/Significance/SKILL.md) (다수 라이트 거리 기반 토글), `Editor` |

Static (Lightmap·0 비용) / Stationary (4개 영역 한도) / Movable (Realtime Shadow Map·매 프레임). **AttenuationRadius / CastShadows / 채널이 비용 결정**.

### 3.30 [Components] 새 PhysicsComponent (Constraint/Handle/Spring/Thruster/RadialForce/PhysAnim/ClusterUnion)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (Mobility 보통 Movable 강제) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (PhysAnim Tick) |
| 필수 (Components 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PhysicsComponents`](../skills/Components/references/PhysicsComponents.md) |
| 의존 (관련 컴포넌트) | [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) (Constraint = 두 RigidBody) + [`MeshComponents`](../skills/Components/references/MeshComponents.md) (PhysAnim = SkeletalMesh) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC` |
| 선택 | `Network`(ClusterUnion 복제), `StructUtils`(FConstraintInstance) |

**PhysAnim 은 BeginPlay 이후만 ApplyPhysicalAnimationSettings (UnsafeDuringActorConstruction)**. ClusterUnion 부품 추가/제거는 Solver Restart — BeginPlay 1회.

### 3.31 [Components] 새 MovementComponent (UpdatedComponent + 복제 예측)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (UpdatedComponent 의 Mobility = Movable 필수) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (PerformMovement / Phys*) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (Tick 안 TActorIterator 절대 금지) |
| 필수 (Components 체인) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) → [`MovementComponents`](../skills/Components/references/MovementComponents.md) (UCharacterMovementComponent 5종 모드 + Phys* + ServerMove RPC) |
| 의존 (UpdatedComponent) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) (Updated 베이스) + [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) (콜리전 sweep) + [`ShapeComponents`](../skills/Components/references/ShapeComponents.md) (Capsule = ACharacter Root) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `Network`, `Property` |
| 선택 | [`MeshComponents`](../skills/Components/references/MeshComponents.md) (Mesh 페어), [`CameraComponent`](../skills/Components/references/CameraComponent.md) (SpringArm 페어), `Serialization`(SavedMove 압축) |

CharacterMovement 자식: SavedMove + PredictionData_Client 팩토리 + UpdateFromCompressedFlags. **속도값 직접 RPC 금지 — 입력 플래그만**.

### 3.32 [Components] 새 CameraComponent + SpringArm (3인칭/1인칭)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (GetCameraView override 시) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`CameraComponent`](../skills/Components/references/CameraComponent.md) (UCameraComponent + UCameraShakeSourceComponent) |
| 의존 (페어) | [`MovementComponents`](../skills/Components/references/MovementComponents.md) (USpringArmComponent — 카메라 boom·콜리전 회피) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC` |
| 선택 | `Editor`(에디터 시각화 — UCameraProxyMeshComponent) |

3인칭 표준 = SpringArm + Camera 페어. **SpringArm 만 bUsePawnControlRotation = true, Camera 는 false** (이중 회전 금지).

### 3.33 [Components] 새 AudioComponent / ForceFeedback

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (Tick 거의 안 씀 — bCanEverTick = false) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (OnAudioFinished 콜백) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`AudioComponent`](../skills/Components/references/AudioComponent.md) (UAudioComponent + UForceFeedbackComponent + 5.x ISoundParameterControllerInterface + Quartz) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (Sound asset) |
| 선택 | `Network`(폭발음 복제), `Interface`(ISoundParameterController) |

**`SpawnSoundAttached` / `SpawnForceFeedbackAtLocation` 표준 사용** — 직접 컴포넌트 생성 X. Concurrency 적용 + UI 사운드 = `bIsUISound = true`.

### 3.34 [Components] 새 ParticleComponent / Niagara 통합

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**NiagaraSystem 자산 PreLoad + Pool**) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (OnSystemFinished) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) (UFXSystemComponent 자손) → [`ParticleComponents`](../skills/Components/references/ParticleComponents.md) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (NiagaraSystem asset) |
| 선택 | [`Significance`](../skills/Significance/SKILL.md) (거리 기반 SpawnRate 토글) |

**신규 = Niagara (UNiagaraComponent — Niagara 플러그인)**. Cascade 는 호환·기존 자산만. 풀링 = `ENCPoolMethod::AutoRelease`.

### 3.35 [Components] 새 RenderingComponent (Decal/TextRender/SceneCapture/Billboard/PostProcess)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (SceneCapture 수동 Capture 콜백) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) (Billboard/TextRender/MaterialBillboard/Arrow 자손) → [`RenderingComponents`](../skills/Components/references/RenderingComponents.md) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (Material/Texture asset) |
| 선택 | `Editor` (에디터 전용 Arrow/DrawSphere 등) |

**SceneCapture2D `bCaptureEveryFrame = false` + 수동 호출**. Decal Material Domain = `Deferred Decal` 필수. PostProcessSettings 는 `bOverride_*` 비트만 활성.

### 3.36 [Components] 야외 환경 셋업 (Sky/Atmosphere/Fog/Cloud/Wind)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`AtmosphereComponents`](../skills/Components/references/AtmosphereComponents.md) (4종 + 5.x 야외 5종 페어) |
| 의존 (페어) | [`LightComponents`](../skills/Components/references/LightComponents.md) (DirectionalLight + SkyLight 표준 페어) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (Cubemap/Material) |

**5.x 야외 표준** = SkyAtmosphere + DirectionalLight + SkyLight + ExpHeightFog + VolumetricCloud. DirectionalLight = Stationary/Movable (시간 변화).

### 3.37 [Components] 새 SystemComponent (Input — Enhanced Input / ChildActor)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (InputAction 콜백 첫 줄) |
| 필수 (Components) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) (UInputComponent 베이스) → [`SystemComponents`](../skills/Components/references/SystemComponents.md) (Enhanced Input 5.x + UChildActorComponent) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (InputAction/MappingContext asset) |
| 선택 | `CoreUObject/Editor` (디테일 패널) |

**5.x 신규 = Enhanced Input** (UEnhancedInputComponent + UInputMappingContext). LocalPlayerSubsystem 으로 매핑 등록.

### 3.38 [Components] 새 SpecialComponent (Spline/SplineMesh/Timeline/StereoLayer)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Timeline UFUNCTION 콜백) |
| 필수 (Components) | [`SceneComponent`](../skills/Components/references/SceneComponent.md) → [`SpecialComponents`](../skills/Components/references/SpecialComponents.md) (Spline/SplineMesh = StaticMeshComponent 자손/Timeline = ActorComponent/StereoLayer = VR HMD) |
| 의존 (SplineMesh) | [`PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) → [`MeshComponents`](../skills/Components/references/MeshComponents.md) (UStaticMeshComponent 자손) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC` |
| 선택 | `Network` (Timeline 복제 시) |

SplineMesh 100+ 세그먼트 = 드로우콜 폭사 → **HISM 또는 Nanite 검토**. Timeline 콜백 = UFUNCTION + 첫 줄 프로파일링 스코프.

### 3.39 [Components] 다수 NPC / 거리 기반 LOD 최적화 (Significance 통합)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (특히 §5 PrimaryComponentTick — TickInterval) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (Significance 등록 패턴 = 전역 이터레이터 회피) |
| 필수 | [`Significance`](../skills/Significance/SKILL.md) (USignificanceManager + FOrderedBudget + 4개 Budget 시스템 비교) |
| 의존 (대상 컴포넌트) | [`MeshComponents`](../skills/Components/references/MeshComponents.md) (SkeletalMesh §7) + [`LightComponents`](../skills/Components/references/LightComponents.md) + [`ParticleComponents`](../skills/Components/references/ParticleComponents.md) + [`PhysicsComponents`](../skills/Components/references/PhysicsComponents.md) |
| 필수 (CoreUObject) | `UObject`, `GC`, `ObjectHandles` (TWeakObjectPtr 캐싱) |

거리 기반 SpawnRate / Tick / Shadow / Animation 토글. **AnimationBudgetAllocator + FOrderedBudget + TickInterval + CVar 4종 차이 명확히**.

### 3.40 [Components/GAS] GAS 통합 캐릭터 (어빌리티 / 어트리뷰트 / 이펙트)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 — ASC = UActorComponent) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**Ability/Effect Class = Hard / Cosmetic GameplayCue VFX·SFX = Soft + GameplayCueManager LoadPrimaryAsset Bundle**) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (ActivateAbility 스코프) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (Ability 안 TActorIterator 금지) |
| 필수 (Plugin) | [`GAS`](../skills/GAS/SKILL.md) (UAbilitySystemComponent + UAttributeSet + UGameplayAbility + GameplayEffect + GameplayTag) |
| 의존 (Components) | [`ActorComponent`](../skills/Components/references/ActorComponent.md) (ASC = UActorComponent 자손) + [`MovementComponents`](../skills/Components/references/MovementComponents.md) (RootMotionSource 통합) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles`, `Network` |
| 선택 | `StructUtils` (FGameplayAbilitySpec 등), `Property` (Attribute 메타) |

**Pawn 모델 vs PlayerState 모델 결정** (단순 = Pawn / MOBA = PlayerState). Replication = Mixed (Player) / Minimal (AI). InstancingPolicy = `InstancedPerActor` + NetExecutionPolicy = `LocalPredicted` 표준.

### 3.41 [Components/Niagara] Niagara VFX 시스템 통합

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**NiagaraSystem 자산 = Soft + Match Start PreloadPrimaryAssets + ENCPoolMethod::AutoRelease 사전 인스턴스**) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (OnSystemFinished 콜백) |
| 필수 (Plugin) | [`Niagara`](../skills/Niagara/SKILL.md) (UNiagaraComponent + UNiagaraSystem + Stack 모듈 + Data Interface + GPU/CPU SimTarget + Pooling) |
| 의존 (Components) | [`ParticleComponents`](../skills/Components/references/ParticleComponents.md) (Cascade — legacy / UFXSystemComponent 공통) + [`Significance`](../skills/Significance/SKILL.md) (거리 기반 SpawnRate) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` (NiagaraSystem 자산) |

**SpawnSystemAtLocation/Attached 표준** + `ENCPoolMethod::AutoRelease` + User Variables 동적 제어 + GPU Emitter Bounds 수동 + Significance + 데이터 인터페이스 (SkeletalMesh 표면 Spawn 등).

### 3.42 [GameFramework] 새 AActor 작성 (베이스 + 라이프사이클 11단계)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**SpawnActor 히칭 방지 4단 + Class CDO 로드 + Soft vs Hard**) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) |
| 필수 | [`GameFramework/SKILL.md`](../skills/GameFramework/SKILL.md) (메인) + [`GameFramework/Actor`](../skills/GameFramework/references/Actor.md) (라이프사이클 11단계 + Spawn + Tick + Replication + **§12 SpawnActor 히칭 방지**) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` |
| 선택 | `Network`(복제), `Editor` 🛠 (PostEditChange) |

**라이프사이클 11단계** Constructor → PostInitProperties → PostSpawnInitialize → OnConstruction (멱등) → PreInit/Init/PostInit → FinishSpawning → BeginPlay → Tick → EndPlay → Destroyed → BeginDestroy.

### 3.43 [GameFramework] APawn / ACharacter 작성 (게임 캐릭터)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**SkeletalMesh / AnimBP / PhysicsAsset Soft + Bundle + Modular Character**) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) + [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) (Capsule) |
| 필수 | [`GameFramework/PawnCharacter`](../skills/GameFramework/references/PawnCharacter.md) (APawn 598 + ACharacter 1,095 깊이 + **§6 최적화 10종**) |
| 의존 | [`GameFramework/Actor`](../skills/GameFramework/references/Actor.md) + [`Components/MovementComponents`](../skills/Components/references/MovementComponents.md) (CMC 5,200 lines) + [`Components/MeshComponents`](../skills/Components/references/MeshComponents.md) (SkeletalMesh §7) + [`Components/ShapeComponents`](../skills/Components/references/ShapeComponents.md) (Capsule) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles`, `Network` |
| 선택 | [`Significance`](../skills/Significance/SKILL.md) (다수 NPC), [`Components/SystemComponents`](../skills/Components/references/SystemComponents.md) (Enhanced Input) |

**🎯 최적화 10종** Tick 회피·URO·EVisibilityBasedAnimTickOption·Significance·AnimationBudgetAllocator·Network·Mesh LOD·Capsule Channel·PostProcess AnimBP LOD·**AI vs Player 매트릭스** (Significance 1.0/0.5/0.1 9개 항목).

### 3.44 [GameFramework] AController / APlayerController / AIController 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) |
| 필수 | [`GameFramework/Controller`](../skills/GameFramework/references/Controller.md) (AController 420 + APlayerController 2,377 + AIController cross-link) |
| 의존 | [`GameFramework/Actor`](../skills/GameFramework/references/Actor.md) + [`GameFramework/PawnCharacter`](../skills/GameFramework/references/PawnCharacter.md) (Possess 페어) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles`, `Network` (RPC) |
| 선택 | [`Components/SystemComponents`](../skills/Components/references/SystemComponents.md) (Enhanced Input), [`Slate`](../skills/Slate/SKILL.md) (UI Mode) |

**Possess 흐름** (Server only — `OnPossess` override) + **Input Mode 3종** (UIOnly/GameAndUI/GameOnly) + **Input Stack** (Push/Pop) + **Camera Manager** + **SeamlessTravel** + **AcknowledgePawn**.

### 3.45 [GameFramework] AGameMode / GameState / PlayerState 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**🔥 GameMode = PreLoad 진입점** — `HandleMatchHasStarted` 안 `PreloadPrimaryAssets(bLoadRecursive=true)` 의무) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) |
| 필수 | [`GameFramework/GameMode`](../skills/GameFramework/references/GameMode.md) (GameModeBase 672 + GameMode Match State 5종 + GameStateBase + GameState + PlayerState) |
| 의존 | [`GameFramework/Actor`](../skills/GameFramework/references/Actor.md) + [`GameFramework/Controller`](../skills/GameFramework/references/Controller.md) (PostLogin / SeamlessTravel) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles`, `Network` |
| 선택 | [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) |

**🔒 서버 only Authority** + **Match State 5종** + **PlayerState CopyProperties** SeamlessTravel.

### 3.46 [GameFramework] UGameInstance + Subsystem 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**🔥 GameInstance = 글로벌 PreLoad 진입점** — `Init()` 안 `ScanPathForPrimaryAssets` + DefaultEngine.ini `PrimaryAssetTypesToScan` 등록) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (Subsystem 등록 패턴) |
| 필수 | [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) (UGameInstance 664 + Subsystem 4종 비교) |
| 의존 | [`UnrealEd/Subsystems`](../skills/UnrealEd/Subsystems/SKILL.md) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` |

**Init / Shutdown 1회** + **Subsystem 4종** (Engine/GameInstance/World/LocalPlayer) + **Online Session 진입점** + **HandleNetworkError**. **🎯 Manager / Service / Cache → 모두 GameInstanceSubsystem 자식**.

### 3.47 [GameFramework] UWorld / ULevel + WorldSubsystem 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) |
| 필수 | [`GameFramework/World`](../skills/GameFramework/references/World.md) (UWorld 4,667 + ULevel + Tick Group 8종 + Streaming 3종 + WorldSubsystem) |
| 의존 | [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) + [`Components/SystemComponents`](../skills/Components/references/SystemComponents.md) (WP §10) |
| 필수 (CoreUObject) | `UObject`, `Reflection`, `GC`, `ObjectHandles` |

**Tick Group 8종** + **Level Streaming 3종** (Always Loaded / Streaming / WorldPartition) + **UWorldSubsystem 등록 패턴** (TActorIterator 회피 표준).

### 3.48 [GameFramework] / [모든 카테고리] SpawnActor 히칭 방지 + 어셋 비동기 로드

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 (가장 중요) | [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (**SpawnActor 히칭 4단 원인 + Soft/Hard Reference + FStreamableManager + UAssetManager Primary Asset/Bundle + PreLoad 5대 정책 + 4단 표준 패턴**) + [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Async Load 콜백 스코프) |
| 필수 | [`GameFramework/Actor §12`](../skills/GameFramework/references/Actor.md) (**SpawnActor 히칭 방지 4단 표준 패턴**) + [`CoreUObject/ObjectHandles`](../skills/CoreUObject/references/ObjectHandles.md) (TSoftObjectPtr / TSoftClassPtr / FSoftObjectPath / FPrimaryAssetId) |
| 의존 | [`CoreUObject/Package`](../skills/CoreUObject/references/Package.md) (UPackage / LoadPackageAsync) + [`CoreUObject/Cooking`](../skills/CoreUObject/references/Cooking.md) (Cooked Build) + [`AssetRegistry`](../skills/AssetRegistry/SKILL.md) (FAssetData / FARFilter) |
| 통합 | [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) (Init 안 PrimaryAssetType 스캔 + 글로벌 PreLoad) + [`GameFramework/GameMode`](../skills/GameFramework/references/GameMode.md) (HandleMatchHasStarted PreLoad) + [`GameFramework/World`](../skills/GameFramework/references/World.md) (Map 전환 LoadingScreen) |

**🎯 Cooked Build 첫 SpawnActor 히칭 (수백 ms ~ 수 초) 회피** — Editor PIE 와 동작 차이의 90% 원인. **4단 표준 = PreLoad (PreloadPrimaryAssets bLoadRecursive=true) → Wait → SpawnActorDeferred → FinishSpawning**.

### 3.49 [Subsystem] 새 Subsystem 작성 (5종 통합)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (TActorIterator 회피 — Subsystem 우선 사용 표준) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Initialize/Deinitialize 콜백 스코프 의무) |
| 필수 | [`Subsystem/SKILL.md`](../skills/Subsystem/SKILL.md) (**5종 비교 매트릭스 + 작성 표준 패턴 + 결정 트리 9 시나리오 + 함정 10종**) |
| 필수 (CoreUObject) | `CoreUObject/UObject` (라이프사이클) · `CoreUObject/Reflection` (UCLASS / GENERATED_BODY) · `CoreUObject/GC` (UPROPERTY 의무) |
| 깊이 (베이스 별) | [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) (UGameInstanceSubsystem) · [`GameFramework/World`](../skills/GameFramework/references/World.md) (UWorldSubsystem) · [`Input/Subsystem`](../skills/Input/references/Subsystem.md) (UEnhancedInputLocalPlayerSubsystem) · [`EditorSubsystem`](../skills/EditorSubsystem/SKILL.md) 🛠 (UEditorSubsystem) · [`UnrealEd/Subsystems`](../skills/UnrealEd/Subsystems/SKILL.md) 🛠 |
| 선택 | [`10_ComponentPolicies.md §3`](./10_ComponentPolicies.md) (UObject 멤버 GC 방어) · `CoreUObject/Network` (UFUNCTION RPC + GetFunctionCallspace) |

**5종 베이스 결정**: Engine 라이프사이클 = `UEngineSubsystem` / Editor 전용 🛠 = `UEditorSubsystem` / Map 전환 살아남음 = **`UGameInstanceSubsystem`** ⭐ / Map 마다 새로 + Tick 안 함 = `UWorldSubsystem` / Map 마다 새로 + Tick 필요 = `UTickableWorldSubsystem` / LocalPlayer 별 (Couch Co-op) = `ULocalPlayerSubsystem`.

### 3.50 [Animation] 캐릭터 + AnimBP 셋업 + NativeUpdate 분리

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Native* + _AnyThread 의무) + [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (UPROPERTY GC 방어) + [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) (AnimBP / Montage Match Start PreLoad) |
| 필수 | [`Animation/SKILL.md`](../skills/Animation/SKILL.md) (메인 + 6 sub-skill) + [`Animation/references/AnimInstance.md`](../skills/Animation/references/AnimInstance.md) ⭐ (Native* 5단계 + Proxy + Curve + Montage_*) |
| 필수 (자산 페어) | [`AssetClasses/references/Animation.md`](../skills/AssetClasses/references/Animation.md) (UAnimBlueprint / UAnimMontage / UAnimSequence) |
| 필수 (호스트 페어) | [`Components/references/MeshComponents.md`](../skills/Components/references/MeshComponents.md) (USkeletalMeshComponent — AnimClass 지정) |
| 깊이 (RootMotion 시) | [`Animation/references/RootMotion.md`](../skills/Animation/references/RootMotion.md) + [`Components/references/MovementComponents.md`](../skills/Components/references/MovementComponents.md) §5.12 (CMC 페어 의무) |

**의무**: NativeUpdate (게임 스레드 — Owner 캐싱) ↔ NativeThreadSafeUpdate (워커 — 캐싱 값) 분리 + Super FIRST + 첫 줄 프로파일링 스코프.

### 3.51 [Animation] Custom AnimNode (FAnimNode_Base) 작성

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`05_EditorOnlyIndex.md`](./05_EditorOnlyIndex.md) (UAnimGraphNode_* 4단 분리) |
| 필수 | [`Animation/references/AnimGraph.md`](../skills/Animation/references/AnimGraph.md) (4단계 _AnyThread + StateMachine + Layer Interface) |
| 필수 (Editor 노드) | [`Editor/SKILL.md`](../skills/Editor/SKILL.md) (UAnimGraphNode_* Editor 모듈 분리) |
| 깊이 | [`Animation/references/Sync.md`](../skills/Animation/references/Sync.md) (SyncGroup + Inertialization 5.x) |

**의무**: `Initialize_AnyThread` / `CacheBones_AnyThread` / `Update_AnyThread` / `Evaluate_AnyThread` 4단계 + 자식 FPoseLink 호출 + 워커 스레드 (Owner 접근 X) + UAnimGraphNode_* Editor 모듈 분리.

### 3.52 [Animation] AnimNotify / NotifyState 작성 (발자국 / 콤보 / 히트박스)

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Notify 첫 줄 스코프) + [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) §5 (Pool / AutoRelease) |
| 필수 | [`Animation/references/AnimNotify.md`](../skills/Animation/references/AnimNotify.md) |
| 필수 (Spawn) | [`Niagara/SKILL.md`](../skills/Niagara/SKILL.md) (`ENCPoolMethod::AutoRelease`) + [`AssetClasses/references/Audio.md`](../skills/AssetClasses/references/Audio.md) |
| 깊이 (Branch Point) | [`AssetClasses/references/Animation.md`](../skills/AssetClasses/references/Animation.md) §3 |

**의무**: Owner 검증 (`IsValid`) + VFX = `ENCPoolMethod::AutoRelease` + NotifyState 의 NotifyEnd 페어 + Branch Point (Montage Section 정밀).

### 3.53 [Animation] 다수 NPC (50+) 60fps 유지 ⭐⭐

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) §1 (Bone LOD + URO + Visibility + Significance 4중) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (TActorIterator 회피 — Significance 등록 표준) |
| 필수 ⭐⭐ | [`Animation/references/Optimization.md`](../skills/Animation/references/Optimization.md) (5중 통합 — URO + Visibility + Sharing + Budget + Significance) |
| 필수 | [`Components/references/MeshComponents.md`](../skills/Components/references/MeshComponents.md) §7 (URO + EVisibilityBasedAnimTickOption 5종) + [`Significance/SKILL.md`](../skills/Significance/SKILL.md) (USignificanceManager) |
| 깊이 (100+ NPC) | `USkeletalMeshComponentBudgeted` + `IAnimationBudgetAllocator` (AnimationBudgetAllocator Plugin) |
| 깊이 (군중 동일 모션) | `UAnimSharingInstance` |

**환경별 결정 매트릭스**: 1~10 = URO + AlwaysTickPose / 10~50 = + OnlyTickPoseWhenRendered + Significance / 50~100 = + Tick Interval 거리 기반 / 100+ = `USkeletalMeshComponentBudgeted` ⭐ / 군중 동일 모션 = + AnimSharing.

### 3.54 [Animation] IK Rig 작성 (5.x 표준 — 발 IK / 무기 IK / 시선 추적 동시) ⭐

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (IK Solver _AnyThread 의무) + [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) §1 (LOD Threshold + Bone LOD 페어) |
| 필수 ⭐ | [`Animation/references/IK.md`](../skills/Animation/references/IK.md) (5.x IK Rig + 7 Solvers + 16 Retarget Ops + Legacy IK 8종) |
| 필수 (런타임) | [`Animation/references/AnimInstance.md`](../skills/Animation/references/AnimInstance.md) (NativeUpdate Goal 캐싱 → NativeThreadSafe 전달) + [`Animation/references/AnimGraph.md`](../skills/Animation/references/AnimGraph.md) (FAnimNode_IKRig 노드) |
| 필수 (자산) | [`AssetClasses/references/Animation.md`](../skills/AssetClasses/references/Animation.md) (Skeleton 호환 검사) |
| Plugin 의존 | Build.cs `IKRig` (Plugin) + .uplugin `IKRig` enabled |
| 깊이 (다수 NPC) | [`Animation/references/Optimization.md`](../skills/Animation/references/Optimization.md) (LOD Threshold + IK skip) |

**5.x IK Rig 표준 흐름**: UIKRigDefinition 자산 (Goals + Solver Stack) → AnimGraph FAnimNode_IKRig → NativeUpdate (Goal 위치 Trace) → NativeThreadSafe (BlueprintReadOnly UPROPERTY).

### 3.55 [Animation] IK Retargeter (다른 Skeleton 모션 재사용) ⭐

| 묶음 | sub-skill |
|------|-----------|
| 🚨 정책 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (Retargeter 콜백) + [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) §1 (Source Mesh Hidden) |
| 필수 ⭐ | [`Animation/references/IK.md`](../skills/Animation/references/IK.md) §4 (UIKRetargeter + 16 Retarget Ops + FAnimNode_RetargetPoseFromMesh) |
| 필수 (Source/Target 자산) | UIKRigDefinition 2개 (Source: Mannequin, Target: Custom Char) |
| 필수 (자산) | [`AssetClasses/references/Mesh.md`](../skills/AssetClasses/references/Mesh.md) §3 (USkeleton + Compatible Skeleton) |
| 깊이 (StrideWarping / SpeedPlanting) | [`Animation/references/IK.md`](../skills/Animation/references/IK.md) §4.3 (16 Retarget Ops) |

**5.x IK Retargeter 표준 흐름**: Source IKRig (예: SK_Mannequin_IKRig) + Target IKRig (예: SK_MyChar_IKRig) → UIKRetargeter 자산 (ChainMappings + RetargetOps) → AMyChar 안 Source SkelMesh `SetVisibility(false)` → AnimBP FAnimNode_RetargetPoseFromMesh 노드.

---

## 3-A. Components 의존성 트리 (필수 묶음 결정 가이드)

> **컴포넌트 작성 시 반드시 베이스 체인 모두 Read** — 부모 클래스의 라이프사이클·virtual 호출 규약을 모르면 자식이 깨진다.

### A.1 베이스 의존성 체인 (4단)

```
UActorComponent  (트랜스폼 무관 — 스탯·인벤토리·로직)
└── USceneComponent  (트랜스폼·부착·Mobility)
    └── UPrimitiveComponent  (콜리전·렌더 SceneProxy·Material·HLOD·Overlap)
        ├── UMeshComponent  (StaticMesh/SkeletalMesh/SkinnedMesh)
        │   └── 자식 9종 (StaticMesh/SkeletalMesh/InstancedStaticMesh/HISM/SplineMesh/PoseableMesh 등)
        └── UShapeComponent  (Box/Sphere/Capsule — Pawn Root 표준)
```

### A.2 컴포넌트 → 필수 sub-skill 체인 매트릭스

| 작성할 컴포넌트 | 필수 베이스 체인 (모두 Read) | 추가 sub-skill |
|---------------|------------------------------|---------------|
| 순수 로직 (Health/Stamina/Inventory) | `ActorComponent` | — |
| 트랜스폼 보유 (Attach/Detach) | `ActorComponent` → `SceneComponent` | — |
| Camera / SpringArm | `ActorComponent` → `SceneComponent` | `CameraComponent` (+ MovementComponents 의 SpringArm) |
| Audio 사운드 | `ActorComponent` → `SceneComponent` | `AudioComponent` |
| ForceFeedback | `ActorComponent` → `SceneComponent` | `AudioComponent` |
| Sky/Atmosphere/Fog | `ActorComponent` → `SceneComponent` | `AtmosphereComponents` (+ LightComponents) |
| Wind | `ActorComponent` → `SceneComponent` | `AtmosphereComponents` |
| Spline (경로) | `ActorComponent` → `SceneComponent` | `SpecialComponents` |
| Timeline (시간 곡선) | `ActorComponent` | `SpecialComponents` |
| StereoLayer (VR) | `ActorComponent` → `SceneComponent` | `SpecialComponents` |
| Light (Point/Spot/Rect/Directional/Sky) | `ActorComponent` → `SceneComponent` | `LightComponents` |
| Decal | `ActorComponent` → `SceneComponent` | `RenderingComponents` |
| TextRender / Billboard / MaterialBillboard | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `RenderingComponents` |
| SceneCapture (2D / Cube) | `ActorComponent` → `SceneComponent` | `RenderingComponents` |
| PostProcess (Actor 단위) | `ActorComponent` → `SceneComponent` | `RenderingComponents` |
| Trigger (Box/Sphere/Capsule) | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `ShapeComponents` (+ 🚨 [`08_OverlapHotspots.md`](./08_OverlapHotspots.md)) |
| Pawn 콜리전 (Capsule = ACharacter Root) | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `ShapeComponents` |
| StaticMesh / SkeletalMesh / ISM / HISM / SplineMesh | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `MeshComponents` |
| ParticleSystem / VectorField / (Niagara) | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `ParticleComponents` |
| 일반 Movement (Projectile/Rotating/InterpTo) | `ActorComponent` → `SceneComponent` (UpdatedComponent 의존) | `MovementComponents` |
| **CharacterMovement** (가장 큼) | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` → `ShapeComponents` (Capsule) → `MeshComponents` (Skeletal) | `MovementComponents` (UpdatedComponent + 복제 예측) |
| Physics Constraint (조인트) | `ActorComponent` → `SceneComponent` (+ 두 PrimitiveComponent) | `PhysicsComponents` |
| Physics Handle (잡기) | `ActorComponent` (+ PrimitiveComponent — 잡힐 대상) | `PhysicsComponents` |
| Physics Spring / Thruster / RadialForce | `ActorComponent` → `SceneComponent` (+ PrimitiveComponent — 영향 대상) | `PhysicsComponents` |
| PhysicalAnimation (Hit Reaction) | `ActorComponent` (+ MeshComponents — SkeletalMesh) | `PhysicsComponents` |
| ClusterUnion (5.x Chaos 파괴) | `ActorComponent` → `SceneComponent` → `PrimitiveComponent` | `PhysicsComponents` (+ GeometryCollection — 별도) |
| InputComponent (Enhanced Input) | `ActorComponent` | `SystemComponents` |
| ChildActorComponent | `ActorComponent` → `SceneComponent` | `SystemComponents` |

### A.3 모든 Components 공통 의무 (예외 없음)

> **모든 Components 작성 시 — 베이스 체인 외에 항상 함께 Read**:

| 인덱스 | 의무 적용 |
|--------|----------|
| 🚨 [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) | **6대 정책 — Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO** (모든 Components sub-skill 본문 시작부 의무 블록) |
| 🚨 [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) | **Tick / TimerManager / 람다 / OnRep_\* / 콜백 첫 줄에 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무** |
| 🚨 [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) | **Tick / 콜백 안 `TActorIterator` / `TObjectIterator` 사용 금지** — 등록 패턴 우선 |
| [`04_OverrideIndex.md`](./04_OverrideIndex.md) | virtual + Super 호출 통합 (BeginPlay/EndPlay/Tick/PostInitProperties 순서) |
| [`05_EditorOnlyIndex.md`](./05_EditorOnlyIndex.md) | 🛠 PostEditChangeProperty / WITH_EDITOR 가드 |
| [`08_OverlapHotspots.md`](./08_OverlapHotspots.md) | UPrimitiveComponent 자손 (Shape/Mesh/Character 등) — 트리거·콜리전 작성 시 |

### A.4 Cross-Skill 통합 시나리오 (자주 함께 쓰는 묶음)

| 통합 시나리오 | 동시 로드 sub-skill |
|--------------|---------------------|
| **3인칭 캐릭터** | ActorComponent + SceneComponent + PrimitiveComponent + ShapeComponents (Capsule Root) + MeshComponents (Skeletal) + MovementComponents (CharacterMovement + SpringArm) + CameraComponent |
| **AI NPC (다수)** | 위 캐릭터 + Significance + (선택) AnimationBudgetAllocator |
| **무기 액터** | ActorComponent + SceneComponent + PrimitiveComponent + MeshComponents + ParticleComponents (총구 화염) + AudioComponent (발사음) + RenderingComponents (탄피·발사 흔적 Decal) + PhysicsComponents (RadialForce 폭발) |
| **차량** | 위 무기와 유사 + MovementComponents (Movement 자식) + PhysicsComponents (Spring 4륜) + CameraComponent (운전 카메라) |
| **건물 / 구조물** | ActorComponent + SceneComponent + PrimitiveComponent + MeshComponents + LightComponents (Static Lightmap) + RenderingComponents (Decal — 더러움) |
| **트리거 영역** | ActorComponent + SceneComponent + PrimitiveComponent + ShapeComponents (+ 🚨 OverlapHotspots) |
| **야외 환경** | AtmosphereComponents (5종 페어) + LightComponents (DirectionalLight + SkyLight) + ParticleComponents (날씨 입자) |
| **VR 게임** | 위 캐릭터 + SpecialComponents (StereoLayer HMD 메뉴) + SystemComponents (Enhanced Input — VR Controllers) |

---

## 4. 카테고리별 기본 묶음

시나리오 식별이 안 될 때의 fallback:

| 카테고리 | 기본 sub-skill 묶음 |
|----------|---------------------|
| **[Components]** | 🚨 [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 정책 의무) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) + [`Components/SKILL.md`](../skills/Components/SKILL.md) (메인 인덱스) + 베이스 체인 (`ActorComponent` → `SceneComponent` → `PrimitiveComponent` 필요한 만큼) + `CoreUObject/UObject` + `CoreUObject/Reflection` + `CoreUObject/GC` + `CoreUObject/ObjectHandles`. **시나리오별 추가 sub-skill 은 §3-A.2 매트릭스** 참조 |
| **[GameFramework]** | 🚨 [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 정책) + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) + [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) + [`GameFramework/SKILL.md`](../skills/GameFramework/SKILL.md) (메인 인덱스 + 라이프사이클 11단계) + 베이스 체인 (Actor → 자식) + `CoreUObject/UObject` + `CoreUObject/Reflection` + `CoreUObject/GC` + `CoreUObject/ObjectHandles`. **시나리오별 추가 sub-skill 은 §3.42-§3.47 + 의존성 트리** (다음 시점 §3-AB 신설 예정) |
| **[Slate]** 게임 UI (UMG) | `UMG/UWidget` + `UMG/UUserWidget` + `SlateCore/SWidget` + `SlateCore/Layout` + `SlateCore/Drawing` (+ `06_InvalidationHotspots.md`) |
| **[Slate]** 게임 UI (저수준 SWidget) | `SlateCore/SWidget` + `SlateCore/Layout` + `SlateCore/Drawing` + `SlateCore/Types` |
| **[Slate]** 인하우스 툴 🛠 | `Slate/EditorApplication` + `Slate/Docking` + `Slate/Menu` + `Slate/Commands` (+ `05_EditorOnlyIndex.md`) |
| **[Render]** | `CoreUObject/UObject` + `CoreUObject/ObjectHandles` (Renderer 본체 sub-skill 추가 전까지) |

---

## 5. 사전 로드 명령 패턴 (Claude 작업 시작 시)

내부 처리 예시 (사용자에게 노출 X):

```
[입력] "[Slate] 새 인하우스 툴 패널 추가"
↓ 시나리오 = 3.16 인하우스 툴 시작
↓ Read("skills/Slate/SKILL.md")              ← 메인 (분리 원칙 §8 포함)
↓ Read("skills/Slate/references/EditorApplication.md")
↓ Read("skills/Slate/references/Docking.md")
↓ Read("skills/Slate/references/Menu.md")
↓ Read("skills/Slate/references/Commands.md")
↓ 노드 그래프도 추가하면 GraphEditor 추가 로드
↓ 코드 작성 시작 — 4단 분리 (Build.cs / Type=Editor / WITH_EDITOR / 모듈 분리) 적용
```

여러 sub-skill을 한 번에 로드해도 메인 SKILL.md (`skills/<Module>/SKILL.md`) 부터 읽는 것을 권장 — 인덱스 표·작성 규칙·에디터 표기 규칙·**런타임/에디터 분리 원칙(§8)** 을 먼저 흡수.

---

## 6. 빠른 검색 키워드 → sub-skill

### 6.1 CoreUObject

- *생성자 / `PostInitProperties` / `PostLoad` / `BeginDestroy`* → `UObject`
- *`UCLASS` / `UPROPERTY` / `UFUNCTION` / 메타데이터 / `UObjectIterator`* → `Reflection`
- *`FProperty` / `FObjectProperty` / `CastField` / `TFieldIterator`* → `Property`
- *`UPackage` / `LoadPackage` / `SavePackage` / `FPackagePath`* → `Package`
- *`UInterface` / `IInterface` / `TScriptInterface` / `Execute_*`* → `Interface`
- *`CollectGarbage` / `MarkAsGarbage` / `FGCObject` / `FReferenceCollector`* → `GC`
- *`Serialize(FArchive&)` / `BulkData` / `LoadPackageAsync` / `PreSave`* → `Serialization`
- *`DOREPLIFETIME` / `RepNotify` / `Server`/`Client`/`NetMulticast` UFUNCTION* → `Network`
- *`PostEditChangeProperty` / `Modify` / `PostEditUndo` / `IsDataValid` / `GetAssetRegistryTags`* → `Editor` 🛠
- *`NeedsLoadForServer` / `IsEditorOnly` / `BeginCacheForCookedPlatformData` / `UObjectRedirector`* → `Cooking` 🛠
- *`FInstancedStruct` / `FSharedStruct` / `FStructView` / `UPropertyBag` / `UUserDefinedStruct`* → `StructUtils`
- *`TObjectPtr` / `TWeakObjectPtr` / `TSoftObjectPtr` / `FSoftObjectPath` / `FPrimaryAssetId` / `FObjectKey`* → `ObjectHandles`
- *`UProperty` / `UnrealTypePrivate.h` / `UObjectProperty` 옛 캐스트* → `DeprecatedUProperty`

### 6.2 SlateCore

- *`SWidget` / `SCompoundWidget` / `SLATE_BEGIN_ARGS` / `Construct` / `TSlateAttribute`* → `SWidget`
- *`FGeometry` / `FArrangedChildren` / `EVisibility` / `FMargin` / `TPanelChildren`* → `Layout`
- *`FSlateDrawElement` / `OnPaint` / `LayerId` / `DrawCall` / `SInvalidationPanel` / `EInvalidateWidgetReason`* → `Drawing`
- *`FSlateBrush` / `FSlateColor` / `FSlateStyleSet` / `FAppStyle` / `FCoreStyle`* → `Styling`
- *`FReply` / `OnMouseButtonDown` / `FPointerEvent` / `FKeyEvent` / `FHittestGrid` / Drag-Drop* → `Input`
- *`FSlateApplication`(베이스) / `FSlateUser` / `SWindow` / `FSlateThrottleManager`* → `Application`
- *`FCurveSequence` / `FCurveHandle` / `FSlateSprings` / `RegisterActiveTimer`* → `Animation`
- *`FSlateFontInfo` / `LOCTEXT` / `FSlateFontMeasure` / Composite Font* → `Text`
- *`TAttribute` / `EHorizontalAlignment` / `FOptionalSize` / `FPaintArgs` / `ISlateMetaData`* → `Types`
- *`FSlateTrace` / `FSlateDebugging` / `Widget Reflector` / `Slate.DrawElementsStats`* → `Trace` 🛠

### 6.3 UMG

- *`UWidget` / `RebuildWidget` / `SynchronizeProperties` / `Native*` 사슬* → `UMG/UWidget`
- *`EWidgetTickFrequency::Auto` / `bIsVolatile` / `ForceVolatile` / `InvalidateLayoutAndVolatility`* → `UMG/UWidget` §5 + `06_InvalidationHotspots.md`
- *`UUserWidget` / `BindWidget` / `BindWidgetOptional` / `NativeOnInitialized` / `NativeConstruct` / `NativePreConstruct` / `NativeOnPaint`* → `UMG/UUserWidget`
- *`URichTextBlock` / `STextBlock` 다중 갱신 / `SEditableText` / `UListView` / `UProgressBar` / `UThrobber` 인밸리데이션* → `06_InvalidationHotspots.md`
- *override 결정 / Super 호출 의무 / RebuildWidget 5단계 사이클* → `04_OverrideIndex.md`
- *🛠 / `WITH_EDITOR` / `WITH_EDITORONLY_DATA` / 모듈 분리 / `Type=Editor`* → `05_EditorOnlyIndex.md`

### 6.4 Slate (인하우스 툴 묶음)

- *`FSlateApplication::Get()` / `IInputProcessor` / `Tick`/`PumpMessages` / `InitializeCoreStyle` / standalone 진입* → `EditorApplication` 🛠
- *`SDockTab` / `FTabManager` / `FGlobalTabmanager` / `FLayoutSaveRestore` / 탭 등록* → `Docking` 🛠
- *`FMenuBuilder` / `FToolBarBuilder` / `FExtender` / `FMultiBoxExtender` / 메인 메뉴* → `Menu` 🛠
- *`TCommands<T>` / `FUICommandInfo` / `FUICommandList` / `FInputChord` / `UI_COMMAND` / 단축키* → `Commands` 🛠
- *`UEdGraph` / `UEdGraphNode` / `UEdGraphPin` / `UEdGraphSchema` / `SGraphPanel` / 노드 그래프* → `GraphEditor` 🛠
- ***런타임/에디터 분리 / Build.cs Type=Editor / WITH_EDITOR / 모듈 분리*** → `Slate/SKILL.md §8`

---

## 7. sub-skill 의존성 그래프 / 함께 로드 패턴

> sub-skill 간 자주 함께 참조되는 묶음 — 한 묶음을 읽을 때 어떤 sub-skill 이 같이 등장할 가능성이 큰지.

### 7.1 CoreUObject 내부 의존 (코어 → 응용)

```
                ┌──────────────────┐
                │     UObject      │  ← 모든 것의 베이스
                └────────┬─────────┘
                         │
        ┌────────────────┼────────────────┬─────────────┐
        │                │                │             │
   ┌────▼───┐       ┌────▼─────┐    ┌─────▼─────┐  ┌────▼─────────┐
   │   GC   │       │Reflection │    │ ObjectHand│  │Serialization │
   └────┬───┘       └────┬──────┘    │   les     │  └──────┬───────┘
        │                │            └─────┬─────┘         │
        │                │                  │               │
        └─────┐    ┌─────┘                  │               │
              ▼    ▼                        │               │
            ┌──────────┐               ┌────▼─────┐    ┌────▼─────┐
            │ Property │               │ Package  │◀───│Network   │
            └────┬─────┘               └──────────┘    └──────────┘
                 │
        ┌────────┼────────┐
        │                 │
   ┌────▼─────┐      ┌────▼──────────┐
   │ Editor 🛠│      │ Cooking 🛠    │
   └──────────┘      └────────────────┘

  병렬 (관계 약함):  Interface · StructUtils · DeprecatedUProperty
```

**자주 함께 로드되는 묶음**:

- 새 UCLASS 작성 → `UObject` + `Reflection` + `GC` + `ObjectHandles` (4종 세트)
- 직렬화 + 쿠킹 → `Serialization` + `Package` + `Cooking`
- 에디터 콜백 → `Editor` + `Property` + `UObject`

### 7.2 SlateCore 내부 의존

```
       ┌──────────┐
       │  Types   │  ← TAttribute / Enum / Struct (모두 사용)
       └────┬─────┘
            │
            │
       ┌────▼─────┐         ┌──────────┐
       │ SWidget  │◀────────│ Animation│
       └────┬─────┘         └──────────┘
            │
   ┌────────┼─────────┬───────────┐
   │        │         │           │
┌──▼──┐  ┌──▼───┐  ┌──▼────┐  ┌───▼──────┐
│Layout│  │Input │  │Drawing│  │ Styling  │
└──────┘  └──────┘  └───┬───┘  └────┬─────┘
                        │           │
                        │           │
                   ┌────▼──────┐    │
                   │   Text    │◀───┘
                   └───────────┘

       Application (전역 — 모든 위젯이 의존)
       Trace      🛠 (디버그 — 옵션)
```

**자주 함께 로드되는 묶음**:

- 새 SWidget → `SWidget` + `Layout` + `Drawing` + `Types` (4종 세트)
- 인터랙션 위젯 → 위 4종 + `Input`
- 스타일이 있는 위젯 → 위 4종 + `Styling` + (`Text` 폰트 시)
- 인밸리데이션 디버깅 → `Drawing` + `SWidget` + `Trace`

### 7.3 Slate 인하우스 툴 묶음 의존

```
                    ┌────────────────────┐
                    │ EditorApplication  │  ← 진입점 (FSlateApplication)
                    └────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐        ┌─────▼─────┐         ┌────▼──────┐
   │  Docking │        │   Menu    │◀────────│  Commands │
   └──────────┘        └───────────┘         └───────────┘
        │                    │                    │
        │                    │                    │
        └────────────┐       │       ┌────────────┘
                     │       │       │
                     ▼       ▼       ▼
                  ┌──────────────────────┐
                  │     GraphEditor      │ ← 모두 결합 (인하우스 노드 에디터)
                  │  + EdGraph (Engine)  │
                  └──────────────────────┘

   (보류) Notifications 🛠 — 토스트/에러 표시 (모든 묶음에서 사용 가능)
```

**자주 함께 로드되는 묶음**:

- 일반 인하우스 툴 → `EditorApplication` + `Docking` + `Menu` + `Commands` (4종 핵심)
- 노드 에디터 → 위 4종 + `GraphEditor` (5종)
- 메뉴/툴바만 추가 → `Menu` + `Commands` (2종)
- 단축키만 추가 → `Commands` + `SlateCore/Input`

### 7.4 UMG 의존 (CoreUObject + SlateCore 연결고리)

```
        ┌──────────────────────────┐
        │   UMG/UWidget (베이스)    │   bIsVolatile / RebuildWidget / Native* 사슬
        │   UMG/UUserWidget (BP)    │   BindWidget / NativeConstruct / NativeOnPaint
        └─────────┬────────────────┘
                  │ TakeWidget()
                  ▼
        ┌──────────────────────────┐
        │   SlateCore/SWidget      │   ← UMG가 RebuildWidget 시 생성
        │   + Layout/Drawing/Input │
        └─────────┬────────────────┘
                  │
                  ▼
        ┌──────────────────────────┐
        │  CoreUObject/UObject     │   ← UMG는 UObject임 (GC/Replication)
        │  + ObjectHandles         │
        └──────────────────────────┘

  교차 인덱스 — 04/05/06 모두 UMG 작업에서 자주 참조
```

**자주 함께 로드되는 묶음**:

- 신규 UMG 위젯 → `UMG/UWidget` + `UMG/UUserWidget` + `SlateCore/SWidget` + `SlateCore/Layout` + `SlateCore/Drawing`
- UMG 인밸리데이션 디버깅 → 위 5종 + `06_InvalidationHotspots.md` + `SlateCore/Trace`
- UMG override 결정 → 위 5종 + `04_OverrideIndex.md`

### 7.5 모듈 간 cross-reference (자주 등장)

```
인하우스 툴 작성 시 ↓ 자주 함께 참조 ↑
┌────────────────────────────────────────────────┐
│  Slate/EditorApplication/Docking/Menu/Commands │
│            ↓                                   │
│  SlateCore/Application (FSlateApplicationBase) │
│  SlateCore/SWidget     (위젯 베이스)           │
│  SlateCore/Input       (FReply, FKeyEvent)     │
│  SlateCore/Styling     (FAppStyle)             │
│            ↓                                   │
│  CoreUObject/UObject   (UObject 라이프사이클)  │
│  CoreUObject/Editor 🛠 (PostEditChange 콜백)   │
│  CoreUObject/ObjectHandles (TObjectPtr)        │
└────────────────────────────────────────────────┘

노드 그래프 에디터 (GraphEditor 🛠) 추가 의존:
  + CoreUObject/Reflection   (UCLASS 등록)
  + CoreUObject/Serialization (그래프 호환성)
  + CoreUObject/Cooking       (Editor-only 가드)
```

### 7.6 부분 cross-reference 표

| 출발 sub-skill | 자주 함께 보는 sub-skill |
|----------------|--------------------------|
| `CoreUObject/UObject` | `Reflection` + `GC` + `ObjectHandles` (UCLASS 작성 4종) |
| `CoreUObject/Reflection` | `UObject` + `Property` + (`StructUtils` 동적 USTRUCT 시) |
| `CoreUObject/GC` | `UObject` + `ObjectHandles` |
| `CoreUObject/Serialization` | `UObject` + `Property` + `Package` (+ `Cooking` 에디터) |
| `CoreUObject/Editor` 🛠 | `UObject` + `Property` + (`Reflection` 메타) |
| `CoreUObject/Cooking` 🛠 | `Serialization` + `Package` + `Reflection` |
| `SlateCore/SWidget` | `Layout` + `Drawing` + `Types` + (`Input` 인터랙션) |
| `SlateCore/Drawing` | `SWidget` + `Layout` + `Styling` + `Trace` |
| `SlateCore/Application` | `SWidget` + `Input` + (`ApplicationCore` 미작성) |
| `Slate/EditorApplication` 🛠 | `Docking` + `Menu` + `Commands` + `SlateCore/Application` |
| `Slate/Docking` 🛠 | `EditorApplication` + `Menu` + `Commands` |
| `Slate/Menu` 🛠 | `Commands` + (`Docking` 메인 메뉴) |
| `Slate/Commands` 🛠 | `Menu` + `SlateCore/Input` |
| `Slate/GraphEditor` 🛠 | 모든 인하우스 툴 + `CoreUObject/UObject`/`Editor`/`Reflection` |
| `UMG/UWidget` | `UMG/UUserWidget` + `SlateCore/SWidget` + `06_InvalidationHotspots.md` + `04_OverrideIndex.md` |
| `UMG/UUserWidget` | `UMG/UWidget` + `SlateCore/SWidget` + `04_OverrideIndex.md` (Native* 사슬) |

---

## 8. 향후 확장 (현재 미작성 모듈)

다음 모듈들이 같은 sub-skill 분할 패턴으로 추가될 때 본 하네스 표도 갱신해야 한다:

| 모듈 | Tier | 예상 sub-skill | 시나리오 영향 |
|------|------|----------------|---------------|
| `Slate/Notifications` 🛠 | 3 (보류) | FSlateNotificationManager / SNotificationList | 인하우스 툴 토스트·에러 표시 |
| `Slate/Application` (게임 공통) | 3 | FSlateApplication 게임 측면 | 게임 UI 진입 |
| `Slate/CommonWidgets` | 3 | SButton/SCheckBox/STextBlock/SImage 등 | 게임 UI 작성 |
| `Slate/LayoutWidgets` | 3 | SBoxPanel/SOverlay/SGridPanel 등 | 게임 UI 레이아웃 |
| `Slate/ListsTrees` | 3 | SListView/STreeView 등 | 게임/툴 리스트 |
| `Slate/TextInput` | 3 | SEditableText/SRichTextBlock 등 | 텍스트 입력 |
| `Slate/MiscWidgets` | 3 | SSlider/SColor*/SViewport 등 | 보조 위젯 |
| `Slate/Animation` | 3 | FAnimatedAttribute (5.x) | 어트리뷰트 보간 |
| `Core` | 1 | Containers/String/Memory/Threading/Logging | [Components/Slate/Render] 모두 기본 묶음 |
| `Engine` | 1 | AActor/UWorld/UGameInstance/Subsystem/Component/Tick | [Components] 핵심 |
| `UMG/StandardWidgets` | 3 | Button/CheckBox/Image/TextBlock/RichTextBlock 등 | UMG 게임 UI |
| `UMG/PanelWidgets` | 3 | VerticalBox/HorizontalBox/CanvasPanel/Overlay/GridPanel | UMG 레이아웃 |
| `UMG/ListWidgets` | 3 | UListView/UTreeView/UTileView | UMG 리스트 |
| `UMG/Slot` | 3 | UPanelSlot 사슬 | UMG 슬롯 |
| `UMG/ViewModel` | 3 | MVVM 통합 | UMG 데이터 바인딩 |
| `ApplicationCore` | 3 | GenericApplication/GenericWindow/MessageHandler/Cursor/InputDevice | [Slate] OS 통합 |
| `InputCore`/`InputDevice` | 3 | FKey/EKeys/IInputDevice | [Components/Slate] 입력 식별 |
| `RHI`/`RenderCore`/`Renderer` | 2 | RDG·Shader·SceneViewExtension·MaterialShader·PostProcess | [Render] 핵심 |
| `AnimGraphRuntime`/`AnimationCore` | 4 | AnimGraph·BoneIndex·IK·Cloth | [Components] 캐릭터/애니 |
| `AudioMixer` | 5 | Submix·SourceVoice·DSP | [Components] 사운드 |
| `Networking`/`Sockets` | 5 | Socket·Replication 디테일 | [Components] 멀티플레이 |
| `LevelSequence`/`MovieScene` | 5 | UWidgetAnimation 시퀀서 통합 | [Slate]/[Cinematic] 애니 |
| `skills/GraphEditor/` (Editor 모듈, 별도) | (예외) | KismetNodes/KismetPins/MaterialNodes/MaterialPins/DragAndDrop 깊이 | 인하우스 노드 에디터 |
| `skills/UnrealEd/` (Editor 모듈, 별도) | (예외) | FAssetEditorToolkit·FAssetTypeActions·UAssetDefinition | 인하우스 에셋 에디터 |

---

## 8.5 sub-skill 의존성 표 — Editor/Developer 모듈 9개 추가 후 갱신

> 본 표는 §7 의 의존성 그래프를 보완. 각 sub-skill이 **자주 함께 참조해야 하는 다른 sub-skill** 들을 한곳에 정리. 시나리오에 따라 조합.

### 8.5.1 인하우스 에셋 에디터 만들 때 (가장 자주)

```
[필수 5종 세트]
   UnrealEd/AssetEditorToolkit  ← FAssetEditorToolkit 자손 (메인 베이스)
              ↓ 의존
   EditorFramework               ← IToolkit / IToolkitHost / FToolkitManager
   AssetTools                    ← IAssetTypeActions (더블클릭 라우팅)
   PropertyEditor                ← IDetailCustomization (디테일 패널)
   ToolMenus                     ← UToolMenus (툴바·메뉴)
              ↓
   Slate/Docking + Slate/Menu + Slate/Commands + Slate/EditorApplication
              ↓
   SlateCore/SWidget + Layout + Drawing + Input + Application
              ↓
   CoreUObject/UObject + Editor + Reflection + ObjectHandles

[필요 시 추가]
   UnrealEd/Subsystems            ← 외부에서 OpenEditorForAsset
   UnrealEd/Kismet2               ← BP 통합
   UnrealEd/Elements              ← 5.x Element 선택
   AssetRegistry                  ← 에셋 메타 검색
   EditorWidgets                  ← 공통 위젯 (검색·드롭·콤보)
   MainFrame                      ← OnMainFrameCreationFinished 후 메뉴 등록
   EditorSubsystem                ← 사용자 정의 UEditorSubsystem 자손
```

### 8.5.2 인하우스 노드 그래프 에디터

```
[필수]
   Slate/GraphEditor              ← UEdGraph + GraphEditor 위젯
   UnrealEd/AssetEditorToolkit    ← 인하우스 에디터 베이스
   UnrealEd/Kismet2               ← 그래프 컴파일 (BP 라면)
   ToolMenus                      ← 노드 컨텍스트 메뉴
   PropertyEditor                 ← 노드 디테일 패널
              ↓
   (위 8.5.1 의 표준 5종 세트가 모두 의존)
```

### 8.5.3 레벨 에디터 도구 (메인 에디터 안 도구)

```
[필수]
   LevelEditor                    ← FLevelEditorModule / ILevelEditor / SLevelViewport
   ToolMenus                      ← LevelEditor.LevelEditorToolBar / MainMenu 확장
   MainFrame                      ← OnMainFrameCreationFinished 콜백
              ↓
   UnrealEd/Subsystems            ← UEditorActorSubsystem (액터 일괄 조작)
   UnrealEd/Elements              ← 5.x 선택 (LevelEditor.GetElementSelectionSet)
   UnrealEd/Layers                ← 레이어 시스템
   EditorFramework                ← UEdMode (커스텀 EdMode 시)
              ↓
   Slate/Commands + ToolMenus + Slate/Docking
```

### 8.5.4 Asset 임포트 / 자동화

```
[필수]
   UnrealEd/Factories             ← UFactory / UActorFactory / FReimportHandler
   AssetTools                     ← IAssetTypeActions
   AssetRegistry                  ← 임포트 후 메타 갱신 (자동)
   UnrealEd/Subsystems            ← UImportSubsystem
              ↓
   CoreUObject/Package + Serialization
   CoreUObject/Cooking            ← 쿠킹 시점 처리
```

### 8.5.5 디테일 패널 커스터마이징

```
[필수]
   PropertyEditor                 ← IDetailCustomization / IPropertyTypeCustomization
   CoreUObject/Editor             ← PostEditChangeProperty
   CoreUObject/Property           ← FProperty / FPropertyHandle
   CoreUObject/Reflection         ← UPROPERTY 메타키
              ↓
   ToolMenus                      ← DetailRowMenuContext (5.x)
   EditorWidgets                  ← STextPropertyEditableTextBox 자동 사용
```

### 8.5.6 에디터 서브시스템 작성

```
[필수]
   EditorSubsystem                ← UEditorSubsystem 베이스 (Build.cs 의존)
              ↓
   CoreUObject/UObject + Reflection + ObjectHandles + GC
              ↓ (시나리오에 따라)
   UnrealEd/Subsystems            ← 빌트인 12개 패턴 참고
   AssetRegistry                  ← Asset 메타 옵서버
```

### 8.5.7 빠른 sub-skill ↔ sub-skill 매핑 (대표)

| 출발 sub-skill | 자주 함께 보는 sub-skill |
|----------------|--------------------------|
| `UnrealEd/AssetEditorToolkit` | `EditorFramework`(IToolkit) + `Slate/Docking` + `Slate/Menu` + `Slate/Commands` + `PropertyEditor` + `ToolMenus` |
| `UnrealEd/Subsystems` | `EditorSubsystem`(베이스) + `AssetRegistry`(메타) + `UnrealEd/Elements`(선택) |
| `UnrealEd/Kismet2` | `Slate/GraphEditor`(EdGraph) + `CoreUObject/Reflection` + `CoreUObject/Serialization` |
| `UnrealEd/Factories` | `AssetTools`(IAssetTypeActions) + `AssetRegistry` + `UnrealEd/Subsystems`(UImportSubsystem) + `CoreUObject/Package` |
| `UnrealEd/Elements` | `UnrealEd/Subsystems`(UEditorActorSubsystem) + `LevelEditor`(GetElementSelectionSet) |
| `UnrealEd/Layers` | `UnrealEd/Subsystems` + `LevelEditor`(아웃라이너) |
| `UnrealEd/MaterialEditor` | `Slate/GraphEditor` + `CoreUObject/Reflection` |
| `ToolMenus` | `Slate/Commands`(TCommands<T>) + `Slate/Menu`(레거시 비교) + `MainFrame`(표준 메뉴 이름) + `LevelEditor`(LevelEditor.* 메뉴) |
| `EditorFramework` | `UnrealEd/AssetEditorToolkit`(IToolkit 구현) + `Slate/Docking`(IToolkitHost) + `EditorSubsystem`(UPlacementSubsystem) |
| `EditorSubsystem` | `UnrealEd/Subsystems`(12개 자손 패턴) + `CoreUObject/UObject` |
| `MainFrame` | `ToolMenus`(MainFrame.MainMenu.*) + `Slate/Commands`(GetMainFrameCommandBindings) + `LevelEditor` |
| `LevelEditor` | `MainFrame`(호스팅) + `ToolMenus`(LevelEditor.*) + `UnrealEd/Subsystems` + `UnrealEd/Elements` + `EditorFramework`(IToolkitHost) |
| `EditorWidgets` | `AssetRegistry`(SAssetSearchBox 자동완성) + `PropertyEditor`(STextPropertyEditableTextBox) + `SlateCore/Input` |
| `AssetTools` | `UnrealEd/AssetEditorToolkit`(OpenAssetEditor) + `UnrealEd/Subsystems`(UAssetEditorSubsystem) + `UnrealEd/Factories` + `ToolMenus`(GetActions FToolMenuSection) |
| `AssetRegistry` | `AssetTools`(통합) + `CoreUObject/ObjectHandles`(FSoftObjectPath) + `CoreUObject/Cooking`(쿠킹 메타) + `UnrealEd/Factories`(임포트 후 갱신) |
| `PropertyEditor` | `CoreUObject/Editor`(PostEditChange) + `CoreUObject/Property` + `CoreUObject/Reflection`(메타키) + `ToolMenus`(DetailRowMenu) + `EditorWidgets` |

### 8.5.8 메인 에디터 통합 의존 (5종 세트 + 보조)

```
                  ┌─────────────────────────────┐
                  │   MainFrame                 │  메인 윈도우
                  │   (IMainFrameModule)        │
                  └──────────┬──────────────────┘
                             │ 호스트
                  ┌──────────▼──────────────────┐
                  │   LevelEditor               │  ← 가장 큰 도구
                  │   (FLevelEditorModule)      │
                  └──────────┬──────────────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────────┐
│ ToolMenus    │    │ UnrealEd/    │      │ EditorFramework  │
│              │    │ Subsystems   │      │ (UEdMode 등)     │
└──────────────┘    └──────────────┘      └──────────────────┘
                             │
                  ┌──────────▼──────────────────┐
                  │  EditorSubsystem (베이스)   │
                  └──────────┬──────────────────┘
                             ▼
                  ┌─────────────────────────────┐
                  │  CoreUObject + Slate/SlateCore │
                  └─────────────────────────────┘

별도 도구 (인하우스 에셋 에디터):
   AssetTools (라우팅) → UnrealEd/AssetEditorToolkit (인스턴스) → 위 인프라 사용
   PropertyEditor (디테일) → 인스턴스 안에서 사용
   AssetRegistry → 데이터 베이스
   EditorWidgets → 공통 위젯
```

---

## 9. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-02 | 최초 작성. CoreUObject Tier 1 13개 sub-skill 완성에 맞춰 하네스 표 12종 정의. |
| 2026-05-03 | SlateCore 10개 + Slate 5개(인하우스 툴 묶음, Notifications 제외) 추가. 시나리오 23종으로 확장. **§7 sub-skill 의존성 그래프** 신설. 빠른 검색 키워드 표를 모듈별로 분리. 향후 확장 표에 LevelSequence/MovieScene·GraphEditor 별도 모듈·UnrealEd 추가. |
| 2026-05-04 | UMG 진입(메인 + UWidget·UUserWidget 2개 sub-skill) 반영. **교차 참조 인덱스 §0.1** 신설 → `04_OverrideIndex.md`/`05_EditorOnlyIndex.md`/`06_InvalidationHotspots.md` 연결. §2.4 UMG 한 줄 요약·§3.23/§3.24 시나리오·§4 게임 UI(UMG) 기본 묶음·§6.3 UMG 키워드·**§7.4 UMG 의존 그래프 + §7.6 UMG 행** 추가. |
| 2026-05-04 (오후) | **UMG 5개 sub-skill 추가**(StandardWidgets/PanelWidgets/ListWidgets/Slot/ViewModel) → §2.4 UMG 표 7개로 확장. **`UWidget/SKILL.md §4.4` + `UUserWidget/SKILL.md §4.1.1` Super 호출 규약** + `04_OverrideIndex.md §6 Super 호출 통합 표 + §6.7 구획별 초기화 책임 매트릭스 + §6.8 표준 템플릿` 추가. UserWidget.cpp L1824~L1908 소스 검증. |
| 2026-05-04 (저녁) | **`07_ProfilingScopeRule.md` 신설** — Tick/TimerManager/FTSTicker/람다/바인딩 UFunction/OnRep\_\* 모두에 `TRACE_CPUPROFILER_EVENT_SCOPE` · `SCOPED_NAMED_EVENT` · `QUICK_SCOPE_CYCLE_COUNTER` 부착 의무. SlateCore/UMG 본체 grep 검증. CLAUDE.md §8.1 / §8.3 체크리스트에도 통합. **모든 sub-skill 공통 적용**. |
| 2026-05-04 (밤) | **위키 범위 확장** — Engine/Source/Runtime + Editor + Developer (Programs 제외). `catalog/EditorDevIndex.md` 신설. **`skills/UnrealEd/` 메인 + 8개 sub-skill** (AssetEditorToolkit/Subsystems/Kismet2/Factories/Elements/Layers/MaterialEditor/Misc). 5개 Editor/Developer 모듈 마운트 (UnrealEd/PropertyEditor/AssetTools/EditorFramework/ToolMenus). **§2.5 UnrealEd** sub-skill 표 추가. |
| 2026-05-04 (심야) | **`ToolMenus` / `EditorFramework` / `AssetTools` / `PropertyEditor` 4개 모듈 sub-skill 작성** — 모두 `skills/<Module>/SKILL.md` 단일 파일. 인하우스 에셋 에디터 골격 (`UnrealEd/AssetEditorToolkit` + `EditorFramework/IToolkit` + `AssetTools/IAssetTypeActions` + `PropertyEditor/IDetailCustomization` + `ToolMenus/UToolMenus`) 5종 세트 완성. |
| 2026-05-05 (새벽) | **2차 Editor/Developer 5개 모듈 sub-skill 작성** — `EditorSubsystem` / `MainFrame` / `EditorWidgets` / `AssetRegistry` / `LevelEditor`. **§2.6 단일 SKILL 모듈 9개 표** 신설. **§8.5 sub-skill 의존성 표 (인하우스 에셋 에디터 / 노드 그래프 / 레벨 에디터 도구 / Asset 임포트 / 디테일 패널 / 에디터 서브시스템 6개 시나리오 + ↔ 매핑 + 통합 의존 그래프)** 신설 — 사용자 요청 반영. |
| 2026-05-05 (낮) | **Slate 게임/에디터 공통 7개 sub-skill 작성** — `Application`(SlateApplication 게임 측면) / `CommonWidgets`(SButton·SCheckBox·SSlider·SSpinBox·SInputKeySelector 등) / `LayoutWidgets`(SBox·SBorder·SOverlay·SScrollBox·SSplitter·SGridPanel·SConstraintCanvas 등) / `ListsTrees`(SListView/STreeView/STileView 가상 풀링) / `TextInput`(SEditableText·SRichTextBlock 등) / `MiscWidgets`(Notifications·Colors·Throbber·SViewport) / `Animation`(FAnimatedAttribute 5.x 어트리뷰트 보간). **§2.3 Slate** 표 5→12 확장. Slate 모듈 sub-skill 분할 완료. |
| 2026-05-05 (오후) | **UMG/UWidget §6 Focus/Navigation 시스템 신설** — UWidgetNavigation·EUINavigationRule(6종)·EUINavigation(6방향) + SetNavigationRuleBase/Explicit/Custom/CustomBoundary 4종 (5.x 권장, deprecated SetNavigationRule 분리) + Native\* 7개 포커스/내비 콜백 cross-reference + DesiredFocusWidget + NavigationConfig + 함정 10종. 게임패드/콘솔 환경 표준. §2.4 UWidget 한 줄 요약 갱신. |
| 2026-05-05 (저녁) | **Components 카테고리 진입** — Engine 모듈 마운트. **`skills/Components/` 메인 + 베이스 3 sub-skill** 작성 (ActorComponent / SceneComponent / PrimitiveComponent). Engine/Classes/Components 72 + GameFramework 7 + Camera 2 + Particles 1 + PhysicsEngine 6 = 약 90개 컴포넌트 카탈로그. **15개 sub-skill 분할안** 확정 (베이스 3 + 시각/메시 5 + 콜리전/물리 2 + 게임플레이/시스템 3 + 오디오/특수 2). 게임 시스템 근간 — 깊게 가는 스킬 묶음. |
| 2026-05-05 (밤) | **`Components/MeshComponents` 작성** (StaticMesh/Skeletal/Skinned/InstancedStatic/HISM/SplineMesh/Poseable/InstancedSkinned/Model 9개) + **§7 SkeletalMesh Tick 최적화 깊이** (EVisibilityBasedAnimTickOption 5종 + URO + bAlwaysTickPose + 의사결정 트리). **`08_OverlapHotspots.md` 신설** — PrimitiveComponent 자손 Overlap 비용/핫스팟 통합 인덱스 (8단 체크리스트). **`Significance` sub-skill 신설** — USignificanceManager + FOrderedBudget + 거리 기반 LOD + SkeletalMesh 통합 패턴. |
| 2026-05-05 (자정) | **MeshComponents §7 보강** — §7.4 URO 자세히 (FAnimUpdateRateParameters 12 멤버 + EOptimizeMode 2종 + ShiftBucket 4분산 + Update vs Eval 차이) + §7.5 PostProcess AnimBP / AnimGraph LOD Threshold / bRecentlyRendered + **§7.6 AnimationBudgetAllocator Plugin** 통합 (USkeletalMeshComponentBudgeted + FAnimationBudgetAllocatorParameters 14 필드 + SetComponentSignificance + URO vs Allocator 비교) + 함정 14종 확장. **Significance §7 Budget 시스템 통합** — 4가지 Budget 비교표 (FOrderedBudget / AnimationBudgetAllocator / TickInterval / CVar) + 통합 의사결정 트리. |
| 2026-05-06 (새벽) | **`09_GlobalIteratorPolicy.md` 신설** — TActorIterator·TObjectIterator·TObjectRange·TActorRange **사용 금지 정책**. 4종 안티패턴 + 대안 7종 (Subsystem 등록·AssetRegistry·UWorld::Actors·Tag·GameInstance 캐시·Component 배열·Spatial Hash) + 결정 트리 + **최후의 수단 5조건 + 7허용 예외 + 6금지 케이스** + 5단 체크리스트 + sub-skill 적용 매트릭스. EngineUtils.h L318·L569·L621 / UObjectIterator.h L75·L256·L414 검증. |
| 2026-05-05 | **`[GameFramework]` 카테고리 신설** — `skills/GameFramework/` 메인 + 6 sub-skill 분할 (Actor / PawnCharacter / Controller / GameMode / GameInstance / World). **AActor 5,074 lines 라이프사이클 11단계** + Super 호출 규약 통합. **APawn 598 + ACharacter 1,095 깊이** (Jump 6필드+5메소드 / Crouch bIsCrouched 복제 / Landing / OnMovementModeChanged / LaunchCharacter / RootMotion / Movement Base / SmoothCorrection) + **§6 최적화 10종 — Tick 회피·URO·EVisibilityBasedAnimTickOption·Significance·AnimationBudgetAllocator·Network·Mesh LOD·Capsule Channel·PostProcess AnimBP LOD·AI vs Player 매트릭스**. APlayerController 2,377 lines (Input Mode 3종 + Input Stack + SetViewTarget + SeamlessTravel + AcknowledgePawn). AGameModeBase 672 + AGameMode (Match State 5종 + StartMatch/EndMatch + HandleMatchHasStarted) + GameStateBase (PlayerArray + ServerWorldTimeSeconds) + PlayerState (CopyProperties SeamlessTravel). UGameInstance 664 (Subsystem 4종 비교 — Engine/GameInstance/World/LocalPlayer + Online Session). UWorld 4,667 (Tick Group 8종 + Level Streaming 3종 + UWorldSubsystem 등록 패턴 — TActorIterator 회피 표준). §3.42-§3.47 시나리오 6개 + §4 [GameFramework] 카테고리 기본 묶음. CLAUDE.md §0.2 + §8.0 + §11 카테고리 식별 갱신. |
| 2026-05-05 | **`11_AssetLoadingPolicy.md` 신설** — **SpawnActor 히칭 방지 표준 정책** (모든 sub-skill 횡단). **SpawnActor 히칭 4단 원인** (Class CDO 동기 로드 / Subobject CDO / 재귀 어셋 / Material PSO 컴파일) + Editor PIE vs Cooked Build 차이. **Soft vs Hard Reference 6종 비교 표** (TObjectPtr / TSubclassOf / TSoftObjectPtr / TSoftClassPtr / FSoftObjectPath / FPrimaryAssetId) + 결정 트리. **FStreamableManager API** (StreamableManager.h:730 RequestAsyncLoad + StreamableManager.h:760 RequestSyncLoad + FStreamableHandle 8개 메소드 + Pin/Release 생명주기). **UAssetManager Primary Asset + Bundle 시스템** (UPrimaryDataAsset / FPrimaryAssetId / AssetManager.h:308 LoadPrimaryAsset + AssetManager.h:365 ChangeBundleStateForPrimaryAssets + AssetManager.h:492 PreloadPrimaryAssets + meta=(AssetBundles=) + DefaultEngine.ini PrimaryAssetTypesToScan 자동 스캔). **🎯 SpawnActor 히칭 방지 4단 표준 패턴** (PreLoad bLoadRecursive=true → Wait → SpawnActorDeferred → Init+FinishSpawning). **PreLoadAsset 정책 5대** (Constructor 어셋 로드 금지 / BeginPlay LoadObject 금지 / Match Start PreLoad / Bundle 효율 / Handle Pin). **GameFramework/Actor §12 신설** (4단 표준 + 5대 의무 정책 + Soft vs Hard 결정 매트릭스 + 7단 체크리스트). CLAUDE.md §0.2 교차 인덱스 8개로 확장 + §8.1 어셋 로드 정책 8단 + §8.3 체크리스트 어셋 로드 항목. §3.48 시나리오 신설. |
| 2026-05-05 | **`[AssetClasses]` 카테고리 신설** — `skills/AssetClasses/` 메인 + 9 sub-skill (Mesh / Material / Texture / Animation / Audio / Data / VFX / Camera / Physics). **Components 의 페어 카테고리** (Components 호스트 ↔ AssetClasses 자산). **Mesh** UStaticMesh 2,543 + USkeletalMesh 3,248 + USkeleton + UPhysicsAsset (5.x Nanite + Compatible Skeleton + Virtual Bones + Ragdoll). **Material** UMaterial 2,166 + Instance 1,256 + Interface 1,385 (Domain 7종 + BlendMode 7종 + ShadingModel 12종 + MIC vs MID + 5.x PSO Precache + MaterialParameterCollection). **Texture** UTexture 2,228 + Texture2D + Cube + RenderTarget + Volume (CompressionSettings 10종 + TextureGroup 11종 + MipGenSettings 8종 + Streaming + 5.x VirtualTexture/RVT). **Animation** UAnimSequence 1,001 + UAnimMontage 996 + UBlendSpace 966 + UAnimBlueprint + UAnimInstance 1,776 (5.x NativeThreadSafeUpdateAnimation + Curve API + Montage_* + AnimNotify). **Audio** USoundBase 418 + USoundCue 379 + USoundWave 1,822 + SoundClass + Concurrency (5종 ResolutionRule) + Mix + Attenuation + 5.x MetaSounds. **Data** UDataAsset + UPrimaryDataAsset (Bundle 표준) + UDataTable 552 + UCurveTable 342. **VFX** UNiagaraSystem (Plugin) + UParticleSystem (Cascade legacy) + UVectorField. **Camera** UCameraShakeBase + UCameraShakePattern 4종 (PerlinNoise/WaveOscillator/Sequence/Matinee) + UCameraModifier + 5.x UCameraAnimationSequence. **Physics** UPhysicalMaterial + EPhysicalSurface 32종 + UPhysicalMaterialMask + UPhysicsConstraintTemplate 6DoF Profile. CLAUDE.md §0.2 + §8.0 카테고리 식별에 [AssetClasses] 추가. |
| 2026-05-05 | **`12_AssetOptimizationPolicy.md` 신설** — **어셋 최적화 5대 영역 통합 정책** (9번째 횡단 인덱스). **§1 SkeletalMesh Bone LOD** (`USkeletalMeshLODSettings` + `FBoneFilter` + `BonesToRemove` + `BonesToPrioritize` + `WeightOfPrioritization` + `LODHysteresis` + 5.x `SkinCacheUsage` + LOD 5단계 표준 매트릭스 — 본 비율 100/70/50/30/15%). **§2 StaticMesh LOD** (ScreenSize 표준 1.0/0.5/0.25/0.1/0.05 + 5.x Nanite vs Traditional 결정 매트릭스 + AutoComputeLODScreenSize + MinLOD 플랫폼별 + 폴리곤 감축 매트릭스). **§3 Actor Merging** (4종 비교 — HISM / Mesh Merge / HLOD / 5.x WorldPartition HLOD + 결정 트리 + FMeshMergingSettings + MergeComponentsToStaticMesh API). **§4 Audio Culling** (Attenuation MaxDistance + Concurrency MaxCount 5종 ResolutionRule + SoundMix Volume Mute + Significance 통합 + Audio Engine MaxChannels 자동 Voice Limit). **§5 Niagara Quality Scaling** (UNiagaraEffectType + FNiagaraSystemScalabilitySettings + **품질 레벨 5종 매트릭스** Cinematic/High/Medium/Low/Mobile + ENiagaraSignificanceHandling 4종 + Pool 통합 + Scalability::SetQualityLevels 런타임 전환). **§6 다수 NPC 통합 매트릭스** (LOD 5단계 9개 항목). 함정 15종 + 6대 체크리스트 + sub-skill 적용 매트릭스 10종. CLAUDE.md §0.2 교차 인덱스 9개로 확장 + §8.1 어셋 최적화 5대 영역 + §8.3 체크리스트 어셋 최적화 항목. AssetClasses/Mesh / Audio / VFX / Niagara / Components 메인 5개 sub-skill cross-link 추가. |
| 2026-05-06 | **Anthropic Engineering 3개 글 평가 반영 — P0~P3 일괄 개선** (5개 신규 인덱스 + YAML frontmatter + CLAUDE.md/03_WikiHarness.md 갱신). **P0 — Anthropic Skills 표준 준수**: 모든 SKILL.md 106개 파일 (메인 9 + sub-skill 97) 상단에 YAML frontmatter 추가 (`name` + `description` 2필드). 자동 스킴: `name = {category}-{subskill}` 케밥 케이스 / `description` = 첫 헤딩 기반 자동 생성 후 75개 sub-skill 큐레이트 (UE 5.7.4 핵심 클래스/API/패턴 명시). **P1 신설 인덱스 2개**: `14_TaskHandoffTemplate.md` (멀티 세션 작업 인계 5섹션 표준 — Sprint Contract / Decision Log / Progress / Evaluator Findings / Next Session Brief — Article 1 "context reset > compaction" 패턴) + `15_EvaluatorRecipe.md` (Generator/Evaluator 분리 — 회의적 평가 8단계 + Cooked Build 검증 명령 + 100점 채점 — Article 1 self-evaluation bias 방지). **P2 신설 인덱스 1개**: `16_PolicyPriority.md` (정책 충돌 해결 5단 우선순위 — Tier 1 Compile > Tier 2 GC > Tier 3 Runtime > Tier 4 Performance > Tier 5 Maintainability + 5개 자주 충돌 예시 + 결정 트리). **P3 신설 인덱스 2개**: `17_QualityCriteria.md` (측정 가능한 품질 기준 4종 가중 — Performance 35% + Memory 25% + Network 15% + Maintainability 25% + 플랫폼별 임계 매트릭스 + few-shot calibration) + `18_ModelEvolutionAudit.md` (위키 staleness 감사 2축 — UE 진화 + Anthropic 모델 진화 + 8단계 감사 프로세스 + 6종 결정). **CLAUDE.md §0.2 교차 인덱스 10개 → 15개 확장**. §0.1 디렉토리 구조 표 11_~18_ 8개 인덱스 모두 명시. **Wiki 의 Anthropic Skills 표준 호환성 + 세션 간 인계 + 평가자 분리 + 정책 우선순위 + 품질 측정 + 진화 감사 6대 영역 모두 갖춤**. |
