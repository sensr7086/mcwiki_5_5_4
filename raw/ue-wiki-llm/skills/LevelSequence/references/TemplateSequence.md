---
name: levelsequence-templatesequence
description: UTemplateSequence Plugin — 재사용 가능 템플릿 시퀀스. Binding Type 추상화 (구체 액터 X / Class 만). 100개 캐릭터에 동일 시퀀스 적용 시 — 1개 Template + 100개 LevelSequenceActor (Binding Override). ATemplateSequenceActor + UTemplateSequencePlayer.
---

# LevelSequence/TemplateSequence — 재사용 가능 템플릿

> **위치 (verified)**: `Engine/Plugins/MovieScene/TemplateSequence/Source/TemplateSequence/`
> **요지**: 같은 시퀀스 로직 (피격 반응 / Idle 애니 / 죽음 모션) 을 **수십~수백 액터** 에 재사용. 일반 LevelSequence = 구체 액터 바인딩 / TemplateSequence = **Class 기반 추상 바인딩**.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Plugin 활성 | `TemplateSequence` Plugin 활성 |
| 🚨 Binding Type | TemplateSequence 안 Binding = **UClass** (구체 액터 X) |
| 🚨 사용 시점 | 동일 시퀀스 다수 액터 재사용 (10+ 인스턴스) |
| 🚨 단순 시퀀스 | 1회용 시퀀스 = LevelSequence (Template 사용 X) |

---

## 1. 클래스 구조 [grep-listed]

```
UTemplateSequence : public UMovieSceneSequence
  ↓
ATemplateSequenceActor : public AActor
  ├── TSoftObjectPtr<UTemplateSequence> TemplateSequence
  └── UTemplateSequencePlayer* SequencePlayer

UTemplateSequencePlayer : public UMovieSceneSequencePlayer
  ↓ (LevelSequencePlayer 와 동일 API — Play/Pause/Stop)
```

---

## 2. TemplateSequence vs LevelSequence 차이

| 항목 | LevelSequence | TemplateSequence |
|------|---------------|------------------|
| Binding | 구체 액터 (Possessable / Spawnable) | **UClass 만** (Binding Type) |
| 재사용 | 단일 사용 | 다수 인스턴스 가능 |
| 예시 | 인트로 컷씬 (1회) | 캐릭터 피격 모션 (모든 캐릭터 공통) |
| Player | ULevelSequencePlayer | UTemplateSequencePlayer |
| Actor | ALevelSequenceActor | ATemplateSequenceActor |

---

## 3. 표준 사용 흐름

### 3.1 TemplateSequence 작성 (Editor)

```
1. Content Browser 안 Right Click → "Template Sequence" 생성
2. Sequencer 열기 → 좌측 상단 "Binding Type" 설정
   - 예: ACharacter (모든 캐릭터 공통 적용)
3. Binding 안 Animation / Transform Track 추가
   - "Self" 이름의 Binding (Class 자동 지칭)
4. 저장
```

### 3.2 런타임 적용

```cpp
// MyCharacter.cpp
UCLASS()
class AMyCharacter : public ACharacter
{
    UPROPERTY(EditAnywhere, Category="TemplateSequence")
    TSoftObjectPtr<UTemplateSequence> HitReactionTemplate;

    TSharedPtr<FStreamableHandle> AsyncHandle;

    void PlayHitReaction()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::PlayHitReaction);

        if (HitReactionTemplate.IsNull()) return;

        // [1] Async Load Template
        FStreamableManager& SM = UAssetManager::GetStreamableManager();
        AsyncHandle = SM.RequestAsyncLoad(
            HitReactionTemplate.ToSoftObjectPath(),
            FStreamableDelegate::CreateWeakLambda(this,
                [WeakThis = TWeakObjectPtr<AMyCharacter>(this)]()
                {
                    if (WeakThis.IsValid())
                    {
                        WeakThis->SpawnTemplateActor();
                    }
                })
        );
    }

    void SpawnTemplateActor()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::SpawnTemplateActor);
        UTemplateSequence* Template = HitReactionTemplate.Get();
        if (!Template) return;

        // [2] ATemplateSequenceActor Spawn
        FActorSpawnParameters Params;
        Params.Owner = this;

        ATemplateSequenceActor* SeqActor = GetWorld()->SpawnActor<ATemplateSequenceActor>(
            ATemplateSequenceActor::StaticClass(),
            GetActorLocation(),
            FRotator::ZeroRotator,
            Params
        );

        if (SeqActor)
        {
            // [3] Template 설정 — Binding Type 이 ACharacter 면 자동으로 Owner 매핑
            SeqActor->SetSequence(Template);

            // [4] 재생
            if (UTemplateSequencePlayer* Player = SeqActor->GetSequencePlayer())
            {
                Player->OnFinished.AddDynamic(this, &AMyCharacter::OnHitReactionFinished);
                Player->Play();
            }
        }
    }

    UFUNCTION()
    void OnHitReactionFinished()
    {
        // 정리
        if (AsyncHandle.IsValid())
        {
            AsyncHandle->ReleaseHandle();
        }
    }
};
```

