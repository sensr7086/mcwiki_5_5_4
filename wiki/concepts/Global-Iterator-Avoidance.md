---
type: concept
title: "Global Iterator 회피 정책"
aliases: [TActorIterator, TObjectIterator, Global Iterator Policy]
sources:
  - "[[sources/ue-subsystem-skill]]"
related_concepts:
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, runtime, policy, optimization]
last_updated: 2026-05-09
---

# Global Iterator 회피 정책

## 1. 정의 (한 줄)

`TActorIterator<T>` / `TObjectIterator<T>` / `TObjectRange<T>` / `TActorRange<T>` **사용 금지** — 매 호출 = O(N) 의 World/UObject 트리 순회. 표준 대안 = [[entities/USubsystem]] 안 등록 list (등록 1회 + 검색 0). 자세한 코드 = [[raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md]].

## 2. 자세히

함정 시나리오:
```cpp
// BAD — Tick 마다 N개 Actor 순회 (O(N) 매 frame)
void AMyManager::Tick(float Dt)
{
    for (TActorIterator<AMyEnemy> It(GetWorld()); It; ++It)
    {
        It->DoSomething();  // 100 NPC + 60fps = 6000 호출/초
    }
}
```

표준 대안:
```cpp
// GOOD — 등록 패턴
void AMyEnemy::BeginPlay()
{
    if (UMyEnemyManager* Manager = GetGameInstance()->GetSubsystem<UMyEnemyManager>())
    {
        Manager->Register(this);
    }
}

void AMyEnemy::EndPlay(...) { Manager->Unregister(this); }

void UMyEnemyManager::Tick(float Dt) { for (auto* E : RegisteredEnemies) E->DoSomething(); }
```

## 3. 변형 / 사례 / 응용

- 예외: Editor 의 1 회성 도구 (FEditorUtils 안), 게임 시작 시 1 회 검색 — OK.
- AssetRegistry 도 대안: [[entities/IAssetTools]]::GetAssetsByClass — 자산 측면.
- Significance Manager 도 등록 패턴 — 다수 NPC 환경 표준.
- BP 의 GetAllActorsOfClass 도 동일 함정 — Tick / 콜백 안 사용 금지.

## 4. 관련 entity

- [[entities/USubsystem]] · [[entities/USignificanceManager]] · [[entities/IAssetTools]]

## 5. 열린 질문

- [ ] FActorIterator vs TActorIterator 차이
- [ ] WorldPartition 의 Cell 단위 iteration 표준
