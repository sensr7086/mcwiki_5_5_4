---
name: overlap-hotspots
description: PrimitiveComponent 자손별 Overlap 핫스팟 (Shape/Static/Skeletal/Character/ISM/HISM) + CollisionEnabled/Channel/Profile 매트릭스 + UpdateOverlaps 호출 빈도 + Begin/End 콜백 비용 절감. 트리거/캡슐/메시 콜리전 작성 시.
---

# Overlap Hotspots — PrimitiveComponent 자손 Overlap 비용 통합 인덱스

> **모든 sub-skill 공통 의무** — Overlap 처리는 **잘못 구성하면 심각한 성능 저하** 의 주범. 본 인덱스는 `UPrimitiveComponent` 자손에서 Overlap이 무거워지는 케이스와 회피 패턴을 한곳에 모음.
> 06_InvalidationHotspots.md (UMG·Slate 인밸리데이션) 와 동일 형태 — Components 카테고리 횡단 인덱스.
> CLAUDE.md §8.1 / 03_WikiHarness.md §0.1 교차 참조 인덱스에서 본 문서를 참조.

---

## 0. 한 줄 요약

> **"Overlap = 매 SyncTransform 마다 콜리전 쿼리. 프로파일·Channel·Event 활성 셋팅이 잘못되면 매 프레임 수십~수백 회의 콜리전 쿼리가 발생"**.

근본 비용:
- `bGenerateOverlapEvents=true` 컴포넌트가 이동할 때마다 **현재 위치의 모든 다른 컴포넌트와 콜리전 쿼리**
- BeginOverlap / EndOverlap **델리게이트 발사** + Lock + UFunction 디스패치
- `UpdateOverlaps()` 가 자동 호출되는 시점: SetWorldLocation·MoveComponent·SetRelativeLocation 등 모든 트랜스폼 변경

---

## 1. Overlap 발생 흐름 (이해 베이스)

```
[컴포넌트 이동] (SetWorldLocation / MoveComponent / 부모 트랜스폼 변경)
        │
        ▼
USceneComponent::OnUpdateTransform()
        │
        ▼
UPrimitiveComponent::UpdateOverlaps()              ← 진입점
        │
        ▼
UPrimitiveComponent::UpdateOverlapsImpl()          ← 실제 작업 (L1338)
        │
        ├── ComponentOverlapMulti() — 콜리전 쿼리 (Physics Scene)
        │       │
        │       ▼
        │   현재 위치에서 OverlapTest → TArray<FOverlapResult>
        │
        ├── 새 Overlap 비교 (이전 OverlapInfos vs 현재)
        │
        ├── 사라진 컴포넌트 → BeginComponentOverlap_End
        │   │  └─ FComponentEndOverlapSignature 발사
        │   │     (UFUNCTION Dynamic Delegate — 비싼 디스패치)
        │   │
        │   └─ 다른 액터의 OnActorEndOverlap 도 발사
        │
        └── 새 컴포넌트 → BeginComponentOverlap
            │  └─ FComponentBeginOverlapSignature 발사
            │
            └─ OnActorBeginOverlap (액터별)
```

---

## 2. 컴포넌트별 핫스팟

### 2.1 UShapeComponent (Box / Sphere / Capsule)

**가장 자주 트리거** — 레벨 트리거·검출 영역.

| 핫스팟 | 비용 | 회피 |
|--------|------|------|
| `bGenerateOverlapEvents=true` 인 채로 매 프레임 이동 (회전 트리거 등) | 매 프레임 콜리전 쿼리 + 델리게이트 발사 | 정적 트리거: 위치 고정 / 비대칭이면 채널 분리 |
| Volume 안 항상 다수 액터 (예: 도시 전체 Box) | 매 SyncTransform 마다 N개 Begin/End 발사 | 영역 작게 분할 / 채널 분리 |
| `OnComponentBeginOverlap` 핸들러 무거움 | 매 진입마다 무거운 작업 | TimerManager로 디바운스 + 핸들러 가벼움 |
| 동일 Channel + Block 응답인 트리거 | 다른 액터의 Move 모두 차단 | Trigger Profile 사용 (`OverlapAllDynamic` 등) |

### 2.2 UStaticMeshComponent (메시)

