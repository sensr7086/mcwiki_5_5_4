---
type: source
title: "UE refs — 10 ComponentPolicies (6대 의무 정책 hub)"
slug: ue-ref-10-componentpolicies
source_path: raw/ue-wiki-llm/references/10_ComponentPolicies.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Mobility]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Tick-Group]]"
tags: [ue, reference, policy, components, governance]
---

# UE refs — 10 ComponentPolicies 🚨

> Source: [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]] · CLAUDE.md §0.1.3 의무 정책

## 1. Summary

🚨 **Components 6대 의무** — 모든 UActorComponent / USceneComponent 자손 코드의 본문 시작부에 의무 적용되는 6개 정책 hub. CLAUDE.md §0.1.3 가 본 페이지를 권위 source 로 지정. 권위 concept = [[concepts/Component-Policies-6]]. 깊이 자료 = [[sources/ue-ref-deep-componentpolicies]].

## 2. 6대 정책 통합 매트릭스 🟢

| # | 정책 | 핵심 룰 | 함정 |
| -- | -- | -- | -- |
| 1 | **Mobility** `EComponentMobility::{Static,Stationary,Movable}` | 생성자에서 명시. **런타임 `SetMobility` 금지** (재초기화 비용). Static = 변경 X (Light Build OK) / Stationary = 위치 고정 + 색·강도만 / Movable = 매 프레임 변경 (Dynamic Light) | 런타임에 변경 시 RenderState 재생성 + Light Build 무효 |
| 2 | **NewObject / DuplicateObject** | Constructor = `CreateDefaultSubobject<T>` / 런타임 = `NewObject<T>(this, Class)` / Deep copy = `DuplicateObject<T>(Source, Outer)` + **Outer 유효성 검사 의무** | Outer = nullptr → 즉시 GC 후보 |
| 3 | **GC 방어** | UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` 의무. 비-UCLASS 컨테이너 = `TStrongObjectPtr<T>` 또는 `FGCObject::AddReferencedObjects` | GC root 없으면 Crash (Cooked 빌드 ↑) |
| 4 | **GetOwner 캐싱** | `BeginPlay` 안 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick / 콜백 매번 `Cast<AOwner>(GetOwner())` 금지 (매 호출 RTTI 비용) | Tick 안 매번 Cast → 핫루프 오버헤드 |
| 5 | **PrimaryComponentTick** | **기본 `bCanEverTick = false` 의무**. 필요 시 `TickInterval` (0.05~1s) 우선. 매 프레임 = 마지막 수단 + `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 | 무조건 매 프레임 Tick → Significance 통합 불가 |
| 6 | **CDO** (Class Default Object) | `GetMutableDefault<T>()->Set*()` 금지 (전역 영향). `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. **`CreateDefaultSubobject` 는 Constructor 안만** | CDO 변경 시 모든 인스턴스 영향 + 쿠킹 시 직렬화 오염 |

## 3. 표준 패턴 (6대 통합 코드)

```cpp
UCLASS(ClassGroup=(MC), meta=(BlueprintSpawnableComponent))
class UMCMyComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UMCMyComponent()
    {
        // §5 — 기본 OFF
        PrimaryComponentTick.bCanEverTick = false;
        PrimaryComponentTick.TickInterval = 0.0f;

        // §2 — Constructor = CreateDefaultSubobject
        ChildScene = CreateDefaultSubobject<USceneComponent>(TEXT("ChildScene"));

        // §1 — Mobility (SceneComponent 자손이면)
        // ChildScene->SetMobility(EComponentMobility::Movable);
    }

    virtual void BeginPlay() override
    {
        Super::BeginPlay();
        TRACE_CPUPROFILER_EVENT_SCOPE(MCMyComponent_BeginPlay);

        // §6 — CDO 검사
        if (HasAnyFlags(RF_ClassDefaultObject)) return;

        // §4 — GetOwner 캐싱
        CachedOwner = Cast<AMCCharacter>(GetOwner());
    }

private:
    // §3 — UPROPERTY + TObjectPtr 의무
    UPROPERTY() TObjectPtr<USceneComponent> ChildScene;

    // §4 — TWeakObjectPtr 캐시
    TWeakObjectPtr<AMCCharacter> CachedOwner;
};
```

## 4. 통합 체크리스트

- [ ] 생성자에서 Mobility 명시 (SceneComponent 자손 시)
- [ ] Constructor = `CreateDefaultSubobject` / 런타임 = `NewObject` / Deep copy = `DuplicateObject` 분기
- [ ] UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` 또는 `TStrongObjectPtr`
- [ ] `BeginPlay` 안 `TWeakObjectPtr` 으로 GetOwner 캐싱
- [ ] `bCanEverTick = false` 기본 + 필요 시 `TickInterval` 우선
- [ ] `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` Constructor 만

## 5. Cross-link

- 권위 concept: [[concepts/Component-Policies-6]] · [[concepts/Mobility]] · [[concepts/Garbage-Collection]] · [[concepts/Tick-Group]]
- 깊이 자료: [[sources/ue-ref-deep-componentpolicies]] (정책별 EObjectFlags 표 + 함정 매트릭스)
- 횡단 정책: [[sources/ue-ref-07-profilingscopeRule]] (§5 Tick 스코프) · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- 카테고리 main: [[sources/ue-components-skill]] (15 sub-skill 모두 6대 적용)
- 자매 정책 hub: [[sources/ue-ref-04-overrideindex]] (Super 호출 규약) · [[sources/ue-ref-05-editoronlyindex]] (4단 분리)
