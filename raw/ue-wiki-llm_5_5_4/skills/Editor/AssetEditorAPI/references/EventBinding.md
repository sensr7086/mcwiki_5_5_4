---
name: editor-asseteditorapi-eventbinding
description: UAssetEditorSubsystem 이벤트 바인딩 표준 — OnAssetOpenedInEditor (2-param) + OnAssetEditorRequestClose (2-param) + UEditorSubsystem 안 Initialize/Deinitialize 페어. (parent — Editor/AssetEditorAPI/SKILL.md)
---

# UAssetEditorSubsystem 이벤트 바인딩 표준

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **요지**: 에셋 에디터 열림/닫힘 이벤트 후크 — `UEditorSubsystem` 안 표준 패턴.

---

## 이벤트 시그니처 [verified]

```cpp
// 1. OnAssetOpenedInEditor — 2-param event
DECLARE_EVENT_TwoParams(UAssetEditorSubsystem,
    FOnAssetOpenedInEditorEvent, UObject* /*Asset*/, IAssetEditorInstance* /*EditorInst*/);

// 2. OnAssetEditorRequestClose — 2-param event
DECLARE_EVENT_TwoParams(UAssetEditorSubsystem,
    FAssetEditorRequestCloseEvent, UObject* /*Asset*/, EAssetEditorCloseReason /*Reason*/);
```

---

## 표준 패턴 — UEditorSubsystem 안 등록/해제 페어

```cpp
UCLASS()
class UMyEditorSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()

    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);

        UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
        if (!AES) return;

        // 1. OnAssetOpenedInEditor (UObject*, IAssetEditorInstance*)
        OpenedHandle = AES->OnAssetOpenedInEditor().AddUObject(
            this, &UMyEditorSubsystem::HandleAssetOpened);

        // 2. OnAssetEditorRequestClose (UObject*, EAssetEditorCloseReason)
        CloseHandle = AES->OnAssetEditorRequestClose().AddUObject(
            this, &UMyEditorSubsystem::HandleAssetCloseRequest);
    }

    virtual void Deinitialize() override
    {
        if (UAssetEditorSubsystem* AES = GEditor ? GEditor->GetEditorSubsystem<UAssetEditorSubsystem>() : nullptr)
        {
            AES->OnAssetOpenedInEditor().Remove(OpenedHandle);
            AES->OnAssetEditorRequestClose().Remove(CloseHandle);
        }
        Super::Deinitialize();
    }

private:
    FDelegateHandle OpenedHandle;
    FDelegateHandle CloseHandle;

    void HandleAssetOpened(UObject* Asset, IAssetEditorInstance* EditorInst)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorSubsystem::HandleAssetOpened);
        UE_LOG(LogTemp, Log, TEXT("열림: %s (에디터=%s)"),
            *Asset->GetName(), *EditorInst->GetEditorName().ToString());
    }

    void HandleAssetCloseRequest(UObject* Asset, EAssetEditorCloseReason Reason)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorSubsystem::HandleAssetCloseRequest);
        if (Reason == EAssetEditorCloseReason::CloseAllEditorsForAsset)
        {
            // 에셋 강제 닫힘 대응
        }
    }
};
```

---

## 활용 시나리오

- **에셋 열림 로그 도구** — 사용 통계 / 자동 검증
- **자동 백업 도구** — 에디터 닫기 직전 (`AssetEditorHostClosed`) 자동 저장
- **Force Delete 보호** — `AssetForceDeleted` 시 의존 에셋 자동 정리
- **Refresh 후크** — `EditorRefreshRequested` 시 상태 보존

---

## 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | `OnAssetOpenedInEditor` 1-param 으로 추측 | 2-param 의무 (UObject*, IAssetEditorInstance*) |
| 2 | `OnAssetEditorRequestClose` UObject 1-param 으로 추측 | 2-param 의무 (UObject*, EAssetEditorCloseReason) |
| 3 | Delegate 등록 후 해제 누락 | Initialize/Deinitialize 페어 — Editor 종료 시 댕글링 |
| 4 | 콜백 첫 줄 TRACE_CPUPROFILER_EVENT_SCOPE 누락 | [`07_ProfilingScopeRule`](../../../../references/07_ProfilingScopeRule.md) 의무 |
