---
type: source
title: "UE Slate — CommonWidgets sub-skill"
slug: ue-slate-commonwidgets
source_path: raw/ue-wiki-llm/skills/Slate/references/CommonWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
---

# UE Slate — CommonWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/CommonWidgets.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

일반 인터랙티브 위젯 — SButton + SCheckBox + SComboBox + SImage + SProgressBar + SSpinBox + STextBlock.

## 2. Key claims

- SCheckBox: 체크 토글 (3 상태 — Unchecked / Checked / Undetermined). CheckBoxStyle.
- SComboBox<T>: 드롭다운 — TArray<TSharedPtr<T>> 옵션. OnSelectionChanged delegate. OptionsSource attribute.
- SProgressBar: 진행률 (0~1). Percent attribute. FillImage / BackgroundImage.
- SSpinBox<T> (T = int / float): 숫자 입력 + ↑↓. Value attribute. MinValue / MaxValue / Delta.
