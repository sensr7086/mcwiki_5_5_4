---
name: override-index
description: CoreUObject·SlateCore·Slate·UMG virtual 함수 통합 표 + RebuildWidget 사이클 + Super 호출 의무 + 구획별 초기화 매트릭스. 새 클래스 작성·override 결정 시 의무 Read.
---

# Override Index — virtual 함수 + RebuildWidget 사이클 통합 인덱스

> 본 위키에 작성된 모든 sub-skill 의 **virtual 오버라이드 포인트** 를 한곳에서 보는 인덱스. 각 항목은 정확한 라인 번호와 sub-skill 링크로 cross-reference.
> **§5 RebuildWidget 사이클** 은 UMG → SlateCore 변환의 핵심이라 별도 섹션으로 깊이 다룬다.
> 갱신 이력: 2026-05-03 (CoreUObject 13 + SlateCore 10 + Slate 5 + UMG 2 sub-skill 기준).

---

## 0. 사용 규칙

1. 새 클래스 작성 또는 기존 코드 분석 시, 어느 virtual 을 override 해야 할지 확인.
2. 각 표는 **호출 시점·반환 의미·Super 호출 필수 여부** 를 한 줄로 정리.
3. 자세한 시그니처·예제·함정은 cross-reference 된 sub-skill 본문에서 확인.
4. **🛠 마커** 는 에디터 전용. 게임 빌드에서는 컴파일에서 빠지거나 no-op (자세한 분리는 [`05_EditorOnlyIndex.md`](./05_EditorOnlyIndex.md)).

---

## 1 ~ 5 모듈별 virtual 표 — [`references/OverrideTablesDeep.md`](./references/OverrideTablesDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인은 §6 Super 호출 통합 표 (가장 자주 틀리는 부분) / 깊이는 reference.

| § | 모듈 | 내용 | reference |
|---|------|------|-----------|
| 1 | **CoreUObject** | UObject 라이프사이클 virtual + FProperty/FField virtual + FGCObject/FReferenceCollector | [`§1`](./references/OverrideTablesDeep.md#1-coreuobject-모듈--가장-자주-override) |
| 2 | **SlateCore** | SWidget/SCompoundWidget/SLeafWidget/SPanel virtual + Construct/OnPaint/Tick | [`§2`](./references/OverrideTablesDeep.md#2-slatecore-모듈--위젯-기본-virtual) |
| 3 | **Slate** | 인하우스 툴 묶음 virtual (FAssetEditorToolkit / SDockTab / FUICommandList / SGraphEditor) | [`§3`](./references/OverrideTablesDeep.md#3-slate-모듈--인하우스-툴-묶음) |
| 4 | **UMG** | UWidget/UUserWidget Native* 30+ + RebuildWidget + SynchronizeProperties | [`§4`](./references/OverrideTablesDeep.md#4-umg-모듈--위젯-라이프사이클) |
| 5 | **⚡ RebuildWidget 사이클** | UMG → SlateCore 변환의 핵심 (가장 자주 헷갈리는 부분) | [`§5`](./references/OverrideTablesDeep.md#5--rebuildwidget-사이클-umg--slatecore-변환의-핵심) |

> 자세한 virtual 시그니처 + Super 호출 위치 + 위반 증상 = reference 참조.

---

## 6. 🚨 Super 호출 순서 통합 표 (가장 자주 틀리는 부분)

`override` 시 **Super 를 첫 줄에 호출하느냐, 마지막 줄에 호출하느냐** 가 라이프사이클 안전성을 결정한다. UE 전체 관례:

> **초기화/생성 계열 → Super FIRST**.  **정리/파괴 계열 → Super LAST**.  **콜백/이벤트 계열 → 시나리오별**.

### 6.1 CoreUObject (UObject 라이프사이클)

| virtual | Super 위치 | 베이스 책임 | 위반 시 증상 |
|---------|-----------|------------|--------------|
| `PostInitProperties()` | **FIRST** | UPROPERTY 기본값 적용·CDO 등록 | UPROPERTY 미초기화 / CDO 마커 누락 |
| `PostLoad()` | **FIRST** | 디스크 → 메모리 변환 후 초기화 | UPROPERTY 패치 없는 채로 사용자 코드 실행 |
| `PostInitializeComponents()` (AActor) | **FIRST** | 컴포넌트 RegisterComponent | 컴포넌트 미등록 상태 사용 |
| `BeginPlay()` (AActor/UActorComponent) | **FIRST** | bHasBegunPlay 플래그 설정·자식 BeginPlay | 자식 BeginPlay 누락 / `IsActorInitialized` 거짓 |
| `Tick(DeltaTime)` | **FIRST** | (베이스는 비어있지만 미래 호환) | 향후 Engine 변경 시 컴포넌트 미틱 |
| `EndPlay(EEndPlayReason)` | **LAST** | bHasBegunPlay 해제·델리게이트 정리 | 사용자 cleanup 중 bHasBegunPlay 가 false → 분기 오작동 |
| `BeginDestroy()` | **LAST** | UObject 해제 마커·렌더 리소스 큐 | 사용자 cleanup 중