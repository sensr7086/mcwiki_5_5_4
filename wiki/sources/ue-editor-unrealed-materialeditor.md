---
type: source
title: "UE Editor — UnrealEd / MaterialEditor sub-skill 🛠 (Material 노드 그래프 + 파라미터)"
slug: ue-editor-unrealed-materialeditor
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/MaterialEditor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/UMaterial]]"
  - "[[entities/UEdGraph]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, unrealed, materialeditor, umaterialgraph, umaterialexpression, parameter-value, dynamic-instance]
---

# UE Editor — UnrealEd / MaterialEditor sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/MaterialEditor.md]] · `UnrealEd/Classes/MaterialEditor/` + `UnrealEd/Classes/MaterialGraph/`

## 1. Summary

UnrealEd 안의 Material 에디터 **데이터 베이스 클래스** 모음 — 노드 그래프(`UMaterialGraph`) + 노드 (`UMaterialGraphNode`) + 파라미터 인스턴스 (`UDEditor*ParameterValue` 13종) + 미리보기. 두 부분: **`Classes/MaterialGraph/`** (그래프) + **`Classes/MaterialEditor/`** (파라미터 / 미리보기). Material 본체 위젯·툴바·뷰포트는 별도 `Engine/Source/Editor/MaterialEditor/` 모듈 (본 위키 미마운트). 🛠 **Editor 전용** + `WITH_EDITORONLY_DATA`. 단 `UMaterialExpression` 자체는 런타임도 컴파일러가 참조.

## 2. Key claims

### 2.1. Classes/MaterialGraph/ — 노드 그래프

| 클래스 | 베이스 | 의미 |
| -- | -- | -- |
| **`UMaterialGraph`** ⭐ | `UEdGraph` | Material 의 노드 그래프 |
| `UMaterialGraphNode_Base` | `UEdGraphNode` | 모든 Material 노드 베이스 |
| **`UMaterialGraphNode`** ⭐ | `UMaterialGraphNode_Base` | 표준 노드 (`UMaterialExpression` 래핑) |
| `UMaterialGraphNode_Root` | `UMaterialGraphNode_Base` | 메인 출력 (root) |
| `UMaterialGraphNode_Comment` | `UEdGraphNode_Comment` | 주석 |
| `UMaterialGraphNode_Composite` | `UMaterialGraphNode_Base` | 컴포지트 (서브그래프) |
| `UMaterialGraphNode_Custom` | `UMaterialGraphNode_Base` | Custom HLSL |
| `UMaterialGraphNode_Operator` | `UMaterialGraphNode_Base` | 연산자 |
| `UMaterialGraphNode_PinBase` | `UMaterialGraphNode_Base` | 핀 베이스 |
| `UMaterialGraphSchema` | `UEdGraphSchema` | 스키마 (노드 타입·연결 규칙) |

### 2.2. Classes/MaterialEditor/ — 파라미터 인스턴스 (13종) 🟢

`UDEditorParameterValue` 베이스. 디테일 패널에서 편집 가능한 파라미터 — Material Instance Constant 에디터의 노출:

| 클래스 | 타입 |
| -- | -- |
| `UDEditorScalarParameterValue` | float 스칼라 |
| `UDEditorVectorParameterValue` | FLinearColor (vec3/4) |
| `UDEditorDoubleVectorParameterValue` | double vec3 |
| `UDEditorTextureParameterValue` | `UTexture` |
| `UDEditorTextureCollectionParameterValue` | 텍스처 컬렉션 |
| `UDEditorFontParameterValue` | 폰트 |
| `UDEditorStaticSwitchParameterValue` | 스태틱 스위치 |
| `UDEditorStaticComponentMaskParameterValue` | 스태틱 컴포넌트 마스크 |
| `UDEditorMaterialLayersParameterValue` | 머티리얼 레이어 |
| `UDEditorRuntimeVirtualTextureParameterValue` | RVT |
| `UDEditorSparseVolumeTextureParameterValue` | SVT (5.x) |
| `UDEditorParameterCollectionParameterValue` | 파라미터 컬렉션 |
| `UMaterialEditorInstanceConstant` | Material Instance Constant 래퍼 |

**미리보기**: `UMaterialEditorMeshComponent` / `UMaterialEditorPreviewParameters` / `UPreviewMaterial`.

### 2.3. 새 Material Expression 작성 (런타임)

`UMaterialExpression` 자손 작성 → Material Editor 가 자동으로 `UMaterialGraphNode` 생성 (별도 GraphNode override 거의 불필요):

