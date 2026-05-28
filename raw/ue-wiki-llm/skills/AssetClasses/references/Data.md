---
name: assetclasses-data
description: UDataAsset + UPrimaryDataAsset (Bundle 표준) + UDataTable (552) + UCurveTable (342) + UCurveFloat - 데이터 기반 디자인.
---

# AssetClasses/Data — UDataAsset + UPrimaryDataAsset + UDataTable + UCurveTable + UCurveFloat

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/DataAsset.h` (67) + `DataTable.h` (552) + `CurveTable.h` (342) + `Curves/CurveBase.h` + `CurveFloat.h`
> **베이스**: `UDataAsset : public UObject` → `UPrimaryDataAsset` (Primary Asset 표준) / `UDataTable` (행 기반 데이터) / `UCurveBase` → `UCurveFloat` / `UCurveLinearColor` / `UCurveVector`
> **요지**: **게임 데이터의 모든 표 + 곡선 자산** — 디자이너가 에디터에서 편집 + 코드가 런타임 조회. PrimaryAsset 시스템의 진입점.

---

## 🚨 공통 정책

| 정책 | Data 자산 적용 |
|------|---------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | **🔥 UPrimaryDataAsset = PreLoad 표준** — `meta=(AssetBundles=)` Bundle 명시 + DefaultEngine.ini PrimaryAssetTypesToScan 자동 스캔. **DataTable / CurveTable = 작은 자산** (Hard 사용 OK). |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | DataAsset 멤버 = `UPROPERTY()` + `TObjectPtr<UMyDataAsset>`. 게임 시작 시 Hard 로드 OK (작음). |

---

## 1. UDataAsset (베이스 — 67 lines)

```cpp
// DataAsset.h:20
class UDataAsset : public UObject
{
    // 베이스만 — 그 외 멤버는 자식이 추가
};
```

> **`.uasset` 자산 — 디자이너 편집** + **단순 데이터 컨테이너** (메소드 없이).

### 1.1 표준 자식 패턴

```cpp
// MyWeaponDataAsset.h
UCLASS(BlueprintType)
class UMyWeaponDataAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 Damage;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float FireRate;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TSoftObjectPtr<UStaticMesh> WeaponMesh;
};
```

---

## 2. UPrimaryDataAsset (PreLoad 표준 — 가장 중요)

```cpp
// DataAsset.h:46
class UPrimaryDataAsset : public UDataAsset
{
    // DataAsset.h:52 — Primary Asset Id 자동 (Type+Name)
    ENGINE_API virtual FPrimaryAssetId GetPrimaryAssetId() const override;

    // DataAsset.h:57 — Bundle 데이터 자동 갱신
    ENGINE_API virtual void UpdateAssetBundleData();
};
```

### 2.1 표준 자식 + Bundle 명시

```cpp
UCLASS(BlueprintType)
class UMyEnemyData : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, meta=(AssetBundles="Spawn"))
    TSoftClassPtr<AEnemy> EnemyClass;

    UPROPERTY(EditAnywhere, meta=(AssetBundles="Visual"))
    TSoftObjectPtr<USkeletalMesh> Mesh;

    UPROPERTY(EditAnywhere, meta=(AssetBundles="Visual"))
    TSoftObjectPtr<UAnimBlueprint> AnimBP;

    UPROPERTY(EditAnywhere, meta=(AssetBundles="Audio"))
    TSoftObjectPtr<USoundCue> AttackSound;

    // Override — Type = "Enemy"
    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId(TEXT("Enemy"), GetFName());
    }
};
```

### 2.2 DefaultEngine.ini 자동 스캔 등록

```ini
[/Script/Engine.AssetManagerSettings]
PrimaryAssetTypesToScan=(
    PrimaryAssetType="Enemy",
    AssetBaseClassLoaded=/Script/MyGame.MyEnemyData,
    Directories=((Path="/Game/Data/Enemies")),
    Rules=(Priority=-1,bApplyRecursively=True,CookRule=AlwaysCook)
)
```

> **자세한 PrimaryAsset 패턴 = [`11_AssetLoadingPolicy.md §4`](../../../references/11_AssetLoadingPolicy.md)**.

---

## 3. UDataTable (행 기반 데이터 — 552 lines)

### 3.1 핵심

```cpp
// DataTable.h:79
class UDataTable
{
    // DataTable.h:94 — 행 구조 (USTRUCT)
    UPROPERTY(EditAnywhere)
    TObjectPtr<UScriptStruct> RowStruct;

    // 모든 행 데이터
    TMap<FName, uint8*> RowMap;

