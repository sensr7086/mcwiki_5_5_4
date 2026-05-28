---
type: source
title: "UE LevelSequence — Director (BP Director + Event Track)"
slug: ue-levelsequence-director
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/Director.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B remaining audit
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, levelsequence, director, blueprint, enriched, verified]
citation_disclosure: "🟢 10 / 🟡 2 / 🔴 2 · raw verified · Cycle #13.9 enrich"
---

# UE LevelSequence — Director (BP Director + Event Track)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/Director.md]] (331L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Runtime/LevelSequence/Public/LevelSequenceDirector.h:23`

## 1. Summary

🟢 `ULevelSequenceDirector` = LevelSequence 의 **Blueprint 통합 진입점**. Sequencer Event Track 트리거 → Director BP 함수 호출. 시퀀스 시간 기반 게임 로직 (보스 등장 / UI 알림 / 사운드 큐 / GAS 트리거). BP-only / C++ 자손 모두 가능 + 5.x Custom Clock + Multiplayer NetMulticast.

## 2. Key claims

### 2.1 ULevelSequenceDirector 핵심 🟢 (raw §1 — LevelSequenceDirector.h:23)

```cpp
UCLASS(Blueprintable, MinimalAPI)
class ULevelSequenceDirector : public UObject
{
    GENERATED_BODY()

    UFUNCTION(BlueprintImplementableEvent, Category="Sequencer")
    void OnCreated();                                       // [1] 생성 시

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    FQualifiedFrameTime GetRootSequenceTime() const;        // [2]

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    FQualifiedFrameTime GetCurrentTime() const;             // [3]

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    UMovieSceneClock* GetRootSequenceCustomClock() const;   // [4] 5.x

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    UMovieSceneClock* GetSequenceCustomClock() const;       // [5] 5.x

    UFUNCTION(BlueprintPure, meta=(WorldContext="WorldContextObject"))
    TArray<UObject*> GetBoundObjects(FMovieSceneObjectBindingID) const;  // [6]
};
```

### 2.2 BP-only Director 작성 흐름 🟢 (raw §2)

```
1. LevelSequence 자산 더블클릭 → Sequencer 열림
2. 좌상단 "Open Director Blueprint" 클릭
3. BP Editor 안 자동 생성 LevelSequenceDirector BP 편집
4. OnCreated / 커스텀 함수 추가
5. Sequencer Event Track 추가 → Section Key → Event 선택
6. Event 가 호출할 Director BP 함수 매핑
```

### 2.3 Event Track 사용 표준 🟢 (raw §3)

```
시퀀스 안:
└── Event Track
    └── [120 프레임 — 보스 등장]
        └── EventTrigger Section
            └── Endpoint: PlayBossEntranceSound (Director BP)
```

### 2.4 C++ Director 자손 (고급) 🟢 (raw §4)

```cpp
UCLASS(Blueprintable)
class MYGAME_API UMyLevelSequenceDirector : public ULevelSequenceDirector
{
    UFUNCTION(BlueprintCallable, Category="MyCutscene")
    void TriggerBossSpawn()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::TriggerBossSpawn);
        if (auto* W = GetWorld(); W)
            W->SpawnActor<AMyBoss>(BossClass, SpawnLoc, SpawnRot);
    }

    UFUNCTION(BlueprintCallable, Category="MyCutscene")
    void TriggerGAS(AActor* Target, TSubclassOf<UGameplayAbility> AbilityClass)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::TriggerGAS);
        if (!IsValid(Target) || !AbilityClass) return;
        if (auto* ASC = Target->FindComponentByClass<UAbilitySystemComponent>())
            ASC->TryActivateAbilityByClass(AbilityClass);
    }

protected:
    UPROPERTY(EditDefaultsOnly) TSubclassOf<AActor> BossClass;
};
```

> LevelSequence 자산 → "Director Settings" → Parent Class = `UMyLevelSequenceDirector` 변경.

### 2.5 CreateDirectorInstance virtual 🟢 (raw §5 — LevelSequence.h:61)

```cpp
virtual UObject* CreateDirectorInstance(
    TSharedRef<const FSharedPlaybackState> SharedPlaybackState,
    FMovieSceneSequenceID SequenceID) override;
```

기본 = LevelSequence 자산 안 `DirectorBlueprint` BP 인스턴스 생성. 자손 override 로 별도 로직 추가.

### 2.6 Binding 참조 (Director 안) 🟢 (raw §6)

```cpp
void UMyLevelSequenceDirector::ProcessHeroAction()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::ProcessHeroAction);
    FMovieSceneObjectBindingID HeroBinding;   // BP 노드 "Get Sequence Binding"
    TArray<UObject*> Bound = GetBoundObjects(HeroBinding);
    for (UObject* O : Bound)
        if (AMyHero* H = Cast<AMyHero>(O))
            H->StartCustomAnimation();
}
```

