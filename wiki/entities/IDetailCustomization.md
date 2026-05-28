---
type: entity
title: "IDetailCustomization / IPropertyTypeCustomization"
aliases: [IDetailCustomization, IPropertyTypeCustomization, IDetailLayoutBuilder, IPropertyHandle]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, editor, ui]
last_updated: 2026-05-09
---

# IDetailCustomization / IPropertyTypeCustomization

## 요약

🛠 PropertyEditor 모듈의 핵심 — **디테일 패널 커스터마이징**. IDetailCustomization (UCLASS 단위) + IPropertyTypeCustomization (USTRUCT 단위) + IDetailLayoutBuilder (layout 정의 헬퍼) + IPropertyHandle (프로퍼티 핸들) + FPropertyEditorModule (등록 진입점).

## 관계

- 등록 진입점: FPropertyEditorModule::RegisterCustomClassLayout / RegisterCustomPropertyTypeLayout
- 컨텍스트: SDetailsView (Slate 위젯)
- Editor 빌드만

## 핵심 주장

- IDetailCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override — UCLASS 의 디테일 패널 layout 정의.
- IPropertyTypeCustomization::CustomizeHeader / CustomizeChildren — USTRUCT 의 헤더 + 자식 layout.
- IPropertyHandle 로 Property 동적 접근 — GetValue / SetValue / OnPropertyValueChanged delegate.
- 등록 시점: 모듈의 StartupModule() 안 + 해제는 ShutdownModule().
- BP 노드 (UFUNCTION(BlueprintCallable, meta=...)) 의 디테일 패널은 별도 — UFUNCTION 메타 specifier 로.

## 열린 질문

- [ ] IDetailCategoryBuilder 의 nested 카테고리 패턴
- [ ] IPropertyHandle 의 Array / Map 처리
