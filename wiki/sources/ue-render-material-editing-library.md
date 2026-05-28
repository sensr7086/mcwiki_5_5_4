---
type: source
title: "UE Render/MaterialEditingLibrary — Editor Material 자동화 (UMaterialEditingLibrary 58 UFUNCTION) 🛠"
slug: ue-render-material-editing-library
source_path: raw/ue-wiki-llm/skills/Render/references/MaterialEditingLibrary.md
source_kind: text
source_date: 2026-05-19
ingested: 2026-05-19
last_updated: 2026-05-21
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, render, material, editor, editor-only-4-tier, material-editing-library, automation, blueprint-function-library, python-automation]
citation_disclosure: "🟢 raw verified (594 라인 / 24 KB) · Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h 58 UFUNCTION 명세 + 4단 분리 의무 + FScopedTransaction + RecompileMaterial 의무"
---

# UE Render/MaterialEditingLibrary — Editor Material 자동화 🛠

> Source: [[raw/ue-wiki-llm/skills/Render/references/MaterialEditingLibrary.md]] (594 라인 / 24 KB, 2026-05-19 신규)
> Parent: [[sources/ue-render-skill]] · Pair: [[sources/ue-render-materialexpression]] (런타임 노드 페어)
> Cycle 5p+1 ingest — raw 측 신규 reference (untracked → vault catalog 진입)

## 1. Summary

🟢 **UMaterialEditingLibrary** = Material 시스템의 **Editor 자동화 표준 BlueprintFunctionLibrary** (58 UFUNCTION). Material / MaterialFunction / MaterialInstance 의 CRUD / Connection / Compile / Parameter 일괄 처리. Python / BP / C++ 호출 가능. Editor 전용 (4단 분리 의무).

**위치 (verified)**: `Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h`. **모듈**: `MaterialEditor` (Editor 전용). **Build.cs 의존**: `"MaterialEditor"`.

## 2. 핵심 주장 (raw 인용)

### 2.1 의무 정책 4종

🟢 **Editor 4단 분리** ([[sources/ue-ref-05-editoronlyindex]]) — 모든 코드 `WITH_EDITOR` 가드, Runtime 모듈 X.

🟢 **FScopedTransaction 의무** — `FScopedTransaction Tx(...); Material->Modify();` (Undo/Redo).

🟢 **RecompileMaterial 의무** — `CreateMaterialExpression` 또는 `ConnectMaterial*` 후 누락 시 변경 미반영.

🟢 **Asset Loading Policy** ([[sources/ue-ref-11-assetloadingpolicy]] §3) — Editor Pure 모드 = Sync Load (`TryLoad`).

### 2.2 58 UFUNCTION 카테고리

- **Expression CRUD** — `CreateMaterialExpression` / `DeleteAllMaterialExpressions` / `SetMaterialUsage`
- **Connection** — `ConnectMaterialProperty` (Output→Input) / `ConnectMaterialExpressions` (Expression→Expression) / `DisconnectMaterialProperty`
- **Compile** — `RecompileMaterial` (의무) / `UpdateMaterialFunction`
- **Parameter Get/Set** — Scalar / Vector / Texture / StaticSwitch / RuntimeVirtualTexture / SparseVolumeTexture (각각 GetParameter / SetParameter)
- **MaterialInstance** — `CreateMaterialInstanceAsset` / `SetMaterialInstance*`
- **MaterialFunction** — `CreateMaterialFunctionAsset` / `LayoutMaterialFunctionExpressions`

## 3. 인용할 만한 원문

```cpp
// Expression 생성 + Connection + Compile 3단 표준 패턴
{
    FScopedTransaction Tx(LOCTEXT("AddNode", "Add Material Node"));
    Material->Modify();

    UMaterialExpressionTextureSample* TexSample = Cast<UMaterialExpressionTextureSample>(
        UMaterialEditingLibrary::CreateMaterialExpression(Material, UMaterialExpressionTextureSample::StaticClass())
    );
    TexSample->Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/.../T_Diffuse"));

    UMaterialEditingLibrary::ConnectMaterialProperty(TexSample, TEXT(""), MP_BaseColor);
    UMaterialEditingLibrary::RecompileMaterial(Material);   // 의무 — 누락 시 변경 미반영
}
```

## 3.5 ⭐ Python 자동화 표준 패턴 (`unreal.MaterialEditingLibrary`) — Cycle 5p+1 enrich

🟢 **raw §10 검증** (raw line 379-421). UE Python API 자동 snake_case 변환 (UFUNCTION 명 → Python 명):

