---
type: source
title: "UE AssetClasses — Data sub-skill"
slug: ue-assetclasses-data
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Data.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, asset, data]
---

# UE AssetClasses — Data sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Data.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UDataAsset + UPrimaryDataAsset (Bundle 표준) + UDataTable (552) + UCurveTable (342) + UCurveFloat / UCurveLinearColor — 데이터 기반 디자인.

## 2. Key claims

- UDataAsset: 단순 데이터 컨테이너 (UPROPERTY 들). BP / C++ 양쪽.
- UPrimaryDataAsset: Bundle 패턴의 베이스. UAssetManager 와 통합 — Type:Name 식별 + Bundle 분리 (예: `Visual` / `Audio` / `Gameplay`).
- UDataTable: row 단위 USTRUCT 컬렉션. CSV / JSON import. RowName lookup 빠름.
- UCurveTable: 시간 + 레벨 곡선의 컬렉션.
- UCurveFloat / UCurveLinearColor: 단일 곡선. AnimMontage / AbilityCooldown / 색상 변환.
- Bundle 패턴: 자주 쓰는 Asset (능력 / 무기 / 캐릭터) = Primary Asset 으로 등록 → UAssetManager `PreloadPrimaryAssetClasses(Class, BundleName, bLoadRecursive)` Match Start. → [[concepts/Asset-Loading-Policy]]

## 3. Open questions

- [ ] UDataTable 의 BP 노출 vs C++ 직접 접근 결정
- [ ] PrimaryAsset Bundle 의 분리 표준 패턴
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 변경 0 / 추가 0 / 제거 0 — 단순 수치 또는 미세 변경만. 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Data.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Data.md]]
