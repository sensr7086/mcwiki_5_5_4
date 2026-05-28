---
type: concept
title: "Asset Loading Policy (5대)"
aliases: [Asset Loading, FStreamableManager, UAssetManager]
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, runtime, asset, policy]
last_updated: 2026-05-09
---

# Asset Loading Policy

## 1. 정의 (한 줄)

자산 (Mesh/Material/Texture/SoundCue/NiagaraSystem/Animation) 멤버의 Hard vs Soft 결정 + Constructor 안 어셋 로드 금지 + UAssetManager Primary Asset/Bundle + FStreamableManager 비동기 + Handle Pin/Release 의 5 대 정책. SpawnActor 히칭 회피의 핵심.

## 2. 자세히

| 단계 | 의무 |
| -- | -- |
| 1 | **Hard vs Soft 결정**: 항상 사용 = `TObjectPtr<T>` (Hard, 멤버 = Cooked 시 같이 로드). 가끔 / 큰 자산 = `TSoftObjectPtr<T>` (Soft, path 만 보유). |
| 2 | **Constructor 안 어셋 로드 금지**: `ConstructorHelpers::FObjectFinder<UStaticMesh>(...)` 는 Editor 만 의도된 패턴. 게임 모듈에서 사용 시 모든 Spawn 마다 동기 로드 → 큰 히칭. |
| 3 | **BeginPlay 동기 LoadObject 금지**: `LoadObject<UTexture2D>(...)` 는 디스크 read → 메인 스레드 차단. |
| 4 | **UAssetManager Primary Asset / Bundle**: 자주 사용 자산 = Project Settings 의 Primary Asset Type 등록 + Match Start `UAssetManager::PreloadPrimaryAssets(bLoadRecursive=true)` → 비동기 사전 로드 → 게임 시작 시 메모리 상주. |
| 5 | **FStreamableManager 비동기**: `UAssetManager::Get().GetStreamableManager().RequestAsyncLoad(SoftObjectPath, FStreamableDelegate::CreateLambda([](){...}))`. Handle Pin (TSharedPtr 보관) → 사용 후 Release. |

## 3. 변형 / 사례 / 응용

- **SpawnActor 히칭 4단**: (1) Class load (TSubclassOf vs TSoftClassPtr) → (2) BP CDO load → (3) BP 안 자산 멤버 (Mesh / Material) load → (4) Constructor 시 추가 자산 load. Cooked Build (Development) `stat unit` 으로 검증.
- **SpawnActorDeferred + FinishSpawning**: Property 셋업 후 BeginPlay — Spawn 직후 Property 변경하고 싶을 때.
- **Class slot Soft 결정**: AGameMode 의 DefaultPawnClass = TSoftClassPtr 권장 (Cooked Build 의 Class load 분리).

## 4. 관련 entity

- [[entities/UStaticMesh]] · [[entities/USkeletalMesh]] · [[entities/UMaterial]] · [[entities/UTexture]] · [[entities/UAnimMontage]]
- [[entities/UGameInstance]] (UAssetManager 진입점)

## 5. 열린 질문

- [ ] Bundle 의 비-recursive 로드 사용처
- [ ] FStreamableHandle 의 Pin / Release 패턴 — 메모리 leak 회피
