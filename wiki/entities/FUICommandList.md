---
type: entity
title: "FUICommandList / FUICommandInfo"
aliases: [FUICommandList, FUICommandInfo, TCommands, FInputBindingManager]
kind: model
sources:
  - "[[sources/ue-slate-skill]]"
tags: [ue, slate, editor, ui]
last_updated: 2026-05-09
---

# FUICommandList / FUICommandInfo

## 요약

🛠 단축키 + 메뉴 / 툴바 통합 — Commands 시스템. FUICommandList (per-context bindings) + FUICommandInfo (개별 명령) + TCommands<T> (Commands 등록 헬퍼). FMenuBuilder / FToolBarBuilder 와 같이 사용.

## 관계

- 협력: FMenuBuilder (메뉴 트리), FToolBarBuilder (툴바), [[entities/UToolMenus]] (5.x 모던)
- Editor 빌드만 (대부분)

## 핵심 주장

- TCommands 등록 패턴: `class FMyCommands : public TCommands<FMyCommands> { virtual void RegisterCommands() override; }` → UI_COMMAND 매크로.
- UI_COMMAND(MyCommand, "Label", "Tooltip", EUserInterfaceActionType::Button, FInputChord(EKeys::F)).
- FUICommandList::MapAction(MyCommand, FExecuteAction::CreateRaw(this, &FMyToolkit::OnMyCommand)).
- MenuBuilder.AddMenuEntry(Commands.MyCommand) — 메뉴에 Commands 추가.
- ToolBarBuilder.AddToolBarButton(Commands.MyCommand).
- 5.x UToolMenus 와 통합: FToolMenuEntry::InitToolBarButton(Commands.MyCommand).

## 열린 질문

- [ ] FInputBindingManager 의 사용자 단축키 customization
- [ ] FUICommandList 의 context 분기 (Asset Editor vs LevelEditor)
