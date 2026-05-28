---
type: source
title: "UE Editor — AssetTools sub-skill 🛠 (에셋 타입별 동작 등록)"
slug: ue-editor-assettools
source_path: raw/ue-wiki-llm/skills/Editor/references/AssetTools.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-15
related_entities:
  - "[[entities/IAssetTools]]"
  - "[[entities/IToolkit]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, editor, assettools, iassettypeactions, asset-categories, content-browser, assetdefinition, advanced-category-idempotency]
---

# UE Editor — AssetTools sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/AssetTools.md]] · 13 KB raw · `Developer/AssetTools/` 21 헤더

## 1. Summary

에셋 타입별 동작 정의 모듈. `IAssetTypeActions` 자손 등록 → **컨텐츠 브라우저** 의 (a) 이름·색·카테고리·툴팁, (b) 더블클릭 시 에디터 (`OpenAssetEditor`), (c) 우클릭 컨텍스트 (`GetActions`), (d) 썸네일·복제·이름변경·머지 가능성 결정. **5.1+ 후속 `UAssetDefinition`** (모듈 `AssetDefinition`) 와 *공존* — 5.7.4 기준 두 시스템 모두 작동, 같은 클래스 동시 등록 = 충돌. 🚨 어셋 로드 = Editor 순수 모드 동기 (`TryLoad`).

## 2. Key claims

### 2.1. 핵심 헤더 8

- `IAssetTools.h` (인터페이스 L283) + `UAssetTools` (UInterface L273) — 글로벌 매니저
- `IAssetTypeActions.h` (L27) + `EAssetTypeActivationMethod` — 40+ PURE virtual
- `AssetTypeActions_Base.h` (L24) — `FAssetTypeActions_Base` (거의 항상 자손)
- `AssetTypeCategories.h` — `EAssetTypeCategories` enum + `FAdvancedAssetCategory`
- `IClassTypeActions.h` + `ClassTypeActions_Base.h` — 클래스 타입 (Actor 등)
- `AssetToolsModule.h` (`FAssetToolsModule`) / `AssetToolsSettings.h` / `CollectionAssetManagement.h`

### 2.2. IAssetTools 글로벌 매니저 API 🟢

| API | 라인 | 의미 |
| -- | -- | -- |
| `RegisterAssetTypeActions(TSharedRef<IAssetTypeActions>)` | L293 | 에셋 타입 등록 |
| `UnregisterAssetTypeActions` | L296 | 해제 (Shutdown 의무 — hot-reload dangling 방지) |
| `GetAssetTypeActionsForClass(UClass*)` | L302 | 클래스 → 액션 |
| `RegisterAdvancedAssetCategory(FName, FText)` | L317 | 새 카테고리 |
| `FindAdvancedAssetCategory(FName)` | L320 | 검색 |
| `RegisterClassTypeActions` | L326 | 클래스 액션 |
| `GetTypeColor(UClass*)` | L308 | 타입 색 |

### 2.3. 등록 표준 패턴

```cpp
#if WITH_EDITOR
void FMyGameEditorModule::StartupModule()
{
    IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
    EAssetTypeCategories::Type MyCategory = AssetTools.RegisterAdvancedAssetCategory(
        FName("MyGame"), LOCTEXT("MyGame", "My Game"));
    TSharedRef<FMyAssetTypeActions> Action = MakeShared<FMyAssetTypeActions>(MyCategory);
    AssetTools.RegisterAssetTypeActions(Action);
    RegisteredActions.Add(Action);   // shutdown 시 해제용 멤버 보유 의무
}
void FMyGameEditorModule::ShutdownModule()
{
    if (FModuleManager::Get().IsModuleLoaded("AssetTools"))
    {
        IAssetTools& AT = FModuleManager::GetModuleChecked<FAssetToolsModule>("AssetTools").Get();
        for (auto A : RegisteredActions) AT.UnregisterAssetTypeActions(A);
    }
}
#endif
```

KMCProject `MCEditorModule::StartupModule` 가 `FMCStoryAssetAction` / `FMCPartsAssetAction` 등록 — [[sources/ue-docs-claude]] §architecture.

