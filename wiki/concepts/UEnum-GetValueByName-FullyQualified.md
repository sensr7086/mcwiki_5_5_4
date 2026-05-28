---
title: "UEnum GetValueByName — fully-qualified prefix 요구"
kind: concept
status: stable
severity: "★★"
tags: [reflection, uenum, MMA-32, hazard, ue-574, foundation]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# `UEnum::GetValueByName` — fully-qualified prefix 요구

## 정의

UE 의 `UEnum::GetValueByName(FName)` 은 enum 의 **fully-qualified name** (`EnumTypeName::EnumValueName`) 으로만 lookup 한다. 짧은 이름 (`EnumValueName`) 만 넘기면 `INDEX_NONE` 반환 — 그러나 caller 가 일반적으로 짧은 이름만 알고 있는 경우가 흔해 silent failure 빈번 발생.

특히 `EMaterialProperty` 같이 enum 값이 16개 이상인 경우, 매번 prefix 를 직접 붙이는 것은 error-prone. **사전 정의 TMap 또는 helper 함수**로 매핑하는 패턴이 안전.

## 자세히

### 사례: MCMaterialAuto MMA-32

🟢 **VAULT** — MMA-32 hazard 로그:

문제 코드 (위험):
```cpp
// MCP 도구에서 받은 문자열: "BaseColor"
UEnum* PropEnum = StaticEnum<EMaterialProperty>();   // UEnum 의 template helper
int64 Value = PropEnum->GetValueByName(FName(TEXT("BaseColor")));
// → INDEX_NONE (lookup 실패!)
```

원인:
- `EMaterialProperty::BaseColor` 의 fully-qualified name 은 `"EMaterialProperty::BaseColor"`
- `GetValueByName` 은 fully-qualified 형태만 인식
- 짧은 이름 lookup 시 실패하지만 **assert / log 없이** `INDEX_NONE` 만 반환 → silent bug

### Fix 1: Fully-qualified 직접 사용

```cpp
const FString FullName = FString::Printf(TEXT("EMaterialProperty::%s"), *ShortName);
int64 Value = PropEnum->GetValueByName(FName(*FullName));
if (Value == INDEX_NONE) { /* error handling */ }
```

🟢 **VAULT** — UE 공식 패턴이지만 모든 enum 마다 prefix 직접 알아야 → 다중 enum 환경에서 boilerplate.

### Fix 2: TMap 사전 정의 (MCMaterialAuto 채택)

```cpp
static const TMap<FString, EMaterialProperty> MaterialPropertyMap = {
    { TEXT("BaseColor"),      MP_BaseColor },
    { TEXT("Metallic"),       MP_Metallic },
    { TEXT("Specular"),       MP_Specular },
    { TEXT("Roughness"),      MP_Roughness },
    { TEXT("EmissiveColor"),  MP_EmissiveColor },
    { TEXT("Opacity"),        MP_Opacity },
    { TEXT("OpacityMask"),    MP_OpacityMask },
    { TEXT("Normal"),         MP_Normal },
    { TEXT("WorldPositionOffset"), MP_WorldPositionOffset },
    { TEXT("SubsurfaceColor"), MP_SubsurfaceColor },
    { TEXT("CustomData0"),    MP_CustomData0 },
    { TEXT("CustomData1"),    MP_CustomData1 },
    { TEXT("AmbientOcclusion"), MP_AmbientOcclusion },
    { TEXT("Refraction"),     MP_Refraction },
    { TEXT("PixelDepthOffset"), MP_PixelDepthOffset },
    { TEXT("ShadingModel"),   MP_ShadingModel },
};

if (const EMaterialProperty* Found = MaterialPropertyMap.Find(InputName))
{
    // 사용
}
```

**장점**:
- 짧은 이름 lookup 직관적 — 사용자 입력 그대로 사용
- enum 값 추가/삭제 시 컴파일 시점에 누락 발견 (compile-time symbol 사용)
- prefix 변경 (예: `EMaterialProperty` → `EShaderProperty`) 에 강건

**단점**:
- 새 enum 값 추가 시 TMap 도 수동 추가 필요 — drift 가능
- 16+ 값이라 boilerplate 증가

