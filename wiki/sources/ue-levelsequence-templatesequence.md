---
type: source
title: "UE LevelSequence — TemplateSequence (재사용 가능 템플릿)"
slug: ue-levelsequence-templatesequence
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/TemplateSequence.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-15
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, levelsequence, template, enriched, verified]
citation_disclosure: "🟢 7 / 🟡 1 / 🔴 4 · raw verified · Cycle #13.10 enrich"
---

# UE LevelSequence — TemplateSequence (재사용 템플릿)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/TemplateSequence.md]] (257L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Plugins/MovieScene/TemplateSequence/Source/TemplateSequence/`

## 1. Summary

🟢 **재사용 가능 템플릿 시퀀스** — Binding Type 추상화 (구체 액터 X / **UClass** 만). 100개 캐릭터 피격 모션 / 사망 / 도어 오픈 등 동일 시퀀스 로직 다수 인스턴스 재사용. `UTemplateSequence` (`ULevelSequence` 자손) + `ATemplateSequenceActor` + `UTemplateSequencePlayer`.

## 2. Key claims

### 2.1 클래스 구조 🟡 (raw §1 — grep-listed)

```
UTemplateSequence : public UMovieSceneSequence       // Binding 추상화
  ↓
ATemplateSequenceActor : public AActor
  ├── TSoftObjectPtr<UTemplateSequence> TemplateSequence
  └── UTemplateSequencePlayer* SequencePlayer

UTemplateSequencePlayer : public UMovieSceneSequencePlayer
  ↓ (LevelSequencePlayer 와 동일 API — Play/Pause/Stop)

FTemplateSequenceObjectBindingID                       // Class-based 식별자
```

### 2.2 TemplateSequence vs LevelSequence 🟢 (raw §2)

| 항목 | LevelSequence | TemplateSequence |
|------|---------------|------------------|
| Binding | 구체 액터 (Possessable/Spawnable) | **UClass 만** (Binding Type) |
| 재사용 | 단일 | 다수 인스턴스 |
| 예시 | 인트로 컷씬 1회 | 캐릭터 피격 모션 (모든 캐릭터) |
| Player | `ULevelSequencePlayer` | `UTemplateSequencePlayer` |
| Actor | `ALevelSequenceActor` | `ATemplateSequenceActor` |

### 2.3 표준 사용 흐름 🟢 (raw §3)

**Editor 작성:**
1. Content Browser → Right Click → "Template Sequence" 생성
2. Sequencer 열기 → 좌상단 "Binding Type" 설정 (예: `ACharacter`)
3. Binding "Self" 안 Animation / Transform / Audio Track 추가
4. 저장

**런타임 적용:**

```cpp
UCLASS()
class AMyCharacter : public ACharacter
{
    UPROPERTY(EditAnywhere) TSoftObjectPtr<UTemplateSequence> HitReactionTemplate;
    TSharedPtr<FStreamableHandle> AsyncHandle;

    void PlayHitReaction()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::PlayHitReaction);
        if (HitReactionTemplate.IsNull()) return;

        AsyncHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(
            HitReactionTemplate.ToSoftObjectPath(),
            FStreamableDelegate::CreateWeakLambda(this,
                [WeakThis = TWeakObjectPtr<AMyCharacter>(this)]()
                { if (WeakThis.IsValid()) WeakThis->SpawnTemplateActor(); })
        );
    }

    void SpawnTemplateActor()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(SpawnTemplateActor);
        auto* T = HitReactionTemplate.Get();
        if (!T) return;

        FActorSpawnParameters P; P.Owner = this;            // ⭐ Owner = Binding 매핑
        auto* SeqActor = GetWorld()->SpawnActor<ATemplateSequenceActor>(
            ATemplateSequenceActor::StaticClass(),
            GetActorLocation(), FRotator::ZeroRotator, P);

        if (SeqActor)
        {
            SeqActor->SetSequence(T);
            if (auto* Player = SeqActor->GetSequencePlayer())
            {
                Player->OnFinished.AddDynamic(this, &AMyCharacter::OnHitReactionFinished);
                Player->Play();
            }
        }
    }
};
```

