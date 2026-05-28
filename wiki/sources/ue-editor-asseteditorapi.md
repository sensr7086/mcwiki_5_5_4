---
type: source
title: "Editor/AssetEditorAPI — 실행 중인 에셋 에디터 접근 표준 🛠"
slug: ue-editor-asseteditorapi
source_path: raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/SKILL.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/IDetailCustomization]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, editor, asseteditorapi, asseteditor-layout-bypass, asseteditor-tabmanager-window-menu, getobjectscurrentlybeingedited-public, asset-editor-9-matrix-cycle-5f, onregistertabs-6-hosts-cycle-5g, onregistertabs-signature-precise-cycle-5h]
citation_disclosure: "§3.1 9 자산 매트릭스 = 🟢 4 verified (StaticMesh+Persona 3) / 🟡 4 자체 customization (Material+Texture+Niagara+BehaviorTree 부분) / 🔴 2 미검증 (MaterialInstance+SoundCue) (Cycle 5h #1) · §11.4 6 호스트 OnRegisterTabs 시그니처 정밀 매트릭스 = 🟢 verified (Cycle 5h #2 정밀 grep) — `OnRegisterTabs()` 2 호스트 (Persona/LevelEditor) + `OnRegisterTabsForEditor()` 4 호스트 (BlueprintEditor/UMGEditor/WorkspaceEditor/UMGWidgetPreview)"
---

# Editor/AssetEditorAPI — 실행 중인 에셋 에디터 접근 표준 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/SKILL.md]]
>
> **Citation 마커**: 🟢 [verified] / 🟡 grep-listed / 🔴 INFERRED. [[00_meta/06_VaultCitationRule]]
>
> ⭐⭐⭐ 2026-05-14 Cycle 5b — §11 TabManager Window 메뉴 시스템 발견
> 🔧 2026-05-14 — §11.8 protected vs public 매트릭스
> ⭐⭐⭐ 2026-05-15 Cycle 5f #5 — §3.1 9 자산 매트릭스 격상 (Persona 3 추가)
> ⭐⭐⭐ 2026-05-15 Cycle 5g #1+#2 — §3.1 Texture/Niagara 🟡 + §11.4 OnRegisterTabs 6 호스트 + Material/Niagara/BehaviorTree not-exist
> ⭐⭐⭐ 2026-05-15 Cycle 5h #1+#2 — **§3.1 BehaviorTree 🟡 (자손 customization)** + **§11.4 시그니처 정밀 매트릭스** (`OnRegisterTabs` 2 호스트 vs `OnRegisterTabsForEditor` 4 호스트)

## 1. UAssetEditorSubsystem 핵심 API [verified] 🟢

`Engine/Source/Editor/UnrealEd/Public/Subsystems/AssetEditorSubsystem.h`:

```cpp
IAssetEditorInstance* FindEditorForAsset(UObject* Asset, bool bFocusIfOpen);   // L153
bool OpenEditorForAsset(UObject* Asset);
bool OpenEditorForAssets(const TArray<UObject*>& Assets);
void CloseAllEditorsForAsset(UObject* Asset);
FOnAssetOpenedInEditorEvent& OnAssetOpenedInEditor();          // 2-param L189
FAssetEditorRequestCloseEvent& OnAssetEditorRequestClose();    // 2-param L175
```

## 2. EAssetEditorCloseReason 8종 [verified] 🟢

(매트릭스 유지)

## 3. IAssetEditorInstance 인터페이스 🟢

```cpp
class IAssetEditorInstance
{
public:
    virtual FName GetEditorName() const = 0;
    virtual void FocusWindow(UObject* ObjectToFocusOn = nullptr) = 0;
    virtual bool CloseWindow(EAssetEditorCloseReason);
};
```

### 3.1 ⭐⭐⭐ EditorName + **layout delegate 우회 9 자산 매트릭스** (Cycle 5e→5f→5g→5h 진화)

