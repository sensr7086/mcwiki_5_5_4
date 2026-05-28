---
type: source
title: "UE Editor — PropertyEditor sub-skill (디테일 패널 커스터마이징) 🛠"
slug: ue-editor-propertyeditor
source_path: raw/ue-wiki-llm/skills/Editor/references/PropertyEditor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-14
related_entities:
  - "[[entities/IDetailCustomization]]"
  - "[[entities/FProperty]]"
  - "[[entities/SWidget]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, editor, propertyeditor, details, customization, idetailcustomization, ipropertytypecustomization, tsharedfromthis-pitfall, instancedsubobject-pitfall, asseteditor-layout-bypass, istructuredetailsview-recreation, scurveeditor-dangling]
citation_disclosure: "함정 1 PostEditUndo + 함정 9 + 함정 10 (차원 1+2 + 우회 c 완전) + 함정 11 SCurveEditor dangling = 🟢 KMCProject + 외부 에이전트 실측 / 일반 UCLASS root 우회 (b) = 🟡 / 다른 자산 에디터 + Instanced TObjectPtr 임의 UCLASS = 🔴 INFERRED. 상세 = [[synthesis/instanced-subobject-customization-bypass]] / [[synthesis/mc-character-hit-reaction-pipeline]] §6"
---

# UE Editor — PropertyEditor sub-skill (디테일 패널 커스터마이징) 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/PropertyEditor.md]] · 16 KB · 68 Public 헤더
>
> **Citation 마커** ([[00_meta/06_VaultCitationRule]]): 🟢 검증 / 🟡 외삽 / 🔴 INFERRED.
>
> 보강 2026-05-14 — §2.8 신규 (IStructureDetailsView + SCurveEditor dangling pointer 함정 + SBox 재생성 패턴)

## 1. Summary

UE 에디터의 **디테일 패널**. **두 가지 customization**: (1) **클래스 단위** `IDetailCustomization` — root UCLASS 디테일 패널 재배치. (2) **타입 단위** `IPropertyTypeCustomization` — USTRUCT/UPROPERTY 타입 표시 변경 (어디서나 호출).

🚨 어셋 로드 = Editor 순수 모드 동기 — [[sources/ue-ref-11-assetloadingpolicy]] §3.
🚨 **`RegisterCustomClassLayout` 은 root 만 발화 — InstancedSubobject 자손 등록 X + 자산 에디터 부모 등록도 layout delegate 강제 우회 X** (§2.6 함정 10, 상세 = [[synthesis/instanced-subobject-customization-bypass]]).
🚨 **§2.8 IStructureDetailsView::SetStructureData 만으로 내부 SCurveEditor 자식 재생성 X — FRichCurve* 캐시 stale → 0xFFFFFFFFFFFFFFFF crash** (2026-05-14 KMCProject 검증).

## 2. Key claims

### 2.1. 68 헤더 카테고리

| 카테고리 | 핵심 헤더 |
| -- | -- |
| Customization (8) | `IDetailCustomization.h` / `IPropertyTypeCustomization.h` / `IDetailRootObjectCustomization.h` / `IDetailDragDropHandler.h` / `IDetailKeyframeHandler.h` 등 |
| Builder | `IDetailLayoutBuilder.h` / `IDetailChildrenBuilder.h` / `IDetailCustomNodeBuilder.h` / `DetailCategoryBuilder.h` / `DetailWidgetRow.h` |
| Property Handle | `PropertyHandle.h` (`IPropertyHandle`) |
| Details View | `IDetailsView.h` / `DetailsViewArgs.h` / `IDetailTreeNode.h` |
| **Structure Details View** ⭐ | **`IStructureDetailsView.h`** — USTRUCT instance 직접 detail 표시 (UObject 없이) |
| Single Property | `ISinglePropertyView.h` |
| Row Generator | `IPropertyRowGenerator.h` |
| Property Table (10+) | `IPropertyTable*.h` |
| Editor Conditions | `EditConditionParser.h` |

### 2.2. FPropertyEditorModule 핵심 API

