---
type: source
title: "UE 5.7.4 Significance Manager Plugin — Main SKILL"
slug: ue-significance-skill
source_path: raw/ue-wiki-llm/skills/Significance/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/USignificanceManager]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
tags: [ue, plugin, optimization, pitfalls]
---

# UE 5.7.4 Significance Manager Plugin — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Significance/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09 · **Last updated: 2026-05-13 (§5 typedef + §6 함정 신규)**

## 1. Summary

Plugin (`Engine/Plugins/Runtime/SignificanceManager/`). UE 의 **거리/카메라 기반 객체 중요도 평가 시스템**. 게임 시작 시 N 개 액터/컴포넌트를 매니저에 등록 → 매 프레임 ViewPoints 와 비교해 중요도 (0~1) 계산 → Tick / LOD / AnimUpdateRate / Cosmetic 컴포넌트 자동 토글. 수십~수백 NPC 환경의 **표준 최적화 시스템**. 단일 캐릭터 게임에는 불필요. **[[concepts/Asset-Optimization-Policy]] 5 대 영역의 통합 진입점**.

## 2. Key claims

- 핵심 클래스 4 개: [[entities/USignificanceManager]] (글로벌 매니저, USubsystem 패턴) + FManagedObjectInfo (관리되는 객체 1개, Object + Tag + SignificanceFunction + PostFunction) + EPostSignificanceType (None/Concurrent/Sequential) + FOrderedBudget (거리 순 N개에 LOD/Budget 분배 헬퍼).
- 등록 패턴: 게임 시작 (BeginPlay) 시 `Manager->RegisterObject(Obj, Tag, SignificanceFunc, PostType, PostFunc)` 호출.
- SignificanceFunction 콜백: ViewPoints 와 거리/시야 계산 → 0~1 점수 반환.
- PostFunction 콜백: 점수 변경 후 후처리 — Tick 토글 / LOD 강제 / Audio cull / Niagara cull. **4 인자 — §5 정확한 시그니처 표 참조**.
- 5 대 영역 통합 진입점: Significance 가 §1 Bone LOD (LOD 강제) + §4 Audio Culling (Sound 활성/비활성) + §5 Niagara Quality Scaling (`ENiagaraSignificanceHandling::EarliestActorBased` 통합) 의 진입점. → [[concepts/Asset-Optimization-Policy]] · [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]]
- 다수 NPC 환경 = Significance Manager 등록 + 콜백 안 5 대 영역 동시 토글 표준 패턴.

## 3. Quotations

> "수십~수백 NPC 가 있는 게임의 표준 최적화 시스템. 단일 캐릭터/주인공 게임에는 불필요."

## 4. Open questions / next sources

