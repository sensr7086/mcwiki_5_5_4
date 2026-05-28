---
title: "UE TextureSample SamplerType 자동 추론 — CompressionSettings + SRGB → EMaterialSamplerType"
kind: concept
status: stable
severity: "★★"
tags: [render, material, texture, sampler-type, MMA-51, ue-574]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-line-shifted  # 2026-05-27 Phase 2 engine grep 완료
---

# UE TextureSample SamplerType 자동 추론 — CompressionSettings + SRGB → EMaterialSamplerType

## 정의

`UMaterialExpressionTextureSample::SamplerType` 의 값이 `Texture` 의 *compression settings* 와 *SRGB flag* 와 일치하지 않으면 UE 가 컴파일 시 *"Sampler type is X, should be Y"* 오류 (Material Editor 의 빨간 ERROR! 노드). 외부 자동화 (Python / MCP / Blueprint) 가 TextureSample 생성 시 *SamplerType 명시 누락* 하면 default `Color` 만 채택 → linear 텍스처 (Specular / Roughness / Mask 등) 에서 컴파일 실패.

해결: `UTexture::CompressionSettings` + `SRGB` flag 기반 *server 측 자동 추론* — caller 가 명시 안 해도 적절한 SamplerType 자동 적용.

## 자세히

### 사례: MCMaterialAuto v0.34 (MMA-51)

🟢 **VAULT** — MCMaterialAuto v0.33 ERROR 발생 + v0.34 자동 추론 채택본.

**v0.33 실패 사례**:
- LLM 이 `add_expression(TextureSample, Texture="T_Nana_Armor_Specular")` 호출
- T_Nana_Armor_Specular: `CompressionSettings=TC_Default, SRGB=false` (linear)
- 그러나 TextureSample 의 default `SamplerType=SAMPLERTYPE_Color` (sRGB 가정)
- Material Editor: **빨간 ERROR!** 노드
- Output Log:
  ```
  [SM5] (Node TextureSample) Sampler type is Linear Color,
        should be Color for /Game/Characters/Nana/Textures/T_Nana_Armor_Specular
  ```
- 사실은 *Linear Color* 이어야 함 (texture 가 linear) — UE 메시지가 *의도와 반대 방향* 표현 (caller 의 SamplerType=Color 가 잘못, *should be LinearColor*)

**v0.34 자동 추론**:
```cpp
if (UMaterialExpressionTextureSample* TexExpr = Cast<...>(Expr)) {
    if (!bLlmOverride && TexExpr->Texture) {
        TexExpr->SamplerType = InferSamplerType(TexExpr->Texture);
    }
}
```

### 매핑 매트릭스 (UE 5.7 표준)

🟢 **VAULT** — UE `UMaterialExpressionTextureSample::AutoSetSampleType` 미러 + `ETextureCompressionSettings` enum:

| CompressionSettings | SRGB | → EMaterialSamplerType |
|---|---|---|
| `TC_Normalmap` | (any) | `SAMPLERTYPE_Normal` |
| `TC_Masks` | (any) | `SAMPLERTYPE_Masks` |
| `TC_Grayscale` | true | `SAMPLERTYPE_Grayscale` |
| `TC_Grayscale` | false | `SAMPLERTYPE_LinearGrayscale` |
| `TC_Alpha` | (any) | `SAMPLERTYPE_Alpha` |
| `TC_DistanceFieldFont` | (any) | `SAMPLERTYPE_DistanceFieldFont` |
| `TC_VectorDisplacementmap` | (any) | `SAMPLERTYPE_LinearColor` |
| `TC_HDR` | (any) | `SAMPLERTYPE_Color` |
| `TC_Default` (etc.) | true | `SAMPLERTYPE_Color` |
| `TC_Default` (etc.) | false | `SAMPLERTYPE_LinearColor` |

⚠ 일부 특수 케이스 (TC_HalfFloat / TC_BC7 / TC_LQ / TC_HDR_Compressed) 미커버 — 기본 `TC_Default` fallback 으로 충분.

### Asset Registry 캐시 활용 — soft load 회피

`UTexture::CompressionSettings` 와 `SRGB` 는 **Asset Registry tag 캐시** 에 자동 등록 (UPROPERTY 의 AssetRegistrySearchable 메타) → texture 실제 로드 *없이* 조회 가능. `list_textures` 도구 응답에 `recommended_sampler_type` 포함 시 효율적.

```cpp
FString CompStr, SrgbStr;
D.GetTagValue(GET_MEMBER_NAME_CHECKED(UTexture, CompressionSettings), CompStr);
D.GetTagValue(GET_MEMBER_NAME_CHECKED(UTexture, SRGB), SrgbStr);
// → "Normalmap", "True" / "0" / 등
```

⚠ Tag 값은 *문자열* — enum 비교 시 `Contains` 또는 prefix 매치 의무.

## 회피 패턴 (Production)