```cpp
// MyMaterialModule (Runtime, NOT Editor)
UCLASS()
class MYMATERIALMODULE_API UMaterialExpressionMyCustom : public UMaterialExpression
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Inputs") FExpressionInput A;
    UPROPERTY(EditAnywhere, Category="Inputs") FExpressionInput B;

    virtual int32 Compile(class FMaterialCompiler* Compiler, int32 OutputIndex) override;
    virtual void GetCaption(TArray<FString>& OutCaptions) const override;
    virtual FText GetCreationDescription() const override;
    virtual FText GetCreationName() const override;
};
```

`Compile` 가 HLSL 출력 — 자세히 → [[sources/ue-render-materialexpression]] (Phase 8 정밀 source).

### 2.4. Material Instance 동적 변경 (런타임)

```cpp
// 게임 런타임 (UnrealEd 의존 X)
UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMaterial, this);
MID->SetScalarParameterValue(TEXT("Health"), 0.5f);
MID->SetVectorParameterValue(TEXT("TintColor"), FLinearColor::Red);
```

`UDEditor*ParameterValue` 의 노출 ↔ 런타임 `SetScalarParameterValue` / `SetVectorParameterValue` 페어.

### 2.5. UMaterialGraph 커스텀 그래프 (드뭄)

표준 Material 에디터를 확장하지 않고 **커스텀 노드 그래프** 를 만들 때만 필요. UEdGraph / UEdGraphNode / UEdGraphSchema 자손 작성 패턴 → [[sources/ue-slate-grapheditor]] · [[sources/ue-slate-uedgraphapi]].

### 2.6. HLSL 컴파일 흐름

```
UMaterial (or UMaterialFunction)
   ↓ (사용자 편집)
UMaterialGraph (UEdGraph) + UMaterialGraphNode (UEdGraphNode)
   ↓ (`UMaterialExpression::Compile` 재귀)
FMaterialCompiler → HLSL
   ↓ (플랫폼별 셰이더 빌드 — DDC 캐시)
FShader (Material PSO)
```

Cooked 빌드: `UMaterialGraph` / `UMaterialGraphNode` 는 strip — `UMaterialExpression` 노드와 컴파일된 셰이더만 남음.

### 2.7. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `UMaterialExpression` 자손이 게임 빌드에서 빠짐 | Runtime 모듈에 배치 (Editor 아님) — 컴파일러가 런타임에서도 참조 |
| 2 | `UDEditor*ParameterValue` 직접 인스턴스화 | 에디터에서만 자동 생성 — 외부 생성 금지 |
| 3 | `UMaterialGraphNode::ReconstructNode` 호출 시 무한 루프 | Super FIRST 의무 |
| 4 | `Compile` 안 무거운 작업 시 스코프 누락 | [[sources/ue-ref-07-profilingscopeRule]] — 큰 머티리얼 컴파일 시간 측정 |
| 5 | `Classes/MaterialGraph/` 헤더를 게임 모듈에서 include | `WITH_EDITORONLY_DATA` — Editor 모듈만 |

### 2.8. Build.cs 🛠

`UnrealEd` + `RHI` + `Renderer` + `MaterialEditor` (별도 모듈). `Classes/MaterialEditor/` / `Classes/MaterialGraph/` 헤더는 Editor 전용 — 게임 빌드 strip.

## 3. Render 카테고리 페어

본 sub-skill 은 **Editor 측 표현** 만 다룸. 런타임 Material 시스템 + Custom Expression 의 HLSL 출력 + Substrate 5.x → [[sources/ue-render-materialexpression]] (Phase 8 Cycle #1 정밀 source 8.8 KB).

## 4. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-unrealed-kismet2]] (`UMaterialGraph` ↔ `FBlueprintEditorUtils` 동등 패턴) / [[sources/ue-editor-unrealed-asseteditortoolkit]] (`FMaterialEditor` 가 자손 — 별도 모듈) / [[sources/ue-slate-grapheditor]] (UEdGraph + 그래프 위젯) / [[sources/ue-slate-uedgraphapi]]
- Render 페어: [[sources/ue-render-materialexpression]] ⭐ (Cycle #1 8.8 KB — `Compile()` + `FMaterialCompiler` + Substrate) / [[sources/ue-render-material]] (Material Domain × ShadingModel) / [[sources/ue-render-shader]]
- 자산 페어: [[sources/ue-assetclasses-material]] · [[entities/UMaterial]]
- 횡단: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-04-overrideindex]] (UEdGraph virtual)
- CoreUObject: [[sources/ue-coreuobject-reflection]] (UPROPERTY → `FExpressionInput`)
