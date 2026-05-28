---
name: unrealed-kismet2
description: 🛠 FKismetEditorUtilities + UBlueprint + FBlueprintCompilationManager - BP 컴파일.
---

# UnrealEd · Kismet2 sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: `Engine/Source/Editor/UnrealEd/Public/Kismet2/` + `Classes/UserDefinedStructure/`
> **다루는 범위**: 블루프린트 통합 헬퍼 — `FBlueprintEditorUtils` · `FKismetEditorUtilities` · `FCompilerResultsLog` · `FKismetReinstanceUtilities` · `FDebuggerCommands` · UUserDefinedStruct.

---

## 1. 개요

블루프린트 시스템과 상호작용하는 **모든 Editor 측 헬퍼**. 게임 런타임의 `BlueprintGeneratedClass` / `KismetSystemLibrary` 와 별개로, Editor 모듈에서 BP 클래스를 변경·재컴파일·검색·디버깅하는 정적 함수 묶음.

**구성**:
- `FBlueprintEditorUtils` — BP 변경의 표준 진입점 (가장 자주)
- `FKismetEditorUtilities` — BP 생성·복제·인스턴스 재생성
- `FCompilerResultsLog` — 컴파일 메시지 누적·출력
- `FKismetReinstanceUtilities` — Hot-Reload 인스턴스 재할당
- `FKismetDebugUtilities` — BP 디버거 헬퍼
- `FDebuggerCommands` — 디버거 단축키
- `UUserDefinedStruct` 에디터 — 사용자 정의 구조체

---

## 2. 핵심 헤더

| 클래스 | 헤더 | 메모 |
|--------|------|------|
| `FBlueprintEditorUtils` | `Public/Kismet2/BlueprintEditorUtils.h` | 가장 자주 사용 — BP 변경 표준 |
| `FKismetEditorUtilities` | `Public/Kismet2/KismetEditorUtilities.h` | BP 생성·복제·CompileBlueprint |
| `FCompilerResultsLog` | `Public/Kismet2/CompilerResultsLog.h` | 컴파일 메시지 |
| `FKismetReinstanceUtilities` | `Public/Kismet2/KismetReinstanceUtilities.h` | Hot-Reload 인스턴스 재할당 |
| `FKismetDebugUtilities` | `Public/Kismet2/KismetDebugUtilities.h` | BP 디버거 |
| `FDebuggerCommands` | `Public/Kismet2/DebuggerCommands.h` | 디버거 단축키 |
| `FBreakpoint` | `Public/Kismet2/Breakpoint.h` | 중단점 |
| `FComponentEditorUtils` | `Public/Kismet2/ComponentEditorUtils.h` | 컴포넌트 편집 |
| `FChildActorComponentEditorUtils` | `Public/Kismet2/ChildActorComponentEditorUtils.h` | 자식 액터 컴포넌트 |
| `FEnumEditorUtils` | `Public/Kismet2/EnumEditorUtils.h` | UEnum 에디터 |
| `FKismet2NameValidators` | `Public/Kismet2/Kismet2NameValidators.h` | 이름 검증 |
| `SClassPickerDialog` | `Public/Kismet2/SClassPickerDialog.h` | 클래스 선택 다이얼로그 |
| `FListenerManager` | `Public/Kismet2/ListenerManager.h` | 리스너 관리 |
| `FReloadUtilities` | `Public/Kismet2/ReloadUtilities.h` | 리로드 |
| `UUserDefinedStruct` (런타임) + 에디터 헬퍼 | `Classes/UserDefinedStructure/UserDefinedStructEditorData.h` | 사용자 정의 구조체 |

---

## 3. 가장 자주 — FBlueprintEditorUtils

| API 카테고리 | 메서드 (대표) |
|-------------|--------------|
| **BP 변경 통지** | `MarkBlueprintAsModified` · `MarkBlueprintAsStructurallyModified` (구조 변경 — 컴파일 필요) |
| **변수 추가/제거** | `AddMemberVariable` · `RemoveMemberVariable` · `RenameMemberVariable` · `ChangeMemberVariableType` |
| **함수 추가/제거** | `AddFunctionGraph` · `RemoveFunctionGraph` · `RenameFunction` |
| **이벤트** | `AddInputEventGraph` · `RemoveInputEventGraph` |
| **노드 검색** | `GetAllNodesOfClass` · `GetAllGraphs` · `FindNodesAndPinsByName` |
| **컴파일** | (Compile 자체는 `FKismetEditorUtilities::CompileBlueprint`) |
| **타이머/실행** | `RemoveTickableNodes` 등 디버그 |

```cpp
#if WITH_EDITOR
// 변수 추가
FBPVariableDescription NewVar;
NewVar.VarName = TEXT("MyNewBool");
NewVar.VarType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
FBlueprintEditorUtils::AddMemberVariable(MyBlueprint, NewVar.VarName, NewVar.VarType);

// 변경 통지 (구조 변경이면 Structurally)
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(MyBlueprint);
#endif
```

---

## 4. FKismetEditorUtilities

