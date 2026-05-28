---
title: "UE Slate 클립보드 이미지 paste — CF_HDROP + CF_DIB → PNG (Windows-only)"
kind: concept
status: stable
severity: "★★"
tags: [editor, slate, clipboard, image, win32, imagewrapper, MMA-52, ue-574]
created: 2026-05-22
last_updated: 2026-05-22
---

# UE Slate 클립보드 이미지 paste — CF_HDROP + CF_DIB → PNG (Windows-only)

## 정의

UE Slate widget 의 `SMultiLineEditableTextBox` 또는 유사 입력 위젯에 *클립보드 이미지* (스크린샷 / Explorer 파일) 를 paste 하려면 — UE 표준 API 에 *이미지 클립보드 지원 없음* → **Windows native Win32 API** 직접 호출 + **ImageWrapper** 모듈로 PNG 인코딩 후 임시 파일 저장 패턴.

`OnKeyDownHandler` 에 Ctrl+V 감지 → `OpenClipboard` + `GetClipboardData(CF_HDROP / CF_DIBV5 / CF_DIB)` → 두 형태 분기 처리 → `Saved/<plugin>/clipboard-<ts>.png` 저장 → 입력창에 path 삽입.

## 자세히

### 사례: MCMaterialAuto v0.30 (MMA-52)

🟢 **VAULT** — MCMaterialAuto v0.30 채택본.

### 두 형태의 클립보드 데이터

| 형식 | 출처 | 처리 |
|---|---|---|
| **CF_HDROP** | Explorer 에서 *파일* 복사 (Ctrl+C on file) | `DragQueryFile` 로 경로 추출 → 확장자 검사 (.png/.jpg/.bmp/.gif/.tga/.webp) |
| **CF_DIBV5** / **CF_DIB** | 스크린샷 (Win+Shift+S / PrintScreen) / Photoshop / GIMP 복사 | raw bitmap data → BGRA 변환 → PNG 인코딩 → 임시 파일 |

### 구현 5-Layer

```cpp
// Layer 1 — OnKeyDownHandler 의 Ctrl+V 감지
FReply Widget::OnPromptKeyDown(const FGeometry&, const FKeyEvent& Ev) {
    if (Ev.GetKey() == EKeys::V && Ev.IsControlDown() && !Ev.IsShiftDown()) {
        if (TryPasteImageFromClipboard()) return FReply::Handled();
    }
    return FReply::Unhandled();   // fallthrough → default text paste
}

// Layer 2 — OpenClipboard + 두 형식 분기
bool TryPasteImageFromClipboard() {
#if PLATFORM_WINDOWS
    if (!::OpenClipboard(nullptr)) return false;
    FString InsertedPath;

    // 2a — CF_HDROP (파일 경로)
    if (HANDLE Drop = ::GetClipboardData(CF_HDROP)) {
        HDROP HD = (HDROP)Drop;
        TCHAR Buf[MAX_PATH] = {};
        if (::DragQueryFile(HD, 0, Buf, MAX_PATH) > 0) {
            if (IsImageExtension(Buf) && FPaths::FileExists(Buf))
                InsertedPath = Buf;
        }
    }

    // 2b — CF_DIBV5 → CF_DIB (raw bitmap)
    if (InsertedPath.IsEmpty()) {
        HANDLE H = ::GetClipboardData(CF_DIBV5);
        if (!H) H = ::GetClipboardData(CF_DIB);
        if (H) InsertedPath = TrySaveDibAsPng(H);
    }
    ::CloseClipboard();
    return !InsertedPath.IsEmpty();
#else
    return false;   // Mac/Linux 미지원
#endif
}

// Layer 3 — DIB → BGRA 변환
LPVOID Bits = ::GlobalLock(DibHandle);
BITMAPINFOHEADER* BIH = (BITMAPINFOHEADER*)Bits;
const int32 Width = BIH->biWidth;
const int32 Height = abs(BIH->biHeight);
const bool bTopDown = (BIH->biHeight < 0);
const int32 BitCount = BIH->biBitCount;   // 24 or 32 only

const int32 HeaderSize = BIH->biSize;     // BITMAPINFOHEADER (40) or BITMAPV5HEADER (124)
const int32 MaskSize = (BIH->biCompression == BI_BITFIELDS) ? 12 : 0;
const uint8* SrcBase = (uint8*)Bits + HeaderSize + MaskSize;
const int32 SrcStride = ((Width * BitCount + 31) / 32) * 4;   // DWORD align

// BGRA 픽셀 buffer (top-down 보정)
TArray<uint8> Bgra; Bgra.SetNumUninitialized(Width * Height * 4);
for (int32 Y = 0; Y < Height; ++Y) {
    const int32 SrcRow = bTopDown ? Y : (Height - 1 - Y);
    const uint8* S = SrcBase + SrcRow * SrcStride;
    uint8* D = Bgra.GetData() + Y * Width * 4;
    for (int32 X = 0; X < Width; ++X) {
        D[0] = S[0]; D[1] = S[1]; D[2] = S[2];
        D[3] = (BitCount == 32) ? S[3] : 0xFF;
        S += BitCount / 8;
        D += 4;
    }
}
::GlobalUnlock(DibHandle);

// Layer 4 — ImageWrapper PNG 인코딩
IImageWrapperModule& Module = FModuleManager::LoadModuleChecked<IImageWrapperModule>("ImageWrapper");
TSharedPtr<IImageWrapper> PNG = Module.CreateImageWrapper(EImageFormat::PNG);
PNG->SetRaw(Bgra.GetData(), Bgra.Num(), Width, Height, ERGBFormat::BGRA, 8);
const TArray64<uint8>& Compressed = PNG->GetCompressed();

// Layer 5 — 파일 저장 + path 삽입
const FString Path = MakeClipboardImagePath();   // Saved/<plugin>/clipboard-<ts>.png
TArray<uint8> Buf; Buf.Append(Compressed.GetData(), Compressed.Num());
FFileHelper::SaveArrayToFile(Buf, *Path);
PromptBox->InsertTextAtCursor(FString::Printf(TEXT(" %s "), *Path));
```

