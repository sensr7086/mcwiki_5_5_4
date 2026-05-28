---
type: source
title: "UE Editor — UnrealEd / Misc sub-skill 🛠 (잡다 유틸)"
slug: ue-editor-unrealed-misc
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Misc.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, unrealed, misc, settings, thumbnail, commandlet, dialog]
---

# UE Editor — UnrealEd / Misc sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Misc.md]] · UnrealEd 의 8 sub-skill 에 속하지 않는 기타 영역

## 1. Summary

UnrealEd 거대 모듈의 **잡다 헬퍼 / 유틸 / 서비스** 모음 — 다른 7 sub-skill (`AssetEditorToolkit` / `Subsystems` / `Kismet2` / `Factories` / `Elements` / `Layers` / `MaterialEditor`) 에 속하지 않는 영역. 자주 사용하는 영역만 카테고리별 한 줄 요약. 자세한 사용법은 각 헤더 직접 참조. 🛠 **Editor 전용**.

## 2. Public/ 영역

### 2.1. Settings / — 에디터 설정

`EditorProjectSettings.h` + `EditorPerProjectUserSettings` (Classes/Settings). **`ISettingsModule`** (별도 `Settings` 모듈) 으로 등록 → Project Settings 패널 노출.

### 2.2. Tools / — InteractiveTool 통합

`InteractiveToolsFramework` 어댑터. `UEdMode` 자손에서 InteractiveTool 사용 시.

### 2.3. ViewportToolbar / — 5.x 모던 툴바

`UToolMenus` 통합 + 뷰포트 우상단 툴바 확장.

### 2.4. Dialogs / — 모달 다이얼로그

`SMessageDialog` / `SCustomDialog` 등. 일반적: **`FMessageDialog::Open(EAppMsgType::YesNo, MsgText)`** (Core 모듈 글로벌 헬퍼).

### 2.5. ImportUtils / — 임포트 헬퍼

[[sources/ue-editor-unrealed-factories]] 보조 — 임포트 전후 처리 (UV 변환 / 머티리얼 매핑).

### 2.6. AutoReimport / — 자동 재임포트

파일 변경 감지 시 자동 재임포트. Project Settings → Loading → Auto Reimport.

### 2.7. EditorState / — 에디터 상태 보존

세션 간 에디터 상태 (열린 에셋 / 뷰포트 위치) 직렬화.

### 2.8. DragAndDrop / — 드래그앤드롭

`FAssetDragDropOp` 등 — 컨텐츠 브라우저 → 다른 에디터 드래그.

### 2.9. Commandlets / — Editor 전용 커맨드렛

`UCommandlet` 자손. `-run=Cook` / `-run=WorldPartitionBuilderCommandlet` 등 헤드리스 빌드.

## 3. Classes/ 영역

### 3.1. Animation / — Animation 에디터 클래스

Persona 모듈 연계. `UAnimSequenceFactory` 등은 Factories sub-skill, Animation 데이터 모델 클래스가 여기.

### 3.2. Preferences / — 사용자 환경설정

| 클래스 | 의미 |
| -- | -- |
| **`UEditorPerProjectUserSettings`** | 프로젝트별 사용자 |
| `UEditorLoadingSavingSettings` | 로딩 / 저장 |
| `UEditorMiscSettings` | 잡다 |
| **`ULevelEditorPlaySettings`** | PIE 설정 |

### 3.3. Settings / — 프로젝트 단위

| 클래스 | 의미 |
| -- | -- |
| `UEditorProjectAppearanceSettings` | 외관 |
| `UEditorProjectExperimentalSettings` | 실험 기능 |
| `UEditorProjectImportExportSettings` | 임포트 |

### 3.4. ThumbnailRendering / — 에셋 썸네일

`UThumbnailRenderer` 자손 — 컨텐츠 브라우저 썸네일:

```cpp
UCLASS()
class UMyAssetThumbnailRenderer : public UThumbnailRenderer
{
    GENERATED_BODY()
    virtual bool CanVisualizeAsset(UObject* Object) override;
    virtual void Draw(UObject* Object, int32 X, int32 Y, uint32 Width, uint32 Height,
        FRenderTarget* Target, FCanvas* Canvas, bool bAdditionalViewFamily) override;
};
```

