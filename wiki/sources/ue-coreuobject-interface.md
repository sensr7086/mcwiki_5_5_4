---
type: source
title: "UE CoreUObject — Interface sub-skill"
slug: ue-coreuobject-interface
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Interface.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/UInterface]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/Pimpl-TUniquePtr-Destructor]]"
tags: [ue, runtime, foundation, coreuobject, interface, pitfalls, verified-2x]
---

# UE CoreUObject — Interface sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Interface.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

UINTERFACE + IInterface 패턴 — UE 의 인터페이스 메커니즘. TScriptInterface + Execute_* 매크로 + Implements<T> + BP 지원 (BlueprintType / Native-Only Cannot / MinimalAPI). **§5 함정 매트릭스 11종 + §6 결정 트리 + §7 specifier 매트릭스 — KMCProject 빌드 에러 다회 사례 (2026-05-13) 에서 발견·재현 검증. §5 #1 은 *2회 재현 확인* (`MCPoolableInterface` + `MCSpatialQueryFilterable`) ⭐⭐ 신뢰도 승격.**

## 2. Key claims

- UE Interface = 2 클래스 페어: UMyInterface (UINTERFACE 메타) + IMyInterface (실제 인터페이스). UMyInterface = reflection 정보, IMyInterface = 메서드.
- UFUNCTION(BlueprintCallable, BlueprintImplementableEvent) — Interface 메서드의 BP 호출 + BP 구현. C++ 호출 시 `Execute_MyMethod(Object, Args...)` 매크로.
- TScriptInterface<IMyInterface> Wrapper — UObject + Interface 양쪽 보유. UPROPERTY 안전.
- Implements<T>(): Object 가 인터페이스 구현하는지 검사.
- BP 지원 분기:
  - **BlueprintType**: BP 가 인터페이스를 *변수 타입* 으로 사용 가능 (Cast / Switch).
  - **Blueprintable**: BP 가 인터페이스 *구현* 가능 — `BlueprintNativeEvent` / `BlueprintImplementableEvent` 사용 가능.
  - **NotBlueprintable** (또는 평범한 UINTERFACE): C++ 만 구현 가능.
  - **MinimalAPI**: 다른 모듈에서 cast 가능 (export 메타).
- C++ 호출 표준: `IMyInterface::Execute_MyMethod(Obj, Args)` — Obj 가 BP 구현한 경우도 안전.

## 3. Quotations

> "UMyInterface = reflection. IMyInterface = methods. C++ 호출 시 Execute_* 매크로."

## 4. Open questions

- [x] **BP 인터페이스 vs Native 인터페이스 결정 트리** — §6 추가 (2026-05-13).
- [ ] UINTERFACE 의 multiple inheritance 함정 — §5 #7 부분 다룸, 정밀 후속.

## 5. 함정 / 안티패턴 (11종 — 2026-05-13)

KMCProject 빌드 에러 / 일반 UE 5.x 함정. # 1·2·3 + #11 = **실제 컴파일 에러 검증** (🟢 VAULT). 나머지는 일반 UE 5.x 지식 (🟡 PARTIAL — Engine source 직접 인용은 후속).

### #1 🟢⭐⭐ `meta=(CannotImplementInterfaceInBlueprint=false)` 가 *반대로* 처리됨 — **2회 재현 확인**

```cpp
// ❌ 의도 — BP 구현 가능 하게 하려고 false 명시 (혹은 "false" 문자열 표기)
UINTERFACE(MinimalAPI, BlueprintType, meta=(CannotImplementInterfaceInBlueprint=false))
class UMyInterface : public UInterface { GENERATED_BODY() };

// 또는 본 cycle 의 두 번째 재현 — "false" 문자열 형태
UINTERFACE(BlueprintType, Blueprintable, meta=(CannotImplementInterfaceInBlueprint="false"))
class MCPLAYMODULE_API UMCSpatialQueryFilterable : public UInterface { GENERATED_BODY() };

// → UHT 에러 (두 케이스 동일):
//   "Interfaces that are not implementable in blueprints cannot have Blueprint Event members."
```

