---
type: synthesis
title: "KMCProject UMCActorSpawnSubsystem 측정 H1 — TActorIterator vs Octree + WarmUpPool + Bundle PreLoad + Significance"
slug: mc-actor-spawn-subsystem-h1-measurement
created: 2026-05-13
last_updated: 2026-05-13
sources:
  - "[[sources/ue-measure-readme]]"
  - "[[sources/ue-measure-summary]]"
  - "[[sources/ue-measure-instancedsubobject-2026-05-12]]"
  - "[[sources/ue-spatialpartition-toctree2]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-ref-09-globaliteratorpolicy]]"
  - "[[sources/ue-ref-07-profilingscopeRule]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/USignificanceManager]]"
concepts:
  - "[[concepts/Global-Iterator-Avoidance]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
status: draft
tags: [synthesis, measurement, h1, kmcproject, actor-spawn, octree2, significance, bundle-preload, performance]
citation_disclosure: "🟢 8 (vault 측정 방법론 + 정책) / 🟡 6 (예상 값 외삽) / 🔴 8 (실측 미완료 — 사용자 PIE 후 검증)"
---

# UMCActorSpawnSubsystem 측정 H1 — Iterator vs Octree + Pool + Bundle + Significance

> **draft 상태** — 측정 계획 (methodology) 정의 + 예상 값 (🟡 외삽). **실측 결과 (🟢) 는 사용자 PIE 검증 후 갱신**.
>
> **vault summary H1 추적**: [[sources/ue-measure-summary]] 의 H1 가설 — "vault 적용 시 시도 횟수 / 비용 단축". 본 측정은 H1 의 *런타임 비용 차원* — vault 적용 코드의 *실제 ms 단축* 검증.

## 1. Thesis 🟢

KMCProject `UMCActorSpawnSubsystem` 은 4 개 vault 패턴을 통합 — **각 패턴이 *실제로* 측정 가능한 비용 단축** 인가? 본 measurement synthesis 는 4 축 비교 매트릭스:

```
[1] Spatial Query     — TActorIterator O(N) vs GetActorsInRadius O(log N + K)
[2] Pool 효과          — WarmUpPool(N) vs no warm — 첫 RequestSpawnAsync ms
[3] Bundle PreLoad     — PreloadActorClasses vs no preload — 첫 spawn ms
[4] Significance ON/OFF — bEnableSignificanceManagement true vs false — 매 frame 비용
```

vault 의 H1 가설 ([[sources/ue-measure-summary]]):
- *vault 적용 → 시도 횟수 단축* (정성적) — 본 세션에서 검증됨 (6 함정 vault 화)
- *vault 적용 → 런타임 비용 단축* (정량적) — **본 measurement 에서 검증 대상**

## 2. 측정 매트릭스 (예상 + 실측)

### 2.1 측정 항목 4 축

| # | 변수 | 예상 (🟡) | 실측 (🔴) |
| -- | -- | -- | -- |
| 1 | 200 NPC / 반경 1500cm 쿼리 — TActorIterator (vault [[concepts/Global-Iterator-Avoidance]] 금지) | ~5 ms (O(N) × 200) | TBD |
| 1 | 200 NPC / 반경 1500cm 쿼리 — GetActorsInRadius (TOctree2) | ~0.1 ms (O(log N + K)) | TBD |
| 1 | **비율** | ~50× 단축 | TBD |
| 2 | 첫 RequestSpawnAsync 후 SpawnNewActorDeferred (no warm) | ~50-200 ms (Soft Class 로드 + CDO + Asset members) | TBD |
| 2 | WarmUpPool(64) 후 RequestSpawnAsync (Acquire from pool) | ~0.05 ms (TMap Find + Activate) | TBD |
| 2 | **비율** | ~1000~4000× 단축 | TBD |
| 3 | Bundle PreLoad 없이 첫 spawn (Cooked Shipping) | ~200~500 ms ([[sources/ue-ref-11-assetloadingpolicy]] §2.1 4단 히칭) | TBD |
| 3 | PreloadActorClasses 후 spawn | ~5-10 ms (CDO 만, asset 메모리 상주) | TBD |
| 3 | **비율** | ~20~100× 단축 | TBD |
| 4 | 50 NPC / Significance OFF — 매 frame 비용 | ~16 ms (전부 60Hz Tick + AnimGraph) | TBD |
| 4 | 50 NPC / Significance ON (URO + Visibility 결합) | ~3-5 ms (vault [[synthesis/character-many-npc-5-fold-optimization]] §4 표 — 50~70% 감소) | TBD |
| 4 | **비율** | ~3~5× 단축 | TBD |

