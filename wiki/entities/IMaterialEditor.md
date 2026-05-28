---
title: "IMaterialEditor"
kind: entity
status: stub
parent: editor
tags: [editor, material, toolkit, interface, ue-574]
module: MaterialEditor
header: "Public/IMaterialEditor.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# IMaterialEditor

Material / MaterialFunction / MaterialInstance Editor 의 **공통 toolkit 인터페이스**. `FAssetEditorToolkit` → `FWorkflowCentricApplication` → `IMaterialEditor` chain 상속. 외부 모듈이 Material Editor toolkit 에 접근할 때 사용 — 가장 흔한 use case 는 `IMaterialEditorModule::OnMaterialEditorOpened` 콜백 안 `TWeakPtr<IMaterialEditor>` 처리.

## 핵심 특성

- **3 editor 통합 인터페이스**: Material / MaterialFunction / MaterialInstance Editor 모두 IMaterialEditor 상속
- **Workflow-centric**: `FWorkflowCentricApplication` 상속 → multi-mode + workflow tab 시스템
- **Live toolkit accessor**: delegate 콜백에서 `TWeakPtr<IMaterialEditor>` 받아 `Pin()` 후 사용

## 주요 API (상속 포함)

| API | 출처 | 설명 |
|---|---|---|
| `GetToolMenuToolbarName(FName& OutParent)` | FWorkflowCentricApplication override | 1-arg only — base 의 0-arg overload 는 name hiding 으로 invisible (C2660 hazard) |
| `GetToolkitFName()` | FAssetEditorToolkit | toolkit 이름 (Material/MaterialFunction/MaterialInstance 구분 가능) |
| `GetObjectsCurrentlyBeingEdited()` | FAssetEditorToolkit | 편집 중인 asset 배열 — `UMaterial` / `UMaterialFunction` / `UMaterialInstance` 추출 |
| `GetMaterialInterface()` | IMaterialEditor 자체 (추정) | (검증 미완 — 후속) |

## 사용 패턴

```cpp
// IMaterialEditorModule::OnMaterialEditorOpened 콜백
void OnEditorOpened(TWeakPtr<IMaterialEditor> WeakEditor)
{
    TSharedPtr<IMaterialEditor> Editor = WeakEditor.Pin();
    if (!Editor.IsValid()) return;

    // toolbar 이름 — 1-arg 의무 (C2660 hazard 회피)
    FName ParentName = NAME_None;
    const FName ToolbarName = Editor->GetToolMenuToolbarName(ParentName);

    // 편집 중인 asset 식별
    if (const TArray<UObject*>* Objs = Editor->GetObjectsCurrentlyBeingEdited())
    {
        for (UObject* O : *Objs)
        {
            if (UMaterial* M = Cast<UMaterial>(O)) { /* ... */ }
        }
    }
}
```

## 관련 함정

- [[concepts/UE-NameHiding-Override-Hazard]] — `GetToolMenuToolbarName()` 0-arg overload hide (C2660)
- [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] — IMaterialEditor 통한 toolbar 확장 표준 패턴
- [[concepts/Material-Editor-External-Change-Reopen]] — IMaterialEditor toolkit 의 UI cache stale 함정

## 관련 entity

- [[FAssetEditorToolkit]] (base — 0-arg + 1-arg overload 둘 다)
- [[IMaterialEditorModule]] (delegate 호스트)
- [[UMaterial]] / [[UMaterialEditingLibrary]]
- [[IToolkit]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| 3 editor 통합 인터페이스 (Material/Function/Instance) | 🟢 VAULT (MaterialEditorModule.h L55/58/62) |
| FWorkflowCentricApplication 상속 chain | 🟢 VAULT (MaterialEditor.cpp 직접 확인) |
| GetToolMenuToolbarName 1-arg only (override hiding) | 🟢 VAULT (WorkflowCentricApplication.h L30 + 실측 C2660) |
| GetMaterialInterface 등 IMaterialEditor 자체 API | 🔴 INFERRED (header L21+ 검토 필요) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-39/40 / v0.20 filing-back)
