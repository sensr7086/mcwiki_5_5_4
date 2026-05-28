---
type: source
title: "UE CoreUObject — UObject sub-skill"
slug: ue-coreuobject-uobject
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/UObject.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-line-shifted  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/UObject]]"
related_concepts:
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Reflection-System]]"
tags: [ue, runtime, foundation, coreuobject, uobject, virtual, name-hiding-c4264, const-propagation-c2440, fstructonscope-stability, tarray-reallocation, ue-macro-identifier-collision, forward-declare-c2664, instanced-uclass-meta-quartet]
---

# UE CoreUObject — UObject sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/UObject.md]] · `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h`
> Parent: [[sources/ue-coreuobject-skill]] · 보강 2026-05-13 — §2.7-2.9 IsDataValid 5.x + C4264 · 보강 2026-05-14 — §2.10 C2440 + §2.11 FStructOnScope TArray + §2.12 UE 글로벌 매크로 식별자 함정 (KMCProject 사용자 진단) · 보강 2026-05-15 (Cycle 5d 1차) — §2.13 forward-declared UObject 자손 → UObject\* 변환 C2664 + §2.14 Instanced Track/Section 4 UCLASS meta 표준 (KMCProject MCComboEditor 실측) · 보강 2026-05-15 (Cycle 5d 2차) — **§2.11.1 신규** (다른 customization 재현 검증 — UE Engine `SRowEditor` / `PerlinNoiseChannel` / `InstancedStructDetails` 3 사이트 — 🟡 single-case → 🟢 일반 패턴)

## 1. Summary

[[entities/UObject]] 베이스 클래스의 풀 디테일 — 라이프사이클 4 단계 (PostInitProperties / PostLoad / BeginDestroy / FinalizeDestroy) + Super 호출 규약 + ConstructObject vs NewObject + ProcessEvent + 생성자 패턴 + **§2.7 표준 virtual 매트릭스** + **§2.10 const 메서드 const propagation** + **§2.11 FStructOnScope + TArray reallocation** + **§2.12 UE 글로벌 매크로 reserved 식별자** (모든 cpp 측면).

## 2. Key claims

### 2.1. 라이프사이클 (4 단계)

```
Constructor → PostInitProperties → (디스크 로드 시 PostLoad) → 사용
   → MarkAsGarbage → BeginDestroy → FinalizeDestroy
```

→ [[concepts/Object-Lifecycle]] 자세히.

### 2.2. Super 호출 규약

| virtual | Super | 위반 |
| -- | -- | -- |
| `PostInitProperties` | **FIRST** | UPROPERTY 미초기화 / CDO 마커 누락 |
| `PostLoad` | **FIRST** | 디스크 → 메모리 변환 미완성 |
| `BeginDestroy` | **LAST** | UObject 해제 마커 누락 |
| `FinalizeDestroy` | **LAST** | 최종 해제 자원 누수 |
| `Serialize` | **FIRST** | UPROPERTY 직렬화 손상 |

→ [[sources/ue-ref-04-overrideindex]] §1 통합.

### 2.3. NewObject 표준

```cpp
NewObject<T>(Outer, Class, Name, Flags, Template, bCopyTransientsFromClassDefaults);
```

- `Outer` 의무 — nullptr 시 즉시 GC 후보
- `RF_Transactional` flag — Editor undo support
- ConstructObject = deprecated → `NewObject` 사용

### 2.4. ProcessEvent

