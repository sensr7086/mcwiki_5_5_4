---
name: coreuobject-cooking
description: 🛠 쿠킹 - NeedsLoadForServer / NeedsLoadForClient + IsEditorOnly + BeginCacheForCookedPlatformData + UObjectRedirector + Iterative Cook + CookOnTheFly.
---

# CoreUObject / Cooking

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 쿠킹·플랫폼 게이팅 UObject virtual + 쿠킹 시 메타 보존(`U{Enum,Struct,Class}CookedMetaData`) + `UObjectRedirector` + `UDEPRECATED_MetaData` + Cooker 컨텍스트
> 관련 sub-skill: [`Editor/`](../Editor/SKILL.md), [`Serialization/`](../Serialization/SKILL.md), [`Package/`](../Package/SKILL.md), [`Reflection/`](../Reflection/SKILL.md)

> 🛠 **이 sub-skill의 대부분 항목이 에디터·쿠킹 빌드 전용** (`WITH_EDITOR` 가드). 게임 런타임에 영향을 주는 부분은 (1) `NeedsLoadFor*`/`IsEditorOnly` 같은 게이팅 결과로 객체가 빌드에서 제외되는 효과, (2) 런타임에 살아남는 `Cooked*MetaData` 객체로 메타데이터 일부에 접근하는 것 두 가지뿐.

---

## 1. 개요

쿠킹은 에디터 빌드에서 게임 빌드용 산출물을 만드는 과정이다. CoreUObject가 제공하는 영역:

1. **플랫폼 게이팅 virtual** — 어떤 객체가 어느 빌드(클라/서버/PIE/타겟 플랫폼)에 포함될지 결정.
2. **파생 데이터 사전 빌드 hook** — `BeginCacheForCookedPlatformData` / `IsCachedCookedPlatformDataLoaded` 로 텍스처 변환·셰이더 컴파일 같은 무거운 작업을 쿠킹 시점에 미리 처리.
3. **메타데이터 보존** — UPROPERTY/UFUNCTION/UENUM 메타는 기본적으로 에디터 전용이지만, `U{Enum,Struct,Class}CookedMetaData` 객체로 일부를 런타임에 보존 가능.
4. **에셋 이동 호환** — `UObjectRedirector` 가 옛 경로 ↔ 새 경로 매핑.
5. **레거시 메타** — `UDEPRECATED_MetaData` 가 옛 패키지의 메타데이터 호환을 담당. 신규 코드는 `FMetaData`(WITH_METADATA) 사용.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/Object.h` | 게이팅 virtual 다수 (§4) | 클라/서버/PIE/타겟 플랫폼별 포함 여부. |
| `Public/UObject/CookedMetaData.h` | `UEnumCookedMetaData : UObject` (L124), `UStructCookedMetaData : UObject` (L144), `UClassCookedMetaData : UObject` (L164), `FObjectCookedMetaDataStore`, `FStructCookedMetaDataStore`, `FFieldCookedMetaDataStore`, `namespace CookedMetaDataUtil` (`NewCookedMetaData<T>`, `FindCookedMetaData<T>`, `PrepareCookedMetaDataForPurge`) | 런타임에 살아남는 메타데이터 객체. `UCLASS(Optional, Within=...)` 로 부모 안에 종속. |
| `Public/UObject/ObjectRedirector.h` | `UObjectRedirector : UObject` (L29), `UObject* DestinationObject` 멤버 | 에셋 이동 시 옛 경로에서 새 경로로 포워딩. `CLASS_MatchedSerializers` 플래그. |
| `Public/UObject/MetaData.h` | `UDEPRECATED_MetaData : UObject` (L33), `class FMetaData` (`#if WITH_METADATA`) | 옛 메타 객체 + 신규 비-UObject 메타. UPackage가 소유. |
| `Public/UObject/ArchiveCookContext.h` | `struct FArchiveCookContext` (L13) | 쿠킹 중 직렬화 컨텍스트 — 어느 타겟 플랫폼·DLC인지. |
| `Public/UObject/CookEnums.h` | `enum class ECookType` (L11), `ECookingDLC` (L18), `EProcessType` (L31), `ECookResult : uint8` (L42), `ECookValidationOptions` (L59) | 쿠커 모드/결과/검증 옵션. |
| `Public/UObject/ICookInfo.h` | `enum class ECookLoadType : uint8` (L52), `enum class EInstigator : uint8` (L113), `namespace UE::Cook` | 쿠킹 도중 객체 로드 타입·트리거. |
| `Public/UObject/CookedMetaData.h` 🛠 | (전체) | 자세한 사용은 §5. |
| `Public/Cooker/CookEvents.h`, `CookDependency.h`, `CookArtifact.h`, `CookDeterminismHelper.h`, `MPCollector.h` 🛠 | Cooker 5.x 의 의존성·아티팩트 추적 | 멀티프로세스 쿠킹·결정론 검증. 일반 게임 코드 안 씀. |

