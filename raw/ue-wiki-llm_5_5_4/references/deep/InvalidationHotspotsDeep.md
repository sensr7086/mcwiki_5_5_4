---
name: invalidation-hotspots-deep
description: UMG/Slate 위젯별 인밸리데이션 핫스팟 깊이 자료 — STextBlock / RichText / EditableText / ListView / Throbber / NativeOnPaint / TAttribute 람다 등 위젯별 다발 케이스 + 회피 전략.
---

# Invalidation Hotspots — Deep Reference (§2 위젯별 핫스팟)

> 본 문서는 [`06_InvalidationHotspots.md`](../06_InvalidationHotspots.md) 의 §2 깊이 자료. 메인 문서는 §0/§1 EInvalidateWidgetReason + §3 InvalidationBox + §4 ForceVolatile + §5 NativeTick + §6 setter 표 + §7 디버그 + §8 핵심 원칙. 본 reference 는 위젯별 hotspot 상세.

---

## 2. 위젯별 인밸리데이션 핫스팟

### 2.1 텍스트 위젯

#### `STextBlock` / `UTextBlock`

| 동작 | 발생 reason | 빈도 | 대안 |
|------|-------------|------|------|
| `SetText(FText)` (값 변경) | `Layout` (텍스트 폭 재계산) | 매번 변경 시 | `TSlateAttribute<FText, EInvalidateWidgetReason::Layout>` 자동화 |
| `SetColorAndOpacity(FSlateColor)` | `Paint` | 호버·강조 시 | TSlateAttribute / TAttribute lambda |
| `SetFont(FSlateFontInfo)` | `Layout` (폰트 메트릭 재측정) | 드뭄 — 한 번만 | 정적 사용 권장 |
| `SetJustification(ETextJustify::Type)` | `Layout` | 드뭄 | 디자이너 설정으로 해결 |

**핫스팟**: 매 프레임 텍스트 변경 (HP/MP 숫자) — Layout 비용 누적.

**대안**:
- 숫자 카운터 같은 자주 갱신은 `STextBlock` 보다 **고정 폭 폰트** + `SetText` (Layout 비용 줄임).
- 숫자만 변하는 케이스는 `SetText` 호출 빈도를 낮추기 (예: 0.1초마다).

#### `URichTextBlock` (가장 비싼 텍스트 위젯)

| 동작 | 발생 reason | 빈도 | 비용 |
|------|-------------|------|------|
| `SetText(FText)` | `Layout` + 마크업 파싱 + Run 시퀀스 재구성 + decorator 인스턴스화 | 매번 | **매우 높음** |
| Decorator 변경 (`<Style>`/`<Image>`/`<Hyperlink>`) | 동상 + 디코레이터 GC | | **매우 높음** |
| `SetTextStyle(FTextBlockStyle)` | `Layout` | 호버 시 | 회피 권장 |

**핫스팟**:
- 매 프레임 또는 0.1초마다 텍스트 변경 → 마크업 파싱 + Run 시퀀스 재구성. 100개 RichTextBlock 이 동시 갱신되면 ms 단위 비용.
- 채팅 로그·다이얼로그 등 자주 추가되는 케이스.

**회피 패턴**:
1. **단순 텍스트는 `STextBlock`/`UTextBlock`** — RichText 는 마크업 필요할 때만.
2. **RichText 안의 일부만 변경**되는 경우 → **분리**: 정적 `URichTextBlock` + 동적 `UTextBlock` 을 `UHorizontalBox` 에 같이.
3. 채팅 로그는 **새 메시지마다 새 RichTextBlock 추가**가 아닌 **누적 텍스트** 한 RichTextBlock 의 SetText 도 비싼데, 더 비싼 것은 100개의 위젯. 적정선 — 100개 메시지 누적 시 RichTextBlock 1개로 잘라 합치기.
4. **`UInvalidationBox` 안에 두지 말 것** — 매번 캐시 무효화로 손해.
5. RichTextBlock 자체를 **커스텀 SLeafWidget** 으로 대체 (간단한 `FSlateDrawElement::MakeText` 한 줄로) — 마크업 불필요 시.

#### `SEditableText` / `UEditableText` / `SMultiLineEditableText` 등

| 동작 | 발생 reason | 빈도 | 비용 |
|------|-------------|------|------|
| 키 입력 (typed) | `Layout` (텍스트 메트릭 재측정) + 커서 위치 갱신 | **매 키마다** | 중간 |
| 선택 영역 변경 | `Paint` (선택 영역 강조) | 마우스 드래그 중 | 낮음 |
| `SetText` | `Layout` | 외부 변경 시 | 중간 |
| Multi-line 텍스트 줄바꿈 | `Layout` + 줄 포맷 재계산 | 모든 줄 변경 시 | **높음** (줄 수 비례) |

