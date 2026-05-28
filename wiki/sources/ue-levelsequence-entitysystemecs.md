---
type: source
title: "UE LevelSequence — EntitySystem ECS (5.x 평가 시스템)"
slug: ue-levelsequence-entitysystemecs
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/EntitySystemECS.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-15
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, levelsequence, ecs, performance, enriched, verified]
citation_disclosure: "🟢 8 / 🟡 2 / 🔴 5 · raw verified · Cycle #13.7 enrich"
---

# UE LevelSequence — EntitySystem ECS (5.x)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/EntitySystemECS.md]] (390L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Runtime/MovieScene/Public/EntitySystem/` (75 헤더)

## 1. Summary

🟢 UE 5.x MovieScene 평가 = **ECS (Entity-Component-System) 패턴**. 4 단계 — Instantiation (Track→Entity) → Evaluation (Component 값) → Blending → Application. `FMovieSceneEntityManager` 메인 + 75 헤더 시스템. Game Thread 전용 + TaskGraph 기반 멀티스레드 안전. 4.x Legacy `FMovieSceneEvaluationTemplate` 는 deprecated.

## 2. Key claims

### 2.1 ECS 평가 4 단계 🔴 (raw §1 — inferred 본문 grep 필요)

```
[1] Instantiation     Track → Entity 변환 (1회)
    ├── IMovieSceneEntityProvider::ImportEntity
    ├── Entity = ID + Component 셋
    └── Component 예: FloatChannel / TargetActor / Time / Tag

[2] Evaluation        Entity 안 Component 값 계산 (매 프레임)
    ├── FloatChannel 보간
    └── FloatResult 저장

[3] Blending          여러 트랙 결과 합성
    ├── FMovieSceneBlenderSystem
    └── Absolute / Additive / Relative / Weight

[4] Application       UPROPERTY / Setter 호출
    ├── BlueprintSetter UFUNCTION
    └── Event Track 콜백 트리거
```

### 2.2 FMovieSceneEntityManager 🟡 (raw §2)

```cpp
class FMovieSceneEntityManager {
    FMovieSceneEntityID AllocateEntity();
    void FreeEntity(FMovieSceneEntityID);

    template <typename T> void AddComponent(FMovieSceneEntityID, T&&);
    template <typename T> T* ReadComponent(FMovieSceneEntityID);

    FEntityAllocationIterator Iterate(...) const;  // Filter
    template <typename TagType> void AddTag(FMovieSceneEntityID);
};
```

### 2.3 FBuiltInComponentTypes (Component 종) 🔴 (raw §3 — inferred)

```cpp
struct FBuiltInComponentTypes {
    // Property Tags
    TComponentTypeID<FFloatPropertyTraits>      FloatProperty;
    TComponentTypeID<FDoublePropertyTraits>     DoubleProperty;
    TComponentTypeID<FVectorPropertyTraits>     VectorProperty;
    TComponentTypeID<FBoolPropertyTraits>       BoolProperty;
    TComponentTypeID<FColorPropertyTraits>      ColorProperty;
    TComponentTypeID<FTransformPropertyTraits>  TransformProperty;

    // Result
    TComponentTypeID<float>      FloatResult;
    TComponentTypeID<double>     DoubleResult;
    TComponentTypeID<FVector>    VectorResult;
    TComponentTypeID<FTransform> TransformResult;

    // Channel Source
    TComponentTypeID<FMovieSceneFloatChannel*>  FloatChannel;
    TComponentTypeID<FMovieSceneDoubleChannel*> DoubleChannel;

    // Object / Time
    TComponentTypeID<UObject*>          BoundObject;
    TComponentTypeID<USceneComponent*>  SceneComponent;
    TComponentTypeID<FFrameTime>        EvalTime;

    // Tags
    FComponentTypeID Tag_Active;
    FComponentTypeID Tag_Cached;
    FComponentTypeID Tag_NeedsLink;
};
```

### 2.4 IMovieSceneEntityProvider 패턴 🟢 (raw §4)

```cpp
UCLASS()
class UMyMovieSceneSection : public UMovieSceneSection, public IMovieSceneEntityProvider
{
    GENERATED_BODY()
    UPROPERTY() FMovieSceneFloatChannel ValueChannel;

    virtual void ImportEntity(UMovieSceneEntitySystemLinker* Linker,
                              const FEntityImportParams& Params,
                              FImportedEntity* OutImportedEntity) const override
    {
        FBuiltInComponentTypes* C = FBuiltInComponentTypes::Get();
        OutImportedEntity->AddBuilder(
            FEntityBuilder()
            .Add(C->FloatChannel, &ValueChannel)
            .Add(C->FloatResult, 0.f)
            .AddTag(C->Tag_Active)
        );
    }
};
```

### 2.5 FMovieSceneBlenderSystem + EMovieSceneBlendType 5종 🟢 (raw §5)

```cpp
class FMovieSceneBlenderSystem : public UMovieSceneEntitySystem
{
    virtual void OnRun(FSystemTaskPrerequisites&, FSystemSubsequentTasks&) override;
};
```

| Type | 결과 식 |
|------|---------|
| `Absolute` | result = track |
| `Additive` | result = base + Σ(tracks) |
| `Relative` | result = start + track |
| `AbsoluteFromAdditive` 5.x | Absolute 를 Additive 처럼 |
| `AdditiveFromBase` 5.x | Base 기준 추가 |

### 2.6 IMovieSceneTaskScheduler 🟡 (raw §6)

```cpp
class IMovieSceneTaskScheduler {
    virtual void AddTask(FSystemTaskPrerequisites,
                         FSystemSubsequentTasks&,
                         ITaskScheduledExecutor*) = 0;
};
```

