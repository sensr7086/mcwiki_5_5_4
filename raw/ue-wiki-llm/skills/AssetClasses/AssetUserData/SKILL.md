---
name: assetclasses-assetuserdata
description: UAssetUserData (Engine/AssetUserData.h:16) + IInterface_AssetUserData (Interfaces/Interface_AssetUserData.h:19) — 자산 메타 확장 표준. 자산 클래스 수정 없이 커스텀 데이터 첨부 (예: 발자국 타입 / LOD 힌트 / Game-specific 메타). StaticMesh / SkeletalMesh / Material / Texture / SoundBase / PhysicsAsset / WorldSettings 모두 지원.
---

# AssetClasses/AssetUserData — 자산 메타 확장 표준

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/AssetUserData.h:16` (UAssetUserData) + `Engine/Source/Runtime/Engine/Classes/Interfaces/Interface_AssetUserData.h:19` (IInterface_AssetUserData)
> **베이스**: `UAssetUserData : public UObject` (DefaultToInstanced + abstract + editinlinenew) — 사용자가 자손 클래스로 구현
> **요지**: **자산 클래스 수정 없이 커스텀 데이터 첨부**. StaticMesh / SkeletalMesh / Material / Texture / Sound / PhysicsAsset / WorldSettings / SoundClass 등이 이미 지원. 게임 측 메타 (발자국 / LOD 힌트 / 카메라 우선순위 등) 통합 표준.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) §3 | UAssetUserData 자손 = UPROPERTY + TObjectPtr (자동 GC) |
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | 일부 데이터 = Editor 전용 (`WITH_EDITORONLY_DATA` 가드) |
| 🎯 5.6+ Deprecated | `PostEditChangeOwner()` (no args) → `PostEditChangeOwner(const FPropertyChangedEvent&)` |

---

## 1. UAssetUserData 베이스 (Engine/AssetUserData.h:16)

```cpp
// UAssetUserData — 사용자가 자손 작성
UCLASS(DefaultToInstanced, abstract, editinlinenew, MinimalAPI)
class UAssetUserData : public UObject
{
    GENERATED_UCLASS_BODY()

    // Editor 디버깅용 (선택)
    virtual void Draw(class FPrimitiveDrawInterface* PDI, const class FSceneView* View) const {}
    virtual void DrawCanvas(class FCanvas& Canvas, class FSceneView& View) const {}

    // Owner 변경 시 콜백 (5.6+)
    virtual void PostEditChangeOwner(const FPropertyChangedEvent& PropertyChangedEvent) {}
};
```

**UCLASS 매크로 의미**:
- `DefaultToInstanced` — 자산 안 인스턴스화 시 자동 (포인터 X)
- `abstract` — 베이스만 — 자손 클래스 작성 의무
- `editinlinenew` — Editor 디테일 패널 안 직접 생성

---

## 2. IInterface_AssetUserData (Interface — 자산 측)

```cpp
// Interface_AssetUserData.h:19
class IInterface_AssetUserData
{
    GENERATED_IINTERFACE_BODY()

    virtual void AddAssetUserData(UAssetUserData* InUserData) {}

    UFUNCTION(BlueprintCallable, Category=AssetUserData, meta=(DeterminesOutputType="InUserDataClass"))
    virtual UAssetUserData* GetAssetUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass);

    UFUNCTION(BlueprintCallable, Category=AssetUserData)
    virtual bool HasAssetUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass);

    virtual void RemoveUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass) {}

    virtual const TArray<UAssetUserData*>* GetAssetUserDataArray() const { return nullptr; }
};
```

→ 자산이 이 Interface 구현 시 = UserData 보관 가능.

---

## 3. 이미 지원하는 자산 (5.x 표준)

| 자산 클래스 | Interface 구현 | 헤더 |
|------------|--------------|------|
| `UStaticMesh` ⭐ | ✅ | `Engine/Classes/Engine/StaticMesh.h` |
| `USkeletalMesh` ⭐ | ✅ | `Engine/Classes/Engine/SkeletalMesh.h` |
| `UMaterial` / `UMaterialInstance` | ✅ | `Engine/Classes/Materials/Material.h` |
| `UTexture` (Texture2D / Cube / 등) | ✅ | `Engine/Classes/Engine/Texture.h` |
| `USoundBase` (SoundCue / SoundWave) | ✅ | `Engine/Classes/Sound/SoundBase.h` |
| `USoundClass` | ✅ | `Engine/Classes/Sound/SoundClass.h` |
| `UPhysicsAsset` | ✅ | `Engine/Classes/PhysicsEngine/PhysicsAsset.h` |
| `AWorldSettings` | ✅ | `Engine/Classes/GameFramework/WorldSettings.h` |
| `UPhysicalMaterial` | ✅ | `Engine/Classes/PhysicalMaterials/PhysicalMaterial.h` |
| `UAnimSequence` / `UAnimBlueprint` | ✅ | `Engine/Classes/Animation/AnimationAsset.h` |

→ 추가로 Custom 자산 = IInterface_AssetUserData 구현 시 지원 가능.

---

## 4. 표준 사용 패턴 — 발자국 사운드 (StaticMesh 별)

### 4.1 UAssetUserData 자손 작성

```cpp
// FootstepData.h
#pragma once
#include "Engine/AssetUserData.h"
#include "FootstepData.generated.h"

