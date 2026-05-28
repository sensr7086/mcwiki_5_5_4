---
name: editor-asseteditorapi
description: 🛠 실행 중인 에셋 에디터 접근 표준 — UAssetEditorSubsystem (FindEditorForAsset / OnAssetOpenedInEditor / OnAssetEditorRequestClose) + IAssetEditorInstance (GetEditorName / FocusWindow / CloseWindow(EAssetEditorCloseReason)) + EditorName static_cast 안전 패턴. IStaticMeshEditor / ISkeletalMeshEditor / IPersonaToolkit / UDebugSkelMeshComponent / FAdvancedPreviewScene = references/. Editor 전용 (4단 분리).
---

# Editor/AssetEditorAPI — 실행 중인 에셋 에디터 접근 표준 🛠

> **위치 (verified)**:
> - **UAssetEditorSubsystem** — `Engine/Source/Editor/UnrealEd/Public/Subsystems/AssetEditorSubsystem.h` (FindEditorForAsset:153 / OnAssetOpenedInEditor:189 / OnAssetEditorRequestClose:175 + IAssetEditorInstance:55 + EAssetEditorCloseReason:29)
>
> **요지**: **이미 열려있는 에셋 에디터** (StaticMesh / SkeletalMesh / Material / Animation 등) 에 외부 코드에서 접근 — 도구 확장 / Editor Subsystem / 자동화 표준.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | **모든 코드 `WITH_EDITOR` 가드 + Editor 모듈 분리 (4단)** |
| 🚨 Build.cs | Editor 모듈만 `"UnrealEd", "StaticMeshEditor", "SkeletalMeshEditor", "Persona", "AdvancedPreviewScene"` 의존 |
| 🚨 Lifetime | 에디터 닫힘 가능 — 매 호출 `FindEditorForAsset` 재조회 |
| 🚨 static_cast 안전성 | `GetEditorName()` 검증 후 cast — 임의 `IAssetEditorInstance*` X |
| 🚨 [`11_AssetLoadingPolicy.md §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | **Editor 순수 모드 = `TryLoad` / `LoadSynchronous` 동기 로드** (PIE / Game 분기 의무 — `IsPureEditorMode`) |

---

## 1. UAssetEditorSubsystem 핵심 API [verified]

```cpp
#if WITH_EDITOR
// 1. 에디터 찾기 (열려있으면 반환, 없으면 nullptr)
UNREALED_API IAssetEditorInstance* FindEditorForAsset(UObject* Asset, bool bFocusIfOpen);

// 2. 에디터 열기 (이미 열려있으면 포커스)
bool OpenEditorForAsset(UObject* Asset);
bool OpenEditorForAssets(const TArray<UObject*>& Assets);

// 3. 에디터 닫기 (에셋별)
void CloseAllEditorsForAsset(UObject* Asset);

// 4. OnAssetOpenedInEditor — 2-param (UObject*, IAssetEditorInstance*)
FOnAssetOpenedInEditorEvent& OnAssetOpenedInEditor();

// 5. OnAssetEditorRequestClose — 2-param (UObject*, EAssetEditorCloseReason)
FAssetEditorRequestCloseEvent& OnAssetEditorRequestClose();
#endif
```

### 1.1 Subsystem 접근 표준

```cpp
#if WITH_EDITOR
UAssetEditorSubsystem* AES = GEditor ? GEditor->GetEditorSubsystem<UAssetEditorSubsystem>() : nullptr;
if (!IsValid(AES)) return;

IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(MyAsset, /*bFocusIfOpen=*/ true);
#endif
```

---

## 2. EAssetEditorCloseReason 8종 [verified] (5.3+)

`UnrealEd/Public/Subsystems/AssetEditorSubsystem.h:29` — 5.3 이전 `CloseWindow()` (no args) deprecated.

| 그룹 | enum | 의미 |
|------|------|------|
| Subsystem 브로드캐스트 | `CloseAllEditorsForAsset` | 특정 에셋의 모든 에디터 닫기 요청 |
| | `CloseOtherEditors` | 자신 제외 닫기 |
| | `RemoveAssetFromAllEditors` | 에셋 제거 (닫힘 보장 X) |
| | `CloseAllAssetEditors` | 모든 에셋 에디터 닫기 |
| 개별 에디터 | `AssetEditorHostClosed` | 기본 — 닫기 버튼 클릭 |
| | `AssetUnloadingOrInvalid` | 에셋 언로드 / 무효 |
| | `EditorRefreshRequested` | 에디터 재오픈 요청 (refresh) |
| | `AssetForceDeleted` | 에셋 강제 삭제됨 |

---

## 3. IAssetEditorInstance 인터페이스 [verified]

`AssetEditorSubsystem.h:55` — 모든 에셋 에디터의 베이스 인터페이스.

```cpp
class IAssetEditorInstance
{
public:
    virtual FName GetEditorName() const = 0;   // ⭐ 식별자 — cast 전 검증 의무
    virtual void FocusWindow(UObject* ObjectToFocusOn = nullptr) = 0;
    virtual bool CloseWindow(EAssetEditorCloseReason InCloseReason);   // 5.3+
    // CloseWindow() (no args) = 5.3 Deprecated
};
```

### 3.1 EditorName 식별자 표 [inferred — 5.x 분기별 grep 검증 권장]

| FName | 에디터 | FName | 에디터 |
|-------|--------|-------|--------|
| `StaticMeshEditor` | UStaticMesh | `MaterialEditor` | UMaterial |
| `SkeletalMeshEditor` | USkeletalMesh | `MaterialInstanceEditor` | UMaterialInstance |
| `AnimationEditor` | UAnimSequence / UAnimMontage | `TextureEditor` | UTexture |
| `AnimationBlueprintEditor` | UAnimBlueprint | `SoundCueEditor` | USoundCue |
| `BehaviorTreeEditor` | UBehaviorTree | `NiagaraEditor` | UNiagaraSystem |

---

## 4. static_cast 안전 패턴 (EditorName 검증 의무) ⭐

`IAssetEditorInstance*` → 구체 인터페이스 변환 시 **EditorName 검증 후 cast** — RTTI 미동작 (UObject X / IInterface X).

```cpp
#if WITH_EDITOR
IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(MyStaticMesh, /*bFocusIfOpen=*/ false);
if (!EditorInst) return;

// ❌ 위험 — 임의 cast (UB 위험)
auto* SME = static_cast<IStaticMeshEditor*>(EditorInst);

// ✅ 안전 — EditorName 검증 후 cast
if (EditorInst->GetEditorName() == FName("StaticMeshEditor"))
{
    auto* SME = static_cast<IStaticMeshEditor*>(EditorInst);
    // 사용 OK
}
#endif
```

---

## 5. 구체 에디터 인터페이스 → `references/`

각 에디터 인터페이스의 상세 코드 패턴은 별도 reference 로 분리:

| 인터페이스 | reference | 핵심 |
|-----------|----------|------|
| `IStaticMeshEditor` ⭐ | [`references/StaticMeshEditor.md`](./references/StaticMeshEditor.md) | `GetStaticMeshComponent()` 표준 |
| `ISkeletalMeshEditor` + `IPersonaToolkit` + `UDebugSkelMeshComponent` | [`references/PersonaToolkit.md`](./references/PersonaToolkit.md) | Persona 통합 구조 + Preview Component |
| `OnAssetOpenedInEditor` / `OnAssetEditorRequestClose` 이벤트 바인딩 | [`references/EventBinding.md`](./references/EventBinding.md) | UEditorSubsystem 안 Initialize/Deinitialize 페어 |
| `FAdvancedPreviewScene` | [`references/AdvancedPreviewScene.md`](./references/AdvancedPreviewScene.md) | 자체 Preview Scene 구성 |

---

## 6. Build.cs 의존성 (의무)

```csharp
// {ProjectName}Editor.Build.cs (Editor 모듈만)
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine",
    "UnrealEd",                    // UAssetEditorSubsystem, IAssetEditorInstance
    "StaticMeshEditor",            // IStaticMeshEditor
    "SkeletalMeshEditor",          // ISkeletalMeshEditor
    "Persona",                     // IPersonaToolkit
    "AdvancedPreviewScene",        // FAdvancedPreviewScene
});
```

> ⚠ Runtime 모듈에 위 의존 추가 X (Cooked Build 깨짐).

---

## 7. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `WITH_EDITOR` 가드 누락 | 모든 코드 의무 — Cooked Build 즉시 깨짐 |
| 2 | Runtime 모듈에 Editor 의존 추가 | 4단 분리 ([`05_EditorOnlyIndex`](../../../references/05_EditorOnlyIndex.md)) |
| 3 | `IAssetEditorInstance*` 직접 `static_cast` (EditorName 검증 X) | `GetEditorName()` 검증 후 cast |
| 4 | `CloseWindow()` (no args — 5.3 deprecated) 사용 | `CloseWindow(EAssetEditorCloseReason)` |
| 5 | `OnAssetOpenedInEditor` 1-param 으로 추측 | 2-param 의무 (UObject*, IAssetEditorInstance*) |
| 6 | `OnAssetEditorRequestClose` UObject 1-param 으로 추측 | 2-param 의무 (UObject*, EAssetEditorCloseReason) |
| 7 | Delegate 등록 후 해제 누락 | Initialize/Deinitialize 페어 ([`references/EventBinding.md`](./references/EventBinding.md)) |
| 8 | `Toolkit->GetPreviewMeshComponent()` 결과 = USkeletalMeshComponent 추측 | `UDebugSkelMeshComponent*` (자손) — [`references/PersonaToolkit.md`](./references/PersonaToolkit.md) |
| 9 | 에디터 닫혔는데 캐싱된 `IAssetEditorInstance*` 재사용 | 매 호출 `FindEditorForAsset` 재조회 |
| 10 | EditorName 하드코딩 — 5.x 변경 시 깨짐 | 분기별 grep 검증 + 상수화 |

---

## 8. 체크리스트

- [ ] 모든 코드 `#if WITH_EDITOR` 가드
- [ ] Build.cs = Editor 모듈만 의존 (UnrealEd / StaticMeshEditor / Persona / AdvancedPreviewScene)
- [ ] `FindEditorForAsset` 매 호출 재조회 (lifetime)
- [ ] EditorName 검증 후 `static_cast`
- [ ] CloseWindow = `EAssetEditorCloseReason` 인자 (5.3+ 표준)
- [ ] OnAssetOpenedInEditor = 2-param (UObject*, IAssetEditorInstance*)
- [ ] OnAssetEditorRequestClose = 2-param (UObject*, EAssetEditorCloseReason)
- [ ] Delegate Initialize/Deinitialize 페어
- [ ] UDebugSkelMeshComponent = 자손 (USkeletalMeshComponent 가 아님)
- [ ] 5.x 분기별 EditorName grep 재검증

