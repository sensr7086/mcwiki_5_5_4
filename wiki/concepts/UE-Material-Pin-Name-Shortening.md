---
title: "UE Material Pin Name Shortening — GetShortenPinName 9개 매핑 hazard"
kind: concept
status: stable
severity: "★★★"
tags: [render, material, pin-name, connect-expression, MMA-48, MMA-45, hazard, ue-574]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-line-shifted  # 2026-05-27 Phase 2 engine grep 완료
---

# UE Material Pin Name Shortening — `GetShortenPinName` 9개 매핑 hazard

## 정의

UE 5.7 의 `UMaterialEditingLibrary::ConnectMaterialExpressions(From, FromOut, To, ToInputName)` 가 **`ToInputName` 인자를 expression 의 *원본 property 이름* 그대로 비교하지 않는다**. 내부적으로 `UMaterialGraphNode::GetShortenPinName(rawName)` 을 적용한 *축약 이름* 으로만 매치한다. 9개 input pin 이름이 *별칭으로 축약* 되어 있고, *원본 property name 으로 호출 시 모두 거부* 된다.

LLM / 외부 자동화가 reflection 으로 얻은 `FStructProperty::GetName()` (= 원본 property 이름) 을 `ToInputName` 으로 그대로 전달하면 — 해당 9개에 대해 *silent rejection* (false 반환).

## 자세히

### 9개 매핑 매트릭스 (UE 5.7 source 직접 확인)

🟢 **VAULT** — `Engine/Source/Editor/UnrealEd/Private/MaterialGraphNode.cpp:596` (UMaterialGraphNode::GetShortenPinName):

| 원본 property name | UE 축약 (실제 ConnectMaterialExpressions 비교에 사용) | 영향 expression 예시 |
|---|---|---|
| `Coordinates` | `UVs` | TextureSample / TextureSampleParameter2D |
| `TextureObject` | `Tex` | TextureSample / TextureObject |
| **`Input`** | **`NAME_None` (빈 이름)** | Saturate / ComponentMask / OneMinus / Abs / Negate / Frac / Floor / Ceil / Round |
| **`Exponent`** | **`Exp`** | Power |
| `AGreaterThanB` | `CompactAGreaterThanB` | If |
| `AEqualsB` | `CompactAEqualsB` | If |
| `ALessThanB` | `CompactALessThanB` | If |
| `MipLevel` | `Level` | TextureSample with MipValue mode |
| `MipBias` | `Bias` | TextureSample with MipBias mode |

⚠ 위 9개 외 input pin (`A` / `B` / `Base` / `Min` / `Max` / `Alpha` 등) 은 *property name 과 축약 이름이 동일* — 매핑 무관 정상 동작.

### 호출 흐름

🟢 **VAULT** — `Engine/Source/Editor/MaterialEditor/Private/MaterialEditingLibrary.cpp`:

```
UMaterialEditingLibrary::ConnectMaterialExpressions(From, FromOut, To, ToInputName)
  ↓
GetExpressionInputByName(To, FName(ToInputName))                   ← L700
  ↓ (이 함수 내부 — L45)
for (FExpressionInputIterator It{Expression}; It; ++It)
  rawName  = Expression->GetInputName(It.Index)                    ← property 이름
  testName = UMaterialGraphNode::GetShortenPinName(rawName)        ← 축약 적용 ★
  if (testName == InputName) return It.Input                        ← 매치는 *축약 이름* 으로
return nullptr                                                       ← 매치 실패 → caller 가 false 반환
```

→ caller 가 `"Exponent"` 전달 시 → `testName="Exp"` 와 비교 → 매치 실패 → `nullptr` 반환 → `ConnectMaterialExpressions` 가 false.

### 사례 1: Power.Exponent ScalarParameter 거부 (MMA-48)

🟢 **VAULT** — MCMaterialAuto v0.23 실측 (사용자 cycle log):

LLM 의 시도 흐름:
1. read_material → Power expression 의 input pin = `Exponent` 인식
2. `connect_expression_to_expression(... dst_input="Exponent")` 호출
3. **서버 거부** — *"입력 핀명은 valid한데 거부"* (사용자 인식)
4. LLM 우회: `ConstExponent=4.0` 직접 fixed value 적용 → 파라미터 노출 안 됨

