---
title: UE LiveCoding Module Path Hazard
slug: UE-LiveCoding-Module-Path-Hazard
kind: concept
status: live
confidence: 🟢 VAULT
last_updated: 2026-05-27
audit_5_5_4: pass  # 2026-05-27 Phase 2 engine grep 완료
engine_version: 5.5.4
related_concepts:
  - UE-Phantom-Header-Hallucination-Hazard
  - Editor-Only-4-Tier-Separation
related_synthesis:
  - mc-datatable-auto-blueprint
  - mc-datatable-auto-build-cycle-postmortem
tags: [livecoding, module-path, phantom-header, citation-rule]
sources:
  - "C:/Unreal/UnrealEngine/Engine/Source/Developer/Windows/LiveCoding/Public/ILiveCodingModule.h"
---

# UE LiveCoding Module Path Hazard

## 한 줄 요약

**`ILiveCodingModule` 은 `Editor/LiveCoding/` 이 아니라 `Developer/Windows/LiveCoding/` 에 있다.** Build.cs 의존 + include 작성 시 path 환각 (Editor 카테고리 가정) 회피 의무.

## 권위 (🟢 VAULT)

UE 5.7.4 engine grep 결과:

```
C:/Unreal/UnrealEngine/Engine/Source/Developer/Windows/LiveCoding/Public/ILiveCodingModule.h
```

`Editor/LiveCoding/` path 는 *존재하지 않는다*. 다른 LiveCoding 관련 헤더도 모두 같은 `Developer/Windows/LiveCoding/` 하위.

## API 표면 (검증된 멤버만)

```cpp
#define LIVE_CODING_MODULE_NAME "LiveCoding"

enum class ELiveCodingCompileFlags : uint8 { None = 0, WaitForCompletion = 1 << 0 };
enum class ELiveCodingCompileResult : uint8 {
    Success, NoChanges, InProgress, CompileStillActive,
    NotStarted, Failure, Cancelled
};

class ILiveCodingModule : public IModuleInterface {
public:
    virtual bool IsEnabledByDefault() const = 0;
    virtual bool HasStarted() const = 0;
    virtual bool IsEnabledForSession() const = 0;
    virtual bool CanEnableForSession() const = 0;
    virtual bool AutomaticallyCompileNewClasses() const = 0;
    virtual void ShowConsole() = 0;
    virtual void Compile() = 0;
    virtual bool Compile(ELiveCodingCompileFlags, ELiveCodingCompileResult*) = 0;
    virtual bool IsCompiling() const = 0;
    virtual void Tick() = 0;

    DECLARE_MULTICAST_DELEGATE(FOnPatchCompleteDelegate);
    virtual FOnPatchCompleteDelegate& GetOnPatchCompleteDelegate() = 0;
};
```

## 함정 family

### 1. Phantom path — "Editor/LiveCoding"

**LLM 환각 빈도 ★★★** — UE 도구의 직관적 위치는 `Editor/` 또는 `Editor/UnrealEd/` 이지만 LiveCoding 은 *Windows-specific Developer* 카테고리. 이유:

- Live Coding 의 internal 은 Live++ (Molecular Matters) 기술 기반 → Windows MSVC 의존.
- Mac/Linux 미지원 → `Source/Editor/` (cross-platform) 카테고리 부적합.

### 2. Build.cs 의존 누락

`PublicDependencyModuleNames` 에 `"LiveCoding"` 미추가 시 link error LNK2019. **Editor 모듈만 추가 가능** (Runtime/Shipping 빌드 차단 — 다른 함정).

### 3. IsEnabledForSession 의존성 (사용자 설정)

API 호출 자체는 성공해도 사용자가 Editor Preferences > Live Coding > Enable 미체크 시 `IsEnabledForSession() == false` → `Compile()` 무시됨. 사전 조건 4 단계 의무:

```cpp
1. FModuleManager::LoadModulePtr<ILiveCodingModule>(LIVE_CODING_MODULE_NAME)  // 모듈 로드
2. Settings.bAutoLiveCodingCompile == true                                     // 사용자 toggle
3. LiveCoding->IsEnabledForSession()                                           // Editor Preferences
4. !LiveCoding->IsCompiling()                                                  // 중복 회피
```

### 4. Compile() 의 thread 제약

`FModuleManager` + Live Coding internal 은 *GameThread 가정*. worker thread 에서 호출 시 race / crash. caller 가 `AsyncTask(ENamedThreads::GameThread, [](){ ... })` 마샬링 의무.

### 5. OnPatchCompleteDelegate leak

multicast delegate — `AddLambda` 만 하고 `Remove` 안 하면 매 호출마다 누적. 1회용 사용 시 lambda 안 self-remove 패턴:

```cpp
FDelegateHandle* HandlePtr = new FDelegateHandle();
*HandlePtr = LC->GetOnPatchCompleteDelegate().AddLambda([HandlePtr]() {
    if (ILiveCodingModule* LC2 = FModuleManager::GetModulePtr<ILiveCodingModule>(
        FName(LIVE_CODING_MODULE_NAME)))
    {
        LC2->GetOnPatchCompleteDelegate().Remove(*HandlePtr);
    }
    delete HandlePtr;
    // ... 실제 로직
});
```

## Citation Rule 회피 절차 (재현용)

```bash
# 1. path 확인
find /c/Unreal/UnrealEngine/Engine -name "ILiveCodingModule.h"

# 2. include 헤더 안 API 시그니처 확인
grep -nE "^\s*virtual " ILiveCodingModule.h

# 3. Build.cs path 확인 (Source 트리 카테고리)
find /c/Unreal/UnrealEngine/Engine/Source -type d -name "LiveCoding"
```

세 step 모두 통과 후 `🟢 VAULT` 인용 가능.

## MCDataTableAuto 적용 사례

- Phase 3c-3 후속 (2026-05-26) — `generate_row_struct` 가 .h 파일 생성 후 자동 컴파일 트리거.
- `UMCDataTableAutoSubsystem::TriggerLiveCodingCompile(InContextHint)` — 4 사전 조건 모두 처리.
- Settings.bAutoLiveCodingCompile toggle — 사용자 비활성화 가능 (default true).

## 변경 이력

- **2026-05-26** — 신규 작성 (Phase 3c-3 후속 — generate_row_struct 자동 Live Coding 통합).
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `ILiveCodingModule.h` 경로: **`Source/Developer/Windows/LiveCoding/Public/`** — 양 버전 동일 (Editor/ 가 아님 — 본 페이지의 모듈 경로 hazard 가 정확히 지적한 부분)
- 파일 byte-identical: **5.5.4 = 5.7.4 = 69 lines, 0 diff**
- **결정**: 🟢 본 페이지의 module path hazard 결론 5.5.4 에서도 그대로 유효 — Developer/Windows/ 경로 일관.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