### 2.7 EventTrigger vs EventRepeater 🟡 (raw §7 — grep-listed)

| Section | 호출 시점 |
|---------|----------|
| `EventTriggerSection` | 한 번만 (Key 시점) — 표준 |
| `EventRepeaterSection` | Section 범위 동안 매 프레임 — 비쌈 |

매 프레임 반복은 Tick / Sound Loop 등 특수 경우만.

### 2.8 Multiplayer Director 🔴 (raw §8 — inferred)

```cpp
UCLASS()
class UMyMultiplayerDirector : public ULevelSequenceDirector
{
    UFUNCTION(BlueprintCallable, NetMulticast, Reliable)
    void MulticastBossDefeated()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MulticastBossDefeated);
        // 모든 클라이언트 — UI / Sound / Effect
    }
};
```

> ⚠ `ALevelSequenceActor::bReplicatePlayback=true` 의존.

### 2.9 5 시나리오 🟢 (raw §9)

| # | 시나리오 | Director 함수 |
|---|---------|---------------|
| 1 | 보스 등장 사운드 | `PlayBossEntranceSound` — Spawn Sound 2D |
| 2 | GAS 트리거 | `TriggerGAS` — `ASC->TryActivateAbilityByClass` |
| 3 | UI 알림 | `ShowStoryNotification` — UMG Widget Create + AddToViewport |
| 4 | Cinematic Begin/End | `BeginCinematicMode` / `EndCinematicMode` — PC->SetCinematicMode |
| 5 | Custom Clock (5.x) | `GetSequenceCustomClock` — 가변 시간 흐름 |

## 3. 함정 10 🟢 (raw §10)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Director BP Cooked Build 누락 | LevelSequence 자산 = Director BP 자동 포함 검증 |
| 2 | Director 인스턴스 외부 UPROPERTY 보유 | Sequence Play 동안만 — `TWeakObjectPtr` |
| 3 | C++ 자손 시 LevelSequence Parent Class 변경 누락 | Director Settings → Parent Class |
| 4 | Event Track = Possessable 함수 직접 호출 | Director 안 헬퍼로 wrap |
| 5 | EventRepeater 매 프레임 호출 → 성능 저하 | EventTrigger (1회) 우선 |
| 6 | NetMulticast 자동 동기 추측 | `bReplicatePlayback=true` 필요 |
| 7 | Director 안 `GetWorld()` nullptr 추측 | Director = World 컨텍스트 보유 (정상) |
| 8 | Binding ID Guid 하드코딩 | BP 노드 "Get Sequence Binding" |
| 9 | Custom Clock 모든 시퀀스 적용 추측 | Per-sequence / Per-root 분리 |
| 10 | `TRACE_CPUPROFILER_EVENT_SCOPE` 누락 | 모든 콜백 첫 줄 의무 |

## 4. 체크리스트 🟢 (raw §11)

- [ ] Director BP = LevelSequence 자산 안 자동 생성
- [ ] C++ 자손 = Blueprintable + UCLASS
- [ ] LevelSequence Parent Class = C++ 자손 (Director Settings)
- [ ] Event Track 함수 = Director BP 정의
- [ ] EventTrigger vs EventRepeater 명시
- [ ] Binding ID = BP 노드 (Guid 하드코딩 X)
- [ ] Cooked Build 검증
- [ ] Multiplayer = `bReplicatePlayback=true` + NetMulticast
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] Director 외부 보유 = `TWeakObjectPtr`

## 5. 신뢰도 🟢 (raw §12)

| 항목 | tier | 출처 |
|------|------|------|
| ULevelSequenceDirector 6 UFUNCTION | 🟢 verified | `LevelSequenceDirector.h:23-67` |
| GetBoundObjects(Binding) | 🟡 grep-listed | BlueprintPure UFUNCTION 패턴 |
| ULevelSequence::CreateDirectorInstance virtual | 🟢 verified | `LevelSequence.h:61` |
| EventTriggerSection vs EventRepeaterSection | 🟡 grep-listed | 헤더 존재 |
| Director BP 자동 생성 흐름 | 🔴 inferred | Editor UI — 코드 검증 X |
| Multiplayer NetMulticast Director | 🔴 inferred | UE 일반 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 페어: [[sources/ue-levelsequence-tracks]] (UMovieSceneEventTrack §9) · [[sources/ue-levelsequence-levelsequenceplayer]] (CreateDirectorInstance) · [[sources/ue-levelsequence-moviescene]] (UMovieSceneSequence virtual)
- 정책: 🚨 [[concepts/Profiling-Scope-Rule]] (모든 콜백 의무)
- 카테고리 페어: [[sources/ue-blueprint-skill]] (BlueprintImplementableEvent) · [[sources/ue-networking-skill]] (NetMulticast)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 0 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/LevelSequence/references/Director.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/LevelSequence/references/Director.md`
