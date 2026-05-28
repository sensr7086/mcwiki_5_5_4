---
type: source
title: "UE Editor — UnrealEd / Kismet2 sub-skill 🛠 (BP 통합 헬퍼)"
slug: ue-editor-unrealed-kismet2
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Kismet2.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/UBlueprint]]"
  - "[[entities/UBlueprintGeneratedClass]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/CPP-BP-Boundary]]"
tags: [ue, editor, unrealed, kismet2, blueprint, fblueprinteditorutils, fkismeteditorutilities, fcompilerresultslog, reinstance, hot-reload]
---

# UE Editor — UnrealEd / Kismet2 sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Kismet2.md]] · `Engine/Source/Editor/UnrealEd/Public/Kismet2/` + `Classes/UserDefinedStructure/`

## 1. Summary

블루프린트 시스템과 상호작용하는 **모든 Editor 측 헬퍼** 묶음. 게임 런타임의 `BlueprintGeneratedClass` / `KismetSystemLibrary` 와 별개로, Editor 모듈에서 BP 클래스를 **변경·재컴파일·검색·디버깅** 하는 정적 함수 묶음. 7 핵심: **`FBlueprintEditorUtils`** (BP 변경 표준) · **`FKismetEditorUtilities`** (생성·복제·CompileBlueprint) · **`FCompilerResultsLog`** (컴파일 메시지) · **`FKismetReinstanceUtilities`** (Hot-Reload 인스턴스 재할당) · **`FKismetDebugUtilities`** (BP 디버거) · **`FDebuggerCommands`** (단축키) · **`UUserDefinedStruct`** + `UUserDefinedStructEditorData`. 🛠 **Editor 전용**.

## 2. Key claims

### 2.1. 핵심 헤더 매트릭스

| 클래스 | 헤더 | 역할 |
| -- | -- | -- |
| **`FBlueprintEditorUtils`** ⭐ | `Public/Kismet2/BlueprintEditorUtils.h` | 가장 자주 — BP 변경 표준 |
| `FKismetEditorUtilities` | `Public/Kismet2/KismetEditorUtilities.h` | BP 생성·복제·`CompileBlueprint` |
| `FCompilerResultsLog` | `Public/Kismet2/CompilerResultsLog.h` | 컴파일 메시지 + `FTokenizedMessage` |
| `FKismetReinstanceUtilities` | `Public/Kismet2/KismetReinstanceUtilities.h` | Hot-Reload 인스턴스 재할당 |
| `FKismetDebugUtilities` | `Public/Kismet2/KismetDebugUtilities.h` | BP 디버거 헬퍼 |
| `FDebuggerCommands` | `Public/Kismet2/DebuggerCommands.h` | 디버거 단축키 |
| `FBreakpoint` | `Public/Kismet2/Breakpoint.h` | 중단점 |
| `FComponentEditorUtils` / `FChildActorComponentEditorUtils` | `Public/Kismet2/Component*EditorUtils.h` | 컴포넌트 편집 |
| `FEnumEditorUtils` | `Public/Kismet2/EnumEditorUtils.h` | UEnum 에디터 |
| `FKismet2NameValidators` | `Public/Kismet2/Kismet2NameValidators.h` | 이름 검증 |
| `SClassPickerDialog` | `Public/Kismet2/SClassPickerDialog.h` | 클래스 선택 다이얼로그 |
| `FReloadUtilities` | `Public/Kismet2/ReloadUtilities.h` | 리로드 |
| `UUserDefinedStruct` + `UUserDefinedStructEditorData` | `Classes/UserDefinedStructure/UserDefinedStructEditorData.h` | 사용자 정의 USTRUCT 페어 |

### 2.2. FBlueprintEditorUtils — 가장 자주 🟢

| API 카테고리 | 메서드 (대표) |
| -- | -- |
| **BP 변경 통지** | `MarkBlueprintAsModified` · **`MarkBlueprintAsStructurallyModified`** ⭐ (구조 변경 — 컴파일 필요) |
| 변수 추가/제거 | `AddMemberVariable` · `RemoveMemberVariable` · `RenameMemberVariable` · `ChangeMemberVariableType` |
| 함수 추가/제거 | `AddFunctionGraph` · `RemoveFunctionGraph` · `RenameFunction` |
| 이벤트 | `AddInputEventGraph` · `RemoveInputEventGraph` |
| 노드 검색 | `GetAllNodesOfClass` · `GetAllGraphs` · `FindNodesAndPinsByName` |
| 디버그 | `RemoveTickableNodes` |

```cpp
#if WITH_EDITOR
// 변수 추가
FBPVariableDescription NewVar;
NewVar.VarName = TEXT("MyNewBool");
NewVar.VarType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
FBlueprintEditorUtils::AddMemberVariable(MyBlueprint, NewVar.VarName, NewVar.VarType);
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(MyBlueprint);   // 의무
#endif
```

### 2.3. FKismetEditorUtilities — BP 생성·컴파일

| API | 의미 |
| -- | -- |
| `CreateBlueprint(UClass* Parent, UObject* Outer, FName Name, EBlueprintType, UClass* BPClass, UClass* BPGCClass)` | 새 BP 생성 |
| **`CompileBlueprint(UBlueprint*, EBlueprintCompileOptions, FCompilerResultsLog*)`** ⭐ | 컴파일 실행 (동기) |
| `IsClassABlueprintInterface(const UClass*)` | BP 인터페이스 검사 |
| `CreateBlueprintFromActor(...)` | 액터 → BP 추출 |
| `HarvestBlueprintFromActors(...)` | 다중 액터 → BP |
| `CreateNewBoundEventForComponent` | 컴포넌트 이벤트 생성 |