UENUM(BlueprintType)
enum class EFootstepSurface : uint8
{
    Default UMETA(DisplayName="기본"),
    Grass   UMETA(DisplayName="잔디"),
    Wood    UMETA(DisplayName="나무"),
    Metal   UMETA(DisplayName="금속"),
    Stone   UMETA(DisplayName="돌"),
    Water   UMETA(DisplayName="물"),
};

UCLASS(BlueprintType, EditInlineNew, CollapseCategories, meta=(DisplayName="Footstep Data"))
class MYGAME_API UFootstepData : public UAssetUserData
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Footstep")
    EFootstepSurface SurfaceType = EFootstepSurface::Default;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Footstep")
    TSoftObjectPtr<USoundBase> FootstepSound;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Footstep")
    float Volume = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Footstep")
    float Pitch = 1.0f;
};
```

### 4.2 자산 측 — Editor 에서 첨부

```
Static Mesh Editor:
1. Details 패널 → "Asset User Data" 카테고리 (자동 표시)
2. Add Element → "Footstep Data" 선택
3. SurfaceType = Wood / FootstepSound = SFX_Wood_Footstep / Volume = 0.8
4. Save
```

### 4.3 런타임 측 — 읽기

```cpp
// AnimNotify_Footstep.cpp
void UAnimNotify_Footstep::Notify(USkeletalMeshComponent* MeshComp, ...)
{
    UE_PROFILE();
    if (!IsValid(MeshComp) || !IsValid(MeshComp->GetOwner())) return;

    // 발 본 위치 아래 Trace
    FVector FootLoc = MeshComp->GetSocketLocation(TEXT("foot_l"));
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(Footstep), true);
    Params.AddIgnoredActor(MeshComp->GetOwner());

    if (MeshComp->GetWorld()->LineTraceSingleByChannel(
        Hit, FootLoc + FVector(0, 0, 50), FootLoc - FVector(0, 0, 50),
        ECC_Visibility, Params))
    {
        if (UPrimitiveComponent* HitComp = Hit.GetComponent())
        {
            // StaticMesh 의 UFootstepData 가져오기
            if (auto* SMC = Cast<UStaticMeshComponent>(HitComp))
            {
                if (UStaticMesh* SM = SMC->GetStaticMesh())
                {
                    // ⭐ AssetUserData 사용
                    if (auto* FootData = SM->GetAssetUserData<UFootstepData>())
                    {
                        // 표면별 사운드 재생
                        if (FootData->FootstepSound.IsValid())
                        {
                            UGameplayStatics::PlaySoundAtLocation(
                                MeshComp->GetWorld(),
                                FootData->FootstepSound.LoadSynchronous(),
                                Hit.ImpactPoint,
                                FootData->Volume,
                                FootData->Pitch);
                        }
                    }
                }
            }
        }
    }
}
```

> **GetAssetUserData<T>()** = 템플릿 헬퍼 (자동 Cast).

---

## 5. Custom Class 에 Interface 구현 (선택)

자체 자산 클래스 만들 시:

```cpp
// MyCustomAsset.h
UCLASS(BlueprintType)
class UMyCustomAsset : public UDataAsset, public IInterface_AssetUserData
{
    GENERATED_BODY()

public:
    // IInterface_AssetUserData
    virtual void AddAssetUserData(UAssetUserData* InUserData) override
    {
        if (InUserData)
        {
            RemoveUserDataOfClass(InUserData->GetClass());
            AssetUserData.Add(InUserData);
        }
    }

    virtual UAssetUserData* GetAssetUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass) override
    {
        for (UAssetUserData* Data : AssetUserData)
        {
            if (Data && Data->IsA(InUserDataClass))
                return Data;
        }
        return nullptr;
    }

    virtual void RemoveUserDataOfClass(TSubclassOf<UAssetUserData> InUserDataClass) override
    {
        AssetUserData.RemoveAll([&](UAssetUserData* D) { return D && D->IsA(InUserDataClass); });
    }

    virtual const TArray<UAssetUserData*>* GetAssetUserDataArray() const override
    {
        return &AssetUserData;
    }

