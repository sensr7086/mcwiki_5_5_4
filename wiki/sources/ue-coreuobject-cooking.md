---
type: source
title: "UE CoreUObject — Cooking sub-skill"
slug: ue-coreuobject-cooking
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Cooking.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
  - "[[entities/UPackage]]"
related_concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Lifecycle]]"
tags: [ue, build, foundation, coreuobject]
---

# UE CoreUObject — Cooking sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Cooking.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

🛠 Cooking — Editor 자산 → 플랫폼별 Cooked 자산 변환. NeedsLoadForServer / NeedsLoadForClient + IsEditorOnly + BeginCacheForCookedPlatformData + UObjectRedirector + Iterative Cook + CookOnTheFly.

## 2. Key claims

- NeedsLoadForServer / NeedsLoadForClient — UObject override. Cosmetic 데이터 (VFX / SFX) 는 Server 빌드에서 stripped.
- IsEditorOnly — Editor 만 사용. Cooked 빌드 stripped.
- BeginCacheForCookedPlatformData(TargetPlatform) — Cook 시 플랫폼별 데이터 빌드. Texture compression / Mesh build 등.
- UObjectRedirector — 자산 이동/리네임 시 옛 path → 새 path 의 redirect. 자동 cleanup 기능.
- Iterative Cook — 변경된 자산만 cook. Full cook 의 시간 절약.
- CookOnTheFly — 디바이스에서 자산을 PC 의 Editor 로부터 streaming. 빠른 반복 개발.
- DDC (DerivedDataCache) 통합 — Cook 결과 캐싱. Local DDC + Shared DDC.

## 3. Quotations

> "Cook = Editor → 플랫폼별 변환 + DDC 캐싱 + Iterative 옵션."

## 4. Open questions

- [ ] CookOnTheFly 의 5.x 표준 셋업
- [ ] UObjectRedirector 의 자동 cleanup
