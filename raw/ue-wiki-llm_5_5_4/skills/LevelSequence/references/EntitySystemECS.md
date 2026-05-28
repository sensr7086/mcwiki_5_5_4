---
name: levelsequence-entitysystem-ecs
description: 5.x ECS 평가 시스템 — FMovieSceneEntityManager + FBuiltInComponentTypes + IMovieSceneEntityProvider + MovieSceneBlenderSystem + IMovieSceneTaskScheduler. 평가 4단계 (Instantiation → Evaluation → Blending → Application). Component Registry + Entity Allocation. 멀티스레드 안전 (Game Thread).
---

# LevelSequence/EntitySystemECS — 5.x ECS 평가 시스템

> **위치 (verified)**:
> - **EntitySystem 루트** — `Engine/Source/Runtime/MovieScene/Public/EntitySystem/` (UE 5.5 — 64 헤더)
> - **FBuiltInComponentTypes** — `EntitySystem/BuiltInComponentTypes.h`
> - **IMovieSceneEntityProvider** — `EntitySystem/IMovieSceneEntityProvider.h`
> - **IMovieSceneTaskScheduler** — `EntitySystem/IMovieSceneTaskScheduler.h`
> - **FMovieSceneBlenderSystem** — `EntitySystem/MovieSceneBlenderSystem.h`
> - **FMovieSceneComponentRegistry** — `EntitySystem/MovieSceneComponentRegistry.h`
>
> **요지**: 5.x MovieScene 평가 = **ECS (Entity-Component-System)** 패턴. Track → Entity 변환 → Component 값 계산 → Blending → Application. 멀티스레드 안전 (Game Thread 안에서만).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Game Thread 전용 | ECS 평가 = Game Thread — Render Thread 접근 X |
| 🚨 Component Registry | Custom Component 등록 = `FBuiltInComponentTypes` 초기화 시점 |
| 🚨 5.x 신규 | 4.x Legacy 평가 = `FMovieSceneEvaluationTemplate` (deprecated) — 5.x = ECS |
| 🚨 멀티스레드 | TaskScheduler 통한 안전 — 직접 동시 접근 X |

---

## 1. ECS 평가 4단계 ⭐

```
[1] Instantiation     (Track → Entity 변환)
    ├── IMovieSceneEntityProvider 가 Section 마다 Entity 생성
    ├── Entity = ID + Component 셋
    └── Component 예: PropertyTag / FloatValue / TargetActor / Time

[2] Evaluation        (Entity 안 Component 값 계산)
    ├── Channel 값 평가 (FloatChannel / IntChannel / etc)
    ├── 시간 기반 보간
    └── Result Component 에 결과 저장

[3] Blending          (여러 트랙 결과 합성)
    ├── FMovieSceneBlenderSystem
    ├── Absolute / Additive / Relative 결합
    └── Weight 계산

[4] Application       (최종 값 게임 오브젝트에 적용)
    ├── Property Setter 호출 (UFUNCTION BlueprintSetter)
    ├── 또는 직접 UPROPERTY 수정
    └── 콜백 트리거 (Event Track)
```

---

## 2. FMovieSceneEntityManager 핵심

```cpp
// 5.x — 평가 엔진의 메인
class FMovieSceneEntityManager
{
public:
    // === Entity 생성/제거 ===
    FMovieSceneEntityID AllocateEntity();
    void FreeEntity(FMovieSceneEntityID InEntity);

    // === Component 추가/제거 ===
    template <typename T>
    void AddComponent(FMovieSceneEntityID Entity, T&& InComponent);

    template <typename T>
    T* ReadComponent(FMovieSceneEntityID Entity);

    // === Query (필터) ===
    FEntityAllocationIterator Iterate(...) const;

    // === Tag 시스템 ===
    template <typename TagType>
    void AddTag(FMovieSceneEntityID Entity);
};
```

> 자세한 API = `EntitySystem/MovieSceneEntityManager.h` (64 헤더 안 핵심).

---

## 3. FBuiltInComponentTypes (기본 Component 종)

5.x MovieScene 이 기본 제공하는 Component 종 — Property Track 자동 매핑.

