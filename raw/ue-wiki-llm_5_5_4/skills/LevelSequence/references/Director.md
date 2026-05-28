---
name: levelsequence-director
description: ULevelSequenceDirector + Event Track BP 통합 — UFUNCTION(BlueprintImplementableEvent) OnCreated + 시퀀스 안 Binding 참조 + Event Track 안 BP 함수 호출. BP-only Director / C++ Director 자손 / Cooked Build 검증. UMovieSceneEventTrack 페어.
---

# LevelSequence/Director — BP Director + Event Track

> **위치 (verified)**:
> - **ULevelSequenceDirector** — `Engine/Source/Runtime/LevelSequence/Public/LevelSequenceDirector.h:20` (UE 5.5 — 134 lines)
> - **UMovieSceneEventTrack** — `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/MovieSceneEventTrack.h`
>
> **요지**: LevelSequence 의 **Blueprint 통합 진입점**. Sequencer 안 Event Track 트리거 → Director BP 안 함수 호출. 시퀀스 시간 기반 게임 로직 (보스 등장 / UI 알림 / 사운드 큐 / GAS 트리거).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Director BP 클래스 | LevelSequence 자산 안 자동 생성 — `CreateDirectorInstance` virtual override |
| 🚨 Cooked Build | Director BP = 시퀀스 어셋 의존 — Cooked 안 함께 패키징 |
| 🚨 [`07_ProfilingScopeRule`](../../../references/07_ProfilingScopeRule.md) | Director 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 Lifetime | Director Instance = Sequence Play 동안만 — UWeakObjectPtr 사용 |

---

## 1. ULevelSequenceDirector 핵심 [verified — LevelSequenceDirector.h:23-]

```cpp
UCLASS(Blueprintable, MinimalAPI)
class ULevelSequenceDirector : public UObject
{
public:
    GENERATED_BODY()

    // [1] 생성 시 호출 (BP 구현)
    UFUNCTION(BlueprintImplementableEvent, Category="Sequencer")
    void OnCreated();

    // [2] 시간 조회
    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    FQualifiedFrameTime GetRootSequenceTime() const;

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    FQualifiedFrameTime GetCurrentTime() const;

    // [3] Custom Clock (5.x)
    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    UMovieSceneClock* GetRootSequenceCustomClock() const;

    UFUNCTION(BlueprintCallable, Category="Sequencer|Director")
    UMovieSceneClock* GetSequenceCustomClock() const;

    // [4] Binding 해결 (시퀀스 안 ObjectBinding → 실 액터)
    UFUNCTION(BlueprintPure, Category="Sequencer|Director",
              meta=(WorldContext="WorldContextObject"))
    TArray<UObject*> GetBoundObjects(FMovieSceneObjectBindingID ObjectBinding) const;

    // ... 기타 API
};
```

---

## 2. BP-only Director 작성 흐름 (가장 일반)

```
1. Content Browser 안 LevelSequence 자산 더블클릭 → Sequencer 열림
2. Sequencer 좌측 상단 "Open Director Blueprint" 버튼 클릭
3. BP Editor 안 자동 생성된 LevelSequenceDirector BP 편집
4. BP 안 OnCreated / 커스텀 함수 추가
5. Sequencer 안 Event Track 추가 → Section 안 Key → Event 선택
6. Event 가 호출할 Director BP 함수 매핑
```

---

## 3. Event Track 사용 표준

### 3.1 Director BP 안 함수 정의

```
// LevelSequence_Intro_Director (BP)
Function: PlayBossEntranceSound
  Input: None
  Output: None
  Body:
    GetWorld → Spawn Sound 2D → Sound = BossEntranceCue
```

### 3.2 Sequencer 안 Event Track

```
시퀀스 안:
└── Event Track (Master 또는 Possessable Binding 안)
    └── [120 프레임 — 보스 등장 시점]
        └── EventTrigger Section
            └── Endpoint: PlayBossEntranceSound (Director BP 함수)
```

→ 재생 시 120 프레임에 도달하면 자동 `PlayBossEntranceSound` 호출.

---

## 4. C++ Director 자손 작성 (고급)

BP-only 로 부족한 경우 (네이티브 헬퍼 필요):

