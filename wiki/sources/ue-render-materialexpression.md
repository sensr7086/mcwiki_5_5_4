---
type: source
title: "UE Render — MaterialExpression sub-skill (Custom Material Expression 깊이)"
slug: ue-render-materialexpression
source_path: raw/ue-wiki-llm/skills/Render/references/MaterialExpression.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-12
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
related_entities:
  - "[[entities/UMaterial]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, render, gpu, material, materialexpression, editor-only, slim-card]
citation_disclosure: "신뢰도 — raw §12 자기 신뢰도 표 기준: 🟢 [verified] 6건 (MaterialExpression virtual / FMaterialCompiler 578 / UMaterialExpressionCustom 구조 / MIR::FEmitter / Substrate virtual 458-470 / 269 파일 wc) · 🟡 [grep-listed] 1건 (FMaterialCompiler 카테고리 분류) · 🔴 [inferred] 2건 (269 expression 카테고리 그룹화 / SubstrateSlabBSDF 정확 시그니처)"
---

# UE Render — MaterialExpression (Custom Material Expression 깊이 🛠)

> Source: [[raw/ue-wiki-llm/skills/Render/references/MaterialExpression.md]] (526L)
> Parent: [[sources/ue-render-skill]] · 페어: [[sources/ue-render-material]] (자산 측) · [[sources/ue-render-shader]] (FGlobalShader 측)
> 외부 표준: [Epic Docs — Custom Material Expressions](https://dev.epicgames.com/documentation/en-us/unreal-engine/custom-material-expressions-in-unreal-engine)

## 1. Summary

UE 5.7.4 의 **Custom Material Expression 작성 표준** — Material Graph 노드의 C++ 깊은 작성 가이드. `UMaterialExpression` 자손 + `FMaterialCompiler` API + 5.x `MIR::FEmitter` Build 인터페이스 + Substrate 통합. 🛠 **Editor 전용** (`WITH_EDITOR` 가드 + 4단 분리 의무). 3가지 접근 — (a) `UMaterialExpressionCustom` 인라인 HLSL / (b) `UMaterialFunction` 재사용 / (c) `UMaterialExpression` 자손 C++ (가장 강력).

## 2. Key claims

### 2.1 3 가지 Custom 접근 결정 트리 🟢

| 접근 | 작성 위치 | 재사용 | Permutation 비용 |
|------|----------|--------|-----------------|
| (a) `UMaterialExpressionCustom` 인라인 | Material Graph 안 | 복사 X | 매 Material 별 (폭증 위험) |
| (b) `UMaterialFunction` | UMaterialFunction 어셋 | ✅ Shared | 한 번만 컴파일 |
| (c) ⭐ `UMaterialExpression` 자손 C++ | Editor 모듈 | ✅ Shared | 한 번만 + 5.x Substrate 통합 |

### 2.2 `UMaterialExpression` 핵심 virtual 후크 🟢 [verified]

raw `Engine/Public/Materials/MaterialExpression.h` 라인 명시:

| Virtual | 라인 | 역할 |
|---------|------|------|
| `Compile(FMaterialCompiler*, int32 OutputIndex)` | 270 | 컴파일 본체 (Cook / Editor 컴파일 시점 1회) |
| `Build(MIR::FEmitter&)` | 281 | 5.x 신규 — Material IR 빌더 (Compile() 후속) |
| `GetInputs()` / `GetInput(int32)` | — | 입력 핀 메타 |
| `GetOutputs()` / `GetOutput(int32)` | — | 출력 핀 메타 |
| `IsResultSubstrate()` | 458 | 5.x — Substrate BSDF 반환 여부 |
| `GenerateMaterialTopologyTree(...)` | 470 | 5.x — Substrate operator tree |

### 2.3 `FMaterialCompiler` API — **578** `int32` 메소드 🟢 [verified]

raw `Engine/Public/MaterialCompiler.h` grep 결과 578 메소드. 15+ 카테고리 — Constant / 산술 / 벡터 / 삼각 / 분기 / 텍스처 / 파티클 / Substrate 등. **카테고리별 메소드 분포는 🟡 [grep-listed]** (이름 패턴 추출, 정확한 그룹화 미검증).

> ⚠ **불일치 fix** (2026-05-12 vault 정합) — raw `description` 의 "600+" 표기는 라운드업. 본 vault 카드는 **578 통일** (raw §12 [verified] 기준).

### 2.4 `UMaterialExpressionCustom` 인라인 HLSL 노드 🟢 [verified]

raw `Engine/Public/Materials/MaterialExpressionCustom.h:64-115` — 구조:

- `Code` (FString) — 인라인 HLSL 본문
- `Inputs` (TArray<`FCustomInput`>) — 입력 매핑
- `AdditionalOutputs` (TArray<`FCustomOutput`>) — 추가 출력
- `AdditionalDefines` (TArray<`FCustomDefine`>) — #define 매크로
- `IncludeFilePaths` (TArray<FString>) — `#include "Plugin/Shaders/X.ush"` 등록

함정 — 매 Material 별 *고유 Permutation* → 동일 HLSL 을 N 머티리얼에서 쓰면 N 셰이더 빌드. 디자이너 재사용엔 (b) `UMaterialFunction` 권장.

### 2.5 5.x 신규 `MIR::FEmitter` Build 인터페이스 🟢 [verified]

raw `MaterialExpression.h:35-37` namespace 선언 + `:281` Build virtual:

- 기존 `Compile(FMaterialCompiler*)` 와 *병행* — 5.x 의 신규 Material IR 빌더
- `Build()` 는 IR (Intermediate Representation) 트리 생성 → 후단계에서 HLSL Translator 가 처리
- 마이그레이션 단계 — 일부 Expression 은 Compile / Build 둘 다 override (5.7.4 = 점진적 전환)

### 2.6 Substrate Material 5.x 통합 🟢 [verified — virtual] · 🔴 [inferred — Compile 시그니처]

raw `MaterialExpression.h:458-470` 의 4 virtual 검증됨:
- `IsResultSubstrate()` / `GatherSubstrateMaterialInfo()` / `GenerateMaterialTopologyTree()` / `SubstrateOperator()`

**Substrate Material 자체의 5.7.4 상태** — Production (UE 5.4 부터 정식 통합). raw 의 `[grep-listed]` 표기는 *Compile 패턴* (`SubstrateSlabBSDF` 등 정확 시그니처)의 신뢰도가 낮다는 의미 — feature 자체의 상태가 아님.

### 2.7 `UMaterialExpression` 자손 262종 🟢 [verified — 파일 수] · 🔴 [inferred — 카테고리 분류]

raw `ls Engine/Public/Materials/MaterialExpression*.h | wc -l` = **269 [verified]**. 카테고리 분류 (산술 35 / 벡터 15 / ...) 는 파일명 prefix 기반 — *정확한 그룹화 미검증* (🔴 INFERRED).

### 2.8 🚨 공통 정책 (5건)

| 정책 | 적용 |
|------|------|
| 🚨 [[concepts/Editor-Only-4-Tier-Separation]] | `UMaterialExpression` 자손 = Editor 모듈 + `WITH_EDITOR` 가드 의무 (4단 분리) |
| 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 | Editor 순수 모드 = 동기 로드 (`TryLoad`) |
| 🚨 Compile() 호출 시점 | Cook / Editor 컴파일 1회 — *런타임 X*. 무한 루프 / 비싼 연산 안전 X |
| 🚨 PSO Precache 5.x | Custom Expression 추가 시 Permutation 폭증 — `r.PSOPrecache=1` 의무 |
| 🚨 `GetReferencedTexture()` override | `Compiler->Texture(...)` 호출 시 — 텍스처 의존성 추적 의무 |

## 3. 함정 (12종 중 주요 5)

1. `Compile()` 안 비싼 연산 — Cook 시 멈춤 가능. `cache` 옵션 활용
2. `WITH_EDITOR` 가드 누락 — Cooked 빌드 컴파일 에러
3. `GetReferencedTexture` 미구현 — DDC 무효화 안 됨 (텍스처 변경 시 stale)
4. 인라인 Custom 의 Permutation 폭증 — `UMaterialFunction` 또는 C++ Expression 으로 분리
5. `MIR::Build()` 와 `Compile()` 불일치 — 5.x 마이그레이션 시 두 path 결과 동등성 검증 의무

## 4. 코드 예 (slim — 자손 C++ 표준)

```cpp
#if WITH_EDITOR
UCLASS()
class MYRENDEREDITOR_API UMyMaterialExpressionFoo : public UMaterialExpression
{
    GENERATED_BODY()
public:
    UPROPERTY()
    FExpressionInput Input;

    virtual int32 Compile(class FMaterialCompiler* Compiler, int32 OutputIndex) override
    {
        if (!Input.GetTracedInput().Expression)
        {
            return Compiler->Errorf(TEXT("UMyMaterialExpressionFoo: Input missing"));
        }
        const int32 InputCode = Input.Compile(Compiler);
        return Compiler->Add(InputCode, Compiler->Constant(1.0f));   // 예시
    }

    virtual void GetCaption(TArray<FString>& OutCaptions) const override
    {
        OutCaptions.Add(TEXT("My Foo Expression"));
    }
};
#endif
```

## 5. Cross-link

- 페어 — [[sources/ue-render-material]] (UMaterial 자산 + Translator) · [[sources/ue-render-shader]] (FGlobalShader / USF)
- 카테고리 — [[sources/ue-render-skill]] (Render main hub, 12→13 sub-skill)
- 자산 측 — [[entities/UMaterial]] · [[sources/ue-assetclasses-material]]
- 정책 — 🚨 [[sources/ue-ref-05-editoronlyindex]] (4단 분리) · 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 (Editor 동기) · 🚨 [[sources/ue-ref-07-profilingscopeRule]] (TRACE_CPUPROFILER)
- citation — [[00_meta/06_VaultCitationRule]] (3 tier 마커)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-editor-unrealed-materialeditor]] (inbound=3, suggest_missing_cross_link high confidence)
## 6. 신뢰도 매트릭스 (raw §12 정합)

