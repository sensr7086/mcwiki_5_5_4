---
type: source
title: "10_ComponentPolicies — Deep Reference (Mobility + NewObject + GC + GetOwner + Tick + CDO)"
slug: ue-ref-deep-componentpolicies
source_path: raw/ue-wiki-llm/references/deep/ComponentPoliciesDeep.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Mobility]]"
  - "[[concepts/Tick-Group]]"
  - "[[concepts/Garbage-Collection]]"
tags: [ue, reference, policy, components, enriched-card]
citation_disclosure: "🟢 14 / 🟡 2 / 🔴 0 · raw verified · Cycle 5f #1 enrich"
---

# 10_ComponentPolicies — Deep Reference

> Source: [[raw/ue-wiki-llm/references/deep/ComponentPoliciesDeep.md]]
> 부모 정책: 🚨 [[sources/ue-ref-10-componentpolicies]] · [[concepts/Component-Policies-6]]
> Cycle 5f #1 — stub 카드 → enrich 카드 (6대 정책 매트릭스 + 3-tier marker)

## 1. Summary

🟢 Components 6대 정책 — Mobility / NewObject + DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO. 각 정책별 상세 코드 + 함정 + 결정 트리.

## 2. 핵심 §/매트릭스 카탈로그 (raw §1~§6)

### 2.1 Mobility 정책 (raw §1) 🟢

- 🟢 `EComponentMobility::{Static, Stationary, Movable}` (`EngineTypes.h:3786-3814`)
- 🟢 컴포넌트 베이스별 적용 (ActorComponent 무관 / SceneComponent 보유 / Light 비용 핵심)
- 🟢 5 규칙: 명시 의무 / 런타임 SetMobility 금지 (re-register 트리거, `SceneComponent.h:1285-1287`) / Static 트랜스폼 변경 금지 / Stationary 4영역 겹침 한계 / 결정 트리
- 🟢 결정 트리: 런타임 이동 Yes → Movable / No + 속성 변화 → Stationary / 둘 다 No → Static (Lightmap)

### 2.2 NewObject + DuplicateObject (raw §2) 🟢

- 🟢 4 생성 진입점 매트릭스: `CreateDefaultSubobject` (Constructor만) / `NewObject<T>(Outer)` (런타임) / `DuplicateObject<T>(Source, Outer)` (deep copy) / `AddComponentByClass` (5.x BP 표준)
- 🟢 Constructor → BeginPlay 분리 — `CreateDefaultSubobject` Constructor 외 호출 시 죽음
- 🟢 Replication 자동 등록 — Constructor 컴포넌트 자동 추적
- 🟢 표준 패턴: `NewObject + RegisterComponent + (AttachToComponent)`
- 🟢 Outer 유효성 검사 (Other 가 곧 destroy 되면 GC 즉시)
- 🟢 Tick 안 NewObject 금지 — Object Pool 패턴

### 2.3 GC 방어 4종 전략 (raw §3) 🟢

| 전략 | 적용 | 비고 |
|------|------|------|
| `UPROPERTY()` + `TObjectPtr<T>` | UCLASS / USTRUCT 멤버 | 🟢 표준 — Reflection 자동 GC 루트 |
| `TStrongObjectPtr<T>` | 비-UCLASS C++ 매니저 | 🟢 자동 GC 루트 등록 |
| `FGCObject::AddReferencedObjects` | 매니저 컬렉션 | 🟢 virtual override + GetReferencerName |
| `TWeakObjectPtr<T>` | 약한 참조 | 🟢 GC 무관, IsValid 검사 |

- 🟢 5.x 정리: TObjectPtr / TWeakObjectPtr / TSoftObjectPtr / TStrongObjectPtr / FSoftObjectPath 매트릭스
- 🟢 함정 3종: 람다 raw 캡처 / UPROPERTY 누락 / TArray<UObject*> UPROPERTY 누락

### 2.4 GetOwner 캐싱 (raw §4) 🟢

- 🟢 `UActorComponent::GetOwner()` = `GetTypedOuter<AActor>()` — 매번 Outer Cast 비용
- 🟢 표준 패턴: `BeginPlay` 안 `CachedOwner = Cast<AMyChar>(GetOwner())` (TWeakObjectPtr)
- 🟢 BeginPlay 호출 안 되는 경우 5 매트릭스 (Constructor/CDO/PIE/Editor Preview)
- 🟢 InitializeComponent 대체 (BeginPlay 비활성 시)
- 🟢 EndPlay 안 Reset (TWeakObjectPtr 자동 무효화이지만 명시 권장) — Super LAST

### 2.5 PrimaryComponentTick (raw §5) 🟢

