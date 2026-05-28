---
type: synthesis
title: "Editor preview scene 와 런타임 spawn 로직의 공용 헬퍼 핸드오프 (Pattern A)"
slug: editor-preview-scene-runtime-handoff
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-editor-editorsubsystem]]"
  - "[[sources/ue-editor-unrealed-asseteditortoolkit]]"
  - "[[sources/ue-editor-unrealed-subsystems]]"
  - "[[sources/ue-editor-propertyeditor]]"
  - "[[sources/ue-assetclasses-assetuserdata]]"
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/ue-components-particlecomponents]]"
  - "[[sources/ue-ref-05-editoronlyindex]]"
  - "[[sources/ue-ref-07-profilingscopeRule]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-editor-asseteditorapi]]"
  - "[[sources/ue-editor-eventbinding]]"
  - "[[sources/ue-editor-staticmesheditor]]"
  - "[[sources/ue-editor-personatoolkit]]"
  - "[[sources/ue-editor-advancedpreviewscene]]"
  - "[[sources/ue-editor-dependencies]]"
entities:
  - "[[entities/UEngineSubsystem]]"
  - "[[entities/USubsystem]]"
  - "[[entities/IToolkit]]"
  - "[[entities/UStaticMesh]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UNiagaraComponent]]"
  - "[[entities/UNiagaraSystem]]"
  - "[[entities/UActorComponent]]"
  - "[[entities/IDetailCustomization]]"
concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Slate-Editor-Runtime-Separation]]"
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, mc, editor, niagara]
---

# Editor preview scene 와 런타임 spawn 로직의 공용 헬퍼 핸드오프 (Pattern A)

> Status: living · 2026-05-11 · **vault verified 2026-05-11** (Phase 6 AssetEditorAPI sub-skill 5종 대조 결과 코드 100% 정합) · **viewport 드로우 성공 2026-05-11** (SM_Sword_F06 + NS_Flame_4)

## 1. Thesis

**자산 메타 (`UAssetUserData`) 의 spawn 로직은 런타임 `UActorComponent` 와 에디터 `UEditorSubsystem` 사이에서 *완전히 동일* 해야 한다.** 두 컨텍스트가 다른 건 *attach 대상 메시 컴포넌트의 출처* 뿐 — 런타임은 게임 World 의 Owner Actor 의 메시, 에디터는 `IStaticMeshEditor::GetStaticMeshComponent()` / `IPersonaToolkit::GetPreviewMeshComponent()` 의 preview 메시. 따라서 spawn / load / cleanup 의 모든 단계는 **stateless namespace 헬퍼** 로 압축되고, 호출자 (runtime / editor) 는 *얇은 래퍼* 가 된다.

이 패턴이 [[concepts/Editor-Only-4-Tier-Separation]] (런타임/에디터 분리) 과 *충돌하지 않는다* — 헬퍼 본체는 런타임 모듈에 살고, 에디터 측은 `#if WITH_EDITOR` 가드된 호출자만 추가. Backward dep 은 정적 멀티캐스트 ([[concepts/Subsystem-5-Types]] §UEditorSubsystem 구독) 로 회피.

## 2. 결정 표 — 어디에 어떤 코드가 사는가

| 책임 | 위치 | 모듈 | 이유 |
| -- | -- | -- | -- |
| Spawn / Load / Cleanup 로직 | `MCNiagaraSocketBindingHelpers` (namespace) | MCPlayModule (런타임) | 두 컨텍스트 공유. WITH_EDITOR 의존 없음. |
| Runtime 호출자 | `UMCStaticMeshNiagaraSpawnerComponent` | MCPlayModule | BeginPlay/EndPlay 라이프사이클 |
| Editor 호출자 | `UMCNiagaraSocketPreviewSubsystem` | MCEditorModule | WITH_EDITOR 가드 + UEditorSubsystem |
| 디테일 변경 통지 | `UMCNiagaraSocketBindings::OnBindingsChanged` (static 멀티캐스트) | MCPlayModule (헤더) | Editor → 구독, Runtime → broadcast. 백워드 dep 없음. |
| Asset metadata | `UMCNiagaraSocketBindings : UAssetUserData` | MCPlayModule | 자산에 첨부 (cooked 빌드 포함) |
| 자산 디테일 패널 | `FMCNiagaraSocketBindingDetails : IPropertyTypeCustomization` | MCEditorModule | WITH_EDITOR only |

