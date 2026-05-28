> ⚠ **DEPRECATED 2026-05-15** — 본 v1.7.0 은 SpatialPartition (Cycle #11) 만 다룸. **`docs/g3-handoff-ue-wiki-llm-v1.8.0.md` 가 대체** — LevelSequence (Cycle #12) 도 통합. 외부 에이전트는 v1.8.0 문서 우선 참조.

---

# G3 게이트 작업 인계 — ue-wiki-llm plugin v1.6.0 → v1.7.0 (DEPRECATED)

> **인계 대상**: ue-wiki-llm plugin 담당 다른 에이전트 (mcwiki main session 영역 X)
> **작성**: 2026-05-13 · mcwiki vault v0.2.0 release 후
> **목적**: Phase II G3 게이트 통과 — `ue-spatial-partition-specialist` plugin 활성화 + orchestrator §5.4 명문화

---

## 0. 현 상태 (2026-05-13)

### Plugin 권한 매트릭스

| 항목 | raw (E:\MCWiki\raw\ue-wiki-llm\) | plugin (Cowork install) |
|------|----------------------------------|------------------------|
| **agent** `ue-spatial-partition-specialist.md` | ✅ 존재 (189L) | ❌ 누락 |
| **skills/SpatialPartition/** | ✅ 5 파일 (SKILL + 4 ref) | ❌ 없음 |
| **agents/ue-orchestrator.md** §5.4 | ⚠ `[SpatialPartition]` 라우팅만 (line 3, 34, 129) | ⚠ §5.4 boundary protocol 섹션 없음 |
| **plugin.json** | — | v1.6.0 |

→ 모든 항목 plugin 측 갱신 필요.

### Plugin 위치

- **Windows 원본 (사용자 빌드 source 추정)**: `C:\Unreal\UnrealEngine\LLM_Wiki\` 또는 별도 dir
- **Mount path (read-only Cowork mount)**: `/sessions/pensive-gracious-franklin/mnt/.remote-plugins/plugin_019SPM4GSPfAfagqWFsrexY4/`
- **Cowork install path (Windows)**: `C:\Users\김민철\AppData\Roaming\Claude\local-agent-mode-sessions\11afa6ca-099c-461d-91ad-c4ce8c45ecff\3e9ec507-52ef-4d6f-92ee-3b9186b79803\rpm\plugin_019SPM4GSPfAfagqWFsrexY4\`

---

## 1. 필요 변경 5건

| # | 작업 | 출발지 → 도착지 |
|---|------|----------------|
| 1 | `plugin.json` version + description + keywords | v1.6.0 → **v1.7.0** |
| 2 | agent 신규 | `raw/agents/ue-spatial-partition-specialist.md` → `plugin/agents/` |
| 3 | skills 신규 | `raw/skills/SpatialPartition/*` → `plugin/skills/SpatialPartition/*` (5 파일) |
| 4 | orchestrator §5.4 섹션 삽입 | `plugin/agents/ue-orchestrator.md` 의 `## 출력 형식` 앞에 §5.4 boundary protocol 본문 추가 |
| 5 | `.mcpb` 재빌드 | `mcpb pack .` → `dist/ue-wiki-llm-1.7.0.mcpb` |

### orchestrator §5.4 본문 (수동 삽입 시 — Self-check 6단 v0.4 기준)

```markdown
## §5.4 Agent Boundary Protocol (vault 와의 인터페이스 의무)

> Vault 와 통신하는 도구 (`mcwiki` MCP) 는 main Cowork 만 보유. specialist 는 raw/wiki 파일 시스템만 접근 → §5.2 QUERY workflow 가 specialist 안에서 시행 불가 → **main 이 boundary 마다 §5.2 를 wrap**.

### 5단계 boundary

```
[A] PRE-DELEGATE  vault 정찰 (read_index + search + read_page)
        ↓
[B] DELEGATE      Task(specialist, prompt) — vault 컨텍스트 + §13 의무 명시
        ↓
[C] POST-RECEIVE  (1) §13 tier 분해 (🟢/🟡/🔴) + 보너스 발견
                  (2) 5-tier 카운트 정합 검사 (자산 추가/제거 cycle)
        ↓
[D] FILE-BACK     사용자 OK 게이트 → write_page / synthesis_finalize
        ↓
[E] LOG           append_log (op=query|synthesis|...) 의무
```

### POST-RECEIVE 검증 의무 (2026-05-13 보강)

- ❌ bash `wc -c` / `ls -la` 단독 의존 금지 — mount stale false negative 위험
- ✅ file `Read` tool 또는 mcwiki `read_page` — vault 의 진짜 view
- ⭐ 두 방법 cross-check 권장

### Specialist 권한 매트릭스

| 작업 | Specialist | main (orchestrator) |
|------|-----------|---------------------|
| raw/wiki 파일 Read/Write | ✅ | ✅ |
| mcwiki MCP (read_index / search / read_page) | ❌ | ✅ |
| mcwiki MCP (write_page / append_log / synthesis_*) | ❌ | ✅ |
| log.md 직접 edit (Bash) | ❌ 금지 (mcwiki append_log 의무) | — |

### Self-check 6단 (2026-05-13 v0.4 확장)

| 단계 | self-check |
|------|-----------|
| §A | read_index + search + read_page 호출 했나? |
| §B | prompt 안 vault 컨텍스트 + §13 의무 명시? |
| §C-1 | specialist 반환을 §13 tier 분류 표 작성? |
| §C-2 | 자산 추가/제거 시 5-tier 카운트 정합 검사? (자산 변경 없는 cycle 은 N/A) |
| §D | 사용자 OK 게이트 거쳤나? |
| §E | append_log 호출? cycle 측정 데이터 포함? |

6/6 ✅ = cycle 인정.

### Cycle 등재 표준

매 specialist 호출 후 main 이:

1. `read_page kind=synthesis slug=agent-boundary-cycles-2026-q2` — cycle 로그 읽음
2. `write_page` — §4 cycle 로그에 새 entry append
3. 집계 메트릭 갱신 + G2 진행률 갱신
4. cycle #10 도달 시 Phase II 결정 트리 적용

> 정밀판: `00_meta/07_AgentBoundaryProtocol.md` · 마스터: `CLAUDE.md §5.4`
```

---

## 2. 자동화 도구 — `tools/pack-plugin.ps1`

**경로**: `E:\MCWiki\tools\pack-plugin.ps1` (이번 세션 작성, 7 단계 자동)

### DryRun 사전 검증

```powershell
E:\MCWiki\tools\pack-plugin.ps1 -DryRun
```

출력: 변경 예상 항목 표시 (실제 수정 X).

### 본 빌드

```powershell
E:\MCWiki\tools\pack-plugin.ps1 `
    -PluginSource "C:\Unreal\UnrealEngine\LLM_Wiki" `
    -RawVault "E:\MCWiki\raw\ue-wiki-llm" `
    -NewVersion "1.7.0"
```

스크립트가 자동:
1. 환경 검증 (Plugin/Raw 경로 + mcpb CLI)
2. Backup zip (`backup-pre-v1.7.0-{timestamp}.zip`)
3. 6 파일 복사 (raw → plugin)
4. plugin.json v1.6.0 → v1.7.0 + description + keywords 갱신
5. ue-orchestrator.md §5.4 섹션 idempotent 삽입 (이미 있으면 skip)
6. `mcpb pack` 실행 → `dist/ue-wiki-llm-1.7.0.mcpb`
7. 사후 Cowork install 가이드 표시

### 파라미터

- `-PluginSource` (디폴트: `C:\Unreal\UnrealEngine\LLM_Wiki`)
- `-RawVault` (디폴트: `E:\MCWiki\raw\ue-wiki-llm`)
- `-NewVersion` (디폴트: `1.7.0`)
- `-OutDir` (디폴트: `$PluginSource\dist`)
- `-SkipBackup` (위험)
- `-DryRun` (변경 X)

### Idempotent §5.4 삽입

스크립트의 §5 단계가 `ue-orchestrator.md` 검사 — `## §5.4 Agent Boundary Protocol` 이미 있으면 skip. 재실행 안전.

⚠ **본 문서의 §1 본문은 6단 self-check 보강 후 버전**. 스크립트 안 §5.4 본문 (5단 self-check) 과 *살짝 다름*. 다음 둘 중 결정:

- **옵션 A**: 스크립트 그대로 실행 — 5단 self-check 로 plugin 빌드 후 *추후* 6단 보강 (별도 cycle)
- **옵션 B**: 스크립트 안 §5.4 본문 블록을 본 문서의 6단 버전으로 수동 교체 후 실행

권장: **옵션 A** (단순 + 점진 — 6단 확장은 향후 보강 cycle).

---

## 3. 수동 단계 (자동화 스크립트 미사용 시)

```powershell
# 0. 작업 디렉토리 이동
cd C:\Unreal\UnrealEngine\LLM_Wiki

# 1. Backup
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
Compress-Archive -Path .claude-plugin -DestinationPath "backup-pre-v1.7.0-$ts.zip" -Force

# 2. SpatialPartition 5 + agent 1 = 6 파일 복사
robocopy E:\MCWiki\raw\ue-wiki-llm\skills\SpatialPartition .claude-plugin\skills\SpatialPartition /E
copy E:\MCWiki\raw\ue-wiki-llm\agents\ue-spatial-partition-specialist.md .claude-plugin\agents\

# 3. plugin.json 갱신 (notepad 또는 IDE)
notepad .claude-plugin\plugin.json
#   "version": "1.6.0"  →  "1.7.0"
#   description / keywords 갱신 (§4 본문 참조)

# 4. ue-orchestrator.md §5.4 섹션 삽입 (## 출력 형식 앞에)
notepad .claude-plugin\agents\ue-orchestrator.md

# 5. mcpb 재빌드
mcpb pack . dist\ue-wiki-llm-1.7.0.mcpb

# 6. Cowork uninstall (v1.6.0) → install (v1.7.0) → 재시작
```

---

## 4. plugin.json 새 본문 (수동 적용 시)

```json
{
  "name": "ue-wiki-llm",
  "version": "1.7.0",
  "description": "Unreal Engine 5.7.4 LLM Wiki — 20 카테고리 + 130+ sub-skill (Render 12 — RDG/Shader/Material/MaterialExpression/SceneViewExtension/MeshDrawing/PostProcess/Lumen+Nanite/RHI/Vulkan/Mobile/VR + SpatialPartition 4 — TOctree2/TQuadTree/StaticSpatialIndex/WorldPartitionRuntime + Subsystem 2 — 5종+Online) + 15 횡단 인덱스 + Evaluator Workflow + §5.4 Agent Boundary Protocol + 14 specialist (spatial-partition 신규). Cross-Platform 게임 (DX12/Vulkan/Metal) + Mobile 60fps + VR 90fps + Online + 대규모 월드 (1km+) AActor 공간 인덱싱 표준 통합. Generator/Evaluator 분리.",
  "author": {"name": "민철", "email": "sensr7086@naver.com"},
  "homepage": "https://github.com/sensr7086/ue-wiki-llm",
  "license": "MIT",
  "keywords": ["unreal-engine", "ue5", "ue-5.7", "cpp", "gamedev", "slate", "umg", "components", "gameframework", "subsystem", "editor", "animation", "blueprint", "networking", "ai", "build", "metasound", "render", "rdg", "shader", "lumen", "nanite", "rhi", "vulkan", "mobile", "vr", "online", "spatial-partition", "octree", "worldpartition", "wiki", "evaluator", "boundary-protocol", "korean"]
}
```

---

## 5. 검증 (install 후)

### Cowork UI 안

```
1. Plugin 관리 → ue-wiki-llm v1.7.0 확인
2. Task tool spawn → "ue-wiki-llm:ue-spatial-partition-specialist" 활성 확인
3. [SpatialPartition] prefix 명령 라우팅 동작
4. orchestrator system_prompt 안 §5.4 5단계 노출 확인
```

### .mcpb 사전 검증 (zip 내용)

```powershell
python -c "import zipfile, json; z=zipfile.ZipFile('dist/ue-wiki-llm-1.7.0.mcpb'); m=json.loads(z.read('.claude-plugin/plugin.json').decode()); print('version:', m['version']); print('keywords:', len(m['keywords']))"
```

---

## 6. G3 통과 후 Phase II 게이트 진행

| 게이트 | 통과 후 상태 |
|--------|-------------|
| G1 (1개월 MCP 안정) | 🟡 진행 — mcwiki v0.2.0 install 시점 (2026-05-13) → **2026-06-13 자동 PASS** (변경 없으면) |
| ✅ G2 (10 cycle 검증) | PASS (10/10 + 보너스 37건) |
| ⏳ G3 (orchestrator §5.4) | **본 작업 통과 시 PASS** |

→ 3 게이트 모두 통과 시 **Phase II C 적용 검토 시작** = orchestrator agent 에 mcwiki MCP 권한 추가 (별도 plugin upgrade — v1.8.0 후보).

---

## 7. Cross-link

- [[CLAUDE.md#§5.4]] — 마스터 schema §5.4 boundary protocol
- [[00_meta/07_AgentBoundaryProtocol]] — 정밀판 (§2.4 5-tier + §5.1 POST-RECEIVE 검증)
- [[synthesis/agent-boundary-cycles-2026-q2]] — G2 게이트 cycle 로그
- [[sources/ue-agent-spatial-partition]] — 신규 agent 정의
- [[sources/ue-spatialpartition-skill]] — 20번째 카테고리 main hub

---

## 8. 작업 완료 보고

작업 완료 시 vault 측에 통보 (수동):

```text
mcwiki:append_log
  op=feature
  title="G3 게이트 PASS — ue-wiki-llm v1.7.0 release"
  body="plugin 14 agents 활성 (spatial-partition 추가) + orchestrator §5.4 명문화 + Phase II G3 통과 ..."
```

또는 main session 에 단순 보고. main 이 vault entry append.

다음 cycle 부터 orchestrator 가 §5.4 boundary protocol 자동 적용 → main wrap 부담 ↓.