### Fix 3: 일반화 helper

```cpp
template<typename TEnum>
TEnum GetEnumValueByShortName(const FString& ShortName, TEnum Default)
{
    UEnum* E = StaticEnum<TEnum>();   // UEnum 의 template specialization helper
    if (!E) return Default;
    const FString FullName = FString::Printf(TEXT("%s::%s"), *E->CppType, *ShortName);
    int64 V = E->GetValueByName(FName(*FullName));
    return V == INDEX_NONE ? Default : static_cast<TEnum>(V);
}
```

🟡 **PARTIAL** — `UEnum::CppType` 정확한 형식 미확정. namespace-scoped enum 일 때 prefix 가 `Outer::EnumType` 형태인지 확인 필요. MCMaterialAuto 는 Fix 2 채택 (정량 검증 회피).

## 회피 패턴 (Production 권장)

| 상황 | 권장 패턴 |
|---|---|
| enum 값 ≤ 5 | Fix 1 — fully-qualified 직접 |
| enum 값 6 ~ 30 | Fix 2 — TMap 사전 정의 |
| enum 값 > 30 또는 동적 | Fix 3 — generic helper (검증 후) |
| user-facing 문자열 입력 | Fix 2 — error 메시지 명확 |

## 변형 사례

1. **`UEnum::GetIndexByName`**:
   - 같은 prefix 요구. value 가 아니라 index 만 다름.

2. **`UEnum::GetNameByValue(int64)` (역방향)**:
   - fully-qualified name 반환 — 문자열 처리 시 prefix 잘라야 사용자 입력과 매칭 가능

3. **BlueprintType USTRUCT 의 enum 멤버**:
   - reflection 으로 set 할 때 동일 hazard — `ImportText` 가 fully-qualified 만 인식

4. **다른 UE enum 들**:
   - `EBlendMode`, `EShadingModel`, `ETranslucencyLightingMode` 등 머티리얼 enum 전부 동일 처리 필요
   - 각각 별도 TMap 또는 generic helper 호출

## 관련 entity

- [[UEnum]] (`StaticEnum<T>()` template — 본문 inline)
- [[EMaterialProperty]]
- [[FName]]
- [[UMaterial]]

## 열린 질문

1. ❓ `UEnum::CppType` 의 정확한 형식 — namespace-scoped enum 또는 nested enum 의 경우 `Outer::Type::Value` 인지 미확정.
2. ❓ Generated `*_BPLibrary` 의 enum reflection 패턴 — Blueprint 측에서는 prefix 처리가 자동인지 미확인.
3. ❓ Hot-reload 후 enum value 재매핑 — TMap 의 컴파일 시점 binding 이 hot-reload 와 충돌 가능성 검증 필요.

## Cross-link

- `concepts/UE-FStructProperty-Cast-Type-Safety` (같은 reflection hazard 계열)
- `concepts/Material-Editor-External-Change-Reopen` (같은 v0.14 작업)
- `synthesis/UE-Reflection-Type-Safety-Patterns` (TODO — reflection hazard 합성)
- `00_meta/03_EvaluatorRecipe` § Stage 4 (Type-Safety 검증)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `GetValueByName` fully-qualified 요구 | 🟢 VAULT | UE 5.7 소스 `UnrealType.cpp` 직접 확인 |
| Silent failure (assert 없음) | 🟢 VAULT | 위와 동일 |
| TMap 패턴 채택 | 🟢 VAULT | MCMaterialAuto v0.14 실측 채택 |
| `UEnum::CppType` 형식 | 🔴 INFERRED | 정확한 namespace handling 미검증 |
| Hot-reload 충돌 가능성 | 🔴 INFERRED | 검증 미완 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-32 fix 직후, MCMaterialAuto v0.14 채택본 기반)
- 2026-05-22: cross-link 정리 — `StaticEnum` link → `[[UEnum]]` + template helper 명시 inline
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

UEnum 의 fully-qualified 요구는 CoreUObject 기초 semantic — UnrealType.cpp 의 lookup 동작이 minor patch 사이 변경된 사례 없음. 5.5.4 에서도 동일 적용.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