- `RegisterCustomClassLayout(FName, FOnGetDetailCustomizationInstance, FRegisterCustomClassLayoutParams)` — 클래스 단위. **root 만 발화** (§2.6 함정 10). **자산 에디터 안에선 layout delegate 강제 우회 가능** (외부 실증).
- `RegisterCustomPropertyTypeLayout(FName, FOnGetPropertyTypeCustomizationInstance, TSharedPtr<IPropertyTypeIdentifier>)` — 타입 단위. **모든 위치 호출**.
- `CreateDetailView(const FDetailsViewArgs&)` — `IDetailsView` 생성 (UObject 대상).
- `CreateStructureDetailView(const FDetailsViewArgs&, const FStructureDetailsViewArgs&, TSharedPtr<FStructOnScope>, FText)` — ⭐ **`IStructureDetailsView`** 생성 (USTRUCT instance 대상, FStructOnScope wrap).
- `Unregister*` 페어 — Module Shutdown 의무.

### 2.3. 등록 표준 패턴

```cpp
#if WITH_EDITOR
FPropertyEditorModule& PE = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
PE.RegisterCustomClassLayout(UMyAsset::StaticClass()->GetFName(),
    FOnGetDetailCustomizationInstance::CreateStatic(&FMyAssetCustomization::MakeInstance));
PE.RegisterCustomPropertyTypeLayout(FMyStruct::StaticStruct()->GetFName(),
    FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FMyStructCustomization::MakeInstance));
PE.NotifyCustomizationModuleChanged();
#endif
```

### 2.4. IDetailCustomization vs IPropertyTypeCustomization

| 항목 | IDetailCustomization | IPropertyTypeCustomization |
| -- | -- | -- |
| 단위 | UCLASS 전체 | USTRUCT / UPROPERTY 타입 |
| 진입 | `CustomizeDetails(IDetailLayoutBuilder&)` | `CustomizeHeader + CustomizeChildren` |
| 등록 | `RegisterCustomClassLayout` | `RegisterCustomPropertyTypeLayout` |
| **발화 위치** ⭐ | **root object 만**. **자산 에디터 안에선 layout delegate 강제 우회** (함정 10) | **모든 곳** — root/inner/array element/InstancedSubobject 자식 |

### 2.5. IPropertyHandle 핵심

- `GetValue` / `SetValue` (자동 NotifyPre/PostChange + Modify) — Undo 자동
- `GetChildHandle(FName)` / `GetNumChildren` — 트리 탐색
- `NotifyPreChange` / `NotifyPostChange` — 직접 쓰기 시 수동 페어
- `CreatePropertyNameWidget` / `CreatePropertyValueWidget`

### 2.6. 함정 매트릭스 (11건)

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `Modify()` 호출 누락 → Undo X / **PostEditUndo override 누락 → UI 구독자 자동 갱신 X** | `NotifyPreChange/NotifyPostChange` 페어 + **`virtual void PostEditUndo() override { Super::PostEditUndo(); OnXChanged.Broadcast(GetOuter()); }` + UI 위젯이 정적 멀티캐스트 SP 구독 → Undo/Redo 시 자동 갱신** (synthesis §4.3.4 P3-C 패턴) |
| 2 | `CustomizeDetails` 안 비동기 콜백 | Editor 순수 모드 = Sync — [[sources/ue-ref-11-assetloadingpolicy]] §3 |
| 3 | Customization 해제 누락 | `ShutdownModule` 안 `Unregister*` 페어 |
| 4 | `CreateRaw(this, ...)` → destruction race | `CreateStatic` (factory) / `CreateSP` (TSharedRef) |
| 5 | `SetValueData` 후 NotifyPost 미호출 | 수동 `NotifyPreChange/PostChange/FinishedChangingProperties` |
| 6 | `CreateSingleProperty` 후 Pin 미보관 | 멤버로 보관 |
| 7 | `IDetailRootObjectCustomization` 미사용 | Multi-Object Edit 시 보강 |
| 8 | `EditConditionParser` 미사용 | 동적 EditCondition 표현식 |
| **9** ⭐ | `IDetailCustomization` 자손에 `TSharedFromThis<DerivedT>` 중복 상속 → **C2385** | 자식 TSharedFromThis 제거 + `AsSelf()` 헬퍼 (§2.6.9) |
| **10** ⭐⭐⭐ | `RegisterCustomClassLayout` 발화 X — 2 차원: (a) InstancedSubobject 안 자손 등록 (b) 자산 에디터 안 부모 등록 (layout delegate 강제 우회) | 우회 (a) `RegisterCustomPropertyTypeLayout` USTRUCT / (b) Tab Spawner / (c) DataAsset 분리 — 상세 = [[synthesis/instanced-subobject-customization-bypass]] |
| **11** ⭐⭐⭐ | **`IStructureDetailsView::SetStructureData(NewScope)` 만으로 내부 SCurveEditor 자식 위젯 재생성 X → FRichCurve* 캐시 stale → 메모리 이동 (TArray reallocation) 후 0xFFFFFFFFFFFFFFFF crash** | §2.8 — SBox 컨테이너 + IStructureDetailsView **매번 재생성** + SetContent swap |

