---
name: ue-wiki-llm-install
description: UE 5.5.4 LLM Wiki Plugin 설치 가이드 — Claude Code 환경에서 다른 UE 프로젝트가 본 위키를 사용하는 4가지 방법 (Skills install / Symlink / Submodule / 진입점 import).
---

# UE Wiki LLM — Install Guide

> 본 가이드는 **다른 UE 5.5.4 프로젝트** 가 LLM_Wiki 를 사용하는 4가지 방법을 안내. Claude Code 환경에서 가장 권장되는 방법은 **방법 1 (Plugin install)** 또는 **방법 4 (진입점 import)**.

---

## 사전 요구사항

- **Claude Code** ≥ 2.0
- **UE 5.5.4** (다른 마이너 버전은 [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) 감사 후 사용)
- 본 위키 절대 경로 (예: `C:\Unreal\UnrealEngine\LLM_Wiki`)

---

## 방법 1: Claude Code Plugin 으로 install ⭐⭐ (가장 권장)

### 1.1 글로벌 install (모든 프로젝트에서 사용)

```bash
# Windows (PowerShell)
$env:USERPROFILE | %{ "$_\.claude\plugins\ue-wiki-llm" } | %{
    New-Item -ItemType SymbolicLink -Path $_ -Target "C:\Unreal\UnrealEngine\LLM_Wiki" -Force
}

# 또는 mklink (cmd)
mklink /J "%USERPROFILE%\.claude\plugins\ue-wiki-llm" "C:\Unreal\UnrealEngine\LLM_Wiki"

# Linux/Mac
ln -s /path/to/LLM_Wiki ~/.claude/plugins/ue-wiki-llm
```

### 1.2 프로젝트별 install

```bash
cd C:\MyGame
mkdir .claude\plugins
mklink /J ".claude\plugins\ue-wiki-llm" "C:\Unreal\UnrealEngine\LLM_Wiki"
```

### 1.3 Claude Code 가 자동 인식

Plugin install 후 Claude Code 가 `.claude-plugin/plugin.json` 자동 감지 → 13개 카테고리 + 108 sub-skill 사용 가능.

```
사용자: [Components] 새 ItemPickup 컴포넌트 작성
Claude: (plugin.json 의 trigger_keywords 매칭)
        → ue-wiki-llm/skills/Components/SKILL.md 자동 routing
        → ActorComponent 베이스 + 6대 정책 + 코드 생성
```

---

## 방법 2: Symlink (간단)

```bash
# 프로젝트 폴더 안에 위키 심볼릭 링크
cd C:\MyGame
mklink /J LLM_Wiki C:\Unreal\UnrealEngine\LLM_Wiki

# 또는 PowerShell
New-Item -ItemType SymbolicLink -Path "LLM_Wiki" -Target "C:\Unreal\UnrealEngine\LLM_Wiki"
```

프로젝트의 `CLAUDE.md` 에 진입점 추가:
```markdown
## UE 위키 (외부 참조)
모든 UE 작업 시 `./LLM_Wiki/CLAUDE.md` 의무 로드.
```

---

## 방법 3: Git Submodule (협업)

```bash
cd C:\MyGame
git submodule add https://github.com/sensr7086/ue-wiki-llm LLM_Wiki
git submodule update --init --recursive

# 위키 갱신 시
cd LLM_Wiki
git pull origin main
cd ..
git add LLM_Wiki
git commit -m "Update UE wiki to vX.Y.Z"
```

**장점**: 버전 관리 / 협업 / 분기별 staleness 감사 자연스러움.
**단점**: git 환경 + submodule 학습 필요.

---

## 방법 4: 진입점 import (가장 간단 — 5분 setup)

각 프로젝트의 `CLAUDE.md` 첫 부분에 추가:

```markdown
# MyGame CLAUDE.md

## UE 5.5.4 작업 시 외부 위키 의무 로드

본 프로젝트는 언리얼 엔진 5.5.4 사용. C++ / Slate / UMG / Components / GameFramework / Editor / Subsystem 작업 시 **반드시 외부 위키 진입점 로드**:

> 📖 위키 진입: `C:\Unreal\UnrealEngine\LLM_Wiki\CLAUDE.md`
> 시나리오 매칭: `C:\Unreal\UnrealEngine\LLM_Wiki\00_Overview\03_WikiHarness.md`
> 위키 작성 메타: `C:\Unreal\UnrealEngine\LLM_Wiki\_meta\CLAUDE-wiki-governance.md` (위키 갱신 시만)

작업 시 카테고리 명시 의무: `[CoreUObject]` / `[SlateCore]` / `[Slate]` / `[UMG]` / `[Components]` / `[GameFramework]` / `[AssetClasses]` / `[Input]` / `[Editor]` / `[Subsystem]` / `[Significance]` / `[GAS]` / `[Niagara]`

---
## (본 프로젝트 고유 룰)
프로젝트명: MyGame
UE 버전: 5.5.4
...
```