### Build.cs 의존

```cs
"ImageWrapper",      // PNG 인코딩
"ApplicationCore",   // 이미 다른 곳 의존 (Win32 wrapper)
```

Win32 헤더 include:
```cpp
#if PLATFORM_WINDOWS
  #include "Windows/AllowWindowsPlatformTypes.h"
  #include <Windows.h>
  #include <shellapi.h>   // DragQueryFile
  #include "Windows/HideWindowsPlatformTypes.h"
#endif
```

## 회피 패턴 (Production)

### Anti-pattern

| ❌ Anti | ✅ 패턴 |
|---|---|
| CF_BITMAP (HBITMAP) 만 시도 | CF_DIB / CF_DIBV5 가 더 호환 (Win10/11) |
| OpenClipboard 후 CloseClipboard 누락 | 다른 앱이 clipboard 사용 불가 — 의무 |
| bottom-up DIB 인식 안 함 | `biHeight` 부호 검사 → row 순서 반대 복사 |
| BI_BITFIELDS 무시 | header 뒤 3 DWORD 마스크 — pixel data 시작 위치 보정 |
| 1/4/8/16-bit (팔레트) DIB 처리 | 24/32-bit 만 — 팔레트 cases skip |

### Mac/Linux fallback

`PLATFORM_MAC` / `PLATFORM_LINUX` 가드 — 본 패턴은 *default text paste* 만 진행 (fall-through). Cross-platform 지원은 별도 native API (NSPasteboard / X11 / Wayland) 필요.

## 변형 사례

1. **TGA / EXR paste**: ImageWrapper 가 PNG 외 포맷 지원 — `EImageFormat::TGA` 등 변경 시 동일 패턴
2. **drag-drop**: Slate 의 `OnDragOver` / `OnDrop` — 파일 drop 지원 (이미지 외 다양한 타입)
3. **여러 파일 paste**: `DragQueryFile(HD, 0...)` 의 0 인덱스만 시도 — 다중 파일 시 loop 필요

## 관련 함정

- `GlobalLock/GlobalUnlock` 의 짝 — 잊으면 메모리 누수
- `OpenClipboard(nullptr)` — `HWND` 전달 시 충돌 위험 — nullptr 안전
- DIB header 가 *BITMAPV5HEADER* (124 byte) 이면 BITMAPINFOHEADER (40) 보다 큼 — `biSize` 로 검사 의무
- `FFileHelper::SaveArrayToFile` 는 `TArray<uint8>` 만 — `TArray64<uint8>` 변환 의무 (PNG 가 2GB 미만 보장)

## 관련 entity

- [[SWidget]] (Slate widget base)
- [[FSlateApplication]] (input handling)

## 열린 질문

1. ❓ Mac / Linux clipboard image API 통합 — UE 의 `FPlatformApplicationMisc` 확장 가능성.
2. ❓ Office (Word/Excel) 의 *embedded image* paste 지원 — OLE / CF_ENHMETAFILE 별도 처리 필요.
3. ❓ Animated GIF clipboard — 첫 frame 만 추출 또는 별도 처리.

## Cross-link

- `concepts/LLM-Visual-Reference-Hallucination` (paste 한 이미지가 vision 으로 변환되어야 효과 최대)
- `concepts/MCP-Async-UI-Bridge-Pattern` (paste 결과를 promise bridge 로 LLM 에 전달 가능)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` § Tier 2 Widget

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| CF_HDROP / CF_DIBV5 / CF_DIB 분기 | 🟢 VAULT | Win32 표준 (Windows SDK 공식) |
| BITMAPV5HEADER 호환성 | 🟢 VAULT | Windows SDK 문서 |
| ImageWrapper PNG 인코딩 | 🟢 VAULT | UE 5.7 `IImageWrapperModule` |
| top-down DIB 인식 | 🟢 VAULT | `biHeight` 부호 표준 |
| 1/4/8/16-bit 팔레트 미지원 | 🟡 PARTIAL | 실측 — 가장 흔한 24/32-bit 만 검증 |
| Office embedded image | 🔴 INFERRED | OLE 처리 별도 — 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-52 / MCMaterialAuto v0.30 채택본 기반)
