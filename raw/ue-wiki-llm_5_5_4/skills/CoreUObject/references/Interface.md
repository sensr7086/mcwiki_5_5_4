---
name: coreuobject-interface
description: UINTERFACE + IInterface - TScriptInterface + Execute_* 매크로 + Implements<T> + BP 지원 BlueprintType vs Native-Only Cannot vs MinimalAPI.
---

# CoreUObject / Interface

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: `UInterface`/`IInterface` 패턴, `TScriptInterface<T>`, `UEditorPathObjectInterface`
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`Reflection/`](../Reflection/SKILL.md)

---

## 1. 개요

UE의 인터페이스는 **두 클래스 쌍** 패턴이다:

- `U<Name>` — UObject 자손, 메타 객체 (BP 노출, UClass에 등록되는 표지자). 멤버 없음.
- `I<Name>` — 추상 C++ 인터페이스, 실제 가상 함수 선언. **UObject 아님**.

이 분리 덕분에 인터페이스를 BP로도 노출할 수 있고(`U<Name>`이 UCLASS 메타로 등록), C++에서는 다중 상속이 가능하다(`IInterface`만 다중 상속).

```cpp
UINTERFACE(MinimalAPI, meta=(IsBlueprintBase="true", CannotImplementInterfaceInBlueprint))
class UInterface : public UObject { GENERATED_BODY() };

class IInterface { GENERATED_BODY() };
```

`UEditorPathObjectInterface` 가 같은 패턴의 표준 예 (UE5의 Level Instance에서 외부 객체가 내부 객체를 참조할 때 사용).

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/Interface.h` | `UINTERFACE` 매크로(=`UCLASS()`), `UInterface` (L18, `: public UObject`), `IInterface` (L25) | 모든 UE 인터페이스의 베이스 쌍. `UInterface`는 메타용으로 멤버가 없다. |
| `Public/UObject/ScriptInterface.h` | `class FScriptInterface` (L21), `template <typename T> class TScriptInterface : public FScriptInterface` (L138) | **UObject 포인터 + 인터페이스 포인터 쌍**의 안전 핸들. UPROPERTY로 노출 가능. |
| `Public/Misc/EditorPathObjectInterface.h` | `UEditorPathObjectInterface` (L14, `: public UInterface`), `IEditorPathObjectInterface` (L27) 🛠 | Level Instance 등에서 에디터 경로 해석 위임. 에디터 빌드 위주. |
| `Public/UObject/ScriptMacros.h` | `UFUNCTION`/`UINTERFACE` 디스패치 매크로 | 인터페이스 메서드의 `Execute_*` 정적 헬퍼 자동 생성. |

### 2.1 UINTERFACE 매크로 옵션

`UINTERFACE` 는 `UCLASS()` 의 별칭(매크로 expansion 시 같은 처리)이지만, 의미상 다음 메타가 자주 붙는다:

- `MinimalAPI` — DLL export 최소화 (헤더만 export, 구현은 제외).
- `meta=(IsBlueprintBase="true")` — BP 인터페이스로도 사용 가능.
- `meta=(CannotImplementInterfaceInBlueprint)` — C++ 클래스만 구현 가능 (BP에서 implement 금지).
- `BlueprintType` — TScriptInterface로 BP 변수에 사용 가능.

---

## 3. 자주 쓰는 API

```cpp
// === C++에서 인터페이스 구현 ===
UCLASS()
class UMyDoor : public UActorComponent, public IMyOpenable
{
    GENERATED_BODY()
public:
    // IMyOpenable 가상 함수 구현 — 자세한 패턴은 5.1
    virtual void Open_Implementation() override;
};

// === 인터페이스 호출 (C++ 인스턴스) ===
if (IMyOpenable* O = Cast<IMyOpenable>(Comp))
{
    O->Execute_Open(Cast<UObject>(O));     // BP 함수도 안전하게 호출
}

// === 인터페이스 구현 여부 검사 ===
if (Comp->GetClass()->ImplementsInterface(UMyOpenable::StaticClass()))
{
    IMyOpenable::Execute_Open(Comp);       // 정적 디스패치
}
// 또는:
bool b = Comp->Implements<UMyOpenable>();

// === TScriptInterface (BP/UPROPERTY 노출 가능한 핸들) ===
UPROPERTY(EditAnywhere)
TScriptInterface<IMyOpenable> Target;     // BP에서도 핀으로 노출

if (Target) Target->Execute_Open(Target.GetObject());

// === FScriptInterface 직접 ===
FScriptInterface SI;
SI.SetObject(MyComp);
SI.SetInterface(Cast<IMyOpenable>(MyComp));
```

---

## 4. 가상 함수 (오버라이드 포인트)

`IInterface` 자체는 빈 베이스라 정해진 virtual이 없다. 각 인터페이스는 자기 가상 함수를 선언한다. **두 가지 호출 형태**가 핵심:

### 4.1 UFUNCTION(BlueprintNativeEvent) — BP 오버라이드 가능

```cpp
// IMyOpenable.h
UINTERFACE(MinimalAPI, Blueprintable)
class UMyOpenable : public UInterface { GENERATED_BODY() };