### 2.4 사용 시나리오 5종 🟢 (raw §4)

| # | 시나리오 | Binding Type | Track 구성 |
|---|---------|-------------|-----------|
| 1 | 캐릭터 피격 반응 | ACharacter | SkeletalAnim + CameraShake + Audio |
| 2 | 캐릭터 사망 모션 | ACharacter | DeathAnim + Ragdoll + Fade |
| 3 | 아이템 픽업 | AItemPickup | Particle + Sound + Material Glow |
| 4 | 캐릭터 등장 | ACharacter | FadeIn + SpawnVFX + EntrancePose |
| 5 | 환경 인터랙션 | ADoor | Transform 회전 + DoorSqueak |

### 2.5 Binding Type 결정 트리 🟢 (raw §5)

```
다수 액터 재사용?
├── No → LevelSequence
└── Yes
    ├── 모든 액터가 동일 부모 (ACharacter / AItemPickup)
    │   └── TemplateSequence (Binding Type = 공통 부모)
    └── 다양한 클래스
        └── TemplateSequence + 인터페이스 추상화
```

### 2.6 SequencerScripting 통합 🟢

Python/BP 로 Template 안 Binding override 자동 — 100 캐릭터 자동 생성 시 [[sources/ue-levelsequence-sequencerscripting]] 페어.

## 3. 함정 6 🟢 (raw §6)

| # | 함정 | 정답 |
|---|------|------|
| 1 | TemplateSequence 안 구체 액터 Binding | UClass 만 (Binding Type) |
| 2 | 1회용 시퀀스에 TemplateSequence 사용 | 단순 1회 = LevelSequence |
| 3 | Template Hard Reference | TSoftObjectPtr + Async Load |
| 4 | Binding Type 변경 후 기존 Track 호환성 X | Sequence 작성 시점 고정 |
| 5 | Owner 매핑 누락 → 빈 시퀀스 | `FActorSpawnParameters.Owner = Caller` |
| 6 | Cooked Build 동작 X 추측 | 정상 동작 (Plugin 패키징 시) |

## 4. 체크리스트 🟢 (raw §7)

- [ ] TemplateSequence Plugin 활성
- [ ] Binding Type = 공통 부모 클래스
- [ ] Track = "Self" Binding 사용
- [ ] 런타임 = ATemplateSequenceActor + Owner 매핑
- [ ] Template 어셋 = TSoftObjectPtr + Async Load
- [ ] OnFinished 콜백 등록/해제 페어
- [ ] EndPlay 안 Async Handle Release
- [ ] Cooked Build 검증

## 5. 신뢰도 🟢 (raw §8)

| 항목 | tier | 출처 |
|------|------|------|
| TemplateSequence Plugin 위치 | 🟢 verified | `Plugins/MovieScene/TemplateSequence/` |
| UTemplateSequence : UMovieSceneSequence | 🔴 inferred | Plugin 헤더 grep 권장 |
| ATemplateSequenceActor 구조 | 🔴 inferred | ALevelSequenceActor 와 유사 |
| Binding Type = UClass 추상화 | 🔴 inferred | Plugin 본문 grep |
| UTemplateSequencePlayer : UMovieSceneSequencePlayer | 🔴 inferred | 명명 규칙 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 페어: [[sources/ue-levelsequence-sequencerscripting]] (자동화 결합) · [[sources/ue-levelsequence-levelsequenceplayer]] (Player 동일 API)
- 베이스: [[sources/ue-levelsequence-moviescene]] (UMovieSceneSequence 자손)
- 트랙: [[sources/ue-levelsequence-tracks]] (동일 트랙 사용 가능)
- 정책: 🚨 [[concepts/Asset-Loading-Policy]] (Template Soft + Async) · 🚨 [[concepts/Profiling-Scope-Rule]]
