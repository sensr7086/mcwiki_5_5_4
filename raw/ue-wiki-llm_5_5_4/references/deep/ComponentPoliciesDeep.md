---
name: component-policies-deep
description: Components 6대 정책 깊이 자료 — Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO. 각 정책별 상세 코드 패턴 + 함정 + EObjectFlags + 결정 트리.
---

# Component Policies — Deep Reference

> 본 문서는 [`10_ComponentPolicies.md`](../10_ComponentPolicies.md) 의 §1-§6 깊이 자료. 메인 문서는 6대 정책 매트릭스 요약. 본 reference 는 각 정책의 상세 코드 / 함정 / 결정 트리.

---

## 1. Mobility 정책 (`EComponentMobility::{Static, Stationary, Movable}`)

### 1.1 정의 (`EngineTypes.h:3786-3814`)

```cpp
namespace EComponentMobility
{
    enum Type : int
    {
        Static,        // 변경 없음 — Lightmap Bake / 가장 빠른 렌더
        Stationary,    // 위치 고정·속성 변경 가능 — 부분 Bake + 동적 그림자
        Movable,       // 완전 동적 — 가장 비싼 렌더
    };
}
```

### 1.2 컴포넌트 베이스별 적용

| 베이스 | Mobility 적용 | 비고 |
|--------|--------------|------|
| `UActorComponent` | **무관** — 트랜스폼 없음 | Mobility 자체가 의미 없음 |
| `USceneComponent` | **`Mobility` 필드 보유** ([`SceneComponent.h:1287`](../skills/Components/references/SceneComponent.md)) | 기본 Movable. 부모 트랜스폼 따라감 |
| `UPrimitiveComponent` | SceneComponent 자손 — 위 동일 | 콜리전·렌더 비용 결정 |
| `ULightComponent*` | **Mobility 가 비용의 핵심** ([`LightComponents §2`](../skills/Components/references/LightComponents.md)) | Static 0 / Stationary 중간 / Movable 최대 |
| `UMeshComponent*` | Static 메시 = Lightmap, Stationary = Hybrid, Movable = 동적 그림자 | LOD/HLOD 영향 |

### 1.3 핵심 규칙

#### (A) 명시 의무

```cpp
// 생성자 — Mobility 명시 (디폴트는 Movable 이지만 의도 명시 권장)
USceneComponent* SC = CreateDefaultSubobject<USceneComponent>(TEXT("SC"));
SC->SetMobility(EComponentMobility::Static);   // 또는 Stationary / Movable
```

#### (B) 런타임 `SetMobility` 금지

[`SceneComponent.h:1285-1287`](../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SceneComponent.h):
```cpp
/** Set how often this component is allowed to move during runtime.
 *  Causes a component re-register if the component is already registered */
UFUNCTION(BlueprintCallable, Category="Transformation")
ENGINE_API virtual void SetMobility(EComponentMobility::Type NewMobility);
```

> 🚨 **런타임 호출 금지** — 컴포넌트 re-register 트리거 (RenderState/PhysicsState 재생성). Lightmap 데이터·Static Lighting Cache 무효화. **에디터·생성자에서만**.

#### (C) Static 컴포넌트의 트랜스폼 변경 금지

```cpp
// 안티패턴 — Static 컴포넌트를 런타임 이동
StaticMesh->SetMobility(EComponentMobility::Static);
StaticMesh->SetWorldLocation(NewLoc);   // 🚨 경고 + Lightmap 깨짐

// 정답 — 런타임 이동 필요하면 Movable
StaticMesh->SetMobility(EComponentMobility::Movable);
StaticMesh->SetWorldLocation(NewLoc);   // OK
```

#### (D) Stationary 라이트 Overlap 한계

> Stationary Light **4개 이상 영역 겹침** 시 마지막 라이트는 자동 Movable 처리 — Bake 채널 4개 (RGBA) 한계. 영역 분리 또는 Movable 변환.

#### (E) Mobility 결정 트리

```
컴포넌트가 런타임에 이동하는가?
├── Yes → Movable
└── No
    └── 컴포넌트 속성 (라이트 색·Material 파라미터 등) 이 런타임에 변하는가?
        ├── Yes → Stationary
        └── No → Static  ← Lightmap Bake 활용 (가장 빠름)
```