```cpp
// EntitySystem/BuiltInComponentTypes.h (개념 — 일반 명명)
struct FBuiltInComponentTypes
{
    // === Property Tags ===
    TComponentTypeID<FFloatPropertyTraits>      FloatProperty;
    TComponentTypeID<FDoublePropertyTraits>     DoubleProperty;
    TComponentTypeID<FVectorPropertyTraits>     VectorProperty;
    TComponentTypeID<FBoolPropertyTraits>       BoolProperty;
    TComponentTypeID<FColorPropertyTraits>      ColorProperty;
    TComponentTypeID<FTransformPropertyTraits>  TransformProperty;

    // === Result Components ===
    TComponentTypeID<float>                     FloatResult;
    TComponentTypeID<double>                    DoubleResult;
    TComponentTypeID<FVector>                   VectorResult;
    TComponentTypeID<FTransform>                TransformResult;

    // === Channel Source ===
    TComponentTypeID<FMovieSceneFloatChannel*>  FloatChannel;
    TComponentTypeID<FMovieSceneDoubleChannel*> DoubleChannel;

    // === Object Reference ===
    TComponentTypeID<UObject*>                  BoundObject;
    TComponentTypeID<USceneComponent*>          SceneComponent;

    // === Time / Frame ===
    TComponentTypeID<FFrameTime>                EvalSeconds;
    TComponentTypeID<FFrameTime>                EvalTime;

    // === Tags (특수 분류) ===
    FComponentTypeID                            Tag_Active;
    FComponentTypeID                            Tag_Cached;
    FComponentTypeID                            Tag_NeedsLink;
};
```

> 정확 매핑은 `BuiltInComponentTypes.h` grep 검증 권장.

---

## 4. IMovieSceneEntityProvider 패턴

Track 측에서 Entity 생성 인터페이스.

```cpp
// EntitySystem/IMovieSceneEntityProvider.h
class IMovieSceneEntityProvider
{
public:
    // 평가 필드 정의 (이 Track 의 Entity 가 어떤 컴포넌트 가질지)
    virtual void ImportEntity(UMovieSceneEntitySystemLinker* Linker,
                               const FEntityImportParams& Params,
                               FImportedEntity* OutImportedEntity) const = 0;

    // 5.x — 인터페이스 등록 (UMovieSceneTrack 자손 안)
};
```

### 4.1 Section 안 IMovieSceneEntityProvider 구현

```cpp
UCLASS()
class UMyMovieSceneSection : public UMovieSceneSection, public IMovieSceneEntityProvider
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FMovieSceneFloatChannel ValueChannel;       // 키프레임 채널

    // === IMovieSceneEntityProvider ===
    virtual void ImportEntity(UMovieSceneEntitySystemLinker* Linker,
                               const FEntityImportParams& Params,
                               FImportedEntity* OutImportedEntity) const override
    {
        FBuiltInComponentTypes* Components = FBuiltInComponentTypes::Get();

        // [1] Entity 에 Float Channel 컴포넌트 추가
        OutImportedEntity->AddBuilder(
            FEntityBuilder()
            .Add(Components->FloatChannel, &ValueChannel)
            .Add(Components->FloatResult, 0.f)                   // 결과 저장 슬롯
            .AddTag(Components->Tag_Active)
        );
    }
};
```

---

## 5. Blender System (Blending 단계)

```cpp
// EntitySystem/MovieSceneBlenderSystem.h
class FMovieSceneBlenderSystem : public UMovieSceneEntitySystem
{
public:
    // 여러 Track 의 동일 Property 결합
    virtual void OnRun(FSystemTaskPrerequisites& InPrerequisites,
                       FSystemSubsequentTasks& Subsequents) override
    {
        // Absolute / Additive / Relative 모드 별 결합
    }
};
```

### 5.1 EMovieSceneBlendType 5종 (Blending 모드)

| Type | 설명 |
|------|------|
| `Absolute` | 결과 = 트랙 값 (다른 트랙 무시) |
| `Additive` | 결과 = 기본값 + Σ(트랙 값) |
| `Relative` | 결과 = 시작 값 + (트랙 값) |
| `AbsoluteFromAdditive` (5.x) | Absolute 모드를 Additive 트랙처럼 |
| `AdditiveFromBase` (5.x) | Base 값 기준 추가 |