```cpp
UCLASS(Blueprintable)
class MYGAME_API UMyLevelSequenceDirector : public ULevelSequenceDirector
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="MyCutscene")
    void TriggerBossSpawn()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::TriggerBossSpawn);
        UWorld* World = GetWorld();
        if (!World) return;

        // 보스 액터 Spawn — Director 가 World 컨텍스트 가짐
        World->SpawnActor<AMyBoss>(BossClass, SpawnLoc, SpawnRot);
    }

    UFUNCTION(BlueprintCallable, Category="MyCutscene")
    void TriggerGAS_GameplayAbility(AActor* TargetActor, TSubclassOf<UGameplayAbility> AbilityClass)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::TriggerGAS_GameplayAbility);
        if (!IsValid(TargetActor) || !AbilityClass) return;

        if (auto* ASC = TargetActor->FindComponentByClass<UAbilitySystemComponent>())
        {
            ASC->TryActivateAbilityByClass(AbilityClass);
        }
    }

protected:
    UPROPERTY(EditDefaultsOnly, Category="MyCutscene")
    TSubclassOf<AActor> BossClass;
};
```

> Sequence 안 BP Director 의 부모 클래스를 `UMyLevelSequenceDirector` 로 설정해야 적용.

---

## 5. ULevelSequence::CreateDirectorInstance Override [verified — LevelSequence.h:61]

LevelSequence 가 Director 인스턴스 생성 시점 — virtual override 가능.

```cpp
// LevelSequence.h:61 (override 가능)
virtual UObject* CreateDirectorInstance(
    TSharedRef<const FSharedPlaybackState> SharedPlaybackState,
    FMovieSceneSequenceID SequenceID) override;
```

기본 구현 = LevelSequence 자산 안 `DirectorBlueprint` BP 인스턴스 생성. 자손 클래스에서 별도 로직 추가 가능.

---

## 6. 시퀀스 안 Binding 참조 (Director 안)

```cpp
// Director BP 안 또는 C++ 자손
void UMyLevelSequenceDirector::ProcessHeroAction()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyLevelSequenceDirector::ProcessHeroAction);

    // 1. Sequencer 안 Hero Binding 검색 (BP 노드 = "Get Sequence Binding")
    FMovieSceneObjectBindingID HeroBinding;   // Sequencer 안 노출된 Binding 변수
    HeroBinding.SetGuid(FGuid(TEXT("...")));  // 또는 BP 안 자동 전달

    // 2. 실 액터 가져오기
    TArray<UObject*> BoundObjects = GetBoundObjects(HeroBinding);
    for (UObject* Obj : BoundObjects)
    {
        if (AMyHero* Hero = Cast<AMyHero>(Obj))
        {
            Hero->StartCustomAnimation();
        }
    }
}
```

---

## 7. EventTriggerSection vs EventRepeaterSection [verified — Tracks.md §8]

| Section | 호출 시점 |
|---------|----------|
| **`EventTriggerSection`** | 한 번만 (Key 시점) |
| **`EventRepeaterSection`** | Section 범위 동안 매 프레임 반복 |

> 매 프레임 반복 = 비쌈 — Tick / Sound Loop 등 특수 경우에만.

---

## 8. 멀티플레이 Director (Replication)

```cpp
// Director BP — Replicated Event
UCLASS()
class UMyMultiplayerDirector : public ULevelSequenceDirector
{
    GENERATED_BODY()

    // 서버에서만 호출 → 모든 클라이언트 동기
    UFUNCTION(BlueprintCallable, NetMulticast, Reliable, Category="MyCutscene")
    void MulticastBossDefeated()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyMultiplayerDirector::MulticastBossDefeated);
        // 모든 클라이언트에서 실행 — UI 알림 / 사운드 / 효과
    }
};
```

> ⚠ **Director 가 NetMulticast 호출** = `ALevelSequenceActor::bReplicatePlayback=true` 의존.

---

## 9. 시나리오 5종

### 9.1 보스 등장 사운드

```
Event Track 시점 (보스 등장 0.5초 전):
└── PlayBossEntranceSound (Director BP 함수)
    → Sound 2D Spawn
```

### 9.2 GAS 어빌리티 트리거

```
Event Track 시점 (스킬 발동 프레임):
└── TriggerGAS_GameplayAbility (Director BP 함수)
    → Hero->ASC->TryActivateAbilityByClass(SwordSlashAbility)
```

### 9.3 UI 알림

```
Event Track 시점 (스토리 진행 알림):
└── ShowStoryNotification (Director BP 함수)
    → UMG Widget Create + AddToViewport
```

### 9.4 Cinematic 시작/종료 (BeginCinematicMode / EndCinematicMode)