### 1.4 체크리스트

- [ ] 생성자에서 Mobility 명시 (`SetMobility(...)` 또는 `Mobility = ...`)
- [ ] 런타임 `SetMobility` 호출 안 함 (에디터·생성자만)
- [ ] Static 컴포넌트 런타임 트랜스폼/속성 변경 안 함
- [ ] Stationary 라이트 영역 겹침 검사 (4개 한도)
- [ ] 의도 모호하면 Movable (보수적·유연)

---

## 2. NewObject + DuplicateObject 정책

### 2.1 4가지 생성 진입점

| 메소드 | 사용 시점 | 시그니처 | 특징 |
|--------|----------|----------|------|
| `CreateDefaultSubobject<T>(Name)` | **Constructor 안만** | UObject 멤버 | CDO 자동 등록 + Replication 자동 등록 |
| `NewObject<T>(Outer, Class, Name?, Flags?)` | 런타임 (BeginPlay 이후) | `Outer` 가 자동 GC 루트 | UPROPERTY 보유 또는 TStrongObjectPtr 의무 |
| `DuplicateObject<T>(Source, Outer, Name?)` | 런타임 deep-copy | Source 의 모든 SubObject 도 복제 | Outer 가 NULL 이면 transient package |
| `AddComponentByClass(Class, Manual?, Transform, DeferredFinish?)` | 런타임 (블루프린트 표준) | UActorComponent 전용 | Owner 자동 설정 + 등록 |

### 2.2 진입점별 코드 패턴

#### (A) `CreateDefaultSubobject` — Constructor 전용

```cpp
AMyActor::AMyActor()
{
    // ✅ Constructor 안에서만
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    RootComponent = Mesh;

    // ❌ BeginPlay 또는 일반 함수 — 죽음
    // CreateDefaultSubobject 는 ObjectInitializer 가 활성일 때만
}
```

> **Replication 자동 등록**: Constructor 안 생성 컴포넌트는 자동으로 `OwningActor.OwnedComponents` 에 등록 + Replication 시 Sub-Object 자동 추적.

#### (B) `NewObject<T>` — 런타임 표준

```cpp
void AMyActor::SpawnEffect()
{
    // ✅ Outer 명시 — 자기 자신 또는 적절한 부모
    UNiagaraComponent* Effect = NewObject<UNiagaraComponent>(this);

    // 또는 명시 클래스
    UMyComponent* Comp = NewObject<UMyComponent>(this, UMyComponent::StaticClass(), TEXT("Custom"));

    // ❌ Outer = nullptr 또는 GetTransientPackage() — GC 위험
    // UNiagaraComponent* Bad = NewObject<UNiagaraComponent>();   // transient package
    // 일반 컴포넌트는 Outer = Owning Actor 표준
}
```

> **컴포넌트 런타임 추가**: `NewObject<T>(Owner)` + `RegisterComponent()` + Attach (필요 시).
> **표준 패턴**:
> ```cpp
> auto* NewComp = NewObject<UMyComponent>(this);
> NewComp->RegisterComponent();      // 등록 + BeginPlay 호출
> NewComp->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
> ```

#### (C) `DuplicateObject<T>` — Deep Copy

```cpp
// 같은 Material 인스턴스 변형
UMaterialInstanceDynamic* OriginalMID = ...;
UMaterialInstanceDynamic* CopyMID = DuplicateObject<UMaterialInstanceDynamic>(OriginalMID, this);

// DataAsset 변형 (런타임 수정용 사본)
UMyDataAsset* RuntimeCopy = DuplicateObject<UMyDataAsset>(SourceAsset, this);
```

> **언제 NewObject vs DuplicateObject?**
> - 빈 객체 생성 → `NewObject`
> - Source 의 속성·SubObject 까지 복사 → `DuplicateObject`
> - 단순 값 복사 → `NewObject` + 멤버 명시 복사 (가장 빠름)

#### (D) `AddComponentByClass` — Blueprint 표준 (5.x)

```cpp
// 5.x 블루프린트 패턴 — Spawn Actor 후 컴포넌트 추가
UActorComponent* NewComp = MyActor->AddComponentByClass(UMyComponent::StaticClass(),
    /*bManualAttachment=*/false,
    /*RelativeTransform=*/FTransform::Identity,
    /*bDeferredFinish=*/false);
```