| FName | 호스트 | 에셋 클래스 | 우회 위험 | Engine grep 출처 |
| -- | -- | -- | -- | -- |
| `StaticMeshEditor` | StaticMeshEditor | UStaticMesh | **🟢 우회 확정** | Journey Phase 5 + KMCProject (2026-05-12) |
| `SkeletalMeshEditor` | Persona | USkeletalMesh | **🟢 우회 확정** | `PersonaModule.cpp` + Persona 3 widget |
| `AnimationEditor` | Persona | UAnimSequence/Montage | **🟢 우회 확정** | Persona 동일 |
| `AnimationBlueprintEditor` | Persona | UAnimBlueprint | **🟢 우회 확정** | Persona 동일 |
| `MaterialEditor` | MaterialEditor | UMaterial | **🟡 자체 RegisterCustomClassLayout** | `MaterialEditor.cpp` 자체 등록 |
| `TextureEditor` | TextureEditor | UTexture | **🟡 자체 RegisterCustomClassLayout** | `TextureEditorModule.cpp:77` `RegisterCustomClassLayout("Texture", ...)` |
| `NiagaraEditor` | NiagaraEditor | UNiagaraSystem | **🟡 자체 RegisterCustomClassLayout** | `NiagaraEditorModule.cpp:1311+` 9개 등록 |
| **`BehaviorTreeEditor`** ⭐ | BTEditor | UBehaviorTree | **🟡 부분 — 자손 customization (Cycle 5h #1)** | `BehaviorTreeEditorModule.cpp:58-62` `BTDecorator_Blackboard` / `BTDecorator` / `BlackboardKeyType_Class/Enum/Object` 자손 등록. `UBehaviorTree` 자체 자손 customization 미확인 — 표준 디테일 추정 |
| `MaterialInstanceEditor` | MaterialInstanceEditor | UMaterialInstance | 🔴 INFERRED | grep 결과 없음 (Material 동일 메커니즘 또는 표준 디테일) |
| `SoundCueEditor` | SoundCueEditor | USoundCue | 🔴 INFERRED | grep 결과 없음 — 표준 디테일 추정 |

#### 3.1.1 격상 진화

| 상태 | 5e 1차 | 5f #5 | 5g #1 | **5h #1** |
| -- | -- | -- | -- | -- |
| 🟢 우회 확정 | 1 | 4 | 4 | **4** (유지) |
| 🟡 자체 메커니즘 | 0 | 1 | 3 | **4** (+BehaviorTree 부분) |
| 🔴 INFERRED | 9 | 5 | 3 | **2** (MaterialInstance / SoundCue) |

#### 3.1.2 회피 패턴 (자산 카테고리별)

| 자산 | 우회 패턴 |
| -- | -- |
| **Persona 4** ⭐ | `FPersonaModule::OnRegisterTabs` delegate |
| **StaticMeshEditor** | Tab Spawner + DataAsset 분리 |
| **Material/Texture/Niagara 🟡** | 자체 RegisterCustomClassLayout 활성 — 외부 등록 가능 (충돌 시 등록 순서 의존). 안전 위해 Tab Spawner 권장 |
| **BehaviorTreeEditor 🟡** | 자손 customization 패턴 (BTDecorator / BlackboardKey) — UBehaviorTree 자체는 표준 |
| 🔴 미검증 2 | 표준 RegisterCustomClassLayout 시도 → UE_LOG 진단 (Cycle 5i+) |

## 4. static_cast 안전 패턴 ⭐ [verified]

```cpp
#if WITH_EDITOR
if (EditorInst->GetEditorName() == FName("StaticMeshEditor"))
{
    auto* SME = static_cast<IStaticMeshEditor*>(EditorInst);
}
#endif
```

## 5. 구체 에디터 인터페이스 → references/

| 인터페이스 | reference |
| -- | -- |
| `IStaticMeshEditor` ⭐ | [[sources/ue-editor-staticmesheditor]] |
| `ISkeletalMeshEditor` + `IPersonaToolkit` + `UDebugSkelMeshComponent` | [[sources/ue-editor-personatoolkit]] |
| 이벤트 바인딩 | [[sources/ue-editor-eventbinding]] |
| `FAdvancedPreviewScene` | [[sources/ue-editor-advancedpreviewscene]] |

## 6. Build.cs 의존성

```csharp
PrivateDependencyModuleNames.AddRange(new[] {
    "UnrealEd", "StaticMeshEditor", "SkeletalMeshEditor", "Persona", "AdvancedPreviewScene"
});
```

## 7. 함정 13대 (Cycle 5h 매트릭스 정밀화 — 함정 추가 없음)

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `WITH_EDITOR` 가드 누락 | 모든 코드 |
| 2 | Runtime 에 Editor 의존 | 4단 분리 |
| 3 | `IAssetEditorInstance*` 직접 cast | EditorName 검증 후 cast |
| 4 | `CloseWindow()` no args | `CloseWindow(EAssetEditorCloseReason)` |
| 5 | `OnAssetOpenedInEditor` 1-param 추측 | 2-param |
| 6 | `OnAssetEditorRequestClose` 1-param 추측 | 2-param |
| 7 | Delegate 등록 후 해제 누락 | Init/Deinit 페어 |
| 8 | `GetPreviewMeshComponent()` 반환 추측 | UDebugSkelMeshComponent |
| 9 | 캐싱된 `IAssetEditorInstance*` 재사용 | 매 호출 재조회 |
| 10 | EditorName 하드코딩 | 분기별 grep |
| **11** ⭐ | Persona 4 + StaticMeshEditor 에서 RegisterCustomClassLayout 시도 → 강제 우회 | Tab Spawner / DataAsset 분리 |
| **12** ⭐⭐⭐ | AssetEditor Window 메뉴 ToolMenus 시도 → stub | 호스트별 OnRegisterTabs[ForEditor] delegate |
| **13** ⭐ | 외부 모듈 `Toolkit->GetEditingObjects()` C2248 | `GetObjectsCurrentlyBeingEdited()` public nullable |

## 8. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 자매: [[sources/ue-editor-staticmesheditor]] / [[sources/ue-editor-personatoolkit]] / [[sources/ue-editor-eventbinding]] / [[sources/ue-editor-advancedpreviewscene]]
- 횡단 정책: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-11-assetloadingpolicy]] §3
- ⭐ layout delegate 우회 deep: [[synthesis/instanced-subobject-customization-bypass]]
- ⭐⭐⭐ TabManager Window 메뉴: [[sources/ue-editor-toolmenus]] §2.9 + [[sources/ue-editor-personatoolkit]] §2.7
- PropertyEditor: [[sources/ue-editor-propertyeditor]] §2.6.10
- 측정: [[sources/ue-measure-instancedsubobject-2026-05-12]]
- ⭐ Baseline grep: [[sources/ue-meta-baseline-grep-system]]
- Citation: [[00_meta/06_VaultCitationRule]]

