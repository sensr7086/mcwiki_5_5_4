---
title: "C++ Name Hiding — derived override 가 base overload 를 가리는 함정 (C2660)"
kind: concept
status: stable
severity: "★★"
tags: [cpp, name-hiding, override, build-error, C2660, ue-574, foundation]
created: 2026-05-22
last_updated: 2026-05-22
---

# C++ Name Hiding — derived override 가 base overload 를 가리는 함정 (C2660)

## 정의

C++ 의 *name hiding* 규칙 — derived 클래스가 같은 이름의 함수를 *하나만* override 하면, base class 의 *다른 overload 들이 derived scope 에서 숨겨짐*. 호출 시 컴파일러는 derived 클래스의 visible scope 만 검색 → "no matching overload" → **C2660 (MSVC)** 또는 "no matching function" (clang/gcc).

UE 의 인터페이스 hierarchy 가 길어 (예: `IMaterialEditor` → `FWorkflowCentricApplication` → `FAssetEditorToolkit`) base 의 0-arg overload 와 derived 의 1-arg override 가 흔히 발생.

## 자세히

### 사례: MCMaterialAuto v0.20 빌드 (MMA-40)

🟢 **VAULT** — MMA-40 hazard 로그:

**base 헤더** (`Engine/Source/Editor/UnrealEd/Public/Toolkits/AssetEditorToolkit.h:243-244`):
```cpp
UNREALED_API virtual FName GetToolMenuToolbarName(FName& OutParentName) const;   // 1-arg
UNREALED_API FName GetToolMenuToolbarName() const;                                // 0-arg overload
```

**derived 헤더** (`WorkflowOrientedApp/WorkflowCentricApplication.h:30`):
```cpp
UNREALED_API virtual FName GetToolMenuToolbarName(FName& OutParentName) const override;
//                                                ^^^^^^^^^^^^^^^^^^^ 1-arg 만 override
```

**호출 코드** (실패):
```cpp
TSharedPtr<IMaterialEditor> Editor = ...;
const FName ToolbarName = Editor->GetToolMenuToolbarName();   // ❌ C2660
//                                                          0-arg overload 가 hide 된 상태
```

**에러 메시지** (MSVC):
```
error C2660: 'FWorkflowCentricApplication::GetToolMenuToolbarName':
  함수는 0개의 인수를 사용하지 않습니다.
note: 'FWorkflowCentricApplication::GetToolMenuToolbarName' 선언을 참조하십시오.
note: 인수 목록 '()' 을 일치시키는 동안
```

### 원인 — C++ standard §3.3.10 (Hiding) + §10.2 (Member Name Lookup)

derived class scope 안에서 *같은 이름의 멤버를 선언* 하면 base class 의 동일 이름 멤버 *전부* 가 derived scope 에서 lookup 불가:

```cpp
struct Base {
    void Foo(int);
    void Foo();   // overload
};
struct Derived : Base {
    void Foo(int) override;   // ← 1-arg override → Base::Foo() 도 hide!
};

Derived d;
d.Foo();        // ❌ error — Base::Foo() 가 derived scope 에서 invisible
d.Foo(42);      // ✅ ok
d.Base::Foo();  // ✅ ok — explicit base scope
```

### Fix 3 패턴

#### Fix 1: 1-arg 버전 호출 (가장 단순)

```cpp
FName ParentName = NAME_None;   // out-param
const FName ToolbarName = Editor->GetToolMenuToolbarName(ParentName);
```

#### Fix 2: explicit base scope

```cpp
const FName ToolbarName = Editor->FAssetEditorToolkit::GetToolMenuToolbarName();
```
- ✅ 0-arg 그대로 호출
- ⚠ derived 의 virtual dispatch 우회 — derived 가 override 한 1-arg 로직이 적용 안 됨 (이 케이스는 다른 함수라 무관하지만 일반 명심)

#### Fix 3: using declaration (base 에 접근 권한 있을 때만)

