---
type: source
title: "UE Editor — Persona Toolkit + ISkeletalMeshEditor + UDebugSkelMeshComponent"
slug: ue-editor-personatoolkit
source_path: raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/references/PersonaToolkit.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-19
related_entities:
  - "[[entities/IToolkit]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, asseteditorapi, persona, skeletalmesh, animation, kmcproject-verified, on-register-tabs-delegate, getobjectscurrentlybeingedited-public, enable-tab-padding, layout-cache, ue-anim-preview-instance-modifybone, scrub-driven-tick-3-axis, set-update-animation-in-editor]
---

# UE Editor — Persona Toolkit + ISkeletalMeshEditor 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/references/PersonaToolkit.md]]
> 보강 2026-05-13 — IAssetEditorInstance 별도 헤더 없음 함정 + KMCProject Phase 2 사례 cross-link
> ⭐⭐⭐ 보강 2026-05-14 — §2.7 `FPersonaModule::OnRegisterTabs` delegate + §2.7.5 6요소 표준 + §2.7.9 protected vs public + §2.7.10 Layout cache + ⭐ §2.7.11 **UAnimPreviewInstance::ModifyBone PoseModifier 표준** (Phase 5 검증, multi-bone preview)
> ⭐⭐⭐ 보강 2026-05-19 — §2.4.1 **UDebugSkelMeshComponent scrub-driven preview Tick 3축 표준** (Phase 5a 검증, KMCProject MCComboEditor) + 함정 10/11 신규

## 1. Summary

Skeletal Mesh / Animation 계열 에디터 = **Persona Toolkit** 통합. 핵심 인터페이스 3:
- **`ISkeletalMeshEditor`** + **`IPersonaToolkit`** + **`UDebugSkelMeshComponent`**

Build.cs 의존: `"SkeletalMeshEditor"` + `"Persona"`. 🛠 **Editor 전용**.

⭐⭐⭐ **§2.7 핵심**: Persona toolkit Window 메뉴 항목 = `FPersonaModule::OnRegisterTabs` delegate (ToolMenus 가 *아님*).
⭐⭐⭐ **§2.7.11 핵심**: Persona Preview Mesh 의 본 회전 적용 = `UAnimPreviewInstance::ModifyBone(BoneName).Rotation = Rot` PoseModifier 표준.
⭐⭐⭐ **§2.4.1 핵심 (신규 2026-05-19)**: 자체 PreviewScene 안 UDebugSkelMeshComponent scrub-driven preview = **Slate Tick override 안 3축 명시** (`SEditorViewport::Tick` + `World->Tick` + `TickAnimation`) — `SetPosition` 단독 호출 시 silent fail.

## 2. Key claims

### 2.1. 통합 구조 — Persona Toolkit 🟢

```
USkeletalMesh → FindEditorForAsset → ISkeletalMeshEditor → GetPersonaToolkit
   → IPersonaToolkit → GetPreviewMeshComponent → UDebugSkelMeshComponent
```

### 2.2. 표준 접근 패턴 🟢

```cpp
UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(SkelMesh, false);
if (EditorInst && EditorInst->GetEditorName() == FName("SkeletalMeshEditor"))
{
    auto* SkelEditor = static_cast<ISkeletalMeshEditor*>(EditorInst);
    TSharedRef<IPersonaToolkit> Toolkit = SkelEditor->GetPersonaToolkit();
    UDebugSkelMeshComponent* PreviewMesh = Toolkit->GetPreviewMeshComponent();
}
```

### 2.3. ⭐ IAssetEditorInstance 헤더 위치 함정 (2026-05-13) 🟢

⚠ `IAssetEditorInstance.h` 파일 **X** (C1083). 사용 위치:
- `Subsystems/AssetEditorSubsystem.h` / `Toolkits/IToolkit.h` 안 정의.

→ Forward decl 또는 위 헤더 include.

### 2.4. UDebugSkelMeshComponent 추가 기능

`UDebugSkelMeshComponent : public USkeletalMeshComponent` — Editor 전용:
- `BoneDrawMode` / Cloth 디버그 / Physics 시각화 / Pose Watch
- ⭐ `PreviewInstance` (TObjectPtr<UAnimPreviewInstance>) — §2.7.11 PoseModifier 진입점

