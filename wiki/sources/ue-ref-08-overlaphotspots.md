---
type: source
title: "UE refs — 08 OverlapHotspots (Component Overlap 비용 hub)"
slug: ue-ref-08-overlaphotspots
source_path: raw/ue-wiki-llm/references/08_OverlapHotspots.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UCharacterMovementComponent]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, reference, components, overlap, collision, hotspot, performance]
---

# UE refs — 08 OverlapHotspots 🚨

> Source: [[raw/ue-wiki-llm/references/08_OverlapHotspots.md]] · CLAUDE.md §0.1.4 cross-cutting 인덱스 · UE 5.7.4 PrimitiveComponent.h L1338 (UpdateOverlapsImpl) 검증

## 1. Summary

`UPrimitiveComponent` 자손에서 Overlap 처리가 무거워지는 케이스 + 회피 패턴. **Overlap = 매 SyncTransform 마다 콜리전 쿼리** — `bGenerateOverlapEvents=true` 컴포넌트 이동 시 현재 위치의 모든 다른 컴포넌트와 쿼리. 잘못 구성 시 매 프레임 수십~수백 회 콜리전 쿼리 + BeginOverlap/EndOverlap 델리게이트 발사. 6 컴포넌트 카테고리 (Shape / StaticMesh / SkeletalMesh / Character / ISM / Decal/Niagara) hotspot 매트릭스 + Profile/Channel 분리 표준 + UpdateOverlaps 빈도 절감.

## 2. Overlap 발생 흐름

```
[컴포넌트 이동] (SetWorldLocation / MoveComponent / 부모 트랜스폼)
   ↓ USceneComponent::OnUpdateTransform
   ↓ UPrimitiveComponent::UpdateOverlaps                ← 진입점
   ↓ UpdateOverlapsImpl (L1338)
   ↓ ComponentOverlapMulti — Physics Scene 쿼리
   ↓ 이전 OverlapInfos vs 현재 비교
   ├─ 사라진 → BeginComponentOverlap_End + OnActorEndOverlap (UFunction Dynamic Delegate — 비싼 디스패치)
   └─ 새 컴포넌트 → BeginComponentOverlap + OnActorBeginOverlap
```

## 3. 컴포넌트별 hotspot 매트릭스 🟢

### 3.1. UShapeComponent (Box / Sphere / Capsule) — 가장 자주 트리거

| hotspot | 회피 |
| -- | -- |
| `bGenerateOverlapEvents=true` + 매 프레임 이동 (회전 트리거) | 정적 트리거 = 위치 고정 / 비대칭 시 채널 분리 |
| Volume 안 항상 다수 액터 (도시 전체 Box) | 영역 분할 / 채널 분리 |
| `OnComponentBeginOverlap` 핸들러 무거움 | TimerManager 디바운스 + 핸들러 경량화 |
| 동일 Channel + Block 응답 트리거 | Trigger Profile (`OverlapAllDynamic`) |

### 3.2. UStaticMeshComponent

| hotspot | 회피 |
| -- | -- |
| `bGenerateOverlapEvents=true` + 매 프레임 이동 (lift / 플랫폼) | Simple Collision (Box/Capsule) + Convex Hull |
| **`Per Poly Collision`** (`bUseSimpleCollision=false`) + Overlap | 매 트라이앵글 검사 → Simple Collision 또는 Convex Decomposition |
| 콜리전 채널 모두 Block | 필요한 채널만 Block / 나머지 Ignore |
| ISM 안 인스턴스 모두 OverlapEvents | 인스턴스 단위 Overlap 비활성 + 별도 트리거 |

### 3.3. USkeletalMeshComponent — 가장 비싼 케이스

본별로 콜리전 가능 + 매 프레임 본 갱신.

| hotspot | 회피 |
| -- | -- |
| `Physics Asset` 모든 본 Overlap 활성 | Significant 본만 콜리전 (CCD 필요한 곳) |
| `bGenerateOverlapEvents=true` + `AlwaysTickPoseAndRefreshBones` | `OnlyTickPoseWhenRendered` + 안 보이면 Overlap 자동 정지 |
| 클로스 시뮬 + Overlap | `bDisableClothSimulation=true` 또는 거리 기반 비활성 |
| Per-poly Collision (캐릭터 메시) | Capsule 트리거 + Skel 메시 = NoCollision |

### 3.4. UCharacterMovementComponent 통합

| hotspot | 회피 |
| -- | -- |
| 캐릭터 캡슐 OverlapEvents + 트리거 다수 | 트리거 채널 분리 (Player 만) |
| 캡슐 + 메시 모두 Overlap 활성 | 캡슐만 활성, 메시 비활성 |
| RootMotion + OverlapEvents | `bDisableMovement=true` 시 Overlap 정지 |
| CrouchedHalfHeight 변경 | 빈도 제한 |

### 3.5. UInstancedStaticMeshComponent (ISM / HISM)

| hotspot | 회피 |
| -- | -- |
| 인스턴스 단위 Overlap (5.x 부분 지원) | 별도 트리거 컴포넌트 |
| HISM `bDisableCollision=false` + 다수 인스턴스 | 콜리전 분리 (Foliage 채널) |

### 3.6. UDecalComponent / UNiagaraComponent / UParticleSystemComponent

대부분 `bGenerateOverlapEvents=false` 기본. **켜지 말 것**.

## 4. CollisionEnabled / Profile / Channel 매트릭스 🟢

### 4.1. CollisionEnabled 정책

