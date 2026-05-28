---
name: render-material
description: UMaterial / USF / Material Domain 7종 + ShadingModel 12종 + Material Expression 진입점. 머티리얼 컴파일 흐름 (HLSL Translator → USF → Cooked PSO) + 5.x PSO Precache 통합. Custom Material Expression 깊이 = references/MaterialExpression.md. AssetClasses/Material 의 Render 측 페어.
---

# Render/Material — UMaterial 컴파일 + USF + Custom HLSL

> **위치 (5.5.4)**: 자산 = `Engine/Source/Runtime/Engine/Public/Materials/Material.h` 등 (`Classes/` 아님) + Render = `Engine/Source/Runtime/Renderer/Public/MaterialShader.h` + `RenderCore/Public/ShaderMaterial.h` + USF = `Engine/Shaders/`
> **요지**: Material 시스템의 **Render 측 깊이** — UMaterial 어떻게 USF / HLSL 로 변환되어 GPU 에서 실행되는지. AssetClasses/Material (자산 측) 과 페어.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 PSO Precache (5.x) | 모든 Material 사용 패턴 = `r.PSOPrecache=1` 활성 의무 |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §2 | MIC vs MID 결정 + Material Quality Level |
| 🚨 Cooked Build | Material Compilation = Cook 시점 (런타임 X) — Custom Material 추가 시 Cook 시간 ↑ |

---

## 1. Material Domain 7종

| Domain | 용도 | Shader 단계 |
|--------|------|-----------|
| `MD_Surface` ⭐ | 일반 Surface (Static/Skeletal Mesh) | VS + PS + (DS/HS Tessellation) |
| `MD_DeferredDecal` | Deferred Decal | PS |
| `MD_LightFunction` | Light 함수 | PS |
| `MD_Volume` | Volume Fog 등 | VS + PS |
| `MD_PostProcess` | Material Post Process Pass | PS |
| `MD_UI` | UMG / Slate UI | PS |
| `MD_RuntimeVirtualTexture` | RVT 출력 | PS |

---

## 2. Material Compilation 흐름

```
[Editor]
UMaterial::PostEditChangeProperty
  ↓
FHLSLMaterialTranslator::Translate
  ↓ Material Expression Graph → HLSL
.usf 파일 생성 (Generated/Material_X.usf)
  ↓
FShaderCompilerWorker (별도 프로세스)
  ↓ HLSL → DXIL/SPIR-V/MSL (플랫폼별)
DDC 캐시 (Derived Data Cache)
  ↓
FMaterialShaderMap 등록

[Cooked Build]
Cook 시점 = 모든 Material × Permutation × Quality 컴파일
  ↓
Cooked DDC + Pak 안 저장
  ↓
런타임 = 컴파일 X, 로드만
```

---

## 3 ~ 4 Material Expression — [`MaterialExpression.md`](./MaterialExpression.md) ✂️

**Custom Material Expression 깊이** = 별도 sub-skill 로 분리. 본 메인은 요약만:

| 접근 | 사용 시점 | 상세 |
|------|----------|------|
| **(a) `UMaterialExpressionCustom` 인라인 HLSL** | 그래프 안 작은 수식 | [`MaterialExpression.md §5`](./MaterialExpression.md#5-umaterialexpressioncustom--인라인-hlsl-노드-verified) |
| **(b) `UMaterialFunction`** | 재사용 / 디자이너 변경 | (Material Editor 자산) |
| **(c) `UMaterialExpression` 자손 C++** ⭐ | 새 노드 타입 / Substrate 통합 / GBuffer | [`MaterialExpression.md §3`](./MaterialExpression.md#3-compile-표준-패턴-가장-중요-) |

**`MaterialExpression.md` 가 다루는 깊이**:
- **UMaterialExpression virtual 후크** — Compile / Build (5.x MIR) / GetInput / GetOutput / IsResultSubstrate
- **FMaterialCompiler 578 `int32` 메소드** — Constant / 산술 / 벡터 / 삼각 / 텍스처 / 파티클 / Substrate 등 15+ 카테고리
- **269 Material Expression 카테고리 분류**
- **Substrate 5.x 통합** — `SubstrateSlabBSDF` / `SubstrateUnlitBSDF` / Topology Tree
- **Editor 모듈 분리 4단** + 함정 12종

---

## 5. 5.x PSO Precache (의무)

### 5.1 동작
- 5.x = 모든 Material × Vertex Factory × LOD × Pass 조합 = PSO 가 사전 컴파일 필요
- 미사용 시 = 첫 Render 시 PSO Compile Stall (수십~수백 ms 히칭)

### 5.2 활성

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.PSOPrecache=1
r.PSOPrecaching.LazyLoadShadersWhenPSOPrecacheRequested=0
```

```cpp
// 사용 패턴 등록 (Material 사용 시점)
if (auto* Mesh = SkelMeshComp->GetSkeletalMeshAsset())
{
    Mesh->PrecachePSOs(SkelMeshComp->GetVertexFactoryType(), SkelMeshComp);
}
```

→ 자세한: [`AssetClasses/references/Material.md`](../../AssetClasses/references/Material.md) §5.

---

## 6. Material Quality Level

```cpp
// 5 단계 — Material Editor 안 Material Quality 노드
EMaterialQualityLevel::Low
EMaterialQualityLevel::Medium
EMaterialQualityLevel::High
EMaterialQualityLevel::Epic        // 5.x — Cinematic
EMaterialQualityLevel::Num
```

```hlsl
// USF 안에서 Quality 분기
#if (MATERIAL_QUALITY_LEVEL == MATERIAL_QUALITY_LEVEL_LOW)
    // 저사양 패스
#else
    // 고사양 패스
#endif
```

---

## 7. ShadingModel 12종 (5.x)

| ShadingModel | 용도 |
|--------------|------|
| `Unlit` | 라이트 영향 X (UI / Particle) |
| `DefaultLit` ⭐ | 일반 PBR |
| `Subsurface` | SSS (피부 / 양초) |
| `PreintegratedSkin` | 사전 적분 스킨 |
| `ClearCoat` | 코팅 (자동차 페인트) |
| `SubsurfaceProfile` | 5.x — 더 정밀 SSS |
| `TwoSidedFoliage` | 양면 라이팅 (잎) |
| `Hair` | 머리카락 |
| `Cloth` | 천 |
| `Eye` | 눈 |
| `SingleLayerWater` | 5.x — 물 (단일 레이어) |
| `ThinTranslucent` | 5.x — 얇은 반투명 |

---

## 8. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UMaterial 매번 새로 생성 (런타임) | UMaterialInstanceDynamic 사용 (CreateDynamicMaterialInstance) |
| 2 | MIC (Constant) 런타임 변경 | MID (Dynamic) 사용 — MIC = 디자이너 / 런타임 변경 X |
| 3 | Custom HLSL = 매 Material 별 Permutation 폭증 | Material Function 으로 공유 |
| 4 | 5.x PSO Precache 비활성 — 첫 Render 히칭 | `r.PSOPrecache=1` + 사용 패턴 등록 |
| 5 | Cooked Build Custom HLSL 에러 = 런타임 검출 | 개발 중 Cooked Build 검증 의무 |
| 6 | UMaterialExpression Custom = Runtime 모듈 | Editor 모듈 분리 (4단 분리) |
| 7 | 5.x Lumen + Custom HLSL 충돌 | Custom 노드 안 Lumen 호환 검사 |
| 8 | Material Quality 미고려 → Mobile 60fps 못 맞춤 | Quality 분기 의무 (Low / Medium 분리) |

---

## 9. 체크리스트

- [ ] Material Domain 정확 (Surface / PostProcess / UI 등)
- [ ] MIC vs MID 결정 (디자이너 vs 런타임)
- [ ] Custom HLSL = Material Function 공유 우선
- [ ] PSO Precache 활성 + 사용 패턴 등록 (5.x)
- [ ] UMaterialExpression Custom = Editor 모듈 분리
- [ ] Cooked Build 검증 (개발 중)
- [ ] ShadingModel 정확 (5.x 신규 4종 인지)
- [ ] Material Quality 분기 (Mobile 대응)

---

## 10. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- ⭐ [`Render/references/MaterialExpression.md`](./MaterialExpression.md) — **Custom Material Expression 깊이** (UMaterialExpression virtual + FMaterialCompiler 578 메소드 + UMaterialExpressionCustom + Substrate 5.x + 269 표현식)
- **자산 페어**: [`AssetClasses/references/Material.md`](../../AssetClasses/references/Material.md) — UMaterial / MIC / MID / 5.x PSO Precache
- [`Render/references/Shader.md`](./Shader.md) — FMaterialShader (Material 컴파일 결과)
- [`Render/references/PostProcess.md`](./PostProcess.md) — MD_PostProcess Material
- [`Editor/SKILL.md`](../../Editor/SKILL.md) — UMaterialExpression Editor 모듈

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. Material Domain 7종 + Compilation 흐름 + Custom HLSL 노드 + UMaterialExpression 작성 + 5.x PSO Precache + Quality 5단 + ShadingModel 12종 + 함정 8대. |
| 2026-05-12 | **§3~§4 슬림화** — Custom Material Expression 깊이를 [`MaterialExpression.md`](./MaterialExpression.md) 로 분리 (Level 3 progressive disclosure). 새 sub-skill = 표현식 269종 + FMaterialCompiler 578 메소드 + UMaterialExpressionCustom + Substrate 5.x. |
