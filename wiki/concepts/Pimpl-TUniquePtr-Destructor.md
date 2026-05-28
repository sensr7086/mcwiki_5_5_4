---
type: concept
title: "Pimpl + TUniquePtr / TSharedPtr → C4150 Incomplete Type Destructor 함정"
slug: Pimpl-TUniquePtr-Destructor
created: 2026-05-13
last_updated: 2026-05-13
tags: [concept, pimpl, smart-ptr, incomplete-type, c4150, pitfall, uclass]
citation_disclosure: "🟢 8 (KMCProject 3 시도 빌드 검증 + C++ 표준 + UE 표준 API) / 🟡 2 (Engine source 정밀 인용 후속) / 🔴 0"
---

# Pimpl + TUniquePtr → Incomplete Type Destructor 함정

> **요약**: UCLASS 의 `GENERATED_BODY` + Pimpl forward + `TUniquePtr<IncompleteType>` 멤버 = **C4150 error**. `destructor 명시` 만으로는 부족, **`TPimplPtr<>` + `MakePimpl<>()` 가 표준 정답**.
>
> **KMCProject 검증** (2026-05-13): 3 시도 (forward only / destructor 명시 / TPimplPtr) — 처음 2 단계는 실패, 3 단계만 통과.

## 1. C4150 매커니즘 🟢

C++ 표준 `[expr.delete]`: **incomplete type 의 `delete` 는 undefined behavior**. 컴파일러는 클래스 정의 시점에 **모든 멤버가 instantiable** 한지 검증 — destructor 호출 가능성 포함:

```cpp
// .h
struct FImpl;                      // forward — incomplete
class UMyClass : public UWorldSubsystem
{
    GENERATED_BODY()
private:
    TUniquePtr<FImpl> Impl;        // ← 멤버 선언 시점에 TUniquePtr<FImpl>::~TUniquePtr() instantiate
};
// TUniquePtr<FImpl>::~TUniquePtr() {
//     delete Ptr;                  // ← FImpl incomplete → C4150
// }
```

**핵심 오해**: `destructor 명시 .cpp 정의` 가 충분하다는 생각. 실제로는:

- `UMyClass::~UMyClass()` 자체 instantiation 시점은 `.cpp` 안 (안전)
- 그러나 **멤버 `TUniquePtr<FImpl>` 의 destructor template instantiation 은 *클래스 정의 시점* (`.h` parsing)** — 즉 `UMyClass::~UMyClass()` 정의 위치와 무관

## 2. 3 단계 정답 매트릭스 🟢 (KMCProject 검증)

### Stage 1 — 단순 forward (실패)

```cpp
// .h
struct FImpl;
TUniquePtr<FImpl> Impl;

// .cpp
struct UMyClass::FImpl { ... };
```

→ **C4150** in `.gen.cpp` (UCLASS 의 reflection 코드가 `.h` include).

### Stage 2 — destructor 명시 (실패)

```cpp
// .h
UMyClass();
virtual ~UMyClass() override;
// ...
struct FImpl;
TUniquePtr<FImpl> Impl;

// .cpp
UMyClass::UMyClass() = default;
UMyClass::~UMyClass() = default;
```

→ **C4150 재발** — `TUniquePtr<FImpl>` 자체 destructor instantiation 이 클래스 정의 시점에 발생. 자기 destructor 만 보호 부족.

### Stage 3 — `TPimplPtr<>` (정답) ✅

```cpp
// .h
#include "Templates/PimplPtr.h"

struct FImpl;
TPimplPtr<FImpl> Impl;

// .cpp
struct UMyClass::FImpl { ... };

void UMyClass::Initialize(...)
{
    Impl = MakePimpl<FImpl>(Args...);   // ← .cpp 안에서 destroy 함수 capture
}
```

→ **빌드 통과**. `TPimplPtr` 의 destroy 함수가 `MakePimpl<T>()` 호출 시점 (`.cpp` 안 T complete) 에 dynamic capture.

## 3. `TPimplPtr` 의 동작 원리 🟡

vault 미정밀 (Engine source 직접 인용 후속):

```cpp
// Templates/PimplPtr.h (개념)
template <typename T>
class TPimplPtr
{
    T* Object = nullptr;
    void (*Destroyer)(T*) = nullptr;   // 함수 포인터 — instantiation 불필요
public:
    ~TPimplPtr() { if (Object && Destroyer) Destroyer(Object); }   // ← Destroyer 만 호출
};

template <typename T, typename... Args>
TPimplPtr<T> MakePimpl(Args&&... InArgs)
{
    return TPimplPtr<T>(new T(Forward<Args>(InArgs)...),
                       [](T* P) { delete P; });   // ← lambda 가 .cpp 안에서 T complete
}
```

핵심: `delete P;` 가 **`MakePimpl<T>()` 호출 위치** (`.cpp` 안) 에서 instantiate. `TPimplPtr<T>::~TPimplPtr()` 자체는 함수 포인터 호출만 — incomplete OK.

## 4. Smart Pointer 매트릭스 🟢

| smart ptr | Incomplete type 안전 | destructor 명시 필요 | 일반 용도 |
| -- | -- | -- | -- |
| `TUniquePtr<T>` | ❌ — `delete Ptr` 직접 | ✅ (불충분 — 본 §2.2) | Complete type 만 |
| `TSharedPtr<T>` | ❌ — 동일 | ✅ (불충분) | Complete type 만 |
| **`TPimplPtr<T>`** ⭐ | ✅ — destroy 동적 capture | ❌ | **Pimpl 전용 표준** |
| `TUniquePtr<T, CustomDeleter>` | ✅ — Deleter 정의가 .cpp 안 | ❌ | 고급 (TPimplPtr 더 간단) |
| raw `T*` + manual `delete` | ✅ — UB 회피 호출자 책임 | n/a | 단순 (위험 — Destroy 잊으면 leak) |

