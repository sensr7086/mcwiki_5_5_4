---
type: source
title: "UE SlateCore — Text sub-skill"
slug: ue-slatecore-text
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Text.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui, text]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