## 3. 5단계 라이프사이클

### 3.1. Runtime BeginPlay path

1. `UMCStaticMeshNiagaraSpawnerComponent::BeginPlay` — Owner Actor 캐싱 + `FindTargetMeshComponent` 으로 메시 컴포넌트 추출.
2. `MCNiagaraSocketBindingHelpers::GetBindingsFromMesh(MeshComp)` — UStaticMesh/USkeletalMesh 분기로 `GetAssetUserData<UMCNiagaraSocketBindings>`.
3. `RequestLoad(Bindings, Priority, "Runtime:<Owner>", OnLoaded)` — 모든 `TSoftObjectPtr<UNiagaraSystem>` 한 핸들로 비동기. 핸들 멤버 Pin ([[concepts/Asset-Loading-Policy]] §2 단계 5).
4. 콜백 `HandleBindingsLoaded` → `SpawnAllNow(TargetMesh, Bindings, Context, OutSpawned)` — `UNiagaraFunctionLibrary::SpawnSystemAttached` + `ENCPoolMethod::AutoRelease` ([[sources/ue-niagara-skill]] §SpawnSystemAttached).
5. `EndPlay` — `LoadHandle->CancelHandle()` + `DeactivateAll(SpawnedNiagaras)` — Pool 에 반환.

### 3.2. Editor preview path

1. `GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OnAssetOpenedInEditor` 구독 ([[sources/ue-editor-unrealed-subsystems]] §FOnAssetOpenedInEditorEvent).
2. 콜백 `OnAssetOpenedInEditor(Asset, IAssetEditorInstance*)` — `Asset->IsA<UStaticMesh>()` || `IsA<USkeletalMesh>()` 검사 + `EditorInstance->GetEditorName()` 으로 식별.
3. `ResolvePreviewMesh` — UE 의 *casual cast* 패턴:
   - StaticMesh: `static_cast<IStaticMeshEditor*>(EditorInstance)->GetStaticMeshComponent()`.
   - SkeletalMesh: `static_cast<ISkeletalMeshEditor*>(EditorInstance)->GetPersonaToolkit()->GetPreviewMeshComponent()`.
4. `Entries.Add(WeakAsset, MakeUnique<FMCNiagaraSocketPreviewEntry>())` — TUniquePtr 로 주소 안정성. raw pointer 콜백 캡처 가능.
5. `SpawnForEntry(*Entry)` → 헬퍼 `RequestLoad` → 콜백에서 `SpawnAllNow`. 자산 close 시 `OnAssetEditorRequestClose` → `DestroyForEntry`.

### 3.3. Refresh path (디테일 변경)

1. 디자이너가 디테일 패널에서 binding 수정 → `FPropertyHandle::SetValue` → UE 자동 `PostEditChangeProperty` 호출.
2. `UMCNiagaraSocketBindings::PostEditChangeProperty` override → `OnBindingsChanged.Broadcast(GetOuter())`.
3. `UMCNiagaraSocketPreviewSubsystem::Initialize` 에서 미리 `AddUObject(this, &RefreshForAsset)` 구독돼있음.
4. `RefreshForAsset(HostAsset)` — `Entries.Find` 으로 entry 검색 → `DestroyForEntry` + `SpawnForEntry`.
5. 런타임 측은 영향 없음 (PIE 중이 아니면 broadcast 무시).

## 4. 함정