### 2.3 Outer 유효성 검사

```cpp
// 안티패턴 — Outer 가 곧 destroy 될 객체
void AMyActor::Foo(AActor* Other)
{
    if (Other && Other->IsActorBeingDestroyed())
    {
        // 🚨 Other 가 destroy 중 — NewObject 의 Outer 로 부적절
    }
    UMyObj* New = NewObject<UMyObj>(Other);   // GC 시 즉시 사라짐
}

// 정답
auto* New = NewObject<UMyObj>(this);   // 자기 자신을 Outer 로
```

### 2.4 Tick 안 NewObject 금지

> **매 Tick `NewObject`** = GC 압박 폭증. Object Pool / Recycling 패턴 사용.

```cpp
// 안티패턴
void Tick(float Dt)
{
    auto* Damage = NewObject<UDamageEvent>(this);   // 🚨 매 프레임
}

// 정답 — 풀
TArray<UDamageEvent*> Pool;   // UPROPERTY 로 GC 보호
UDamageEvent* AcquireFromPool() { ... }
```

### 2.5 체크리스트

- [ ] Constructor 안 = `CreateDefaultSubobject` 만
- [ ] 런타임 = `NewObject<T>(Outer)` — Outer 유효성 검사
- [ ] Deep copy 필요 = `DuplicateObject<T>(Source, Outer)`
- [ ] Component 런타임 추가 = `NewObject` + `RegisterComponent` + (옵션) `Attach`
- [ ] 결과 객체 멤버 보관 시 `UPROPERTY` 또는 `TStrongObjectPtr` (§3 참조)
- [ ] Tick 안 NewObject 안 함 — 풀링

---

## 3. GC 방어 전략

> UE5 GC 는 도달 불가능한 UObject 를 **자동 회수** — 강한 참조 없으면 다음 GC 사이클에 사라짐. C++ 객체에서 UObject 를 보유할 때 의무 룰.

### 3.1 GC 루트 4가지 방법

| 방법 | 적용 | 비고 |
|------|------|------|
| `UPROPERTY()` 마킹 | UCLASS / USTRUCT 안 멤버 | **표준** — Reflection 통해 자동 GC 루트 |
| `TStrongObjectPtr<T>` | 비-UCLASS C++ 객체 | C++ 클래스 (FGCObject 자손 아님) |
| `FGCObject::AddReferencedObjects` | 비-UCLASS 매니저 (커스텀 컬렉션) | `FGCObject` 자손 + virtual override |
| `FGCObjectScopeGuard` | 짧은 스코프 보호 | 함수 내 임시 |

### 3.2 (A) `UPROPERTY()` — 최우선

```cpp
UCLASS()
class UMyComponent : public UActorComponent
{
    GENERATED_BODY()

    // ✅ UPROPERTY 마킹 — 자동 GC 루트
    UPROPERTY()
    TObjectPtr<UMyObj> SafeRef;

    UPROPERTY()
    TArray<TObjectPtr<UMyObj>> SafeArray;

    // ❌ 마킹 없음 — GC 시 nullptr 됨
    UMyObj* DanglingPtr;          // 위험!

    // ❌ 마킹 없음 — TArray 안의 UObject* 도 GC 안 됨
    TArray<UMyObj*> DanglingArr;  // 위험!
};
```

> **5.x `TObjectPtr<T>` 표준** — Raw `UObject*` 보다 권장 (지연 로딩 + 디버깅 정보).

### 3.3 (B) `TStrongObjectPtr<T>` — 비-UCLASS 클래스

```cpp
// 비-UCLASS C++ 매니저 또는 일반 클래스에서 UObject 보유
class FMyManager
{
    TStrongObjectPtr<UMyObj> StrongRef;   // ✅ GC 루트 자동 등록

public:
    void Init()
    {
        StrongRef = TStrongObjectPtr<UMyObj>(NewObject<UMyObj>());
    }
};
```

> **언제 사용?**
> - C++ 매니저·서비스 (FGCObject 자손 아닌 일반 클래스)
> - TFunction 람다 캡처 안 UObject 보유
> - 싱글톤 / static 변수 안 UObject

### 3.4 (C) `FGCObject` — 매니저 클래스