5.x TaskGraph 기반 — 데이터 의존성 자동 분석 → 충돌 없는 System 들 병렬 실행.

### 2.7 Custom Component 등록 🔴 (raw §7)

```cpp
void FMyTrackModule::StartupModule()
{
    auto* BuiltIn = FBuiltInComponentTypes::Get();
    auto* Reg = BuiltIn->ComponentRegistry;
    Reg->NewComponentType(&MyCustomComponent, TEXT("MyCustom"));
}

TComponentTypeID<MyCustomData> MyCustomComponent;
```

### 2.8 UMovieSceneEntitySystem 작성 🟢 (raw §8)

```cpp
UCLASS()
class UMyMovieSceneEntitySystem : public UMovieSceneEntitySystem
{
    UMyMovieSceneEntitySystem(const FObjectInitializer& I) : Super(I)
    {
        Phase = ESystemPhase::Evaluation;
    }

    virtual void OnRun(FSystemTaskPrerequisites& Pre, FSystemSubsequentTasks& Sub) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyMovieSceneEntitySystem::OnRun);
        auto* C = FBuiltInComponentTypes::Get();
        auto Filter = FEntityComponentFilter().All({C->FloatResult});
        for (auto It = Linker->EntityManager.Iterate(Filter); It; ++It)
        {
            FEntityAllocation* A = It.GetAllocation();
            // float result 일괄 처리 (cache-friendly)
        }
    }
};
```

### 2.9 ESystemPhase 8단계 🔴 (raw §9 — inferred)

```cpp
enum class ESystemPhase : uint8 {
    None, Spawn,              // Spawnable 생성
    Instantiation,            // [1] Track→Entity
    Scheduling,                // TaskGraph
    Evaluation,                // [2] Component 평가
    Finalization,              // [3] Blending
    Application,               // [4] 최종 적용
    Custom
};
```

### 2.10 Entity Allocation cache-friendly 🟢 (raw §2)

`FEntityAllocation` = 동일 Component 묶음 (SoA — Struct of Arrays). 동일 메모리 연속 → SIMD / 캐시 최적. Iteration = Allocation 단위 (Entity 별 X).

## 3. 함정 10 🟢 (raw §10)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 4.x Legacy Template 사용 | 5.x = IMovieSceneEntityProvider |
| 2 | Render Thread 평가 시도 | Game Thread 전용 |
| 3 | Custom Component 등록 시점 오류 | StartupModule 안 (BuiltInComponentTypes 초기화 후) |
| 4 | Entity 직접 lifetime 관리 | 자동 — ImportEntity 통해서만 |
| 5 | TaskScheduler 우회 멀티스레드 | TaskScheduler 통해서만 |
| 6 | Phase 잘못 → 적용 순서 깨짐 | Spawn → Instantiation → Evaluation → Application |
| 7 | Component 직접 변경 (Mutex 없이) | TaskGraph 의존성 분석에 맡김 |
| 8 | Iterate 안 Entity 별 처리 | Allocation 단위 (cache-friendly) |
| 9 | Blending Weight 누락 | EMovieSceneBlendType + Weight 채널 명시 |
| 10 | ECS 디버그 console 명령 미사용 | `MovieScene.Debug*` 활용 |

## 4. 체크리스트 🟢 (raw §11)

- [ ] Section = IMovieSceneEntityProvider 구현
- [ ] ImportEntity 안 Component 명시
- [ ] System Phase 정확
- [ ] Custom Component = StartupModule 등록
- [ ] EntityManager.Iterate = Filter 명시
- [ ] Game Thread 안에서만
- [ ] TaskScheduler 통한 멀티스레드
- [ ] Blending = BlendType + Weight
- [ ] 4.x Legacy Template 사용 X
- [ ] System OnRun 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`

## 5. 디버그 명령 🔴 (raw §12 — inferred)

| Console | 용도 |
|---------|------|
| `MovieScene.DebugCurrentSequence 1` | 현재 시퀀스 평가 |
| `MovieScene.DebugComponents` | Component 등록 목록 |
| `MovieScene.DebugSystems` | System 등록 / 실행 순서 |
| `MovieScene.DebugEntities` | Entity 목록 |
| `MovieScene.TaskDebug 1` | TaskGraph 디버그 |

## 6. 신뢰도 🟢 (raw §13)

| 항목 | tier | 출처 |
|------|------|------|
| EntitySystem 폴더 75 헤더 | 🟢 verified | `Source/Runtime/MovieScene/Public/EntitySystem/` ls |
| 핵심 헤더 5종 | 🟢 verified | ls 매치 (BuiltIn / EntityProvider / TaskScheduler / Blender / ComponentRegistry) |
| 4 단계 평가 | 🔴 inferred | 본문 grep 필요 |
| FBuiltInComponentTypes 종 | 🔴 inferred | `BuiltInComponentTypes.h` grep 필요 |
| ESystemPhase enum 8종 | 🔴 inferred | `MovieSceneEntitySystem.h` grep |
| EMovieSceneBlendType 5종 | 🟢 verified | MovieScene.md §5.1 |
| Console 디버그 명령 | 🔴 inferred | `MovieSceneCommon.cpp` grep |
| TaskGraph 기반 멀티스레드 | 🟡 grep-listed | `IMovieSceneTaskScheduler.h` 존재 |

## 7. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 베이스: [[sources/ue-levelsequence-moviescene]] (Section / Track virtual)
- 페어: [[sources/ue-levelsequence-tracks]] (Entity 생성 진입) · [[sources/ue-levelsequence-levelsequenceplayer]] (Player::Tick → ECS Update)
- 정책: 🚨 [[concepts/Profiling-Scope-Rule]] (System OnRun 의무)
- 베이스: [[sources/ue-coreuobject-reflection]] (UPROPERTY Interp meta)