derived 클래스 자체 작성 시:
```cpp
struct Derived : Base {
    using Base::Foo;   // ← base 의 모든 Foo overload 를 derived scope 로 가져옴
    void Foo(int) override;
};
```
- 외부 모듈에서 *UE base class* 수정 불가 → 본 hazard 에서는 적용 불가

## 회피 패턴

| 상황 | 권장 Fix |
|---|---|
| UE base class call (수정 불가) | Fix 1 (out-param 전달) — 가장 자연스러움 |
| derived virtual dispatch 우회 의도 | Fix 2 (`Base::Member` syntax) |
| 자체 클래스 hierarchy 설계 | Fix 3 (`using Base::Foo`) — 권장 패턴 |

## 변형 사례

1. **Multiple overload 모두 가리는 경우**:
   - base 에 `Foo()`, `Foo(int)`, `Foo(int, int)` — derived 가 `Foo()` 만 override
   - → derived scope 에서 `Foo(int)` 와 `Foo(int, int)` 둘 다 invisible
2. **const / non-const overload**:
   - `void Foo() const` 와 `void Foo()` — derived 가 const 만 override 시 non-const 가 hide
3. **UE 의 다른 hierarchy**:
   - `UPrimitiveComponent` ↔ `UStaticMeshComponent` 의 일부 함수
   - `IPropertyHandle` ↔ derived 안 동일 이름 멤버
4. **Template + virtual 결합**:
   - template member function + virtual override 가 섞이면 더 복잡 — 별도 검토 필요

## 진단

컴파일 에러 메시지 패턴:
- MSVC: `error C2660: '<Class>::<Member>' : 함수는 N개의 인수를 사용하지 않습니다`
- Clang: `error: no matching member function for call to '<Member>'` + `candidate function not viable: requires N arguments`
- gcc: 비슷한 형태

진단 절차:
1. 에러 메시지의 *Class::Member* 확인 — derived class 임 (override 한 곳)
2. base class header 검색 — 같은 이름의 *다른 overload* 존재 여부
3. derived 가 *부분 override* 만 했는지 확인 — 그 overload 만 visible

## 관련 entity

- [[FAssetEditorToolkit]] (UE base — 0-arg + 1-arg overload 둘 다)
- [[IMaterialEditor]] (IMaterialEditor → FWorkflowCentricApplication → FAssetEditorToolkit chain)

## 열린 질문

1. ❓ UE 의 다른 hierarchy 에서 동일 hazard 사례 카탈로그 — UEdGraph / UPrimitiveComponent / IPropertyHandle 등 검토 필요.
2. ❓ UE 의 `UE_REQUIRES` / `TEnableIf` template trick 으로 hiding 회피 가능한지 — UE 5.x 패턴 검증.
3. ❓ `[[deprecated]]` overload 의 hiding 동작 — derived 가 non-deprecated 만 override 시 base 의 deprecated 도 hide 되는지.

## Cross-link

- `concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern` (이 hazard 의 실측 발견 cycle)
- `concepts/Unity-Build-Include-Cascade` (다른 build-error 함정)
- `synthesis/UE-Cpp-Hazard-Catalog` (TODO — UE C++ 함정 합성)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| C++ name hiding 규칙 (§3.3.10) | 🟢 VAULT | C++ standard 공식 |
| FAssetEditorToolkit 0-arg + 1-arg overload | 🟢 VAULT | AssetEditorToolkit.h L243-244 직접 확인 |
| FWorkflowCentricApplication 1-arg override only | 🟢 VAULT | WorkflowCentricApplication.h L30 직접 확인 |
| Fix 1 (out-param) 채택 동작 | 🟢 VAULT | MCMaterialAuto v0.20 실측 |
| `using Base::Foo` 패턴 | 🟢 VAULT | C++ standard 명시 |
| `[[deprecated]]` overload hiding | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-40 / MCMaterialAuto v0.20 빌드 fix 직후)
