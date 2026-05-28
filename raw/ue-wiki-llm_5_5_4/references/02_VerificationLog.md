# 검증 로그 (Verification Log)

이 문서는 LLM Wiki 1차 개요 단계에서 **실제로 확인된 사실**, **사용한 데이터 출처**,
**알려진 한계**를 정리한다. 다른 모델/세션이 이어서 작업할 때 이 문서만 읽고 컨텍스트를
재구성할 수 있도록 자족적으로 작성한다.

---

## 1. 환경 (확인됨)

| 항목 | 값 | 출처 |
|------|-----|------|
| 엔진 루트 경로 | `C:\Unreal\UnrealEngine` | 사용자 지정, 마운트 확인됨 |
| 분석 대상 트리 | `C:\Unreal\UnrealEngine\Engine\Source\Runtime` | 디렉토리 존재 확인 |
| 엔진 버전 | **5.5.4** | `Engine/Build/Build.version` 직접 파싱 |
| BranchName | `UE5` | 동일 파일 |
| Changelist | `0` (IsLicenseeVersion=0, IsPromotedBuild=0) | 동일 파일 |
| Compatible Changelist | `47537391` | 동일 파일 |

`Build.version` 원본 내용:

```json
{
    "MajorVersion": 5,
    "MinorVersion": 7,
    "PatchVersion": 4,
    "Changelist": 0,
    "CompatibleChangelist": 47537391,
    "IsLicenseeVersion": 0,
    "IsPromotedBuild": 0,
    "BranchName": "UE5"
}
```

## 2. 디렉토리 구조 (확인됨)

`Engine/Source` 직속:

```
Developer/         (분석 범위 외)
Editor/            (분석 범위 외)
Programs/          (분석 범위 외)
Runtime/           ← 분석 대상
ThirdParty/        (분석 범위 외)
UnrealClient.Target.cs
UnrealEditor.Target.cs
UnrealGame.Target.cs
UnrealServer.Target.cs
```

`Engine/Source/Runtime/` 직속 폴더 수: **189**

## 3. 모듈 통계 (확인됨)

| 지표 | 수 | 비고 |
|------|----|------|
| Runtime 폴더 총 수 | 189 | `ls Runtime/ \| wc -l` |
| `.Build.cs` 직접 보유 모듈 | **152** | 빌드 단위(실제 모듈) |
| `.Build.cs` 없는 폴더 | **37** | "컨테이너 폴더" — 하위에 다시 모듈을 둠 |

### 컨테이너 폴더 전체 목록 (37개)

```
AdpcmAudioDecoder · Advertising · Analytics · Android · Apple
AudioCaptureImplementations · AudioDeviceEnumeration · AudioLink
AudioPlatformSupport · AugmentedReality · BinkAudioDecoder · CUDA
CorePreciseFP · CoreVerseVM · Datasmith · Experimental · IOS
Interchange · Linux · MRMesh · Net · NetworkReplayStreaming
NullInstallBundleManager · Online · OpusAudioDecoder · PacketHandlers
PlatformThirdPartyHelpers · Portal · RadAudioCodec · Solaris
StudioTelemetry · TextureUtilitiesCommon · Toolbox · Unix
VirtualProduction · VorbisAudioDecoder · Windows
```

이들은 카탈로그 표에서 의존성 컬럼이 `—`이고 폴더 컬럼이 `컨테이너`로 표시된다.

## 4. 카테고리 분류 (작성자 매핑)

| # | 카테고리 | 모듈 수 |
|---|----------|--------|
| 1 | Foundation | 34 |
| 2 | Engine | 16 |
| 3 | Rendering | 17 |
| 4 | UI/App | 13 |
| 5 | Animation | 9 |
| 6 | Physics | 9 |
| 7 | AI | 5 |
| 8 | Audio | 19 |
| 9 | Networking | 13 |
| 10 | Cinematic | 12 |
| 11 | VR/XR | 4 |
| 12 | VP | 2 |
| 13 | Platform | 8 |
| 14 | DevTools | 10 |
| 15 | Messaging | 5 |
| 16 | Time | 3 |
| 17 | Misc | 10 |
| **합계** | | **189** ✓ |

분류 근거: 각 모듈의 폴더명·`.Build.cs` 의존성·UE5 도메인 지식의 결합. **자동 검증된 분류가 아니다** — 다음 모델이 SKILL.md를 작성하면서 어색한 분류는 재배치해야 한다(예: `Datasmith`는 현재 Misc로 들어가 있으나 VP 쪽 성격도 강함).

## 5. 데이터 소스 (다른 모델이 그대로 사용 가능)

