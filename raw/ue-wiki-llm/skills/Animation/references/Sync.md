---
name: animation-sync
description: SyncGroup (FAnimSyncScope) + Mirror (MirrorSyncScope) + Inertialization (FAnimNode_Inertialization 5.x). 다중 BlendSpace/Sequence 박자 동기 + 좌우 미러 + 0ms 블렌드 (전이) 표준. State Machine 전이 자연스러움 + Locomotion 발 위치 동기 + Crouch ↔ Stand 즉시 전환.
---

# Animation/Sync — SyncGroup + Mirror + Inertialization (5.x)

> **위치**: `Engine/Source/Runtime/Engine/Public/Animation/AnimSync*.h` + `MirrorSyncScope.h` + `AnimInertializationSyncScope.h`
> **요지**: **세 가지 동기 매커니즘** — Sync Group (박자), Mirror (좌우 반전), Inertialization (0ms 블렌드). 자연스러운 전이의 핵심.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | Sync 콜백 첫 줄 프로파일링 스코프 |

---

## 1. SyncGroup — 박자 동기 (Locomotion 표준)

### 1.1 정의

다중 BlendSpace / Sequence 가 같은 박자로 재생 → **발 위치 동기화**. 예: Walk(1초) ↔ Run(0.5초) BlendSpace 가 같은 발 박자.

### 1.2 사용 (AnimBP 안 노드 설정)

```
- BlendSpace 노드 → Sync Group Name = "Locomotion"
- Method = Graph (또는 Sequence)
- Role = Leader / Follower

Leader = 박자 기준 (가장 흔한 = BlendSpace)
Follower = Leader 박자에 맞춤
```

### 1.3 FAnimSyncScope (워커 스레드)

```cpp
// Engine/Public/Animation/AnimSyncScope.h
// AnimNode 안 사용
void FAnimNode_MyBlend::Update_AnyThread(const FAnimationUpdateContext& Ctx)
{
    UE::Anim::FAnimSyncScope SyncScope(Ctx, /*GroupName=*/ TEXT("Locomotion"), /*Role=*/ EAnimGroupRole::CanBeLeader);
    // 자식 노드 Update — 자동 박자 맞춤
    BasePose.Update(Ctx);
}
```

### 1.4 Sync 결정 매트릭스

| 시나리오 | Sync Group | Role |
|---------|-----------|------|
| BlendSpace (Walk/Run) | "Locomotion" | Leader |
| Upper Body Aim (Sequence) | "UpperBody" | Leader |
| 외부 Layer 가 Locomotion 따라가기 | "Locomotion" | Follower |
| 동기 X (독립) | (none) | - |

---

## 2. Mirror — 좌우 반전

### 2.1 정의

UMirrorDataTable 사용 — 본 이름 좌↔우 매핑 (`hand_l ↔ hand_r`). 좌측 모션 자산 1개로 좌우 모션 모두 처리.

### 2.2 패턴

```cpp
// 1. UMirrorDataTable 자산 (Editor 에서 작성)
//    - hand_l ↔ hand_r
//    - foot_l ↔ foot_r
//    - 모든 좌우 본 매핑

// 2. AnimGraph 안 Mirror 노드 사용
//    Input Pose → [Mirror Node, MirrorDataTable=MyMirror] → Output

// 3. 런타임 활성/비활성
SkelMesh->GetAnimInstance()->Set("bMirror", bShouldMirror);
```

### 2.3 MirrorSyncScope

```cpp
// 워커 스레드 — 동기 맞춤
UE::Anim::FMirrorSyncScope MirrorScope(Ctx, MirrorDataTable);
BasePose.Update(Ctx);
```

---

## 3. Inertialization — 0ms 블렌드 ⭐ 5.x 표준

### 3.1 정의

State Machine 전이 시 일반 Crossfade Blend 대신 **모든 본의 가속도/속도 캐싱 → 자연스러운 0ms 전이**. Crouch↔Stand 등 빠른 전이에 필수.

### 3.2 패턴 (AnimGraph)

```
StateMachine 안:
- 각 State 출력 → Inertialization 노드 → Result

(Inertialization 노드가 전이 감지 시 자동 처리 — Editor 에서 노드만 추가)
```

### 3.3 일반 Blend vs Inertialization

