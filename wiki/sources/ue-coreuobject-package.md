---
type: source
title: "UE CoreUObject — Package sub-skill"
slug: ue-coreuobject-package
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Package.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPackage]]"
related_concepts:
  - "[[concepts/Asset-Lifecycle]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, runtime, foundation, coreuobject, asset]
---

# UE CoreUObject — Package sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Package.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

[[entities/UPackage]] / FPackagePath. LoadPackage / SavePackage / LoadPackageAsync / StaticLoadObject 진입점 + Mount Point + GetTransientPackage (UPackage 의 transient — 메모리 전용 임시).

## 2. Key claims

- UPackage = `.uasset` / `.umap` 1 개에 대응. Outer chain 의 최상위.
- LoadPackage(Outer, Filename, Flags) — 동기 로드. Cooked 빌드에서는 큰 hitch.
- LoadPackageAsync — 비동기 로드. FStreamableManager 의 lower-level 대안.
- SavePackage — Editor 만. 런타임에서 호출 금지.
- StaticLoadObject(Class, Outer, Path) — `LoadObject<T>(...)` 의 underlying.
- Mount Point: 가상 디렉토리 매핑 — `/Game/`, `/Engine/`, `/Plugin/MyPlugin/` 등. Plugin 자산 = `/MyPlugin/...` 경로.
- GetTransientPackage(): 메모리 전용 임시 패키지 — 디스크에 저장 안 됨.

## 3. Quotations

> "동기 LoadPackage 는 Cooked 빌드 hitch 의 주범 — FStreamableManager 비동기 권장."

## 4. Open questions

- [ ] 5.x I/O Store (.utoc/.ucas) 의 UPackage 영향
- [ ] WorldPartition 의 cell streaming 과 UPackage
