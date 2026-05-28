---
name: ue-blueprint
description: UE 5.5.4 Blueprint 시스템(노드 그래프 + UFUNCTION/UPROPERTY 노출 + BlueprintFunctionLibrary + Blueprint Native/Implementable Event + Macro/Interface) 위키. C++↔BP 경계 + 성능 함정(VM Thunk, Tick BP 함정) + Cooked Build 동작.
---

# Blueprint — UE 5.5.4 노드 그래프 / C++ ↔ BP 경계

> **카테고리** — Tier 2 (게임 로직 / 디자이너 협업)
> **대표 클래스** — `UBlueprint`, `UBlueprintGeneratedClass`, `UEdGraph`, `UFunction`(VM)
> **트리거 키워드** — Blueprint, BP, UFUNCTION(BlueprintCallable), BlueprintImplementableEvent, BlueprintNativeEvent, BlueprintReadOnly, BlueprintFunctionLibrary

본 sub-skill은 **C++ 코드를 Blueprint에 어떻게 노출하는지**, **BP가 C++을 어떻게 호출하는지**, 그리고 **BP의 성능/Cooked-build 함정**을 정리한다. BP 자체의 노드 사용법은 디자이너/공식 문서 영역으로 위임.

---

## 1. C++ → Blueprint 노출 표준

### 1.1 UFUNCTION 매크로 의미

| 매크로 | 의미 | 함정 |
|--------|------|------|
| `BlueprintCallable` | BP에서 호출 가능. C++ 본체. | `Category=...` 필수. const 시 입출력 핀 분리. |
| `BlueprintPure` | 노드에 실행 핀 없음. const + 부작용 없어야. | side-effect 있으면 디자이너가 매번 호출. |
| `BlueprintImplementableEvent` | BP가 구현. C++은 시그니처만. | C++에서 호출 → BP 구현 없으면 NOP. |
| `BlueprintNativeEvent` | C++ 기본 구현 + BP 오버라이드 가능. | `Implementation` 접미사 함수에 본체. |
| `BlueprintCosmetic` | 서버에서 호출 안 됨. | 멀티플레이 데디 서버 최적화. |
| `BlueprintAuthorityOnly` | Authority만 호출. | 클라 호출 시 NOP. |

### 1.2 UPROPERTY 노출

| 매크로 | BP 가시성 |
|--------|---------|
| `EditAnywhere, BlueprintReadWrite` | 디테일 패널 + BP 변수 |
| `EditDefaultsOnly, BlueprintReadOnly` | 디폴트만 + BP 읽기 |
| `VisibleAnywhere, BlueprintReadOnly` | 패널 표시 + BP 읽기 |
| `BlueprintAssignable` (Delegate) | BP에서 Bind 가능 |
| `BlueprintCallable` (Delegate) | BP에서 Broadcast 가능 |

> 🚨 **`Category=` 필수** — 모든 BP 노출 매크로는 `Category="..."` 지정. 누락 시 컴파일 경고 + BP 검색 어려움.

### 1.3 BlueprintFunctionLibrary 패턴

```cpp
UCLASS()
class UMyBPLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, BlueprintPure, Category="MyGame|Math",
              meta=(WorldContext="WorldContextObject"))
    static float CalcDamage(UObject* WorldContextObject, float Base, float Multiplier);
};
```

> static 함수만 가능. `WorldContextObject` 메타로 BP에서 World 자동 주입 [grep-listed].

---

## 2. Blueprint → C++ 호출 (역방향)

C++ 인터페이스로 BP 구현 강제:

```cpp
UINTERFACE(BlueprintType)
class UDamageable : public UInterface { GENERATED_BODY() };

class IDamageable
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintNativeEvent, Category="Damage")
    void TakeHit(float Amount);
    virtual void TakeHit_Implementation(float Amount) {}
};
```

C++ 호출 시:

```cpp
if (Target->Implements<UDamageable>())
{
    IDamageable::Execute_TakeHit(Target, 10.f);  // BP 구현 라우팅
}
```

> ⚠ **직접 C++ 메서드 호출 금지** — `static Execute_*` 헬퍼 의무. BP 구현이 호출되지 않음 [verified].

---

## 3. 성능 함정 (의무 인지)

### 3.1 BP VM Thunk 비용

