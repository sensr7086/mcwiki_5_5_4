---
type: source
title: "UE UMG — StandardWidgets sub-skill"
slug: ue-umg-standardwidgets
source_path: raw/ue-wiki-llm/skills/UMG/references/StandardWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, umg, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE UMG — StandardWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/StandardWidgets.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

표준 BP 위젯 — UButton + UImage + UCheckBox + UTextBlock + UProgressBar + URichTextBlock + UComboBoxString.

## 2. Key claims

- UButton: 클릭 가능. SButton wrapping. OnClicked / OnPressed / OnReleased delegate.
- UImage: 이미지 표시. SetBrushFromTexture / SetBrushFromMaterial.
- UCheckBox: 체크 토글. OnCheckStateChanged delegate.
- UTextBlock: 단순 텍스트. SetText(FText).
- URichTextBlock: 리치 텍스트 (마크업). DataTable 기반 styles.
- UProgressBar: 진행률 (0~1). SetPercent.
- UComboBoxString: 문자열 드롭다운. AddOption / SetSelectedOption / OnSelectionChanged.
- 모두 [[entities/UWidget]] 자손 — 내부 TSharedRef<SWidget> wrap.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
