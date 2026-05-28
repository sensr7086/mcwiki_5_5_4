---
name: editor-asseteditorapi-personatoolkit
description: ISkeletalMeshEditor + IPersonaToolkit + UDebugSkelMeshComponent 접근 표준 — Skeletal/Animation 계열 에디터 Preview Component 접근. (parent — Editor/AssetEditorAPI/SKILL.md)
---

# ISkeletalMeshEditor + IPersonaToolkit + UDebugSkelMeshComponent [grep-listed]

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **헤더**:
> - `Engine/Source/Editor/SkeletalMeshEditor/Public/ISkeletalMeshEditor.h`
> - `Engine/Source/Editor/Persona/Public/IPersonaToolkit.h`
> - `Engine/Source/Editor/UnrealEd/Classes/Animation/DebugSkelMeshComponent.h`
>
> **Build.cs 의존**: `"SkeletalMeshEditor", "Persona"`

---

## 통합 구조 — Persona Toolkit

Skeletal Mesh / Animation 계열 에디터 = **Persona Toolkit** 통합. Preview Component = `UDebugSkelMeshComponent` (`USkeletalMeshComponent` 자손, Editor 전용).

```
USkeletalMesh
   ↓ FindEditorForAsset
IAssetEditorInstance (= ISkeletalMeshEditor)
   ↓ GetPersonaToolkit
TSharedRef<IPersonaToolkit>
   ↓ GetPreviewMeshComponent
UDebugSkelMeshComponent (USkeletalMeshComponent 자손)
```

---

## 표준 패턴

```cpp
#if WITH_EDITOR
#include "ISkeletalMeshEditor.h"
#include "IPersonaToolkit.h"
#include "Animation/DebugSkelMeshComponent.h"

void AccessSkeletalMeshEditor(USkeletalMesh* SkelMesh)
{
    if (!IsValid(SkelMesh)) return;

    UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(SkelMesh, false);
    if (!EditorInst || EditorInst->GetEditorName() != FName("SkeletalMeshEditor")) return;

    // 1. ISkeletalMeshEditor cast
    auto* SkelEditor = static_cast<ISkeletalMeshEditor*>(EditorInst);

    // 2. IPersonaToolkit 가져오기 — Persona 통합 API
    TSharedRef<IPersonaToolkit> Toolkit = SkelEditor->GetPersonaToolkit();

    // 3. Preview Mesh Component (UDebugSkelMeshComponent — USkeletalMeshComponent 자손)
    if (UDebugSkelMeshComponent* PreviewComp = Toolkit->GetPreviewMeshComponent())
    {
        // - 본 시각화 (DebugDrawSkeleton)
        // - Cloth 시뮬 디버그
        // - Animation Preview
    }

    // 4. Preview Scene (FAdvancedPreviewScene)
    // TSharedRef<IPersonaPreviewScene> PreviewScene = Toolkit->GetPreviewScene();
}
#endif
```

---

## UDebugSkelMeshComponent 추가 기능 [inferred]

`UDebugSkelMeshComponent : public USkeletalMeshComponent` — Editor 전용 추가 기능:

| 기능 | 설명 |
|------|------|
| `BoneDrawMode` | 본 시각화 모드 (All / SelectedAndParents / None 등) |
| `bDrawBoneInfluences` | 본 영향력 시각화 |
| `bDrawMorphTargetVerts` | Morph Target 정점 시각화 |
| Cloth Simulation 디버그 | 클로스 시뮬 시각화 |
| Physics Asset 시각화 | Physics Body / Constraint 표시 |
| Pose Watch | Animation 포즈 와치 |

---

## 활용 시나리오

- **Animation Preview 자동화** — 외부 도구에서 Preview Mesh 의 본 트랜스폼 추출
- **Cloth 시뮬 디버그 도구** — Cloth 파라미터 동적 변경 + 시각화
- **Skeleton 검증** — 본 계층 / 본 회전 한계 검증
- **Editor Automation** — Animation Test Suite

---

## 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | `Toolkit->GetPreviewMeshComponent()` 반환 = `USkeletalMeshComponent*` 추측 | 실제 = `UDebugSkelMeshComponent*` (자손) |
| 2 | `AnimationBlueprintEditor` / `AnimationEditor` 도 같은 패턴 추측 | 각 에디터별 EditorName 검증 + 별도 인터페이스 |
| 3 | Persona Toolkit lifetime = ISkeletalMeshEditor lifetime 동등 | TSharedRef 라 Toolkit 만 살아남는 케이스 가능 — IsValid 검사 |