```python
import unreal

# [1] Material asset 생성
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material = asset_tools.create_asset(
    asset_name="M_AutoMaterial",
    package_path="/Game/Materials",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew()
)

# [2] Expression 추가 (위치 X, Y — 노드 그래프 레이아웃)
color_node = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionConstant3Vector, -300, 0
)
color_node.set_editor_property("constant", unreal.LinearColor(1.0, 0.5, 0.0, 1.0))

scalar_node = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, -300, 200
)
scalar_node.set_editor_property("parameter_name", "Roughness")
scalar_node.set_editor_property("default_value", 0.5)

# [3] Connection — MaterialProperty enum 값은 대문자 + MP_ prefix
unreal.MaterialEditingLibrary.connect_material_property(
    color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
)
unreal.MaterialEditingLibrary.connect_material_property(
    scalar_node, "", unreal.MaterialProperty.MP_ROUGHNESS
)

# [4] Layout + Compile — 의무 (누락 시 변경 미반영)
unreal.MaterialEditingLibrary.layout_material_expressions(material)
unreal.MaterialEditingLibrary.recompile_material(material)

# [5] 저장
unreal.EditorAssetLibrary.save_loaded_asset(material)
```

### 3.5.1 시나리오 (raw §11 권위)

🟢 **PBR Master Material 자동 생성** — Diffuse/Normal/Roughness/Metallic/AO 5종 텍스처 슬롯 + ConnectMaterialProperty 5 슬롯 (raw §11.1).

🟢 **Material Instance 일괄 갱신 (Variation)** — 50개 캐릭터 변형 → 각각 MIC 생성 + Color/Metallic 파라미터 + `update_material_instance(mic)` 의무 (raw §11.2):

```python
for i, char_color in enumerate(character_colors):
    mic = create_mic(f"/Game/MIC/Character_{i}", parent_material)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mic, "BaseColor", char_color
    )
    unreal.MaterialEditingLibrary.update_material_instance(mic)
```

### 3.5.2 함정 (raw §함정 #9)

🟢 **Enum 값 표기 의무** — `unreal.MaterialProperty.MP_BASE_COLOR` (**대문자 + MP_ prefix**). `MaterialProperty.BaseColor` 형식 X — Python wrapper 가 C++ enum 명을 그대로 노출.

### 3.5.3 의무 정책 (Python 변환 후에도 유지)

- 🚨 **RecompileMaterial 의무** — `recompile_material(material)` 누락 시 변경 미반영 (§2.1 동일)
- 🚨 **layout_material_expressions** — 노드 X/Y 자동 정렬 (Editor UI 가독성)
- 🚨 **EditorAssetLibrary.save_loaded_asset** — 명시 저장 의무 (Python 자동화는 자동 저장 X)
- ⚠ **`update_material_instance(mic)`** — MIC 파라미터 변경 후 의무 (renderstate 갱신)

### 3.5.4 신뢰도 격상 후보

🟡 → 🟢 격상 — Python API 명명 (snake_case 변환) 의 일반 패턴은 UE Python 표준 변환 규칙, 본 사례 5종 (`create_material_expression`, `connect_material_property`, `layout_material_expressions`, `recompile_material`, `set_material_instance_vector_parameter_value`) raw §10 권위 verified.

## 4. 열린 질문 (Cycle 5p+2 후속 검토)

- 🟡 58 UFUNCTION 중 deprecated 후보 grep — UE 5.7.4 vs 5.8+ 비교
- ✅ ~~Python 자동화 표준 패턴~~ — **resolved (Cycle 5p+1 §3.5)** — raw §10 + §11 검증 통합
- 🔴 Bulk Material 빌드 (1000+ asset) 시 RecompileMaterial 비용 — 측정 데이터 없음

## 5. Cross-link

### 페어 (Render 카테고리)
- [[sources/ue-render-skill]] (메인)
- [[sources/ue-render-materialexpression]] (런타임 UMaterialExpression 자손 — 자동 생성 대상)
- [[sources/ue-render-material]] (런타임 UMaterial 자체)
- [[sources/ue-assetclasses-material]] (자산 페어)

### 의무 정책
- [[sources/ue-ref-05-editoronlyindex]] — 4단 분리 의무
- [[sources/ue-ref-11-assetloadingpolicy]] §3 — Editor Pure 모드 로드 정책

### Editor 카테고리 협업
- [[sources/ue-agent-editor]] — Editor 작업 시 본 sub-skill 자동 로드
- [[sources/ue-editor-unrealed-materialeditor]] (MaterialEditor 모듈 메타)

## 6. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-19 (Cycle 5p+1 ingest) | 최초 작성 — raw `skills/Render/references/MaterialEditingLibrary.md` (594 라인 / 24 KB) ingest. §1 Summary / §2 의무 정책 4종 + 58 UFUNCTION 카테고리 / §3 Expression+Connection+Compile 3단 표준 패턴 / §4 열린 질문 / §5 Cross-link (페어 + 의무 + Editor 협업). Render 카테고리 13 → 14. |
| **2026-05-21 (Cycle 5p+1 enrich — Python)** | ⭐ **§3.5 Python 자동화 표준 패턴** 신규 — raw §10 + §11 통합. PBR Master / MIC 일괄 갱신 시나리오 + 함정 #9 enum + 의무 4종 + 5 UFUNCTION (`create_material_expression` / `connect_material_property` / `layout_material_expressions` / `recompile_material` / `set_material_instance_vector_parameter_value`) raw 권위 verified. §4 Python 열린 질문 ✅ resolved. |