---

## 3. 자주 쓰는 API

```cpp
// === 게이팅 (UObject 가상) ===
class UMyClientOnlyData : public UDataAsset
{
    GENERATED_BODY()
public:
    virtual bool NeedsLoadForServer() const override { return false; }   // 서버 빌드 제외
    virtual bool NeedsLoadForClient() const override { return true; }
};

class UMyEditorTool : public UObject
{
    GENERATED_BODY()
public:
    virtual bool IsEditorOnly() const override { return true; }          // 쿠킹에서 자동 제외
};

// === 쿠킹 시 파생 데이터 빌드 ===
#if WITH_EDITOR
void UMyTexture::BeginCacheForCookedPlatformData(const ITargetPlatform* TP)
{
    Super::BeginCacheForCookedPlatformData(TP);
    StartAsyncCompression(TP);     // 비동기 시작
}

bool UMyTexture::IsCachedCookedPlatformDataLoaded(const ITargetPlatform* TP)
{
    return Super::IsCachedCookedPlatformDataLoaded(TP) && CompressionDone(TP);
}
#endif

// === 쿠킹된 메타데이터 노출 (런타임 사용 가능) ===
// CookedMetaData.h (런타임에 일부 보존된 메타를 사용)
if (UClassCookedMetaData* CMD = CookedMetaDataUtil::FindCookedMetaData<UClassCookedMetaData>(SomeClass, TEXT("CookedMetaData")))
{
    if (CMD->HasMetaData())
    {
        CMD->ApplyMetaData(SomeClass);   // 캐싱된 메타를 다시 클래스에 주입
    }
}

// === ObjectRedirector 처리 ===
UObject* Resolved = LoadObject<UObject>(nullptr, TEXT("/Game/Old/Path.Old"));
if (UObjectRedirector* R = Cast<UObjectRedirector>(Resolved))
{
    Resolved = R->DestinationObject;     // 옛 경로 → 새 객체
}
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 플랫폼 게이팅 (`Public/UObject/Object.h`)

> `false` 반환 시 해당 빌드/플랫폼에 객체가 포함되지 않는다.

| 시그니처 | 위치 | 가드 | 의미 |
|----------|------|------|------|
| `virtual bool NeedsLoadForClient() const` | Object.h L559 | (런타임) | 클라이언트 빌드에 포함될지. |
| `virtual bool NeedsLoadForServer() const` | Object.h L567 | (런타임) | 서버 빌드에 포함될지. |
| `virtual bool NeedsLoadForTargetPlatform(const ITargetPlatform*) const` | Object.h L575 | `WITH_EDITOR` 위주 호출 | 특정 타겟에 포함될지. |
| `virtual bool NeedsLoadForEditorGame() const` | Object.h L583 | (런타임) | PIE에서 필요한지. |
| `virtual bool IsEditorOnly() const` | Object.h L593 | (런타임) | 에디터 전용 객체. 쿠킹 시 자동 제외. |
| `virtual bool HasNonEditorOnlyReferences() const` | Object.h L604 | (런타임) | 자신은 에디터 전용이지만 비-에디터 객체를 참조하는지. |
| `virtual bool IsPostLoadThreadSafe() const` | Object.h L614 | (런타임) | true면 PostLoad 비동기 호출 가능. |
| `virtual bool IsDestructionThreadSafe() const` | Object.h L625 | (런타임) | 비동기 파괴 가능 여부. |

### 4.2 쿠킹 시 파생 데이터 캐싱 🛠

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual void BeginCacheForCookedPlatformData(const ITargetPlatform*)` 🛠 | Object.h L1211 | `WITH_EDITOR` | 쿠킹 시 파생 데이터 사전 빌드 시작. |
| `virtual bool IsCachedCookedPlatformDataLoaded(const ITargetPlatform*)` 🛠 | Object.h L1218 | `WITH_EDITOR` | 위 작업 완료 폴링. true 반환 전엔 패키지 저장 보류. |
| `virtual void WillNeverCacheCookedPlatformDataAgain()` 🛠 | Object.h L1223 | `WITH_EDITOR` | 더 이상 캐시 호출 없음 통지. |
| `virtual void ClearCachedCookedPlatformData(const ITargetPlatform*)` 🛠 | Object.h L1230 | `WITH_EDITOR` | 특정 타겟의 캐시 비우기. |
| `virtual void ClearAllCachedCookedPlatformData()` 🛠 | Object.h L1237 | `WITH_EDITOR` | 모든 타겟. |
| `virtual void CookAdditionalFilesOverride(const TCHAR*, const ITargetPlatform*, ...)` 🛠 | Object.h L1264 | `WITH_EDITOR` | 패키지 외 추가 파일 출력. |
| `virtual void GetAdditionalAssetDataObjectsForCook(FArchiveCookContext&, ...) const` 🛠 | Object.h L907 | `WITH_EDITOR` | 함께 묶일 추가 객체 보고. |
| `virtual void GetExtendedAssetRegistryTagsForSave(const ITargetPlatform*, TArray<FAssetRegistryTag>&) const` 🛠 | Object.h L915 | `WITH_EDITOR` | 저장 시 추가 태그. |
| `virtual void OnCookEvent(UE::Cook::ECookEvent, UE::Cook::FCookEventContext&)` 🛠 | Object.h L295 | `WITH_EDITOR` | Cooker 이벤트 통지. |