### 2.2 측정 환경

| 항목 | 값 |
| -- | -- |
| 빌드 | **Development** 또는 **Shipping** (Cooked) — vault [[sources/ue-ref-11-assetloadingpolicy]] §1.2 함정: Editor PIE 잘 동작 → Cooked 히칭 |
| 프로파일링 | `stat unit` / `stat game` / `stat startfile` → `stat stopfile` → Frontend |
| 측정 도구 | `FPlatformTime::Seconds()` + `UE_LOG` (간단) 또는 Unreal Insights (정밀) |
| NPC 액터 | `AMCPooledActor` 자손 BP — 동일 메시 / 동일 AnimBP / 다양한 spawn 위치 |
| 카메라 | 단일 player camera (다중 ViewPoints 미사용 — 첫 검증) |

## 3. 측정 절차 (단계별) 🟡

### 3.1 측정 1 — TActorIterator vs GetActorsInRadius

**시나리오**: 200 NPC spawn 후 매 frame 반경 1500cm 쿼리 측정.

```cpp
// A. Naive — TActorIterator (vault 금지 패턴, 비교용)
double Start = FPlatformTime::Seconds();
TArray<AActor*> Naive;
for (TActorIterator<AMCPooledActor> It(World); It; ++It)
{
    AActor* A = *It;
    if (FVector::Dist(A->GetActorLocation(), Center) <= 1500.f)
    {
        Naive.Add(A);
    }
}
double NaiveMs = (FPlatformTime::Seconds() - Start) * 1000.0;

// B. Vault — TOctree2 (GetActorsInRadius)
Start = FPlatformTime::Seconds();
TArray<AActor*> Octree;
Spawner->GetActorsInRadius(Center, 1500.f, Octree);
double OctreeMs = (FPlatformTime::Seconds() - Start) * 1000.0;

UE_LOG(LogMCAsset, Display, TEXT("[H1.1] Naive=%.3fms (N=%d) / Octree=%.3fms (N=%d) / 비율=%.1f×"),
    NaiveMs, Naive.Num(), OctreeMs, Octree.Num(), NaiveMs / OctreeMs);
```

기대 — Naive ~5 ms, Octree ~0.1 ms, 비율 ~50×.

### 3.2 측정 2 — WarmUpPool 효과

**시나리오**: 동일 클래스 64 spawn 비교 — WarmUp 한 풀 vs no warm.

```cpp
// A. No warm — 첫 64 spawn
double Start = FPlatformTime::Seconds();
for (int32 i = 0; i < 64; ++i)
{
    Spawner->RequestSpawnAsync(BulletClass, GetRandomTransform(), OnSpawned, OnFailed);
}
double NoWarmMs = (FPlatformTime::Seconds() - Start) * 1000.0;

// B. Warm — Subsystem Initialize 직후 WarmUpPool(64) → 그 다음 64 spawn
Spawner->WarmUpPool(BulletClass, 64);
Start = FPlatformTime::Seconds();
for (int32 i = 0; i < 64; ++i)
{
    Spawner->RequestSpawnAsync(BulletClass, GetRandomTransform(), OnSpawned, OnFailed);
}
double WarmMs = (FPlatformTime::Seconds() - Start) * 1000.0;
```

기대 — No warm ~3000-12000 ms (히칭 누적), Warm ~3-6 ms (Pool Acquire).

### 3.3 측정 3 — Bundle PreLoad 효과 (Cooked)

**시나리오** (Cooked Shipping):

