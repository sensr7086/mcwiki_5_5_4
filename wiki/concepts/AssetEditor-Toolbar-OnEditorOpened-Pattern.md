---
title: "AssetEditor Toolbar 동적 확장 — OnEditorOpened delegate 패턴"
kind: concept
status: stable
severity: "★★★"
tags: [editor, asset-editor, toolbar, toolmenus, material-editor, persona, MMA-39, ue-574]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# AssetEditor Toolbar 동적 확장 — OnEditorOpened delegate 패턴

## 정의

UE 5.7 의 AssetEditor toolkit (Material Editor / Persona / Blueprint Editor 등) 의 **Toolbar 에 외부 모듈이 entry 를 동적으로 추가** 하는 표준 패턴. 핵심: 해당 module 의 `OnXxxEditorOpened` delegate 에 콜백 binding → toolkit live 상태에서 `GetToolMenuToolbarName()` 호출로 정확한 ToolBar name 획득 → `UToolMenus::Get()->ExtendMenu(ToolbarName)`.

**vault §2.9 페어 진단** ([[sources/ue-editor-toolmenus]]):
- `AssetEditor.<X>.MainMenu.*` → **ToolMenus 외 시스템** (TabManager) → ExtendMenu 영원히 stub
- `AssetEditor.<X>.ToolBar`     → **ToolMenus 관리** ✅ — 본 패턴 적용 가능

본 페이지는 vault §2.9.5 의 `🔴 INFERRED` (Blueprint Editor / Material Editor / Niagara Editor 등의 OnRegisterTabs delegate) 를 **Material Editor 의 OnMaterialEditorOpened delegate 로 🟢 VAULT 격상** + 실측 채택본 정리.

## 자세히

### 사례: MCMaterialAuto v0.18 → v0.20 (MMA-38 / MMA-39)

🟢 **VAULT** — MMA-38/39 hazard 로그:

**v0.18 (실패)** — `RegisterStartupCallback` 안에서 직접 ExtendMenu:
```cpp
UToolMenu* M = UToolMenus::Get()->ExtendMenu("AssetEditor.MaterialEditorApp.MainMenu.Tools");
// → MainMenu 는 TabManager 자체 시스템 → 영원히 stub. UI 노출 안 됨. (MMA-38)
```

**v0.20 (확정)** — `IMaterialEditorModule::OnMaterialEditorOpened` delegate 사용:
```cpp
// StartupModule
IMaterialEditorModule& Module = FModuleManager::LoadModuleChecked<IMaterialEditorModule>("MaterialEditor");
EditorOpenedHandle = Module.OnMaterialEditorOpened().AddStatic(&Callback);

// Callback — Material/MaterialFunction/MaterialInstance Editor 모두 호출
void Callback(TWeakPtr<IMaterialEditor> WeakEditor)
{
    TSharedPtr<IMaterialEditor> Editor = WeakEditor.Pin();
    if (!Editor.IsValid()) return;

    // ⭐ FWorkflowCentricApplication 이 1-arg override → 1-arg 버전 호출 의무 (C2660 hazard 별도 concept)
    FName ParentName = NAME_None;
    const FName ToolbarName = Editor->GetToolMenuToolbarName(ParentName);
    if (ToolbarName == NAME_None) return;

    UToolMenu* ToolBar = UToolMenus::Get()->ExtendMenu(ToolbarName);
    if (!ToolBar) return;

    FToolMenuOwnerScoped OwnerScoped(FName("MyOwner"));
    FToolMenuSection& Section = ToolBar->FindOrAddSection("MySection");

    // 중복 add 방어 — Editor 가 여러 번 열릴 때 동일 콜백 반복 호출
    const FName EntryName(TEXT("MyButton"));
    if (Section.FindEntry(EntryName) == nullptr)
    {
        Section.AddEntry(FToolMenuEntry::InitToolBarButton(
            EntryName, FUIAction(...), Label, Tooltip, Icon));
    }
}
```

**핵심 효과**:
- Material Editor toolkit 이 live 상태 → `GetToolMenuToolbarName()` 가 정확한 (이미 ToolMenus 에 등록된) ToolBar name 반환
- Material / MaterialFunction / MaterialInstance Editor *모두* `IMaterialEditor` 인터페이스 → 단일 콜백 통합
- Toolbar entry 가 Material Editor 가 *열린 동안만* 표시 → context 일치

