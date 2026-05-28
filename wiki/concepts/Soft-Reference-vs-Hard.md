---
type: concept
title: "Soft Reference vs Hard Reference"
aliases: [TSoftObjectPtr, TObjectPtr, Soft Reference, Hard Reference]
sources:
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-components-skill]]"
related_concepts:
  - "[[concepts/Object-Handles]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, runtime, asset, policy]
last_updated: 2026-05-09
---

# Soft Reference vs Hard Reference

## 1. 정의 (한 줄)

자산 (Mesh / Material / Texture 등) 멤버를 `TObjectPtr<>` (Hard, 같이 로드) 또는 `TSoftObjectPtr<>` (Soft, path 만 보유) 중 어느 쪽으로 저장할지의 결정. 메모리 / 로드 시간 / 의존 그래프에 큰 영향.

## 2. 자세히

| 측면 | Hard (`TObjectPtr<T>`) | Soft (`TSoftObjectPtr<T>`) |
| -- | -- | -- |
| 디스크 보유 | 자산 path + 자산 자체 (cook 시 같이) | 자산 path 만 (lazy load) |
| 메모리 | 즉시 | path 만 |
| 액세스 | `Mesh->GetSomething()` 직접 | `Mesh.LoadSynchronous()` 또는 비동기 |
| 의존 그래프 | 부모가 로드되면 자손도 로드 | 끊어짐 — 명시적 load 필요 |
| GC | edge | 아님 (로드된 후에만) |

## 3. 변형 / 사례 / 응용

- **항상 사용 = Hard**: 캐릭터의 기본 mesh, 무기의 Material slot — 객체 lifetime 동안 항상.
- **가끔 / 큰 자산 = Soft**: 능력별 VFX (UNiagaraSystem), 팀별 색상 텍스처, 옵션 무기 — 필요 시점에만.
- **Class slots 도 동일**: `TSubclassOf<T>` (Hard, Class load 같이) vs `TSoftClassPtr<T>` (Soft, Class load 분리).
- **TArray<TSoftObjectPtr<>>** 의 흔한 사용: 능력 풀 / 무기 풀 — 일부만 활성화될 때 메모리 절약.

## 4. 관련 entity

- [[entities/UStaticMesh]] / [[entities/USkeletalMesh]] / [[entities/UMaterial]] / [[entities/UTexture]]

## 5. 열린 질문

- [ ] Soft → Hard 마이그레이션 (게임 진행에 따라 pin 후 다음 사용 위해 보존)
- [ ] Async load 후 Pin (TSharedPtr<FStreamableHandle>) 의 Release 시점
