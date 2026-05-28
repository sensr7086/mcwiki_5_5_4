---
name: unrealed-misc
description: 🛠 GEditor + FEditorDelegates + FEditorUtilities + Slate / Tooltip 헬퍼 모음.
---

# UnrealEd · Misc sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: 다른 7개 sub-skill에 속하지 않는 UnrealEd의 기타 영역.
> **다루는 범위**: Settings · Preferences · ImportUtils · Tools · ViewportToolbar · Dialogs · Animation · Builders · CookOnTheSide · ThumbnailRendering · TexAligner · DragAndDrop · EditorState · Features · Instances · Serialization · Tests · Text · Commandlets · AutoReimport.

---

## 1. 개요

UnrealEd는 거대 모듈이라 8개 sub-skill로도 다 못 다룬다. 본 sub-skill은 **잡다한 헬퍼·유틸·서비스** 의 집합. 자주 사용하는 영역만 카테고리별로 한 줄 요약. 자세한 사용법은 각 헤더 파일 직접 참조.

---

## 2. Public/ 영역

### 2.1 Settings/ — 에디터 설정

| 헤더 (예시) | 의미 |
|------------|------|
| `EditorProjectSettings.h` | 프로젝트 단위 에디터 설정 |
| `EditorPerProjectUserSettings` (Classes/Settings) | 사용자 단위 |

ISettingsModule (`Settings` 모듈) 으로 등록 — Project Settings 패널에 노출.

### 2.2 Tools/ — 인터랙티브 툴 통합

`InteractiveToolsFramework` 모듈과의 어댑터. `UEdMode` 자손에서 InteractiveTool 사용 시.

### 2.3 ViewportToolbar/ — 뷰포트 툴바

5.x 모던 툴바 통합 (`UToolMenus` + 뷰포트 우상단 툴바 확장).

### 2.4 Dialogs/ — 모달 다이얼로그

| 헤더 | 의미 |
|------|------|
| (`SMessageDialog` 등) | 메시지 박스 |
| (`SCustomDialog` 등) | 커스텀 다이얼로그 |

`FMessageDialog::Open` 글로벌 헬퍼가 일반적 (Core 모듈).

### 2.5 ImportUtils/ — 임포트 헬퍼

`Factories` sub-skill 보조 — 임포트 전후 처리 유틸 (UV 변환·머티리얼 매핑 등).

### 2.6 AutoReimport/ — 자동 재임포트

파일 변경 감지 시 자동 재임포트. 사용자 설정 기반 (Project Settings → Loading → Auto Reimport).

### 2.7 EditorState/ — 에디터 상태 보존

세션 간 에디터 상태 (열린 에셋·뷰포트 위치 등) 직렬화.

### 2.8 DragAndDrop/ — 드래그앤드롭

`FAssetDragDropOp` 등 — 컨텐츠 브라우저에서 다른 에디터로 드래그.

### 2.9 Commandlets/ — Editor 전용 커맨드렛

`-run=Cook` 등 헤드리스 빌드 도구. `UCommandlet` 자손.

### 2.10 Text/ · Tests/ · Features/ · Instances/ · Serialization/

각각 텍스트 헬퍼, 자동화 테스트 통합, Editor Features (옵션 토글), 인스턴스 헬퍼, Editor 직렬화. 사용 빈도 낮음.

---

## 3. Classes/ 영역

### 3.1 Animation/ — Animation 에디터 클래스

Persona 모듈과 연계. `UAnimSequenceFactory` 등은 `Factories` sub-skill, Animation 데이터 모델 클래스가 여기.

### 3.2 Builders/ — Builder Brush

BSP (구식 지오메트리) 빌더. 거의 사용 안 함 (5.x는 Geometry Script 권장).

### 3.3 Preferences/ — 사용자 환경설정

