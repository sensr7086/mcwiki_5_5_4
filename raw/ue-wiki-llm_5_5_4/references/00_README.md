# UE 5.5.4 LLM Wiki

언리얼 엔진 5.5.4 (`C:\Unreal\UnrealEngine`) 의 **Engine/Source/Runtime** 트리(189개 모듈)를
LLM이 정확히 인용·검색·코드 생성에 활용할 수 있도록 정리하는 위키 + 스킬 저장소.

## 폴더 구조

```
LLM_Wiki/
├─ references/        ← 큰 그림(읽기 시작점)
│   ├─ 00_README.md           이 문서
│   ├─ 01_LayerMap.md         런타임 모듈 계층/의존 그래프 개요
│   ├─ 02_VerificationLog.md  검증 로그 + 작업 인계 메모
│   └─ 03_WikiHarness.md      ★ 시나리오별 sub-skill 묶음 (단일 진입점)
├─ catalog/         ← 전체 카탈로그(검색용 인덱스)
│   └─ RuntimeIndex.md        189개 모듈 카테고리 분류 + 1줄 요약 + Build.cs 통계
└─ skills/          ← 모듈별 스킬
    └─ <ModuleName>/
        ├─ SKILL.md           모듈 진입점 (개요·의존·API 요약·sub-skill 인덱스)
        └─ <SubSkill>/        모듈 내부의 기능 그룹별 sub-skill
            └─ SKILL.md       해당 그룹의 헤더·클래스·virtual·예제
```

**Sub-skill 분할 원칙**: 한 모듈 안에서 클래스가 많거나(예: CoreUObject 63개 UCLASS) 기능 도메인이 뚜렷이 나뉠 때, 메인 SKILL.md는 모듈 전체 진입점으로만 두고 클래스 상세는 기능 그룹(`UObject`, `Reflection`, `GC`, `Serialization` 등)별 sub-skill로 분산한다. 작은 모듈은 `SKILL.md` 한 파일이면 충분.

**작업 시작점은 [`03_WikiHarness.md`](./03_WikiHarness.md)** — 어떤 작업에 어떤 sub-skill을 묶어 읽어야 하는지 시나리오별 표가 있다. CLAUDE.md (`§0`/`§8.0`/`§11`) 가 이 문서를 가리키며, Claude는 코드 작성 전 해당 묶음을 사전 로드한다.

## 작성 원칙

1. **사실에 기반한다.** 추측은 명시("추정") 또는 생략. UE 5.5.4 트리에 실제로 존재하는 심볼만 인용.
2. **컨테이너 폴더와 모듈을 구분한다.** `.Build.cs`가 없는 폴더(예: `Online/`, `Net/`, `Apple/`, `IOS/`, `Datasmith/`)는 다수 서브모듈을 묶는 그룹이므로, 카탈로그에 "컨테이너"로 표시한다.
3. **의존성을 우선시한다.** 한 모듈을 이해하려면 의존하는 하위 모듈을 먼저 읽어야 한다 — `Engine` → `CoreUObject` → `Core` 순서로.
4. **개요(Overview) → 카탈로그(Catalog) → 스킬(Skills)** 순서로 깊이를 늘려간다. 처음 진입하는 LLM/사람은 `00_Overview`부터.

## 진행 단계

| 단계 | 산출물 | 상태 |
|------|--------|------|
| 1. 모듈 메타 수집 (.Build.cs 의존성 파싱) | `/tmp/runtime_meta.json`(임시) | ✅ |
| 2. 카테고리 분류 + 1줄 요약 | `catalog/RuntimeIndex.md` | ✅ |
| 3. 런타임 계층 맵 | `references/01_LayerMap.md` | ✅ |
| 4. 핵심 모듈 SKILL.md 작성 (Tier 1) | `skills/<Mod>/SKILL.md` | 🟨 진행 중 (CoreUObject ✅ / Core, Engine, Launch, Projects ⏳) |
| 4a. CoreUObject sub-skill 13개 분할 | `skills/CoreUObject/<Sub>/SKILL.md` | ✅ 완료 (UObject·Reflection·Property·Package·Interface·GC·Serialization·Network·Editor·Cooking·StructUtils·ObjectHandles·DeprecatedUProperty) |
| 4b. SlateCore (Tier 3) sub-skill 10개 | `skills/SlateCore/<Sub>/SKILL.md` | ✅ 완료 (SWidget·Layout·Drawing·Styling·Input·Application·Animation·Text·Types·Trace) |
| 4c. Slate 인하우스 툴 묶음 | `skills/Slate/<Sub>/SKILL.md` | 🟨 진행 중 (메인 §8 분리 원칙 + EditorApplication·Docking·Menu·Commands·GraphEditor ✅ / Notifications ⏸ / 게임 공통 7개 ⏳) |
| 5. Tier 2~3 도메인별 확장 | 동일 | ⏳ |
| 6. 전체 모듈 SKILL 보완 | 동일 | ⏳ |

## Tier 분류(작성 우선순위)

- **Tier 1 — Foundation**: `Core`, `CoreUObject`, `Engine`, `Launch`, `Projects`
- **Tier 2 — Rendering / RHI**: `RHI`, `RenderCore`, `Renderer`, `D3D12RHI`, `VulkanRHI`
- **Tier 3 — UI / Input**: `ApplicationCore`, `InputCore`, `SlateCore`, `Slate`, `UMG`
- **Tier 4 — Animation / Physics**: `AnimationCore`, `AnimGraphRuntime`, `PhysicsCore`
- **Tier 5 — Audio / Net / AI / Cinematic**: `AudioMixer`, `Networking`, `Sockets`, `AIModule`, `MovieScene`
- **Tier 6 — 그 외 도메인 모듈** (Cloth, Live Link, Media, VR/XR, VP, DevTools, Messaging…)

## 엔진 정보

- 버전: `5.5.4` (`Engine/Build/Build.version` 기준, BranchName=UE5)
- 대상 트리: `Engine/Source/Runtime/*` (189 모듈, 152 직접 빌드 + 37 컨테이너 폴더)
- 비대상(향후): `Engine/Source/Editor/`, `Engine/Source/Developer/`, `Engine/Source/Programs/`, `Engine/Plugins/`