protected:
    UPROPERTY(EditAnywhere, Instanced, Category="AssetUserData")
    TArray<TObjectPtr<UAssetUserData>> AssetUserData;
};
```

→ Details 패널 자동 노출 (Instanced + editinlinenew 덕분).

---

## 6. 자주 쓰는 시나리오 매트릭스

| 시나리오 | UAssetUserData 자손 | 첨부 자산 |
|---------|------------------|----------|
| 발자국 사운드 (표면별) | UFootstepData | UStaticMesh |
| Material LOD 힌트 | UMaterialLODData | UMaterial |
| Sound Concurrency 그룹 메타 | USoundGroupData | USoundBase |
| 카메라 우선순위 (Cinematic) | UCameraPriorityData | AWorldSettings |
| 다국어 자산 (Localization) | ULocalizationMetaData | (모든 자산) |
| 자산 출처 / 라이선스 정보 | UAssetMetaData | (모든 자산) |
| 게임 디자인 메타 (Damage 배율 등) | UGameplayMetaData | UStaticMesh / 무기 자산 |
| 광물 / 자원 표시 (RPG) | UResourceData | UStaticMesh |
| Mobile LOD 강제 | UMobileLODData | USkeletalMesh / UStaticMesh |

---

## 7. Component 호환 (Mesh 컴포넌트 측)

`UStaticMeshComponent` / `USkeletalMeshComponent` 자체도 IInterface_AssetUserData 구현 — 컴포넌트 별 메타 가능.

```cpp
// 컴포넌트 별 데이터 (자산은 공유 — 인스턴스마다 다름)
USkeletalMeshComponent* Mesh = GetMesh();

UFootstepData* MyData = NewObject<UFootstepData>(this);
MyData->SurfaceType = EFootstepSurface::Metal;   // 이 인스턴스만
MyData->Volume = 0.5f;

Mesh->AddAssetUserData(MyData);                  // 자산 X, 컴포넌트만

// 읽기
if (auto* Data = Mesh->GetAssetUserData<UFootstepData>())
{
    // Mesh 자체 OverrideStaticMesh = 자산 메타 무시
    // Component AssetUserData = 인스턴스 메타 사용
}
```

---

## 8. Editor 통합 (자동)

`editinlinenew` + `DefaultToInstanced` 덕분에:
- Details 패널 자동 표시 (자산 측 + 컴포넌트 측)
- Add / Remove 자동 UI
- 인라인 편집 가능

추가 커스터마이징 시 = PropertyEditor sub-skill (Details Customization).

---

## 9. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UAssetUserData 자손 클래스 비-Instanced | UCLASS = DefaultToInstanced + EditInlineNew |
| 2 | UPROPERTY() Instanced 누락 | 자산 측 `UPROPERTY(EditAnywhere, Instanced)` 의무 |
| 3 | GetAssetUserData<T>() 매 Tick 호출 (느림) | Component 초기화 시 캐싱 |
| 4 | UAssetUserData 자체에 UObject 멤버 (자산 참조) | TSoftObjectPtr (PreLoad 정책 — 11_§2) |
| 5 | PostEditChangeOwner() Deprecated 사용 (5.4-) | FPropertyChangedEvent 인자 버전 (5.6+) |
| 6 | 자산 + Component AssetUserData 우선순위 혼동 | Component 가 자산 override (인스턴스 우선) |
| 7 | Network Replicated 시도 (UAssetUserData) | Replicated X — Cosmetic / 메타만 |
| 8 | 자산 1개에 같은 Class UserData 2개 추가 | AddAssetUserData = 자동 Remove 후 추가 (중복 X) |

---

## 10. 체크리스트

- [ ] UAssetUserData 자손 = UCLASS(DefaultToInstanced, EditInlineNew)
- [ ] UPROPERTY 멤버 = TSoftObjectPtr (자산 참조)
- [ ] 자산 측 IInterface_AssetUserData 구현 확인 (이미 표준 자산은 OK)
- [ ] 런타임 = GetAssetUserData<T>() 캐싱 (Tick 회피)
- [ ] PostEditChangeOwner = 5.6+ 시그니처 (FPropertyChangedEvent)
- [ ] Component vs 자산 우선순위 인지 (Component override)
- [ ] Network = Cosmetic 만 (Replicated X)

---

## 11. 관련

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인 (10 sub-skill)
- [`AssetClasses/Mesh/SKILL.md`](../Mesh/SKILL.md) — UStaticMesh / USkeletalMesh (이미 지원)
- [`AssetClasses/Material/SKILL.md`](../Material/SKILL.md) — UMaterial (이미 지원)
- [`AssetClasses/Audio/SKILL.md`](../Audio/SKILL.md) — USoundBase / USoundClass (이미 지원)
- [`AssetClasses/Physics/SKILL.md`](../Physics/SKILL.md) — UPhysicsAsset / UPhysicalMaterial (이미 지원)
- [`Editor/PropertyEditor/SKILL.md`](../../Editor/PropertyEditor/SKILL.md) — Details Customization (선택)
- [`CoreUObject/UObject/SKILL.md`](../../CoreUObject/UObject/SKILL.md) — UObject 베이스 + Instanced
- [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — TSoftObjectPtr 의무

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. **UAssetUserData (Engine/AssetUserData.h:16)** + IInterface_AssetUserData (:19) + 표준 자산 10종 지원 + 발자국 시나리오 표준 패턴 + Custom Class 구현 + Component 호환 + Editor 통합 + 함정 8대. |