1. **TMap 재할당으로 raw pointer 무효화** — `TMap<Key, FStruct>` 는 rehash 시 value 이동. 콜백이 entry 주소 캡처하면 dangling. 해결 — `TMap<Key, TUniquePtr<FStruct>>` 로 감싸 entry 주소 안정.
2. **`static_cast<IStaticMeshEditor*>` UB 가능성** — `IAssetEditorInstance` 와 `IStaticMeshEditor` 는 별도 hierarchy. concrete `FStaticMeshEditor` 가 둘 다 상속. UE 코드베이스 패턴이지만 표준 C++ 관점 회색. `GetEditorName()` 검사로 방어.
3. **콜백 시점 Entry 제거** — async load 콜백이 도착했는데 그 사이 자산이 닫혔으면 `Entries.Find()` 검증 필수. raw ptr 만 보면 use-after-free.
4. **Backward dep (Editor → Play 가 normal)** — MCPlayModule 이 MCEditorModule 의 subsystem 호출하면 cyclic. **해결 — static 멀티캐스트** (MCPlayModule 헤더에 선언, Editor 측 구독). MCPlayModule 은 누가 구독하는지 모름.
5. **Niagara Pool 이중 반환** — `Deactivate()` 한 컴포넌트를 한 번 더 `Deactivate()` 하면 안전하지만 `DestroyComponent()` 하면 풀 회계 깨짐. 헬퍼 `DeactivateAll` 은 Deactivate 만 (Pool 이 알아서 회수).
6. **Cooked Build 에서 PreviewSubsystem 비활성** — `UEditorSubsystem` 자체가 `#if WITH_EDITOR` only. cook 시 통째로 컴파일 제외 ([[concepts/Editor-Only-4-Tier-Separation]]).
7. **Persona/SkeletalMeshEditor 모듈 의존** — preview mesh 접근 위해 MCEditorModule.Build.cs 에 `Persona`, `SkeletalMeshEditor`, `StaticMeshEditor` 필요. Editor only 빌드라 cook 빌드 영향 없음.
8. **WeakObject vs ObjectPtr 혼용** — 헬퍼는 `TArray<TWeakObjectPtr<UNiagaraComponent>>` 통일. 런타임 컴포넌트도 `TObjectPtr` 대신 `TWeakObjectPtr` 로 변경 — Pool AutoRelease 가 lifetime 관리하므로 약참조로 충분.
9. **자산 첫 열림 시 binding 비어있으면 entry 미생성** — 사용자 흐름은 (자산 열기 → 디테일에서 binding 추가) 가 정상. `OnAssetOpenedInEditor` 가 *binding 비어있다는 이유로* early return 하면 entry 가 안 만들어짐. 그 후 `PostEditChangeProperty` 의 broadcast 도 `Entries.Find` 가 nullptr 반환해 무효. **해결 — `RefreshForAsset` 에 entry 미존재 fall-through 패스**: `UAssetEditorSubsystem::FindEditorForAsset(HostAsset)` 으로 현재 열린 에디터 검색 → `ResolvePreviewMesh` → entry 신규 생성 + spawn. (2026-05-11 사용자 실제 증상)
10. **로그 verbosity 함정** — 진단 메시지를 `Verbose` 로 깔면 콘솔 출력 안 됨. 핵심 진입점 (open / refresh / resolve / spawn) 은 `Display` 로, soft fail 만 `Verbose` 로. 사용자 검증 가능성 확보.
11. **EditorPreview Niagara 활성화 — `bAutoActivate` 단독으로는 부족** — `EWorldType::EditorPreview` 의 `FNiagaraWorldManager` 는 SystemInstance lazy init / batch tick 큐가 disabled. `SpawnSystemAttached(bAutoActivate=true)` 와 명시 `Activate(true)` 둘 다 silently 거부됨. **해결 — 3단 보강**: `SetForceSolo(true)` (WorldManager 우회, 자체 tick) + `Activate(true)` + `ResetSystem()` (SystemInstance 강제 재시작). 또한 `Pool=ENCPoolMethod::None` 필수 — AutoRelease 는 게임 World 가정. **🟢 verified 2026-05-11** — 사용자 SM_Sword_F06 + NS_Flame_4 viewport 드로우 성공 로그: `IsRegistered=1 Asset=NS_Flame_4 ExecState=3 ForceSolo=1`.
12. **`UNiagaraComponent::IsActive()` vs `GetExecutionState()` — 진실은 ExecState** — `IsActive()` 는 USceneComponent 의 `bIsActive` flag 만 반환. Niagara 의 실제 시뮬 상태는 `GetExecutionState()` (`ENiagaraExecutionState` 0=Active / 1=Inactive / 2=InactiveClear / **3=Complete** / 4=Disabled). `IsActive=0` 이라도 `ExecState=3 (Complete)` 면 정상 종료 (emitter lifetime 끝). 진단 시 `IsActive` 단일 의존 금지.
13. **`Deactivate()` 만으론 Pool=None 컴포넌트 cleanup 안 됨** — `AutoRelease` Pool 은 `Deactivate()` 호출 시 컴포넌트를 Pool 큐로 회수 → 자동 cleanup. **Pool=None (EditorPreview 분기) 은 `Deactivate()` 가 `IsActive=false` 만 설정 + 컴포넌트는 viewport / socket attach 그대로 유지.** RefreshForAsset 마다 새 NC 가 attach 누적되어 *여러 Niagara 동시 표시* + GC 부담. **해결 — `DeactivateAll` 헬퍼에 PoolingMethod 분기**: `if (NC->PoolingMethod == ENCPoolMethod::None) NC->DestroyComponent();`. 런타임 (AutoRelease) 은 그대로, EditorPreview 만 명시 destroy. (2026-05-11 Location Offset 슬라이더 조정 시 사용자 보고)
14. **드래그 중간 (Interactive PostEditChange) 의 PoolingMethod race** — `PostEditChangeProperty` 가 *드래그 마우스 릴리스 시점* 만이 아니라 *Interactive change* (드래그 중 매 frame) 에도 fire 됨. RefreshForAsset 매 frame → 이전 RequestLoad 콜백이 늦게 fire 되어 *PoolingMethod 가 None 이 아닌 값* 으로 도착하는 race 발생. PoolingMethod 검사 분기 만으로는 cleanup 누락 → `destroyed=0 + total=N` 누적. **해결 — `DeactivateAll` 에 `bForceDestroy` 옵션 추가**: 에디터 측 `DestroyForEntry` 가 `DeactivateAll(Spawned, true)` 로 호출 → PoolingMethod 무관 무조건 `DestroyComponent`. 런타임은 default false 그대로 (AutoRelease Pool 회수 호환). 호출자가 *컨텍스트 결정*. (2026-05-12 드래그 중 누적 사용자 보고)

