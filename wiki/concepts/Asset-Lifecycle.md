---
type: concept
title: "Asset Lifecycle (PostLoad / Cooking / DDC / BulkData)"
aliases: [Asset Lifecycle, PostLoad, Cooking]
sources:
  - "[[sources/ue-assetclasses-skill]]"
related_concepts:
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/BulkData]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, runtime, asset]
last_updated: 2026-05-09
---

# Asset Lifecycle

## 1. 정의 (한 줄)

`.uasset` 디스크 자산이 메모리에 올라와 사용되기까지의 4 단계 — PostLoad (deserialize 후 fixup) / Cooking (Editor → Cooked 변환) / DDC (Derived Data Cache) / [[concepts/BulkData]] (lazy load 큰 데이터).

## 2. 자세히

```
.uasset 디스크 (Editor)
    │
    ├─▶ LinkerLoad → FArchive deserialize → UObject 인스턴스
    ├─▶ PostLoad (Editor 만의 fixup, 마이그레이션, default 값 갱신)
    └─▶ 사용 (Editor)

Editor → Shipping 변환 시:
    ├─▶ Cook (Cooker process) — 플랫폼별 데이터 변환 (Texture compress, Shader compile, Mesh build)
    │   ├─▶ DDC 캐싱 (PSO / Compressed Texture / Mesh build result) — 다음 cook 가속
    │   └─▶ .upak / .iostore 로 묶음
    └─▶ Cooked .pak

런타임 (Cooked):
    ├─▶ pak 마운트 → linker
    ├─▶ Lazy BulkData (Mesh RenderData / Texture pixel / Sound PCM) 필요 시 디스크 → RAM
    └─▶ 사용 — PostLoad fixup 대부분 skip
```

## 3. 변형 / 사례 / 응용

- **WITH_EDITORONLY_DATA 가드**: Editor 만 사용하는 데이터 (raw pixel / source tris / LOD source) 는 가드 안 + Cooked 빌드에서 제외.
- **DerivedDataCache (DDC)**: Editor build 의 핵심 캐싱 — Compiled Shader / Compressed Texture / Mesh build result. Local DDC + Shared DDC (네트워크).
- **PostLoad 함정**: Editor 의 PostLoad 가 Cooked Build 에서 skip 되는 fixup 이 있을 수 있음 → Cooked 검증 의무. [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]]

## 4. 관련 entity

- [[entities/UStaticMesh]] · [[entities/USkeletalMesh]] · [[entities/UMaterial]] · [[entities/UTexture]]
- [[entities/UPackage]]

## 5. 열린 질문

- [ ] PSO Precache 의 Cook 단계 통합
- [ ] 5.x I/O Store (.utoc/.ucas) vs pak 의 차이