| 항목 | Tier | 근거 |
|------|------|------|
| UMaterialExpression virtual 후크 (270/281/458/470) | 🟢 verified | `MaterialExpression.h:148-617` |
| FMaterialCompiler 578 메소드 | 🟢 verified | grep 578 매치 |
| UMaterialExpressionCustom 구조 | 🟢 verified | `MaterialExpressionCustom.h:64-115` |
| MIR::FEmitter namespace + Build | 🟢 verified | `MaterialExpression.h:35-37 / :281` |
| Substrate virtual 4종 | 🟢 verified | `MaterialExpression.h:458-470` |
| 269 expression 파일 | 🟢 verified | `wc -l` |
| FMaterialCompiler 카테고리 분류 | 🟡 grep-listed | 메소드 이름 패턴 sample |
| 269 expression 카테고리 그룹 | 🔴 inferred | 파일명 prefix 기반 |
| Substrate Compile 정확 시그니처 | 🔴 inferred | grep 검증 전 사용 금지 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 3
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 2
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 0

**주요 시그니처 변경**:
- `description: 🛠 Custom Material Expression 깊이 — UMaterialExpression 자손 작성 표준 + FM → description: 🛠 Custom Material Expression 깊이 — UMaterialExpression 자손 작성 표준 + FM`
- `> - **FMaterialCompiler** — `Engine/Source/Runtime/Engine/Public/MaterialCompile → > - **UMaterialExpression** — `Engine/Source/Runtime/Engine/Public/Materials/Mat`
- `> - **269 expressions** — `Engine/Public/Materials/MaterialExpression*.h` (Abs,  → > - **MIR::FEmitter** — 5.x 신규 Material IR 빌더 (`MaterialExpression.h:44` namespa`

**5.5.4 표현 (5.7.4 에 없음)**:
- `> - **FMaterialCompiler** — `Engine/Source/Runtime/Engine/Public/MaterialCompiler.h` (643 virtual, 548 `int32` 리턴 — 5.5.`
- `> - **262 expressions** — `Engine/Public/Materials/MaterialExpression*.h` (Abs, Add, ..., VirtualTexture — 5.5.4)`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/Render/references/MaterialExpression.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/Render/references/MaterialExpression.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **1 변경** (269종 → 262종)
- 정합 후 tier: **pass-body-reconciled**