진짜 메커니즘: UE 가 `GetShortenPinName("Exponent")` → `"Exp"` 와 비교 → 실패.

### 사례 2: 단일 input expression (MMA-45 의 진짜 메커니즘)

🟢 **VAULT** — MCMaterialAuto v0.22 실측 (log line 143):

`Saturate` / `ComponentMask` / `OneMinus` 등의 input pin property name 이 모두 *`"Input"`* (single FExpressionInput). 
- `GetShortenPinName("Input")` → `NAME_None` (빈 이름)
- LLM 이 `dst_input="Input"` 보내면 → UE 가 `""` 와 비교 → 실패
- 사용자가 ad-hoc 발견한 *"빈 문자열로 줘야 동작"* 의 정확한 원인이 이것

v0.22 의 MMA-45 fix 는 *증상 대응* (LLM 가이드 + valid list "(empty=default)" 표시) — 근본 원인은 본 MMA-48 의 9개 매핑 중 1건.

## 회피 패턴 (Production)

### Fix 1 — Caller 측 자동 정규화 (MCMaterialAuto v0.23 채택)

```cpp
static FName GetShortenedInputName(FName PinName)
{
    if (PinName == FName(TEXT("Coordinates")))   return FName(TEXT("UVs"));
    if (PinName == FName(TEXT("TextureObject"))) return FName(TEXT("Tex"));
    if (PinName == FName(TEXT("Input")))         return NAME_None;
    if (PinName == FName(TEXT("Exponent")))      return FName(TEXT("Exp"));
    if (PinName == FName(TEXT("AGreaterThanB"))) return FName(TEXT("CompactAGreaterThanB"));
    if (PinName == FName(TEXT("AEqualsB")))      return FName(TEXT("CompactAEqualsB"));
    if (PinName == FName(TEXT("ALessThanB")))    return FName(TEXT("CompactALessThanB"));
    if (PinName == FName(TEXT("MipLevel")))      return FName(TEXT("Level"));
    if (PinName == FName(TEXT("MipBias")))       return FName(TEXT("Bias"));
    return PinName;
}

// ConnectMaterialExpressions 호출 전 자동 변환:
const FString Normalized = GetShortenedInputName(FName(*Raw)).ToString();
UMaterialEditingLibrary::ConnectMaterialExpressions(From, FromOut, To, Normalized);
```

✅ caller 가 property name (`"Exponent"`) 또는 축약 (`"Exp"`) 둘 다 전달 가능 — 모두 정상 동작.

### Fix 2 — `Expression->GetInput(0)` 직접 호출 (단일 input 한정)

단일 input 의 경우 `ToInputName = NAME_None` 으로 전달하면 `GetExpressionInputByName` 의 line 51-54 가 *첫 input 자동 반환*:
```cpp
if (InputName.IsNone())  return Expression->GetInput(0);
```

✅ `dst_input=""` 으로 항상 단일 input 작동 보장.

### Fix 3 — Reflection 시 미리 축약 이름 enumerate

외부 자동화 (LLM 등) 에 valid input list 노출 시 *축약 이름* 으로 반환:
```cpp
for (TFieldIterator<FStructProperty> It(Expr->GetClass()); It; ++It)
{
    if (!IsExpressionInput(*It)) continue;
    FName Short = GetShortenedInputName(FName(It->GetName()));
    OutValidNames.Add(Short.IsNone() ? TEXT("(empty=default)") : Short.ToString());
}
```

LLM 이 받은 list (예: `["Base", "Exp"]` for Power) 를 그대로 dst_input 으로 사용 가능.

## 변형 사례

1. **다른 base 함수**: `GetExpressionOutputIndexByName` 도 비슷한 처리 (`MaterialEditingLibrary.cpp:80-`) — output name 의 R/G/B/A 자동 매핑. 별도 hazard.
2. **MaterialFunctionCall input**: `UMaterialExpressionMaterialFunctionCall::GetInputNameWithType` 사용 (postfix 제거) — 또 다른 매핑 layer. 별도 검토 필요.
3. **UE 5.x 버전 차이**: 9개 매핑이 5.0 → 5.7 동안 변동 가능성 — 다른 UE 버전 사용 시 정확한 source 직접 확인 의무.