**원인**: UHT 의 meta 시스템은 **키 존재 = true** 로 처리. `=false` 명시 또는 `="false"` 문자열 명시는 일부 negative meta 에서만 인식되며, `CannotImplementInterfaceInBlueprint` 는 해당 안 됨 → 키 존재 자체가 "BP 구현 불가" 를 의미 → `BlueprintNativeEvent` 멤버 거부.

`Blueprintable` specifier 가 함께 있어도 meta 가 *우선* — `Blueprintable` 만으로 자동 해결 안 됨.

**정답**:
```cpp
// ✅ MCPoolableInterface / 두 번째 사례 (MCSpatialQueryFilterable) 정답 동일
UINTERFACE(MinimalAPI, Blueprintable, BlueprintType)
class UMyInterface : public UInterface { GENERATED_BODY() };
```

→ `Blueprintable` specifier 가 BP 구현 활성. `meta=(CannotImplementInterfaceInBlueprint)` 는 *반대* 의도일 때만 사용 (그것도 `NotBlueprintable` specifier 가 더 명확).

**KMCProject 검증 사례 (🟢⭐⭐ 2회 재현)**:

| 사례 | 일자 | 위치 | log entry |
| -- | -- | -- | -- |
| **1차** | 2026-05-13 | `MCPoolableInterface.h` | `[2026-05-13] fix \| MCPoolableInterface — UHT 컴파일 에러 수정` |
| **2차 (본 항목)** | 2026-05-13 | `MCSpatialQueryFilterable.h` | `[2026-05-13] fix \| UMCSpatialQueryFilterable — UINTERFACE meta=(CannotImplementInterfaceInBlueprint="false") UHT 역대 처리 함정 재현` |

⭐⭐ **vault 카탈로그 가치 입증** — 동일 함정 2회 발생 = 작업자가 vault 즉시 인지 시 *1 시도 해결* (vault 없으면 3+ 시도 예상). [[sources/ue-measure-summary]] H1 추적에 기여.

### #2 🟢 `BlueprintPure` interface function 에 금지

```cpp
// ❌ UHT 에러
UFUNCTION(BlueprintNativeEvent, BlueprintCallable, BlueprintPure, Category="MC")
bool IsActive() const;

// → "BlueprintPure specifier is not allowed for interface functions"
```

**원인**: UE 5.x UHT 가 interface 함수에 `BlueprintPure` 명시 거부. interface 의 BP override 시 const 보장이 어려움이 이유로 추정 (🔴 Engine source 확인 필요).

**정답**:
```cpp
// ✅ const + BlueprintCallable → BP 에서 자동 Pure 처리
UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MC")
bool IsActive() const;
```

`const` 한정자 + `BlueprintCallable` 만 사용. BP 에서는 const 함수가 자동으로 pure 처리됨 (input pin 없음, output pin 만).

### #3 🟢 `BlueprintNativeEvent` 멤버에 `Blueprintable` 누락

```cpp
// ❌ UHT 에러
UINTERFACE(MinimalAPI)   // Blueprintable 누락
class UMyInterface : public UInterface { GENERATED_BODY() };

class IMyInterface
{
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable)
    void DoSomething();
};

// → "Interfaces that are not implementable in blueprints cannot have Blueprint Event members."
```

**원인**: `BlueprintNativeEvent` / `BlueprintImplementableEvent` 는 BP override 능력 필요 → UINTERFACE 에 `Blueprintable` 필수.

**구분 — #1 vs #3 같은 에러 메시지의 두 원인**:

| 함정 | meta | Blueprintable specifier | 결과 |
| -- | -- | -- | -- |
| #1 | `CannotImplementInterfaceInBlueprint` 존재 (값 무관) | 있음 ✅ | meta 가 우선 → BP impl 차단 |
| #3 | 없음 | 누락 ❌ | specifier 없음 → BP impl 차단 |

⭐ 같은 UHT 에러 메시지지만 *원인 진단* 다름. 빌드 에러 시 양쪽 동시 점검.