```cpp
// 여러 UObject 컬렉션 보유하는 C++ 매니저
class FMyManager : public FGCObject
{
    TArray<UMyObj*> Objects;   // raw 포인터 (FGCObject 가 보호)

    // FGCObject override
    virtual void AddReferencedObjects(FReferenceCollector& Collector) override
    {
        Collector.AddReferencedObjects(Objects);
    }

    virtual FString GetReferencerName() const override { return TEXT("FMyManager"); }
};
```

### 3.5 (D) `TWeakObjectPtr<T>` — 약한 참조

```cpp
// 다른 곳에서 GC 결정 → 여기서는 안전 약 참조만
UPROPERTY()
TWeakObjectPtr<AActor> CachedOwner;   // GC 무관 — IsValid() 검사 후 사용

// 사용 시
if (CachedOwner.IsValid())
{
    AActor* Owner = CachedOwner.Get();
    // ...
}
```

> **Component 의 `GetOwner` 캐싱** 에 표준 사용 — §4 참조.

### 3.6 5.x — TObjectPtr / TWeakObjectPtr / TSoftObjectPtr / TStrongObjectPtr 정리

| 타입 | 용도 | GC 영향 |
|------|------|---------|
| `TObjectPtr<T>` | Raw `T*` 의 5.x 권장 대체 (UPROPERTY 안에서) | UPROPERTY 면 GC 루트, 아니면 무관 |
| `TWeakObjectPtr<T>` | 약한 참조 — IsValid() 검사 | GC 영향 없음 |
| `TStrongObjectPtr<T>` | C++ (UPROPERTY 못 쓰는) 강한 참조 | GC 루트 자동 등록 |
| `TSoftObjectPtr<T>` | 비동기 로드 — `LoadSynchronous` / `Async` | GC 영향 없음 |
| `FSoftObjectPath` | 경로만 (TSoftObjectPtr 의 베이스) | GC 영향 없음 |

### 3.7 함정 — 자주 보는 GC 누수

```cpp
// 함정 1 — 람다 캡처
auto Lambda = [Obj]() { Obj->DoSomething(); };
// 🚨 Lambda 가 Obj 를 raw 보유 — GC 시 dangling
// 정답: TWeakObjectPtr 로 캡처
auto Safe = [WeakObj = TWeakObjectPtr<UObj>(Obj)]()
{
    if (auto* O = WeakObj.Get()) O->DoSomething();
};

// 함정 2 — 멤버 raw 포인터 마킹 누락
class UMyComp : public UActorComponent
{
    UMyObj* CachedObj;   // 🚨 UPROPERTY 없음 → GC 시 사라짐
};

// 함정 3 — TArray<UObject*> 마킹 누락
TArray<UObject*> Items;   // UPROPERTY 없으면 안 보호
```

### 3.8 체크리스트

- [ ] UCLASS 안 모든 UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` (5.x)
- [ ] UCLASS 안 `TArray<UObject*>` 도 `UPROPERTY()` 마킹
- [ ] 비-UCLASS C++ 클래스 안 UObject = `TStrongObjectPtr<T>`
- [ ] 매니저 클래스 = `FGCObject` 자손 + `AddReferencedObjects` override
- [ ] 약한 참조 = `TWeakObjectPtr<T>` (IsValid 검사 후 사용)
- [ ] 람다 캡처 안 UObject = `TWeakObjectPtr` 로 캡처
- [ ] `NewObject` 결과 즉시 UPROPERTY/TStrongObjectPtr 에 보관 (스택 변수만 = GC 위험)

---

## 4. GetOwner 캐싱 정책

> `UActorComponent::GetOwner()` 는 단순 멤버 반환이지만, **Cast<AOwner>** 후 보관이 표준 — Tick / 콜백 안 매번 Cast 비용.

### 4.1 베이스 시그니처

```cpp
// UActorComponent 에서 (ActorComponent.h)
FORCEINLINE AActor* GetOwner() const { return GetTypedOuter<AActor>(); }
// 즉, GetTypedOuter — 매번 Outer 체크 + Cast
```

### 4.2 표준 캐싱 패턴

#### (A) `TWeakObjectPtr<AOwner>` — 표준

```cpp
UCLASS()
class UMyComponent : public UActorComponent
{
    GENERATED_BODY()

protected:
    UPROPERTY()
    TWeakObjectPtr<AMyChar> CachedOwner;   // 약 참조 — Owner GC 시 자동 nullptr