→ **UE 5.x Pimpl 의 표준 정답 = `TPimplPtr<>`** + `MakePimpl<>()`.

## 5. UCLASS GENERATED_BODY 와의 상호작용 🟡

UCLASS 매크로가 `.gen.cpp` 안에서 reflection 코드 자동 생성:
- `StaticClass()` registration
- `AddReferencedObjects` (GC)
- `StaticConstructObject_Internal`
- 그 외 reflection 함수들

`.gen.cpp` 가 `UMyClass.h` 만 include → `FImpl` invisible. 클래스 정의의 모든 멤버 destructor 가 *이 시점에 instantiate-able* 해야. `TUniquePtr<FImpl>` 는 destructor 안 `delete FImpl*` → incomplete → 빌드 실패.

`TPimplPtr<FImpl>` 는 destructor 안에서 `delete FImpl*` 직접 호출 안 함 (함수 포인터만) → instantiate-able OK.

## 6. KMCProject 검증 사례 🟢

`UMCActorSpawnSubsystem` 작성 시 (2026-05-13) 3 단계 모두 실측:

| Stage | 코드 | 결과 |
| -- | -- | -- |
| 1 | `TUniquePtr<FOctreeData>` + `MakeUnique` | ❌ C4150 in `.gen.cpp` |
| 2 | 위 + `virtual ~UMCActorSpawnSubsystem() override` + `.cpp` `= default` | ❌ C4150 재발 |
| 3 | `TPimplPtr<FOctreeData>` + `MakePimpl<FOctreeData>()` | ✅ 빌드 통과 |

각 시도 → log entry `[2026-05-13] fix | UMCActorSpawnSubsystem — Pimpl + TUniquePtr<IncompleteType>` 와 `... TUniquePtr<Incomplete> 함정 정밀 + TPimplPtr 정답` 에 누적 기록.

## 7. 결정 트리

```
UCLASS 자손 / 다른 모듈 노출 클래스의 멤버에 Pimpl 필요한가?
├── No → 평범한 멤버 (TUniquePtr / TSharedPtr OK, complete type)
│
└── Yes → forward declaration + .cpp 안 정의
    ├── 멤버 1개 → TPimplPtr<T> + MakePimpl<T>() ⭐ 표준
    ├── 멤버 share 필요 (참조 계수) → TSharedPtr<T> + CustomDeleter 또는 별도 패턴
    └── raw 포인터 (구식) → manual delete 의무 + UPROPERTY 사용 시 GC 안 됨
```

## 8. 안티패턴 (vault 함정 정밀 갱신)

1. ❌ "destructor 명시만 하면 TUniquePtr<Incomplete> 안전" → C4150 재발 (Stage 2 사례)
2. ❌ "TUniquePtr 가 TPimplPtr 보다 표준이라 우선" → Pimpl 컨텍스트에서는 TPimplPtr 가 표준
3. ❌ "incomplete 멤버 잘 동작 후 다른 모듈 .cpp 에서 include 시 또 다른 위치에서 instantiate" → 같은 함정, 같은 fix
4. ❌ `.gen.cpp` 가 자동 생성 코드라 무시 → `.gen.cpp` 도 정상 컴파일 단위, incomplete 검출

## 9. Cross-link

### Sources

- [[sources/ue-coreuobject-skill]] (UCLASS GENERATED_BODY 시스템)
- [[sources/ue-coreuobject-interface]] §5 (UE C++ 함정 매트릭스 — 본 concept 가 #11 보강)
- [[sources/ue-coreuobject-uobject]] (UObject lifecycle)

### Related concepts

- [[concepts/Reflection-System]] (`.gen.cpp` 자동 생성)
- [[concepts/Object-Lifecycle]] (UObject destructor 흐름)
- [[concepts/Object-Handles]] (TObjectPtr / TWeakObjectPtr 등 smart ptr 가족)

### Related fix log

`[2026-05-13] fix | UMCActorSpawnSubsystem — Pimpl + TUniquePtr<IncompleteType> C4150 fix` (Stage 1·2 시도) ·
`[2026-05-13] fix | UMCActorSpawnSubsystem — TUniquePtr<Incomplete> 함정 정밀 + TPimplPtr 정답` (Stage 3 정답)

### Related synthesis

- [[synthesis/toctree2-worldpartition-pair-pattern]] (TOctree2 통합 시 TPimplPtr 권장)
- [[synthesis/actor-pool-reset-pattern]] §8 (KMCProject Subsystem 구현 — TPimplPtr 사례)

## 10. 후속 검증 후보

🟡 → 🟢 승격 가능:

- [ ] §3 `TPimplPtr` 정확한 정의 — Engine `Templates/PimplPtr.h` 라인 인용
- [ ] §3 `MakePimpl` 변형 (allocator / Args perfect forwarding) — Engine source
- [ ] §5 `.gen.cpp` 의 정확한 자동 생성 코드 (UnrealHeaderTool / KismetCompiler 측)
- [ ] §4 `TSharedPtr<T>` + CustomDeleter 패턴의 정확한 .cpp 안 instantiation 매트릭스
