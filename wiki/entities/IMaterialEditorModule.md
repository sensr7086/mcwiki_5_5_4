---
title: "IMaterialEditorModule"
kind: entity
status: stub
parent: editor
tags: [editor, material, module, delegate, ue-574]
module: MaterialEditor
header: "Public/MaterialEditorModule.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# IMaterialEditorModule

`MaterialEditor` 모듈의 **외부 API 인터페이스**. 핵심 책임은 3개 editor 변종 (Material / MaterialFunction / MaterialInstance) 의 *lifecycle delegate* 노출 — 외부 모듈이 editor open 시점에 hook 가능. vault [[sources/ue-editor-toolmenus]] §2.9.5 의 "Material Editor delegate 🔴 INFERRED" 를 정확히 해소하는 module.

## 핵심 delegate (3종)

| Delegate | 매크로 | 콜백 시그니처 | 호출 시점 |
|---|---|---|---|
| `OnMaterialEditorOpened()` | `DECLARE_EVENT_OneParam` | `TWeakPtr<IMaterialEditor>` | UMaterial 더블클릭 → toolkit 생성 직후 |
| `OnMaterialFunctionEditorOpened()` | 동일 | 동일 | UMaterialFunction 더블클릭 시 |
| `OnMaterialInstanceEditorOpened()` | 동일 | 동일 | UMaterialInstance 더블클릭 시 |

## 주요 API

| API | 설명 |
|---|---|
| `Get()` (static) | `FModuleManager::Get().GetModuleChecked<IMaterialEditorModule>("MaterialEditor")` 의 wrapper |
| `OnMaterialEditorOpened()` | delegate 참조 (`FMaterialEditorOpenedEvent&`) |
| `CreateMaterialEditor(...)` | external 호출로 Material Editor 생성 (toolkit factory) |
| `GetMaterialEditingFunctionLibrary` | (검증 미완) |

## 사용 패턴

```cpp
// StartupModule
IMaterialEditorModule& MatModule = FModuleManager::LoadModuleChecked<IMaterialEditorModule>("MaterialEditor");
EditorOpenedHandle = MatModule.OnMaterialEditorOpened().AddStatic(&MyCallback);

// Callback (매 Material Editor open 마다 호출 — 3 변종 자동 분기)
void MyCallback(TWeakPtr<IMaterialEditor> WeakEditor)
{
    auto Editor = WeakEditor.Pin();
    if (!Editor.IsValid()) return;
    // toolkit live 상태 — ExtendMenu 등 안전 적용
}

// ShutdownModule
if (FModuleManager::Get().IsModuleLoaded("MaterialEditor"))
{
    MatModule.OnMaterialEditorOpened().Remove(EditorOpenedHandle);
}
```

## 관련 함정

- [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] — 본 module 사용한 표준 패턴
- `OnRegisterTabs` delegate **부재** — Persona 와 달리 *MainMenu / Window 메뉴 확장 불가* — vault §2.9 한계
- ShutdownModule 의 `IsModuleLoaded` 검사 누락 시 dangling — module unload 순서 race

## 관련 entity

- [[IMaterialEditor]] (toolkit 인터페이스 — 콜백 인자)
- [[UMaterial]] / [[UMaterialEditingLibrary]]
- [[UToolMenus]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| 3 delegate (Material / Function / Instance) | 🟢 VAULT (MaterialEditorModule.h L55/58/62 직접 확인) |
| `TWeakPtr<IMaterialEditor>` 시그니처 | 🟢 VAULT (DECLARE_EVENT_OneParam 직접 확인) |
| OnRegisterTabs delegate 부재 | 🟢 VAULT (header 전체 검토) |
| CreateMaterialEditor / GetMaterialEditingFunctionLibrary API | 🔴 INFERRED (검증 미완) |

## 변경 이력

- 2026-05-22: stub 작성 (v0.20 filing-back)