**핫스팟**:
- 멀티라인 EditableText 에 1000줄 입력 후 한 줄 추가 → 줄바꿈 재계산 비용.
- 채팅 입력창에서 한국어 IME 입력 시 매 글자마다 `OnKeyChar` 호출.

**회피 패턴**:
1. **단일 라인 입력은 `UEditableText` / `UEditableTextBox`** — Multi 보다 훨씬 가벼움.
2. **검색창**은 `USearchBox` (Slate 기본) — 디바운스 내장.
3. 멀티라인 + 큰 텍스트는 **scroll 영역** 안에 두어 가시 범위만 페인트.
4. **외부 setter (`SetText`) 빈도 낮추기** — 사용자 입력은 어쩔 수 없지만 외부 자동 갱신은 0.1~0.5초 throttle.

---

### 2.2 리스트 / 트리 위젯

#### `SListView<T>` / `UListView` / `UTileView` / `UTreeView`

| 동작 | 발생 reason | 빈도 | 비용 |
|------|-------------|------|------|
| `RequestListRefresh()` | `Layout` (모든 가시 행 재생성) | 데이터 변경 시 | **높음** |
| `RequestListRefreshAndScrollToBottom()` | 위 + 스크롤 | 채팅 추가 등 | **높음** |
| `SetItemSelection(...)` | `Paint` (선택 강조) | 클릭 시 | 낮음 |
| 스크롤 (사용자) | `Layout` (가시 행 재배치) | 매 프레임 (스크롤 중) | **중간** |

**핫스팟**:
- 매 프레임 `RequestListRefresh` 호출 → 모든 가시 행 위젯 재생성. 100개 행 × 60fps = 6000회/초.
- 큰 리스트 (10000+ 아이템) 의 데이터 변경 → 풀에서 위젯 재생성.

**회피 패턴**:
1. **`RequestListRefresh` 호출 빈도 최소화** — 변경된 행만 알면 `RequestRowItemRefresh(Item)` 사용 (가능하면).
2. **`UDynamicEntryBox` / `EntryWidgetClass`** — UListViewBase 의 위젯 풀링. 풀에서 재사용 (새로 생성 X).
3. **`IUserListEntry`/`IUserObjectListEntry`** 콜백 (`OnListItemObjectSet`/`SetEntry`) — 위젯 생성은 한 번, 데이터 갱신만 매번.
4. **`EItemAlignment::EvenlyDistributed`** 같은 고비용 정렬 회피.
5. 가상화 (`Virtualizing`) 활성 — 가시 영역만 위젯 생성. UE 기본은 활성.

#### `IUserListEntry::OnListItemObjectSet(UObject*)` 패턴 — 핵심

```cpp
UCLASS()
class UMyItemEntryWidget : public UUserWidget, public IUserObjectListEntry
{
    GENERATED_BODY()
public:
    UPROPERTY(meta=(BindWidget)) UTextBlock* NameText;
    UPROPERTY(meta=(BindWidget)) UImage*     IconImage;

protected:
    virtual void NativeOnListItemObjectSet(UObject* InListItem) override
    {
        // 위젯은 풀에서 재사용 — 데이터만 갱신
        if (UMyItem* Item = Cast<UMyItem>(InListItem))
        {
            NameText->SetText(Item->GetName());            // Layout (텍스트 폭)
            IconImage->SetBrushFromTexture(Item->Icon);    // Paint
        }
    }
};
```

`NativeConstruct` 가 아닌 `NativeOnListItemObjectSet` 을 override — **위젯 재사용** + **데이터만 변경**.

---

### 2.3 진행도 / 애니메이션 위젯

#### `SProgressBar` / `UProgressBar`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `SetPercent(float)` | `Paint` (Layout 변경 없음 — 박스 크기 동일) | 매 프레임 가능 |
| `SetFillColorAndOpacity` | `Paint` | 드뭄 |

**핫스팟**: 매 프레임 부드러운 보간으로 갱신 — 그래도 비교적 가벼움 (Paint 만, Layout X).

**회피 패턴**:
1. `TSlateAttribute<float, EInvalidateWidgetReason::Paint>` 으로 자동화.
2. 큰 변화만 갱신 (`abs(NewPercent - OldPercent) > 0.01f`).
3. Tick 대신 `RegisterActiveTimer` (SlateCore Animation).