| 모드 | 콜리전 쿼리 | 물리 시뮬 | 비용 | 사용 |
| -- | -- | -- | -- | -- |
| `NoCollision` | X | X | 0 | 시각 전용 |
| `QueryOnly` | ✅ | X | 낮음 | **트리거 / 검출 영역** |
| `PhysicsOnly` | X | ✅ | 중간 | 시뮬만 (Overlap 없음) |
| `QueryAndPhysics` | ✅ | ✅ | 높음 | 일반 액터 |
| `ProbeOnly` (5.x) | ✅ proba | X | 낮음 | 가시성 검사 |

### 4.2. Channel 매트릭스 — N×M → N+M 감소

```
[Project Settings > Collision > Object Channels]
ECC_GameTraceChannel1 = "Player"
ECC_GameTraceChannel2 = "NPC"
ECC_GameTraceChannel3 = "Item"

[응답 매트릭스]
                Player  NPC    Item
Player Trigger: Overlap Ignore Ignore
NPC Trigger:    Ignore  Overlap Ignore
Item Pickup:    Overlap Ignore Ignore
```

→ 캐릭터 N명 + 트리거 M개라도 **N×M 검사 → N+M 감소**.

## 5. UpdateOverlaps 빈도 절감

자동 호출 시점: `SetWorldLocation` / `SetWorldRotation` / `SetWorldTransform` / `SetRelativeLocation` / `MoveComponent` / `OnAttachmentChanged` / `OnComponentCollisionSettingsChanged`.

**명시 차단**: `SetCollisionProfileName(NewProfile, /*bUpdateOverlaps=*/false)` + 다음 Tick 일괄 갱신. **Teleport**: `SetWorldLocation(NewPos, false, nullptr, ETeleportType::TeleportPhysics)`.

## 6. Begin/End 콜백 비용 절감

```cpp
// ✅ 가벼움 + 스코프 + 디바운스
UFUNCTION() void HandleBeginOverlap(UPrimitiveComponent* Comp, AActor* Other, ...)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_HandleBeginOverlap);   // 의무
    if (LastOverlapTime + 0.1f > GetWorld()->GetTimeSeconds()) return;
    LastOverlapTime = GetWorld()->GetTimeSeconds();
    if (AItem* Item = Cast<AItem>(Other)) { /* ... */ }
}
```

**ActorOverlap vs ComponentOverlap**: `AActor::OnActorBeginOverlap` 가 가벼움 (컴포넌트 정보 불필요 시 우선) · `UPrimitiveComponent::OnComponentBeginOverlap` 는 컴포넌트 구분 필요 시.

## 7. 8단 체크리스트

- [ ] `bGenerateOverlapEvents` 가 정말 필요한 컴포넌트만 true
- [ ] CollisionProfile 의도 일치 (Trigger / Pawn / OverlapAllDynamic)
- [ ] Channel 분리로 N×M → N+M
- [ ] Begin/End 핸들러 경량화 + 무거운 작업 TimerManager 디바운스
- [ ] 핸들러 `TRACE_CPUPROFILER_EVENT_SCOPE` 부착
- [ ] 매 프레임 이동 큰 메시 (회전 플랫폼) — Simple Collision + 채널 최소화
- [ ] SkeletalMesh — `OnlyTickPoseWhenRendered` + Physics Asset 본 콜리전 최소화
- [ ] ISM/HISM — 인스턴스 단위 Overlap 비활성 + 별도 트리거 컴포넌트

## 8. 디버그 / 측정

| 명령 | 효과 |
| -- | -- |
| `stat physics` | 물리 (Overlap 포함) 시간 |
| `stat collision` | 콜리전 쿼리 통계 |
| `Show Collision` (뷰포트) | 시각화 |
| `Trace.Start cpu,frame,physics` | Insights 트레이스 |

## 9. 시나리오 → 해결 (3 표준)

**9.1. 트리거 박스 안 캐릭터 매 프레임 검사** — 채널 분리 (Player 만) + `OnComponentBeginOverlap` 1회만 발사 → `bIsInside=true` 보관 + 명시 검사 = 입력 발생 시.

**9.2. 다수 NPC + 캐릭터 콜리전 매 프레임** — NPC ↔ NPC Ignore + NPC ↔ Player 만 검사 + Significance Manager Tick 빈도 ↓.

**9.3. 회전 플랫폼 위 액터 추적** — 별도 BoxComponent 트리거 (Mesh = NoCollision) + Box 1회 Overlap + `SetBase` (CharacterMovement).

## 10. Cross-link

- 권위 concept: [[concepts/Profiling-Scope-Rule]] (핸들러 스코프 의무)
- 자매 정책 hub: [[sources/ue-ref-06-invalidationhotspots]] (Slate/UMG 페어) · [[sources/ue-ref-07-profilingscopeRule]] §2.3 (Overlap 콜백) · [[sources/ue-ref-10-componentpolicies]] §5 (Tick 정책) · [[sources/ue-ref-12-assetoptimizationpolicy]] §6 (NPC LOD 매트릭스)
- 적용 카테고리: [[sources/ue-components-primitivecomponent]] (Overlap API 베이스) · [[sources/ue-components-shapecomponents]] · [[sources/ue-components-meshcomponents]] · [[sources/ue-components-movementcomponents]] · [[sources/ue-components-charactermovementdeep]] (deep)
- 통합 최적화: [[sources/ue-significance-skill]] (거리 LOD — Overlap 빈도 ↓) · [[sources/ue-spatialpartition-toctree2]] (TOctree2 반경 쿼리 대안)
- Networking: [[sources/ue-coreuobject-network]] (Overlap 멀티플레이 동기화)
