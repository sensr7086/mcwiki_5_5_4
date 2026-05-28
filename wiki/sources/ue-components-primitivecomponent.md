---
type: source
title: "UE Components — UPrimitiveComponent sub-skill"
slug: ue-components-primitivecomponent
source_path: raw/ue-wiki-llm/skills/Components/references/PrimitiveComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, rendering]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Components — UPrimitiveComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/PrimitiveComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/UPrimitiveComponent]] 렌더 + 콜리전 통합 베이스 — SetVisibility / SetCollisionEnabled / Overlap 이벤트 / Custom Depth / Render Proxy.

## 2. Key claims

- SetVisibility(bVisible, bPropagateToChildren) — Render 시각 토글.
- SetCollisionEnabled(ECollisionEnabled): NoCollision / QueryOnly / PhysicsOnly / QueryAndPhysics.
- CollisionProfile (Pawn / WorldStatic 등) + Channel (ECC_*) 매트릭스.
- Overlap 이벤트: bGenerateOverlapEvents + UpdateOverlaps. OnComponentBeginOverlap / OnComponentEndOverlap delegate. Hot spot — 다수 Actor 환경에서 큰 비용 ([[raw/ue-wiki-llm/references/08_OverlapHotspots.md]]).
- Custom Depth: SetRenderCustomDepth(true) — 외곽선 / 후처리 효과 표준.
- Render Proxy (FPrimitiveSceneProxy): 렌더 스레드 표현 분리. ENQUEUE_RENDER_COMMAND 로 데이터 전달 (포인터 공유 X).
- Material: SetMaterial(Index, Material) — UMaterialInstanceDynamic (MID) 으로 동적 파라미터.

## 3. Open questions

- [ ] FPrimitiveSceneProxy 의 BatchedElement / DrawDynamic 분기
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 4
- 추가 (5.5.4 에만): 13
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| `virtual bool ShouldComponentIgnoreHitResult(FHitResult const& TestHit, EMoveC → | `void IgnoreActorWhenMoving(AActor* Actor, bool bShouldIgnore)` | L1012 | 액터 무`
- `| `bool WasRecentlyRendered(float Tolerance=0.2f) const` | 최근 렌더? (L955) | → | `bool WasRecentlyRendered(float Tolerance=0.2f) const` | 최근 렌더? (L935) |`
- `| `void SetMaterialByName(FName MaterialSlotName, UMaterialInterface*)` | L1155  → | `UMaterialInterface* GetMaterial(int32 ElementIndex) const` | L1432 | 가져오기 |`
- `| `void SetExcludedFromHLODLevel(uint8 HLODLevel, bool bSetExcluded)` | L732 | 설 → | `bool IsExcludedFromHLODLevel(EHLODLevelExclusion HLODLevel) const` | L716 | 특`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| `TArray<AActor*> CopyArrayOfMoveIgnoreActors()` | L1018 | 복사 |`
- `| `void ClearMoveIgnoreActors()` | L1029 | 초기화 |`
- `| `void IgnoreComponentWhenMoving(UPrimitiveComponent* Component, bool)` | L1047 | 컴포넌트 무시 |`
- `| `void ClearMoveIgnoreComponents()` | L1064 | 초기화 (인라인) |`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Components/references/PrimitiveComponent.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Components/references/PrimitiveComponent.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