#### 2.4.1 ⭐⭐⭐ Scrub-driven Preview Tick 3축 표준 (2026-05-19 신규) 🟢

##### 2.4.1.1 배경 — Persona 외부 자체 PreviewScene 안 scrub-driven preview

Persona toolkit 외부 (자체 `SEditorViewport` 자손 + `FAdvancedPreviewScene` 안 `UDebugSkelMeshComponent` 직접 호스트) 에서 scrub-driven preview (Timeline scrub frame → mesh pose 갱신) 구현 시:

```cpp
// ❌ Anti-pattern — silent fail (빌드 OK, 에러 0, 그러나 mesh 정지)
PreviewMeshComponent->SetSkeletalMesh(...);
PreviewMeshComponent->SetAnimationMode(EAnimationMode::AnimationSingleNode);
PreviewMeshComponent->SetAnimation(Montage);
PreviewMeshComponent->Stop();                              // = SetPlaying(false)
PreviewMeshComponent->SetPosition(Time, /*bFireNotifies=*/false);  // 시간만 갱신, pose 미갱신
```

`SetPosition` 은 `AnimSingleNodeInstanceProxy.CurrentTime` 만 set — pose 재평가는 별도 Tick 경유 의무.

##### 2.4.1.2 Engine 권위 — Editor world Tick 분기

`SkeletalMeshComponent.cpp` L1682 + L1718:
```cpp
bool ShouldUpdateTransform(bool bLODHasChanged) const
{
    if (GetWorld()->WorldType == EWorldType::Editor) {
        if (bUpdateAnimationInEditor) return true;
        return bLODHasChanged;                          // ← default false 시 SKIP
    }
}

bool ShouldTickPose() const
{
    if (GetWorld()->WorldType == EWorldType::Editor) {
        if (bUpdateAnimationInEditor) return true;
    }
}
```

⚠ **함정**: `FAdvancedPreviewScene` 기본 WorldType = **`EWorldType::EditorPreview`** (Editor 아님) → 위 분기 미진입 → `bUpdateAnimationInEditor` 플래그 무효한 경우 있음.

##### 2.4.1.3 ⭐⭐⭐ 표준 패턴 — Slate Tick override 3축 명시

```cpp
// .h
class SMyPreviewSceneViewport : public SEditorViewport
{
public:
    virtual void Tick(const FGeometry&, const double InCurrentTime, const float InDeltaTime) override;
};

// .cpp
void SMyPreviewSceneViewport::Tick(const FGeometry& AllottedGeometry,
                                    const double InCurrentTime,
                                    const float InDeltaTime)
{
    // ⭐ 1축 — Slate base Tick (SCompoundWidget 자손 의무)
    SEditorViewport::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

    // ⭐ 2축 — Preview World 전체 tick (Light/Sky/Floor + 모든 component)
    if (PreviewScene.IsValid() && PreviewScene->GetWorld())
    {
        PreviewScene->GetWorld()->Tick(LEVELTICK_All, InDeltaTime);
    }

    // ⭐ 3축 — AnimInstance 명시 tick (SetPosition 이후 pose 재평가 보장)
    if (PreviewMeshComponent)
    {
        PreviewMeshComponent->TickAnimation(InDeltaTime, /*bNeedsValidRootMotion=*/false);
    }
}
```

##### 2.4.1.4 각 축 역할 매트릭스

| 축 | API | 효과 |
| -- | -- | -- |
| 1 | `SEditorViewport::Tick` (= `SCompoundWidget::Tick`) | Slate framework 가 매 frame 자동 호출 — override 진입점 |
| 2 | `UWorld::Tick(LEVELTICK_All, DeltaTime)` | Preview World 의 모든 actor/component tick — light/sky/floor 시각 일관성 |
| 3 | `USkeletalMeshComponent::TickAnimation(DeltaTime, false)` | AnimInstance 명시 tick → `Proxy.CurrentTime` 기반 pose evaluate → mesh 시각 갱신 |

##### 2.4.1.5 Fallback — `SetUpdateAnimationInEditor(true)` (보조)

```cpp
#if WITH_EDITOR
    PreviewMeshComponent->SetUpdateAnimationInEditor(true);
#endif
```