| API | 메모 |
|-----|------|
| `CreateBlueprint(UClass* ParentClass, UObject* Outer, FName Name, EBlueprintType, UClass* BPClass=UBlueprint::StaticClass(), UClass* BPGCClass=UBlueprintGeneratedClass::StaticClass())` | 새 BP 생성 |
| `CompileBlueprint(UBlueprint* Blueprint, EBlueprintCompileOptions, FCompilerResultsLog* Results)` | 컴파일 실행 |
| `IsClassABlueprintInterface(const UClass*)` | BP 인터페이스 클래스인지 |
| `CreateBlueprintFromActor(...)` | 액터에서 BP 추출 |
| `HarvestBlueprintFromActors(...)` | 다중 액터 → BP |
| `CreateNewBoundEventForComponent` | 컴포넌트 이벤트 생성 |

---

## 5. FCompilerResultsLog (컴파일 메시지)

```cpp
FCompilerResultsLog Results;
FKismetEditorUtilities::CompileBlueprint(MyBlueprint, EBlueprintCompileOptions::None, &Results);

// 결과 검사
if (Results.NumErrors > 0)
{
    for (const TSharedRef<FTokenizedMessage>& Msg : Results.Messages)
    {
        UE_LOG(LogTemp, Error, TEXT("BP Compile: %s"), *Msg->ToText().ToString());
    }
}
```

`FTokenizedMessage` 는 메시지에 노드/핀 링크를 포함 (클릭 시 노드로 점프).

---

## 6. FKismetReinstanceUtilities (Hot-Reload)

C++ 헤더 변경 후 재컴파일 시, 기존 인스턴스를 새 클래스 인스턴스로 자동 변환:

```cpp
FBlueprintCompileReinstancer Reinstancer(NewBPClass);
Reinstancer.ReinstanceObjects(/*bForceReplace=*/true);
```

직접 호출은 드물고, 보통 BP 컴파일 시스템이 자동 호출. `FReloadUtilities` 와 함께 모듈 리로드 시 호출됨.

---

## 7. UUserDefinedStruct 에디터 (사용자 정의 USTRUCT)

`UUserDefinedStruct` (런타임 객체) + `UUserDefinedStructEditorData` (에디터 메타) 쌍으로 동작. 변경 시:

```cpp
// 사용자 정의 USTRUCT 변경 → 영향받는 BP들 자동 재컴파일
FStructureEditorUtils::ModifyStructData(MyStruct);
FStructureEditorUtils::OnStructureChanged(MyStruct, EStructureEditorChangeInfo::AddedNewProperty);
```

---

## 8. 가상 함수 / Super 호출

본 sub-skill의 클래스 대다수는 **static 헬퍼** — virtual override 없음. 다만 다음은 override 가능:

| 클래스 | virtual | Super | 메모 |
|--------|---------|-------|------|
| `IBlueprintCompilerCreationContext` | (인터페이스) | — | BP 컴파일러 확장 |
| `FKismetCompilerContext` | `CompileFunctions` 등 | (override 시 Super FIRST) | 커스텀 BP 컴파일 |
| `FBPVariableMetaData` | (구조) | — | |
| `UUserDefinedStruct` virtual | `Serialize` 등 (CoreUObject 베이스) | [04_OverrideIndex §6.1](../../../references/04_OverrideIndex.md) |

---

## 9. 함정

| 함정 | 회피 |
|------|------|
| `MarkBlueprintAsModified` 만 호출 후 컴파일 안 함 | 구조 변경은 `MarkBlueprintAsStructurallyModified` + 외부에서 `CompileBlueprint` 호출 |
| 게임 모듈에서 `FBlueprintEditorUtils` 사용 | Editor 모듈 분리 |
| 변수 추가 후 BP 노드 노출 안 됨 | `MarkBlueprintAsStructurallyModified` 누락 |
| BP 컴파일 결과 검사 누락 | `FCompilerResultsLog::NumErrors` 확인 + 에러 로그 |
| 인스턴스 변경 시 Reinstancer 직접 호출 | BP 시스템에 위임 — `MarkBlueprintAsStructurallyModified` 만 호출 |
| static 함수에 스코프 부착 누락 | 핫 경로면 `TRACE_CPUPROFILER_EVENT_SCOPE` 부착 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

## 10. 에디터 전용 🛠

전체 sub-skill 에디터 빌드 전용. Module 의존: `UnrealEd` + `BlueprintGraph` + `KismetCompiler` + `Kismet`.

---

## 11. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — UnrealEd 메인
- [`UnrealEd/AssetEditorToolkit`](../AssetEditorToolkit/SKILL.md) — `FBlueprintEditor` 가 자손
- [`Slate/GraphEditor`](../../Slate/references/GraphEditor.md) — UEdGraph 런타임 + GraphEditor 위젯
- [`CoreUObject/Reflection`](../../CoreUObject/references/Reflection.md) — UCLASS/UFUNCTION 메타 (BP 변수가 사용)
- 향후: `BlueprintGraph` / `KismetCompiler` / `Kismet` (별도 모듈, 미마운트)
- 교차 인덱스: [`04_OverrideIndex.md`](../../../references/04_OverrideIndex.md) · [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