```cpp
// A. No preload — GameMode::BeginPlay 직후 첫 spawn (가장 최악 case)
double Start = FPlatformTime::Seconds();
Spawner->RequestSpawnAsync(EnemyClass, T, OnSpawned, OnFailed);
double NoPreloadMs = (FPlatformTime::Seconds() - Start) * 1000.0;
// 비동기 — OnSpawned 가 실제 spawn 완료. 시간은 콜백 ms 측정.

// B. Preload — GameMode::BeginPlay 안 PreloadActorClasses 호출 + LoadingScreen 종료 후 첫 spawn
// (LoadingScreen 안에서 Bundle 로드 완료 가정)
Start = FPlatformTime::Seconds();
Spawner->RequestSpawnAsync(EnemyClass, T, OnSpawned, OnFailed);
double PreloadedMs = (FPlatformTime::Seconds() - Start) * 1000.0;
```

기대 — Cooked Shipping 에서 No preload ~200-500 ms, Preloaded ~5-10 ms.

> 🚨 vault [[sources/ue-ref-11-assetloadingpolicy]] §1.2 함정: **Editor PIE 에서는 측정 X (메모리 상주로 0 ms)**. Cooked Shipping 빌드 필수.

### 3.4 측정 4 — Significance ON/OFF (50 NPC)

**시나리오**: 50 NPC spawn 후 `stat unit` 측정.

| 환경 | bEnableSignificance | URO | Visibility | 매 frame Game thread |
| -- | -- | -- | -- | -- |
| 베이스라인 | false | false | false | ~16 ms |
| Significance only | true | false | false | ~10-12 ms (멀리 액터 Tick OFF) |
| Vault 표준 (3축 누적) | true | true | true | ~3-5 ms (50-70% 감소) |

vault [[synthesis/character-many-npc-5-fold-optimization]] §4 표 인용.

## 4. 함정 / 열린 질문 🟡

- [ ] **🔴 Editor PIE 측정의 함정** — vault §1.2 — PIE 가 어셋 메모리 상주로 0 ms → Cooked Shipping 빌드 의무
- [ ] **🟡 측정 도구 정확도** — `FPlatformTime::Seconds()` (저비용 / ms 단위) vs Unreal Insights (정밀 / Trace 오버헤드)
- [ ] **🟡 Variance** — 단일 측정 vs N 반복 평균 ± 표준편차 (`stat startfile` × 10)
- [ ] **🔴 NPC 디자인 의존** — 다른 메시 / 다른 AnimBP / 다른 컴포넌트 셋업 시 결과 변동 큼
- [ ] **🔴 카메라 위치 의존** — Significance score 가 거리 기반 — viewer 가 시나리오 중심에 가까이 있을 때만 ON/OFF 차이 큼
- [ ] **🟡 캐시 효과** — 같은 측정 반복 시 OS 파일 캐시 / GPU 메모리 캐시로 후속 측정이 더 빠름. 첫 측정만 의미
- [ ] **🔴 PSO Precache 결합** — vault [[concepts/PSO-Precache]] — `r.PSOPrecache=1` 활성 시 첫 spawn 의 PSO 컴파일 ms 변동

## 5. 측정 후 가설 검증 매트릭스 (실측 후 갱신) 🔴

| H1 sub-가설 | 예상 비율 | 실측 비율 | tier |
| -- | -- | -- | -- |
| H1.1 Octree vs Iterator | ~50× | TBD | 🔴 |
| H1.2 WarmUp vs no warm | ~1000× | TBD | 🔴 |
| H1.3 Bundle vs no preload | ~50× | TBD | 🔴 |
| H1.4 Significance 누적 | ~3-5× | TBD | 🔴 |

→ 실측 후 본 페이지 갱신. 결과가 예상 ± 30% 안 — H1 검증 ✅. 큰 편차 — vault 패턴의 *실제 효과* 가 다르거나 측정 노이즈.

## 6. ⭐⭐ 신뢰도 등급 가능성

vault [[sources/ue-measure-readme]] 의 신뢰도 정의:
- ⭐ = 단일 세션 자기 비교
- ⭐⭐ = 같은 Claude **다른 컨텍스트** vault 공유 (KMCProject vs 외부 에이전트)