**한계**:
- `EWorldType::Editor` 분기에 의존 — `EditorPreview` WorldType 시 무효
- 암묵적 동작 — explicit 검증 어려움

**권장**: Tick override 가 1순위. `SetUpdateAnimationInEditor` 는 보조 (양쪽 적용 — defense-in-depth).

##### 2.4.1.6 Persona scrub 표준 비교

`SAnimationScrubPanel.cpp` L385 + L760-790:
- Persona 는 `SetPlaying(false) + SetPosition(NewValue, bFireNotifies)` 만 호출
- Persona toolkit 내부 PreviewScene Tick path 가 World tick + AnimInstance tick 자동 보장
- **자체 SEditorViewport 자손에서는 본 path 가 없음 → 명시 호출 의무**

##### 2.4.1.7 KMCProject 검증 (Phase 5a, 2026-05-19)

```
SMCComboPreviewSceneViewport (자체 SEditorViewport 자손)
   ↓ Timeline scrub drag
SyncToScrubFrame → SetPosition(LocalSeconds, false)
   ↓ ❌ 1차: Tick override 없음 → silent fail
   ↓ ✅ 2차: Tick override 3축 명시 → pose 실시간 갱신
빌드 + 동작 검증 통과 ✅
```

log: `[2026-05-19] fix | MCComboEditor Phase 5a hotfix — Editor PreviewMesh scrub silent fail`.

cross-link: [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] (일반화 페이지) + [[synthesis/mc-combo-editor-levelsequence-lite]] §Phase 5a (case study).

### 2.5. ⭐ OnAssetEditorOpened delegate (2026-05-13) 🟢

`UAssetEditorSubsystem::OnAssetEditorOpened()` — 모든 자산 열림 시. KMCProject Phase 2a focus 추적 검증.

### 2.6. 활용 시나리오

- Animation Preview 자동화 / Cloth 디버그 / Skeleton 검증
- 별도 도킹 탭 추가 (Phase 2)
- Persona Window 메뉴 항목 (§2.7)
- ⭐ **Preview Mesh 본 회전 적용 (§2.7.11) — Hit Curve Preview**
- ⭐⭐⭐ **자체 PreviewScene 안 scrub-driven preview (§2.4.1) — Sequencer-lite editor**
- Editor Automation

### 2.7. ⭐⭐⭐ FPersonaModule::OnRegisterTabs delegate — Window 메뉴 추가 표준 (2026-05-14) 🟢

#### 2.7.1 배경

Persona toolkit (5 모드) Window 메뉴 = **TabManager 자체 시스템** (ToolMenus 가 *아님*).

#### 2.7.2 시그니처

```cpp
// PersonaModule.h L70 + L550
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnRegisterTabs,
    FWorkflowAllowedTabSet&, TSharedPtr<FAssetEditorToolkit>);

class FPersonaModule { FOnRegisterTabs& OnRegisterTabs(); };
```

#### 2.7.3 5 Persona 모드 호출 (검증)

SkeletalMeshEditorMode L120 / SkeletonEditorMode L111 / AnimationEditorMode L125 / AnimationBlueprintEditorMode L203 / AnimationBlueprintInterfaceEditorMode L93. delegate 1회 = 5 모드 모두 적용.

#### 2.7.4 표준 적용 패턴

```cpp
void FMyEditorModule::StartupModule()
{
    FPersonaModule& PersonaModule = FModuleManager::LoadModuleChecked<FPersonaModule>("Persona");
    OnRegisterTabsHandle = PersonaModule.OnRegisterTabs().AddStatic(&OnRegisterTabs);
}

void FMyEditorModule::OnRegisterTabs(FWorkflowAllowedTabSet& TabFactories,
                                     TSharedPtr<FAssetEditorToolkit> Toolkit)
{
    if (Toolkit->GetToolkitFName() != FName(TEXT("SkeletalMeshEditor"))) return;
    TabFactories.RegisterFactory(MakeShared<FMyTabFactory>(Toolkit));
}
```

#### 2.7.5 FWorkflowTabFactory 자손 — 6요소 표준 ⭐⭐⭐

🚨 **6요소 누락 0 의무** (Engine `FMorphTargetTabSummoner` 미러):