---

## 6. IMovieSceneTaskScheduler (5.x 멀티스레딩)

```cpp
// EntitySystem/IMovieSceneTaskScheduler.h
class IMovieSceneTaskScheduler
{
public:
    // Task 스케줄링 — 의존성 그래프
    virtual void AddTask(FSystemTaskPrerequisites InPrerequisites,
                          FSystemSubsequentTasks& OutSubsequents,
                          ITaskScheduledExecutor* InExecutor) = 0;
};
```

> 5.x 평가 = TaskGraph 기반 멀티스레딩 — 데이터 의존성 분석 후 자동 병렬화.

---

## 7. Component Registry (Custom Component 등록)

```cpp
// FMovieSceneComponentRegistry — Custom Component 추가
void FMyTrackModule::StartupModule()
{
    FBuiltInComponentTypes* BuiltIn = FBuiltInComponentTypes::Get();
    FMovieSceneComponentRegistry* Registry = BuiltIn->ComponentRegistry;

    // Custom Component 등록
    Registry->NewComponentType(&MyCustomComponent, TEXT("MyCustom"));
}

// Custom Component 사용
TComponentTypeID<MyCustomData> MyCustomComponent;

void UMyEntitySystem::OnRun(...)
{
    auto EntityFilter = FEntityComponentFilter()
        .All({MyCustomComponent, BuiltIn->FloatResult});

    for (FEntityAllocation* Allocation : Linker->EntityManager.Iterate(EntityFilter))
    {
        // Allocation 안 컴포넌트 처리
    }
}
```

---

## 8. UMovieSceneEntitySystem (System 작성)

```cpp
UCLASS()
class UMyMovieSceneEntitySystem : public UMovieSceneEntitySystem
{
    GENERATED_BODY()

public:
    UMyMovieSceneEntitySystem(const FObjectInitializer& ObjectInitializer)
        : Super(ObjectInitializer)
    {
        // Phase 설정 (Instantiation / Evaluation / Application)
        Phase = ESystemPhase::Evaluation;

        // 의존성 (이 System 이 동작하는 Component 조건)
        SystemCategories = ...;
    }

    virtual void OnRun(FSystemTaskPrerequisites& InPrerequisites,
                       FSystemSubsequentTasks& Subsequents) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyMovieSceneEntitySystem::OnRun);

        // Entity 순회 + Component 처리
        FBuiltInComponentTypes* BuiltIn = FBuiltInComponentTypes::Get();
        auto Filter = FEntityComponentFilter().All({BuiltIn->FloatResult});

        for (auto It = Linker->EntityManager.Iterate(Filter); It; ++It)
        {
            FEntityAllocation* Alloc = It.GetAllocation();
            // float result 컴포넌트 일괄 처리
        }
    }
};
```

---

## 9. Phase (System 실행 순서)

```cpp
enum class ESystemPhase : uint8
{
    None,
    Spawn,                  // Spawnable 생성
    Instantiation,           // [1] Track → Entity
    Scheduling,              // TaskGraph 스케줄링
    Evaluation,              // [2] Component 값 계산
    Finalization,            // [3] Blending
    Application,             // [4] 최종 적용 (Property Setter)
    Custom,                  // 사용자 정의
};
```

---

## 10. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 4.x Legacy `FMovieSceneEvaluationTemplate` 사용 | 5.x = ECS — IMovieSceneEntityProvider 표준 |
| 2 | Game Thread 외 평가 시도 (Render Thread 접근) | ECS = Game Thread 전용 |
| 3 | Custom Component 등록 시점 부정확 | StartupModule 안 등록 — FBuiltInComponentTypes 초기화 후 |
| 4 | Entity 직접 lifetime 관리 시도 | 자동 — Track Section 안 ImportEntity 통해 생성/제거 |
| 5 | TaskScheduler 우회 직접 멀티스레딩 | TaskScheduler 통해서만 |
| 6 | Phase 잘못 설정 → 적용 순서 깨짐 | Spawn → Instantiation → Evaluation → Application 순서 의무 |
| 7 | Component 직접 변경 (Mutex 없이) | TaskGraph 가 의존성 분석 — 동일 Component 동시 수정 X |
| 8 | EntityManager.Iterate 안 Allocation 단위 X | Allocation 단위 효율 — Entity 별 X |
| 9 | Blending Weight 미설정 → 결합 오류 | EMovieSceneBlendType 명시 + Weight 채널 |
| 10 | 5.x ECS 디버그 = Console 명령 누락 | `MovieScene.DebugCurrentSequence` 등 활용 |