### 2.4. IAssetTypeActions PURE_VIRTUAL 핵심

`GetName()` (L40) / **`GetSupportedClass()`** (L43) ⭐ / **`GetTypeColor()`** (L46) ⭐ / `ShouldFindEditorForAsset()` (L61) / **`OpenAssetEditor(TArray<UObject*>&, TSharedPtr<IToolkitHost>)`** (L64) ⭐ / `AssetsActivatedOverride` (L70) / `CanRename / CanDuplicate / CanFilter` (L73-82) / `GetFilterName` (L85) / `CanLocalize / CanMerge / Merge / Merge(3-way)` (L88-97) / **`GetCategories()`** (L100) ⭐ — 비트마스크 / `GetObjectDisplayName(UObject*)` (L103).

추가 30+ optional virtual (썸네일 / 미리보기 / Diff) — `FAssetTypeActions_Base` 가 기본 구현 (사용자는 `FAssetTypeActions_Base` 자손 권장).

### 2.5. 표준 자손 패턴

```cpp
class FMyAssetTypeActions : public FAssetTypeActions_Base
{
    EAssetTypeCategories::Type Category;
public:
    FMyAssetTypeActions(EAssetTypeCategories::Type C) : Category(C) {}
    virtual FText GetName() const override        { return LOCTEXT("MyAsset", "My Asset"); }
    virtual UClass* GetSupportedClass() const override { return UMyAsset::StaticClass(); }
    virtual FColor GetTypeColor() const override  { return FColor::Cyan; }
    virtual uint32 GetCategories() override        { return Category; }
    virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithin) override
    {
        EToolkitMode::Type Mode = EditWithin.IsValid() ? EToolkitMode::WorldCentric : EToolkitMode::Standalone;
        for (UObject* Obj : InObjects)
            if (auto* A = Cast<UMyAsset>(Obj))
                MakeShared<FMyAssetEditor>()->InitMyAssetEditor(Mode, EditWithin, A);
    }
};
```

### 2.6. EAssetTypeCategories — 비트마스크

기본: `Basic / Animation / MaterialsAndTextures / Sounds / Physics / UI / Misc / Gameplay / Blueprint / AI / Media / World / FX`. 새 모듈 카테고리는 `RegisterAdvancedAssetCategory` 동적 등록 (비트 자동 할당). uint32 → **64+ 카테고리 시 한계** (Open question — 5.7.4 미해결).

#### 2.6.1 ⭐ `RegisterAdvancedAssetCategory` 같은 이름 idempotency (2026-05-15 추가, KMCProject 실측) 🟢

같은 `FName` 으로 여러 번 호출 시 **모두 같은 `EAssetTypeCategories::Type` 비트마스크 반환** → 1 카테고리에 N 자산 그룹화 표준 패턴.

```cpp
// ✅ KMCProject MCEditorModule::StartupModule — 같은 "MCAsset" 이름 3번 호출
EAssetTypeCategories::Type StoryCat = AT.RegisterAdvancedAssetCategory(FName("MCAsset"), LOCTEXT("MCStoryAsset", "MCStory Asset"));
EAssetTypeCategories::Type PartsCat = AT.RegisterAdvancedAssetCategory(FName("MCAsset"), LOCTEXT("MCPartsAsset", "MCParts Asset"));
EAssetTypeCategories::Type ComboCat = AT.RegisterAdvancedAssetCategory(FName("MCAsset"), LOCTEXT("MCComboAsset", "MCCombo Asset"));
// StoryCat == PartsCat == ComboCat — 모두 같은 비트
AT.RegisterAssetTypeActions(MakeShared<FMCStoryAssetAction>(StoryCat));
AT.RegisterAssetTypeActions(MakeShared<FMCPartsAssetAction>(PartsCat));
AT.RegisterAssetTypeActions(MakeShared<FMCComboAssetAction>(ComboCat));   // 모두 "MCAsset" advanced 카테고리에 표시
```