본 측정이 ⭐⭐ 도달 조건:
1. 같은 vault 를 본 다른 세션의 에이전트가 같은 결과 도출
2. KMCProject 환경 외 *다른 UE 5.7.4 프로젝트* 에서 같은 측정
3. vault summary H1 페이지에 cross-link 등재

→ 본 페이지가 ⭐⭐ 데이터의 *2 번째 사례* 가 될 가능성 ([[sources/ue-measure-instancedsubobject-2026-05-12]] 가 1번째).

## 7. Cross-link

### Sources

- [[sources/ue-measure-readme]] (측정 방법론 + 신뢰도 정의)
- [[sources/ue-measure-summary]] (H1 가설 추적)
- [[sources/ue-measure-instancedsubobject-2026-05-12]] (⭐⭐ 첫 사례 — 패턴 모범)
- [[sources/ue-spatialpartition-toctree2]] (§2.4 O(log N + K) 인용)
- [[sources/ue-significance-skill]] (§5 typedef + §6 함정)
- [[sources/ue-ref-11-assetloadingpolicy]] (§1.2 PIE 함정 + §2.6 4단)
- [[sources/ue-ref-09-globaliteratorpolicy]] (TActorIterator 금지 — 본 측정의 *왜* )
- [[sources/ue-ref-07-profilingscopeRule]] (TRACE 도구 패턴)

### Entities

- [[entities/AActor]] · [[entities/USignificanceManager]]

### Concepts

- [[concepts/Global-Iterator-Avoidance]] (본 측정의 핵심 가설)
- [[concepts/Asset-Loading-Policy]] (Bundle PreLoad)
- [[concepts/Asset-Optimization-Policy]] (Significance 5축)
- [[concepts/Profiling-Scope-Rule]]
- [[concepts/Cooked-vs-Uncooked]] (측정 환경 분기)

### Related synthesis

- [[synthesis/mc-actor-spawn-subsystem-implementation]] (측정 대상 — 본 페이지가 그 §9.2 측정 항목의 정밀 검증)
- [[synthesis/character-many-npc-5-fold-optimization]] (Significance 누적 5축 — 측정 4 의 근거)
- [[synthesis/spawnactor-hitching-4-step-pattern]] (측정 3 의 근거 — Cooked 4단 히칭)
- [[synthesis/actor-pool-reset-pattern]] §5 Pool Subsystem (측정 2 의 근거)
- [[synthesis/toctree2-worldpartition-pair-pattern]] (측정 1 의 근거 — O(log N + K) 페어)

## 8. 후속 (실측 후)

- [ ] 사용자 PIE / Cooked 빌드 측정 결과 수집 (4 축 × N 반복)
- [ ] 본 페이지 §2.1 표의 실측 컬럼 갱신
- [ ] §5 가설 검증 매트릭스 결과 갱신
- [ ] §6 ⭐⭐ 신뢰도 도달 검증 — 다른 에이전트 / 다른 프로젝트 재현
- [ ] vault [[sources/ue-measure-summary]] 의 H1 추적에 본 페이지 등록
- [ ] *별도 raw measurement source* (`sources/ue-measure-mcactorspawn-h1-2026-05-XX`) 작성 — 본 synthesis 가 그것을 인용 (해석)

## 9. 3-tier 신뢰도

| 영역 | tier | 근거 |
| -- | -- | -- |
| §1 4 축 측정 항목 | 🟢 | vault 측정 방법론 + 본 Subsystem 구조 |
| §2.1 예상 값 | 🟡 | 일반 UE 5.x 지식 + vault 패턴 비용 외삽 |
| §2.2 측정 환경 | 🟢 | vault §1.2 Cooked 의무 |
| §3 측정 절차 (코드) | 🟢 | 일반 UE 측정 패턴 + KMCProject API |
| §4 함정 매트릭스 | 🟡 (🔴 Cooked 의무는 vault 직접) | |
| §5 가설 검증 | 🔴 | **실측 미완료** — 사용자 PIE 후 갱신 |
| §6 ⭐⭐ 가능성 | 🟡 | vault 신뢰도 정의 인용 + 본 케이스 외삽 |