class IMyOpenable
{
    GENERATED_BODY()
public:
    // BP에서 override 가능, C++에서는 _Implementation 으로 기본 구현
    UFUNCTION(BlueprintNativeEvent, Category="Door")
    void Open();
    virtual void Open_Implementation() {}    // C++ 기본 구현 (옵션)

    // BP에서는 호출만, C++만 override
    UFUNCTION(BlueprintCallable, Category="Door")
    bool IsOpen() const;
    virtual bool IsOpen_Implementation() const { return false; }
};
```

호출 측에서는 항상 `Execute_Open(ObjectAsUObject)` 정적 헬퍼를 쓴다 — UFUNCTION 가상 디스패치를 처리하면서 BP 구현도 안전하게 호출.

### 4.2 일반 C++ virtual — BP 노출 불가, 다중 상속 자유

```cpp
class IMyHookable
{
    GENERATED_BODY()
public:
    virtual void OnHook(int32 Index) = 0;    // BP에는 안 보임
};
```

순수 C++ 가상 함수는 `Execute_*` 헬퍼가 없으므로, **반드시 `Cast<I...>` 후 직접 호출**.

### 4.3 UEditorPathObjectInterface 🛠

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `IEditorPathObjectInterface` 메서드 🛠 | EditorPathObjectInterface.h | `WITH_EDITOR` 빈도 큼 | `UObject::ResolveSubobject` 와 짝지어 외부에서 Level Instance 내부를 참조할 때 경로 해석. |

---

## 5. 예제

### 5.1 인터페이스 정의 + C++ 구현 + BP override

```cpp
// IMyOpenable.h
UINTERFACE(MinimalAPI, Blueprintable, meta=(IsBlueprintBase="true"))
class UMyOpenable : public UInterface { GENERATED_BODY() };

class MYGAME_API IMyOpenable
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintNativeEvent, Category="Door")
    void Open();
    virtual void Open_Implementation() {}
};

// MyDoor.h
UCLASS()
class MYGAME_API AMyDoor : public AActor, public IMyOpenable
{
    GENERATED_BODY()
public:
    virtual void Open_Implementation() override;
};

// 호출 측
void Use(AActor* A)
{
    if (A && A->GetClass()->ImplementsInterface(UMyOpenable::StaticClass()))
    {
        IMyOpenable::Execute_Open(A);      // BP override가 있으면 그쪽이 호출됨
    }
}
```

### 5.2 TScriptInterface 멤버 (BP 디테일 패널 노출)

```cpp
UCLASS()
class UMyKeycard : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Keycard", meta=(MustImplement="MyOpenable"))
    TScriptInterface<IMyOpenable> Target;

    void Use()
    {
        if (Target.GetObject())
            IMyOpenable::Execute_Open(Target.GetObject());
    }
};
```

> `meta=(MustImplement="MyOpenable")` 가 디테일 패널에서 "이 인터페이스를 구현한 객체만" 선택 가능하게 게이팅한다.

### 5.3 인터페이스 다중 구현

```cpp
UCLASS()
class UMyKey : public UObject, public IMyPickupable, public IMyInspectable
{
    GENERATED_BODY()
public:
    virtual void Pickup_Implementation() override;
    virtual void Inspect_Implementation() override;
};
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UEditorPathObjectInterface` / `IEditorPathObjectInterface` 🛠 | EditorPathObjectInterface.h L14·L27 | `WITH_EDITOR` 위주 | Level Instance·World Partition 등 에디터 워크플로우와 짝. 런타임에선 의미 약함. |
| `meta=(MustImplement)` 메타 키 🛠 | (UPROPERTY 메타) | `WITH_EDITORONLY_DATA` | 디테일 패널 게이팅 — 쿠킹 후 사라짐. |
| `meta=(CannotImplementInterfaceInBlueprint)` 메타 키 🛠 | (UINTERFACE 메타) | UHT 단계 | 컴파일 시 BP 구현 차단. |

> 인터페이스 호출 자체(`Execute_*`)는 런타임 코드. 에디터 전용은 메타·검증·디테일 패널 통합 부분.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — `Implements<T>`/`ImplementsInterface(UClass*)` 호출 자체는 UObject 헬퍼
- [`Reflection/`](../Reflection/SKILL.md) — `UINTERFACE` 가 사실상 `UCLASS()` — UClass 메타로 등록
- [`ObjectHandles/`](../ObjectHandles/SKILL.md) — `TScriptInterface<T>` 와 `TWeakObjectPtr<T>` 의 차이