```
Sequence 시작 (Frame 0):
└── BeginCinematicMode (Director BP)
    → PlayerController->SetCinematicMode(true, true, true, true, true)

Sequence 끝 (Frame End):
└── EndCinematicMode (Director BP)
    → PlayerController->SetCinematicMode(false, ...)
```

### 9.5 Custom Clock (5.x — 가변 시간 흐름)

```cpp
UMovieSceneClock* Clock = Director->GetSequenceCustomClock();
// Clock 의 Time 조작으로 시퀀스 흐름 가변
```

---

## 10. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Director BP Cooked Build 누락 | LevelSequence 자산 = Director BP 자동 포함 (Cooked 검증) |
| 2 | Director 인스턴스 외부 보유 (UPROPERTY*) | Sequence Play 동안만 — `TWeakObjectPtr` 권장 |
| 3 | C++ Director 자손 시 LevelSequence 자산 BP 부모 변경 누락 | LevelSequence 자산 → "Director Settings" → Parent Class 변경 |
| 4 | Event Track 안 함수 = Director BP 함수만 가능 (Possessable 함수 X) | Possessable 함수 호출 시 Director 안 헬퍼로 wrapping |
| 5 | EventRepeaterSection 매 프레임 호출 → 성능 저하 | EventTrigger (1회) 우선 / Repeater 는 특수 경우만 |
| 6 | NetMulticast Director 함수 = 자동 동기 추측 | `ALevelSequenceActor::bReplicatePlayback=true` 필요 |
| 7 | Director 안 `GetWorld()` nullptr 추측 | Director 는 World 컨텍스트 가짐 (정상 작동) |
| 8 | Binding ID Guid 하드코딩 | BP 노드 "Get Sequence Binding" 사용 (자동 생성) |
| 9 | Custom Clock 5.x = 모든 시퀀스 적용 추측 | Per-sequence 또는 Per-root 분리 (GetSequence vs GetRoot) |
| 10 | Director 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 누락 | 모든 콜백 의무 |

---

## 11. 체크리스트

- [ ] Director BP = LevelSequence 자산 안 자동 생성
- [ ] C++ Director 자손 = Blueprintable + UCLASS 마크
- [ ] LevelSequence 자산 → Director Settings → Parent Class = C++ 자손
- [ ] Event Track 함수 = Director BP 안 정의
- [ ] EventTrigger (1회) vs EventRepeater (반복) 명시
- [ ] Binding ID = BP 노드 사용 (Guid 하드코딩 X)
- [ ] Cooked Build 검증 — Director BP 동작 확인
- [ ] Multiplayer = `bReplicatePlayback=true` + NetMulticast Director
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] Sequence Play 동안만 Director 유효 — `TWeakObjectPtr` 보관

---

## 12. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| ULevelSequenceDirector 클래스 + UFUNCTION 4종 (OnCreated / GetRootSequenceTime / GetCurrentTime / GetCustomClock) | **[verified]** ✅ | `LevelSequenceDirector.h:23-67` |
| GetBoundObjects(Binding) | **[grep-listed]** ⚠ | `LevelSequenceDirector.h` 안 BlueprintPure UFUNCTION 일반 패턴 |
| ULevelSequence::CreateDirectorInstance virtual | **[verified]** ✅ | `LevelSequence.h:61` |
| EventTriggerSection vs EventRepeaterSection | **[grep-listed]** ⚠ | `MovieSceneEventSection.h` / `MovieSceneEventRepeaterSection.h` 헤더 존재 |
| Sequencer 안 Director BP 자동 생성 흐름 | **[inferred]** ❌ | Editor UI 흐름 — 코드 검증 X |
| Multiplayer NetMulticast Director | **[inferred]** ❌ | UE 일반 — 검증 권장 |

---

## 13. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — 런타임 재생 (Director 호출)
- [`./Tracks.md`](./Tracks.md) — UMovieSceneEventTrack (§8)
- [`./MovieScene.md`](./MovieScene.md) — UMovieSceneSequence::CreateDirectorInstance virtual
- [`Blueprint/SKILL.md`](../../Blueprint/SKILL.md) — BlueprintImplementableEvent + Native Event
- [`Networking/SKILL.md`](../../Networking/SKILL.md) — NetMulticast / Replication

---

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **ULevelSequenceDirector 4 UFUNCTION [verified]** + **Event Track 사용 흐름** + **BP-only / C++ 자손 작성** + **CreateDirectorInstance virtual** + Binding 참조 + Multiplayer + 시나리오 5종 + 함정 10. Engine 5.5.4 검증 — LevelSequenceDirector.h:23-67. |