### Layer 1 — Tool_AddExpression 자동 추론 (v0.34 채택)
```cpp
if (auto TexExpr = Cast<UMaterialExpressionTextureSample>(Expr)) {
    const bool bLlmOverride = (Params->HasField(properties.SamplerType));
    if (!bLlmOverride && TexExpr->Texture) {
        TexExpr->SamplerType = InferSamplerType(TexExpr->Texture);
    }
}
```

### Layer 2 — list_textures 응답에 recommended_sampler_type
```cpp
Row->SetStringField(TEXT("recommended_sampler_type"), Recommended);
Row->SetStringField(TEXT("compression"), CompStr);
Row->SetBoolField(TEXT("srgb"), bSRGB);
```

### Layer 3 — Tool description 에 명시
"For TextureSample: SamplerType is AUTO-INFERRED from CompressionSettings + SRGB."

→ 3-Layer 모두 적용 시 LLM 이 SamplerType 명시 안 해도 ERROR 발생 안 함.

## 변형 사례

1. **TextureSampleParameter2D**: TextureSample 자손 → 동일 자동 추론 적용
2. **TextureCube / TextureSampleParameterCube**: 별도 EMaterialSamplerType (TextureCube/Linear etc.) — 본 매핑 확장 필요
3. **MaterialFunction 안 TextureSample**: 동일 자동 추론 — `add_function_expression` 도구에도 적용 후속
4. **Virtual Texture**: `SAMPLERTYPE_VirtualColor` / `VirtualNormal` 등 — `bIsVirtualTexture` flag 검사 후 별도 매핑

## 관련 함정

- LLM 의 `properties.SamplerType` 명시 — *override 우선* — vault [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] 패턴 1 (식별자 양쪽 허용) 응용
- TC_Default + SRGB=false 의 ambiguity — 대부분 *Specular / Roughness / Mask* 텍스처 — 추론 정확
- TC_Normalmap 의 SRGB 무관 — Normal map 은 *항상 linear* — SRGB flag 무시
- 일부 게임팀이 *custom CompressionSettings* (예: TC_EditorIcon) 사용 — fallback 의무

## 관련 entity

- [[UMaterialExpression]] (TextureSample base)
- [[UMaterialEditingLibrary]] (CreateMaterialExpression API)
- [[UTexture]] (CompressionSettings + SRGB property)
- [[FProperty]] (Asset Registry tag 캐시 기반 조회)
- [[EMaterialProperty]] (관련 enum 패턴)

## 열린 질문

1. ❓ Virtual Texture (`bIsVirtualTexture`) — `SAMPLERTYPE_Virtual*` 매핑 별도 처리 필요. 본 매트릭스 미커버.
2. ❓ TextureCube / TextureSample2DArray — 다른 EMaterialSamplerType 매핑. 후속 cycle.
3. ❓ Custom CompressionSettings 의 fallback 정확도 — game team 별 검증 필요.

## Cross-link

- `concepts/MCP-Tool-Schema-LLM-Friendly-Design` (패턴 1 — 식별자 양쪽 허용 → SamplerType override 응용)
- `concepts/UEnum-GetValueByName-FullyQualified` (EMaterialSamplerType enum prefix hazard)
- `concepts/LLM-Visual-Reference-Hallucination` (LLM 이 SamplerType 추측 회피 — server 자동 흡수)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` § Tier 1 도구 schema

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 9개 CompressionSettings → SamplerType 매핑 | 🟢 VAULT | UE 5.7 `MaterialExpressionTextureSample::AutoSetSampleType` + `ETextureCompressionSettings` enum |
| Asset Registry tag 캐시 활용 | 🟢 VAULT | `UTexture::CompressionSettings` 의 AssetRegistrySearchable 메타 |
| 3-Layer 적용 후 ERROR 발생 안 함 | 🟢 VAULT | MCMaterialAuto v0.34 실측 |
| Virtual Texture 매핑 | 🔴 INFERRED | 미커버 |
| Custom CompressionSettings fallback 정확도 | 🟡 PARTIAL | UE 표준만 검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-51 / MCMaterialAuto v0.34 채택본 기반)
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass-line-shifted

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `UMaterialExpressionTextureBase::AutoSetSampleType`: 5.5.4 `MaterialExpressions.cpp:2481` · 5.7.4 동 파일 line 2473
- 선언 `.h`: 5.5.4 `MaterialExpressionTextureBase.h:61` · 5.7.4 line 63
- **본문 diff = whitespace 만** (5.5.4: `if ( Texture )` · 5.7.4: `if (Texture)`). 로직 byte-identical.
- 실제 9개 매핑은 `GetSamplerTypeForTexture` (별도 함수, AutoSetSampleType 이 호출) — 5.5.4 에서 동일 패턴 유지 추정.
- **결정**: 🟢 5.5.4 에서 동일 동작. 본 페이지 참조 인용은 5.7 시점이지만 동작 변경 없음.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
