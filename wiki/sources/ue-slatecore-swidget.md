---
type: source
title: "UE SlateCore — SWidget sub-skill"
slug: ue-slatecore-swidget
source_path: raw/ue-wiki-llm/skills/SlateCore/references/SWidget.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-line-shifted  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/SWidget]]"
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, slate, ui, foundation, tooltip-tattribute, c3668-trap, kmcproject-pair]
citation_disclosure: "🟢 raw verified · Cycle 5p+4 enrich (§5 SetToolTipText TAttribute pull 모델 + Trap C3668 일반화)"
---

# UE SlateCore — SWidget sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/SWidget.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

[[entities/SWidget]] 베이스 디테일 — SLATE_BEGIN_ARGS + Construct + OnPaint + ComputeDesiredSize + ArrangeChildren + SLATE_NEW + SAssignNew + SCompoundWidget vs SLeafWidget. **§5 (Cycle 5p+4 신규)** — SetToolTipText TAttribute pull 모델 + C3668 잘못된 virtual override 함정 일반화.

## 2. Key claims

- SWidget abstract — 직접 인스턴스화 X. SCompoundWidget (자식 보유) 또는 SLeafWidget (자식 X) 자손 작성.
- SLATE_BEGIN_ARGS / SLATE_END_ARGS 매크로 + FArguments struct — 생성자 옵션.
- Construct(const FArguments& InArgs): Slate 매크로 SNew/SAssignNew 호출 시 진입점.
- SNew(SButton) 매크로: TSharedRef<SButton> 반환. .OnClicked / .Content() 로 chain.
- SAssignNew(MyButton, SButton): 멤버 변수에 ref 할당 + Construct.
- 4 핵심 virtual: OnPaint / ComputeDesiredSize / OnArrangeChildren / 입력 콜백.
- **§5 (Cycle 5p+4)** — `SetToolTipText(TAttribute<FText>&)` 표준 dynamic binding 패턴 — getter virtual 부재, TAttribute pull 모델.

## 3. Quotations

> "SWidget property 동적 바인딩은 거의 모든 attribute (Visibility/Text/Enabled/ToolTipText 등) 가 **Setter + TAttribute** 패턴을 따른다. getter 가 widget 멤버 함수가 아닌 callback (lambda 또는 함수 포인터) 형태로 widget 외부에 위임된다."

## 4. Open questions

- [ ] OnFocusReceived / OnFocusLost — focus group 차이
- [ ] Slate framework 안 cached invalidation cycle 의 최적 invalidate timing

## 5. ⭐⭐⭐ SetToolTipText TAttribute Dynamic Binding 표준 패턴 — Cycle 5p+4 신규 (C3668 Trap 일반화)

> **Cycle 5p+4 enrich 트리거**: KMCProject MCComboEditor Phase 4 마무리 작업 중 발견된 C3668 빌드 에러 (Trap 50). `virtual FText GetToolTipText() const override` 가정 → Engine 권위 부재 → 컴파일 실패. 본 §5 는 일반 패턴 + 함정 회피 매트릭스.
>
> **vault scope policy** ([[00_meta/08_VaultScopePolicy]]): 본 §5 는 **UE 일반 영역** (96% scope). KMCProject Trap 50 은 inline case study 으로 §5.5 안 참조.

### 5.1 Engine 권위 — `SetToolTipText` 시그니처 (UE 5.7.4)

→ Engine 본가: `Engine/Source/Runtime/SlateCore/Public/Widgets/SWidget.h` L1317-L1320.

```cpp
// L1317 — TAttribute 받음 (dynamic, 매 hover 시 callback 호출)
SLATECORE_API void SetToolTipText(const TAttribute<FText>& ToolTipText);

// L1320 — FText 받음 (정적, 한 번 set 후 변경 X)
SLATECORE_API void SetToolTipText(const FText& InToolTipText);
```

⭐ **핵심**: `GetToolTipText` virtual 메서드는 **존재하지 않음**. Slate framework 는 TAttribute pull 모델 — 매 hover 시점에 lambda/callback 호출하여 동적 텍스트 build.

### 5.2 TAttribute pull 모델 — 동적 ToolTip 표준 패턴

```cpp
class SMyCustomWidget : public SCompoundWidget
{
public:
	void Construct(const FArguments& InArgs)
	{
		// ... 기존 ChildSlot setup ...

		// ⭐ Dynamic tooltip binding — TAttribute<FText>::CreateSP
		//   매 hover 시점에 BuildTooltipText() 호출 → 결과 텍스트 표시.
		//   CreateSP 는 TSharedPtr weak ref 보존 → widget destroy 시 자동 invalidate (lifetime safe).
		SetToolTipText(TAttribute<FText>::CreateSP(this, &SMyCustomWidget::BuildTooltipText));
	}

private:
	/** 일반 private const helper (virtual override 아님). Slate framework 호출은 TAttribute lambda 경유. */
	FText BuildTooltipText() const
	{
		// 매 hover 시점에 호출 — 동적 데이터 반영 (예: hover 위치 / 선택 상태 등).
		return FText::Format(LOCTEXT("TipFmt", "Current state: {0}"), FText::FromString(CurrentState));
	}

	FString CurrentState;
};
```