### 4.3 ConfigOverride (런타임에도 일부 효과)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual const TCHAR* GetConfigOverridePlatform() const` | Object.h L1395 | 이 객체의 ini 로드 시 다른 플랫폼 ini 사용. |
| `virtual void OverrideConfigSection(FString&)` | Object.h L1402 | 섹션 이름 변경. |
| `virtual void OverridePerObjectConfigSection(FString&)` | Object.h L1409 | per-object 섹션 변경. |

### 4.4 CookedMetaData / Redirector / DEPRECATED_MetaData virtual

```cpp
// UEnumCookedMetaData / UStructCookedMetaData / UClassCookedMetaData 공통
virtual void PostLoad() override;              // 부모(UEnum/UScriptStruct/UClass)에 메타 적용
virtual bool HasMetaData() const;
virtual void CacheMetaData(const U.../*Source*/);    // 캐싱 (쿠킹 시)
virtual void ApplyMetaData(U.../*Target*/) const;    // 런타임 주입
```

```cpp
// UObjectRedirector (ObjectRedirector.h L29~)
virtual void PreSave(FObjectPreSaveContext) override;
virtual void Serialize(FArchive&) override;
virtual void Serialize(FStructuredArchive::FRecord) override;
virtual bool NeedsLoadForEditorGame() const override;
virtual void GetAssetRegistryTags(FAssetRegistryTagsContext) const override;
virtual bool HasNonEditorOnlyReferences() const override { return true; }
virtual bool GetNativePropertyValues(TMap<FString,FString>& Out, uint32 ExportFlags=0) const override;
```

---

## 5. 예제

### 5.1 서버 빌드에서 빠지는 데이터

```cpp
UCLASS()
class UMyHapticData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY() TArray<float> Pattern;

    virtual bool NeedsLoadForServer() const override { return false; }   // 서버에 안 나감
};
```

### 5.2 텍스처 변환 같은 무거운 쿠킹 작업

```cpp
#if WITH_EDITOR
void UMyTexture::BeginCacheForCookedPlatformData(const ITargetPlatform* TP)
{
    Super::BeginCacheForCookedPlatformData(TP);
    if (!CompressedFor.Contains(TP))
        StartAsyncCompression(TP);   // 백그라운드 작업 시작
}

bool UMyTexture::IsCachedCookedPlatformDataLoaded(const ITargetPlatform* TP)
{
    return Super::IsCachedCookedPlatformDataLoaded(TP)
        && CompressedFor.Contains(TP);   // 완료된 타겟만 true
}

void UMyTexture::ClearCachedCookedPlatformData(const ITargetPlatform* TP)
{
    Super::ClearCachedCookedPlatformData(TP);
    CompressedFor.Remove(TP);
}
#endif
```