**정답**:
```cpp
UINTERFACE(MinimalAPI, Blueprintable)
class UMyInterface : public UInterface { GENERATED_BODY() };
```

### #4 🟡 `Cast<IFoo>(Obj)` 가 BP 구현 객체에 nullptr 반환

```cpp
// ❌ BP 가 IFoo 를 구현하면 dynamic_cast 가 IFoo* 못 찾음
IFoo* Foo = Cast<IFoo>(SomeObject);   // BP impl 인 경우 nullptr
if (Foo) Foo->Bar();                    // 진입 X

// ✅ 표준
if (SomeObject->Implements<UFoo>())   // UFoo (메타) 검사
{
    IFoo::Execute_Bar(SomeObject);    // Execute_* 가 BP override 자동 디스패치
}
```

**원인**: BP 구현은 IFoo C++ vtable 에 없음 → `Cast<>` (또는 `dynamic_cast`) 가 nullptr. `Implements<UFoo>()` + `Execute_*` 패턴이 표준.

### #5 🟡 UPROPERTY 에 raw `IInterface*` 사용

```cpp
// ❌ GC 추적 안 됨 + Editor reflection 안 됨
UPROPERTY()
IFoo* RawInterface;   // 컴파일 안 됨 또는 UHT 경고

// ✅ TScriptInterface wrapper — UObject + Interface 둘 다 보유
UPROPERTY(EditAnywhere)
TScriptInterface<IFoo> InterfaceRef;

// 사용
if (UObject* Obj = InterfaceRef.GetObject())
{
    IFoo::Execute_Bar(Obj);
}
```

`TScriptInterface` = UObject 포인터 + IInterface 포인터 페어. GC 안전 + Editor 디테일 패널 가시.

### #6 🟡 `_Implementation` 누락 시 link 에러

```cpp
// .h
UFUNCTION(BlueprintNativeEvent)
void DoSomething();

// .cpp — 누락
// void IMyInterface::DoSomething_Implementation() {}   // ← 이게 없으면 link 에러

// → unresolved external symbol "...IMyInterface::DoSomething_Implementation"
```

**정답**: `BlueprintNativeEvent` 멤버는 C++ 측 default `_Implementation` 의무. 본문 비워두더라도 정의 필요.

```cpp
void IMyInterface::DoSomething_Implementation() {}
```

`BlueprintImplementableEvent` 는 C++ 구현 없음 (BP 전용) — `_Implementation` 불필요.

**Alternative — inline default**: 헤더 안 본문 정의 (간단한 default 시):

```cpp
class IMyInterface
{
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable)
    bool CanDoSomething() const;
    virtual bool CanDoSomething_Implementation() const { return true; }   // ← inline default
};
```

→ `IMCSpatialQueryFilterable::CanBeSpatialQueryResult_Implementation` 가 본 패턴 사용 (2026-05-13).

### #7 🟡 UINTERFACE multiple inheritance — vtable / Execute_* ambiguity

```cpp
// ❌ 두 인터페이스가 같은 메서드 이름 가지면 Execute_* 호출 ambiguous
class IFoo { UFUNCTION(BlueprintNativeEvent) void Tick(); };
class IBar { UFUNCTION(BlueprintNativeEvent) void Tick(); };

class AMyActor : public AActor, public IFoo, public IBar { /* 어느 Tick? */ };

// IFoo::Execute_Tick(this) vs IBar::Execute_Tick(this) — 명시 호출만 안전
```

**정답**: 같은 메서드 이름 회피 또는 항상 `IFoo::Execute_Method(Obj)` / `IBar::Execute_Method(Obj)` 명시. Multi-inherit 자체는 UE 5.x 에서 동작하지만 *naming collision 방어 의무*.

또 — 다중 interface 자손이 base class member 호출 시 `IFoo::SomeMember()` 명시로 ambiguity 회피.

### #8 🟡 `MinimalAPI` 없이 다른 모듈에서 cast → link 에러