```cpp
TabLabel = LOCTEXT(...);             // 1
TabIcon = FSlateIcon(...);           // 2
EnableTabPadding();                  // 3 ⭐ 누락 시 메뉴 미표시 (함정 7)
bIsSingleton = true;                 // 4 정확한 멤버명 (bIsSingleInstance X)
ViewMenuDescription = LOCTEXT(...);  // 5
ViewMenuTooltip = LOCTEXT(...);      // 6
```

CreateTabBody — `Toolkit->GetObjectsCurrentlyBeingEdited()` public API (§2.7.9).

#### 2.7.6 Build.cs 의존

```csharp
"UnrealEd", "Persona", "SkeletalMeshEditor", "PropertyEditor", "Slate", "SlateCore"
// FWorkflowTabFactory / FWorkflowAllowedTabSet = UnrealEd 모듈
// + Phase 5 추가: "AnimGraphRuntime" (FAnimNode_ModifyBone — §2.7.11)
```

#### 2.7.7 결정 가이드

```
Persona toolkit 항목 추가 위치?
├── Window 메뉴 → FPersonaModule::OnRegisterTabs
├── Asset 메뉴 글로벌 → ToolMenus MainFrame.MainMenu.Asset
├── Toolbar → ExtendToolbar()
└── 글로벌 Nomad Tab → FGlobalTabmanager (ETabSpawnerMenuType::Default)
```

#### 2.7.8 4가지 Persona 통합 패턴 매트릭스

| 패턴 | API | 표시 위치 |
| -- | -- | -- |
| A. Nomad Tab | RegisterNomadTabSpawner | Standalone / 호스트 메뉴 |
| B. ToolMenus MainFrame | UToolMenus::ExtendMenu | 메인 윈도우 |
| ⭐ **C. OnRegisterTabs** | FPersonaModule::OnRegisterTabs | Persona Window 메뉴 자동 |
| D. PluginEditor | (자체 ApplicationMode) | 별도 Mode |

#### 2.7.9 ⭐ FAssetEditorToolkit 외부 모듈 접근 API — protected vs public (2026-05-14)

| API | 가시성 | 외부 모듈 |
| -- | -- | -- |
| ⭐ `GetObjectsCurrentlyBeingEdited()` | public (L154) | ✅ nullable 포인터 |
| `GetEditingObject()` / `GetEditingObjects()` / `GetEditingObjectPtrs()` | protected | ❌ 자손 toolkit 만 |
| `GetToolkitFName()` | public | ✅ 분기용 |

KMCProject 검증 — C2248 protected 에러 → `GetObjectsCurrentlyBeingEdited()` 표준.

#### 2.7.10 ⭐ Editor Layout cache 잔재 함정 (2026-05-14)

`Saved/Config/WindowsEditor/EditorLayout.ini` stale → 신규 TabFactory 등록되어도 첫 실행 메뉴 미표시. **Window > Reset Layout** 또는 INI 파일 삭제.

#### 2.7.11 ⭐⭐⭐ UAnimPreviewInstance::ModifyBone PoseModifier 표준 (2026-05-14 신규) 🟢

##### 2.7.11.1 배경 — Preview Mesh 본 회전 적용

Persona Preview Mesh 안 본 회전을 *런타임 적용* (예: Hit Bone Curve preview) 시:
- AnimInstance 가 매 tick 본 회전 override → 우리 SetBoneRotation 효과 사라짐
- 정답: **`UAnimPreviewInstance::ModifyBone(BoneName)`** PoseModifier 시스템 — AnimGraph evaluation *이후* 적용. 유지됨.

##### 2.7.11.2 표준 패턴 (Engine `SkeletonSelectionEditMode.cpp` L309)

```cpp
#include "AnimPreviewInstance.h"                  // AnimGraph 모듈
#include "BoneControllers/AnimNode_ModifyBone.h"  // AnimGraphRuntime 모듈
#include "Animation/DebugSkelMeshComponent.h"

if (UDebugSkelMeshComponent* Mesh = PreviewMesh)
{
    // ⭐ 변수 이름 `_PreviewInstance` underscore prefix — UE `#define PI` 매크로 회피 (§2.7.12)
    if (auto* _PreviewInstance = Mesh->PreviewInstance.Get())
    {
        FAnimNode_ModifyBone& SkelControl = _PreviewInstance->ModifyBone(BoneName);
        SkelControl.Rotation = NewRotation;     // FRotator
        SkelControl.Translation = NewTrans;     // FVector (선택)
        SkelControl.Scale = NewScale;           // FVector (선택)
    }
}