쿠커는 패키지 저장 직전 `IsCachedCookedPlatformDataLoaded(TP)` 가 true 가 될 때까지 대기한다. 비동기 작업이 끝나야 결정론적 결과로 디스크에 직렬화 가능.

### 5.3 옛 경로 호환 (Redirector 자동 처리)

대부분은 엔진이 자동 처리하지만 명시적 추적이 필요할 때:

```cpp
UObject* Loaded = LoadObject<UObject>(nullptr, TEXT("/Game/Items/OldSword.OldSword"));
if (UObjectRedirector* R = Cast<UObjectRedirector>(Loaded))
{
    Loaded = R->DestinationObject;   // 새 경로로 자동 포워딩
}
```

### 5.4 런타임에서 메타데이터 일부 사용 (CookedMetaData)

```cpp
// 쿠킹 시 부모 클래스 내부에 UClassCookedMetaData("CookedMetaData") 가 함께 저장된다.
if (UClassCookedMetaData* CMD = CookedMetaDataUtil::FindCookedMetaData<UClassCookedMetaData>(MyClass, TEXT("CookedMetaData")))
{
    if (CMD->HasMetaData())
    {
        CMD->ApplyMetaData(MyClass);  // 메타데이터 맵을 클래스에 다시 주입
    }
}
// 이후 MyClass->GetMetaData(TEXT("Category")) 등이 런타임에서도 동작
```

> 주의: 런타임 메타데이터는 비싸다. 게임 로직에는 필요한 키만 별도 UPROPERTY로 모델링하는 편이 낫다.

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

이 sub-skill 자체가 거의 전부 에디터·쿠킹 전용이다. 위 §4·§5 의 🛠 표시 항목 모두가 해당. 추가로:

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| Cooker 보조 헤더(`Public/Cooker/*.h`) 🛠 | (디렉토리) | `WITH_EDITOR` 위주 | 멀티프로세스 쿠킹·의존 추적·결정론. |
| `UDEPRECATED_MetaData` 🛠 | MetaData.h L33 | `Deprecated` (`Config = Engine`) | 옛 패키지 호환 — 신규 코드 사용 금지. |
| `FMetaData` (`#if WITH_METADATA`) 🛠 | MetaData.h | `WITH_METADATA` (≈ `WITH_EDITORONLY_DATA`) | 신규 비-UObject 메타. UPackage 소유. |
| `FArchiveCookContext` 🛠 | ArchiveCookContext.h L13 | `WITH_EDITOR` | 쿠킹 중 직렬화 컨텍스트. |
| `IEditorPathObjectInterface` 🛠 | EditorPathObjectInterface.h | `WITH_EDITOR` | 본 위키 [`Interface/`](../Interface/SKILL.md) 참조. |

**런타임에서 의미 있는 항목**:

- `NeedsLoadFor*`/`IsEditorOnly`/`IsPostLoadThreadSafe`/`IsDestructionThreadSafe` 의 효과 (객체가 빌드에 포함/제외되는 결과).
- `UObjectRedirector` 가 옛 경로로 들어왔을 때 `DestinationObject` 를 따라가는 처리.
- `UClassCookedMetaData` 등이 패키지에 동봉되어 있다면 메타데이터 일부를 런타임에서도 조회 가능.

그 외 모든 hook 은 에디터/쿠커 빌드에서만 호출되거나, 호출되더라도 의미 없는 no-op이다.

---

## 7. 관련 sub-skill

- [`Editor/`](../Editor/SKILL.md) — `IsDataValid`/`GetAssetRegistryTags` 등 에디터 콜백
- [`Serialization/`](../Serialization/SKILL.md) — `PreSave`/`PostSave` 와 쿠킹 라이터
- [`Package/`](../Package/SKILL.md) — `SavePackage`/`FSavePackageContext` 가 쿠킹의 출력 면
- [`Reflection/`](../Reflection/SKILL.md) — UPROPERTY/UCLASS 메타가 쿠킹에 어떻게 보존되는가
