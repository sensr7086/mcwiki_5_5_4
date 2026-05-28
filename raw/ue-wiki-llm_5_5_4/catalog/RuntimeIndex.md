# UE 5.5.4 Runtime 모듈 카탈로그 인덱스

- 총 모듈 수: **189** (Engine/Source/Runtime/*)
- 분류 카테고리: **17**
- 표 컬럼: 모듈명 / Public Deps 수 / Private Deps 수 / Public·Private 폴더 / 한 줄 요약

> 주: 일부 폴더(예: Apple/IOS/Online/Net/Datasmith 등)는 직접적인 .Build.cs가 없는 **컨테이너 폴더**로, 하위 모듈을 묶기 위한 그룹핑에 가깝습니다.

## Foundation

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AutoRTFM` | 0 | 0 | Pub/Pri | 자동 메모리 트랜잭션(소프트웨어 트랜잭셔널 메모리). 동시성·롤백 지원 실험 인프라. |
| `BuildSettings` | 0 | 0 | Pub/Pri | 빌드 시점 상수(엔진 버전, 브랜치명, ChangeList) 임베딩. 모든 모듈에 안전하게 link 가능. |
| `Cbor` | 1 | 0 | Pub/Pri | CBOR(Concise Binary Object Representation) 직렬화. |
| `ColorManagement` | 1 | 0 | Pub/Pri | 색공간 변환 코어. |
| `Core` | 0 | 0 | Pub/Pri | 최저수준 기반: 컨테이너(TArray/TMap/FString), 메모리, 스레드/태스크, 로그(LogChannel), 파일 IO 추상, 타이밍, 플랫폼 추상(FPlatform...)을 제공. 모든 모듈의 시작점. |
| `CoreOnline` | 3 | 0 | Pub/Pri | 온라인 서비스용 공통 타입(FUniqueNetId 등)을 Engine/Online 서브시스템에서 분리한 경량 의존성 코어. |
| `CorePreciseFP` | — | — | 컨테이너 | 엄격한 부동소수점 모드용 보조 코어. 결정론적 시뮬·네트워크 동기화용 정밀 수치. |
| `CoreUObject` | 3 | 3 | Pub/Pri | UObject 시스템: 리플렉션(UClass/UProperty/UFunction), 가비지 컬렉터, 직렬화(FArchive), 패키지/Asset 로딩, CDO, FName/FSoftObjectPath. |
| `CoreVerseVM` | — | — | 컨테이너 | Verse 언어 런타임 VM 코어. CoreUObject와 분리된 Verse 객체/실행 모델. |
| `DeveloperSettings` | 0 | 3 | Pub/Pri | UDeveloperSettings 베이스(프로젝트/엔진 ini 자동 매핑). |
| `FieldNotification` | 2 | 0 | Pub/Pri | 프로퍼티 변경 알림(MVVM/UMG ViewModel 베이스). |
| `GameplayTags` | 4 | 6 | Pub/Pri | FGameplayTag 계층 태그 시스템 — Ability/Behavior 전반. |
| `GeometryCore` | 1 | 1 | Pub/Pri | TMesh/Spatial 자료구조, 거리/교차/메시 연산 코어. |
| `IPC` | 0 | 0 | Pub/Pri | 프로세스 간 통신 채널. |
| `ImageCore` | 0 | 0 | Pub/Pri | FImage / FImageView 픽셀 포맷 변환·블릿 코어. |
| `Instrumentation` | 0 | 0 | Pub/Pri | Sanitizer/계측 빌드용 런타임 인프라. |
| `Interchange` | — | — | 컨테이너 | Interchange 임포트 파이프라인 컨테이너 — FBX/glTF/USD 등 통합 임포터 런타임. |
| `Json` | 2 | 0 | Pub/Pri | JSON 파서/리더/라이터 (FJsonObject, TJsonReader/Writer). |
| `JsonUtilities` | 3 | 0 | Pub/Pri | UStruct ↔ JSON 양방향 매핑 헬퍼(FJsonObjectConverter). |
| `MathCore` | 1 | 0 | Pub/Pri | 추가 수학 유틸 (행렬/회전/보간 확장). |
| `OodleDataCompression` | 0 | 0 | — | Oodle 압축 통합. |
| `PakFile` | 0 | 0 | Pub/Pri | .pak 가상 파일 시스템(IPlatformFilePak) — 패키징/시프 마운트·시그니처. |
| `Projects` | 2 | 1 | Pub/Pri | uproject/uplugin 파일 파싱 및 플러그인 매니페스트 시스템. |
| `PropertyPath` | 0 | 2 | Pub/Pri | 리플렉션 기반 프로퍼티 경로 표현. |
| `RSA` | 0 | 0 | Pub/Pri | RSA 서명/검증 (서명된 PAK/Pak 시그니처용). |
| `SandboxFile` | 0 | 0 | Pub/Pri | 쿠킹용 샌드박스 파일 시스템(개발/리다이렉트). |
| `Serialization` | 3 | 1 | Pub/Pri | Bulk 데이터/메모리·파일 아카이브, 압축 직렬화 유틸. |
| `StreamingFile` | 3 | 0 | Pub/Pri | 원격/스트리밍 파일 IO. |
| `SymsLib` | 0 | 0 | — | 심벌 파싱 라이브러리(크래시 디버깅용). |
| `TraceLog` | 0 | 0 | Pub/Pri | Unreal Insights용 저오버헤드 트레이스/이벤트 로깅 코어. CPU/GPU/메모리 채널. |
| `TypedElementFramework` | 2 | 0 | Pub/Pri | Typed Element 시스템(에셋/월드 통합 인터페이스 핸들). |
| `TypedElementRuntime` | 3 | 0 | Pub/Pri | Typed Element 런타임 구현체(Actor/Component 등). |
| `UniversalObjectLocator` | 2 | 0 | Pub/Pri | 범용 객체 식별자(원격/지연/대체 가능 핸들). |
| `XmlParser` | 0 | 1 | Pub/Pri | 경량 XML 파서. |

## Engine

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AssetRegistry` | 0 | 7 | Pub/Pri | 에셋 메타데이터 인덱스/태그 검색·라이트 종속성. |
| `BlueprintRuntime` | 0 | 2 | Pub/Pri | 쿠킹된 블루프린트 VM 런타임 보조. |
| `Engine` | 39 | 33 | Pub/Pri | 게임플레이 프레임워크 본체: AActor, UWorld, ULevel, APawn, AGameModeBase, UGameInstance, Tick/Subsystem, 컴포넌트, 콜리전 채널 등. |
| `EngineMessages` | 1 | 1 | Pub/Pri | MessageBus용 엔진 공용 구조체. |
| `EngineSettings` | 1 | 1 | Pub/Pri | GameMapsSettings/GeneralProjectSettings 등 엔진 ini 백킹 UDeveloperSettings. |
| `Foliage` | 0 | 5 | Pub/Pri | 정적/계절 식생 인스턴싱(IFP/HISM). |
| `GameplayDebugger` | 3 | 6 | Pub/Pri | 게임플레이 카테고리별 온스크린 디버그 뷰. |
| `GameplayMediaEncoder` | 0 | 11 | Pub/Pri | 게임플레이 비디오/오디오 인코딩(미디어 캡처). |
| `GameplayTasks` | 5 | 0 | Pub/Pri | 비동기 게임플레이 동작 그래프 — GAS/AI 병렬 작업 베이스. |
| `Landscape` | 0 | 25 | Pub/Pri | 지형 시스템: 하이트/레이어/콜리전·LOD 스트리밍. |
| `Launch` | 0 | 37 | Pub/Pri | 엔진 진입점(GuardedMain → FEngineLoop). 초기화/Tick 루프/셧다운 오케스트레이션. |
| `MoviePlayer` | 2 | 10 | Pub/Pri | 맵 로딩 동영상/애니메이션 재생기. |
| `MoviePlayerProxy` | 0 | 1 | Pub/Pri | MoviePlayer를 Engine 의존 없이 호출하기 위한 프록시. |
| `PreLoadScreen` | 4 | 9 | Pub/Pri | 초기 부팅 시 로드 화면(엔진 초기화 이전부터 표시). |
| `UELibrary` | 3 | 2 | Pub/Pri | UE를 라이브러리로 임베드하는 호스팅 레이어. |
| `UnrealGame` | 0 | 3 | Pri | 기본 UnrealGame 타겟 정적 진입(쿠킹된 게임 빌드). |

## Rendering

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `D3D12RHI` | 0 | 0 | Pub/Pri | Direct3D 12 RHI 백엔드. |
| `IESFile` | 0 | 0 | Pub/Pri | IES 광 프로파일 파서. |
| `ImageWrapper` | 0 | 1 | Pub/Pri | PNG/JPEG/EXR/BMP 인코더/디코더. |
| `ImageWriteQueue` | 4 | 3 | Pub/Pri | 비동기 이미지 디스크 라이트 큐. |
| `MaterialShaderQualitySettings` | 0 | 8 | Pri | 머티리얼 셰이더 품질 등급. |
| `NullDrv` | 0 | 0 | Pub/Pri | 헤드리스 더미 RHI(서버/유닛 테스트). |
| `OpenColorIOWrapper` | 1 | 1 | Pub/Pri | OCIO 변환 래퍼. |
| `OpenGLDrv` | 2 | 7 | Pub/Pri | OpenGL/ES RHI 백엔드 (모바일/레거시). |
| `RHI` | 0 | 0 | Pub/Pri | 렌더 하드웨어 인터페이스 추상층: 버퍼/텍스처/뷰/커맨드 리스트/셰이더 바인딩. |
| `RHICore` | 0 | 0 | Pub/Pri | RHI 백엔드 공통 헬퍼. |
| `RenderCore` | 2 | 5 | Pub/Pri | RDG(렌더 그래프), 셰이더 매니저, 머티리얼 셰이더 컴파일 파이프라인 코어. |
| `Renderer` | 2 | 11 | Pub/Pri | 디퍼드/포워드 렌더 패스, 라이팅, 그림자, 포스트프로세스 — Lumen/Nanite 포함. |
| `SlateNullRenderer` | 0 | 6 | Pub/Pri | 헤드리스 Slate 렌더러. |
| `SlateRHIRenderer` | 0 | 11 | Pub/Pri | Slate를 RHI 위에서 렌더링. |
| `StreamingPauseRendering` | 3 | 6 | Pub/Pri | 스트리밍 일시정지 화면. |
| `SynthBenchmark` | 3 | 1 | Pub/Pri | GPU 합성 벤치마크. |
| `VulkanRHI` | 0 | 13 | Pub/Pri | Vulkan RHI 백엔드. |

## UI/App

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AdvancedWidgets` | 4 | 3 | Pub/Pri | 추가 고급 위젯 모음. |
| `AppFramework` | 5 | 1 | Pub/Pri | 툴/유틸 앱(작은 Slate 도구)용 베이스. |
| `ApplicationCore` | 1 | 0 | Pub/Pri | OS 레벨 윈도우/이벤트/디스플레이/입력 추상(GenericApplication, GenericWindow). |
| `CEF3Utils` | 0 | 1 | Pub/Pri | CEF3 통합 유틸. |
| `GameMenuBuilder` | 6 | 0 | Pub/Pri | 단순 게임 메뉴 빌더 헬퍼(샘플성). |
| `InputCore` | 2 | 0 | Pub/Pri | FKey/EKeys 입력 식별자/매핑 코어. |
| `InputDevice` | 0 | 2 | Pub/Pri | 입력 디바이스 플러그인 인터페이스(IInputDevice). |
| `Slate` | 6 | 1 | Pub/Pri | 표준 위젯(SButton/STextBlock/SListView 등) 라이브러리 + Application 통합. |
| `SlateCore` | 6 | 0 | Pub/Pri | 선언형 위젯·레이아웃·드로우 엘리먼트 코어(SWidget/FSlateBrush). |
| `UMG` | 6 | 13 | Pub/Pri | Slate 위에 UWidget(블루프린트 노출) 게임 UI 레이어 + UWidgetBlueprint. |
| `WebBrowser` | 2 | 12 | Pub/Pri | CEF3 기반 임베디드 브라우저 위젯. |
| `WebBrowserTexture` | 0 | 12 | Pub/Pri | WebBrowser 페이지를 텍스처로 노출. |
| `WidgetCarousel` | 0 | 5 | Pub/Pri | 캐러셀형 위젯. |

## Animation

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AnimGraphRuntime` | 5 | 1 | Pub/Pri | 애니메이션 그래프 노드(블렌드/스테이트머신/제어 릭 런타임). |
| `AnimationCore` | 2 | 0 | Pub/Pri | 본/리타게팅/IK 솔버/커브 등 저수준 애니메이션 수학. |
| `ClothingSystemRuntimeCommon` | 3 | 2 | Pub/Pri | 의상 시뮬레이션 공용 런타임. |
| `ClothingSystemRuntimeInterface` | 2 | 0 | Pub/Pri | Cloth 백엔드 인터페이스. |
| `ClothingSystemRuntimeNv` | 4 | 1 | Pub/Pri | NvCloth 백엔드(레거시). |
| `LiveLinkAnimationCore` | 4 | 0 | Pub/Pri | LiveLink 애니메이션 데이터 적용 코어. |
| `LiveLinkInterface` | 2 | 0 | Pub/Pri | LiveLink 데이터 구조/소스 인터페이스. |
| `LiveLinkMessageBusFramework` | 5 | 0 | Pub/Pri | MessageBus 기반 LiveLink 전송. |
| `SkeletalMeshDescription` | 4 | 0 | Pub/Pri | 스켈레탈 메시 기술 데이터(메시 임포트/편집용). |

## Physics

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `GeometryFramework` | 12 | 2 | Pub/Pri | 런타임 동적 메시 컴포넌트(UDynamicMesh/UDynamicMeshComponent). |
| `InteractiveToolsFramework` | 5 | 6 | Pub/Pri | 인터랙티브 툴(모델링 툴키트) 런타임 프레임워크 — 제스처/입력/변환 행위. |
| `MeshConversion` | 5 | 0 | Pub/Pri | MeshDescription ↔ DynamicMesh ↔ StaticMesh 변환. |
| `MeshConversionEngineTypes` | 8 | 0 | Pub/Pri | 변환에 필요한 엔진 타입 분리 모듈. |
| `MeshDescription` | 2 | 0 | Pub/Pri | FMeshDescription — 임포트/편집용 중간 메시 표현. |
| `MeshUtilitiesCommon` | 0 | 1 | Pub/Pri | 메시 유틸 공용. |
| `PhysicsCore` | 1 | 2 | Pub/Pri | Chaos 통합 콜리전 셋업·서피스/머티리얼 등 물리 코어 타입. |
| `RawMesh` | 0 | 2 | Pub/Pri | FRawMesh 레거시 메시 표현. |
| `StaticMeshDescription` | 3 | 2 | Pub/Pri | 스태틱 메시 전용 MeshDescription 래핑. |

## AI

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AIModule` | 6 | 3 | Pub/Pri | BehaviorTree, EQS, AIController, Perception, BlackBoard. |
| `MassEntity` | 5 | 0 | Pub/Pri | Mass ECS 엔티티/프래그먼트/프로세서 기반 대규모 시뮬레이션. |
| `NavigationSystem` | 5 | 2 | Pub/Pri | 월드 내비메시 빌드/쿼리/탐색/회피. |
| `Navmesh` | 0 | 1 | Pub/Pri | Recast/Detour 통합 — NavMesh 타일 데이터. |
| `StateStream` | 2 | 0 | Pub/Pri | 결정론적 상태 스트리밍(렌더/AI 동기화용 신규 시스템). |

## Audio

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AdpcmAudioDecoder` | — | — | 컨테이너 | ADPCM 디코더(컨테이너 폴더). |
| `AudioAnalyzer` | 2 | 3 | Pub/Pri | 오디오 분석(Loudness/FFT/Onset). |
| `AudioCaptureCore` | 2 | 1 | Pub/Pri | 오디오 입력 캡처 추상. |
| `AudioCaptureImplementations` | — | — | 컨테이너 | 플랫폼별 오디오 캡처 구현 컨테이너. |
| `AudioDeviceEnumeration` | — | — | 컨테이너 | 오디오 입출력 디바이스 열거. |
| `AudioExtensions` | 4 | 0 | Pub/Pri | Modulation/Parameter/Soundfield 확장 인터페이스. |
| `AudioLink` | — | — | 컨테이너 | 외부 오디오 엔진(Wwise 등) 연동 브리지. |
| `AudioMixer` | 3 | 10 | Pub/Pri | 신규 오디오 믹서(AudioMixerSourceVoice, Submix 그래프). |
| `AudioMixerCore` | 0 | 3 | Pub/Pri | AudioMixer 백엔드/플랫폼 디바이스 추상. |
| `AudioPlatformConfiguration` | 0 | 2 | Pub/Pri | 플랫폼별 오디오 설정. |
| `AudioPlatformSupport` | — | — | 컨테이너 | 플랫폼별 보조 컨테이너. |
| `BinkAudioDecoder` | — | — | 컨테이너 | BinkAudio 디코더(컨테이너 폴더). |
| `NonRealtimeAudioRenderer` | 0 | 6 | Pub/Pri | 오프라인 비실시간 오디오 렌더링. |
| `OpusAudioDecoder` | — | — | 컨테이너 | Opus 디코더(컨테이너 폴더). |
| `RadAudioCodec` | — | — | 컨테이너 | RAD Audio 코덱 통합. |
| `SignalProcessing` | 1 | 2 | Pub/Pri | DSP 기본 블록(필터/딜레이/엔벨로프/리버브 컴포넌트). |
| `SoundFieldRendering` | 0 | 5 | Pub/Pri | 앰비소닉 등 사운드 필드 렌더링. |
| `UEWavComp` | 0 | 0 | — | WAV 압축 유틸. |
| `VorbisAudioDecoder` | — | — | 컨테이너 | Vorbis 디코더. |

## Networking

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `CookOnTheFly` | 4 | 0 | Pri | 쿠킹 온더플라이 클라/서버. |
| `ExternalRPCRegistry` | 0 | 5 | Pub/Pri | 외부 RPC 엔드포인트 등록(자동화/원격 디바이스). |
| `FriendsAndChat` | 3 | 1 | Pub/Pri | 친구/채팅 서비스 런타임. |
| `Net` | — | — | 컨테이너 | 네트워킹 컨테이너(서브모듈). |
| `NetworkFile` | 0 | 4 | Pub/Pri | 네트워크 경유 파일 IO 클라이언트. |
| `NetworkFileSystem` | 2 | 8 | Pub/Pri | 쿠커 → 디바이스 네트워크 파일 서버. |
| `NetworkReplayStreaming` | — | — | 컨테이너 | 리플레이 스트리밍(컨테이너). |
| `Networking` | 2 | 0 | Pub/Pri | TCP/UDP 소켓 헬퍼·메시지 프로토콜 베이스. |
| `Online` | — | — | 컨테이너 | OnlineSubsystem 모음 컨테이너. |
| `PacketHandlers` | — | — | 컨테이너 | 패킷 변환 체인(암호화/오라클/PacketHandler 컨테이너). |
| `Sockets` | 0 | 2 | Pub/Pri | ISocket/ISocketSubsystem 플랫폼 추상. |
| `StorageServerClient` | 0 | 6 | Pri | Iostore/Storage Server 프로토콜 클라이언트. |
| `StorageServerClientDebug` | 0 | 6 | Pri | Storage Server 디버그 도구. |

## Cinematic

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AVEncoder` | 4 | 4 | Pub/Pri | 공통 비디오/오디오 인코더 추상. |
| `AVIWriter` | 1 | 0 | Pub/Pri | AVI 컨테이너 라이팅. |
| `CinematicCamera` | 0 | 8 | Pub/Pri | ACineCameraActor/UCineCameraComponent 시네마틱 카메라. |
| `LevelSequence` | 7 | 7 | Pub/Pri | 레벨에 배치되는 ALevelSequenceActor + ULevelSequence. |
| `Media` | 2 | 0 | Pub/Pri | 미디어 플레이어/소스/플레이 체인 코어. |
| `MediaAssets` | 8 | 3 | Pub/Pri | UMediaPlayer/UMediaTexture 등 에셋 레벨 노출. |
| `MediaUtils` | 5 | 1 | Pub/Pri | 미디어 유틸/헬퍼. |
| `MovieScene` | 7 | 1 | Pub/Pri | Sequencer 코어: 트랙/섹션/평가 템플릿. |
| `MovieSceneCapture` | 0 | 13 | Pub/Pri | 시퀀서 영상/이미지 캡처 파이프라인. |
| `MovieSceneTracks` | 10 | 7 | Pub/Pri | 기본 트랙 타입(Transform/Property/Audio 등) 구현. |
| `Overlay` | 3 | 3 | Pub/Pri | 자막/오버레이 트랙. |
| `UEJpegComp` | 0 | 0 | — | JPEG 컴포넌트 유틸. |

## VR/XR

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AugmentedReality` | — | — | 컨테이너 | AR 트래킹/세션 인터페이스(컨테이너). |
| `EyeTracker` | 0 | 10 | Pub/Pri | 시선 추적 추상 인터페이스. |
| `HeadMountedDisplay` | 0 | 8 | Pub/Pri | HMD/스테레오 렌더링 인터페이스. |
| `MRMesh` | — | — | 컨테이너 | 혼합 현실(MR) 메시 캡처 컨테이너. |

## VP

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `NNE` | 0 | 3 | Pub/Pri | Neural Network Engine — 추론 백엔드(ORT/DML/CPU). |
| `VirtualProduction` | — | — | 컨테이너 | 버추얼 프로덕션 컨테이너. |

## Platform

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `Android` | — | — | 컨테이너 | Android 플랫폼 모듈 컨테이너(JNI, Java, Permissions 등). |
| `Apple` | — | — | 컨테이너 | Apple(macOS/iOS 공통) 컨테이너. |
| `IOS` | — | — | 컨테이너 | iOS 컨테이너(AdSupport/StoreKit/AVFoundation 통합 등). |
| `Linux` | — | — | 컨테이너 | Linux 컨테이너. |
| `PlatformThirdPartyHelpers` | — | — | 컨테이너 | 플랫폼별 ThirdParty 정적 라이브러리 헬퍼. |
| `Solaris` | — | — | 컨테이너 | Solaris 컨테이너(거의 사용 안함). |
| `Unix` | — | — | 컨테이너 | Unix 공용 코어. |
| `Windows` | — | — | 컨테이너 | Windows 컨테이너(D3D, XAudio2 등 보조). |

## DevTools

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `AutomationMessages` | 2 | 1 | Pub/Pri | 자동화 메시지(Test Framework). |
| `AutomationTest` | 1 | 2 | Pub/Pri | FAutomationTestBase / SimpleAutomation 매크로 — 단위/기능 테스트 본체. |
| `AutomationWorker` | 1 | 7 | Pub/Pri | 자동화 워커(원격 디바이스에서 테스트 실행). |
| `ClientPilot` | 0 | 2 | Pub/Pri | 데모/QA 자동 플레이 파일럿. |
| `CrashReportCore` | 6 | 0 | Pub/Pri | 크래시 리포터 클라이언트 공용 코어. |
| `HardwareSurvey` | 2 | 0 | Pub/Pri | 하드웨어 서베이 보고. |
| `PerfCounters` | 0 | 3 | Pub/Pri | 퍼포먼스 카운터(서버용 stat 노출). |
| `RewindDebuggerRuntimeInterface` | 0 | 2 | Pub/Pri | Rewind Debugger와 게임의 인터페이스. |
| `StudioTelemetry` | — | — | 컨테이너 | 에픽 내부 텔레메트리(컨테이너). |
| `Toolbox` | — | — | 컨테이너 | 툴박스 컨테이너. |

## Messaging

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `Messaging` | 2 | 0 | Pub/Pri | FMessageBus 메시지 버스 코어(인프로/네트워크 transports). |
| `MessagingCommon` | 2 | 0 | Pub/Pri | 메시지 공통 타입. |
| `MessagingRpc` | 3 | 0 | Pub/Pri | 메시지 버스 위에 RPC 패턴 구현. |
| `SessionMessages` | 1 | 1 | Pub/Pri | 세션 메시지(엔진 인스턴스 검색/제어). |
| `SessionServices` | 1 | 3 | Pub/Pri | 세션 서비스 — Session Frontend가 사용하는 게임 측 서비스. |

## Time

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `TimeManagement` | 5 | 0 | Pub/Pri | FFrameNumber/FFrameRate, 타임코드, 시퀀서·LiveLink 프레임 시스템. |
| `VectorVM` | 2 | 0 | Pub/Pri | Niagara 벡터 VM(스크립트 시뮬레이션 인터프리터). |
| `VerseCompiler` | 2 | 0 | Pub/Pri | Verse 언어 컴파일러 프런트엔드. |

## Misc

| 모듈 | Pub | Pri | 폴더 | 요약 |
|------|-----|-----|------|------|
| `Advertising` | — | — | 컨테이너 | 모바일 광고 SDK 통합 컨테이너. |
| `Analytics` | — | — | 컨테이너 | 분석 프로바이더 컨테이너. |
| `CUDA` | — | — | 컨테이너 | CUDA 런타임 통합(ML/연구). |
| `Datasmith` | — | — | 컨테이너 | Datasmith 임포터 컨테이너. |
| `Experimental` | — | — | 컨테이너 | 실험 모듈 컨테이너. |
| `InstallBundleManager` | 0 | 4 | Pub/Pri | 인스톨 번들/체인 다운로드 관리. |
| `NullInstallBundleManager` | — | — | 컨테이너 | 더미 인스톨 번들 매니저. |
| `Portal` | — | — | 컨테이너 | Epic 런처 포털 통합 컨테이너. |
| `RuntimeAssetCache` | 0 | 3 | Pub/Pri | 런타임 에셋 캐시(레거시). |
| `TextureUtilitiesCommon` | — | — | 컨테이너 | 텍스처 유틸 공용 컨테이너. |
