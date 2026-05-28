---
name: editor-asseteditorapi-advancedpreviewscene
description: FAdvancedPreviewScene 사용 표준 — 자체 Preview Scene 구성 (Custom Asset Editor / Thumbnail Renderer). (parent — Editor/AssetEditorAPI/SKILL.md)
---

# FAdvancedPreviewScene [inferred]

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **헤더**: `Engine/Source/Editor/AdvancedPreviewScene/Public/AdvancedPreviewScene.h`
> **Build.cs 의존**: `"AdvancedPreviewScene"`
>
> **요지**: 외부에서 자체 Preview Scene 구성 시 (Custom Asset Editor / Thumbnail Renderer / Tool Window). `FPreviewScene` 자손 — Sky / Floor / 환경 라이트 + Profile 지원.

---

## 표준 패턴

```cpp
#if WITH_EDITOR
#include "AdvancedPreviewScene.h"

// 자체 Preview Scene (간단 Wrapper)
TSharedPtr<FAdvancedPreviewScene> PreviewScene;

void Setup()
{
    FAdvancedPreviewScene::ConstructionValues CVS;
    CVS.bAlwaysAllowAudioPlayback = false;
    CVS.bShouldSimulatePhysics = false;
    PreviewScene = MakeShared<FAdvancedPreviewScene>(CVS);

    // Mesh 추가
    UStaticMeshComponent* PreviewMeshComp = NewObject<UStaticMeshComponent>();
    PreviewMeshComp->SetStaticMesh(MyMesh);
    PreviewScene->AddComponent(PreviewMeshComp, FTransform::Identity);
}
#endif
```

---

## FAdvancedPreviewScene vs FPreviewScene

| 항목 | FPreviewScene | FAdvancedPreviewScene |
|------|---------------|----------------------|
| Sky | 없음 | Sky Sphere 포함 |
| Floor | 없음 | Floor Mesh 포함 |
| 환경 라이트 | 단순 Directional | HDR / Sky Light / 다중 |
| Profile 시스템 | X | ✅ (Editor 설정 연동) |
| 위치 | Engine 모듈 | Editor 전용 |

→ Editor 전용 Preview UI 작성 시 `FAdvancedPreviewScene` 표준.

---

## 활용 시나리오

- **Custom Asset Editor** — 자체 Preview Viewport 구성
- **Thumbnail Renderer** — `UThumbnailRenderer::Draw` 안 Scene 구성
- **Tool Window Preview** — 도구 윈도우 안 미니 Preview
- **Editor Automation** — 자동 스크린샷 캡처

---

## 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | Runtime 모듈에 `"AdvancedPreviewScene"` 의존 | Editor 모듈 전용 — Cooked 빌드 깨짐 |
| 2 | `FPreviewScene` 으로 작성 | Editor UI = `FAdvancedPreviewScene` (Sky / Floor / Profile) |
| 3 | Component lifetime — `AddComponent` 후 GC 방어 누락 | TStrongObjectPtr 또는 UPROPERTY 보관 |
