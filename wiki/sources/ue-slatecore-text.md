---
type: source
title: "UE SlateCore — Text sub-skill"
slug: ue-slatecore-text
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Text.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui, text]
---

# UE SlateCore — Text sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Text.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

FText + FString + LOCTEXT/NSLOCTEXT + STextBlock + 다국어 + Localization + Rich Text Markup.

## 2. Key claims

- FText: localized 텍스트 (UI 표준). 절대 FString 으로 UI 표시 안 함.
- LOCTEXT 매크로: 단일 namespace. `LOCTEXT("MyKey", "My Default Text")`.
- NSLOCTEXT 매크로: 명시 namespace. `NSLOCTEXT("MyNS", "MyKey", "My Default Text")`.
- LOCTEXT_NAMESPACE / #undef LOCTEXT_NAMESPACE — 파일 단위 namespace 설정.
- FStringFormat / FText::Format — 다국어 안전 format. `FText::Format(LOCTEXT("Greeting", "Hello, {0}"), Args)`.
- RichTextMarkup: <Style.Bold>Bold</> 등 inline style. URichTextBlock 통합.
- Localization 데이터: .archive 파일 + Editor 의 Localization Dashboard.
- HarfBuzz: 텍스트 셰이핑 (Arabic / Hebrew / etc — RTL).
- FreeType: 폰트 렌더링.
