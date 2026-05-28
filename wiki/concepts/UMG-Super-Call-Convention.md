---
type: concept
title: "UMG Super 호출 규약"
aliases: [UMG Super Call, NativeConstruct Super]
sources:
  - "[[sources/ue-umg-skill]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, umg, ui, policy]
last_updated: 2026-05-09
---

# UMG Super 호출 규약

## 1. 정의 (한 줄)

[[entities/UUserWidget]] 의 NativeConstruct / NativePreConstruct → Super FIRST, NativeDestruct → Super LAST. 위반 시 Slate Invalidation 깨짐.

## 2. 자세히

```cpp
void UMyUserWidget::NativeConstruct()
{
    Super::NativeConstruct();  // ← FIRST
    // 자식 위젯 binding / delegate 등록
}

void UMyUserWidget::NativePreConstruct()
{
    Super::NativePreConstruct();  // ← FIRST
    // Editor 미리 보기 셋업
}

void UMyUserWidget::NativeDestruct()
{
    // delegate 해제 / 캐싱 해제
    Super::NativeDestruct();  // ← LAST
}
```

전체 override 카탈로그는 [[raw/ue-wiki-llm/references/04_OverrideIndex.md]].

## 3. 변형 / 사례 / 응용

- Construct 흐름: UWidget::RebuildWidget → SWidget 트리 생성 → NativeConstruct 호출 → BP Construct event.
- 위반 결과: Slate 의 Invalidation 시스템이 SWidget 등록을 못 봄 → 화면에 안 그려지거나 입력 차단 등.
- 6 대 정책 ([[concepts/Component-Policies-6]]) 의 UMG 적용 — UWidget 자손도 동일 패턴.

## 4. 관련 entity

- [[entities/UUserWidget]] · [[entities/UWidget]]

## 5. 열린 질문

- [ ] PreConstruct 안에서 외부 리소스 접근의 함정 (Editor preview 시 World 없음)
