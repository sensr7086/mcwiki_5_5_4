---
name: unrealed-materialeditor
description: 🛠 IMaterialEditor + UMaterialGraph + UMaterialGraphNode - 머티리얼 에디터 통합.
---

# UnrealEd · MaterialEditor sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용) — `Classes/MaterialEditor/` + `Classes/MaterialGraph/`
> **다루는 범위**: Material 에디터의 노드 그래프 + 파라미터 인스턴스 + 미리보기 클래스. 본격 Material 에디터 위젯은 별도 `MaterialEditor` 모듈 (미마운트).

---

## 1. 개요

UnrealEd 안에 Material 에디터의 **데이터 베이스 클래스** 가 모여 있다. 노드 그래프(`UMaterialGraph`) 와 노드 (`UMaterialGraphNode`) 는 Engine 모듈의 `UEdGraph`/`UEdGraphNode` 자손 ([`Slate/GraphEditor`](../../Slate/references/GraphEditor.md) 참조).

Material 본체 위젯·툴바·뷰포트는 별도 `Engine/Source/Editor/MaterialEditor/` 모듈 (본 위키 미마운트).

---

## 2. 두 부분

### 2.1 Classes/MaterialGraph/ — 노드 그래프

| 클래스 | 베이스 | 의미 |
|--------|--------|------|
| `UMaterialGraph` | `UEdGraph` | Material의 노드 그래프 |
| `UMaterialGraphNode_Base` | `UEdGraphNode` | 모든 Material 노드 베이스 |
| `UMaterialGraphNode` | `UMaterialGraphNode_Base` | 표준 노드 (`UMaterialExpression` 래핑) |
| `UMaterialGraphNode_Root` | `UMaterialGraphNode_Base` | 메인 출력 (root) |
| `UMaterialGraphNode_Comment` | `UEdGraphNode_Comment` | 주석 |
| `UMaterialGraphNode_Composite` | `UMaterialGraphNode_Base` | 컴포지트 (서브그래프) |
| `UMaterialGraphNode_Custom` | `UMaterialGraphNode_Base` | 커스텀 HLSL |
| `UMaterialGraphNode_Operator` | `UMaterialGraphNode_Base` | 연산자 |
| `UMaterialGraphNode_PinBase` | `UMaterialGraphNode_Base` | 핀 베이스 |
| `UMaterialGraphSchema` | `UEdGraphSchema` | 스키마 (노드 타입·연결 규칙) |

### 2.2 Classes/MaterialEditor/ — 파라미터 인스턴스 + 미리보기

| 클래스 | 의미 |
|--------|------|
| `UDEditorParameterValue` (베이스) | 디테일 패널에서 편집 가능한 파라미터 |
| `UDEditorScalarParameterValue` | 스칼라 |
| `UDEditorVectorParameterValue` | 벡터3 |
| `UDEditorDoubleVectorParameterValue` | 벡터3 (double) |
| `UDEditorTextureParameterValue` | 텍스처 |
| `UDEditorTextureCollectionParameterValue` | 텍스처 컬렉션 |
| `UDEditorFontParameterValue` | 폰트 |
| `UDEditorStaticSwitchParameterValue` | 스태틱 스위치 |
| `UDEditorStaticComponentMaskParameterValue` | 스태틱 컴포넌트 마스크 |
| `UDEditorMaterialLayersParameterValue` | 머티리얼 레이어 |
| `UDEditorRuntimeVirtualTextureParameterValue` | RVT |
| `UDEditorSparseVolumeTextureParameterValue` | SVT |
| `UDEditorParameterCollectionParameterValue` | 파라미터 컬렉션 |
| `UMaterialEditorInstanceConstant` | Material Instance Constant 에디터 래퍼 |
| `UMaterialEditorMeshComponent` | 미리보기 메시 컴포넌트 |
| `UMaterialEditorPreviewParameters` | 미리보기 파라미터 |
| `UPreviewMaterial` | 미리보기 머티리얼 |

---

## 3. 자주 쓰는 패턴

### 3.1 새 Material Expression (Material 노드 추가)

런타임 `UMaterialExpression` 자손 작성 + Material Editor 가 자동으로 `UMaterialGraphNode` 생성:

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

`UMaterialGraphNode` 가 자동으로 이를 래핑해 Material 에디터에 노드로 표시. 별도 GraphNode override 거의 불필요.

### 3.2 Material Instance 파라미터 동적 변경 (런타임)

```cpp
// 게임 런타임 (UnrealEd 의존 X)
UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMaterial, this);
MID->SetScalarParameterValue(TEXT("Health"), 0.5f);
MID->SetVectorParameterValue(TEXT("TintColor"), FLinearColor::Red);
```

### 3.3 디테일 패널 커스터마이징

`UDEditorScalarParameterValue` 등의 디테일 패널 표시는 `MaterialEditor` 모듈의 IDetailCustomization 처리. 본 sub-skill 범위 외.

---

## 4. UMaterialGraph / UMaterialGraphNode 작성 (커스텀 그래프)

표준 Material 에디터를 확장하지 않고 커스텀 노드 그래프를 만들 때만 필요. 자세한 패턴은 [`Slate/GraphEditor`](../../Slate/references/GraphEditor.md) — `UEdGraph`/`UEdGraphNode`/`UEdGraphSchema` 자손 작성 패턴.

---

## 5. 함정

| 함정 | 회피 |
|------|------|
| `UMaterialExpression` 자손이 게임 빌드에 포함 | Material Expression 은 런타임 — `WITH_EDITORONLY_DATA` 가드 X (런타임에서도 컴파일러가 사용) |
| `UDEditor*ParameterValue` 직접 인스턴스화 | 에디터에서만 자동 생성 — 외부에서 만들면 안 됨 |
| `UMaterialGraphNode::ReconstructNode` 호출 시 무한 루프 | 베이스 호출 (Super FIRST) |
| `Compile` 안 무거운 작업 시 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) — 큰 머티리얼은 컴파일 시간 측정 권장 |

---

## 6. 에디터 전용 🛠

`Classes/MaterialEditor/` 의 `UDEditor*` 와 `UMaterialEditor*` 는 에디터 전용. `Classes/MaterialGraph/` 의 `UMaterialGraph`/`Node` 도 에디터 전용 (`WITH_EDITORONLY_DATA`). `UMaterialExpression` 자체는 런타임도 컴파일러가 참조.

---

## 7. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — 메인
- [`Slate/GraphEditor`](../../Slate/references/GraphEditor.md) — UEdGraph 런타임 + GraphEditor 위젯 (Material 그래프의 베이스)
- [`CoreUObject/Reflection`](../../CoreUObject/references/Reflection.md) — UPROPERTY (`UMaterialExpression` 입력)
- 향후: `MaterialEditor` 모듈 (별도, 미마운트) — Material 에디터 위젯/툴바
- 교차: [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
