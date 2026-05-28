---
type: source
title: "AssetClasses/AssetUserData — 자산 메타 확장 표준"
slug: ue-assetclasses-assetuserdata
source_path: raw/ue-wiki-llm/skills/AssetClasses/AssetUserData/SKILL.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-13
related_entities:
  - "[[entities/UObject]]"
related_concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, assetclasses, asset-user-data, meta, mesh, material, texture, sound, physicsasset, persona, kmcproject-verified]
---

# AssetClasses/AssetUserData — 자산 메타 확장 표준

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/AssetUserData/SKILL.md]] · `Engine/AssetUserData.h:16` (UAssetUserData) + `Interfaces/Interface_AssetUserData.h:19` (IInterface_AssetUserData)
> 보강: 2026-05-13 — KMCProject `UMCHitBoneCurveUserData` Phase 1-4 실증 사례 추가 + 함정 #9 C4264 신규 + Phase 4 IsDataValid Override 통합.

## 1. Summary

`UAssetUserData` + `IInterface_AssetUserData` — **자산 클래스 수정 없이 커스텀 데이터 첨부**. 사용자가 `UAssetUserData` 자손 작성 → 자산 (StaticMesh / SkeletalMesh / Material / Texture / Sound / PhysicsAsset / Animation 등) 의 detail 패널에서 add. 표준 자산 10+ 이미 `IInterface_AssetUserData` 구현. UCLASS 핵심 = `DefaultToInstanced` + `EditInlineNew` + `abstract`. KMCProject `UMCHitBoneCurveUserData` 가 Phase 1 (데이터 구조) → Phase 2 (Persona 별도 탭) → Phase 4 (Editor IsDataValid + Skeleton 호환성) 전 단계 검증.

## 2. Key claims

### 2.1. UAssetUserData 베이스 🟢

```cpp
// Engine/AssetUserData.h:16
UCLASS(DefaultToInstanced, abstract, editinlinenew, MinimalAPI)
class UAssetUserData : public UObject
{
    GENERATED_UCLASS_BODY()

    // Editor 디버깅용 (선택)
    virtual void Draw(class FPrimitiveDrawInterface* PDI, const class FSceneView* View) const {}
    virtual void DrawCanvas(class FCanvas& Canvas, class FSceneView& View) const {}

    // Owner 변경 시 콜백 (5.6+ 시그니처)
    virtual void PostEditChangeOwner(const FPropertyChangedEvent& PropertyChangedEvent) {}
};
```

UCLASS 매크로 의미:
- `DefaultToInstanced` — 자산 안 인스턴스화 시 자동 (포인터 X)
- `abstract` — 베이스만 — 자손 클래스 작성 의무
- `editinlinenew` — Editor 디테일 패널 안 직접 생성

### 2.2. IInterface_AssetUserData — 자산 측 인터페이스 🟢

```cpp
// Interface_AssetUserData.h:19
class IInterface_AssetUserData
{
    virtual void AddAssetUserData(UAssetUserData* InUserData) {}

    UFUNCTION(BlueprintCallable, Category=AssetUserData, meta=(DeterminesOutputType="InUserDataClass"))
    virtual UAssetUserData* GetAssetUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass);

    UFUNCTION(BlueprintCallable, Category=AssetUserData)
    virtual bool HasAssetUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass);

    virtual void RemoveUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass) {}
    virtual const TArray<UAssetUserData*>* GetAssetUserDataArray() const { return nullptr; }
};
```

자산이 본 인터페이스 구현 시 = UserData 보관 가능.

### 2.3. 이미 지원하는 자산 (5.x 표준) 🟢

| 자산 클래스 | Interface 구현 | 헤더 |
| -- | -- | -- |
| `UStaticMesh` ⭐ | ✅ | `Engine/Classes/Engine/StaticMesh.h` |
| `USkeletalMesh` ⭐ | ✅ | `Engine/Classes/Engine/SkeletalMesh.h` |
| `UMaterial` / `UMaterialInstance` | ✅ | `Engine/Classes/Materials/Material.h` |
| `UTexture` (Texture2D / Cube / 등) | ✅ | `Engine/Classes/Engine/Texture.h` |
| `USoundBase` (SoundCue / SoundWave) | ✅ | `Engine/Classes/Sound/SoundBase.h` |
| `UPhysicsAsset` | ✅ | `Engine/Classes/PhysicsEngine/PhysicsAsset.h` |
| `AWorldSettings` | ✅ | `Engine/Classes/GameFramework/WorldSettings.h` |
| `UAnimSequence` / `UAnimBlueprint` | ✅ | `Engine/Classes/Animation/AnimationAsset.h` |