- C++ 함수 1회 = ~수십 ns
- BP 노드 1회 = **~수백 ns ~ μs** (VM 디스패치 + 핀 박싱) [inferred — 일반 측정치, 외부 검증 의무]
- **Tick BP는 절대 회피** — Tick에 BP 그래프 수십 노드 = 60fps에서 1ms+
- 해결 — BP 이벤트 그래프는 **Native C++로 이전** + BP는 데이터/디자이너 영역만

### 3.2 BP Construction Script

- 에디터 / Cooked 양쪽에서 호출 — `WITH_EDITORONLY_DATA` 방어 의무
- 자산 하드 로드 위치 → `11_AssetLoadingPolicy` 적용
- BP CDO 대상 — `RF_ClassDefaultObject` 검사 (`10_ComponentPolicies §6`)

### 3.3 BP Tick

- Actor BP의 `Event Tick` 활성화는 디자이너가 의식 못 함
- 매 BP에 `Class Defaults → Auto Receive Input` / `Tick Interval` 명시
- 다수 BP Actor + Tick = 60fps 폭락 → C++ Subsystem으로 통합 (`skills/Subsystem/SKILL.md`)

---

## 4. Cooked Build 함정

| 함정 | 원인 | 해결 |
|------|------|------|
| BP가 Editor PIE에선 OK, Cooked에서 NOP | `WITH_EDITOR` 가드 누락 | `#if !WITH_EDITOR` 분기 검토 |
| BP 인스턴스 변수 손실 | Default vs Instance 혼동 | `EditDefaultsOnly` 의도 검증 |
| BlueprintImplementableEvent 호출 안 됨 | BP 부모 클래스가 BNE 미구현 | C++ 본체 `BlueprintNativeEvent`로 변환 |
| `GetMutableDefault<T>()` 사용한 BP | CDO 손상 | `10_ComponentPolicies §6` |

---

## 5. Blueprint Macro / Interface / Class

| 종류 | 클래스 | 용도 | 함정 |
|------|--------|------|------|
| Blueprint Class | `UBlueprint` | 일반 BP (Actor/Component 기반) | C++ 부모 변경 시 컴파일 |
| Blueprint Macro Library | `UBlueprintMacroLibrary` | 노드 그룹 매크로 | 디버그 어려움 |
| Blueprint Function Library | `UBlueprintFunctionLibrary` | static 함수 모음 | C++ 본체 권장 |
| Blueprint Interface | `UInterface` + `BlueprintType` | 다중 상속 회피 | `Execute_*` 헬퍼 의무 |
| Animation Blueprint | `UAnimBlueprint` | AnimGraph + EventGraph | `skills/Animation/AnimGraph` |
| Widget Blueprint | UMG `UUserWidget` | UI | `skills/UMG/UUserWidget` |

---

## 6. C++ ↔ BP 협업 표준 (실무 권장)

1. **로직은 C++** — Tick / 복제 / 성능 critical
2. **데이터는 BP** — DataTable / DataAsset / 디자이너 튜닝
3. **이벤트 콜백은 BNE** — C++ 디폴트 + BP 오버라이드
4. **Delegate는 `BlueprintAssignable`** — UI / 게임플레이 이벤트
5. **Function Library는 BP 호출용 Pure 함수** — Math / String / 변환

---

## 7. 정책 의무

- 🚨 `04_OverrideIndex` — BP 오버라이드 시 Super 호출 규약
- 🚨 `10_ComponentPolicies §6` — CDO (BP 디폴트) 손상 금지
- 🚨 `11_AssetLoadingPolicy` — BP Construction Script 자산 로드
- 🚨 `07_ProfilingScopeRule` — BP Tick = 측정 의무

---

## 8. 더 깊이 / 외부 검증

- 위키에 없는 BP 노드 동작 → `references/19_ExternalSourcesGuide.md`로 docs.unrealengine.com `BlueprintAPI` 검색
- BP 컴파일 에러 / 노드 그래프 디버깅 → Epic 포럼 / Q&A 사용
- BP → C++ 변환 (Nativization) 5.x에서 deprecated [grep-listed]

---

## 관련 sub-skill

- [`skills/CoreUObject/references/Reflection.md`](../CoreUObject/references/Reflection.md) — UFUNCTION / UPROPERTY 메타
- [`skills/Animation/references/AnimGraph.md`](../Animation/references/AnimGraph.md) — AnimBP
- [`skills/UMG/references/UUserWidget.md`](../UMG/references/UUserWidget.md) — Widget BP
- [`references/04_OverrideIndex.md`](../../references/04_OverrideIndex.md)
- [`references/10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md)