### Cycle 5l reverse-link 보강 (suggest_missing 결과)

- ⭐ [[synthesis/mc-character-hit-reaction-pipeline]] (KMCProject Persona 별도 탭 + AssetEditor TabManager 패턴 3회 인용)
- ⭐ [[synthesis/mc-combo-editor-levelsequence-lite]] (KMCProject MCComboEditor Toolkit + 4단 분리 3회 인용)
- [[sources/ue-editor-unrealed-subsystems]] (UAssetEditorSubsystem 베이스 + Window 메뉴 페어)
- [[synthesis/bp-scs-preview-viewport-lifecycle]] (BP SCS Preview Viewport — AssetEditor lifecycle 페어)

## 9. Open questions

- [x] §3.1 자산 에디터별 layout delegate 우회 실증 (Persona 3 추가) — Cycle 5f #5
- [x] §3.1 Texture/Niagara 자체 메커니즘 (Cycle 5g #1)
- [x] §3.1 BehaviorTree 자손 customization 패턴 (Cycle 5h #1)
- [ ] §3.1 잔여 2 자산 (MaterialInstance / SoundCue) UE_LOG 진단 — Cycle 5i+
- [ ] `IAssetEditorInstance` → `FTabManager` 접근 시그니처
- [x] §11.4 호스트 OnRegisterTabs 6 매트릭스 (Cycle 5g #2 + 5h #2 정밀 시그니처)

## 10. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-08 | 최초 작성 — UAssetEditorSubsystem 7 API |
| 2026-05-12 | §3.1 layout delegate 우회 위험 컬럼 (StaticMesh 🟢 / 9 🔴) |
| 2026-05-14 | ⭐⭐⭐ §11 신규 — TabManager Window 메뉴 시스템 |
| 2026-05-14 | ⭐ §11.8 신규 — protected vs public 매트릭스 |
| 2026-05-15 | Cycle 5f #5 — §3.1 Persona 3 추가 |
| 2026-05-15 | Cycle 5g #1+#2 — §3.1 Texture/Niagara 🟡 + §11.4 6 호스트 매트릭스 |
| **2026-05-15** | ⭐⭐⭐ **Cycle 5h #1+#2 — §3.1 BehaviorTree 🟡 (자손 customization) + §11.4 정밀 시그니처 매트릭스** (`OnRegisterTabs()` 2 호스트 vs `OnRegisterTabsForEditor()` 4 호스트). tag `onregistertabs-signature-precise-cycle-5h` |

## 11. ⭐⭐⭐ AssetEditor Window 메뉴 = TabManager 자체 시스템 (2026-05-14)

### 11.1 배경 — FAssetEditorToolkit::InitAssetEditor (L222)

```cpp
NewTabManager->SetAllowWindowMenuBar(true);   // ⭐ TabManager 자체 Window 메뉴
```

### 11.2 RegisterTabSpawners — toolkit 자체 등록 (L342)

`InTabManager->RegisterTabSpawner(...).SetGroup(AssetEditorTabsCategory)` 형태.

### 11.3 ToolMenus 와 비교

| 시스템 | 메뉴 호스트 | 등록 API |
| -- | -- | -- |
| ToolMenus | MainFrame / LevelEditor / ContentBrowser | `UToolMenus::ExtendMenu(...)` + RegisterStartupCallback |
| ⭐ TabManager LocalWorkspace | 각 AssetEditor 자체 | `InTabManager->RegisterTabSpawner(...).SetGroup(...)` |
| GlobalTabmanager | 글로벌 | `FGlobalTabmanager::RegisterNomadTabSpawner(...)` |

### 11.4 ⭐⭐⭐ 호스트별 OnRegisterTabs delegate 6 매트릭스 — **시그니처 정밀화 (Cycle 5h #2)** 🟢

UE Engine grep `FOnRegisterTabs` 종합 (Persona 5 모드 + Plugin 포함):

| 호스트 모듈 | accessor 이름 ⚠ | 시그니처 (param 수) | 위치 | 검증 |
| -- | -- | -- | -- | -- |
| `FPersonaModule` | **`OnRegisterTabs()`** | **2** `(FWorkflowAllowedTabSet&, TSharedPtr<FAssetEditorToolkit>)` | `Editor/Persona/Public/PersonaModule.h` L70/L550 | 🟢 Cycle 5b |
| `FLevelEditorModule` | **`OnRegisterTabs()`** | **1** `(TSharedPtr<FTabManager>)` | `Editor/LevelEditor/Public/LevelEditor.h` | 🟢 Cycle 5b |
| `FBlueprintEditorModule` | **`OnRegisterTabsForEditor()`** ⚠ | **3** `(FWorkflowAllowedTabSet&, FName ModeName, TSharedPtr<FBlueprintEditor>)` | `Editor/Kismet/Public/BlueprintEditorModule.h:225-226` | 🟢 Cycle 5e #6 |
| `IUMGEditorModule` 🆕 | **`OnRegisterTabsForEditor()`** ⚠ | **2** `(const FWidgetBlueprintApplicationMode&, FWorkflowAllowedTabSet&)` | `Editor/UMGEditor/Public/UMGEditorModule.h:36-37` | 🟢 Cycle 5h #2 |
| `IWorkspaceEditorModule` 🆕 (Experimental) | **`OnRegisterTabsForEditor()`** ⚠ | **3** `(FWorkflowAllowedTabSet&, const TSharedRef<FTabManager>&, TSharedPtr<IWorkspaceEditor>)` | `Plugins/Experimental/Workspace/Source/WorkspaceEditor/Public/IWorkspaceEditorModule.h:271-272` | 🟢 Cycle 5h #2 |
| `IUMGWidgetPreviewModule` 🆕 (Plugin) | **`OnRegisterTabsForEditor()`** ⚠ | **2** `(const TSharedPtr<IWidgetPreviewToolkit>&, const TSharedRef<FTabManager>&)` | `Plugins/Editor/UMGWidgetPreview/Source/UMGWidgetPreview/Public/IUMGWidgetPreviewModule.h:23-24` | 🟢 Cycle 5h #2 |
| ❌ FMaterialEditorModule | — | — | (미존재) | 🔴 not-exist |
| ❌ FNiagaraEditorModule | — | — | (미존재) | 🔴 not-exist |
| ❌ FBehaviorTreeEditorModule | — | — | (미존재) | 🔴 not-exist |

#### 11.4.1 ⚠⚠⚠ accessor 이름 매트릭스 — *Persona/LevelEditor 만 `OnRegisterTabs()`, 4 호스트는 `OnRegisterTabsForEditor()`*

```
2 호스트 `OnRegisterTabs()`:
  - FPersonaModule (2-param)
  - FLevelEditorModule (1-param)

4 호스트 `OnRegisterTabsForEditor()`:
  - FBlueprintEditorModule (3-param)
  - IUMGEditorModule (2-param)
  - IWorkspaceEditorModule (3-param)
  - IUMGWidgetPreviewModule (2-param)
```

→ **generic 호출 불가**. 호스트별 분기 + accessor 이름 정확 검증 의무.

#### 11.4.2 DECLARE 매크로 매트릭스

| DECLARE | 사용처 |
| -- | -- |
| `DECLARE_MULTICAST_DELEGATE_TwoParams` | Persona (1 호스트만) |
| `DECLARE_EVENT_OneParam` | LevelEditor (추정) |
| `DECLARE_EVENT_TwoParams` | UMGEditor / UMGWidgetPreview |
| `DECLARE_EVENT_ThreeParams` | BlueprintEditor / WorkspaceEditor |

→ Persona 만 MULTICAST_DELEGATE, 나머지는 EVENT — 이벤트 인스턴스 멤버 패턴.

#### 11.4.3 시그니처 분기

- **1-param** (1 호스트): LevelEditor — `(TSharedPtr<FTabManager>)` (toolkit 인자 없음)
- **2-param** (3 호스트):
  - Persona: `(FWorkflowAllowedTabSet&, TSharedPtr<FAssetEditorToolkit>)` — toolkit 포인터
  - UMGEditor: `(const FWidgetBlueprintApplicationMode&, FWorkflowAllowedTabSet&)` — Mode 식별
  - UMGWidgetPreview: `(const TSharedPtr<IWidgetPreviewToolkit>&, const TSharedRef<FTabManager>&)` — toolkit + TabManager
- **3-param** (2 호스트):
  - BlueprintEditor: `(FWorkflowAllowedTabSet&, FName ModeName, TSharedPtr<FBlueprintEditor>)` — Mode 식별 (FName)
  - WorkspaceEditor: `(FWorkflowAllowedTabSet&, const TSharedRef<FTabManager>&, TSharedPtr<IWorkspaceEditor>)` — toolkit + TabManager

#### 11.4.4 잔여 호스트 (Material / Niagara / BehaviorTree) 대안

OnRegisterTabs[ForEditor] 미존재 → 외부 모듈 메뉴 항목 추가 시:
- `FGlobalTabmanager::RegisterNomadTabSpawner(...)` (Nomad Tab — 글로벌 Window)
- ToolMenus `ContentBrowser.AssetContextMenu.<AssetType>` (우클릭)
- 자손 Editor 자체 settings 확장

### 11.5 표준 패턴 — Persona 적용 예

상세 = [[sources/ue-editor-personatoolkit]] §2.7.4-2.7.5 (KMCProject `FMCHitBoneCurveEditorMenu` Cycle 5b 적용).

### 11.6 KMCProject 검증 — 5 후보 ToolMenus stub (2026-05-14)

모두 `IsMenuRegistered=FALSE` 영구. 진짜 fix = `FPersonaModule::OnRegisterTabs`.

### 11.7 결정 가이드

```
어디에 노출?
  ├── 메인 윈도우 → ToolMenus + RegisterStartupCallback
  ├── 특정 AssetEditor (6 호스트) → 호스트별 OnRegisterTabs[ForEditor] (§11.4)
  ├── OnRegisterTabs 미존재 호스트 (Material/Niagara/BehaviorTree) → Nomad Tab / AssetContextMenu / Editor settings
  ├── 모든 Editor Window 글로벌 → FGlobalTabmanager::RegisterNomadTabSpawner
  └── ContentBrowser 우클릭 → ToolMenus ContentBrowser.AssetContextMenu.<AssetType>
```

### 11.8 ⭐ protected vs public 매트릭스 (2026-05-14)

| API | 가시성 | 외부 모듈 |
| -- | -- | -- |
| ⭐ `GetObjectsCurrentlyBeingEdited()` | **public** (L154) `const TArray<UObject*>*` nullable | ✅ 표준 |
| `GetEditingObject()` / `GetEditingObjects()` / `GetEditingObjectPtrs()` | protected (L333/336/337) | ❌ 자손 toolkit 만 |
| `GetToolkitFName()` | public | ✅ 분기용 |

KMCProject 검증 — `MCHitBoneCurveEditorMenu.cpp` C2248 → `GetObjectsCurrentlyBeingEdited()` 표준.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