| 측면 | 일반 Blend (Crossfade) | Inertialization (5.x) |
|------|----------------------|-----------------------|
| 블렌드 시간 | 0.2 ~ 0.5초 (긴 전이) | 0초 (즉시) |
| 본 가속도 | 무시 (선형 보간) | 캐싱 (자연스러움) |
| 다중 전이 | 큐잉 X (어색) | 큐잉 OK (자연) |
| 빠른 전이 (Crouch↔Stand) | 어색 | ⭐ 자연스러움 |
| 비용 | 두 Pose 동시 평가 | 1 Pose + 보간 (저렴) |

### 3.4 FAnimNode_Inertialization

```cpp
// Engine/Public/Animation/AnimNode_Inertialization.h (자동 처리)
// AnimGraph 에 노드 추가만 하면 됨
// 전이 시점에 자동으로 RequestInertialization 호출됨
```

### 3.5 Manual 트리거 (Custom AnimNode 안)

```cpp
void FAnimNode_MyState::Update_AnyThread(const FAnimationUpdateContext& Ctx)
{
    Super::Update_AnyThread(Ctx);

    if (bStateChanged)
    {
        // 다음 Inertialization 노드에 전이 요청 (0.2초 동안 보간)
        UE::Anim::IInertializationRequester* Requester = Ctx.GetMessage<UE::Anim::IInertializationRequester>();
        if (Requester)
        {
            Requester->RequestInertialization(0.2f);
        }
    }
}
```

---

## 4. AnimInertializationSyncScope (Sync 와 Inertialization 통합)

```cpp
// Engine/Public/Animation/AnimInertializationSyncScope.h
// 두 시스템 동시 적용 — Sync Group + Inertialization
UE::Anim::FAnimInertializationSyncScope Scope(Ctx, GroupName, Role, MirrorDataTable);
BasePose.Update(Ctx);
```

---

## 5. 전이 결정 트리

```
Crossfade (일반 Blend) vs Inertialization?
├── 빠른 전이 (Crouch↔Stand, < 0.2초)            → Inertialization ⭐
├── 느린 전이 (Idle ↔ Combat Stance, > 0.5초)    → 일반 Blend
├── 다중 전이 가능 (A→B→C 빠른 연속)             → Inertialization (큐잉)
├── 단일 전이 (느린)                              → 일반 Blend
└── 5.x 신규 게임                                  → Inertialization 우선 (전부)
```

---

## 6. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 다중 BlendSpace Sync Group 미지정 (박자 어긋남) | "Locomotion" Sync Group |
| 2 | Sync Role 미지정 (어떤게 Leader 인지 불명) | Leader / Follower 명확히 |
| 3 | 좌우 모션 자산 2개 (메모리 2배) | UMirrorDataTable + Mirror 노드 (1 자산) |
| 4 | Crouch ↔ Stand 일반 Blend (느림 — 어색) | Inertialization ⭐ |
| 5 | Inertialization 노드 누락 — 전이 끊김 | StateMachine 출력 → Inertialization → Result |
| 6 | RequestInertialization 호출 시점 부정확 | bStateChanged 검증 후만 |
| 7 | Mirror DataTable 본 이름 매핑 누락 | 모든 좌/우 본 매핑 의무 |
| 8 | 5.x 신규 게임 — 일반 Blend 만 사용 | Inertialization 표준 (5.x) |

---

## 7. 체크리스트

- [ ] BlendSpace / Sequence 다중 = Sync Group 의무 ("Locomotion")
- [ ] Sync Role 명확 (Leader / Follower)
- [ ] 좌우 모션 = UMirrorDataTable + Mirror 노드 (1 자산)
- [ ] StateMachine 전이 = Inertialization 노드 (5.x 표준)
- [ ] 빠른 전이 (Crouch↔Stand) = Inertialization 의무
- [ ] 5.x 신규 게임 = Inertialization 표준

---

## 8. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인
- [`Animation/references/AnimGraph.md`](../AnimGraph/SKILL.md) — StateMachine + Transition
- [`Animation/references/AnimInstance.md`](../AnimInstance/SKILL.md) — 워커 스레드
- [`AssetClasses/references/Animation.md`](../../AssetClasses/references/Animation.md) — UBlendSpace / UAnimMontage

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. SyncGroup + Mirror + Inertialization (5.x 0ms) + 결정 트리 + 함정 8대. |
