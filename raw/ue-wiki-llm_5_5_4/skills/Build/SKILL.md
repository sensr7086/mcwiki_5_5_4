---
name: ue-build
description: UE 5.5.4 빌드/패키징/배포 위키. UnrealBuildTool(UBT) + UnrealAutomationTool(UAT) + Build.cs/Target.cs + Cooking + Pak/IoStore + Shipping/Development/Test 구성 + DLC/Patch + BuildGraph. Cooked Build 안전 + Hot Reload vs Live Coding + Module 의존 4단 분리.
---

# Build — UE 5.5.4 빌드 / 패키징 / 배포

> **카테고리** — Tier 2 (인프라 / DevOps)
> **대표 도구** — UnrealBuildTool (UBT), UnrealAutomationTool (UAT), Build.cs, Target.cs, BuildGraph
> **트리거 키워드** — UnrealBuildTool, UBT, UAT, Build.cs, Target.cs, Cooking, Pak, IoStore, Shipping, Development, Test, DLC, Patch, BuildGraph

본 sub-skill은 모듈 의존 / 빌드 구성 / 패키징 / 배포 표준을 정리. Editor 전용 4단 분리는 [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) 페어.

---

## 1. Build.cs — 모듈 의존 표준

```cs
public class MyGame : ModuleRules
{
    public MyGame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new[] {
            "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput"
        });

        PrivateDependencyModuleNames.AddRange(new[] {
            "Slate", "SlateCore", "UMG", "AIModule", "GameplayTasks",
            "GameplayAbilities", "GameplayTags", "NavigationSystem"
        });

        // 에디터 전용 의존 — 4단 분리 §1
        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(new[] {
                "UnrealEd", "PropertyEditor", "ToolMenus", "EditorScriptingUtilities"
            });
        }

        // 플랫폼 분기
        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            PublicDefinitions.Add("MYGAME_WIN64=1");
        }
    }
}
```

> 🚨 **Public vs Private 의존** — Public은 헤더에서 노출, Private은 .cpp에서만. 헤더 최소 포함 (`docs/CLAUDE.md §3.2`).

---

## 2. Target.cs — 빌드 구성

| 구성 | 용도 | 디파인 |
|------|------|--------|
| Development | 개발 + 디버그 가능 | `UE_BUILD_DEVELOPMENT=1` |
| DebugGame | 풀 디버그 (CRT 디버그 라이브러리) | `UE_BUILD_DEBUG=1` |
| Test | Shipping 동작 + 디버그 명령 일부 | `UE_BUILD_TEST=1` |
| Shipping | 배포 (모든 디버그 제거) | `UE_BUILD_SHIPPING=1` |

```cs
public class MyGameTarget : TargetRules
{
    public MyGameTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;  // Editor / Server / Client / Program
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;  // 5.5.4도 5_5 OK
        ExtraModuleNames.AddRange(new[] { "MyGame" });
    }
}
```

> 🚨 `Shipping` — `UE_LOG`, `check`, `ensure` 모두 제거. `checkSlow`는 Development만 [verified].

---

## 3. Cooking + Packaging

### 3.1 Cooking 기본

- **Cook** = 자산을 플랫폼별 바이너리로 변환 (PNG → PVRTC, FBX → 압축 메시)
- **DDC** (Derived Data Cache) — Cook 결과 캐시. Local + Shared
- **Iterative Cook** — 변경된 자산만 재쿡

### 3.2 Pak vs IoStore (5.x)

| 포맷 | 특징 | 사용 |
|------|------|------|
| `.pak` | 단일 파일 패키지 (legacy) | UE4 호환 |
| **IoStore** (`.utoc` + `.ucas`) | 5.x 표준 — 빠른 로드 + Streaming | 5.x 신규 프로젝트 의무 권장 |

`DefaultGame.ini`:

```ini
[/Script/UnrealEd.ProjectPackagingSettings]
bUseIoStore=True
bGenerateChunks=True
bChunkHardReferencesOnly=False
```

### 3.3 Cook 명령 (UAT)

```bash
# Editor 메뉴 — Project Launcher / Package Project

# Command line (BuildCookRun)
RunUAT.bat BuildCookRun ^
    -project="MyGame.uproject" ^
    -platform=Win64 ^
    -clientconfig=Shipping ^
    -cook -allmaps -build -stage -pak -archive ^
    -archivedirectory="C:\Builds\MyGame"
```

> 🚨 `-allmaps` 또는 `Maps to Cook` 명시적 지정 — 누락 시 missing reference만 쿡 → 런타임 LoadMap 실패 [grep-listed].

---

## 4. Hot Reload vs Live Coding (5.x)

| 시스템 | 작동 | 함정 |
|--------|------|------|
| Hot Reload (legacy) | DLL 재로드 | UPROPERTY 변경 시 인스턴스 손실 |
| **Live Coding** (5.x 표준) | 패치 in-place | 헤더 변경 시 재시작 필요 |

