---
name: editor-asseteditorapi-staticmesheditor
description: IStaticMeshEditor 접근 표준 — UAssetEditorSubsystem::FindEditorForAsset + EditorName 검증 + GetStaticMeshComponent 표준 패턴. (parent — Editor/AssetEditorAPI/SKILL.md)
---

# IStaticMeshEditor 접근 [grep-listed]

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **헤더**: `Engine/Source/Editor/StaticMeshEditor/Public/IStaticMeshEditor.h`
> **Build.cs 의존**: `"StaticMeshEditor"`

---

## 표준 패턴 — 외부 코드에서 Preview Component 접근

```cpp
#if WITH_EDITOR
#include "IStaticMeshEditor.h"

void AccessStaticMeshEditor(UStaticMesh* Mesh)
{
    if (!IsValid(Mesh)) return;

    UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(Mesh, /*bFocusIfOpen=*/ false);
    if (!EditorInst) return;

    // EditorName 검증
    if (EditorInst->GetEditorName() != FName("StaticMeshEditor")) return;

    // 안전 cast
    auto* SME = static_cast<IStaticMeshEditor*>(EditorInst);
    if (UStaticMeshComponent* PreviewComp = SME->GetStaticMeshComponent())
    {
        // Preview Component 사용 (Material 변경 / 시각화 등)
    }
}
#endif
```

---

## 활용 시나리오

- **Material 일괄 변경 도구** — 열려있는 Static Mesh Editor 의 Preview Material 동적 변경
- **LOD 시각화 디버그** — Preview Component LOD 강제 설정
- **Custom Thumbnail Capture** — Preview Component 기반 썸네일 생성
- **Editor Automation** — 자동 검증 도구에서 Preview 상태 추출

---

## 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | EditorName 검증 없이 `static_cast` | UB 위험 — 반드시 `FName("StaticMeshEditor")` 검증 |
| 2 | `GetStaticMeshComponent()` 반환값 nullptr 미체크 | Preview 미초기화 시 가능 |
| 3 | 캐싱한 `IStaticMeshEditor*` 재사용 | 매 호출 `FindEditorForAsset` 재조회 |