// Reset — 본 ref pose 복원
if (auto* _PreviewInstance = Mesh->PreviewInstance.Get())
{
    _PreviewInstance->RemoveBoneModification(BoneName);
}
```

##### 2.7.11.3 Build.cs 의존 추가 — AnimGraphRuntime

```csharp
PublicDependencyModuleNames.AddRange(new[] {
    // ... 기존 ...
    "AnimGraph",                  // UAnimPreviewInstance (Editor)
    "AnimGraphRuntime",           // ⭐ FAnimNode_ModifyBone (BoneControllers/AnimNode_ModifyBone.h)
    // ...
});
```

##### 2.7.11.4 multi-bone preview 패턴 (KMCProject Phase 5)

```cpp
// 매 tick (Slate ActiveTimer 또는 컴포넌트 Tick)
for (const FName& BoneName : PreviewActiveBones)
{
    const FMCHitBoneAdditiveCurve* Entry = FindEntryByBone(BoneName);
    if (!Entry || !Entry->RotationCurves) continue;

    if (PreviewElapsed < Entry->Duration)
    {
        // 활성 — sample + apply
        const FRotator NewRot = Entry->SampleAtTime(PreviewElapsed, HitDir).GetRotation().Rotator();
        FAnimNode_ModifyBone& SkelControl = _PreviewInstance->ModifyBone(BoneName);
        SkelControl.Rotation = NewRot;
    }
    else
    {
        // 본 만료 — 그 본만 reset (다른 본 계속)
        _PreviewInstance->RemoveBoneModification(BoneName);
    }
}
```

##### 2.7.11.5 함정 — `UCLASS(MinimalAPI)` + 변수 이름 매크로 충돌

`UAnimPreviewInstance` 는 `UCLASS(MinimalAPI)` (AnimPreviewInstance.h L163) — class export 제한. 다만:
- `auto*` 또는 `UAnimPreviewInstance*` type 명시 모두 *forward decl* 만으로 작동 가능 (메서드 호출 시 complete type 필요)
- 진짜 함정 = **변수 이름** — `auto* PI = Mesh->PreviewInstance` 안 `PI` 가 UE `#define PI` 매크로 치환 → C2059 (vault [[sources/ue-coreuobject-uobject]] §2.12 + [[sources/mc-asset-validation-policy]] §12)

⭐ **vault 자체 평가** (2026-05-14) — 1차 진단 (MinimalAPI 가설) 잘못 → 사용자 root cause 진단 (PI 매크로) → `_PreviewInstance` 변수 이름 변경 → 빌드 통과 + Phase 5 multi-bone preview 검증.

##### 2.7.11.6 KMCProject 검증 (Phase 5, 2026-05-14)

```
SMCHitBoneCurveEditor.cpp — UAnimPreviewInstance::ModifyBone PoseModifier 패턴
   ↓ multi-bone preview 적용
빌드 통과 + Persona Preview Mesh 안 본 다중 동시 회전 ✅
   ↓ max(Duration) 도달
모든 본 자동 reset + Timer stop ✅
```

log: `[2026-05-14] verify | Phase 5 multi-bone Preview 검증 완료`.

##### 2.7.11.7 vs USkeletalMeshComponent 표준 API 비교

| API | 가시성 | AnimInstance override 영향 | 권장 |
| -- | -- | -- | -- |
| ⭐ **`UAnimPreviewInstance::ModifyBone`** | public + UE_API export | ✅ PoseModifier — AnimGraph 이후 적용, 유지됨 | ⭐⭐⭐ Persona Preview 표준 |
| `USkeletalMeshComponent::SetBoneRotationByName` | public | ⚠ AnimInstance 매 tick override 가능 | 🟡 fallback (Persona 외 런타임) |

→ **Persona Preview 안 본 회전 = ModifyBone PoseModifier 표준 의무**.