**Engine 권위 매트릭스**:
- `SlateCore/Public/Widgets/SWidget.h` L1317 — `SetToolTipText(const TAttribute<FText>&)`
- `Core/Public/Misc/Attribute.h` `TAttribute<T>::CreateSP(InUserObject, MethodPtr)` — Shared Ptr weak ref binding
- `Core/Public/Misc/Attribute.h` `TAttribute<T>::CreateLambda([](){})` — lambda binding (capture 가능)
- `Core/Public/Misc/Attribute.h` `TAttribute<T>::Create(StaticFuncPtr)` — static function pointer

### 5.3 ⚠ C3668 함정 — `virtual GetToolTipText` 잘못된 가정

**잘못된 패턴 (C3668 발생)**:
```cpp
class SMyCustomWidget : public SCompoundWidget
{
public:
	// ❌ Engine 권위 부재 — base class 에 GetToolTipText virtual 없음!
	virtual FText GetToolTipText() const override;
};
```

**빌드 에러**:
```
error C3668: 'SMyCustomWidget::GetToolTipText': 재정의 지정자 'override'가 있는 메서드가 기본 클래스 메서드를 재정의하지 않았습니다.
```

**원인 분석**:
- "setter 가 있으니 getter 도 있겠다" 라는 **잘못된 대칭 가정**
- Slate API 는 TAttribute pull 모델 — getter 가 widget 멤버 함수가 아닌 `TAttribute<>` callback 으로 동작
- C3668 = "override 지정자가 있지만 base class 에 매칭 virtual 부재" — Engine 권위 grep 시 명확 발견 가능

**vault 일반화 회피 패턴**:
1. **virtual override 추가 전 base class header grep 의무**:
   ```bash
   Grep "GetToolTipText|virtual" SlateCore/Public/Widgets/SWidget.h
   ```
2. **Slate widget property 동적 바인딩 = Setter + TAttribute 표준** — Visibility / Text / Enabled / ToolTipText 등 거의 모든 attribute 가 동일 구조
3. **C3668 발생 시 virtual 키워드 제거 가 90% 정답** (Engine 권위 부재)

### 5.4 동일 패턴 widget property 매트릭스 (TAttribute pull 모델)

| Property | Setter (TAttribute overload) | Helper 패턴 |
| -- | -- | -- |
| ToolTipText | `SetToolTipText(TAttribute<FText>)` L1317 | `FText BuildTooltipText() const` + `SetToolTipText(TAttribute::CreateSP(this, &Build))` |
| Visibility | `SetVisibility(TAttribute<EVisibility>)` | `EVisibility GetVisibility() const` + `SetVisibility(TAttribute::CreateSP(this, &GetVis))` |
| Enabled state | `SetEnabled(TAttribute<bool>)` | 동일 |
| Text (STextBlock) | `.Text(TAttribute<FText>)` SLATE_ATTRIBUTE | `.Text_Lambda([this]() { ... })` |
| Color/Opacity | `SetColorAndOpacity(TAttribute<FLinearColor>)` | 동일 |

⭐ **공통 패턴**: 모든 widget property setter 가 `TAttribute<T>` overload 를 노출 — dynamic binding 표준.

### 5.5 ⭐ Case Study: KMCProject MCComboEditor Trap 50 (Cycle 5p+4)

> **vault scope policy** ([[00_meta/08_VaultScopePolicy]]): KMCProject (mc-) 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강.

KMCProject `SMCComboTrackArea` Phase 4 마무리 Section Tooltip 구현 시:

**1차 시도 (실패, C3668)**:
```cpp
// SMCComboTrackArea.h (잘못된 가정)
virtual FText GetToolTipText() const override;

// SMCComboTrackArea.cpp
FText SMCComboTrackArea::GetToolTipText() const
{
    UMCComboSection* Section = HoveredSection.Get();
    return Section ? FText::FromString(Section->DisplayName.ToString()) : FText::GetEmpty();
}
```

**빌드 결과**: `error C3668: 'SMCComboTrackArea::GetToolTipText': 재정의 지정자 'override'가 있는 메서드가 기본 클래스 메서드를 재정의하지 않았습니다.`

**원인 분석 (Engine grep)**:
- `Grep "GetToolTipText" SlateCore/Public/Widgets/SWidget.h` → **부재 확인**
- `Grep "SetToolTipText" 동상` → L1317 `TAttribute<FText>` overload + L1320 `FText` overload **만 존재**

**2차 정정 (Engine 권위 정확)**:
```cpp
// SMCComboTrackArea.h (정정)
// (virtual override 제거)
FText BuildHoveredTooltipText() const;  // 일반 private const helper

// SMCComboTrackArea.cpp Construct
SetToolTipText(TAttribute<FText>::CreateSP(this, &SMCComboTrackArea::BuildHoveredTooltipText));
```