    virtual void BeginPlay() override
    {
        Super::BeginPlay();
        TRACE_CPUPROFILER_EVENT_SCOPE(MyComp_BeginPlay);

        // ✅ BeginPlay 1회 캐싱
        CachedOwner = Cast<AMyChar>(GetOwner());
    }

    virtual void TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TF) override
    {
        Super::TickComponent(Dt, TickType, TF);
        TRACE_CPUPROFILER_EVENT_SCOPE(MyComp_Tick);

        // ✅ 캐시 사용
        if (auto* Owner = CachedOwner.Get())
        {
            Owner->DoStuff();
        }
    }
};
```

#### (B) `TObjectPtr<AOwner>` — Owner 가 component 보다 절대 먼저 destroy 안 될 때

```cpp
UPROPERTY()
TObjectPtr<AMyChar> StrongCachedOwner;   // Owner 라이프사이클 보장 — GC 루트
```

> 일반적으로 **Component 는 Owner 와 함께 destroy** — `TObjectPtr` 도 안전. 단 외부 참조 시점 차이가 있으면 `TWeakObjectPtr` 보수적.

### 4.3 Tick 안 GetOwner / Cast 금지

```cpp
// 🚨 안티패턴 — 매 Tick Cast
void TickComponent(...)
{
    auto* Owner = Cast<AMyChar>(GetOwner());   // 매 프레임 Cast 비용
    // ...
}

// ✅ 정답 — 캐시 + 검증
void TickComponent(...)
{
    auto* Owner = CachedOwner.Get();
    if (!Owner) return;
    // ...
}
```

### 4.4 BeginPlay 가 안 호출되는 경우

| 시나리오 | BeginPlay 호출? | 캐싱 위치 |
|----------|---------------|----------|
| 일반 Spawn | ✅ | `BeginPlay` |
| Constructor (CDO) | ❌ | 절대 안 됨 — Constructor 에서 GetOwner 호출 무의미 |
| `RegisterComponent` (런타임 추가) | ✅ (BeginPlay 자동 호출) | `BeginPlay` |
| 에디터 (PIE 시작 전) | ✅ (PIE 시작 시) | `BeginPlay` |
| Editor Preview Component | ❌ | `OnRegister` 또는 `InitializeComponent` |

```cpp
// 만약 BeginPlay 가 비활성 (에디터 전용 등) 이면 InitializeComponent
virtual void InitializeComponent() override
{
    Super::InitializeComponent();
    CachedOwner = Cast<AMyChar>(GetOwner());
}
```

### 4.5 OnComponentDestroyed / EndPlay — 캐시 클리어

```cpp
virtual void EndPlay(const EEndPlayReason::Type Reason) override
{
    CachedOwner.Reset();   // 명시 클리어 (선택 — TWeakObjectPtr 자동 무효화)
    Super::EndPlay(Reason);   // EndPlay 는 Super LAST
}
```

### 4.6 체크리스트

- [ ] Owner 사용하는 컴포넌트 = `BeginPlay` 에서 캐싱
- [ ] `TWeakObjectPtr<AOwner>` 표준 (또는 라이프사이클 보장 시 `TObjectPtr`)
- [ ] Tick / 콜백 안 매번 `GetOwner()` + `Cast<>` 안 함
- [ ] 캐시 사용 전 `IsValid()` 검사 (TWeakObjectPtr)
- [ ] BeginPlay 안 호출되는 컴포넌트는 `InitializeComponent` 사용

---

## 5. PrimaryComponentTick 정책

> `UActorComponent::PrimaryComponentTick` ([`ActorComponent.h:168`](../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/ActorComponent.h)) — **컴포넌트 Tick 의 비용 결정**.

### 5.1 5단 Tick 의사결정 트리

```
질문 1: Tick 이 진짜 필요한가?
├── No → bCanEverTick = false (기본). Delegate / TimerManager 사용
└── Yes
    └── 질문 2: 매 프레임 정확도가 필요한가?
        ├── No (0.1s ~ 1s 간격 OK) → bCanEverTick = true + SetComponentTickInterval(0.1f)
        └── Yes (애니메이션·물리·이동 등) → bCanEverTick = true + 매 프레임
            └── 질문 3: 적절한 TickGroup?
                ├── 입력·이동 처리 → TG_PrePhysics (기본)
                ├── 물리 후 시각 갱신 → TG_PostPhysics
                ├── 카메라·UI → TG_PostUpdateWork
                └── 별도 의존성 → SetTickGroup(TG_*)
