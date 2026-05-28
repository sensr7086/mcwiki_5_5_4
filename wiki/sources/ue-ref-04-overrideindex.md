---
type: source
title: "UE refs — 04 OverrideIndex (Super 호출 통합 hub)"
slug: ue-ref-04-overrideindex
source_path: raw/ue-wiki-llm/references/04_OverrideIndex.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/UMG-Super-Call-Convention]]"
  - "[[concepts/Object-Lifecycle]]"
tags: [ue, reference, override, super, lifecycle, virtual, governance]
---

# UE refs — 04 OverrideIndex 🚨

> Source: [[raw/ue-wiki-llm/references/04_OverrideIndex.md]] · CoreUObject 13 + SlateCore 10 + Slate 5 + UMG 2 sub-skill 기준

## 1. Summary

CoreUObject / SlateCore / Slate / UMG / Components / GameFramework virtual 함수 통합 표 + RebuildWidget 사이클 + **Super 호출 의무** + 구획별 초기화 매트릭스. **모든 new class / override 결정 시 Read 의무**. 깊이 매트릭스 = [[sources/ue-ref-deep-overridetables]] (§1-§5). 본 페이지는 §6 Super 호출 통합 표 (가장 자주 틀리는 부분) 의 권위 source.

## 2. Super 호출 통합 규칙 🟢

> **초기화/생성 계열 → Super FIRST**. **정리/파괴 계열 → Super LAST**. **콜백/이벤트 계열 → 시나리오별**.

### 2.1. CoreUObject — UObject 라이프사이클

| virtual | Super | 베이스 책임 | 위반 증상 |
| -- | -- | -- | -- |
| `PostInitProperties()` | **FIRST** | UPROPERTY 기본값·CDO 등록 | UPROPERTY 미초기화 / CDO 마커 누락 |
| `PostLoad()` | **FIRST** | 디스크 → 메모리 변환 후 초기화 | UPROPERTY 패치 안 된 채 사용자 코드 |
| `PostInitializeComponents()` (AActor) | **FIRST** | 컴포넌트 `RegisterComponent` | 컴포넌트 미등록 사용 |
| `BeginPlay()` (AActor/UActorComponent) | **FIRST** | `bHasBegunPlay` 설정·자식 BeginPlay | 자식 BeginPlay 누락 |
| `Tick(DeltaTime)` | **FIRST** | (현재 비어있음, 미래 호환) | 향후 Engine 변경 시 미틱 |
| `EndPlay(EEndPlayReason)` | **LAST** | `bHasBegunPlay` 해제·델리게이트 정리 | cleanup 중 플래그 거짓 → 분기 오작동 |
| `BeginDestroy()` | **LAST** | UObject 해제 마커·렌더 리소스 큐 | cleanup 중 |
| `FinishDestroy()` | **LAST** | 최종 해제 | 자원 누수 |
| `Serialize(FArchive&)` | **FIRST** | UPROPERTY 직렬화 | 직렬화 데이터 손상 |

### 2.2. Components / GameFramework

| virtual | Super | 비고 |
| -- | -- | -- |
| `UActorComponent::InitializeComponent` | **FIRST** | `bWantsInitializeComponent=true` 필요 |
| `UActorComponent::TickComponent` | **FIRST** | Tick 가능 컴포넌트만 |
| `UActorComponent::OnRegister / OnUnregister` | **FIRST / LAST** | RenderState 등록·해제 |
| `UActorComponent::OnComponentCreated / DestroyComponent` | **FIRST / LAST** | 컴포넌트 라이프사이클 |
| `USceneComponent::OnAttachmentChanged` | **FIRST** | Transform 갱신 |
| `AActor::PreInitializeComponents / PostInitializeComponents` | **FIRST** | InitializeComponent 묶음 |
| `AController::OnPossess / OnUnPossess` | **FIRST / LAST** | Pawn possession |

### 2.3. SlateCore — SWidget

| virtual | Super | 비고 |
| -- | -- | -- |
| `SWidget::Construct(FArguments&)` | **FIRST** (SCompoundWidget) | ChildSlot 셋업 |
| `SWidget::Tick(FGeometry, double, float)` | (Super 없음, 베이스 비어있음) | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| `SWidget::OnPaint(...)` | (시나리오별) | 페인트 사이클 — 자세히 [[sources/ue-slatecore-drawing]] |
| `SCompoundWidget::OnMouseButtonDown / Up / Move` | 시나리오별 | FReply 반환 |

### 2.4. UMG — UWidget / UUserWidget 🟢

UMG/Slate 변환의 핵심 — **가장 자주 틀리는 부분**:

| virtual | Super | 베이스 책임 | 위반 증상 |
| -- | -- | -- | -- |
| `UUserWidget::NativeOnInitialized()` | **FIRST** | 1회 초기화 | 베이스 초기화 누락 |
| `UUserWidget::NativePreConstruct()` | **FIRST** | 에디터 미리보기·런타임 모두 | preview broken |
| `UUserWidget::NativeConstruct()` | **FIRST** | Slate 위젯 생성 후 | binding 누락 |
| `UUserWidget::NativeTick(FGeometry, float)` | **FIRST** + 스코프 | Tick 베이스 | 스코프 없음 — Insights 식별 불가 |
| `UUserWidget::NativeDestruct()` | **LAST** | 정리 베이스 | 자식 정리 후 베이스 |
| `UWidget::SynchronizeProperties()` | **FIRST** | Slate 위젯 속성 동기화 | 속성 미반영 |
| `UWidget::RebuildWidget()` | (override 시 베이스 호출 안 함 — 직접 SNew) | SWidget 인스턴스 생성 | — |
| `UWidget::ReleaseSlateResources(bool)` | **LAST** | 위젯 트리 정리 | leak |

### 2.5. Editor — 🛠 Toolkit

| virtual | Super | 비고 |
| -- | -- | -- |
| `FAssetEditorToolkit::RegisterTabSpawners` | **FIRST** | 기본 탭 누락 방지 — [[sources/ue-editor-unrealed-asseteditortoolkit]] |
| `FAssetEditorToolkit::UnregisterTabSpawners` | **FIRST** | 베이스 등록한 것 먼저 정리 |
| `FAssetEditorToolkit::InitToolMenuContext` | **FIRST** | ToolMenu 컨텍스트 |
| `FMaterialEditor / FBlueprintEditor` (FAssetEditorToolkit 자손) | 위와 동일 | — |

## 3. RebuildWidget 사이클 (UMG → SlateCore) 🟢

UMG 의 가장 복잡한 부분 — UWidget 가 Slate SWidget 으로 변환되는 흐름:

```
1. UWidget::TakeWidget()          ← 외부 진입
2. UWidget::RebuildWidget()       ← override (SNew(SMyWidget) 반환)
3. UWidget::OnWidgetRebuilt()     ← 후처리 콜백
4. UWidget::SynchronizeProperties() ← UPROPERTY → SWidget 속성 동기화 (Super FIRST)
5. (사용 중)
6. UWidget::ReleaseSlateResources(bReleaseChildren) ← cleanup (Super LAST)
```

`RebuildWidget` 은 **SNew 으로 새 SWidget 생성 / 반환** — Super 호출 안 함 (베이스는 abstract). `SynchronizeProperties` 는 매번 변경 시 호출 — Super FIRST.

자세히 → [[sources/ue-umg-uwidget]] · [[sources/ue-umg-uuserwidget]] · [[sources/ue-umg-invalidationdeep]].

## 4. Super + 스코프 순서

`Super` 와 `TRACE_CPUPROFILER_EVENT_SCOPE` 동시 사용 시:

```cpp
// ✅ Super FIRST → 스코프 그 다음
void UMyWidget::NativeTick(const FGeometry& Geo, float Dt)
{
    Super::NativeTick(Geo, Dt);                          // 1. Super FIRST
    SCOPED_NAMED_EVENT_TEXT("MyWidget::Tick", FColor::Cyan);   // 2. 스코프
    // 작업
}
```

**근거**: Super 안의 비용은 베이스가 자체 측정 (예: `SObjectWidget::Tick` 의 `SCOPED_NAMED_EVENT_FSTRING`). 자세히 → [[sources/ue-ref-07-profilingscopeRule]] §4.1.

## 5. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | 초기화 함수에서 Super LAST | FIRST 의무 — 베이스 초기화 누락 |
| 2 | 정리 함수에서 Super FIRST | LAST 의무 — 사용자 cleanup 중 베이스 플래그 무효 |
| 3 | `Tick` override 시 Super 누락 | 베이스가 비어있어도 FIRST — 미래 호환 |
| 4 | `RebuildWidget` 에서 Super 호출 | 베이스 abstract — SNew 으로 직접 생성 |
| 5 | Super 와 스코프 순서 거꾸로 | Super FIRST → 스코프 (Super 비용 중복 측정 회피) |

## 6. Cross-link

- 권위 concept: [[concepts/Component-Lifecycle]] · [[concepts/Actor-Lifecycle]] · [[concepts/UMG-Super-Call-Convention]] · [[concepts/Object-Lifecycle]]
- 깊이 자료: [[sources/ue-ref-deep-overridetables]] (§1-§5 정밀 매트릭스 — 100+ virtual 시그니처)
- 자매 정책 hub: [[sources/ue-ref-07-profilingscopeRule]] (Super + 스코프 순서) · [[sources/ue-ref-05-editoronlyindex]] (4단 분리) · [[sources/ue-ref-10-componentpolicies]] (Components 6대) · [[sources/ue-ref-06-invalidationhotspots]]
- 카테고리 main 적용: [[sources/ue-coreuobject-skill]] (§1) · [[sources/ue-slatecore-skill]] (§3) · [[sources/ue-umg-skill]] (§4 + §3 RebuildWidget) · [[sources/ue-components-skill]] · [[sources/ue-gameframework-skill]]
- Editor toolkit: [[sources/ue-editor-unrealed-asseteditortoolkit]] (§2.5 Toolkit Super)