### 2.4. FCompilerResultsLog — 컴파일 메시지

```cpp
FCompilerResultsLog Results;
FKismetEditorUtilities::CompileBlueprint(MyBlueprint, EBlueprintCompileOptions::None, &Results);

if (Results.NumErrors > 0)
{
    for (const TSharedRef<FTokenizedMessage>& Msg : Results.Messages)
        UE_LOG(LogTemp, Error, TEXT("BP Compile: %s"), *Msg->ToText().ToString());
}
```

`FTokenizedMessage` 는 메시지에 **노드/핀 링크 포함** — 클릭 시 노드로 점프.

### 2.5. BP 컴파일 흐름 (4 단계)

`Skeleton Class` → `Blueprint Class` → **`BlueprintGeneratedClass`** → CDO

- Skeleton Class: 함수 시그니처 전용 (참조 해결용)
- Blueprint Class: 의존성 + 그래프 데이터
- BlueprintGeneratedClass: 런타임 결과물 — **Cooked 빌드에 남는 유일한 것**
- CDO: Class Default Object — `Component-Policies-6 §6` 의 CDO 정책 적용 대상

### 2.6. FKismetReinstanceUtilities — Hot-Reload

C++ 헤더 변경 후 재컴파일 시, 기존 인스턴스를 새 클래스 인스턴스로 자동 변환:

```cpp
FBlueprintCompileReinstancer Reinstancer(NewBPClass);
Reinstancer.ReinstanceObjects(/*bForceReplace=*/true);
```

직접 호출은 드물고, 보통 BP 컴파일 시스템이 자동 호출. `FReloadUtilities` 와 함께 모듈 리로드 시 호출.

### 2.7. UUserDefinedStruct (사용자 정의 USTRUCT)

`UUserDefinedStruct` (런타임) + `UUserDefinedStructEditorData` (에디터 메타) 쌍으로 동작:

```cpp
// 사용자 정의 USTRUCT 변경 → 영향받는 BP 자동 재컴파일
FStructureEditorUtils::ModifyStructData(MyStruct);
FStructureEditorUtils::OnStructureChanged(MyStruct, EStructureEditorChangeInfo::AddedNewProperty);
```

### 2.8. Virtual / Super 호출 (드뭄)

본 sub-skill 의 클래스 대다수는 **static 헬퍼** — virtual override 없음. 다만:

| 클래스 | virtual | Super | 메모 |
| -- | -- | -- | -- |
| `FKismetCompilerContext` | `CompileFunctions` 등 | (override 시 Super FIRST) | 커스텀 BP 컴파일러 확장 |
| `IBlueprintCompilerCreationContext` | (인터페이스) | — | BP 컴파일러 생성 컨텍스트 |
| `UUserDefinedStruct` | `Serialize` 등 (CoreUObject 베이스) | → [[sources/ue-ref-04-overrideindex]] §1 |

### 2.9. 함정 (6대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `MarkBlueprintAsModified` 만 호출 후 컴파일 안 함 | 구조 변경은 **`MarkBlueprintAsStructurallyModified`** + `CompileBlueprint` |
| 2 | 게임 모듈에서 `FBlueprintEditorUtils` 사용 | Editor 모듈 분리 — [[sources/ue-ref-05-editoronlyindex]] |
| 3 | 변수 추가 후 BP 노드 노출 안 됨 | `MarkBlueprintAsStructurallyModified` 누락 |
| 4 | BP 컴파일 결과 검사 누락 | `FCompilerResultsLog::NumErrors` 확인 + 에러 로그 |
| 5 | 인스턴스 변경 시 Reinstancer 직접 호출 | BP 시스템에 위임 — `MarkBlueprintAsStructurallyModified` 만 |
| 6 | static 함수에 스코프 부착 누락 (핫 경로) | `TRACE_CPUPROFILER_EVENT_SCOPE` → [[sources/ue-ref-07-profilingscopeRule]] |

### 2.10. Build.cs (Editor 모듈만) 🛠

`UnrealEd` + `BlueprintGraph` + `KismetCompiler` + `Kismet`. uplugin `"Type": "Editor"`.

## 3. KMCProject 페어

`MCEditorModule/MCStoryEditor/` 가 본 sub-skill 의 패턴을 *직접 적용 안 함* (커스텀 그래프 = `UMCStory_Graph` UObject + `UMCStory_Node` 자손) 이지만, 향후 BP-like 컴파일이 필요해질 경우 본 sub-skill 의 `FCompilerResultsLog` + `FBlueprintCompileReinstancer` 가 참조 대상. → [[sources/ue-docs-claude]] §architecture.

## 4. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-unrealed-asseteditortoolkit]] (`FBlueprintEditor` 가 자손) / [[sources/ue-editor-unrealed-materialeditor]] (`UMaterialGraph` 동등 패턴) / [[sources/ue-slate-grapheditor]] (UEdGraph + GraphEditor 위젯)
- 횡단: [[sources/ue-ref-04-overrideindex]] §1 (UObject virtual) · [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]]
- CoreUObject 페어: [[sources/ue-coreuobject-reflection]] (UPROPERTY → BP 변수)
- Blueprint 카테고리: [[sources/ue-blueprint-skill]] (런타임 BP 시스템)
