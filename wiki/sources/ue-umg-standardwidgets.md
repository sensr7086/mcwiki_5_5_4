---
type: source
title: "UE UMG — StandardWidgets sub-skill"
slug: ue-umg-standardwidgets
source_path: raw/ue-wiki-llm/skills/UMG/references/StandardWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, umg, ui]
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