### 호스트별 delegate 매트릭스 (격상)

| 호스트 | Delegate | Module | 콜백 시그니처 | Tier |
|---|---|---|---|---|
| **Material Editor** | `IMaterialEditorModule::OnMaterialEditorOpened()` | `MaterialEditor` | `TWeakPtr<IMaterialEditor>` | 🟢 **VAULT** (v0.20 실측) |
| MaterialFunction Editor | `IMaterialEditorModule::OnMaterialFunctionEditorOpened()` | `MaterialEditor` | `TWeakPtr<IMaterialEditor>` | 🟢 VAULT (header L58) |
| MaterialInstance Editor | `IMaterialEditorModule::OnMaterialInstanceEditorOpened()` | `MaterialEditor` | `TWeakPtr<IMaterialEditor>` | 🟢 VAULT (header L62) |
| **Persona (SkelMesh/Skeleton/Anim*)** | `FPersonaModule::OnRegisterTabs()` | `Persona` | `FWorkflowAllowedTabSet&` + `TSharedPtr<FAssetEditorToolkit>` | 🟢 VAULT (Cycle 5b) |
| Blueprint Editor | `FBlueprintEditorModule::OnRegisterTabs()` (추정) | `Kismet` | (미검증) | 🔴 INFERRED |
| Niagara Editor | (미확인) | `NiagaraEditor` | (미확인) | 🔴 INFERRED |

⚠ **두 패턴의 차이**:
- **OnEditorOpened** (Material): single toolkit 인스턴스 → toolbar 직접 확장 (MainMenu 는 불가)
- **OnRegisterTabs** (Persona): `FWorkflowAllowedTabSet&` 에 `FWorkflowTabFactory` 등록 → TabManager Window 메뉴 자동 등록

Material Editor 에서 *Tools/Window 메뉴* 확장이 필요하면 `OnRegisterTabs` 같은 별도 delegate 가 필요하지만 — Material Editor 모듈은 *해당 delegate 미노출* (`MaterialEditorModule.h` 전체 검토 — `OnRegisterTabs` 부재).

## 회피 패턴 (Production)

### Layer 1 — delegate 등록 시점

```cpp
void FMyEditorModule::StartupModule()
{
    IMaterialEditorModule& Module = FModuleManager::LoadModuleChecked<IMaterialEditorModule>("MaterialEditor");
    EditorOpenedHandle = Module.OnMaterialEditorOpened().AddStatic(&OnOpenedCallback);
}
```
- `LoadModuleChecked` — Editor 모듈은 이 시점에 거의 항상 로드됨
- `AddStatic` — static 함수 binding (this 캡처 회피, dangling 방어)
- handle 보관 의무 — Shutdown 시 Remove

### Layer 2 — 콜백 안 중복 add 방어

```cpp
const FName EntryName(TEXT("MyButton"));
if (Section.FindEntry(EntryName) == nullptr) {
    Section.AddEntry(...);
}
```
- Editor 가 닫혔다가 다시 열리면 콜백 재호출 → entry name 검사로 idempotent

### Layer 3 — Shutdown unregister

```cpp
void FMyEditorModule::ShutdownModule()
{
    if (EditorOpenedHandle.IsValid())
    {
        if (FModuleManager::Get().IsModuleLoaded("MaterialEditor"))
        {
            IMaterialEditorModule& Module = FModuleManager::GetModuleChecked<IMaterialEditorModule>("MaterialEditor");
            Module.OnMaterialEditorOpened().Remove(EditorOpenedHandle);
        }
        EditorOpenedHandle.Reset();
    }
    UToolMenus::UnregisterOwner(FName("MyOwner"));   // entry 일괄 정리
}
```

## 변형 사례

1. **MaterialFunction Editor 만 분기 처리**:
   - 콜백 안 `Editor->GetEditingObjects()` 검사 → `UMaterialFunction` 타입이면 별도 entry
2. **MIC (MaterialInstance) 만 분기**:
   - `OnMaterialInstanceEditorOpened` 별도 콜백 등록
