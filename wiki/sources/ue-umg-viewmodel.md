---
type: source
title: "UE UMG — ViewModel sub-skill (5.x MVVM)"
slug: ue-umg-viewmodel
source_path: raw/ue-wiki-llm/skills/UMG/references/ViewModel.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, umg, ui, mvvm]
---

# UE UMG — ViewModel sub-skill (5.x MVVM)

> Source: [[raw/ue-wiki-llm/skills/UMG/references/ViewModel.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

🆕 5.x MVVM Plugin — UMVVMViewModelBase + UMVVMView + Field Notify + Binding 자동화. UMG 의 데이터 바인딩 표준.

## 2. Key claims

- UMVVMViewModelBase: ViewModel 베이스. UPROPERTY(BlueprintReadWrite, Setter, FieldNotify) — 변경 시 View 자동 갱신.
- UMVVMView: UUserWidget 자손 — ViewModel 바인딩 컨테이너. Editor 의 MVVM 패널에서 binding 정의.
- Field Notify: UPROPERTY(FieldNotify) + Setter — 변경 시 자동 OnFieldValueChanged broadcast.
- Binding 종류: One-Way (ViewModel → View) / Two-Way (양방향) / One-Time (초기 1회).
- BP 노출: ViewModel 변수 / 함수 = BP 그래프에서 사용 가능.
- 분리 원칙: View (UMG widget) ↔ ViewModel (data + business logic) ↔ Model (외부 데이터).
- 사용처: 복잡한 UI (인벤토리 / 캐릭터 시트 / 설정 화면).