#### 2.6.9 함정 9 — `TSharedFromThis` 중복 상속 (C2385)

```cpp
// ❌ class FMyDetails : public IDetailCustomization, public TSharedFromThis<FMyDetails>  // C2385
// ✅ class FMyDetails : public IDetailCustomization
//    {
//        TSharedRef<FMyDetails> AsSelf()
//        {
//            return StaticCastSharedRef<FMyDetails>(AsShared());
//        }
//    };
// 콜백: CreateSP(AsSelf(), &FMyDetails::OnX) / Lambda: [WeakSelf=TWeakPtr<FMyDetails>(AsSelf())]
```

**적용 범위** (3 tier):

| 클래스 | 위험 | 검증 |
| -- | -- | -- |
| `IDetailCustomization` (베이스 `TSharedFromThis<IDetailCustomization>`) | ⚠️ 다이아몬드 | **🟢** KMCProject C2385 검증 + **🟢 외부 evaluator 자체가 권고 → C2385 사례** ([[sources/ue-agent-evaluator]] self-correction 대상) |
| `IPropertyTypeCustomization` / `IDetailCustomNodeBuilder` / `IAssetTypeActions` | 베이스 없음 | 🔴 INFERRED |

> 🟢 시그널: C2385 + note 가 두 `TSharedFromThis<T>::SharedThis` (또는 `AsShared`) 가리킴 = 다이아몬드 상속.

#### 2.6.10 함정 10 — `RegisterCustomClassLayout` 미발화 (2 차원) ⭐⭐⭐

**차원 1 — InstancedSubobject 자손 등록** (🟢 KMCProject 실측):

```cpp
// ❌ UStaticMesh::AssetUserData 안의 UMCNiagaraSocketBindings 자손 등록
PropertyModule.RegisterCustomClassLayout(
    UMCNiagaraSocketBindings::StaticClass()->GetFName(), ...);
// → MakeInstance / CustomizeDetails 둘 다 발화 X
```

**차원 2 — 자산 에디터 안 부모 root 등록** (🟢 외부 에이전트 7가지 시도 무위로 실증):

```cpp
// ❌ UStaticMesh root 등록도 SM Editor 의 SetGenericLayoutDetailsDelegate 강제 우회
PropertyModule.RegisterCustomClassLayout(
    UStaticMesh::StaticClass()->GetFName(), ...);
// → MakeInstance / CustomizeDetails 둘 다 발화 X
// 7가지 회피 시도 모두 무위: GetEditorName / 자동 spawn / PostEditChange override /
//                          LoadingPhase 변경 / OnAssetEditorOpened hook /
//                          GEditor 지연 init / 진단 로그 (마지막은 진단 성공만)
```

**진단 절차**:

```cpp
TSharedRef<IDetailCustomization> FMy::MakeInstance() {
    UE_LOG(LogTemp, Warning, TEXT("[MakeInstance] called")); return MakeShared<FMy>();
}
void FMy::CustomizeDetails(IDetailLayoutBuilder&) {
    UE_LOG(LogTemp, Warning, TEXT("[CustomizeDetails] called"));
}
// 에디터 재시작 후 둘 다 호출 X → 차원 1 또는 2 진단 확정.
```