| 핫스팟 | 비용 | 회피 |
|--------|------|------|
| `bGenerateOverlapEvents=true` + 매 프레임 이동 (lift·플랫폼) | 메시 복잡도 × 콜리전 쿼리 | Simple Collision (Box/Capsule) 사용 + Convex Hull |
| `Per Poly Collision` (`bUseSimpleCollision=false`) + Overlap | 매 트라이앵글 검사 — 매우 비쌈 | Simple Collision 또는 Convex Decomposition |
| 콜리전 채널 모두 Block | 모든 액터의 Move 차단 + Hit | 필요한 채널만 Block / 나머지 Ignore |
| ISM 안 인스턴스 모두 OverlapEvents | 인스턴스 수만큼 폭증 | 인스턴스 단위 Overlap 비활성 + 별도 트리거 컴포넌트 |

### 2.3 USkeletalMeshComponent (스켈레탈)

**가장 비싼 케이스** — 본별로 콜리전 가능 + 매 프레임 본 갱신.

| 핫스팟 | 비용 | 회피 |
|--------|------|------|
| `Physics Asset` 의 모든 본에 Overlap 활성 | 본 수만큼 콜리전 쿼리 + 본 갱신 후 매번 재계산 | Significant 본만 콜리전 활성 (CCD 필요한 곳만) |
| `bGenerateOverlapEvents=true` + `AlwaysTickPoseAndRefreshBones` | 매 프레임 본 변환 + 콜리전 쿼리 | `OnlyTickPoseWhenRendered` + 안 보이면 Overlap 자동 정지 |
| 클로스 시뮬 + Overlap | 시뮬 매 프레임 + 콜리전 | `bDisableClothSimulation=true` 또는 거리 기반 비활성 |
| Per-poly Collision (캐릭터 메시) | 본 변환 후 매 트라이앵글 검사 | Capsule 트리거 + Skel 메시는 NoCollision |

### 2.4 UCharacterMovementComponent 통합

`UCharacterMovementComponent` 가 매 Tick 마다 캐릭터 캡슐을 이동 → `UpdateOverlaps` 자동 호출:

| 핫스팟 | 비용 | 회피 |
|--------|------|------|
| 캐릭터 캡슐의 OverlapEvents = true + 트리거 다수 | 매 프레임 N개 트리거와 검사 | 트리거 채널 분리 (Player만) |
| 캡슐 + 메시 모두 Overlap 활성 | 같은 액터 두 컴포넌트 모두 처리 | 캡슐만 활성, 메시는 비활성 |
| RootMotion + OverlapEvents | 매 프레임 트랜스폼 변경 | `bDisableMovement=true` 시 Overlap도 정지 |
| CrouchedHalfHeight 변경 시 | 캡슐 사이즈 변경 → 새 Overlap 검사 | 빈도 제한 |

### 2.5 UInstancedStaticMeshComponent (ISM/HISM)

| 핫스팟 | 비용 | 회피 |
|--------|------|------|
| 인스턴스 단위 Overlap (지원 X 또는 매우 제한적) | (5.x — 부분 지원) | 별도 트리거 컴포넌트로 |
| HISM `bDisableCollision=false` + 다수 인스턴스 | 인스턴스 수만큼 트리 검색 | 콜리전 분리 (Foliage 채널) |

### 2.6 UDecalComponent / UNiagaraComponent / UParticleSystemComponent

대부분 `bGenerateOverlapEvents=false` 기본. 켜지 말 것.

---

## 3. SetGenerateOverlapEvents 결정 트리

```
이 컴포넌트가 다른 액터의 진입을 검출해야 하는가?
├─ 아니오 (정적 메시·라이트·이펙트) → false
└─ 예 (트리거·캐릭터·픽업) →
    ├─ 매 프레임 이동? →
    │   ├─ 예 (캐릭터 캡슐) → true (필수) + 채널 최소화
    │   └─ 아니오 (정적 트리거) → true (저렴)
    └─ 콜백 빈도가 매우 높을 것? →
        ├─ 예 → 디바운스 + 핸들러 경량화 + 거리 throttle
        └─ 아니오 → true 무방
```

---

## 4. CollisionEnabled / Channel / Profile 매트릭스

### 4.1 CollisionEnabled 정책

| 모드 | 콜리전 쿼리 | 물리 시뮬 | 비용 | 사용처 |
|------|-----------|----------|------|--------|
| `NoCollision` | X | X | 0 | 시각 전용 |
| `QueryOnly` | ✅ | X | 낮음 | 트리거·검출 영역 |
| `PhysicsOnly` | X | ✅ | 중간 | 시뮬만 (Overlap 없음) |
| `QueryAndPhysics` | ✅ | ✅ | 높음 | 일반 액터 |
| `ProbeOnly` (5.x) | ✅ (proba) | X | 낮음 | 가시성 검사 |