| 클래스 | 의미 |
|--------|------|
| `UEditorPerProjectUserSettings` | 프로젝트별 사용자 설정 |
| `UEditorLoadingSavingSettings` | 로딩/저장 |
| `UEditorMiscSettings` | 잡다 |
| `ULevelEditorPlaySettings` | PIE 설정 |

### 3.4 Settings/ — 프로젝트 단위 설정

| 클래스 | 의미 |
|--------|------|
| `UEditorProjectAppearanceSettings` | 외관 |
| `UEditorProjectExperimentalSettings` | 실험 기능 |
| `UEditorProjectImportExportSettings` | 임포트 |

### 3.5 ThumbnailRendering/ — 에셋 썸네일

`UThumbnailRenderer` 자손 — 컨텐츠 브라우저 썸네일.

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

`UThumbnailManager::RegisterCustomRenderer` 또는 `UThumbnailRenderer` 자손에 `UCLASS(CustomConstructor)` + INI 설정.

### 3.6 TexAligner/ — 텍스처 정렬 (BSP 시절 유틸)

거의 사용 안 함.

### 3.7 UserDefinedStructure/ — Kismet2 sub-skill 참조

[`UnrealEd/Kismet2`](../Kismet2/SKILL.md) 의 UUserDefinedStruct 다룸.

### 3.8 CookOnTheSide/ — Cook 헬퍼

빌드 시스템 통합.

### 3.9 Editor/ — UEditorEngine 등 메인 진입

`UEditorEngine` 의 일부 분리된 헬퍼. 직접 다루는 일은 드묾 — `GEditor` 가 글로벌 인스턴스.

### 3.10 Exporters/ — Factories sub-skill 참조

[`UnrealEd/Factories`](../Factories/SKILL.md) 가 다룸.

---

## 4. 자주 쓰는 진입점 모음

| 시나리오 | 진입점 |
|----------|--------|
| 메시지 박스 | `FMessageDialog::Open(EAppMsgType::YesNo, MsgText)` (Core) |
| 프로젝트 설정 등록 | `ISettingsModule::Get().RegisterSettings(...)` (Settings 모듈) |
| 사용자 설정 읽기 | `GetMutableDefault<UEditorPerProjectUserSettings>()->bMySetting` |
| PIE 시작/정지 | `GEditor->RequestPlaySession(...)` / `GEditor->RequestEndPlayMap()` |
| Editor 모드 변경 | `GLevelEditorModeTools().ActivateMode(...)` (EditorFramework) |
| 썸네일 등록 | `UMyAssetThumbnailRenderer` 자손 + `UCLASS` |
| 자동화 테스트 | `IMPLEMENT_SIMPLE_AUTOMATION_TEST` (AutomationTest.h, Core) |

---

## 5. 함정

| 함정 | 회피 |
|------|------|
| `UEditorPerProjectUserSettings` 직접 수정 후 저장 안 함 | `SaveConfig()` 호출 |
| 게임 모듈에서 Editor Settings 접근 | `#if WITH_EDITOR` 가드 |
| ThumbnailRenderer 의 Draw 안 무거운 작업에 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) — 컨텐츠 브라우저 스크롤 시 매번 호출 |
| Builder Brush 사용 | 5.x는 Geometry Script 권장 |
| Commandlet 에서 GEngine 접근 | 헤드리스 모드라 일부 시스템 미초기화 |

---

## 6. 에디터 전용 🛠

전체 sub-skill 에디터 빌드 전용.

---

## 7. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — 메인
- [`UnrealEd/AssetEditorToolkit`](../AssetEditorToolkit/SKILL.md) · [`Subsystems`](../Subsystems/SKILL.md) · [`Kismet2`](../Kismet2/SKILL.md) · [`Factories`](../Factories/SKILL.md) · [`Elements`](../Elements/SKILL.md) · [`Layers`](../Layers/SKILL.md) · [`MaterialEditor`](../MaterialEditor/SKILL.md) — 다른 7개 sub-skill
- 교차: [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