```cpp
// MCPlayModule 안 정의 — MinimalAPI 누락
UINTERFACE(Blueprintable)   // ← MinimalAPI 없음
class UMCFoo : public UInterface { GENERATED_BODY() };

// MCEditorModule 안 — cast 시 link 에러
if (Obj->Implements<UMCFoo>()) { ... }   // UMCFoo::StaticClass() 가 다른 모듈로 export 안 됨

// ✅ 정답
UINTERFACE(MinimalAPI, Blueprintable)
class MCPLAYMODULE_API UMCFoo : public UInterface { GENERATED_BODY() };
```

`MinimalAPI` 가 reflection class 만 export (전체 class 가 아님 — 비용 절감). `MODULENAME_API` prefix 도 페어로 의무.

**예외**: `MinimalAPI` 사용 시 UInterface (UMyInterface) 측에는 `MODULENAME_API` *불필요* — IMyInterface 측만 필요. `MCSpatialQueryFilterable` / `MCPoolableInterface` 모두 이 패턴.

### #9 🟡 `BlueprintImplementableEvent` 는 C++ default 불가

```cpp
// ❌
UFUNCTION(BlueprintImplementableEvent)
void DoSomething();

// .cpp 안 — 컴파일 에러 (BIE 함수는 C++ override 불허)
void IFoo::DoSomething_Implementation() {}   // ← 안 됨
```

**정답**: C++ default 구현 필요하면 `BlueprintNativeEvent` 사용. `BlueprintImplementableEvent` 는 *BP 전용 override* — C++ 호출만 가능, C++ 구현 X.

### #10 🟡 raw `Interface->Method()` 호출 — BP override 무시

```cpp
// ❌
IFoo* Foo = ...;
Foo->DoSomething();   // C++ _Implementation 만 호출. BP override 안 됨.

// ✅
IFoo::Execute_DoSomething(Foo->_getUObject());   // BP override 자동 디스패치
```

`Execute_*` 매크로가 `ProcessEvent` 통한 BP virtual dispatch 처리. raw 함수 호출은 C++ 만 보고 BP override 무시 — silent bug.

### #11 🟢 Pimpl + `TUniquePtr<IncompleteType>` C4150 — destructor 명시 *부족*, `TPimplPtr` 가 정답

본 항목은 *Interface 전용은 아님* — UCLASS GENERATED_BODY 자손 일반 함정. 본 페이지 §5 함정 매트릭스의 자매 항목으로 분류해 cross-link.

```cpp
// ❌ Stage 1 — 단순 forward Pimpl
struct FImpl;
TUniquePtr<FImpl> Impl;   // → C4150: incomplete type delete in .gen.cpp

// ❌ Stage 2 — destructor 명시 .cpp 안 default (부족)
virtual ~UMyClass() override;   // .h
UMyClass::~UMyClass() = default;   // .cpp
// → C4150 재발 — 멤버 TUniquePtr 자체 destructor instantiation 은 클래스 정의 시점

// ✅ Stage 3 — TPimplPtr (UE 표준 Pimpl smart ptr)
#include "Templates/PimplPtr.h"
struct FImpl;
TPimplPtr<FImpl> Impl;   // destroy 함수 동적 capture — incomplete 안전

// .cpp
Impl = MakePimpl<FImpl>(Args...);   // .cpp 안에서 FImpl complete → destroy capture
```

**정답** 자세히: [[concepts/Pimpl-TUniquePtr-Destructor]] §2 (3 단계 매트릭스) + §3 (TPimplPtr 동작 원리) + §4 (Smart Pointer 매트릭스).

**KMCProject 검증** (2026-05-13): `UMCActorSpawnSubsystem::FOctreeData` Pimpl 시 3 단계 모두 실측. Stage 1·2 → C4150, Stage 3 → 빌드 통과. log entries:
- `[2026-05-13] fix | UMCActorSpawnSubsystem — Pimpl + TUniquePtr<IncompleteType> C4150 fix` (Stage 1·2)
- `[2026-05-13] fix | UMCActorSpawnSubsystem — TUniquePtr<Incomplete> 함정 정밀 + TPimplPtr 정답` (Stage 3)