추가로 Custom 자산 = `IInterface_AssetUserData` 구현 시 지원.

### 2.4. 표준 사용 패턴 — UAssetUserData 자손 작성 🟢

```cpp
// MyData.h
UCLASS(BlueprintType, DefaultToInstanced, EditInlineNew, CollapseCategories,
    meta=(DisplayName="My Custom Data"))
class MYGAME_API UMyCustomData : public UAssetUserData
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MyGame")
    FName Tag = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MyGame")
    TSoftObjectPtr<USoundBase> Sound;          // vault [[sources/ue-ref-11-assetloadingpolicy]] §2.5

#if WITH_EDITOR
    // 5.6+ 시그니처 — vault §9 함정 #5
    virtual void PostEditChangeOwner(const FPropertyChangedEvent& PropertyChangedEvent) override;

    // 5.x Editor Data Validation 시스템 통합 — vault §9 함정 #9 (C4264 회피)
    virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;
#endif
};
```

🚨 **자손 BP 헬퍼 함수 이름** — `IsDataValid()` (인자 없음) 으로 자체 검증 함수 *절대 정의 금지*. UObject 베이스의 `IsDataValid(FDataValidationContext&)` 와 *name hiding (C4264)* 충돌. → `HasValidData()` / `IsMyDataValid()` 등 도메인 명시 이름 사용. KMCProject `UMCHitBoneCurveUserData::HasValidBoneCurves()` 사례.

### 2.5. 디자이너 측 — Editor 첨부 🟢

```
StaticMesh / SkeletalMesh / Material / Texture / etc Editor:
1. Details 패널 → "Asset User Data" 카테고리 (자동 표시)
2. Add Element (+) → 자손 클래스 선택 (예: "My Custom Data")
3. 인라인 편집 (DefaultToInstanced + EditInlineNew 덕분)
4. Save
```

### 2.6. 런타임 측 — 읽기 🟢

```cpp
// 표준 접근 — GetAssetUserData<T>() 템플릿 자동 cast
if (USkeletalMesh* Mesh = GetSkeletalMeshAsset())
{
    if (auto* MyData = Mesh->GetAssetUserData<UMyCustomData>())
    {
        if (MyData->Sound.IsValid())
        {
            UGameplayStatics::PlaySoundAtLocation(World, MyData->Sound.LoadSynchronous(), Loc);
        }
    }
}
```

`GetAssetUserData<T>()` = 템플릿 헬퍼 — 자동 `Cast<T>`.

### 2.7. Component 호환 (Mesh 컴포넌트 측) 🟢

`UStaticMeshComponent` / `USkeletalMeshComponent` 자체도 `IInterface_AssetUserData` 구현 — **컴포넌트 별 메타** 가능 (자산은 공유 / 인스턴스마다 다름):

```cpp
USkeletalMeshComponent* Mesh = GetMesh();

UMyCustomData* MyData = NewObject<UMyCustomData>(this);
MyData->Tag = FName("Specific");        // 이 인스턴스만
Mesh->AddAssetUserData(MyData);          // 자산 X, 컴포넌트만
```

⚠ **우선순위**: Component AssetUserData 가 자산 override (인스턴스 우선).

### 2.8. Editor 통합 자동 🟢

`DefaultToInstanced + EditInlineNew` 덕분에:
- Details 패널 자동 표시 (자산 측 + 컴포넌트 측)
- Add / Remove 자동 UI
- 인라인 편집 가능

추가 커스터마이징 시 = `IDetailCustomization` ([[sources/ue-editor-propertyeditor]]) 또는 *별도 도킹 탭* (KMCProject 패턴 [[synthesis/instanced-subobject-customization-bypass]] §4.3).