## 진단 (Hazard 발생 시)

증상:
- `ConnectMaterialExpressions` 가 false 반환
- input pin name 이 *명백히 존재* (reflection 으로 확인)
- raw property name 과 다른 이름이 어딘가에서 비교됨

진단 절차:
1. `MaterialGraphNode.cpp:596` 의 `GetShortenPinName` 매핑 9개 확인
2. property name 이 9개 중 하나면 → 축약 이름으로 변환 후 재시도
3. property name 이 9개 외면 → 다른 원인 (예: type 미스매치, output index, 노드 자체 invalid)

## 관련 entity

- [[UMaterialEditingLibrary]] (ConnectMaterialExpressions API — pin name shortening 미러 의무)
- [[UMaterialExpression]] (base — GetInputName / GetInput(i))
- [[FExpressionInput]] (input pin 표현)
- [[UMaterialGraph]] (GetShortenPinName 의 소속)

## 열린 질문

1. ❓ UE 5.8+ 에서 매핑 9개 외 추가/변경 여부 — 버전 업그레이드 시 재검증 필요.
2. ❓ `MipValueMode` / `SamplerSource` 등 enum property 가 input pin 으로 노출되는 경우 — 별도 매핑 가능성.
3. ❓ MaterialFunction 내부의 input pin 도 같은 매핑 적용되는지 — `add_function_input` 도구 영향 검토 필요 (현재 가정: 별도 처리).

## Cross-link

- `concepts/UE-FStructProperty-Cast-Type-Safety` (같은 reflection 계열)
- `concepts/UEnum-GetValueByName-FullyQualified` (유사 reflection prefix hazard)
- `concepts/Material-Editor-External-Change-Reopen` (같은 Material 계열)
- `synthesis/UE-Material-Editing-Library-Patterns` (TODO — MaterialEditingLibrary 사용 패턴 합성)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| GetShortenPinName 9개 매핑 | 🟢 VAULT | `MaterialGraphNode.cpp:596-636` 직접 확인 |
| ConnectMaterialExpressions 의 shortening 호출 흐름 | 🟢 VAULT | `MaterialEditingLibrary.cpp:45-78` + `:700` 직접 확인 |
| `Input → NAME_None` → 단일 input 자동 매핑 | 🟢 VAULT | `MaterialEditingLibrary.cpp:51-54` 직접 확인 |
| Power.Exponent 사례 | 🟢 VAULT | MCMaterialAuto v0.23 실측 사용자 cycle |
| MaterialFunctionCall 의 GetInputNameWithType 별도 layer | 🟡 PARTIAL | `MaterialEditingLibrary.cpp:60` 언급 — 정확한 동작 미검증 |
| UE 5.8+ 매핑 변동 가능성 | 🔴 INFERRED | 버전 업그레이드 시 재확인 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-48 / MCMaterialAuto v0.23 채택본 기반)
- 2026-05-22: MMA-45 의 *진짜 메커니즘* 흡수 — Input → NAME_None 매핑이 단일 input 정책의 근본 원인
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass-line-shifted

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `GetShortenPinName` 함수: 5.5.4 `MaterialGraphNode.cpp:585` · 5.7.4 동 파일 line 596
- **라인 shift 11 라인 위로** (1117 → 1134 lines, 17 줄 짧음)
- **9개 매핑 본문 byte-identical** — 함수 body 56 라인 diff 0 (Coordinates→UVs / TextureObject→Tex / Input→NAME_None / Exponent→Exp / AGreaterThanB→CompactAGreaterThanB / AEqualsB→CompactAEqualsB / ALessThanB→CompactALessThanB / ... 9개 매핑 그대로)
- **결정**: 🟢 본 페이지의 9개 매핑 + Pin Name Shortening 동작 5.5.4 에서 그대로 유효. 라인 596 인용은 5.7.4 vintage — 5.5.4 환경에서는 585.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