## 6. BP 인터페이스 vs Native 인터페이스 결정 트리 (2026-05-13 신규)

```
이 인터페이스를 누가 구현할 수 있어야 하는가?

├── C++ 만 — 디자이너가 BP 로 구현할 일 없음
│   └── UINTERFACE(MinimalAPI)   // 평범한, Blueprintable X
│       UFUNCTION() void Bar();   // BP 노출 안 함 (성능 우선)
│
├── C++ + BP 둘 다 — 디자이너가 BP class 로 구현 가능
│   ├── 디폴트 C++ 구현 필요 (override 안 한 BP 가 안전한 default 동작)
│   │   └── UFUNCTION(BlueprintNativeEvent, BlueprintCallable)
│   │       void Bar();
│   │   // .cpp 안 void IFoo::Bar_Implementation() { /* default */ }
│   │
│   └── BP 만 구현 (C++ default 필요 없음 — 항상 BP override)
│       └── UFUNCTION(BlueprintImplementableEvent, BlueprintCallable)
│           void Bar();
│   →  공통: UINTERFACE(MinimalAPI, Blueprintable, BlueprintType)
│
└── BP 가 *변수 타입* 으로 사용해야 함 (Cast / Switch / 변수 선언)
    └── 위 + BlueprintType specifier 페어 (이미 포함)
```

**KMCProject 사례 (2026-05-13)**:

| 인터페이스 | 분기 | UINTERFACE | 본문 |
| -- | -- | -- | -- |
| `IMCPoolableInterface` | C++ + BP, default 필요 | `MinimalAPI, Blueprintable, BlueprintType` | 5 BNE (OnPoolActivate / OnPoolDeactivate / IsPoolActive / GetSignificanceTag / OnSignificanceChanged) |
| `IMCSpatialQueryFilterable` | C++ + BP, default 필요 | `MinimalAPI, Blueprintable, BlueprintType` | 1 BNE (CanBeSpatialQueryResult) — inline default `return true` |

두 인터페이스 동일 분기 — *C++ + BP 둘 다, 디폴트 C++ 구현 필요*. 본 패턴이 KMCProject 의 표준.

```cpp
UINTERFACE(MinimalAPI, Blueprintable, BlueprintType)
class UMCPoolableInterface : public UInterface { GENERATED_BODY() };

class MCPLAYMODULE_API IMCPoolableInterface
{
    GENERATED_BODY()
public:
    // C++ default + BP override — AMCPooledActor 베이스가 default, BP 자손이 override
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MC|Pool")
    void OnPoolActivate(const FTransform& SpawnTransform);

    // const + BlueprintCallable → 자동 Pure (BlueprintPure 금지)
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MC|Pool")
    bool IsPoolActive() const;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MC|Pool|Significance")
    FName GetSignificanceTag() const;
};
```

## 7. UINTERFACE / UFUNCTION specifier 매트릭스 (2026-05-13 신규)

### 7.1 UINTERFACE specifier

| specifier | 효과 | 사용 |
| -- | -- | -- |
| `MinimalAPI` | reflection class 만 export | 거의 항상 (다른 모듈에서 cast 가능) |
| `Blueprintable` | BP 에서 interface *구현* 가능 | `BlueprintNativeEvent` / `BlueprintImplementableEvent` 사용 시 의무 |
| `NotBlueprintable` | C++ 만 구현 가능 | BP 노출 안 할 때 |
| `BlueprintType` | BP 변수 타입으로 사용 가능 (Cast / Switch) | 디자이너 워크플로 필요 시 |
| `meta=(CannotImplementInterfaceInBlueprint)` | **NotBlueprintable 과 동등** (헷갈리는 alias) | *피하기* — `NotBlueprintable` 명시 권장. **§5 #1 함정** — `=false` / `="false"` 모두 무력화 안 됨, 키 존재 자체가 차단. |

### 7.2 Interface 안 UFUNCTION specifier 매트릭스

