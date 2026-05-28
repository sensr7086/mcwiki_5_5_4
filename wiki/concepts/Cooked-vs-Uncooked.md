---
type: concept
title: "Cooked vs Uncooked Build"
aliases: [Cooked, Uncooked, Editor Build, Shipping Build]
sources:
  - "[[sources/ue-assetclasses-skill]]"
related_concepts:
  - "[[concepts/Asset-Lifecycle]]"
  - "[[concepts/BulkData]]"
tags: [ue, runtime, asset, build]
last_updated: 2026-05-09
---

# Cooked vs Uncooked Build

## 1. 정의 (한 줄)

Editor / PIE = Uncooked (raw 자산 + Editor 메타 + DDC 사용), Shipping / Test / Development packaged = Cooked (플랫폼 변환된 자산만 + DDC 의존 X). 둘의 동작이 미묘하게 다른 것이 LLM Wiki 가 잡아주기 어려운 영역 [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]].

## 2. 자세히

| 측면 | Editor / PIE (Uncooked) | Cooked Build |
| -- | -- | -- |
| 자산 형식 | `.uasset` raw + WITH_EDITORONLY_DATA | 플랫폼 변환 (compressed Texture, compiled Shader, built Mesh) |
| PostLoad fixup | 활성 (마이그레이션, default 갱신) | 대부분 skip |
| Shader 컴파일 | 동적 (필요 시 stall) | 빌드 시점 + DDC 사전 cook |
| ConstructorHelpers::FObjectFinder | 작동 (느리지만) | 작동 안 할 수 있음 (파일 경로 변경) |
| `LoadObject<T>()` 동기 호출 | 작동 (디스크 read) | 작동하지만 큰 hitch |
| `bForceMipLevelsToBeResident` | 디스크에 raw mip 보유 | streaming pool 의존 |

## 3. 변형 / 사례 / 응용

- **검증 의무**: 모든 게임 코드는 Cooked Build (Development) 의 `stat unit` 으로 검증해야 함. Editor PIE 의 동작 ≠ Cooked. [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]]
- **WITH_EDITOR / WITH_EDITORONLY_DATA 가드**: Editor 전용 코드는 가드 + 4 단 분리 ([[raw/ue-wiki-llm/references/05_EditorOnlyIndex.md]]).
- **자주 발견되는 차이**:
  - Editor 에서는 spawn 빠른데 Cooked 에서 큰 hitch (자산 로드 모두 동기) → [[concepts/Asset-Loading-Policy]] PreLoad 표준
  - Editor 에서는 정상 표시되는데 Cooked 에서 mesh 깨짐 (Cook 누락 / DDC 손상)
  - Editor 에서만 Construction Script 호출 (런타임 OnConstruction 과 분기)

## 4. 관련 entity

- [[entities/UPackage]] · [[entities/UStaticMesh]] · [[entities/UTexture]]

## 5. 열린 질문

- [ ] DDC 손상 진단 패턴
- [ ] Cooked Build 에서만 발생하는 흔한 crash 카탈로그
