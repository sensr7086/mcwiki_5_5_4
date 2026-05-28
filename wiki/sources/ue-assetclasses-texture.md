---
type: source
title: "UE AssetClasses — Texture sub-skill"
slug: ue-assetclasses-texture
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Texture.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UTexture]]"
related_concepts:
  - "[[concepts/BulkData]]"
tags: [ue, asset, rendering]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Texture sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Texture.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UTexture (2,174) + UTexture2D + UTextureCube + UTextureRenderTarget2D + UVolumeTexture. CompressionSettings 10 종 + TextureGroup 11 종 + MipGenSettings 8 종 + 5.x VirtualTexture / RVT.

## 2. Key claims

- CompressionSettings 10 종: Default (BC1/BC3) / NormalMap (BC5) / Masks / Grayscale / HDR (BC6H) / UI / DistanceFieldFont / EditorIcon / Alpha / DisplacementMap.
- TextureGroup 11 종: World / WorldNormalMap / Character / UI / Lightmap / RenderTarget / Cinematic / etc — LOD bias + streaming priority.
- MipGenSettings 8 종: FromTextureGroup / Sharpen0~10 / NoMipmaps / SimpleAverage / etc.
- Streaming: 자동 (Texture Streaming Pool) 또는 bForceMipLevelsToBeResident.
- 5.x VirtualTexture (VT): 큰 텍스처 (10K+) 를 tile 단위 stream. 메모리 ↓ GPU ↑.
- 5.x RuntimeVirtualTexture (RVT): Material 결과를 텍스처로 캐싱 — Decal / Foliage 색조 합성.
- BulkData ([[concepts/BulkData]]): mip pixel data 가 lazy load. WITH_EDITORONLY_DATA source raw.

## 3. Open questions

- [ ] VT vs Texture Streaming 결정 트리
- [ ] RVT update 빈도 / 메모리 비용
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 2
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 4
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 6

**주요 시그니처 변경**:
- `├── UTexture2D (397 — 가장 흔함, 일반 2D) → └── UTexture (2,174 lines — 모든 Texture 베이스)`
- `EPixelFormat GetPixelFormat(uint32 LayerIndex = 0u) const;   // Texture2D.h:158 → int32 GetSizeX() const;            // Texture2D.h:152`

**5.5.4 표현 (5.7.4 에 없음)**:
- `├── UTexture2D (388 — 가장 흔함, 일반 2D)`
- `int32 GetSizeY() const;            // Texture2D.h:153`
- `int32 GetNumMips() const;          // Texture2D.h:154`
- `EPixelFormat GetPixelFormat(uint32 LayerIndex = 0u) const;   // Texture2D.h:155`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Texture.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Texture.md]]

### Body Reconciliation (2026-05-28 — promoted)

- 자동 substitution + §X 외 본문 grep 검토 완료
- **본문 정합 OK**: GetPixelFormat 본문 잔존 없음 (§X cite 만, false positive)
- 정합 후 tier: **🟢 pass-body-reconciled** (promoted from partial-needs-manual-review)
