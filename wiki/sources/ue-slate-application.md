---
type: source
title: "UE Slate — Application sub-skill"
slug: ue-slate-application
source_path: raw/ue-wiki-llm/skills/Slate/references/Application.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/SWidget]]"
tags: [ue, slate, ui]
---

# UE Slate — Application sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/Application.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

게임 런타임 공용 표준 위젯 — SButton + SImage + SBox + SBorder + STextBlock + SOverlay. SCompoundWidget 기반. 게임 + 에디터 양쪽에서 사용.

## 2. Key claims

- SButton: 클릭 가능 버튼. OnClicked / OnPressed / OnReleased delegate. ButtonStyle 매개.
- SImage: 텍스처 / 브러시 표시. Image / ColorAndOpacity attribute.
- SBox: padding / size override / fixed size 컨테이너.
- SBorder: 배경 + content. BorderImage / BorderBackgroundColor.
- STextBlock: 텍스트 표시. Text / Font / ColorAndOpacity / Justification.
- SOverlay: 자식들을 같은 위치에 (Z 순서). HUD / popup 표준.
- 게임 + 에디터 공통 — UMG 의 [[entities/UWidget]] wrapping 의 베이스.