### 2.9. 함정 / 안티패턴 (9대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | UAssetUserData 자손 클래스 비-Instanced | UCLASS = `DefaultToInstanced + EditInlineNew` |
| 2 | UPROPERTY() Instanced 누락 | 자산 측 `UPROPERTY(EditAnywhere, Instanced)` 의무 |
| 3 | `GetAssetUserData<T>()` 매 Tick 호출 (느림) | Component 초기화 시 캐싱 |
| 4 | UAssetUserData 자체에 UObject 멤버 (자산 참조) | `TSoftObjectPtr` ([[sources/ue-ref-11-assetloadingpolicy]] §2.5) |
| 5 | `PostEditChangeOwner()` Deprecated 사용 (5.4-) | `FPropertyChangedEvent` 인자 버전 (5.6+) |
| 6 | 자산 + Component AssetUserData 우선순위 혼동 | Component 가 자산 override (인스턴스 우선) |
| 7 | Network Replicated 시도 (UAssetUserData) | Replicated X — Cosmetic / 메타만 |
| 8 | 자산 1개에 같은 Class UserData 2개 추가 | `AddAssetUserData` = 자동 Remove 후 추가 (중복 X) |
| **9** ⭐ | **UObject `IsDataValid` 이름 충돌 (C4264) — 자손 BP 헬퍼에 `IsDataValid()` 무인자 정의** | `HasValid<Domain>()` 등 도메인 명시 이름 + **`IsDataValid(FDataValidationContext&)` override 만** (5.x 표준) |

🟢 **#9 KMCProject 검증** (2026-05-13) — `UMCHitBoneCurveUserData::IsDataValid()` 무인자 BP 헬퍼가 베이스의 `IsDataValid(TArray<FText>&)` + `IsDataValid(FDataValidationContext&)` 와 충돌. → `HasValidBoneCurves()` 로 이름 변경 + Phase 4 에서 `IsDataValid(FDataValidationContext&)` override 추가. log entry `[2026-05-13] fix | UMCHitBoneCurveUserData::IsDataValid() C4264`.

### 2.10. ⭐ Phase 4 — Editor Data Validation 시스템 통합 패턴 🟢

5.x 표준 — `UObject::IsDataValid(FDataValidationContext&)` override 로 **Content Browser 의 "Validate Data" 메뉴 자동 통합**:

```cpp
#include "Misc/DataValidation.h"

#if WITH_EDITOR
EDataValidationResult UMyCustomData::IsDataValid(FDataValidationContext& Context) const
{
    EDataValidationResult Result = Super::IsDataValid(Context);

    // 검증 — entry 단위
    if (Tag.IsNone())
    {
        Context.AddError(LOCTEXT("EmptyTag", "Tag must be set"));
        Result = EDataValidationResult::Invalid;
    }

    // Owner 자산 호환성 검증 (예: USkeletalMesh 의 Skeleton 본 검증)
    if (USkeletalMesh* Mesh = Cast<USkeletalMesh>(GetOuter()))
    {
        if (USkeleton* Skel = Mesh->GetSkeleton())
        {
            // FReferenceSkeleton::FindBoneIndex 등 검증
            // → AddWarning("bone not found in Skeleton — will be ignored at runtime")
        }
    }

    return Result;
}
#endif
```

→ 디자이너가 자산 우클릭 → **Asset Actions → Validate Data** 클릭 시 자동 호출. Error/Warning Output Log + Validation Tab 표시.

페어 헬퍼 (KMCProject 패턴):
- `GetInvalidEntryCount(USkeleton*)` — UI marker 갱신
- `CleanupInvalidEntries(USkeleton*)` — Transaction 안 stale 제거 + undo support

## 3. KMCProject 검증 사례 매트릭스 (2026-05-13 신규)

`UMCHitBoneCurveUserData` Phase 1-4 — 본 페이지의 *실증 모범*:

| Phase | 영역 | vault § |
| -- | -- | -- |
| 1 | USkeletalMesh 부착 + USTRUCT 6 FRuntimeFloatCurve | §2.1 UCLASS 매크로 + §2.4 자손 작성 |
| 2 | Persona 별도 탭 (KMCProject 측 컨트롤) | [[synthesis/instanced-subobject-customization-bypass]] §4.3 우회 c |
| 2a | OnAssetEditorOpened delegate Focus 추적 | [[sources/ue-editor-personatoolkit]] (별도) |
| 2b | IStructureDetailsView + FStructOnScope entry 직접 편집 | [[sources/ue-editor-propertyeditor]] §3.x |
| **4** | **IsDataValid(FDataValidationContext&) override + Skeleton cleanup** | **§2.10 (본 페이지)** + §9 #9 (C4264 회피) |

→ `UMCHitBoneCurveUserData` 가 본 페이지의 **§2.10 + §9 #9 1차 검증** 사례.