### 4.2 Profile 우선순위 표

| Profile | 사용처 | Begin/End 발사? |
|---------|--------|----------------|
| `NoCollision` | 시각 | X |
| `BlockAll` | 정적 벽 | (Block 시 Hit만) |
| `OverlapAll` | 광역 트리거 | ✅ 모두 |
| `OverlapAllDynamic` | 동적만 검출 (배경 영구 객체 제외) | ✅ 동적만 |
| `Trigger` | 픽업·체크포인트 | ✅ |
| `Pawn` | 캐릭터 캡슐 | ✅ |
| `Custom` | 사용자 정의 | (설정에 따라) |

### 4.3 Channel 매트릭스

신규 ECC_GameTraceChannel 2~3개로 **Player only / NPC only / Item only** 분리:

```
[Project Settings > Collision > Object Channels]
ECC_GameTraceChannel1 = "Player"
ECC_GameTraceChannel2 = "NPC"
ECC_GameTraceChannel3 = "Item"

[트리거 응답 매트릭스]
                Player  NPC    Item
Player Trigger: Overlap Ignore Ignore
NPC Trigger:    Ignore  Overlap Ignore
Item Pickup:    Overlap Ignore  Ignore
```

→ 캐릭터 N명 + 트리거 M개라도 **N×M 검사가 N+M로 감소**.

---

## 5. UpdateOverlaps 호출 빈도 줄이기

### 5.1 호출 시점 (자동)

`UpdateOverlaps()` 자동 호출 케이스:
- `SetWorldLocation` / `SetWorldRotation` / `SetWorldTransform` (bSweep 옵션과 무관)
- `SetRelativeLocation` / `SetRelativeRotation` / `SetRelativeTransform`
- `MoveComponent` / `MoveComponentImpl`
- `OnAttachmentChanged` (부착 변경)
- `OnComponentCollisionSettingsChanged` (콜리전 변경)

### 5.2 명시 차단 (`bUpdateOverlaps=false`)

```cpp
// 트랜스폼 변경하지만 Overlap 갱신 X (다음 Tick에 한꺼번에)
SetCollisionProfileName(NewProfile, /*bUpdateOverlaps=*/false);

// 일괄 트랜스폼 변경 후 마지막에 한 번만
for (int32 i = 0; i < N; i++)
{
    Comp[i]->SetWorldLocation(...);
}
// 모든 컴포넌트 한꺼번에 갱신 — 별도 호출 X (자동)
```

### 5.3 ETeleportType (물리 비활성화)

```cpp
// 물리 시뮬 끊김 + Overlap 한 번에 갱신
SetWorldLocation(NewPos, /*bSweep=*/false, nullptr, ETeleportType::TeleportPhysics);
```

---

## 6. Begin/End 콜백 비용 절감

### 6.1 핸들러 경량화

```cpp
// ❌ 무거움
UFUNCTION() void HandleBeginOverlap(...)
{
    TArray<AActor*> AllItems;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), AItem::StaticClass(), AllItems);   // O(N)
    for (AActor* Item : AllItems) { /* ... */ }
}

// ✅ 가벼움 + 스코프
UFUNCTION() void HandleBeginOverlap(UPrimitiveComponent* Comp, AActor* Other, ...)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_HandleBeginOverlap);
    if (AItem* Item = Cast<AItem>(Other))    // 단일 캐스팅
    {
        // ...
    }
}
```

### 6.2 디바운스

```cpp
UFUNCTION() void HandleBeginOverlap(...)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_HandleBeginOverlap);
    // 0.1초 안에 다시 트리거되면 무시
    if (LastOverlapTime + 0.1f > GetWorld()->GetTimeSeconds()) return;
    LastOverlapTime = GetWorld()->GetTimeSeconds();
    // ...
}
```

### 6.3 ActorOverlap vs ComponentOverlap

| 델리게이트 | 의미 | 사용 |
|-----------|------|------|
| `AActor::OnActorBeginOverlap` / `OnActorEndOverlap` | 액터 단위 — 어떤 컴포넌트든 | 액터 진입 검출 |
| `UPrimitiveComponent::OnComponentBeginOverlap` / `OnComponentEndOverlap` | 컴포넌트 단위 | 어떤 컴포넌트가 트리거됐는지 구분 |

ActorOverlap이 가벼움 — 컴포넌트 정보 불필요하면 우선.

---

## 7. 디버깅 / 측정

### 7.1 콘솔 명령