    // Row 검색
    template<class T>
    T* FindRow(FName RowName, const TCHAR* ContextString, bool bWarnIfRowMissing = true) const;

    // 모든 Row 조회
    const TMap<FName, uint8*>& GetRowMap() const;
};
```

### 3.2 RowStruct 정의 (FTableRowBase)

```cpp
// MyWeaponRow.h
USTRUCT(BlueprintType)
struct FMyWeaponRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere)
    int32 Damage;

    UPROPERTY(EditAnywhere)
    float FireRate;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> Mesh;
};
```

### 3.3 사용 — Row 검색

```cpp
// 단일 Row
FMyWeaponRow* Row = WeaponTable->FindRow<FMyWeaponRow>(TEXT("Sword"), TEXT("Context"));
if (Row)
{
    Damage = Row->Damage;
}

// 모든 Row 순회
for (const auto& Pair : WeaponTable->GetRowMap())
{
    FMyWeaponRow* Row = reinterpret_cast<FMyWeaponRow*>(Pair.Value);
    // ...
}

// CSV / JSON Import / Export — 디자이너 워크플로
```

### 3.4 함정

```cpp
// ❌ 매 프레임 FindRow 호출
void Tick() {
    auto* Row = Table->FindRow<FMyRow>(TEXT("Foo"), TEXT("Tick"));   // O(1) 이지만 매 프레임 비용
}

// ✅ 정답 — BeginPlay 에서 캐싱
void BeginPlay() {
    CachedRow = Table->FindRow<FMyRow>(TEXT("Foo"), TEXT("BeginPlay"));
}
```

---

## 4. UCurveTable (곡선 표 — 342 lines)

### 4.1 핵심

```cpp
// CurveTable.h:40
class UCurveTable
{
    // RichCurve / SimpleCurve 모드
    enum class ECurveTableMode { Empty, SimpleCurves, RichCurves };

    // RichCurve 행 (Bezier / Tangent)
    const TMap<FName, FRichCurve*>& GetRichCurveRowMap() const;

    // SimpleCurve 행 (Linear)
    const TMap<FName, FSimpleCurve*>& GetSimpleCurveRowMap() const;
};
```

### 4.2 사용 (DPS Scaling / Damage Curve / etc)

```cpp
// 레벨 별 데미지 곡선
FRichCurve* DamageCurve = CurveTable->FindCurve(TEXT("Damage"), TEXT("Context"));
float DamageAtLevel10 = DamageCurve->Eval(10.f);   // X = 레벨 / Y = 데미지
```

---

## 5. UCurveFloat / UCurveLinearColor / UCurveVector (단일 곡선)

```cpp
// CurveFloat.h:30
class UCurveFloat : public UCurveBase
{
    UPROPERTY()
    FRichCurve FloatCurve;

    float GetFloatValue(float InTime) const;
};

// 사용 — 시간 기반 값 (Timeline / Animation Driver)
float Value = MyCurveFloat->GetFloatValue(Time);
```

> **5.x — Timeline Component 가 직접 UCurveFloat 사용**.

---

## 6. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | DataAsset 안 게임 로직 | 단순 데이터 컨테이너만 — 로직은 Component / GameMode |
| 2 | DataTable 매 프레임 FindRow | BeginPlay 에서 캐싱 |
| 3 | UDataAsset 사용 + Primary Asset 표준 X | UPrimaryDataAsset 사용 — Bundle + GetPrimaryAssetId override |
| 4 | DataAsset 의 어셋 멤버 = Hard Reference | 큰 어셋 = `TSoftObjectPtr` + `meta=(AssetBundles=)` |
| 5 | DefaultEngine.ini PrimaryAssetTypesToScan 등록 안 함 | 자동 스캔 안 됨 — 등록 의무 |
| 6 | UCurveFloat 매 Eval 호출 (매 프레임) | 캐싱 또는 Timeline Component 사용 |
| 7 | DataTable RowStruct 변경 후 ImportCSV 미실행 | 데이터 손실 — 재 import 필요 |
| 8 | 🚨 자주 사용 PrimaryDataAsset PreLoad 안 함 | Match Start `PreloadPrimaryAssets` |

---

## 7. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (UPrimaryDataAsset Bundle 시스템)

---

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UDataAsset 67** 베이스 + **UPrimaryDataAsset** GetPrimaryAssetId / UpdateAssetBundleData / `meta=(AssetBundles=)` 표준. **UDataTable 552** RowStruct (FTableRowBase) + FindRow / GetRowMap + CSV Import/Export. **UCurveTable 342** RichCurve / SimpleCurve. **UCurveFloat / Vector / LinearColor** (CurveBase / GetFloatValue / Timeline 통합). 함정 8종. |