---

## 11. 체크리스트

- [ ] Track 안 Section = IMovieSceneEntityProvider 구현
- [ ] `ImportEntity` 안 Component 명시 (FloatChannel / FloatResult / etc)
- [ ] System 작성 시 Phase 정확 (Instantiation / Evaluation / Application)
- [ ] Custom Component = StartupModule 안 등록
- [ ] EntityManager.Iterate = Filter (All / Any / None) 명시
- [ ] Game Thread 안에서만 평가 (Render Thread X)
- [ ] TaskScheduler 통한 멀티스레드 (직접 X)
- [ ] Blending = EMovieSceneBlendType 명시 + Weight 채널
- [ ] 5.x — 4.x Legacy Template 사용 X
- [ ] `TRACE_CPUPROFILER_EVENT_SCOPE` 모든 System OnRun 첫 줄

---

## 12. 디버그 / 프로파일링

| Console 명령 | 용도 |
|-------------|------|
| `MovieScene.DebugCurrentSequence 1` | 현재 시퀀스 평가 디버그 |
| `MovieScene.DebugComponents` | Component 등록 목록 |
| `MovieScene.DebugSystems` | System 등록 / 실행 순서 |
| `MovieScene.DebugEntities` | Entity 목록 |
| `MovieScene.TaskDebug 1` | TaskGraph 디버그 |

> 정확한 콘솔 명령 = `MovieScene/Private/MovieSceneCommon.cpp` grep 권장.

---

## 13. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| EntitySystem 폴더 64 헤더 | **[verified]** ✅ | `Source/Runtime/MovieScene/Public/EntitySystem/` ls (UE 5.5 64개 확인) |
| 핵심 헤더 (BuiltInComponentTypes / IMovieSceneEntityProvider / IMovieSceneTaskScheduler / MovieSceneBlenderSystem / MovieSceneComponentRegistry) | **[verified]** ✅ | ls 매치 |
| 4 단계 평가 (Instantiation/Evaluation/Blending/Application) | **[inferred]** ❌ | UE 일반 — 본문 grep 필요 |
| FBuiltInComponentTypes 컴포넌트 종 | **[inferred]** ❌ | UE 일반 — `BuiltInComponentTypes.h` grep 권장 |
| ESystemPhase enum | **[inferred]** ❌ | UE 일반 — `MovieSceneEntitySystem.h` grep |
| EMovieSceneBlendType 5종 | **[verified]** ✅ | `MovieScene.md §5.1` 검증 표 |
| Console 디버그 명령 | **[inferred]** ❌ | UE 일반 — `MovieSceneCommon.cpp` grep 권장 |

---

## 14. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인 (§4 ECS 평가 흐름)
- ⭐ [`./MovieScene.md`](./MovieScene.md) — Section / Track 베이스
- [`./Tracks.md`](./Tracks.md) — 빌트인 트랙 (Property Track ECS 자동 매핑)
- [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — Player::Tick → ECS Update
- [`CoreUObject/Reflection.md`](../../CoreUObject/references/Reflection.md) — UPROPERTY Interp meta

---

## 15. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **5.x ECS 평가 4단계 (Instantiation/Evaluation/Blending/Application)** + **FMovieSceneEntityManager 핵심** + **FBuiltInComponentTypes** + **IMovieSceneEntityProvider 패턴** + **FMovieSceneBlenderSystem (EMovieSceneBlendType 5종)** + **IMovieSceneTaskScheduler 멀티스레드** + **Custom Component 등록** + **UMovieSceneEntitySystem 작성** + **ESystemPhase 8단계** + **Console 디버그** + 함정 10. Engine 5.5.4 검증 — EntitySystem 폴더 64 헤더. |