| specifier | 허용 | 비고 |
| -- | -- | -- |
| `BlueprintCallable` | ✅ | C++ 와 BP 둘 다 호출 |
| `BlueprintNativeEvent` | ✅ | C++ default `_Implementation` + BP override |
| `BlueprintImplementableEvent` | ✅ | BP 전용 (C++ default 없음) |
| `BlueprintPure` | ❌ | **UHT 거부** — const + BlueprintCallable 자동 Pure |
| `BlueprintAuthorityOnly` | 🟡 | 일반 UFUNCTION 가능 (Engine source 미확인) |
| `BlueprintCosmetic` | 🟡 | 동일 |
| Category | ✅ | 권장 |

## 8. Cross-link

### Sources

[[sources/ue-coreuobject-skill]] (parent) · [[sources/ue-coreuobject-uobject]] · [[sources/ue-coreuobject-reflection]]

### Entities

[[entities/UInterface]] · [[entities/UObject]]

### Concepts

[[concepts/Reflection-System]] · ⭐ [[concepts/Pimpl-TUniquePtr-Destructor]] (§5 #11 정밀판 — 3 단계 매트릭스 + TPimplPtr 표준)

### Related fix log (⭐⭐ 함정 #1 2회 재현 확인)

- `[2026-05-13] fix | MCPoolableInterface — UHT 컴파일 에러 수정 (UINTERFACE Blueprintable + BlueprintPure 제거)` — §5 #1·#2·#3 (**1차** 재현)
- ⭐ `[2026-05-13] fix | UMCSpatialQueryFilterable — UINTERFACE meta=(CannotImplementInterfaceInBlueprint="false") UHT 역대 처리 함정 재현` — §5 #1 (**2차** 재현, 본 페이지 ⭐⭐ 신뢰도 승격 근거)
- `[2026-05-13] fix | UMCActorSpawnSubsystem — Pimpl + TUniquePtr<IncompleteType> C4150 fix` — §5 #11 Stage 1·2
- `[2026-05-13] fix | UMCActorSpawnSubsystem — TUniquePtr<Incomplete> 함정 정밀 + TPimplPtr 정답` — §5 #11 Stage 3 정답

### Related feature log

- `[2026-05-13] feature | UMCSpatialQueryLibrary — UMCActorSpawnSubsystem Octree 쿼리 소비자 (BPFunctionLibrary + 4 필터 + IMCSpatialQueryFilterable)` — `IMCSpatialQueryFilterable` 신규 (§6 결정 트리 *C++ + BP 둘 다, 디폴트 C++ 구현* 분기)

### Related synthesis

[[synthesis/actor-pool-reset-pattern]] §8 — `IMCPoolableInterface` 적용 사례 + Pimpl TPimplPtr 사용
[[synthesis/mc-actor-spawn-subsystem-implementation]] §7.1 #1·#2·#3 — Interface 함정 매트릭스 (본 페이지 §5 의 KMCProject 적용 사례 묶음)

## 9. 후속 검증 후보

🟡 / 🔴 → 🟢 승격 가능 항목 (Engine source 직접 인용 후):

- [ ] §5 #2 `BlueprintPure` 거부의 정확한 UHT 위치 (`UnrealHeaderTool.cpp` 또는 `UHT/Specifiers/*.cs`)
- [ ] §5 #4 BP 구현 객체의 `Cast<IFoo>` 동작 (`UClass::ImplementsInterface` 의 vtable 처리)
- [ ] §5 #6 `_Implementation` 자동 정의 가능 케이스 (BP-only override 시 unresolved 회피 매크로)
- [ ] §5 #7 multiple interface 자손의 ProcessEvent 디스패치 순서
- [ ] §5 #11 `TPimplPtr` Engine source 정밀 인용 — [[concepts/Pimpl-TUniquePtr-Destructor]] §10 후속 후보와 동일
- [ ] §7.2 `BlueprintAuthorityOnly` / `BlueprintCosmetic` 의 interface 허용 여부 (Engine source)
- [x] **§5 #1 2회 재현 확인 (2026-05-13)** — ⭐⭐ 승격 완료. 3회 재현 시 ⭐⭐⭐ 승격 후보.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
