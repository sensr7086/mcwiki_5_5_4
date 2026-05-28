---
type: source
title: "UE Components Specialist — 16 sub-skill + 6대 정책 자동"
slug: ue-agent-components
source_path: raw/ue-wiki-llm/agents/ue-components-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Mobility]]"
  - "[[concepts/Tick-Group]]"
tags: [ue, agent, specialist, components, 6-policies, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Components Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-components-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Components]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 UE 5.7.4 Components 카테고리 전문가 — **UActorComponent / USceneComponent / UPrimitiveComponent + 13 카테고리 16 sub-skill** 통합. **6대 정책** 자동 적용 (Mobility / NewObject / GC / GetOwner / Tick / CDO). 컴포넌트 작성/갱신 전담.

## 2. 자동 로드 (5 파일)

1. `skills/Components/SKILL.md` (메인 — 15 sub-skill)
2. [[sources/ue-ref-10-componentpolicies]] (**6대 정책 의무**)
3. [[sources/ue-ref-07-profilingscopeRule]] (콜백 스코프)
4. [[sources/ue-ref-09-globaliteratorpolicy]] (Iterator 회피)
5. 사용자 요청 매칭 베이스 sub-skill

## 3. 베이스 결정 트리

```
트랜스폼 무관 (스탯/인벤토리/로직) → UActorComponent
트랜스폼/부착/Mobility            → USceneComponent
콜리전/렌더/Material/Overlap     → UPrimitiveComponent 자손
  ├── Mesh                       → MeshComponents
  ├── 트리거/콜라이더               → ShapeComponents
  ├── 라이트                       → LightComponents
  ├── Constraint/Spring          → PhysicsComponents
  ├── UpdatedComponent+복제      → MovementComponents
  ├── Camera+SpringArm           → CameraComponent
  ├── Sound                      → AudioComponent
  ├── Cascade/Niagara/Vector     → ParticleComponents
  ├── Decal/TextRender/Capture   → RenderingComponents
  ├── SkyAtmo/Fog/Cloud/Wind     → AtmosphereComponents
  ├── Input/ChildActor           → SystemComponents
  └── Spline/Timeline/StereoLayer → SpecialComponents
```

## 4. 6대 정책 자동 적용 (10_ComponentPolicies)

```cpp
UCLASS(meta=(BlueprintSpawnableComponent))
class MYGAME_API UMyComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UMyComponent()
    {
        // (5) PrimaryComponentTick — false 기본 의무
        PrimaryComponentTick.bCanEverTick = false;
        // (6) CreateDefaultSubobject — Constructor 안만
        SubMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SubMesh"));
    }

    virtual void BeginPlay() override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComponent::BeginPlay);  // 🚨 의무
        Super::BeginPlay();  // ⚠️ FIRST
        // (4) GetOwner 캐싱 — TWeakObjectPtr (BeginPlay 1회)
        CachedOwner = Cast<AOwner>(GetOwner());
    }

private:
    UPROPERTY()  // (3) GC 방어
    TObjectPtr<UStaticMeshComponent> SubMesh;
    TWeakObjectPtr<AOwner> CachedOwner;  // (4) 캐싱
};
```

> (1) Mobility / (2) NewObject vs CreateDefaultSubobject 도 자동 검증.

## 5. 자주 헷갈리는 결정

| 시나리오 | 베이스 |
|---------|--------|
| 인벤토리 / 스탯 | UActorComponent |
| 무기 어태치 | USceneComponent |
| 트리거 영역 | UShapeComponent (UBoxComponent 등) |
| 렌더링 / 콜리전 | UPrimitiveComponent 자손 |
| 매 프레임 이동 | UMovementComponent (UpdatedComponent + 복제) |

## 6. 어셋 멤버 추가 시 (의무)

→ [[sources/ue-ref-11-assetloadingpolicy]] 자동 적용:
- Constructor 안 어셋 로드 금지
- BeginPlay 동기 LoadObject 금지
- Soft + Async 표준

## 7. 다수 NPC / 60fps 환경

→ [[sources/ue-ref-12-assetoptimizationpolicy]] + [[sources/ue-components-meshcomponents]] §7:
- URO 활성
- EVisibilityBasedAnimTickOption (5종)
- AnimationBudgetAllocator
- Significance 통합

## 8. Baseline Grep 의무

함정 키워드: `UActorComponent` / `Mobility` / `Tick` / `CDO` / `GetOwner` / `RegisterComponent` / `RenderState` / `bUseAttachParentBound`.

## 9. 거부 조건

- Actor / Pawn / Character — `ue-gameframework-specialist`
- Slate / UMG — `ue-slate-umg-specialist`
- Editor 도구 — `ue-editor-specialist`

## 10. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-asset]] (자산 페어) · [[sources/ue-agent-gameframework]] (Actor 호스트)
- 정책 권위: [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-deep-componentpolicies]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 11 절. 13 카테고리 결정 트리 + 6대 정책 + Cross-link 5 카테고리 |