#### `SThrobber` / `SCircularThrobber` / `UThrobber` / `UCircularThrobber`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| 회전 애니메이션 | **자동 휘발성** (매 프레임 Paint) | 매 프레임 |
| `SetNumPieces` (Throbber) | `Layout` | 드뭄 |

**핫스팟**: Throbber 자체가 **휘발성** — `UInvalidationBox` 안에 두면 캐시가 매 프레임 무효화 → **두지 말 것**.

**회피 패턴**:
1. Throbber 가 보일 때만 `SetVisibility(Visible)`, 안 보일 때 `Collapsed`.
2. **`UInvalidationBox` 외부에** 배치.
3. 자주 사용 안 함 (로딩 중에만) → 동적 생성/제거.

#### `FCurveSequence` (SlateCore Animation)

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `Play(SharedThis(this))` | `Paint` (커브 값 사용 람다 갱신) | 매 프레임 (재생 중) |
| `JumpToEnd` / `Reverse` | `Paint` | 한 번 |

**핫스팟**: 호버 페이드·메뉴 슬라이드 같은 단순 트위닝 — `Paint` 만 발생, 비교적 가벼움.

**회피 패턴**: 정상. Throbber 와 달리 **재생 끝나면 자동 ActiveTimer 종료** → 캐시 활용 가능.

---

### 2.4 버튼 / 체크박스

#### `SButton` / `UButton`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| 호버 (Mouse Enter/Leave) | `Paint` (호버 색 변경) | 호버 시 |
| 클릭 (Pressed/Released) | `Paint` | 클릭 시 |
| `SetButtonStyle` | `Layout` (스타일 변경) | 드뭄 |
| `SetColorAndOpacity` | `Paint` | 드뭄 |

**핫스팟**: 일반적으로 가벼움. 다만 **버튼이 100개 동시 호버** (메뉴 빠르게 지나가기) 시 누적.

**회피 패턴**:
1. 메뉴 배경에 `UInvalidationBox` — 호버되는 버튼만 갱신.
2. `SButton` 의 `IsFocusable` false 설정 — 포커스 변경 인밸리데이션 회피.

#### `SCheckBox` / `UCheckBox`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `SetIsChecked(ECheckBoxState)` | `Paint` (체크 박스 그림 변경) | 클릭 시 |
| 호버 | `Paint` | 호버 시 |

**핫스팟**: 가벼움. 100+ 체크박스 (인벤토리 다중 선택) — 모두 동시 갱신은 드뭄.

---

### 2.5 패널 위젯 — 자식 변경

#### `SBoxPanel` (`SVerticalBox`/`SHorizontalBox`) / `UVerticalBox`/`UHorizontalBox`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `AddChild(Widget)` | `ChildOrder` (Prepass + Layout 함의) | 매번 추가 시 |
| `RemoveChild(Widget)` | `ChildOrder` | 매번 제거 시 |
| `ClearChildren` | `ChildOrder` (다수 자식 제거) | 한 번 |
| Slot 의 `Padding` / `HAlign` / `VAlign` 변경 | `Layout` | 드뭄 |

**핫스팟**: 채팅창처럼 **자주 자식 추가**되는 케이스 — `ChildOrder` 가 매번 발행.

**회피 패턴**:
1. **`UListView`/`UScrollBox` 사용** — `UVerticalBox` 에 동적 추가 대신.
2. **풀링** — 자식을 미리 만들고 `SetVisibility` 토글.
3. 정적 자식 트리는 `UInvalidationBox` 안에.

#### `UCanvasPanel` / `SConstraintCanvas`

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `UCanvasPanelSlot::SetPosition` | `Layout` (자식 위치 변경) | 드래그 중 매 프레임 |
| `UCanvasPanelSlot::SetSize` | `Layout` | 리사이즈 중 매 프레임 |
| `UCanvasPanelSlot::SetZOrder(int32)` | `ChildOrder` (정렬 변경) | 드뭄 |
| `UCanvasPanelSlot::SetAnchors` | `Layout` | 드뭄 |

**핫스팟**: 드래그 중 위치 갱신 — 매 프레임 Layout. 부모 패널만 갱신되므로 비교적 가벼움.

**회피 패턴**:
1. `SetRenderTransform(FWidgetTransform)` 으로 대체 — `RenderTransform` reason 만 발행 (Layout 변경 X).
2. 드래그 종료 후 최종 위치만 `SetPosition`.