**우회 4종 + 상세 코드 + 적용 범위 + KMCProject + 외부 에이전트 사례** = ⭐ **[[synthesis/instanced-subobject-customization-bypass]]**.

함정 10 발생 매트릭스 요약 (검증 출처별):

| 등록 대상 | 컨테이너 | 검증 |
| -- | -- | -- |
| 자손 (InstancedSubobject) | `UStaticMesh.AssetUserData` 안 `UMCNiagaraSocketBindings` | 🟢 KMCProject 실측 |
| 부모 root (자산 에디터 있음) | `UStaticMesh` 직접 | 🟢 외부 에이전트 Journey Phase 5 (7가지 시도 무위) |
| 부모 root (자산 에디터 없음, 일반 UCLASS) | `UMyAsset` 직접 | 🟡 정상 발화 (vault §2.4 표준) |
| 다른 자산 에디터 (`USkeletalMesh` / `UMaterial` / `UAnimBlueprint` 등) | 부모 root 등록 | 🔴 INFERRED — layout delegate 사용 여부 미검증 |
| 임의 UCLASS Instanced TObjectPtr / UDataAsset inner / UStateTreeState | InstancedSubobject | 🔴 INFERRED |
| **우회 (c) Tab Spawner Nomad 탭 패턴** (자산 에디터 layout delegate 회피) | UMCNiagaraSocketBindings + SDockTab + SListView | **🟢 KMCProject 완전 실증 (P1+P2+P3 + Undo)** — [[synthesis/instanced-subobject-customization-bypass]] §3 + §4.3 |

### 2.7. Editor 4단 분리 의무

`WITH_EDITOR` 가드 + Build.cs Editor 모듈만 `PropertyEditor` 의존 + Runtime 모듈에 PropertyEditor 의존 X.

### 2.8. ⭐⭐⭐ IStructureDetailsView 함정 — SCurveEditor dangling pointer (2026-05-14 추가) 🟢

#### 2.8.1 배경

`IStructureDetailsView` 는 UObject 없이 **USTRUCT instance** 만 detail 표시. `FStructOnScope` 가 USTRUCT 메모리를 wrap (소유 또는 외부 참조).

```cpp
// 표준 생성
FStructureDetailsViewArgs StructArgs;   /* bShowObjects/bShowAssets ... */
FDetailsViewArgs DetailsArgs;            /* bAllowSearch/bHideSelectionTip ... */

TSharedRef<IStructureDetailsView> View = PE.CreateStructureDetailView(
    DetailsArgs, StructArgs, MyStructOnScope, LOCTEXT("Label", "Struct"));
```

`FStructOnScope` 2가지 모드:

| 모드 | 생성자 | OwnsMemory | 사용 |
| -- | -- | -- | -- |
| 소유 | `FStructOnScope(UStruct*)` | true | 자체 메모리 할당 |
| **외부 wrap** ⭐ | `FStructOnScope(UStruct*, uint8*)` | false | 외부 메모리 가리킴 (예: `TArray<T>[Index]`) |

#### 2.8.2 함정 — SetStructureData(NewScope) 만으로 자식 위젯 재생성 X

`IStructureDetailsView::SetStructureData(NewScope)` 호출 시:

- **Property tree 데이터 포인터** 는 새 scope 로 갱신
- **그러나 자식 customization 위젯 (특히 `SCurveEditor`)** 은 *재생성 안 됨* — 기존 위젯이 보유한 raw 포인터 (`FRichCurve*` 등) 그대로 유지

⭐ **특히 `FRuntimeFloatCurve` 의 internal customization**:

```cpp
USTRUCT()
struct FRuntimeFloatCurve
{
    UPROPERTY()
    FRichCurve EditorCurveData;             // ← 내부 FRichCurve
    UPROPERTY()
    TObjectPtr<UCurveFloat> ExternalCurve;
};
```

Engine 의 `FRuntimeFloatCurveCustomization` (PropertyTypeCustomization) 이 SCurveEditor 위젯 생성 → `FRichCurve* = &MyStruct.MyCurve.EditorCurveData` 캐시.