> ⚠ Live Coding은 `Ctrl+Alt+F11` 단축키. 컴파일 에러 시 에디터에 즉시 표시 [grep-listed].

---

## 5. Plugin 빌드 (.uplugin)

```json
{
    "FileVersion": 3,
    "Version": 1, "VersionName": "1.0",
    "FriendlyName": "MyPlugin",
    "Modules": [
        {
            "Name": "MyPluginRuntime",
            "Type": "Runtime",
            "LoadingPhase": "Default"
        },
        {
            "Name": "MyPluginEditor",
            "Type": "Editor",
            "LoadingPhase": "PostEngineInit"
        }
    ]
}
```

| Module Type | 빌드 포함 |
|-------------|----------|
| Runtime | 모든 빌드 |
| Editor | `bBuildEditor` 시만 (Cooked Shipping 제외) |
| EditorNoCommandlet | Editor (Commandlet 제외) |
| Developer | Development + Test, Shipping 제외 |
| RuntimeAndProgram | + 별도 Program |
| UncookedOnly | Editor + Commandlet, Cooked 제외 |

> 🚨 **4단 분리** — `05_EditorOnlyIndex` Tier 1: 모듈 분리 / Tier 2: uplugin Type / Tier 3: Build.cs `bBuildEditor` / Tier 4: `#if WITH_EDITOR`.

---

## 6. DLC / Patch (Chunk + Release)

### 6.1 Release Version

```bash
RunUAT.bat BuildCookRun -project=... -platform=Win64 -clientconfig=Shipping ^
    -cook -allmaps -createreleaseversion=1.0
```

→ `Releases/1.0/Win64/AssetRegistry.bin` 생성. 이후 패치는 이 base 위에.

### 6.2 Patch

```bash
... -basedonreleaseversion=1.0 -generatepatch
```

→ 변경 자산만 Pak으로 만든 패치. 클라이언트가 base 위에 마운트.

### 6.3 DLC

```bash
... -basedonreleaseversion=1.0 -DLCName=MyDLC
```

→ DLC 전용 Plugin 폴더 자산을 별도 Pak. 런타임 `IPlatformFilePak` 마운트.

---

## 7. BuildGraph — CI/CD 표준

`BuildGraph` (XML 기반) — Epic 표준 빌드 파이프라인:

```xml
<BuildGraph>
    <Agent Name="Cook" Type="Win64">
        <Node Name="Compile">
            <Compile Target="MyGameEditor" Configuration="Development"/>
        </Node>
        <Node Name="Cook" Requires="Compile">
            <Cook Project="MyGame.uproject" Platform="Win64"/>
        </Node>
        <Node Name="Stage" Requires="Cook">
            <Stage Project="MyGame.uproject"/>
        </Node>
    </Agent>
</BuildGraph>
```

> Jenkins / TeamCity / GitHub Actions 통합 — `RunUAT.bat BuildGraph -script=Build.xml -target=Stage`.

---

## 8. 자주 만나는 함정

| 함정 | 원인 | 해결 |
|------|------|------|
| Cooked Shipping에서 `UnrealEd` link 에러 | 게임 모듈이 Editor 의존 | `05_EditorOnlyIndex` 4단 분리 |
| 자산이 Cook 안 됨 | `Maps to Cook` 누락 / 하드 ref 없음 | `Always Cook` 폴더 / `+CookAdditional...` |
| Live Coding 후 BP 변수 사라짐 | UPROPERTY 추가 시 | 에디터 재시작 |
| Pak 마운트 실패 | Mount Point 불일치 | `FCoreDelegates::OnMountPak` 검증 |
| DLC가 base와 충돌 | 같은 자산 포함 | `-CookCultures` / 자산 분리 |

---

## 9. 정책 의무

- 🚨 `05_EditorOnlyIndex` — 4단 분리 의무 (Cooked Shipping 깨짐 방지)
- 🚨 `15_EvaluatorRecipe` Stage 2 — Cooked Development + Cooked Shipping 빌드 통과
- 🚨 `16_PolicyPriority` Tier 1 — Compile / Cook 통과는 다른 모든 정책보다 우선

---

## 10. 외부 검증

- 위키에 없는 BuildGraph 옵션 → docs.unrealengine.com `BuildGraph` (`references/19_ExternalSourcesGuide.md`)
- Zen Server (5.x DDC 호스팅) → 위키에 없음, `[inferred]`
- Project Launcher 프로필 → Epic 공식 문서

---

## 관련

- 🛠 [`references/05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — 4단 분리
- 🔍 [`references/15_EvaluatorRecipe.md`](../../references/15_EvaluatorRecipe.md) — Cooked 검증
- ⚖ [`references/16_PolicyPriority.md`](../../references/16_PolicyPriority.md)
- 📋 [`docs/INSTALL.md`](../../docs/INSTALL.md)
- 🌐 [`references/19_ExternalSourcesGuide.md`](../../references/19_ExternalSourcesGuide.md)
