---
name: component-policies
description: 🚨 Components 6대 의무 — 모든 컴포넌트 본문 시작부 의무 블록. (1) Mobility 명시 (2) NewObject·DuplicateObject Outer 검증 (3) GC 방어 UPROPERTY+TObjectPtr/TStrongObjectPtr (4) GetOwner 캐싱 BeginPlay TWeakObjectPtr (5) PrimaryComponentTick false 기본 (6) CDO GetMutableDefault 금지·RF_ClassDefaultObject 검사.
---

# 🚨 Component Policies — 6대 공통 의무 (모든 Components 적용)

> **본 문서는 [`skills/Components/`](../skills/Components/) 의 모든 sub-skill 에 적용되는 공통 정책의 종합 인덱스입니다**.
>
> **6대 정책**:
> 1. **Mobility 정책** — Static / Stationary / Movable 명시 + `SetMobility` 런타임 금지
> 2. **NewObject + DuplicateObject 정책** — Constructor / 런타임 / 복제 분기
> 3. **GC 방어 전략** — `UPROPERTY()` 또는 `TStrongObjectPtr` 으로 GC 루트 보장
> 4. **GetOwner 캐싱** — `BeginPlay` 에서 `TWeakObjectPtr` / `TObjectPtr` 으로 1회 캐싱
> 5. **PrimaryComponentTick 정책** — 기본 OFF + `TickInterval` 우선 + 매 프레임 마지막 수단
> 6. **CDO 정책** — Class Default Object 변경 금지 + `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` 와 인스턴싱 패턴

---


## 1 ~ 6 깊이 자료 — [`references/ComponentPoliciesDeep.md`](./references/ComponentPoliciesDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 매트릭스 요약 + 깊이 자료 별도 분리.

### 6대 정책 통합 매트릭스

| # | 정책 | 핵심 룰 | reference |
|---|------|---------|-----------|
| 1 | **Mobility** (`EComponentMobility::{Static,Stationary,Movable}`) | 생성자에서 명시. 런타임 `SetMobility` 금지. Static = 변경 안 함 (Light Build OK) / Stationary = 위치 고정 + 색·강도만 (Light Build OK) / Movable = 매 프레임 변경 (Dynamic Light) | [`§1`](./references/ComponentPoliciesDeep.md#1-mobility-정책-ecomponentmobility-static-stationary-movable) |
| 2 | **NewObject + DuplicateObject** | Constructor = `CreateDefaultSubobject<T>` / 런타임 = `NewObject<T>(this, Class)` / Deep copy = `DuplicateObject<T>(Source, Outer)` + Outer 유효성 검사 의무 | [`§2`](./references/ComponentPoliciesDeep.md#2-newobject--duplicateobject-정책) |
| 3 | **GC 방어** | UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` 의무. 비-UCLASS = `TStrongObjectPtr<T>` 또는 `FGCObject::AddReferencedObjects`. **GC root 없으면 Crash** | [`§3`](./references/ComponentPoliciesDeep.md#3-gc-방어-전략) |
| 4 | **GetOwner 캐싱** | `BeginPlay` 에서 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick / 콜백 안 매번 `Cast<AOwner>(GetOwner())` 금지 (매 호출 비용) | [`§4`](./references/ComponentPoliciesDeep.md#4-getowner-캐싱-정책) |
| 5 | **PrimaryComponentTick** | 기본 `bCanEverTick = false` 의무. 필요 시 `TickInterval` (0.05~1s) 우선. 매 프레임 = 마지막 수단 + 프로파일링 스코프 | [`§5`](./references/ComponentPoliciesDeep.md#5-primarycomponenttick-정책) |
| 6 | **CDO** (Class Default Object) | `GetMutableDefault<T>()->Set*()` 으로 CDO 변경 금지. `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. `CreateDefaultSubobject` 는 Constructor 안만 | [`§6`](./references/ComponentPoliciesDeep.md#6-cdo-class-default-object-정책) |

### 통합 체크리스트 (모든 Components sub-skill 적용)

- [ ] 생성자에서 Mobility 명시 (Static / Stationary / Movable)
- [ ] Constructor = `CreateDefaultSubobject` / 런타임 = `NewObject` / Deep copy = `DuplicateObject` 분기
- [ ] UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` 또는 `TStrongObjectPtr`
- [ ] `BeginPlay` 안 `TWeakObjectPtr` 으로 GetOwner 캐싱
- [ ] `bCanEverTick = false` 기본 + 필요 시 `TickInterval` 우선
- [ ] `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` Constructor 만

> 자세한 코드 패턴 / 함정 / 결정 트리 / EObjectFlags 표 = [`references/ComponentPoliciesDeep.md`](./references/ComponentPoliciesDeep.md)