| 명령 | 효과 |
|------|------|
| `stat physics` | 물리 (Overlap 포함) 시간 |
| `stat collision` | 콜리전 쿼리 통계 |
| `p.Chaos.UpdateBoundsParallelMode 0` | (Chaos) 디버그 |
| `Show Collision` (뷰포트) | 시각화 |

### 7.2 Insights 트레이스

```
Trace.Start cpu,frame,physics
```

`UPrimitiveComponent::UpdateOverlaps` 와 `BeginComponentOverlap_*` 가 트레이스에 보임.

### 7.3 사용자 코드 스코프 의무

`OnComponentBeginOverlap` / `OnComponentEndOverlap` / `OnActorBeginOverlap` / `OnActorEndOverlap` 등 모든 핸들러:

```cpp
UFUNCTION() void HandleBeginOverlap(...)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_HandleBeginOverlap);   // ← 의무
    // ...
}
```

[`07_ProfilingScopeRule.md §2.3`](./07_ProfilingScopeRule.md) 의무.

---

## 8. 8단 Overlap 체크리스트

코드 작성 시:

- [ ] `bGenerateOverlapEvents` 가 정말 필요한 컴포넌트만 true (정적 메시·이펙트 false)
- [ ] CollisionProfile 이 의도와 일치 (Trigger / Pawn / OverlapAllDynamic 등)
- [ ] Channel 분리로 N×M → N+M 감소 (Player/NPC/Item 별)
- [ ] Begin/End 핸들러 경량화 + 무거운 작업은 TimerManager 디바운스
- [ ] 핸들러에 `TRACE_CPUPROFILER_EVENT_SCOPE` 부착
- [ ] 매 프레임 이동하는 큰 메시(예: 회전 플랫폼) — Simple Collision + 채널 최소화
- [ ] SkeletalMesh — `OnlyTickPoseWhenRendered` + Physics Asset 본 콜리전 최소화
- [ ] ISM/HISM — 인스턴스 단위 Overlap 비활성 + 별도 트리거 컴포넌트

---

## 9. 자주 발생 시나리오 → 해결

### 9.1 트리거 박스 안 캐릭터 매 프레임 검사

```
문제: TriggerBox.bGenerateOverlapEvents=true + 매 프레임 캐릭터 위치 검사
해결:
  1. TriggerBox 채널을 ECC_GameTraceChannel1 (Player만 Overlap) 로 분리
  2. OnComponentBeginOverlap 1회만 발사 → bIsInside=true 보관
  3. 명시적 검사는 캐릭터의 PlayerController에서 입력 발생 시
```

### 9.2 다수 NPC + 캐릭터 콜리전 매 프레임

```
문제: NPC N명, 각자 Capsule + GenerateOverlapEvents=true
해결:
  1. NPC 끼리 Overlap 채널 Ignore (NPC ↔ NPC 검사 제거)
  2. NPC ↔ Player만 검사
  3. Significance Manager 로 멀리 있는 NPC Tick 빈도 ↓
```

### 9.3 회전 플랫폼 위 액터 추적

```
문제: 회전 플랫폼이 매 프레임 회전 → Mesh가 OverlapEvents=true 시 매 프레임 검사
해결:
  1. 별도 BoxComponent 트리거 추가 (Mesh는 NoCollision)
  2. Box는 한 번 진입 시만 Overlap 발사
  3. 액터 attach 또는 SetBase 사용 (CharacterMovement)
```

---

## 10. 관련 sub-skill / 인덱스

- [`skills/Components/PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) — Overlap API 베이스
- [`skills/Components/ShapeComponents`](../skills/Components/references/ShapeComponents.md) — Trigger 위주
- [`skills/Components/MeshComponents`](../skills/Components/references/MeshComponents.md) — SkeletalMesh Tick 최적화
- [`skills/Components/MovementComponents`](../skills/Components/references/MovementComponents.md) — UCharacterMovementComponent 통합
- [`skills/Significance`](../skills/Significance/SKILL.md) — 거리 기반 LOD (Overlap 빈도 ↓)
- [`skills/CoreUObject/Network`](../skills/CoreUObject/references/Network.md) — Overlap 멀티플레이 동기화
- 교차: [`07_ProfilingScopeRule.md §2.3`](./07_ProfilingScopeRule.md) (Overlap 콜백 스코프 의무)

---

## 11. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. PrimitiveComponent.h L1338 (UpdateOverlapsImpl) + L373 (SetGenerateOverlapEvents) + L1953 (SetCollisionProfileName) 검증. 6개 컴포넌트 카테고리별 핫스팟 + 4개 시나리오 해결 패턴. |