UFunction 호출 진입점. RPC / BlueprintImplementableEvent / BlueprintNativeEvent 의 thunk. `Execute_*` 매크로가 ProcessEvent 호출 ([[sources/ue-coreuobject-interface]] §5 #10).

### 2.5. Constructor 함정

- 자산 로드 금지 ([[concepts/Asset-Loading-Policy]]) — `ConstructorHelpers::FObjectFinder` deprecated
- CDO (Class Default Object) 가 항상 *먼저* 생성
- `HasAnyFlags(RF_ClassDefaultObject)` 검사로 CDO 분기 ([[concepts/Component-Policies-6]] §6)

### 2.6. NewObject Flags 핵심

| Flag | 의미 |
| -- | -- |
| `RF_NoFlags` | 디폴트 |
| `RF_Transactional` | Editor undo |
| `RF_ArchetypeObject` | Template |
| `RF_Transient` | 직렬화 제외 |
| `RF_Public` | 외부 참조 가능 |
| `RF_Standalone` | GC 보호 (Editor 자산) |

### 2.7. ⭐ Editor 표준 virtual 매트릭스 (2026-05-13 추가)

UObject 베이스에 정의된 **자주 마주치는 virtual** — 자손 작성 시 *이름 충돌 회피* 필수:

| virtual | 시그니처 | 가드 | 위치 |
| -- | -- | -- | -- |
| `PreEditChange` | `(FProperty*)` / `(FEditPropertyChain&)` | `WITH_EDITOR` | Object.h L431 / L439 |
| `CanEditChange` | `(FProperty*) const` | `WITH_EDITOR` | L450 |
| `PostEditChangeProperty` | `(FPropertyChangedEvent&)` | `WITH_EDITOR` | L473 |
| `PostEditChangeChainProperty` | `(FPropertyChangedChainEvent&)` | `WITH_EDITOR` | L479 |
| `PreEditUndo` / `PostEditUndo` | `()` | `WITH_EDITOR` | L485 / L488 |
| `PostTransacted` | `(FTransactionObjectEvent&)` | `WITH_EDITOR` | L498 |
| `PreSave` | `(FObjectPreSaveContext)` | (런타임) | L267 |
| `PostSave` | `(FObjectPostSaveContext)` | (런타임) | L275 |
| `Serialize` | `(FArchive&)` | (런타임) | L155 |
| `PostInitProperties` | `()` | (런타임) | L213 |
| `PostLoad` | `()` | (런타임) | L240 |
| `BeginDestroy` | `()` | (런타임) | L249 |
| `FinalizeDestroy` | `()` | (런타임) | L258 |
| `GetAssetRegistryTags` | `(FAssetRegistryTagsContext)` | `WITH_EDITORONLY_DATA` 영향 | L898 |
| ⭐ **`IsDataValid`** | **`(FDataValidationContext& Context) const`** | `WITH_EDITOR` (5.x) | **L1101** |
| (deprecated) `IsDataValid` | `(TArray<FText>& ValidationErrors)` | `WITH_EDITOR` (4.x) | L1111 |
| `BeginCacheForCookedPlatformData` | `(ITargetPlatform*)` | `WITH_EDITOR` | L1211 |
| `IsCachedCookedPlatformDataLoaded` | `(ITargetPlatform*)` | `WITH_EDITOR` | L1218 |

### 2.8. ⭐ Name hiding (C4264) 함정 (2026-05-13 추가) 🟢

(생략 — 기존 내용 유지)

**가장 흔한 케이스 — `IsDataValid` 무인자 BP 헬퍼**:

```cpp
// ❌ 자손 클래스
UCLASS()
class UMyData : public UAssetUserData
{
    UFUNCTION(BlueprintPure)
    bool IsDataValid() const;   // ← 베이스 IsDataValid(...) 모두 hidden — C4264
};
```

**회피 패턴 3종**:

| # | 패턴 | 권장도 |
| -- | -- | -- |
| 1 | **이름 변경** — `HasValid<Domain>()` / `Is<Domain>Valid()` | ⭐⭐⭐ 가장 안전 |
| 2 | `using UBase::IsDataValid;` 베이스 가시화 | ⭐⭐ |
| 3 | **5.x override 활용** — `virtual EDataValidationResult IsDataValid(FDataValidationContext&) const override;` | ⭐⭐⭐ 권장 |

KMCProject 검증 (2026-05-13) — `UMCHitBoneCurveUserData::IsDataValid()` → `HasValidBoneCurves()` + Phase 4 override.

### 2.9. ⭐ 5.x Editor Data Validation 시스템 통합 패턴 🟢

`IsDataValid(FDataValidationContext&)` override 가 "Validate Data" 메뉴 자동 통합. `Context.AddError/AddWarning` 사용.

KMCProject 사례 — `[[sources/ue-assetclasses-assetuserdata]]` §2.10 cross-link.

### 2.10. ⭐ const 메서드 안 GetOuter Cast — const propagation 함정 (C2440, 2026-05-14 추가) 🟢

(상세 기존 유지)

KMCProject 검증 — `UMCHitBoneCurveUserData::IsDataValid` line 266 — `const USkeleton* Skeleton = OwnerMesh->GetSkeleton();` 패턴 적용. log: `[2026-05-14] fix | C2440 fix`.

### 2.11. ⭐ FStructOnScope + UPROPERTY TArray reallocation 함정 (2026-05-14 추가, Cycle 5d 2차 후속 §2.11.1 보강) 🟢

(상세 기존 유지)

KMCProject 검증 — `BoneCurves.Reserve(256)` + IStructureDetailsView 매번 재생성 2중 방어. log: `[2026-05-14] fix | SCurveEditor dangling pointer`.

#### 2.11.1 ⭐⭐ 다른 customization 재현 검증 (2026-05-15 Cycle 5d 2차 후속) 🟢/🟡/🔴

**Cycle 5c §2.11 = KMCProject 1 사례 단독 (single-case)** — single-case 의 일반성 의심 회피를 위해 UE 5.7.4 Engine 의 `CreateStructureDetailView` / `IStructureDetailsView::SetStructureData` / `FStructOnScope` 다른 사용 사이트를 grep + 본문 검증한 결과:

##### 2.11.1.1 검증 대상 (UE Engine 23 사이트)

`grep "CreateStructureDetailView" Engine/Source` → **23 사이트** (PropertyEditor / Persona / Sequencer / DataTableEditor / StructUtilsEditor / MovieSceneTools / WorldPartitionEditor / WorldBookmark / UMGEditor / Kismet / GraphEditor / SequenceRecorder / Blutility / LevelInstanceEditor / CurveEditor / ClothPainter / EditorServer / SCurveEditorToolProperties / SAnimationBlendSpaceGridWidget / SAnimAttributeView / SCopyVertexColorSettingsPanel / SCreateClothingSettingsPanel / SNewLevelInstanceDialog).

##### 2.11.1.2 ⭐⭐⭐ UE Engine 자체 회피 패턴 (B 변종) — `FStructOnScope` 자손 override 🟢

**`Engine/Source/Editor/DataTableEditor/Private/SRowEditor.cpp:44-98`** 의 `FStructFromDataTable` 클래스:

```cpp
class FStructFromDataTable : public FStructOnScope
{
    TWeakObjectPtr<UDataTable> DataTable;
    FName RowName;
public:
    FStructFromDataTable(UDataTable* InDataTable, FName InRowName)
        : FStructOnScope(), DataTable(InDataTable), RowName(InRowName) {}

    // ⭐ 매 호출마다 *현재 메모리 위치 다시 조회* — TArray reallocation 후도 안전
    virtual uint8* GetStructMemory() override
    {
        return (DataTable.IsValid() && !RowName.IsNone()) ? DataTable->FindRowUnchecked(RowName) : nullptr;
    }
    virtual const uint8* GetStructMemory() const override { /* 동일 */ }

    virtual const UScriptStruct* GetStruct() const override
    {
        return DataTable.IsValid() ? DataTable->GetRowStruct() : nullptr;
    }
    // ...
};
```

**핵심 패턴** — UE Engine 의 **DataTable Editor 가 정확히 같은 함정을 회피하는 패턴**: `UDataTable::RowMap` (`TMap<FName, uint8*>`) 이 행 추가/삭제로 재배치돼도 `FName RowName` + `WeakObjectPtr<UDataTable>` 만 wrap → `GetStructMemory()` 가 **매번 lookup** → reallocation-safe.

→ **§2.11 함정은 single-case 가 아닌 일반 패턴**. KMCProject `UMCHitBoneCurveUserData` + UE Engine `SRowEditor` 2 사이트 재현 확인.

##### 2.11.1.3 ⭐⭐ 회피 패턴 매트릭스 (3종 확장) 🟢

| # | 패턴 | 권장도 | 사용처 | 비고 |
| -- | -- | -- | -- | -- |
| A ⭐ | **TArray.Reserve(N) + IStructureDetailsView 매번 재생성** | ⭐⭐ KMCProject 채용 | `UMCHitBoneCurveUserData` (Phase 4) | TArray 측 + 위젯 측 2중 방어 |
| B ⭐⭐ | **`FStructOnScope` 자손 + `GetStructMemory()` override (매번 lookup)** | ⭐⭐⭐ UE Engine 표준 | `SRowEditor` (DataTable) | 가장 robust — Wrap 자체가 동적 해석 |
| C | `FInstancedStructProvider` 사용 (`StructUtilsEditor`) | ⭐⭐ 5.x 신규 | `InstancedStructDetails.cpp:74` | `TArray<TSharedPtr<FStructOnScope>>` 반환 — wrap 외부 관리 |

##### 2.11.1.4 ⭐ 단일 인스턴스 멤버 wrap 의 stability 가정 (PerlinNoiseChannel 사례) 🟡

`Engine/Source/Editor/MovieSceneTools/Private/Channels/PerlinNoiseChannelInterface.cpp:152-188`:

```cpp
FPerlinNoiseParams* PerlinNoiseParams = &FloatChannel->PerlinNoiseParams;
// ...
TSharedRef<FStructOnScope> StructData = MakeShareable(
    new FStructOnScope(FPerlinNoiseParams::StaticStruct(), (uint8*)PerlinNoiseParams));
TSharedRef<IStructureDetailsView> DetailsView =
    EditModule.CreateStructureDetailView(DetailsViewArgs, StructureDetailsViewArgs, StructData);
```

**관찰** — `&FloatChannel->PerlinNoiseParams` 직접 멤버 주소를 wrap. `FloatChannel` (FMovieSceneFloatPerlinNoiseChannel) 이 *MovieScene Section 의 안정 식별자 (ChannelHandle) 로 가져온* 단일 인스턴스라 reallocation 위험 적음. 그러나 178행 코멘트:

```cpp
// The notify hook is owned by us. We will live as long as the menu is active, so as long as the
// NotifyHooks array isn't modified, the address of the hooks should be valid.
DetailsViewArgs.NotifyHook = &NotifyHooks[ChannelHandleIndex];
```

**🟢 UE Engine 자체가 §2.11 함정 인지** — `NotifyHooks` (TArray) 안 원소 주소를 외부에 전달하면서 "이 배열이 수정되지 않는 한 주소가 유효하다" 명시적 가정 문서화. menu 가 열려있는 동안 NotifyHooks 추가/삭제 금지 컨트랙.

→ §2.11 의 본질 = **"address-of-array-element" passing 패턴 일반화**. FStructOnScope 만의 함정이 아니라 **TArray 원소 주소를 외부 hold 하는 모든 시스템** 의 함정. NotifyHook / DelegateRef / Reflected Property* 등 다른 시스템도 동일 위험 — 🟡 *외삽 (외삽 부분 = "다른 시스템도 동일" — 추가 검증 필요)*.

##### 2.11.1.5 ⭐ 검증 결과 신뢰도 격상 (🟡 → 🟢) 🟢

| 항목 | Cycle 5c (2026-05-14) | Cycle 5d 2차 (2026-05-15) |
| -- | -- | -- |
| 검증 사이트 | KMCProject 1 (UMCHitBoneCurveUserData) | KMCProject 1 + UE Engine 2 (SRowEditor + PerlinNoise) |
| 신뢰도 | 🟡 single-case | 🟢 **재현 일반 패턴** |
| 회피 패턴 | 1 (Reserve + 매번 재생성) | **3** (A + B + C 매트릭스) |
| 일반성 | "KMCProject 특수" 의심 | UE Engine 표준 회피 패턴 (B) 발견 — 일반 |
| INFERRED 부분 | dangling 시 0xFFFF crash 일반성 | "다른 시스템 (NotifyHook 등) 도 동일 함정" = 🟡 외삽 |

##### 2.11.1.6 적용 권장 매트릭스

| 시나리오 | 권장 패턴 |
| -- | -- |
| 자산 안 `TArray<TStruct>` 의 *특정 원소* customization | **B** (자손 override) — 가장 robust |
| 자산 안 `TArray<TStruct>` 의 *모든 원소* customization (DataTable-like) | **B** + lookup key (RowName-like) |
| 단일 멤버 (`Asset->Settings`) customization | **A** (Reserve 불요) 또는 직접 wrap (PerlinNoise 패턴) — 단 array 원소면 컨트랙 명시 |
| 5.x `FInstancedStruct` polymorphic 데이터 | **C** (FInstancedStructProvider) |

##### 2.11.1.7 후속 검증 후보 (Cycle 5e+)

- [ ] `SRowEditor::FStructFromDataTable` 패턴을 KMCProject 자체 customization (Combo Section / Track) 에 채용 검토
- [ ] FInstancedStructProvider 의 5.x 안정성 (cross-reload / hot-reload)
- [ ] NotifyHook / Delegate 등 다른 array-element-pointer 시스템의 동일 함정 catalog (🟡 외삽 검증)

### 2.12. ⭐⭐⭐ UE 글로벌 매크로 reserved 식별자 함정 (2026-05-14 추가, 사용자 직접 진단) 🟢

#### 2.12.1 배경 — 글로벌 매크로 pollution

`Engine/Source/Runtime/Core/Public/Math/UnrealMathUtility.h` 가 **모든 cpp 가 transitive include 하는 글로벌 헤더**. 그 안 `#define PI ... (3.1415926535897932f)` 같은 매크로가 *변수 이름 / 식별자* 와 충돌 시 전처리기 단계에서 즉시 치환 → 컴파일 에러 또는 의미 변경.

#### 2.12.2 발견 사례 (2026-05-14)

```cpp
// SMCHitBoneCurveEditor.cpp — line 847
auto* PI = Mesh->PreviewInstance.Get();   // ❌ C2059
```

전처리기 치환 후:

```cpp
auto* (3.1415926535897932f) = Mesh->PreviewInstance.Get();
//      ↑ C2059 "구문 오류: 상수"
```

→ `PI` 매크로가 *상수 리터럴* 로 치환되어 변수 선언 안 됨.

🟢 **사용자 직접 진단** (2026-05-14) — vault 진단 시 잘못된 가설 (`UCLASS(MinimalAPI)`) 2회 반복 후 사용자가 root cause (PI 매크로) 발견. fix = 변수 이름 `_PreviewInstance` 변경.

#### 2.12.3 UE 글로벌 매크로 reserved 식별자 매트릭스 (11종 검증)

`UnrealMathUtility.h` + `Build.h` + 기타 global header 의 매크로:

| 매크로 | 정의 | 위치 | 충돌 위험 | 진단 신호 |
| -- | -- | -- | -- | -- |
| ⭐ **`PI`** | `(3.1415926535897932f)` | UnrealMathUtility.h L65/L129 | ⭐⭐⭐ 가장 흔함 | C2059 "구문 오류: 상수" |
| `INV_PI` | `(0.31830988618f)` | L79/L150 | ⭐ | 동일 |
| `HALF_PI` | `(1.57079632679f)` | L80/L151 | ⭐ | 동일 |
| `TWO_PI` | `(6.28318530717f)` | L81/L152 | ⭐ | 동일 |
| ⭐ **`SMALL_NUMBER`** | `(1.e-8f)` | L66/L130 | ⭐⭐ 변수 이름 흔함 | C2059 |
| ⭐ **`KINDA_SMALL_NUMBER`** | `(1.e-4f)` | L67/L131 | ⭐⭐ | 동일 |
| `BIG_NUMBER` | (UE 상수) | L68 | ⭐ | 동일 |
| `EULERS_NUMBER` | (UE 상수) | L69 | ⭐ | 동일 |
| `MAX_FLT` | (UE float 상한) | L78 | ⭐ (std FLT_MAX 와 다름) | 동일 |
| ⭐ **`check` / `CHECK`** | (assert macro) | Build.h | ⭐⭐⭐ silent pollution | 변수 `check` 사용 시 *함수 호출* 로 변경 |
| `verify` | (assert + retain in shipping) | Build.h | ⭐⭐ | 동일 |

#### 2.12.4 회피 패턴 3종

| # | 패턴 | 권장도 | 예시 |
| -- | -- | -- | -- |
| 1 ⭐ | **Underscore prefix** | ⭐⭐⭐ KMCProject 채용 (2026-05-14) | `_PreviewInstance` / `_check` / `_PI` |
| 2 | **도메인 prefix** | ⭐⭐⭐ 의미 명확 | `AnimPreviewInstance` / `MyCheck` / `LocalPi` |
| 3 | **`#undef PI`** before usage | ❌ 금지 — 전역 영향 + 다른 코드 충돌 | (사용 금지) |

#### 2.12.5 KMCProject 채용 규약

```cpp
// ❌ C2059 — PI 매크로 치환
auto* PI = Mesh->PreviewInstance.Get();
float Pi = 3.14f;
int32 SMALL_NUMBER = 1;
bool check = true;

// ✅ 회피 — underscore prefix (KMCProject 표준)
auto* _PreviewInstance = Mesh->PreviewInstance.Get();
float MyPi = 3.14f;
int32 LocalSmallNumber = 1;
bool bCheckOK = true;
```

KMCProject 검증 (2026-05-14) — `SMCHitBoneCurveEditor.cpp` 의 `auto* PI` → `auto* _PreviewInstance` 변경 후 빌드 통과. log: `[2026-05-14] fix | ⚠ 자체 평가 정정 — Phase 5 C2059 진짜 원인 = UE PI 매크로`.

#### 2.12.6 진단 가이드 — C2059 "구문 오류: 상수"

C2059 with "상수" / "constant" 토큰 = **매크로 치환 의심 #1**.

```
[진단 순서]
1. 에러 라인의 *모든 식별자* 를 UE 글로벌 매크로 매트릭스 (§2.12.3) 와 대조
2. 매칭 식별자 발견 시 변수 이름 변경 (underscore prefix)
3. 매칭 없으면 다른 함정 (type 인식 실패 / template 의존 등) 검토
```

⭐ **교훈** — `auto*` 도 매크로 치환 영향 받음 (auto 가 type 추론 *전* 전처리기가 식별자 치환). type 인식 실패 가설 검증 *전* 매크로 치환 가설 우선.

#### 2.12.7 자체 평가 (Article 1 Evaluator) — 진단 실패 사례

vault 가 2회 잘못된 진단:
1. ToolMenus include path 문제 (1차) — 무관
2. `UCLASS(MinimalAPI)` 외부 모듈 막힘 (2차) — *그럴듯해 보였지만 잘못*

진짜 원인 = §2.12 매크로 식별자 충돌 (사용자 진단).

**교훈**:
- C2059 "상수" 신호 → **매크로 pollution 가설 *제일 먼저***
- *MinimalAPI* 등 attribute 가설 보다 *전처리기 단계 함정* 우선 의심
- 우회로 (symptom fix) vs 진짜 진단 (root cause) 구분 의무

### 2.13. ⭐⭐⭐ forward-declared UObject 자손 → `UObject*` 인자 변환 실패 (C2664, 2026-05-15 추가, KMCProject MCComboEditor 실측) 🟢

#### 2.13.1 배경 — forward declare 의 type 가시성 한계

C++ forward declaration (`class UMyType;`) 는 컴파일러에게 *type 이름 만* 알리고 **(a) size, (b) layout, (c) inheritance chain** 모두 모른다고 명시. 포인터/참조 멤버 선언 또는 함수 시그니처에는 충분하지만, **upcast 가 필요한 호출 사이트** 는 inheritance chain 가시성 필요 → forward declare 만으로는 불가.

UObject 계열에서 자주 마주치는 함정: 토킷 / 매니저 헤더가 도메인 자산 (`UMyAsset`) 을 forward declare 한 상태에서 cpp 가 그 자산을 받아 `IDetailsView::SetObject(UObject*)` / `UAssetEditorSubsystem::OpenEditorForAsset(UObject*)` 등 **`UObject*` 인자 함수** 에 전달하려 하면 컴파일러가 `UMyAsset → UDataAsset → UObject` 상속 체인을 모름 → upcast 거부.

#### 2.13.2 함정 시그니처 (MSVC C2664)

```
error C2664: 'void IDetailsView::SetObject(UObject *,bool)':
    인수 1을(를) 'UMCComboAsset *'에서 'UObject *'(으)로 변환할 수 없습니다.
```

#### 2.13.3 발견 사례 (KMCProject MCComboEditor — `MCComboAssetPrimaryTabFactory.cpp:85`)

```cpp
// ❌ MCComboAssetEditorApplication.h
#include "WorkflowOrientedApp/WorkflowCentricApplication.h"
class UMCComboAsset;   // forward declare
class IDetailsView;

class FMCComboAssetEditorApplication : public FWorkflowCentricApplication, ...
{
public:
    UMCComboAsset* GetCurrentAsset() const { return CurrentAsset; }   // 반환형 UMCComboAsset*
    ...
};

// ❌ MCComboAssetPrimaryTabFactory.cpp
#include "MCComboAssetEditorApplication.h"   // UMCComboAsset 은 여전히 forward declare 만 본 상태
// (MCComboAsset.h 미인클루드)
// ...
TSharedRef<IDetailsView> DetailView = PropertyEditorModule.CreateDetailView(DetailsViewArgs);
DetailView->SetObject(Pinned->GetCurrentAsset());   // ← C2664: UMCComboAsset* → UObject* 변환 불가
```

#### 2.13.4 정답 — cpp 에 full include 추가

```cpp
// ✅ MCComboAssetPrimaryTabFactory.cpp
#include "MCComboAssetEditorApplication.h"
#include "KMCProject/MCPlayModule/MCCombo/MCComboAsset.h"   // ⭐ full include — UObject 상속 체인 가시화
// ...
DetailView->SetObject(Pinned->GetCurrentAsset());   // OK — UMCComboAsset → UDataAsset → UObject upcast
```

KMCProject 검증 (2026-05-15) — full include 추가 후 빌드 통과. log: `[2026-05-15] fix | MCComboEditor C2664 SetObject — full include 추가`.

#### 2.13.5 회피 패턴 매트릭스

| # | 패턴 | 권장도 | 비고 |
| -- | -- | -- | -- |
| 1 ⭐ | **cpp 에 full include 추가** | ⭐⭐⭐ 표준 | 헤더는 forward declare 유지 → 의존성 그래프 최소 |
| 2 | **헤더에 full include 이동** | ⭐ | include 그래프 전염 — 다른 cpp 빌드 시간 ↑ |
| 3 | `static_cast<UObject*>(자손Ptr)` 명시 | ❌ 금지 | 컴파일러는 여전히 상속 체인 모름 → C2440 추가 발생 — 무의미 |
| 4 | `reinterpret_cast<UObject*>(자손Ptr)` | ❌ 절대 금지 | UB — 다중 상속 시 vtable 오프셋 무시 |

#### 2.13.6 C2664 vs C2440 vs C4264 — UObject 자손 관련 변환 함정 3종 매트릭스

| 함정 | 에러 코드 | 트리거 | 원인 카테고리 | 정답 |
| -- | -- | -- | -- | -- |
| **§2.13** forward-declared upcast | C2664 (변환 실패) | `UObject*` 인자 함수에 forward-declared `UMyAsset*` 전달 | **type 가시성** (preprocess) | cpp 에 full include |
| **§2.10** const propagation | C2440 (변환 거부) | `const T*` → `T*` 비-const 변수 대입 | **const-correctness** (semantic) | `const T*` 받기 / const 오버로드 호출 |
| **§2.8** name hiding | C4264 (warning, /WX → error) | 자손 BP 헬퍼 이름이 베이스 virtual 와 충돌 | **lookup 규칙** (overload resolution) | 도메인 prefix `Has<Foo>Valid` |

**핵심 구분** — §2.13 은 **preprocess 단계** (translation unit 이 상속 체인을 보지 못함) 함정이라 cpp 에서 한 줄 include 추가로 해결. §2.10 / §2.8 은 **semantic 분석 단계** 함정이라 코드 패턴 변경 필요.

#### 2.13.7 진단 가이드 — `error C2664`

```
[진단 순서]
1. 에러 메시지의 "인수 N 을(를) 'T1 *' 에서 'T2 *' (으)로 변환할 수 없습니다" 패턴 확인
2. T2 가 T1 의 베이스 (직간접) 일 가능성 검토 — IsA / Cast 가 컴파일되지 않으면 §2.13 강력 의심
3. T1 의 헤더가 같은 translation unit 에서 full include 됐는지 확인 (forward declare 단독이면 §2.13 확정)
4. fix = cpp 에 full include 추가 (헤더가 아닌 cpp — 의존 그래프 최소)
```

#### 2.13.8 예방 — 헤더 작성 규약 (KMCProject 채용)

- **헤더 (`.h`)** — 도메인 자산 forward declare 유지 (`class UMyAsset;`) — 컴파일 단위 의존 최소
- **cpp (`.cpp`)** — 헤더가 forward declare 한 자산을 *함수에 전달* / *상속 체인이 필요한 호출* 에 사용하면 full include 의무
- ⭐ **체크리스트** — cpp 작성 시 다음 호출 패턴은 자산 헤더 include 검증 의무:
  - `IDetailsView::SetObject(UObject*)` / `SetObjects(TArray<UObject*>&)`
  - `UAssetEditorSubsystem::OpenEditorForAsset(UObject*)`
  - `FAssetEditorToolkit::AddEditingObject(UObject*)`
  - `UFactory::FactoryCreateNew` 반환 `UObject*`
  - `NewObject<T>(Outer, ...)` 의 `Outer` 가 forward-declared 자손이면 동일 함정

### 2.14. ⭐⭐⭐ Instanced Track/Section 4 UCLASS meta 표준 (2026-05-15 추가, KMCProject MCComboEditor 실측) 🟢

#### 2.14.1 배경 — LevelSequence MovieScene Track 데이터 모델 차용 표준

LevelSequence `UMovieSceneTrack` / `UMovieSceneSection` 의 디자이너 친화 데이터 모델은 **`Instanced` 자손 컨테이너 패턴** 에 의존. 같은 패턴을 도메인 자산 (combo / dialogue / cutscene-lite 등) 에 차용 시 **4 UCLASS meta** + **페어 UPROPERTY meta** 표준이 필수 — 어느 하나 누락 시 Detail Panel "+" 버튼 비활성 / BP 자손 작성 차단 / Outer 직렬화 실패 등 다양한 증상.

→ [[sources/ue-levelsequence-moviescene]] §2.4 (Track), §2.5 (Section) 데이터 모델 베이스.

#### 2.14.2 표준 4 UCLASS meta + 페어 UPROPERTY meta

```cpp
// ✅ Track / Section 베이스 표준 (KMCProject UMCComboTrack / UMCComboSection 적용)
UCLASS(Abstract, EditInlineNew, DefaultToInstanced, BlueprintType, Blueprintable)
class MCPLAYMODULE_API UMCComboTrack : public UObject
{
    GENERATED_BODY()
public:
    // 페어 UPROPERTY — Instanced + TObjectPtr<> 5.x 표준
    UPROPERTY(EditAnywhere, Instanced, Category = "Combo|Sections")
    TArray<TObjectPtr<UMCComboSection>> Sections;

    // 자손이 어떤 Section 클래스를 만들 지
    virtual TSubclassOf<UMCComboSection> SupportsSectionClass() const
        PURE_VIRTUAL(UMCComboTrack::SupportsSectionClass, return nullptr;);
};
```

```cpp
// 컨테이너 자산 (UMovieScene 위치) — Track 배열 보유
UCLASS(BlueprintType)
class MCPLAYMODULE_API UMCComboAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Instanced, Category = "Combo|Tracks")
    TArray<TObjectPtr<UMCComboTrack>> Tracks;
};
```

#### 2.14.3 각 meta 의 의무 이유 + 누락 시 증상

| meta | 위치 | 의무 이유 | 누락 시 증상 |
| -- | -- | -- | -- |
| `Abstract` | UCLASS | 자손이 `SupportsSectionClass()` 등 PURE_VIRTUAL override 강제 | 베이스 직접 인스턴스화 가능 → 의미 없는 Section 생성 |
| `EditInlineNew` | UCLASS | Detail Panel "+" 버튼 누르면 자손 클래스 인스턴스화 picker 표시 | "+" 비활성 — 디자이너가 Section 추가 불가 |
| `DefaultToInstanced` | UCLASS | Outer 자산이 인스턴스 ownership — 직렬화 시 같은 패키지 안 저장 | Reference 직렬화 → 자산 외부 reference fail / GC 즉시 |
| `BlueprintType` | UCLASS | BP 변수 / 함수 인자 / 반환형으로 사용 가능 | BP 그래프에서 type 인식 불가 |
| `Blueprintable` | UCLASS | 디자이너가 BP 로 자손 작성 가능 | BP 자손 작성 picker 에 미표시 — 디자이너 확장 차단 |
| `EditAnywhere` | UPROPERTY | Detail Panel 에서 array 편집 가능 | array 회색 — 추가/삭제 불가 |
| `Instanced` | UPROPERTY | 배열 원소가 인스턴스 ownership (UCLASS `DefaultToInstanced` 와 페어) | "+" 버튼 비활성 |
| `TObjectPtr<>` (5.x) | UPROPERTY type | Lazy resolve + Editor undo / hot-reload 안전 | raw `U*` 도 동작하나 5.x deprecated 경고 |

#### 2.14.4 4 UCLASS meta 의 상호 의존 매트릭스

| 시나리오 | 4 meta 필요성 |
| -- | -- |
| C++ 자손만 작성 + 베이스 직접 사용 안 함 | `Abstract` + `EditInlineNew` + `DefaultToInstanced` (3) — Blueprintable/BlueprintType 생략 가능 |
| BP 디자이너가 자손 작성 | `BlueprintType` + `Blueprintable` 추가 필수 (5) |
| Outer 자산이 Section/Track 을 같은 패키지에 저장 | `DefaultToInstanced` 의무 |
| Detail Panel 인라인 편집 | `EditInlineNew` 의무 + UPROPERTY `Instanced` 페어 |

⭐ **권장 — 4 (또는 5) 모두 항상 명시** — 디자이너 확장 미래 가능성 + Outer 직렬화 안전 보장.

#### 2.14.5 LevelSequence 와의 매핑

| LevelSequence | KMCProject 도메인 차용 |
| -- | -- |
| `UMovieScene` (`UMovieSceneSignedObject` 자손) | `UMCComboAsset` (`UDataAsset` 자손 — 14 PURE_VIRTUAL 부담 회피) |
| `UMovieSceneTrack` `UCLASS(MovieSceneTrackClass, ..., DefaultToInstanced)` | `UMCComboTrack` `UCLASS(Abstract, EditInlineNew, DefaultToInstanced, BlueprintType, Blueprintable)` |
| `UMovieSceneSection` `UCLASS(BlueprintType, DefaultToInstanced)` | `UMCComboSection` `UCLASS(Abstract, EditInlineNew, DefaultToInstanced, BlueprintType, Blueprintable)` |

⭐ **차이** — LevelSequence 는 `Sequencer` 모듈이 자손 인스턴스화를 담당 → `EditInlineNew` 가 필수 아님. KMCProject 는 *자체 Slate 트랙 패널* 이라 Detail Panel "+" 가 주 인스턴스화 경로 → `EditInlineNew` 필수.

#### 2.14.6 함정 매트릭스 — 4 meta 누락 시 실측

| 누락 | 빌드 | Editor | 런타임 | 진단 |
| -- | -- | -- | -- | -- |
| `Abstract` | ✅ | 베이스 인스턴스 picker 표시 | 의미 없는 빈 Section | 자손 picker 만 보이게 강제 |
| `EditInlineNew` | ✅ | "+" 버튼 비활성 | (영향 없음) | Detail Panel array 어두움 시 의심 |
| `DefaultToInstanced` | ✅ | 추가 OK / 저장 시 reference 직렬화 | **GC 즉시** — Outer 가 자산 외부 reference 보유 | log: "Failed to load referenced object" |
| `BlueprintType` | ✅ | (BP 미사용 시 영향 없음) | BP 변수 type picker 미표시 | BP 그래프 type-name 적색 |
| `Blueprintable` | ✅ | BP 자손 picker 차단 | (영향 없음) | "Create Blueprint Class" 메뉴에 미표시 |
| UPROPERTY `Instanced` | ✅ | "+" 비활성 | (영향 없음) | UCLASS `EditInlineNew` 있어도 동일 — UPROPERTY 페어 필수 |

KMCProject 검증 (2026-05-15) — `UMCComboTrack` / `UMCComboSection` 4 meta + `Instanced` UPROPERTY 모두 명시. Detail Panel "+" → InputTrack/MontageTrack/NotifyTrack 자손 인스턴스화 + Section "+" → 자손 픽커 표시 동작 확인. log: `[2026-05-15] feature | MCComboEditor Phase 1 — Track/Section 4 meta 표준 + Instanced UPROPERTY 페어`.

## 3. Quotations

> "PostInitProperties 는 매 NewObject. PostLoad 는 디스크 deserialize 후만."

> "자손 클래스에 베이스와 같은 이름 함수 정의 시 베이스의 *모든 오버로드* hidden — C4264." (2026-05-13)

> "const 메서드 안 GetOuter Cast 결과는 const 의무 — const 오버로드 자동 호출 → const 반환 propagate." (2026-05-14)

> "`FStructOnScope` 가 wrap 한 `TArray<T>[Index]` 메모리는 reallocation 시 stale → 0xFFFFFFFFFFFFFFFF crash. Reserve(N) + 위젯 매번 재생성 2중 방어." (2026-05-14)

> "C2059 '상수' 신호 시 *매크로 pollution* 가설 우선 — UE 의 `#define PI` 등 글로벌 매크로가 변수 이름 치환. type/attribute 가설보다 전처리기 단계 함정 먼저 의심." (2026-05-14 KMCProject 사용자 진단)

> "C2664 'UMyAsset\* 에서 UObject\* 변환 불가' 신호 시 forward declare 가설 우선 — translation unit 이 상속 체인을 보지 못함. cpp 에 full include 한 줄 추가가 표준. static_cast/reinterpret_cast 우회 금지." (2026-05-15 KMCProject MCComboEditor 실측)

> "Track/Section 데이터 모델 차용 시 4 UCLASS meta (`Abstract` + `EditInlineNew` + `DefaultToInstanced` + `Blueprintable`/`BlueprintType`) + 페어 UPROPERTY `Instanced` 매트릭스 의무 — 누락 시 Detail Panel '+' 비활성 / Outer 직렬화 reference 누출 / 디자이너 확장 차단." (2026-05-15 KMCProject UMCComboTrack 적용)

## 4. 함정 / 안티패턴 (11대)

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | Constructor 안 자산 로드 | [[concepts/Asset-Loading-Policy]] PreLoad 패턴 |
| 2 | CDO 검사 누락 | `HasAnyFlags(RF_ClassDefaultObject)` |
| 3 | NewObject Outer = nullptr | 의무 — GC 즉시 |
| 4 | Editor virtual 무가드 (`PostEditChangeProperty` etc.) | `#if WITH_EDITOR` |
| 5 | `MarkPendingKill` 사용 (4.x deprecated) | `MarkAsGarbage` (5.x) |
| 6 ⭐ | **자손 BP 헬퍼에 베이스 virtual 이름 사용 (C4264)** | 도메인 prefix — `HasValid<Foo>` (§2.8) |
| 7 ⭐ | **const 메서드 안 GetOuter Cast → 비-const 변수 대입 (C2440)** | const 받기 — `const URes* X = Owner->GetRes();` (§2.10) |
| 8 ⭐⭐ | **FStructOnScope 가 wrap 한 TArray 원소 메모리 stale** (🟢 일반 패턴 — UE Engine `SRowEditor` 재현) | (A) TArray.Reserve(N) + widget 측 매번 재생성 / (B) **FStructOnScope 자손 override (UE Engine 표준)** / (C) FInstancedStructProvider (5.x) (§2.11 + §2.11.1) |
| 9 ⭐⭐⭐ | **UE 글로벌 매크로 reserved 식별자 변수 이름 충돌 (C2059)** | underscore prefix (`_PreviewInstance`) 또는 도메인 prefix (§2.12) |
| **10** ⭐⭐⭐ | **forward-declared UObject 자손 → `UObject*` 인자 변환 실패 (C2664)** | cpp 에 full include 추가 — `static_cast` 우회 금지 (§2.13) |
| **11** ⭐⭐⭐ | **Instanced Track/Section UCLASS 4 meta + UPROPERTY `Instanced` 페어 누락** | `Abstract` + `EditInlineNew` + `DefaultToInstanced` + `Blueprintable` + UPROPERTY `Instanced` (§2.14) |

## 5. Cross-link

### Sub-skill

- [[sources/ue-coreuobject-skill]] (parent) · [[sources/ue-coreuobject-reflection]] · [[sources/ue-coreuobject-gc]] · [[sources/ue-coreuobject-serialization]] · [[sources/ue-coreuobject-network]] · [[sources/ue-coreuobject-editor]]

### Concepts

- [[concepts/Object-Lifecycle]] · [[concepts/Garbage-Collection]] · [[concepts/Reflection-System]] · [[concepts/Component-Policies-6]] §6 (CDO) · [[concepts/Asset-Loading-Policy]]

### 횡단 정책

- [[sources/ue-ref-04-overrideindex]] §1 (UObject virtual + Super 통합)
- [[sources/ue-ref-05-editoronlyindex]] (Editor virtual 가드)
- [[sources/ue-ref-07-profilingscopeRule]]

### 적용 사례 매트릭스

- [[sources/ue-assetclasses-assetuserdata]] §2.10 (UAssetUserData 자손 Phase 4)
- [[sources/ue-coreuobject-interface]] §5 함정 (Interface name hiding)
- [[sources/ue-assetclasses-mesh]] §3 (GetSkeleton const 오버로드 — §2.10 페어)
- [[sources/mc-asset-validation-policy]] §11 + §12 (const-correctness 체크리스트 + 변수 이름 회피 규약)
- [[sources/ue-editor-propertyeditor]] §2.8 (IStructureDetailsView 매번 재생성 — §2.11 widget 측 짝)
- [[sources/ue-editor-personatoolkit]] §2.7-2.8 (FPersonaModule::OnRegisterTabs + UAnimPreviewInstance ModifyBone)
- [[sources/ue-editor-unrealed-asseteditortoolkit]] §2.15 (WorkflowOrientedApp 폴더 vs 모듈 — Cycle 5d 페어)
- [[sources/ue-levelsequence-moviescene]] §2.3-2.5 (Track/Section 데이터 모델 베이스 — §2.14 매핑 출처)
- [[synthesis/mc-character-hit-reaction-pipeline]] §6 (KMCProject Hit Curve 시스템 — §2.10/§2.11/§2.12 적용 사례)
- [[synthesis/mc-combo-editor-levelsequence-lite]] (KMCProject MCComboEditor — §2.13/§2.14 적용 사례, Cycle 5d)
- [[synthesis/actor-lifecycle-edge-cases]] (Actor 라이프사이클 함정 — UObject GC/Destroy 페어)
- [[synthesis/component-vs-actor-lifecycle-table]] (Component vs Actor 라이프사이클 매트릭스 — UObject 베이스)
- [[synthesis/spawnactor-hitching-4-step-pattern]] (SpawnActor 히칭 회피 4단 — UObject 생성 베이스)

### Cycle 5l reverse-link 보강 (Cycle 5k Phase 4 suggest_missing 결과)

- [[sources/ue-meta-improvement-roadmap]] (UObject 함정 카탈로그가 P0~P3 우선순위 매트릭스에 4회 인용)
- [[sources/ue-meta-confidence-tags]] (UObject §2.11.1 격상 사례가 🟢/🟡/🔴 tier 매트릭스에 2회 인용)
- [[sources/ue-meta-corrections]] (UObject 정정 6건 매트릭스 — Phase 5 PI 매크로 자체 진단 실패 등)
- [[sources/ue-meta-honest-limits]] (UObject §2.11.1 검증 사이트 ~65% 격상 인용)

### 관련 fix log

- `[2026-05-13] fix | UMCHitBoneCurveUserData::IsDataValid() C4264` — §2.8 1차 검증
- `[2026-05-14] fix | C2440 fix — USkeletalMesh::GetSkeleton() const` — §2.10 1차 검증
- `[2026-05-14] fix | SCurveEditor dangling pointer + Reserve(256)` — §2.11 1차 검증
- ⭐ `[2026-05-14] fix | ⚠ 자체 평가 정정 — Phase 5 C2059 진짜 원인 = UE PI 매크로` — §2.12 1차 검증 (사용자 직접 진단)
- ⭐⭐⭐ `[2026-05-15] fix | MCComboEditor C2664 SetObject — full include 추가` — §2.13 1차 검증
- ⭐⭐⭐ `[2026-05-15] feature | MCComboEditor Phase 1 — Track/Section 4 meta + Instanced UPROPERTY 페어` — §2.14 1차 검증
- ⭐⭐ `[2026-05-15] note | Cycle 5d 2차 §2.11.1 — UE Engine SRowEditor + PerlinNoiseChannel 다른 사이트 검증` — §2.11.1 (single-case 🟡 → 일반 패턴 🟢 격상, UE Engine 자체 회피 패턴 B "FStructOnScope 자손 override" 발견)

## 6. 후속 검증 후보

- [ ] §2.7 Editor virtual 매트릭스의 다른 함수 (`Serialize` / `GetWorld` 등) 의 자손 이름 충돌 사례
- [ ] §2.9 `CombineDataValidationResults` 헬퍼 정확한 사용 패턴
- [ ] §2.10 매트릭스의 다른 const 오버로드 함수 검증
- [ ] §2.11.5 영향 받는 패턴 매트릭스 — AnimGraph FAnimNode 자손 안 raw 캐시 실증
- [x] §2.11.1 다른 customization 재현 검증 — UE Engine SRowEditor + PerlinNoise + InstancedStructDetails 3 사이트 (2026-05-15 Cycle 5d 2차 완료)
- [ ] §2.11.1.4 NotifyHook / Delegate 등 다른 array-element-pointer 시스템 동일 함정 catalog (🟡 외삽 검증)
- [ ] §2.12.3 다른 글로벌 매크로 확장 — `DELTA` / `INDEX_NONE` / `NAME_None` 등 KMCProject 자체 매크로와 충돌 검토
- [ ] §2.12 clang-tidy / static analyzer 자동 검출 룰 — vault `[[synthesis/validation-static-analysis-ide-integration]]` 통합
- [ ] §2.13.8 cpp include 누락 자동 검출 — IWYU (`include-what-you-use`) 통합 검토
- [ ] §2.14 LevelSequence `Sequencer` 모듈 자손 인스턴스화 경로 vs 자체 Slate 트랙 패널 경로의 meta 차이 깊이 비교
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