- `FName` 키 가 이미 존재하면 그 `EAssetTypeCategories::Type` 재사용 (overwrite X)
- 두 번째 인자 `FText` 는 **첫 번째 호출만 반영** — 후속 호출의 LOCTEXT 는 무시 (vault 미검증 — 5.7.4 동작 추정)
- 다중 자산을 같은 advanced 카테고리에 그룹화하려면 **같은 FName 재사용** 이 표준
- 다른 FName 사용 시 별도 카테고리 메뉴 항목으로 분리 표시

KMCProject 검증 (2026-05-15) — Content Browser "Advanced > MCAsset" 메뉴에 Story / Parts / Combo 3종 자산 정상 표시. log: `[2026-05-15] feature | RegisterAdvancedAssetCategory("MCAsset") 3회 idempotent 검증`.

⭐ **함정** — 첫 호출의 `FText` 가 메뉴 라벨 — 후속 호출 LOCTEXT 키를 다르게 두면 LOCTEXT 자체는 미사용 (혼선 회피용으로 매트릭스 §2.6.1 명시 의무).

### 2.7. UAssetDefinition (5.1+ 후속) ⚠

`AssetDefinition` 모듈 — `UAssetDefinition_Default` 자손 + `UAssetDefinitionRegistry::Register`. 시스템 비교:

| 측면 | `IAssetTypeActions` (4.x~) | `UAssetDefinition` (5.1+) |
| -- | -- | -- |
| 베이스 | C++ 인터페이스 | UClass (UObject 자손) |
| 등록 | `RegisterAssetTypeActions` | `UAssetDefinitionRegistry::Register` |
| 카테고리 | uint32 비트마스크 | `FAssetCategoryPath` (계층) |
| Diff / Merge | 같은 인터페이스 | `PerformAssetDiff` 별도 API |
| BP 접근 | X (순수 C++) | UCLASS → Editor BP 접근 가능 |

🚨 **같은 클래스에 둘 다 등록 시 충돌** — 신규 = `UAssetDefinition` 권장, 기존 = `IAssetTypeActions` 유지. 마이그레이션은 한 번에 한 시스템만.

### 2.8. 함정 (6대)

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `GetSupportedClass()` nullptr | UClass 의무 — 등록 실패 |
| 2 | `RegisterAssetTypeActions` 후 `Unregister` 누락 | Shutdown 의무 — hot-reload dangling |
| 3 | `GetCategories()` 0 | 메뉴 안 보임 — 카테고리 의무 |
| 4 | `OpenAssetEditor` 안 비동기 로드 | UI race → [[sources/ue-ref-11-assetloadingpolicy]] §3 |
| 5 | 두 시스템 (`IAssetTypeActions` + `UAssetDefinition`) 같은 클래스 동시 등록 | 충돌 — 한 시스템만 |
| 6 | `FAssetTypeActions_Base` 가 아닌 `IAssetTypeActions` 직접 자손 | 30+ override 부담 — `_Base` 의무 |

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-unrealed-asseteditortoolkit]] (`OpenAssetEditor` → `InitAssetEditor`) / [[sources/ue-editor-unrealed-subsystems]] (`UAssetEditorSubsystem`) / [[sources/ue-editor-asseteditorapi]] / [[sources/ue-editor-propertyeditor]] / [[sources/ue-editor-unrealed-factories]] (UFactory)
- 횡단: [[sources/ue-ref-05-editoronlyindex]] (4단 분리) · [[sources/ue-ref-11-assetloadingpolicy]] §3
- 자산 페어: [[sources/ue-assetclasses-skill]]
- MC-시리즈: [[sources/ue-docs-claude]] (KMCProject `FMCStoryAssetAction` / `FMCPartsAssetAction` / `FMCComboAssetAction`) · [[synthesis/mc-combo-editor-levelsequence-lite]] (Combo 자산 등록 — §2.6.1 idempotency 사례, Cycle 5d)

### 관련 fix log

- ⭐ `[2026-05-15] feature | RegisterAdvancedAssetCategory("MCAsset") 3회 idempotent 검증` — §2.6.1 1차 검증