### 2.8. KMCProject 검증 사례 매트릭스 (2026-05-13 ~ 2026-05-19)

| KMCProject 항목 | 본 페이지 § | 검증 결과 |
| -- | -- | -- |
| C1083 IAssetEditorInstance.h | §2.3 함정 #3 | 🟢 (2026-05-13) |
| OnAssetEditorOpened Focus 추적 (Phase 2a) | §2.5 | 🟢 (2026-05-13) |
| Nomad Tab Spawner (Phase 2 — 불완전) | §2.6 | 🟢 (Cycle 5b 에서 fix) |
| SMCBindingsListWidget Tab Spawner (이전) | §2.6 | 🟢 |
| ⭐⭐⭐ 5 후보 ToolMenus 경로 stub | §2.7.1 | 🟢 (2026-05-14) |
| Cycle 5b OnRegisterTabs 적용 | §2.7.4 | 🟢 (2026-05-14) |
| ⭐ bIsSingleton + GetObjectsCurrentlyBeingEdited | §2.7.5 + §2.7.9 | 🟢 빌드 (2026-05-14) |
| ⭐⭐⭐ EnableTabPadding + Layout cache fix | §2.7.5 + §2.7.10 | 🟢 메뉴 표시 (2026-05-14) |
| ⭐⭐⭐ Phase 5 UAnimPreviewInstance::ModifyBone multi-bone preview | §2.7.11 | ✅ 사용자 검증 완료 (2026-05-14) |
| ⭐⭐⭐ **Phase 5a scrub-driven preview Tick 3축 명시** | §2.4.1 | ✅ **사용자 검증 완료 (2026-05-19)** |

## 3. 함정 (11대) 🟢🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `GetPreviewMeshComponent()` 반환 = USkeletalMeshComponent 추측 | UDebugSkelMeshComponent (자손) |
| 2 | AnimationBlueprintEditor 등도 같은 패턴 추측 | EditorName 검증 + 별도 인터페이스 (OnRegisterTabs delegate 만 5 모드 공통) |
| 3 | Persona Toolkit lifetime = ISkeletalMeshEditor 동등 | TSharedRef — IsValid 검사 |
| **4** ⭐ | `#include "IAssetEditorInstance.h"` C1083 | Forward decl + 위 헤더 (§2.3) |
| **5** ⭐⭐⭐ | Persona Window 메뉴를 ToolMenus 로 시도 → 영원히 stub | `FPersonaModule::OnRegisterTabs` + FWorkflowTabFactory (§2.7) |
| **6** ⭐ | 외부 모듈 `Toolkit->GetEditingObjects()` C2248 | `GetObjectsCurrentlyBeingEdited()` public (§2.7.9) |
| **7** ⭐⭐⭐ | `EnableTabPadding()` 누락 → 메뉴 미표시 | 6요소 표준 미러 (§2.7.5) |
| **8** ⭐⭐ | Editor Layout cache 잔재 → 첫 실행 메뉴 미표시 | Window > Reset Layout (§2.7.10) |
| **9** ⭐⭐⭐ | Persona Preview Mesh 본 회전을 SetBoneRotationByName 만 사용 → AnimInstance 매 tick override | `UAnimPreviewInstance::ModifyBone(BoneName).Rotation = Rot` PoseModifier (§2.7.11) |
| **10** ⭐⭐⭐ **신규** | **`UDebugSkelMeshComponent` scrub-driven preview — `SetPosition` 만 호출 → silent fail (시간만 갱신, pose 미갱신)** | **Slate `Tick` override 안 3축 명시: `SEditorViewport::Tick` + `World->Tick(LEVELTICK_All)` + `TickAnimation` (§2.4.1)** |
| **11** ⭐⭐ **신규** | **`SetUpdateAnimationInEditor(true)` 만 의존 → FAdvancedPreviewScene 의 `WorldType=EditorPreview` 분기 미진입 시 무효** | **Tick override 우선, 플래그는 보조 fallback (§2.4.1.5)** |

## 4. Cross-link

### Sub-skill

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-asseteditorapi]]
- 페어: [[sources/ue-editor-unrealed-asseteditortoolkit]] · [[sources/ue-editor-staticmesheditor]] · [[sources/ue-editor-advancedpreviewscene]] · [[sources/ue-editor-eventbinding]]
- ⭐⭐⭐ ToolMenus 페어: [[sources/ue-editor-toolmenus]] §2.9