> ⚠ `UCanvasPanelSlot::ZOrder` 와 Slate `LayerId` 는 **다른 개념**. ZOrder 는 부모 패널의 자식 정렬, LayerId 는 한 위젯 안의 그리기 순서. 자세히 [`SlateCore/references/Drawing.md §5.1`](../skills/SlateCore/references/Drawing.md).

---

### 2.6 NativeOnPaint / NativePaint override (UMG)

#### `UUserWidget::NativePaint` override

> [`UMG/references/UUserWidget.md §5.4`](../skills/UMG/references/UUserWidget.md) 의무 섹션.

| 영향 | 비용 |
|------|------|
| 위젯 자동 휘발성 처럼 동작 → `UInvalidationBox` 캐시 비활성 | **매우 높음** |
| LayerId 단조 증가 누락 → 자식 가려짐 | 시각 버그 |
| 매 프레임 새 `FSlateBrush` 생성 → DrawCall 배치 깨짐 | 메모리 + DrawCall |
| Canvas Panel ZOrder 와 LayerId 혼동 | 의도와 다른 순서 |

**핫스팟**: 사용자 정의 시각화 (게이지·차트·미니맵) 가 `NativePaint` override 시.

**회피 패턴**:
1. **마지막 수단** — 표준 UMG 위젯 조합으로 표현 가능하면 우선.
2. 직접 그릴 영역만 작은 **C++ SLeafWidget** 분리 + 외부에서 `UInvalidationBox` 로 감싸기.
3. **올바른 LayerId 사용** — `Super::NativePaint(...)` 반환값 받아 `+1`.
4. **`FSlateBrush` 멤버 캐시** — 매 프레임 새로 만들지 말 것.
5. **DrawCall 배치 친화적** — 같은 텍스처/폰트 끼리 묶어 그리기. 자세히 [`SlateCore/references/Drawing.md §5.2`](../skills/SlateCore/references/Drawing.md).

---

### 2.7 입력 / 포커스

#### 포커스 변경 (`OnFocusReceived`/`OnFocusLost`)

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| 포커스 획득/상실 | `Paint` (포커스 표시 그림 변경) | 키보드/게임패드 내비 시 |
| `ShowUserFocus` 활성 | + 부모도 갱신 | 자주 |

**핫스팟**: 게임패드 내비게이션으로 매 0.1초 포커스 이동 — 두 위젯 (이전·새) 모두 갱신.

**회피 패턴**:
1. 포커스 표시를 **`SBorder` 단일 위젯** 으로 감싸기 (포커스된 위젯 위에 이동) — 하나만 갱신.
2. `bIsFocusable = false` (포커스 안 받아도 되는 위젯) — 내비 트리에서 빠짐.

#### `SetVisibility` 잦은 호출

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| `Visible ↔ Collapsed` | `Visibility` (Layout 함의) | **높음** — 부모 트리 재배치 |
| `Visible ↔ Hidden` | `Visibility` (공간 그대로) | 중간 — Paint만 |
| `Visible ↔ HitTestInvisible/SelfHitTestInvisible` | `Visibility` | 낮음 |

**핫스팟**: 빠르게 보였다 숨었다 하는 위젯 (툴팁·버블) — `Collapsed` 사용 시 부모 레이아웃 매번 재계산.

**회피 패턴**:
1. 짧은 시간 (1초 미만) 토글은 `Hidden` 사용 — 공간은 차지하지만 Layout 비용 없음.
2. 영구적 숨김은 `Collapsed`.
3. 알파 페이드는 `SetRenderOpacity(0)` — `Paint` reason 만 (Layout 변경 X).

---

### 2.8 데이터 바인딩 (TAttribute lambda)

#### TAttribute lambda 안의 비싼 계산

| 동작 | 발생 reason | 빈도 |
|------|-------------|------|
| TAttribute lambda 가 매 프레임 호출 | (직접적인 invalidate 는 아니지만 **결과 변경 시 SWidget setter 호출** → 자동 invalidate) | 매 프레임 |

**핫스팟**: lambda 안에서 `ComputeExpensiveLabel()` 같은 무거운 계산 — 매 프레임 호출.

**회피 패턴**:
1. **결과 캐시** — 멤버에 캐시 후 람다는 단순 조회.
2. **`TSlateAttribute<T, reason>`** 사용 — 값 변경 시에만 자동 invalidate (TAttribute 보다 효율).
3. **갱신 트리거 명시** — `SetXxx` 직접 호출이 보통 더 효율.

---

