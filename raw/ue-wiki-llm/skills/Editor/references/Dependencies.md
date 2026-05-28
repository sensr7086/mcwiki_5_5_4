---
name: editor-dependencies
description: Editor 모듈 의존성 트리 + 표준 Build.cs — 인하우스 에셋 에디터 작성 시 의존 순서 + 모든 의존 모듈 매핑. (parent — Editor/SKILL.md)
---

# Editor — 모듈 의존성 트리 + 표준 Build.cs

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **요지**: Editor 카테고리 작성 시 모듈 의존 순서 + 표준 Build.cs 의존 묶음.

---

## 1. 의존성 트리 (작성 순서)

```
[베이스 — 항상 의존]
EditorFramework (IToolkit / UEdMode 베이스)
   ↓
UnrealEd (메인 모듈 — Toolkit / Subsystems / Factories / Kismet2 / Elements / Layers)
   ↓
[기능별 추가]
AssetTools         — 에셋 타입 등록
PropertyEditor     — 디테일 패널
ToolMenus          — 메뉴/툴바
LevelEditor        — 레벨 에디터 확장
MainFrame          — 메인 윈도우 후크
EditorWidgets      — 공통 위젯
EditorSubsystem    — Editor-only 서비스
AssetRegistry      — 에셋 메타 (Runtime 이지만 Editor 사용)
```

---

## 2. 표준 인하우스 에셋 에디터 Build.cs

```csharp
// MyEditorModule.Build.cs (Editor 전용 모듈)
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine", "InputCore",
    "Slate", "SlateCore", "UMG",
    "UnrealEd", "EditorFramework", "EditorSubsystem", "EditorWidgets",
    "AssetTools", "AssetRegistry",
    "PropertyEditor", "ToolMenus",
    "GraphEditor",   // 노드 그래프 에디터 시
    "MainFrame", "LevelEditor"
});
```

---

## 3. 시나리오별 Build.cs 추가 의존

| 시나리오 | 추가 의존 |
|---------|----------|
| 노드 그래프 에디터 | `"GraphEditor"` |
| 실행 중 에셋 에디터 접근 | `"StaticMeshEditor", "SkeletalMeshEditor", "Persona", "AdvancedPreviewScene"` |
| Niagara 통합 | `"Niagara", "NiagaraEditor"` |
| BP 컴파일 확장 | `"BlueprintGraph", "KismetCompiler"` |
| 머티리얼 에디터 확장 | `"MaterialEditor"` |

---

## 4. uplugin Type 명시 (의무)

Editor 전용 모듈 = `.uplugin` 안 `Type=Editor` 명시. 게임 빌드 시 자동 stripped.

```json
{
  "Modules": [
    {
      "Name": "MyToolEditor",
      "Type": "Editor",
      "LoadingPhase": "PostEngineInit"
    }
  ]
}
```

→ Cooked 빌드 시 본 모듈 코드 자동 제외. Runtime 모듈에 Editor 의존 추가 시 즉시 빌드 실패.

---

## 5. 표준 모듈 분리 구조

```
[1] MyToolRuntime/                  Type=Runtime    (게임 빌드 OK)
    ├── Build.cs : "Engine" 만
    ├── UMyData (UObject 자손 — 에셋 데이터)
    └── UMyAsset

[2] MyToolEditor/                   Type=Editor     (게임 빌드 X)
    ├── Build.cs : "Slate","SlateCore","UnrealEd","GraphEditor","ToolMenus" 의존
    ├── FAssetTypeActions_MyAsset (AssetTools)
    ├── FMyAssetEditor (FAssetEditorToolkit)
    └── FMyEditorModule
```

---

## 6. 관련 정책

- 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) — **런타임/에디터 4단 분리 원칙 (의무)**
- [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) — 콜백 첫 줄 스코프 의무
