---
type: source
title: "UE AssetClasses — Audio sub-skill"
slug: ue-assetclasses-audio
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Audio.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/USoundBase]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, asset, audio]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Audio sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Audio.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

[[entities/USoundBase]] (358) + USoundCue (367) + USoundWave (1,787) + USoundClass + USoundConcurrency + USoundMix + USoundAttenuation + 5.x MetaSounds.

## 2. Sub-sub-skills

- [[sources/ue-assetclasses-audio-metasound]] — 5.x MetaSound deep (UMetaSoundSource + UMetaSoundPatch + DSP graph)

## 3. Key claims

- USoundBase: 베이스. USoundCue / USoundWave / UMetaSoundSource 의 부모.
- USoundCue: 노드 그래프 (Random / Concatenator / Doppler / Modulator).
- USoundWave: 압축 PCM. BulkData. 5.x Streaming SoundWave.
- USoundClass: 그룹 (Volume / Pitch).
- USoundConcurrency: ResolutionRule 5 종 — 다수 NPC 표준 ([[concepts/Asset-Optimization-Policy]] §4).
- USoundMix: 효과 셋 — 일시적 활성.
- USoundAttenuation: 거리 / 방향 / Spatial.
- 5.x MetaSounds: SoundCue 후속 — graph + audio-rate + 동적 인스턴싱.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 2
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 1
- 수치 변경: 12

**주요 시그니처 변경**:
- `├── USoundWave (1,822 — 단일 음원 데이터 + Streaming + Compression) → └── USoundBase (358 — 베이스, IInterface_AssetUserData)`

**5.5.4 표현 (5.7.4 에 없음)**:
- `├── USoundCue (367 — 노드 그래프 + 분기 / 랜덤 / Mix)`
- `├── USoundWave (1,787 — 단일 음원 데이터 + Streaming + Compression)`

**5.7.4 표현 (5.5.4 에 없음)**:
- `public IAudioPropertiesSheetAssetUserInterface,`

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Audio.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Audio.md]]

### Body Reconciliation (2026-05-28 — promoted)

- 자동 substitution + §X 외 본문 grep 검토 완료
- **본문 정합 OK**: IAudioPropertiesSheet 본문 잔존 없음 (§X cite 만, false positive)
- 정합 후 tier: **🟢 pass-body-reconciled** (promoted from partial-needs-manual-review)