| 파일 | 용도 |
|------|------|
| `Engine/Build/Build.version` | 엔진 버전 정확도 검증 |
| `LLM_Wiki/catalog/runtime_meta.json` | 189개 모듈 메타: `has_build`, `public_deps[]`, `private_deps[]`, `has_public_dir`, `has_private_dir` |
| `LLM_Wiki/catalog/RuntimeIndex.md` | 사람이 읽는 카탈로그 (한 줄 요약 포함) |
| `LLM_Wiki/references/01_LayerMap.md` | L1~L7 의존 계층 다이어그램 |

`runtime_meta.json`은 `Engine/Source/Runtime/<Module>/<Module>.Build.cs` 를 정규식으로 파싱해서
`PublicDependencyModuleNames` / `PrivateDependencyModuleNames` 의 `new string[]{ ... }` 블록을 추출한 결과다.
`AddRange(new string[]{ ... })` 형태도 매치한다. 컨테이너 폴더(`.Build.cs` 없음)는 `has_build: false` 로 기록된다.

## 6. 알려진 한계 / 검증되지 않은 항목

다음 사항은 **이번 단계에서 검증하지 않았으므로 다음 모델은 SKILL 작성 전 직접 확인할 것**:

1. **카테고리 정합성**. 17개 카테고리는 작성자의 휴리스틱이며 전수 검증 안 됨. 특히 Foundation/Engine 경계, Audio 컨테이너 모듈, VP/Misc 경계는 재검토 후보.
2. **모듈별 한 줄 요약**. UE5 일반 지식 기반의 서술이며 5.5.4 트리에서 클래스/심볼이 그대로 존재하는지는 모듈별로 따로 확인해야 한다.
3. **의존성 파싱 누락 가능성**. 정규식이 다음 케이스를 놓칠 수 있다:
   - 조건부 추가 (`if (Target.Type == ...) PublicDependencyModuleNames.Add("X");` 의 단일 `Add`)
   - `string[]` 외 다른 컬렉션 초기화 패턴
   - 주석 처리된 의존성을 잘못 매치하는 경우는 없음 (주석은 정규식 매치 자체가 안 됨)
   따라서 `runtime_meta.json` 의 의존성 수는 **최저값**으로 간주한다.
4. **버전별 차이**. `Engine/Source/Runtime/` 폴더 자체에는 5.5.4에서 신규 추가/이름변경된 모듈이 있을 수 있다 (`StateStream`, `MassEntity`, `CoreVerseVM` 등은 비교적 최신). 5.4/5.5와 비교 검증은 안 함.
5. **컨테이너 폴더 내부**. 37개 컨테이너 폴더의 하위 모듈은 이번 단계에서 인덱스하지 않았다. 다음 단계에서 컨테이너 단위로 따로 스캔이 필요.
6. **Engine/Source/Editor·Developer·Programs·Plugins**. 분석 대상에 포함되지 않음.

## 7. 작업 산출물 (현재까지)

```
C:\Unreal\UnrealEngine\LLM_Wiki\
├── 00_Overview\
│   ├── 00_README.md              위키 진입점, 폴더 구조, Tier
│   ├── 01_LayerMap.md            L1~L7 의존 계층, 카테고리별 요약
│   └── 02_VerificationLog.md     이 문서
├── 01_Catalog\
│   ├── RuntimeIndex.md           189개 카탈로그 표
│   └── runtime_meta.json         의존성 원시 데이터
└── 02_Skills\                    (비어있음, 다음 단계에서 채움)
```

## 8. 다음 모델을 위한 작업 인계 메모

이어 받을 모델은 다음 순서로 진행하면 된다:

1. `references/00_README.md` 의 "Tier 분류" 절을 본다.
2. **Tier 1**부터 모듈을 하나씩 골라 `skills/<Module>/SKILL.md` 를 작성한다. 형식 가이드:
   - 개요 (역할/책임 한 단락)
   - 핵심 헤더와 클래스 (실제 `Public/`·`Classes/` 안의 헤더 경로 인용)
   - 자주 쓰는 API (시그니처와 한 줄 설명)
   - 사용 예제 (가능하면 5.5.4 트리 안의 호출처를 인용)
   - 관련 모듈 (`runtime_meta.json` 의존성 기반)
3. 작성 시 사실 인용은 **`Engine/Source/Runtime/<Module>/`** 안의 실제 파일을 직접 읽고 확인한다.
4. 작성한 모듈은 `references/00_README.md` "진행 단계" 표에 체크 표시.

작성 규칙은 `references/00_README.md` "작성 원칙" 섹션을 따른다(추측 금지, 사실에 기반).