3. **Persona 미러 — Window 메뉴 항목**:
   - Material Editor 의 OnRegisterTabs 부재 → Window 메뉴 항목 *원리적으로 불가* (vault 검증)
   - 우회: Nomad Tab 전역 등록 (`FGlobalTabmanager::RegisterNomadTabSpawner`) — 모든 editor 의 Window > Nomad 카테고리 표시

## 관련 함정

- vault [[sources/ue-editor-toolmenus]] §2.9 — AssetEditor MainMenu = TabManager 자체 시스템 (ExtendMenu stub)
- C2660 — `FWorkflowCentricApplication::GetToolMenuToolbarName` name hiding hazard → `concepts/UE-NameHiding-Override-Hazard` (TODO)
- C2065 — file-local LOCTEXT_NAMESPACE 위치 의존 → `concepts/LOCTEXT-Namespace-Macro-Position-Hazard` (TODO)
- 중복 add 누락 → 같은 toolbar 에 entry 가 *여러 번* 생기는 시각적 버그 가능 (ToolMenus 자체는 dedup 하지만 명시 검사 권장)

## 관련 entity

- [[IMaterialEditor]] (toolkit 인터페이스 — `GetToolMenuToolbarName(FName&)`)
- [[IMaterialEditorModule]] (delegate 호스트)
- [[UToolMenus]]
- [[FAssetEditorToolkit]] (base — GetToolMenuToolbarName)
- [[IToolkit]]

## 열린 질문

1. ❓ Blueprint Editor 의 정확한 delegate 이름 — `FBlueprintEditorModule::OnEditorOpened` 또는 `OnRegisterTabs` ? UE 5.7 소스 직접 검증 필요.
2. ❓ Niagara Editor / Sequencer / StaticMesh Editor 등 다른 AssetEditor 의 toolbar 확장 표준 — module-by-module 검증 필요.
3. ❓ MainMenu 의 Tools / Window 서브메뉴 확장 — *전체* AssetEditor 통합 방법 존재하는가? (현재 결론: 각 module 별 별도 delegate)

## Cross-link

- `sources/ue-editor-toolmenus` § 2.9 (AssetEditor MainMenu = TabManager) + § 2.9.5 (host-별 OnRegisterTabs delegate — Material 분기)
- `sources/ue-editor-personatoolkit` § 2.7 (Persona OnRegisterTabs 표준 — 본 패턴의 페어)
- `sources/ue-editor-unrealed-materialeditor` (Material Editor 데이터 모델)
- `entities/IMaterialEditor` · `entities/IMaterialEditorModule`
- `00_meta/03_EvaluatorRecipe` § Stage 6 (Integration boundary 검증)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| AssetEditor.<X>.MainMenu.* = TabManager 외 시스템 | 🟢 VAULT | sources/ue-editor-toolmenus §2.9 (Cycle 5b 검증) |
| AssetEditor.<X>.ToolBar = ToolMenus 관리 | 🟢 VAULT | AssetEditorToolkit.cpp:1905 RegisterMenu 직접 확인 |
| IMaterialEditorModule::OnMaterialEditorOpened 3개 delegate | 🟢 VAULT | MaterialEditorModule.h L55/58/62 직접 확인 |
| Material/MaterialFunction/MaterialInstance Editor 모두 IMaterialEditor 인터페이스 | 🟢 VAULT | 실측 — v0.20 단일 콜백 통합 동작 |
| Material Editor 의 OnRegisterTabs delegate 부재 | 🟢 VAULT | MaterialEditorModule.h 전체 검토 |
| 중복 add 시 ToolMenus 자동 dedup 동작 | 🟡 PARTIAL | 실측 — race 시나리오 미검증 |
| Blueprint / Niagara Editor 의 동일 패턴 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MCMaterialAuto v0.20 채택본 기반 — MMA-38/39 filing-back)
- 2026-05-22: vault §2.9.5 의 Material Editor 항목 🔴 INFERRED → 🟢 VAULT 격상
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

UToolMenus delegate 패턴 (raw 11→11 동일). 5.7.4 시 검증한 OnXxxEditorOpened delegate 호출 패턴은 5.5.4 에서도 stable. 다만 새 AssetEditor module 의 정확한 delegate 명 (Material/Persona/Blueprint 등) 은 module-by-module 검증 권장 — 원래 §X 열린 질문에 해당.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
