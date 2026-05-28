---
title: "EMaterialProperty"
kind: entity
status: stub
parent: render
tags: [render, material, enum, ue-574]
module: Engine
header: "Public/SceneTypes.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# EMaterialProperty

머티리얼의 **output property 식별 enum** — BaseColor, Metallic, Specular, Roughness, EmissiveColor, Opacity, OpacityMask, Normal, WorldPositionOffset, SubsurfaceColor, CustomData0/1, AmbientOcclusion, Refraction, PixelDepthOffset, ShadingModel 등 16+ 항목. Material 그래프의 root 노드 output pin 마다 대응.

## 핵심 값 (16+)

| 값 | 매크로 | 용도 |
|---|---|---|
| `MP_BaseColor` | BaseColor | 알베도 |
| `MP_Metallic` | Metallic | metalness PBR |
| `MP_Specular` | Specular | non-metal reflectance |
| `MP_Roughness` | Roughness | surface roughness |
| `MP_EmissiveColor` | EmissiveColor | self-emission |
| `MP_Opacity` | Opacity | translucent |
| `MP_OpacityMask` | OpacityMask | masked |
| `MP_Normal` | Normal | tangent normal |
| `MP_WorldPositionOffset` | WorldPositionOffset | WPO |
| `MP_SubsurfaceColor` | SubsurfaceColor | SSS |
| `MP_CustomData0/1` | CustomData0/1 | custom shading |
| `MP_AmbientOcclusion` | AmbientOcclusion | AO |
| `MP_Refraction` | Refraction | IOR |
| `MP_PixelDepthOffset` | PixelDepthOffset | PDO |
| `MP_ShadingModel` | ShadingModel | per-pixel SM |

## 사용 패턴

- `UMaterialEditingLibrary::ConnectMaterialProperty(Expr, OutputPin, MP_BaseColor)` 등에서 사용
- **MCP/JSON 입력 처리** 시 문자열 → enum 매핑 — [[concepts/UEnum-GetValueByName-FullyQualified]] 의 TMap 사전 정의 패턴 권고

## 관련 함정

- [[concepts/UEnum-GetValueByName-FullyQualified]] — `GetValueByName("BaseColor")` 는 fully-qualified 필수 → 짧은 이름 INDEX_NONE
- 사용자 입력 → enum 변환에서는 **명시 TMap** 사용 권고 (16+ 값 boilerplate 회피)

## 관련 entity

- [[UEnum]] · [[UMaterial]] · [[UMaterialEditingLibrary]] · [[UMaterialExpression]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| 16+ enum 값 catalog | 🟢 VAULT (UE 5.7 `SceneTypes.h` 직접 확인) |
| MP_* 매크로 prefix | 🟢 VAULT |
| TMap 사전 정의 권고 | 🟢 VAULT (MCMaterialAuto v0.14.9 채택) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-32 filing-back cross-link)