**장점**: 5분 작업 / 모든 환경에서 작동.
**단점**: 매 프로젝트마다 진입점 단락 추가 필요.

---

## 사용 확인 (install 후)

새 프로젝트에서 Claude Code 시작 후 테스트:

```
사용자: [Components] 새 RespawnComponent 작성해줘 (캐릭터 5초 후 리스폰)

Claude (위키 자동 로드):
1. CLAUDE.md → 카테고리 [Components] 식별
2. 03_WikiHarness §3.1 시나리오 매칭
3. skills/Components/SKILL.md (메인) + ActorComponent/SKILL.md
4. 10_ComponentPolicies.md (6대 정책)
5. 07_ProfilingScopeRule.md (콜백 스코프)
6. 코드 생성 — 6대 정책 자동 적용
```

기대 코드:
```cpp
UCLASS()
class MYGAME_API URespawnComponent : public UActorComponent
{
    // ⚠️ 6대 정책 자동 적용:
    // 1. PrimaryComponentTick.bCanEverTick = false (정책 5)
    // 2. UPROPERTY() + TWeakObjectPtr (정책 3, 4)
    // 3. CreateDefaultSubobject Constructor 안만 (정책 6)
public:
    URespawnComponent();
    virtual void BeginPlay() override;
    // ...
};
```

---

## 위키 갱신 워크플로우

### 새 패턴 발견 시

```
사용자: [Wiki] [Components] AudioComponent SetSound 매 프레임 호출 함정 추가

Claude (governance.md 자동 로드):
1. meta/CLAUDE-wiki-governance.md (위키 작성 메타 룰 5단)
2. §8.4 5단 의무 검증
3. Components/references/AudioComponent.md §함정 표 갱신
4. 15_EvaluatorRecipe 평가 의무 (다음 세션)
```

### Plugin 버전 업그레이드

```bash
cd C:\Unreal\UnrealEngine\LLM_Wiki

# Plugin.json version 변경
# Marketplace 의 plugins[].version 도 변경

# Submodule 사용 시
git tag v1.1.0
git push --tags
```

각 프로젝트는 다음 sync 시 새 버전 자동 적용.

---

## 분기별 staleness 감사 (필수)

본 위키는 [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) 의무 — 분기마다 감사.

### 트리거
- **분기별 (3개월)** 정기 감사
- **UE 마이너 버전 업그레이드** (5.7 → 5.8 등)
- **Anthropic Claude 모델 메이저 변경**

### 감사 8단계
1. Inventory — 모든 sub-skill 인벤토리
2. Source Validation — 라인 번호 grep 재검증
3. Load-Bearing Test — 사용 시나리오 검증
4. Cross-Reference — cross-link 무결성
5. Real-World — 실제 사용 빈도
6. Decision — 6종 (Continue / Update / Simplify / Merge / Deprecate / Remove)
7. Implementation — 변경 적용
8. Communication — 사용자 안내

자세한 감사 프로세스 = [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md).

---

## 문제 해결

### Q: Claude 가 위키를 인식 못함
- Plugin install (`.claude/plugins/ue-wiki-llm` 존재 확인)
- 프로젝트 CLAUDE.md 안 진입점 단락 (방법 4)
- Claude Code 재시작

### Q: 토큰 사용량이 너무 많음
- 카테고리 명시 의무 (`[Components] ...` 등)
- 한 세션에 한 카테고리만
- references/ 깊이 자료는 lazy load

### Q: UE 5.8 으로 업그레이드 시
- [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) 8단계 감사
- 변경된 API 표시 (deprecated)
- 새 API 추가 (Subsystem 종 추가 시 등)

### Q: 다른 회사 / 팀과 공유
- 방법 3 (Git Submodule) 권장
- 또는 marketplace 표준 따라 공식 plugin 마켓플레이스 등록

---

## 라이선스

MIT — 자유롭게 사용 / 수정 / 배포.

---

## 변경 이력

| 날짜 | 버전 | 변경 |
|------|------|------|
| 2026-05-06 | 1.0.0 | 초기 Plugin 패키징 — `.claude-plugin/plugin.json` + `marketplace.json` + INSTALL.md. 13 카테고리 + 108 sub-skill + 14 횡단 인덱스 + Editor 모듈 통합 + Subsystem 통합 가이드 + 4개 Level 3 references. |