## 5. 관련

### Sources

- [[sources/ue-editor-editorsubsystem]] — UEditorSubsystem 베이스 패턴
- [[sources/ue-editor-unrealed-asseteditortoolkit]] — IAssetEditorInstance / FAssetEditorToolkit
- [[sources/ue-editor-unrealed-subsystems]] — UAssetEditorSubsystem 의 OnAssetOpenedInEditor 이벤트
- [[sources/ue-editor-propertyeditor]] — IPropertyTypeCustomization / PostEditChangeProperty
- [[sources/ue-assetclasses-assetuserdata]] — UAssetUserData::Draw / PostEditChangeProperty hook
- [[sources/ue-niagara-skill]] — SpawnSystemAttached + ENCPoolMethod::AutoRelease
- [[sources/ue-components-particlecomponents]] — UNiagaraComponent 라이프사이클
- [[sources/ue-ref-05-editoronlyindex]] — Editor/Runtime 4단 분리
- [[sources/ue-ref-07-profilingscopeRule]] — TRACE_CPUPROFILER_EVENT_SCOPE 의무
- [[sources/ue-ref-11-assetloadingpolicy]] — SoftPtr + Handle Pin

### Entities

- [[entities/UEngineSubsystem]] · [[entities/USubsystem]] · [[entities/IToolkit]]
- [[entities/UStaticMesh]] · [[entities/USkeletalMesh]] · [[entities/UNiagaraComponent]] · [[entities/UNiagaraSystem]]
- [[entities/UActorComponent]] · [[entities/IDetailCustomization]]

### Concepts

- [[concepts/Editor-Only-4-Tier-Separation]] · [[concepts/Slate-Editor-Runtime-Separation]] · [[concepts/Subsystem-5-Types]]
- [[concepts/Asset-Loading-Policy]] · [[concepts/Component-Policies-6]] · [[concepts/Profiling-Scope-Rule]] · [[concepts/MC-Asset-Validation-Policy]]

### Cross-synthesis

- [[synthesis/mc-soft-asset-component-pattern]] — MCSoft 컴포넌트 (Soft + Loader + Validation)
- [[synthesis/spawnactor-hitching-4-step-pattern]] — 비동기 로드 + Pin 패턴의 표준 4단계
- [[synthesis/vfx-audio-soft-pool-significance]] — Niagara Soft + Pool AutoRelease 의 VFX 표준