```

### 5.2 정책별 코드 패턴

#### (A) Tick 비활성 (기본)

```cpp
UMyComponent::UMyComponent()
{
    PrimaryComponentTick.bCanEverTick = false;   // ✅ 기본·표준 (불필요한 Tick 차단)
}
```

> **모든 컴포넌트의 기본 = OFF**. Epic 의 ActorComponent 생성자 디폴트도 false.

#### (B) Tick 필요 — Interval 우선

```cpp
UMyComponent::UMyComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;     // 시작 시 활성

    // ✅ 0.1초 (10 FPS) 간격 — 매 프레임 비용의 1/6
    PrimaryComponentTick.TickInterval = 0.1f;
    // 또는 BeginPlay 에서 SetComponentTickInterval(0.1f);
}
```

> **TickInterval 사용 케이스**:
> - HP 자연 회복 (1초 간격)
> - 적 탐지 / 인공지능 의사결정 (0.5s)
> - 환경 효과 (안개·바람) 갱신

#### (C) 매 프레임 Tick — 마지막 수단

```cpp
UMyComponent::UMyComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
    PrimaryComponentTick.TickGroup = TG_PrePhysics;    // 기본
}

virtual void TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TF) override
{
    Super::TickComponent(Dt, TickType, TF);
    TRACE_CPUPROFILER_EVENT_SCOPE(MyComp_Tick);   // 🚨 의무 ([`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md))

    // 매 프레임 로직
}
```

#### (D) Tick 동적 활성/비활성

```cpp
// 시작 시 비활성 → 이벤트 시 활성
UMyComponent::UMyComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;   // 시작 OFF
}

void UMyComponent::ActivateLogic()
{
    SetComponentTickEnabled(true);
}