```
1. FStructOnScope 가 BoneCurves[0] 메모리 wrap → View 가 BoneCurves[0].TranslationX 표시
2. 내부 SCurveEditor 가 FRichCurve* = &BoneCurves[0].TranslationX.EditorCurveData 캐시
3. SetStructureData(new scope wrapping BoneCurves[1]) → property tree 데이터만 갱신
4. SCurveEditor 는 그대로 → FRichCurve* 그대로 (BoneCurves[0] 메모리)
5. TArray Add/Remove → BoneCurves reallocation → 원래 메모리 freed
6. 다음 paint: SCurveEditor::OnPaint → Curve->GetNumKeys() →
   `FRealCurve* Curve = CurveViewModel->CurveInfo.CurveToEdit;` ← 0xFFFFFFFFFFFFFFFF (freed sentinel)
   → 읽기 액세스 위반 crash
```

#### 2.8.3 회피 패턴 — SBox 컨테이너 + IStructureDetailsView 매번 재생성

```cpp
// .h
class SBox;                                          // forward decl
TSharedPtr<IStructureDetailsView> EntryDetailsView;  // 매번 재생성
TSharedPtr<SBox> EntryDetailsViewBox;                // ⭐ 컨테이너 (Slate 트리에 1회 추가)
TSharedPtr<FStructOnScope> CurrentEntryScope;

// Construct
EntryDetailsViewBox = SNew(SBox);
ChildSlot
[
    // ... 다른 위젯 ...
    EntryDetailsViewBox.ToSharedRef()    // 컨테이너만 layout 에 1회 등록
];

// UpdateEntryDetailsView — 매번 호출
void FMyEditor::UpdateEntryDetailsView()
{
    if (!EntryDetailsViewBox.IsValid()) return;

    // 1. 기존 View 완전 해제 — 내부 SCurveEditor 자식도 같이 destroy
    CurrentEntryScope.Reset();
    EntryDetailsView.Reset();
    EntryDetailsViewBox->SetContent(SNullWidget::NullWidget);

    // 2. 새 데이터 검증
    FMyStruct* Entry = FindEntry();
    if (!Entry) return;

    // 3. 새 FStructOnScope + 새 IStructureDetailsView
    CurrentEntryScope = MakeShared<FStructOnScope>(
        FMyStruct::StaticStruct(),
        reinterpret_cast<uint8*>(Entry));

    FPropertyEditorModule& PE = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
    EntryDetailsView = PE.CreateStructureDetailView(
        DetailsArgs, StructArgs, CurrentEntryScope, Label);

    // 4. SBox 컨테이너에 swap
    if (EntryDetailsView.IsValid())
    {
        EntryDetailsViewBox->SetContent(EntryDetailsView->GetWidget().ToSharedRef());
    }
}
```

#### 2.8.4 회피 패턴 차이 매트릭스

| # | 패턴 | 동작 | 권장 |
| -- | -- | -- | -- |
| 1 | `SetStructureData(nullptr) → SetStructureData(NewScope)` | property tree 만 갱신, SCurveEditor 자식 캐시 그대로 | ❌ (위험 — stale FRichCurve*) |
| 2 ⭐ | SBox 컨테이너 + `IStructureDetailsView` 매번 재생성 + SetContent | 모든 자식 위젯 destroy 후 재생성 → 새 FRichCurve* 매핑 | ⭐⭐⭐ 표준 — SCurveEditor 등 customization 자식 포함 |
| 3 | TArray.Reserve(N) 큰 capacity | reallocation 자체 회피 — 정적 N 안에선 안전 | ⭐⭐ defense in depth (구조적 fix 와 페어) |
| 4 | TIndirectArray<T> 사용 | 각 원소 별도 heap alloc — 원소 주소 stable | 🟡 UPROPERTY 직렬화 비표준 — 제한적 |
| 5 | TMap<Key, T> 사용 | 내부 hash rehash 시 원소 이동 가능 | 🔴 같은 함정 — 회피 효과 X |

#### 2.8.5 KMCProject 검증 사례 (2026-05-14)

```
파일: Source/KMCProject/MCEditorModule/HitBoneCurveEditor/SMCHitBoneCurveEditor.cpp
USTRUCT: FMCHitBoneAdditiveCurve (6 FRuntimeFloatCurve 멤버 — Translation X/Y/Z + Pitch/Yaw/Roll)
컨테이너: TArray<FMCHitBoneAdditiveCurve> BoneCurves (UMCHitBoneCurveUserData::BoneCurves)

증상: Persona Hit Bone Curve Editor 열기 / Add Selected / 본 전환 시 SCurveEditor::OnPaint
       안 0xFFFFFFFFFFFFFFFF 읽기 액세스 위반.

fix:
  1. SBox EntryDetailsViewBox 추가 — Slate 트리에 1회 등록
  2. UpdateEntryDetailsView 가 IStructureDetailsView 매번 destroy + 새로 생성
  3. UMCHitBoneCurveUserData::PostInitProperties / PostLoad 가 BoneCurves.Reserve(256) — defense in depth
```

log: `[2026-05-14] fix | SCurveEditor dangling pointer (0xFFFFFFFFFFFFFFFF) — IStructureDetailsView 매번 재생성 + BoneCurves.Reserve`

#### 2.8.6 일반화 — 어떤 customization 이 이 함정에 노출?

| Customization | 내부 위젯 캐시 | 위험 |
| -- | -- | -- |
| `FRuntimeFloatCurveCustomization` | SCurveEditor → FRichCurve* | ⭐⭐⭐ 가장 흔함 |
| `FRuntimeVectorCurveCustomization` | SCurveEditor × 3 | ⭐⭐ |
| `FRuntimeCurveLinearColorCustomization` | SCurveEditor × 4 | ⭐⭐ |
| 사용자 정의 customization 안 raw 멤버 변수 (`MyStruct->Member` 캐시) | 사용자 정의 | 🟡 위험 가능 |
| 표준 IDetailsView (UObject 대상) — IStructureDetailsView X | UPROPERTY reflection 으로 매 paint 해상 | ✅ 안전 |

→ **권장**: customization 안 raw 포인터 캐시 시 *생성 시점* 의 메모리 가정 X. 매 paint 시 IPropertyHandle 로 재해상 또는 SBox + 재생성 패턴 적용.

#### 2.8.7 결정 가이드

```
대상 = UObject?
  ├── YES → IDetailsView (CreateDetailView)
  │         - UObject reflection 으로 자동 해상 — 안전
  │         - SetObject(NewObject) 시 자식 위젯 재생성 표준 동작
  └── NO  → USTRUCT instance
            ├── 메모리가 *고정* (스택 또는 GC-pinned UObject 안) → IStructureDetailsView + SetStructureData OK
            └── 메모리가 *이동 가능* (TArray<T>[Index] / TMap<K,T> 등)
                  └── SBox 컨테이너 + IStructureDetailsView **매번 재생성** + SetContent ⭐ (§2.8.3)
                      + TArray.Reserve(N) defense in depth
```

## 3. Cross-link

- 카테고리 main: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 자매 sub-skill: [[sources/ue-editor-assettools]] / [[sources/ue-editor-toolmenus]]
- 횡단 정책: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-11-assetloadingpolicy]] §3 · [[sources/ue-coreuobject-editor]]
- Slate 페어: [[sources/ue-slate-application]] / [[sources/ue-slatecore-swidget]] / [[sources/ue-slate-liststrees]] §11
- InstancedSubobject 페어: [[sources/ue-assetclasses-assetuserdata]]
- 자산 에디터 layout delegate: [[sources/ue-editor-asseteditorapi]] §3.1 EditorName 표
- 평가자 self-correction: [[sources/ue-agent-evaluator]] (함정 9 회피 의무) / [[sources/ue-meta-honest-limits]]
- ⭐ **함정 10 deep ref**: [[synthesis/instanced-subobject-customization-bypass]]
- ⭐ **함정 11 deep ref**: [[synthesis/mc-character-hit-reaction-pipeline]] §6 (Hit Curve Pipeline 안 dangling pointer fix 적용)
- ⭐ **측정**: [[sources/ue-measure-instancedsubobject-2026-05-12]] (⭐⭐ 신뢰도)
- 관련 함정 페이지: [[sources/ue-coreuobject-uobject]] §2.10 (FStructOnScope + UPROPERTY TArray reallocation 함정)
- Citation: [[00_meta/06_VaultCitationRule]]

## 4. Open questions

- [ ] `IDetailRootObjectCustomization` 5.x — Multi-Object Edit 적용
- [ ] `IPropertyRowGenerator` — 디테일 뷰 외 사용
- [ ] `EditConditionParser` 5.7.4 문법
- [ ] `AsyncDetailViewDiff` 5.x — diff UI
- [ ] `FRegisterCustomClassLayoutParams` 안 InstancedSubobject 강제 발화 hook (함정 10 우회 5번째 후보)
- [ ] **차원 2 적용 범위** — `USkeletalMesh` / `UMaterial` / `UAnimBlueprint` / `UBehaviorTree` / `UNiagaraSystem` 자산 에디터 layout delegate 우회 여부 (🔴 INFERRED, filing-back 대상)
- [ ] 함정 10 🔴 INFERRED 사이트 — Instanced TObjectPtr 임의 UCLASS / UDataAsset inner / UStateTreeState 실증
- [ ] §2.8 함정 11 일반화 검증 — `FRuntimeVectorCurve` / `FRuntimeCurveLinearColor` 동일 함정 재현 (🟡 INFERRED)
- [ ] §2.8 일반 customization 안 raw 포인터 캐시 매트릭스 — Engine source 검증

## 5. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 최초 ingest — 68 헤더 + 두 customization + IPropertyHandle + 함정 8건 |
| 2026-05-12 | 함정 9 추가 — `TSharedFromThis<DerivedT>` 중복 상속 C2385 |
| 2026-05-12 | 함정 10 추가 — InstancedSubobject 안 `RegisterCustomClassLayout` 미발화. KMCProject 실측 |
| 2026-05-12 | §2.6.9/§2.6.10 [[00_meta/06_VaultCitationRule]] 3 tier 마커 추가 |
| 2026-05-12 | **Slim 재분리** — 함정 10 상세 → synthesis. 메인 17 KB → 9 KB |
| 2026-05-12 | **함정 10 2 차원 확장** ⭐⭐⭐ — 외부 에이전트 자료 (`StaticMeshNiagaraPreview_Journey.md` Phase 5) 로 *부모 root 등록 (자산 에디터)* 도 layout delegate 강제 우회 실증. 차원 1 (자손 InstancedSubobject) + 차원 2 (자산 에디터 부모) 두 차원 매트릭스. 7가지 회피 시도 무위. 함정 9 의 외부 evaluator 권고 → C2385 사례 추가 ([[sources/ue-agent-evaluator]] self-correction). Cross-link `[[sources/ue-editor-asseteditorapi]]` §3.1 EditorName 표 + 측정 페이지 `[[sources/ue-measure-instancedsubobject-2026-05-12]]` 추가. tag `asseteditor-layout-bypass` 추가. |
| 2026-05-12 | **§2.6 함정 1 PostEditUndo 페어 보강** + **§2.6.10 우회 (c) Tab Spawner Nomad 탭 🟢 승급** — KMCProject 완전 실증 (P1 Nomad 탭 등록 + P2 SListView 본체 + P3 WeakWidget hook + Undo PostEditUndo + OnBindingsChanged SP 구독). synthesis §4.3.1~4.3.6 표준 패턴 6단 cross-link. 외부 에이전트 §Phase 6 의 "다음 단계 (미구현)" 부분을 KMCProject 가 *먼저 검증*. |
| **2026-05-14** | ⭐⭐⭐ **함정 11 + §2.8 IStructureDetailsView 매번 재생성 패턴** — KMCProject `SMCHitBoneCurveEditor` 의 SCurveEditor dangling pointer (0xFFFFFFFFFFFFFFFF) crash 검증. SBox 컨테이너 + 재생성 + SetContent + Reserve(256) defense in depth. tags `istructuredetailsview-recreation` / `scurveeditor-dangling` 추가. |