### KMCProject MC-시리즈 사례 (2026-05-13 ~ 2026-05-19)

- [[synthesis/instanced-subobject-customization-bypass]] §4.3 — Tab Spawner Persona 통합
- [[synthesis/mc-character-hit-reaction-pipeline]] §6 + §6.5 + §6.7 — UMCHitBoneCurveUserData Phase 1+2+4+5 통합 + 함정 12 (PI 매크로)
- ⭐ [[synthesis/mc-combo-editor-levelsequence-lite]] §Phase 5a — KMCProject MCComboEditor scrub-driven preview Tick 3축 (2026-05-19)
- ⭐⭐⭐ [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] — 신규 일반화 페이지 (2026-05-19)

### 횡단 정책 + 매크로 함정 cross-link

- [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-04-overrideindex]] §2.5 · [[sources/ue-ref-07-profilingscopeRule]]
- ⭐ **변수 이름 회피 규약**: [[sources/ue-coreuobject-uobject]] §2.12 (UE 글로벌 매크로 11종) + [[sources/mc-asset-validation-policy]] §12 (KMCProject 채용 규약)

### Cycle 5l reverse-link 보강 (suggest_missing 결과)

- ⭐ [[synthesis/mc-combo-editor-levelsequence-lite]] (KMCProject MCComboEditor — FPersonaModule 페어 + Workflow 4단 분리 4회 인용)
- [[sources/ue-assetclasses-assetuserdata]] (UAssetUserData 통한 Persona 별도 탭 자산 — Phase 4 통합)

### 관련 fix / feature log (KMCProject 2026-05-13 ~ 2026-05-19)

- `feature | UMCHitBoneCurveUserData Phase 2+2a+2b — Persona 별도 도킹 탭 + Focus + IStructureDetailsView`
- `fix | MCHitBoneCurveEditorMenu.cpp C1083`
- ⭐⭐⭐ `[2026-05-14] fix | Cycle 5b — Persona Window 메뉴 = TabManager 자체 시스템 발견`
- ⭐ `[2026-05-14] fix | Cycle 5b 빌드 fix — bIsSingleton + GetObjectsCurrentlyBeingEdited`
- ⭐⭐⭐ `[2026-05-14] fix | Cycle 5b 메뉴 미표시 fix — EnableTabPadding + Layout cache 2단`
- ⭐ `[2026-05-14] fix | ⚠ 자체 평가 정정 — Phase 5 C2059 진짜 원인 = UE PI 매크로` (§2.7.11.5)
- ⭐⭐⭐ `[2026-05-14] verify | Phase 5 multi-bone Preview 검증 완료` (§2.7.11 1차 검증)
- ⭐⭐⭐ **`[2026-05-19] fix | MCComboEditor Phase 5a hotfix — Editor PreviewMesh scrub silent fail (Tick override 명시)` (§2.4.1)**

## 5. 후속 검증 후보

- [ ] §2.7.5 IPersonaToolkit::GetMesh/GetSkeleton/GetAnimationAsset Persona 모드별 분기 매트릭스
- [ ] FBlueprintEditorModule OnRegisterTabs (🔴 INFERRED)
- [ ] §2.7.9 다른 toolkit API protected/public 검증
- [ ] §2.7.10 layout schema 버전 변경 시 cache invalidation 자동화
- [ ] §2.7.11 ModifyBone 외 PoseModifier — `RemoveBoneModification` / `ResetModifiedBone` / `ApplyBoneControllers` 헬퍼 사용 매트릭스 (🟡 INFERRED)
- [ ] §2.7.11 Phase 5 HitDirection UI dropdown (Front/Back/Left/Right) 추가 시 PoseModifier 호출 패턴
- [ ] §2.4.1 `PreviewScene->GetWorld()->Tick` vs `FPreviewScene::Tick` (FPreviewScene 가 자체 Tick override 보유 시 중복 호출 위험) — Engine source 확인 후 분기
- [ ] §2.4.1 LEVELTICK_All vs LEVELTICK_TimeOnly vs LEVELTICK_ViewportsOnly 선택 기준