**결과**: 빌드 PASS. Slate framework 가 매 hover 시점에 `BuildHoveredTooltipText` 호출 → HoveredSection 통해 동적 멀티라인 텍스트 build.

→ KMCProject 사례 상세: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.9.7 + §5.9.8 + 함정 50.

### 5.6 OnMouseMove + HoveredSection 패턴 — Hover-aware Tooltip

동적 tooltip 의 핵심은 **hover 상태 정보** 가 widget 안에 저장되어야 한다는 점. OnMouseMove 안 hover detection 갱신:

```cpp
class SMyCustomWidget : public SCompoundWidget
{
	// ...
	virtual FReply OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
	{
		const FVector2D LocalPos = MyGeometry.AbsoluteToLocal(MouseEvent.GetScreenSpacePosition());

		// ⭐ Drag 분기 가드 — drag 중 hover 갱신 X (perf cost 0).
		if (DragMode == EMyDragMode::None)
		{
			HoveredItem = HitTestItem(LocalPos);
		}

		// ... 기존 drag 처리 ...
		return FReply::Handled();
	}

private:
	TWeakObjectPtr<UMyItem> HoveredItem;

	FText BuildTooltipText() const
	{
		UMyItem* Item = HoveredItem.Get();
		if (!Item) return FText::GetEmpty();
		// 동적 데이터 build
		return FText::Format(LOCTEXT("ItemFmt", "{0} — {1}"), Item->Name, FText::AsNumber(Item->Value));
	}
};
```

### 5.7 함정 카탈로그 (Cycle 5p+4 일반화)

| 함정 | 원인 | 회피 |
| -- | -- | -- |
| C3668 `virtual GetToolTipText() const override` | "setter 가 있으니 getter 도 있을 것" 잘못된 대칭 가정. Engine 권위 부재 | virtual override 추가 전 base class header grep 의무 + Setter + TAttribute 표준 패턴 채택 |
| Hover 상태 동기화 누락 | `OnMouseMove` 안 HoveredItem 갱신 안 함 → tooltip 정적 또는 빈 텍스트 | OnMouseMove 안 HitTest 결과 mutable/TWeakObjectPtr 멤버에 저장 |
| Drag 중 hover 갱신 polluton | drag 중 매 pixel HitTest → hover 변경 깜박임 + perf 낭비 | `if (DragMode == None)` 가드 — drag 중 hover 미갱신 |
| TAttribute lifetime | lambda capture `this` 시 widget destroy 후 dangling | `TAttribute::CreateSP(this, &Method)` 권장 — Shared Ptr weak ref 자동 invalidate |
| GetToolTipWidget 혼동 | `GetToolTipWidget()` 은 다른 virtual (TooltipForce 시점 호출, 별도 widget 반환) | TAttribute 표준 패턴 시 GetToolTipWidget override 불필요 |

## 6. Cross-link

### Engine 권위

- `Engine/Source/Runtime/SlateCore/Public/Widgets/SWidget.h` L1317-L1320 (`SetToolTipText` 두 overload + `GetToolTipText` virtual 부재 확인)
- `Engine/Source/Runtime/Core/Public/Misc/Attribute.h` (`TAttribute<T>::CreateSP / CreateLambda / Create`)
- `Engine/Source/Runtime/SlateCore/Public/Widgets/SCompoundWidget.h` (자식 보유 widget 베이스)
- `Engine/Source/Runtime/SlateCore/Public/Widgets/SLeafWidget.h` (자식 X widget 베이스)

### Parent / 페어 sub-skills

- Parent: [[sources/ue-slatecore-skill]]
- 페어 sub-skill: [[sources/ue-slatecore-input]] (OnMouseMove + Cursor) · [[sources/ue-slatecore-drawing]] (OnPaint) · [[sources/ue-slate-application]] (FSlateApplication)
- Phase II hub: [[sources/ue-slate-commonwidgets]] (STextBlock + TAttribute<FText> 미러 패턴)

### Concept

- [[concepts/Slate-Paint-Cycle]] · [[concepts/Slate-Invalidation]]

### ⭐ Case study (mc-, Cycle 5p+4 §5.5)

- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.9.7 + §5.9.8 (Phase 4 마무리 Section Tooltip + C3668 Trap 50 정정)
- [[synthesis/timeline-custom-slate-widget-pattern]] (Custom Timeline Slate Widget Sequencer-lite — Phase 4 일반화 reusable index)

### Governance (Cycle 5p+4)

- [[00_meta/08_VaultScopePolicy]] §3 — mc- 사례 → ue- reverse-link 의무 (본 §5.5)
- [[00_meta/03_EvaluatorRecipe]] §1.5 — Stage 2.X Engine Authority Verification (본 §5.1 + §5.5)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
