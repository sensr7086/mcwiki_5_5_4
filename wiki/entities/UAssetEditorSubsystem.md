---
title: "UAssetEditorSubsystem"
kind: entity
status: stub
parent: editor
tags: [editor, subsystem, asset-editor, toolkit, ue-574]
module: UnrealEd
header: "Public/Subsystems/AssetEditorSubsystem.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# UAssetEditorSubsystem

GEditor 의 EditorSubsystem — **모든 asset editor toolkit 의 lifecycle 관리**. 어떤 asset 이 열려있는지 추적하고 open / close / reopen 명령을 처리. Material/Texture/Blueprint/Animation 등 모든 asset editor 가 이를 거쳐 등록.

## 핵심 특성

- **Singleton-ish**: `GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()` 로 접근
- **Asset ↔ Toolkit map** 보유: 같은 asset 을 중복 open 시 기존 toolkit focus
- **Multi-asset open**: 하나의 toolkit 이 여러 asset 편집 가능 (TArray)

## 주요 API

| API | 설명 |
|---|---|
| `OpenEditorForAsset(UObject*)` | 새 toolkit 생성 또는 기존 focus |
| `OpenEditorsForAssets(TArray<UObject*>)` | 멀티 open |
| `CloseAllEditorsForAsset(UObject*)` | 해당 asset 의 모든 toolkit 닫기 |
| `FindEditorForAsset(UObject*, bool bFocusIfOpen)` | 열려있는 toolkit 반환 |
| `GetAllEditedAssets()` | 현재 열려있는 모든 asset 배열 |
| `NotifyAssetClosed/Opened` | 이벤트 broadcast |

## 사용 패턴

```cpp
// 활성 머티리얼 인식
UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
TArray<UObject*> Edited = AES->GetAllEditedAssets();
for (UObject* O : Edited) {
    if (UMaterial* M = Cast<UMaterial>(O)) { /* ... */ }
}

// 강제 재오픈 (외부 변경 후 UI sync)
AES->CloseAllEditorsForAsset(Material);
AES->OpenEditorForAsset(Material);
```

## 관련 함정

- [[concepts/Material-Editor-External-Change-Reopen]] — close+reopen 시 사용자 selection / camera / scroll state 모두 reset
- `OpenEditorForAsset` 는 *비동기 가능성* — 일부 toolkit 은 async load 후 open

## 관련 entity

- [[IToolkit]] · [[FAssetEditorToolkit]] · [[USubsystem]] · [[UEngineSubsystem]] · [[UMaterial]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| GEditor subsystem accessor | 🟢 VAULT (UE 5.7 `AssetEditorSubsystem.h`) |
| GetAllEditedAssets API | 🟢 VAULT (MCMaterialAuto 실측 사용) |
| Close+Reopen state reset | 🟢 VAULT (실측 관찰) |
| OpenEditorForAsset 비동기 가능성 | 🔴 INFERRED (toolkit-by-toolkit 정확 동작 미특정) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-33+34 filing-back cross-link)
