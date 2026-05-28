---
type: source
title: "UE Slate — EditorApplication sub-skill"
slug: ue-slate-editorapplication
source_path: raw/ue-wiki-llm/skills/Slate/references/EditorApplication.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, editor]
---

# UE Slate — EditorApplication sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/EditorApplication.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 SDockTab + SWindow + 에디터 전용 위젯 묶음 — Slate 의 Application 측면 (게임 SApplication 과 분리).

## 2. Key claims

- SWindow: Slate의 OS-level 윈도우. ClientSize / Title / Style. 게임 메인 vs 모달 dialog.
- SDockTab: Docking 시스템의 탭 (Docking sub-skill 페어).
- 에디터 전용 위젯들: SListPanel / SSplitter / SSeparator / SThrobber / 등 — 에디터 UI 의 표준 컴포넌트.
- FSlateApplication::Get().AddWindow / AddModalWindow — 새 윈도우 등록.
- Editor 빌드만 — `#if WITH_EDITOR` 가드.