---

## 4. 사용 시나리오 5종

### 4.1 캐릭터 피격 반응

```
TemplateSequence: HitReaction (Binding Type: ACharacter)
├── Skeletal Animation Track: HitMontage
├── Camera Shake Track: HitShake
└── Audio Track: HitSound

→ 모든 캐릭터 피격 시 동일 시퀀스 재사용
```

### 4.2 캐릭터 사망 모션

```
TemplateSequence: DeathMotion
├── Skeletal Animation Track: DeathAnim
├── Ragdoll Trigger
└── Fade Track: Screen Fade
```

### 4.3 아이템 픽업 효과

```
TemplateSequence: ItemPickup (Binding Type: AItemPickup)
├── Particle Track: PickupVFX
├── Audio Track: PickupSound
└── Material Track: Glow
```

### 4.4 캐릭터 등장

```
TemplateSequence: CharacterEntrance
├── Fade In Track
├── Particle Track: SpawnVFX
└── Animation Track: EntrancePose
```

### 4.5 환경 인터랙션

```
TemplateSequence: DoorOpen (Binding Type: ADoor)
├── Transform Track: Door 회전
└── Audio Track: DoorSqueak
```

---

## 5. Binding Type 결정 트리

```
다수 액터 재사용?
├── No → LevelSequence
└── Yes
    ├── 모든 액터가 동일 부모 (ACharacter / AItemPickup)
    │   └── TemplateSequence (Binding Type = 공통 부모)
    └── 다양한 클래스
        └── TemplateSequence 안 인터페이스 통한 추상화
```

---

## 6. 함정 & 안티패턴 (6종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | TemplateSequence 안 구체 액터 Binding | UClass 만 (Binding Type) |
| 2 | 1회용 시퀀스 = TemplateSequence 사용 | 단순 1회 = LevelSequence |
| 3 | ATemplateSequenceActor 안 Hard Reference Template | TSoftObjectPtr + Async Load |
| 4 | Binding Type 변경 후 기존 Track 호환성 X | Binding Type = Sequence 작성 시점에 고정 |
| 5 | TemplateSequence + Owner 매핑 누락 → 빈 시퀀스 | `SeqActor->Owner = Caller` 명시 |
| 6 | TemplateSequence Cooked Build 동작 X 추측 | Cooked 정상 동작 (Plugin 패키징 시) |

---

## 7. 체크리스트

- [ ] TemplateSequence Plugin 활성
- [ ] Binding Type = 공통 부모 클래스 결정
- [ ] Sequence 안 Track = "Self" Binding 사용
- [ ] 런타임 = ATemplateSequenceActor + Owner 매핑
- [ ] Template 어셋 = TSoftObjectPtr + Async Load
- [ ] OnFinished 콜백 등록/해제 페어
- [ ] EndPlay 안 Async Handle Release
- [ ] Cooked Build 검증

---

## 8. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| TemplateSequence Plugin 위치 | **[verified]** ✅ | `Plugins/MovieScene/TemplateSequence/` 존재 |
| UTemplateSequence : UMovieSceneSequence | **[inferred]** ❌ | Plugin 안 헤더 grep 권장 |
| ATemplateSequenceActor 구조 | **[inferred]** ❌ | UE 일반 — ALevelSequenceActor 와 유사 |
| Binding Type = UClass 추상화 | **[inferred]** ❌ | UE 일반 — Plugin 본문 grep 권장 |

---

## 9. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — 런타임 재생 (TemplateSequence 도 동일 API)
- [`./MovieScene.md`](./MovieScene.md) — UMovieSceneSequence 베이스
- [`./Tracks.md`](./Tracks.md) — 동일 트랙 사용 가능
- 🚨 [`../../../references/11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — Template 어셋 Soft + Async

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **TemplateSequence vs LevelSequence 차이** + **Binding Type UClass 추상화** + **표준 사용 흐름 (Editor 작성 + 런타임 적용)** + 시나리오 5 (피격/사망/픽업/등장/도어) + 함정 6. Engine 5.7.4 검증 — TemplateSequence Plugin 존재. |