`UThumbnailManager::RegisterCustomRenderer` 또는 INI 등록. 🚨 `Draw` 안 무거운 작업 → 컨텐츠 브라우저 스크롤 시 매번 호출 → 스코프 의무.

### 3.5. CookOnTheSide / — Cook 헬퍼

빌드 시스템 통합.

### 3.6. Editor / — UEditorEngine

`UEditorEngine` 분리된 헬퍼. 직접 다루는 일 드묾 — **`GEditor`** 가 글로벌 인스턴스.

## 4. 자주 쓰는 진입점 모음 🟢

| 시나리오 | 진입점 |
| -- | -- |
| 메시지 박스 | `FMessageDialog::Open(EAppMsgType::YesNo, MsgText)` (Core) |
| 프로젝트 설정 등록 | `ISettingsModule::Get().RegisterSettings(...)` (Settings 모듈) |
| 사용자 설정 읽기 | `GetMutableDefault<UEditorPerProjectUserSettings>()->bMySetting` |
| **PIE 시작 / 정지** | `GEditor->RequestPlaySession(...)` / `GEditor->RequestEndPlayMap()` |
| Editor 모드 변경 | `GLevelEditorModeTools().ActivateMode(...)` (EditorFramework) |
| 썸네일 등록 | `UMyAssetThumbnailRenderer` 자손 + `UCLASS` |
| 자동화 테스트 | `IMPLEMENT_SIMPLE_AUTOMATION_TEST` (AutomationTest.h, Core) |
| Editor 라이프사이클 콜백 | `FEditorDelegates::OnPreBeginPIE` / `OnPostBeginPIE` / `OnEndPIE` / `OnMapChanged` |

## 5. FEditorDelegates 핵심

| 델리게이트 | 시점 |
| -- | -- |
| `OnPreBeginPIE(bool bIsSimulating)` | PIE 시작 직전 |
| `OnPostBeginPIE(bool)` | PIE 시작 직후 |
| `OnEndPIE(bool)` | PIE 종료 |
| `OnMapChanged(UWorld*, EMapChangeType)` | 맵 로드 |
| `OnLevelActorAdded / Removed` | 액터 변경 |

## 6. GEditor 핵심 멤버

`GEditor` = 글로벌 `UEditorEngine` 인스턴스 (UEngine 자손):

- `PlayInPIEActiveCount` — PIE 세션 카운트
- `EndPlayMap()` — PIE 종료
- `SaveAll()` — 모든 에셋 저장
- `Compile()` — BP 컴파일

## 7. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `UEditorPerProjectUserSettings` 직접 수정 후 저장 안 함 | `SaveConfig()` 호출 |
| 2 | 게임 모듈에서 Editor Settings 접근 | `#if WITH_EDITOR` 가드 |
| 3 | ThumbnailRenderer `Draw` 안 무거운 작업 스코프 누락 | [[sources/ue-ref-07-profilingscopeRule]] — 컨텐츠 브라우저 스크롤 매번 호출 |
| 4 | Builder Brush 사용 | 5.x = Geometry Script 권장 |
| 5 | Commandlet 에서 `GEngine` 접근 | 헤드리스 모드 — 일부 시스템 미초기화 |

### 8. Build.cs (Editor 모듈만) 🛠

`UnrealEd` + `Settings` (별도) + `InteractiveToolsFramework` (Tools 사용 시).

## 9. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill (다른 7 UnrealEd): [[sources/ue-editor-unrealed-asseteditortoolkit]] / [[sources/ue-editor-unrealed-subsystems]] / [[sources/ue-editor-unrealed-kismet2]] / [[sources/ue-editor-unrealed-factories]] / [[sources/ue-editor-unrealed-elements]] / [[sources/ue-editor-unrealed-layers]] / [[sources/ue-editor-unrealed-materialeditor]]
- 횡단: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]] (ThumbnailRenderer)
