---
type: source
title: "UE Editor Specialist 🛠 — 19 sub-skill + 4단 분리 + AssetEditorAPI"
slug: ue-agent-editor
source_path: raw/ue-wiki-llm/agents/ue-editor-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/UToolMenus]]"
  - "[[entities/IDetailCustomization]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, specialist, editor, 4-tier-separation, asset-editor-api, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Editor Specialist 🛠

> Source: [[raw/ue-wiki-llm/agents/ue-editor-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Editor]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 UE 5.7.4 Editor 카테고리 통합 전문가 — UnrealEd / EditorFramework / EditorSubsystem / EditorWidgets / AssetTools / PropertyEditor / ToolMenus / MainFrame / LevelEditor / AssetRegistry / **AssetEditorAPI** 통합 **19 sub-skill**. 인하우스 에셋 에디터 / 디테일 패널 / 메뉴/툴바 / 노드 그래프 / 실행 중인 에셋 에디터 접근 (UAssetEditorSubsystem + IStaticMeshEditor + IPersonaToolkit + UDebugSkelMeshComponent + EditorName static_cast 안전 패턴) 작성 전담. **4단 분리 원칙** 자동.

## 2. 자동 로드 (4 파일)

1. `skills/Editor/SKILL.md` (메인 — 11 카테고리 인덱스)
2. [[sources/ue-ref-05-editoronlyindex]] (**4단 분리 원칙 의무**)
3. [[sources/ue-ref-07-profilingscopeRule]]
4. 사용자 요청 매칭 sub-skill

## 3. 🚨 4단 분리 원칙 (05_EditorOnlyIndex)

모든 Editor 작업 의무:
1. **모듈 분리** — Runtime 모듈 (게임) vs Editor 모듈 (Editor 만)
2. **uplugin Type 명시** — `Type=Editor`
3. **Build.cs 분기** — `bBuildDeveloperTools=true` + Slate/SlateCore/UnrealEd 의존
4. **`#if WITH_EDITOR` 가드** — Runtime 모듈 안 모든 Editor 호출

## 4. 8 시나리오 매핑

| 시나리오 | 필수 sub-skill |
|---------|---------------|
| 인하우스 에셋 에디터 ⭐ | UnrealEd/AssetEditorToolkit + AssetTools + Factories + PropertyEditor + ToolMenus |
| 디테일 패널 커스터마이징 | PropertyEditor (단일) |
| 메뉴 / 툴바 추가 | ToolMenus (5.x 모던) |
| 노드 그래프 에디터 | Slate/GraphEditor + UnrealEd/AssetEditorToolkit |
| Editor Subsystem 작성 | EditorSubsystem + Subsystem |
| 에셋 검색 / 의존성 | AssetRegistry |
| 레벨 에디터 확장 | LevelEditor + UnrealEd/Layers |
| 실행 중인 에셋 에디터 접근 ⭐ | **AssetEditorAPI** (UAssetEditorSubsystem + EditorName static_cast + IStaticMeshEditor / IPersonaToolkit + UDebugSkelMeshComponent + OnAssetEditorRequestClose 2-param + EAssetEditorCloseReason 5.3+) |

## 5. 표준 Build.cs 의존성

```csharp
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine", "InputCore",
    "Slate", "SlateCore", "UMG",
    "UnrealEd", "EditorFramework", "EditorSubsystem", "EditorWidgets",
    "AssetTools", "AssetRegistry",
    "PropertyEditor", "ToolMenus",
    "GraphEditor",   // 노드 그래프
    "MainFrame", "LevelEditor"
});
```

## 6. 표준 모듈 분리

```
MyToolRuntime/    Type=Runtime    (게임 빌드 OK) — UMyData / UMyAsset
MyToolEditor/     Type=Editor     (게임 빌드 X) — FAssetTypeActions / FMyAssetEditor / FMyEditorModule
```

## 7. Baseline Grep 의무 — 함정 키워드 ⭐⭐⭐

`ToolMenus` / `OnRegisterTabs` / `OnRegisterTabsForEditor` / `IDetailsView::SetObject` / `WorkflowOrientedApp` / forward declare / `SetGenericLayoutDetailsDelegate` / `RegisterCustomClassLayout` / `IAssetEditorInstance` / `EditorName` / `FAssetEditorToolkit` / `FStructOnScope` / `IStructureDetailsView`.

→ Cycle 5b 발견 (AssetEditor Window 메뉴 = TabManager 자체) + Cycle 5g §11.4 6 호스트 OnRegisterTabs 매트릭스 + Cycle 5d §2.15 WorkflowOrientedApp 폴더 vs 모듈 + Cycle 5d §2.13 forward declare C2664.

## 8. 거부 조건

- 런타임 코드 — `ue-{category}-specialist`
- 평가 — `ue-evaluator`
- 위키 갱신 — `ue-wiki-maintainer`

## 9. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-slate-umg]] (GraphEditor 페어) · [[sources/ue-agent-asset]] (AssetTools 페어)
- 정책 권위: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]]
- Editor sub-skill: [[sources/ue-editor-asseteditorapi]] · [[sources/ue-editor-toolmenus]] · [[sources/ue-editor-propertyeditor]] · [[sources/ue-editor-personatoolkit]] · [[sources/ue-editor-unrealed-asseteditortoolkit]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 10 절. 4단 분리 원칙 + 8 시나리오 + AssetEditorAPI 매핑 + Cycle 5b/5d/5g 함정 키워드 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