---

## 9. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UAssetEditorSubsystem API 7종 | **[verified]** ✅ | `UnrealEd/Public/Subsystems/AssetEditorSubsystem.h:29 / 55 / 153 / 175 / 189` |
| EAssetEditorCloseReason 8종 | **[verified]** ✅ | 같은 헤더 라인 29~48 |
| IAssetEditorInstance 인터페이스 | **[verified]** ✅ | 같은 헤더 라인 55~ |
| IStaticMeshEditor::GetStaticMeshComponent() | **[grep-listed]** ⚠ | 파일 존재 / 본문 미확인 |
| ISkeletalMeshEditor::GetPersonaToolkit() | **[grep-listed]** ⚠ | 동일 |
| IPersonaToolkit::GetPreviewMeshComponent() | **[grep-listed]** ⚠ | 동일 |
| UDebugSkelMeshComponent (USkeletalMeshComponent 자손) | **[grep-listed]** ⚠ | UnrealEd/Public/Animation/DebugSkelMeshComponent.h 존재 |
| FAdvancedPreviewScene | **[inferred]** ❌ | UE 일반 지식 — 5.7.4 시그니처 grep 검증 필요 |
| EditorName 정확 문자열 10종 | **[inferred]** ❌ | UE 일반 표준 — 5.7.4 분기별 검증 |