- 🟢 5단 의사결정 트리: Tick 필요 → 매 프레임 정확도 → TickGroup 선택
- 🟢 정책 4종: 비활성 기본 / Interval 우선 (0.1s = 10fps) / 매 프레임 마지막 / 동적 ON/OFF
- 🟢 TickGroup 7종 매트릭스 (`ETickingGroup`): PrePhysics / StartPhysics / DuringPhysics / EndPhysics / PostPhysics / PostUpdateWork / LastDemotable
- 🟢 Significance 통합 — 거리 기반 TickInterval 동적 변경
- 🟢 Tick 의존성 — `AddTickPrerequisiteComponent`
- 🚨 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 (페어: [[sources/ue-ref-07-profilingscopeRule]])

### 2.6 CDO (Class Default Object) 정책 (raw §6) 🟢/🟡

- 🟢 CDO 개념 — UClass 마다 단일 인스턴스 (`Class->GetDefaultObject<T>()` 또는 `GetDefault<T>()`)
- 🟢 `RF_ClassDefaultObject` 플래그 (`ObjectMacros.h:563`)
- 🟢 EObjectFlags 매트릭스 4종 (RF_ClassDefaultObject / RF_ArchetypeObject / RF_DefaultSubObject / RF_NeedInitialization)
- 🟢 자기 자신 CDO 검사 — `HasAnyFlags(RF_ClassDefaultObject)` 또는 `IsTemplate()`
- 🟢 게임 로직 안 CDO 변경 금지 — 모든 인스턴스 영향
- 🟡 raw §6.4 본문 일부 truncated — 후속 read 필요 (Cycle 5g 후보)

## 3. 함정 카탈로그 (raw §1~§6 종합)

| # | 함정 | tier |
|---|------|------|
| 1 | 런타임 `SetMobility` 호출 (re-register 트리거) | 🟢 |
| 2 | Static 컴포넌트 런타임 트랜스폼 변경 (Lightmap 깨짐) | 🟢 |
| 3 | Stationary Light 4 영역 겹침 → 자동 Movable 강등 | 🟢 |
| 4 | Constructor 외 `CreateDefaultSubobject` | 🟢 |
| 5 | `NewObject<T>()` Outer 없이 (transient package GC) | 🟢 |
| 6 | Tick 안 NewObject (GC 압박) | 🟢 |
| 7 | 람다 안 UObject raw 캡처 (dangling) | 🟢 |
| 8 | UPROPERTY 누락 멤버 / TArray<UObject*> 누락 | 🟢 |
| 9 | Tick 안 매번 `GetOwner() + Cast<>` | 🟢 |
| 10 | BeginPlay 비활성 (CDO/Editor) 컴포넌트에서 GetOwner 사용 | 🟢 |
| 11 | 모든 컴포넌트 `bCanEverTick = true` (과활성) | 🟢 |
| 12 | TickInterval 무시하고 `Dt` 가 정확히 0.1f 가정 | 🟢 |
| 13 | 🚨 Tick 첫 줄 프로파일링 스코프 누락 | 🟢 |
| 14 | CDO 인스턴스에서 게임 로직 실행 (모든 인스턴스 영향) | 🟢 |

## 4. Cross-link

- 부모: 🚨 [[sources/ue-ref-10-componentpolicies]] · [[concepts/Component-Policies-6]]
- 페어: [[sources/ue-components-actorcomponent]] · [[sources/ue-components-scenecomponent]] · [[entities/UActorComponent]]
- 정책 페어: 🚨 [[sources/ue-ref-07-profilingscopeRule]] (Tick 의무) · [[sources/ue-ref-deep-assetloading]] (NewObject 패턴)
- GC: [[concepts/Garbage-Collection]] · [[sources/ue-coreuobject-gc]]
- Tick: [[concepts/Tick-Group]]
- Mobility: [[concepts/Mobility]] · [[sources/ue-components-lightcomponents]] (Light Mobility 비용)

## 5. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| Mobility 3 종 + 5 규칙 | 🟢 verified | `EngineTypes.h:3786-3814` + `SceneComponent.h:1285-1287` |
| NewObject 4 진입점 | 🟢 verified | raw §2 + Engine source |
| GC 방어 4 전략 | 🟢 verified | `GCObject.h:195-201` |
| GetOwner 캐싱 | 🟢 verified | `ActorComponent.h` `GetTypedOuter` |
| Tick 7 그룹 | 🟢 verified | `ETickingGroup` |
| CDO 4 EObjectFlags | 🟢 verified | `ObjectMacros.h:563` |
| 함정 14 (모두 🟢) | 🟢 | raw §1~§6 |
| raw §6.4 후속 | 🟡 truncated | 후속 read_raw 필요 |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | 10_ComponentPolicies 분리 |
| 2026-05-15 | Cycle 5f #1 — stub 카드 → enrich 카드 (6대 정책 매트릭스 + 함정 14 + 3-tier marker + Cross-link 8건) |