## 4. 자주 쓰는 시나리오 매트릭스

| 시나리오 | UAssetUserData 자손 | 첨부 자산 |
| -- | -- | -- |
| 발자국 사운드 (표면별) | `UFootstepData` | UStaticMesh |
| Material LOD 힌트 | `UMaterialLODData` | UMaterial |
| Sound Concurrency 그룹 메타 | `USoundGroupData` | USoundBase |
| 카메라 우선순위 (Cinematic) | `UCameraPriorityData` | AWorldSettings |
| Mobile LOD 강제 | `UMobileLODData` | USkeletalMesh / UStaticMesh |
| **본별 히트 커브 (KMCProject)** | `UMCHitBoneCurveUserData` | USkeletalMesh |
| **Niagara Socket Binding (KMCProject)** | `UMCNiagaraSocketBindings` | UStaticMesh |
| 게임 디자인 메타 (Damage 배율 등) | `UGameplayMetaData` | UStaticMesh / 무기 자산 |

## 5. 체크리스트

- [ ] UAssetUserData 자손 = `UCLASS(DefaultToInstanced, EditInlineNew)` + `MinimalAPI` (다른 모듈 cast)
- [ ] UPROPERTY 멤버 = `TSoftObjectPtr` (자산 참조 — vault §2.5)
- [ ] 자산 측 `IInterface_AssetUserData` 구현 확인 (표준 자산은 OK)
- [ ] 런타임 = `GetAssetUserData<T>()` 캐싱 (Tick 회피)
- [ ] **자손 BP 헬퍼 이름 — `IsDataValid()` 무인자 금지** (C4264) → `HasValid<Domain>()`
- [ ] **5.x — `IsDataValid(FDataValidationContext&)` override** + `Misc/DataValidation.h` include
- [ ] `PostEditChangeOwner` = 5.6+ 시그니처 (`FPropertyChangedEvent&`)
- [ ] Component vs 자산 우선순위 인지 (Component override)
- [ ] Network = Cosmetic 만 (Replicated X)

## 6. Cross-link

### 카테고리 main

- [[sources/ue-assetclasses-skill]] (메인 — 10 sub-skill)

### 자매 sub-skill

- [[sources/ue-assetclasses-mesh]] / [[sources/ue-assetclasses-material]] / [[sources/ue-assetclasses-audio]] / [[sources/ue-assetclasses-physics]] (모두 IInterface_AssetUserData 구현)

### 횡단 정책

- [[sources/ue-ref-05-editoronlyindex]] (PostEditChangeOwner / IsDataValid — Editor 전용)
- [[sources/ue-ref-11-assetloadingpolicy]] §2.5 (TSoftObjectPtr 자산 참조)
- [[sources/ue-ref-07-profilingscopeRule]]

### CoreUObject

- [[sources/ue-coreuobject-uobject]] (UObject 베이스 + `IsDataValid(FDataValidationContext&)` virtual)
- [[sources/ue-coreuobject-objecthandles]] (TSoftObjectPtr / TStrongObjectPtr)
- [[sources/ue-coreuobject-reflection]] (UPROPERTY meta)

### Editor 통합

- [[sources/ue-editor-propertyeditor]] (IDetailCustomization — 별도 detail UI)
- [[sources/ue-editor-personatoolkit]] (USkeletalMesh Persona 통합)

### KMCProject MC-시리즈 (2026-05-13 신규)

- [[synthesis/instanced-subobject-customization-bypass]] §4.3 우회 c — KMCProject 별도 도킹 탭 패턴 (UMCHitBoneCurveUserData Phase 2 사례)
- [[concepts/MC-Asset-Validation-Policy]] — KMCProject 검증 매크로 (UAssetUserData Cleanup 시 LogMCAsset 사용)

### 관련 fix / feature log (KMCProject 2026-05-13)

- `feature | UMCHitBoneCurveUserData Phase 1 — 데이터 구조` — UCLASS 매크로 적용 1차
- `feature | UMCHitBoneCurveUserData Phase 2/2a/2b — Persona 별도 탭` — IInterface_AssetUserData 외부 편집 패턴
- `fix | UMCHitBoneCurveUserData::IsDataValid() C4264 name hiding` — 함정 #9 발견 + 이름 변경
- `feature | UMCHitBoneCurveUserData Phase 4 — Editor Validation + Cleanup UI` — §2.10 override 패턴 적용