> ⚠ `[inferred]` / `[grep-listed]` 항목 = 사용 전 grep 검증 의무 ([`meta/confidence-tags.md`](../../../meta/confidence-tags.md)).

---

## 10. 관련

- [`../SKILL.md`](../SKILL.md) — Editor 메인 (4단 분리 원칙)
- [`../EditorSubsystem/SKILL.md`](../EditorSubsystem/SKILL.md) — UEditorSubsystem 베이스
- [`../UnrealEd/SKILL.md`](../UnrealEd/SKILL.md) — UnrealEd 모듈 통합
- [`../AssetTools/SKILL.md`](../AssetTools/SKILL.md) — IAssetTypeActions 페어
- [`../../../references/05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) — Editor 4단 분리 원칙
- [`../../Subsystem/SKILL.md`](../../Subsystem/SKILL.md) — UEditorSubsystem 사용 표준
- [`../../../meta/confidence-tags.md`](../../../meta/confidence-tags.md) — 신뢰도 태그 시스템

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. UAssetEditorSubsystem 7 API [verified] + EAssetEditorCloseReason 8종 + IAssetEditorInstance + EditorName static_cast 안전 + IStaticMeshEditor / ISkeletalMeshEditor / IPersonaToolkit / UDebugSkelMeshComponent [gre