- [x] SignificanceFunction 콜백의 매 프레임 비용 — 등록 객체 수와 ViewPoints 수의 곱 (§6 #4 다룸)
- [ ] FOrderedBudget 의 LOD 5 단계 9 개 항목 매트릭스 — raw §7.1 참조, 정밀 추출 후속

## 5. typedef / API 정확한 시그니처 매트릭스 (2026-05-13 신규)

KMCProject `UMCActorSpawnSubsystem` 작성 시 `RegisterObject` 람다 변환 실패 (C2664) 사례 → 정확한 typedef 시그니처 vault 화. raw §4.1 표가 *함수 *타입 이름* 만* 명시했고 풀어쓴 시그니처는 §6 코드 예제에서만 노출 → 추측 위험. 본 §5 가 정확한 *4 typedef* 매트릭스.

### 5.1 콜백 typedef

| typedef | 시그니처 | tier |
| -- | -- | -- |
| `FManagedObjectSignificanceFunction` | `TFunction<float(FManagedObjectInfo*, const FTransform& Viewpoint)>` | 🟢 |
| `FManagedObjectPostSignificanceFunction` | `TFunction<void(FManagedObjectInfo*, float OldSignificance, float NewSignificance, bool bFinal)>` | 🟢 |

- **SignificanceFunc** = 2 인자 / float 반환 / 0.0 ~ 1.0 점수
- **PostFunc** = **4 인자** / void / 점수 변경 시점 호출
- 🟢 검증 — raw §3 / §6 코드 예제 + KMCProject 빌드 에러 (2026-05-13) 로 직접 확인

### 5.2 `RegisterObject` 인자 매트릭스

```cpp
virtual void RegisterObject(
    UObject*                              Object,             // 등록 대상
    FName                                 Tag,                // 그룹 식별자
    FManagedObjectSignificanceFunction    SignificanceFunc,   // 2 인자 람다
    EPostSignificanceType                 PostType = None,    // 디폴트 None
    FManagedObjectPostSignificanceFunction PostFunc = nullptr // 4 인자 람다, 디폴트 nullptr
);
```

### 5.3 EPostSignificanceType 3종

| 값 | 의미 | 사용 시점 |
| -- | -- | -- |
| `None` | Post 함수 없음 — 단순 조회 (외부에서 GetSignificance 폴링) | LOD 직접 변경 — Tick 안에서 query |
| `Concurrent` | 병렬 가능 — 가벼운 작업 | Tick 토글 / Material 파라미터 |
| `Sequential` | 순차만 — 무거운 작업 / BP execution | Subsystem 호출 / UI 갱신 / **BP NativeEvent 호출** |

→ `IMCPoolableInterface::Execute_OnSignificanceChanged` 같은 *BP virtual dispatch* 는 game thread 필수 → **Sequential** 의무.

### 5.4 람다 작성 표준 패턴

```cpp
// SignificanceFunc — 2 인자
auto SigFunc = [Near, Far](USignificanceManager::FManagedObjectInfo* Info,
                            const FTransform& Viewpoint) -> float
{
    const AActor* Actor = Cast<AActor>(Info ? Info->GetObject() : nullptr);
    if (!Actor) return 0.f;
    const float Dist = FVector::Dist(Actor->GetActorLocation(), Viewpoint.GetLocation());
    if (Dist <= Near) return 1.f;
    if (Dist >= Far)  return 0.f;
    return 1.f - (Dist - Near) / (Far - Near);
};

// PostFunc — 4 인자
auto PostFunc = [](USignificanceManager::FManagedObjectInfo* Info,
                   float OldSig, float NewSig, bool /*bFinal*/)
{
    UObject* ObjPtr = Info ? Info->GetObject() : nullptr;
    if (!IsValid(ObjPtr)) return;
    // ... NewSig 인자 직접 사용 (Info->GetSignificance() 호출 불필요)
};

Mgr->RegisterObject(Actor, Tag, SigFunc,
    USignificanceManager::EPostSignificanceType::Sequential, PostFunc);
```

## 6. 함정 / 안티패턴 (5종 — 2026-05-13 신규)

### #1 🟢 PostFunc 시그니처 2 인자로 작성 — C2664 변환 실패

```cpp
// ❌ 2 인자 — vault 본문 §2 한 줄 설명만 보고 추측
auto PostFunc = [](FManagedObjectInfo* Info, float OldSig) { ... };
Mgr->RegisterObject(..., PostFunc);   // C2664: lambda 변환 실패
```

**원인**: `FManagedObjectPostSignificanceFunction` 가 **4 인자** TFunction. vault 본문 §2 "PostFunction 콜백 — 점수 변경 후 후처리" 만 보면 추측 위험. raw §3 / §6 코드 예제 또는 본 §5.1 표 직접 인용.

**정답**: §5.4 의 4 인자 람다.

검증: KMCProject `MCActorSpawnSubsystem.cpp:562` 빌드 에러 → log entry `[2026-05-13] fix | UMCActorSpawnSubsystem — USignificanceManager PostFunc 시그니처`.

### #2 🟡 `EPostSignificanceType::Concurrent` 로 BP NativeEvent 호출

```cpp
// ❌ Concurrent → render thread 가능 → ProcessEvent (BP execution) crash 위험
Mgr->RegisterObject(..., EPostSignificanceType::Concurrent,
    [](FManagedObjectInfo* Info, float Old, float New, bool bFinal)
    {
        IMCPoolableInterface::Execute_OnSignificanceChanged(Info->GetObject(), New, Old);
        //                                                  ↑ BP 호출 — render thread 시 crash
    });
```

**정답**: BP 함수 / Subsystem 호출 / UI 갱신 등 game thread 의무 작업은 **`EPostSignificanceType::Sequential`** 사용. Tick 토글 / Material Parameter 같은 thread-safe 작업만 `Concurrent`.

### #3 🟡 `Info->GetObject()` 가 nullptr / invalid 가능

```cpp
// ❌ 가드 없이 cast
AActor* Actor = Cast<AActor>(Info->GetObject());
Actor->GetActorLocation();   // crash
```

**원인**: 객체가 등록 후 Unregister 되었거나 GC 가비지 상태에서 콜백 도착 가능 (특히 World tear-down 시점).

**정답**:
```cpp
UObject* ObjPtr = Info ? Info->GetObject() : nullptr;
if (!IsValid(ObjPtr)) return;
AActor* Actor = Cast<AActor>(ObjPtr);
if (!Actor) return;
```

### #4 🟢 SignificanceFunc 안 무거운 연산 (raw §5.x 함정)

```cpp
// ❌ 매 프레임 N 객체 × M ViewPoints 호출 — 200 NPC × 4 카메라 = 800 호출/프레임
auto SigFunc = [](FManagedObjectInfo* Info, const FTransform& VP) -> float
{
    AActor* Actor = Cast<AActor>(Info->GetObject());
    if (!Actor) return 0.f;
    // ❌ 매번 ComponentByClass 검색
    UMyMetaComp* Meta = Actor->FindComponentByClass<UMyMetaComp>();
    return CalcScore(Actor, VP, Meta);
};
```

**원인**: vault raw §5.x — "**N 객체 × M ViewPoints** 매 프레임 호출 + 단순 거리만 권장" ([[synthesis/character-many-npc-5-fold-optimization]] §5 함정 #3 도 같이).

**정답**: Score 함수는 **단순 거리만** (FORCEINLINE). 추가 입력 (bIsBoss 등) 은 등록 시 lambda capture 또는 `FManagedObjectInfo::Tag` 분기로 미리 결정.

### #5 🟡 `FManagedObjectInfo*` 의 `const` mismatch

```cpp
// ❌ 일부 UE 버전에서 const 명시 필요 — 변환 실패 케이스
auto SigFunc = [](const FManagedObjectInfo* Info, ...) -> float { ... };

// UE 5.7.4 typedef = non-const FManagedObjectInfo*
typedef TFunction<float(FManagedObjectInfo*, const FTransform&)> FManagedObjectSignificanceFunction;
```

**정답** (UE 5.7.4): **non-const** `FManagedObjectInfo*` 명시. §5.4 의 람다 그대로.

🟡 UE 4.x 또는 다른 버전에서 const 변경 가능성 — 본 버전 (5.7.4) 한정.

## 7. Cross-link

### Sources

[[sources/ue-niagara-skill]] (Niagara Quality Scaling 통합) · [[sources/ue-animation-optimization]] (URO / AnimSharing / Budget) · [[sources/ue-components-meshcomponents]] (SkeletalMesh 통합) · [[sources/ue-ref-12-assetoptimizationpolicy]] (5 대 영역 정책)

### Entities

[[entities/USignificanceManager]] · [[entities/USkeletalMeshComponent]] · [[entities/UAnimInstance]]

### Concepts

[[concepts/Asset-Optimization-Policy]] · [[concepts/URO]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[concepts/Bone-LOD]] · [[concepts/Tick-Group]]

### Related fix log

log entry `[2026-05-13] fix | UMCActorSpawnSubsystem — USignificanceManager PostFunc 시그니처 (4 인자) 수정` — 본 페이지 §6 #1 의 KMCProject 검증 사례.

### Related synthesis

[[synthesis/character-many-npc-5-fold-optimization]] §3 단계 3 (Significance 통합) · [[synthesis/actor-pool-reset-pattern]] §8.3 (KMCProject Subsystem 통합 흐름) · [[synthesis/vfx-audio-soft-pool-significance]] (Niagara Pool 결합)

## 8. 후속 검증 후보

🟡 → 🟢 승격 가능:

- [ ] §5.1 typedef 의 정확한 Engine source 라인 인용 (SignificanceManager.h ~line 100 근처 추정)
- [ ] §5.3 `Concurrent` / `Sequential` 의 정확한 thread 보장 (Engine source `Update` 안 ParallelFor / for 분기)
- [ ] §6 #2 BP NativeEvent 의 Concurrent thread 안전성 — 실제 crash 재현
- [ ] §6 #5 const 매트릭스 — UE 4.27 / 5.0 / 5.x 버전별 typedef 변화 (Audit Policy 분기별 검사)
