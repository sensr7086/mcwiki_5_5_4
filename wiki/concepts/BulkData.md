---
type: concept
title: "BulkData (lazy load)"
aliases: [BulkData, FBulkData, FByteBulkData]
sources:
  - "[[sources/ue-assetclasses-skill]]"
related_concepts:
  - "[[concepts/Asset-Lifecycle]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, runtime, asset]
last_updated: 2026-05-09
---

# BulkData (lazy load)

## 1. 정의 (한 줄)

`.uasset` 안의 큰 데이터 (Mesh vertex/index buffer / Texture pixel data / Sound PCM 등) 를 *별도 파일* 또는 *파일 끝* 에 저장하고 *필요 시점* 에 lazy load 하는 메커니즘. UPackage 의 일부지만 main payload 와 분리.

## 2. 자세히

- BulkData 는 `FBulkData` / `FByteBulkData` / `FFormatContainer` 등의 wrapper.
- Editor 빌드: BulkData 가 같은 `.uasset` 안에 또는 별도 `.ubulk` 파일.
- Cooked 빌드: 플랫폼별로 cooked + 같이 묶임 (`.upak` / `.iostore`).
- Streaming: Texture / SoundWave 의 BulkData 는 자동 streaming pool 에서 관리.

## 3. 변형 / 사례 / 응용

- **Texture pixel data**: Mip level 별로 분리. `ForceMipLevelsToBeResident(Seconds)` 로 강제 resident.
- **Mesh RenderData**: vertex buffer / index buffer / skin weight buffer 가 BulkData. LOD 별로 별도.
- **WITH_EDITORONLY_DATA 의 source data**: Editor 의 raw pixel / source tri / LOD source 는 EditorOnlyBulkData — Cooked 빌드 제외.
- **DerivedDataCache 통합**: BulkData 의 Cooked 결과 (Compressed Texture 등) 가 DDC 에 캐싱.

## 4. 관련 entity

- [[entities/UTexture]] · [[entities/UStaticMesh]] · [[entities/USkeletalMesh]] · [[entities/USoundBase]]
- [[entities/UPackage]]

## 5. 열린 질문

- [ ] 5.x I/O Store 의 BulkData chunking 동작
- [ ] BulkData 강제 unload 패턴 (저메모리 환경)