void UMyComponent::OnLogicComplete()
{
    SetComponentTickEnabled(false);   // 완료 시 OFF — 비용 0
}
```

### 5.3 TickGroup 선택 가이드 (`ETickingGroup`)

| TickGroup | 시점 | 적합 |
|-----------|------|------|
| `TG_PrePhysics` | 물리 시뮬 전 (기본) | 입력·이동·로직 |
| `TG_StartPhysics` | 물리 시작 직후 | 거의 사용 안 함 |
| `TG_DuringPhysics` | 물리 중 | 거의 사용 안 함 |
| `TG_EndPhysics` | 물리 끝 | 물리 결과 활용 |
| `TG_PostPhysics` | 물리 끝 후 | 시각 갱신 — 카메라·이펙트 |
| `TG_PostUpdateWork` | 모든 Tick 후 | UI·HUD |
| `TG_LastDemotable` | 가장 마지막 | 디버그·로그 |

### 5.4 Significance + TickInterval 통합

```cpp
// 거리 기반 TickInterval 동적 변경
void OnSignificanceChanged(float Sig)
{
    if (Sig > 0.7f) SetComponentTickInterval(0.f);     // 매 프레임
    else if (Sig > 0.3f) SetComponentTickInterval(0.1f); // 10 FPS
    else if (Sig > 0.0f) SetComponentTickInterval(0.5f); // 2 FPS
    else SetComponentTickEnabled(false);                  // OFF
}
```

> **NPC 거리 기반 자동 LOD** — [`Significance/SKILL.md §7`](../skills/Significance/SKILL.md) + [`MeshComponents §7`](../skills/Components/references/MeshComponents.md).

### 5.5 Tick 의존성 (한 컴포넌트가 다른 컴포넌트 후 실행)

```cpp
// MyB 가 MyA Tick 후 실행되도록 의존성 명시
void UMyComponentB::BeginPlay()
{
    Super::BeginPlay();
    if (auto* CompA = GetOwner()->FindComponentByClass<UMyComponentA>())
    {
        AddTickPrerequisiteComponent(CompA);   // A 먼저 Tick
    }
}
```

### 5.6 함정

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `bCanEverTick = true` 만 설정 후 Tick 실행 안 함 | `Tick` 메소드 override 또는 비활성화 |
| 2 | Constructor 에서 `SetComponentTickInterval` | `PrimaryComponentTick.TickInterval = 0.1f` 직접 설정 (또는 BeginPlay) |
| 3 | TickInterval 무시하고 `Dt` 가 정확히 0.1f 이라고 가정 | `Dt` 는 실제 경과 시간 — 그 값으로 계산 |
| 4 | 모든 컴포넌트 `bCanEverTick = true` | 진짜 필요한 것만 |
| 5 | 매 프레임 Tick 후 `SetComponentTickEnabled(false)` 안 함 | 1회 작업이면 비활성 |
| 6 | 🚨 Tick 첫 줄 프로파일링 스코프 누락 | [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) 의무 |

### 5.7 체크리스트

- [ ] 기본 = `bCanEverTick = false` (Tick 진짜 필요한가?)
- [ ] Tick 활성 시 = `TickInterval` 우선 (0.05~1.0s)
- [ ] 매 프레임 Tick = 마지막 수단 — 첫 줄 프로파일링 스코프
- [ ] TickGroup 명시 (기본 `TG_PrePhysics` 외 필요 시)
- [ ] 동적 ON/OFF = `SetComponentTickEnabled` 활용
- [ ] Significance 통합 시 거리 기반 TickInterval 변경
- [ ] Tick 의존성 = `AddTickPrerequisiteComponent` / `AddTickPrerequisiteActor`

---

## 6. CDO (Class Default Object) 정책

> **CDO 는 모든 UCLASS 의 기본 인스턴스 1개** — UClass 가 로드될 때 Engine 이 자동 생성. 클래스 인스턴스가 만들어질 때 **CDO 의 속성값을 복사** + Constructor 실행. **CDO 자체를 변경하는 것은 모든 인스턴스의 기본값 변경 = 매우 위험**.

### 6.1 CDO 개념

```cpp
// UClass 마다 단 하나의 CDO
UClass* Class = UMyComponent::StaticClass();
UMyComponent* CDO = Class->GetDefaultObject<UMyComponent>();   // 단일 인스턴스 (캐스트)

// 또는 인라인 헬퍼
UMyComponent* CDO = GetDefault<UMyComponent>();   // 같은 결과
const UMyComponent* CDOConst = GetDefault<UMyComponent>();
```

[`UObjectGlobals.h:2152-2182`](../../UnrealEngine/Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h):
```cpp
template <typename T>
const T* GetDefault()  { return (const T*)T::StaticClass()->GetDefaultObject(); }

template <typename T>
T* GetMutableDefault() { return (T*)T::StaticClass()->GetDefaultObject(); }
```

### 6.2 RF_ClassDefaultObject 플래그

[`ObjectMacros.h:563`](../../UnrealEngine/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h):
```cpp
RF_ClassDefaultObject = 0x00000010,
///< This object is used as the default template for all instances of a class.
///< One object is created for each class.
```

런타임 자기 자신이 CDO 인지 검사:
```cpp
void UMyComponent::DoSomething()
{
    if (HasAnyFlags(RF_ClassDefaultObject))
    {
        // 🚨 CDO 자기 자신 — 게임 로직 실행 금지!
        return;
    }
    // 일반 인스턴스 로직
}

// 또는 IsTemplate() (Archetype 포함 더 광범위)
if (IsTemplate())
{
    return;   // CDO 또는 Archetype
}
```

### 6.3 관련 EObjectFlags

| 플래그 | 의미 |
|--------|------|
| `RF_ClassDefaultObject` (0x10) | UClass 의 기본 인스턴스 (CDO) |
| `RF_ArchetypeObject` (0x20) | Archetype (Blueprint 인스턴스 템플릿 등) |
| `RF_DefaultSubObject` (0x40000) | Constructor 안 `CreateDefaultSubobject` 로 생성된 컴포넌트 — CDO 의 SubObject |
| `RF_NeedInitialization` (0x200) | 초기화 미완료 (`~FObjectInitializer` 시 클리어) |

### 6.4 CDO 변�
