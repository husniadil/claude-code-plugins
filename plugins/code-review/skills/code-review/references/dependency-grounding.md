# Dependency & Compatibility Grounding Reference

Grounding workflow for Step 2e of `code-review`. Verifies usage of third-party libraries against the **exact versions** pinned in the project's manifests/lockfiles — not against the latest release or general knowledge.

## Contents

- [When to trigger](#when-to-trigger)
- [Stack → dependency file lookup](#stack--dependency-file-lookup)
- [Grounding workflow](#grounding-workflow)
- [What to flag](#what-to-flag)
- [Example](#example)

## When to Trigger

- Diff modifies a dependency manifest (see table below)
- New import is introduced from a third-party library
- API usage pattern looks version-sensitive (deprecated methods, renamed exports, signature changes)

## Stack → dependency file lookup

| Stack                       | Manifest / lockfile                                                             | Key versions to extract                                               |
| --------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Node / TypeScript           | `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`              | Direct dep versions, `engines.node`                                   |
| Python                      | `pyproject.toml`, `uv.lock`, `requirements*.txt`, `Pipfile.lock`, `poetry.lock` | Package versions, `requires-python`                                   |
| Go                          | `go.mod`, `go.sum`                                                              | Module versions, `go` directive                                       |
| Java                        | `build.gradle(.kts)`, `pom.xml`                                                 | Framework version (Spring/Quarkus/etc.) → managed transitive versions |
| Kotlin                      | `build.gradle.kts`, `pom.xml`                                                   | Kotlin version, framework version                                     |
| Rust                        | `Cargo.toml`, `Cargo.lock`                                                      | Crate versions, edition                                               |
| Ruby                        | `Gemfile`, `Gemfile.lock`                                                       | Gem versions, Ruby version                                            |
| PHP                         | `composer.json`, `composer.lock`                                                | Package versions, PHP version                                         |
| Elixir                      | `mix.exs`, `mix.lock`                                                           | Dep versions, Elixir/OTP version                                      |
| Runtime pinning (any stack) | `.tool-versions`, `.nvmrc`, `.python-version`, `.ruby-version`                  | Runtime version the project expects                                   |

## Grounding Workflow

1. **Read the manifest** to get the exact pinned versions — do not assume latest. In monorepos, read the manifest of the specific package being modified.
2. **WebSearch** the library + version for:
   - Breaking changes between the previous and new version (if bumped)
   - Deprecated APIs used in the diff
   - Known CVEs / security advisories for the pinned version
   - Compatibility with other pinned deps (e.g., peer deps, Node/Python/JVM version)
3. **WebFetch** official changelog, release notes, or migration guide when WebSearch surfaces relevant URLs. Prefer: npm / PyPI / crates.io pages, GitHub releases, official docs.
4. **Cross-check the usage** in the diff against the version's actual API surface — imports, method names, argument shapes.

## What to Flag

- Usage of APIs deprecated or removed in the pinned version
- Version bump without addressing documented breaking changes
- Pinned version with known CVE (flag as Security gap too)
- Peer-dependency mismatch (e.g., `react` and `react-dom` out of sync)
- Runtime incompatibility (e.g., library needs Node 20 but `.nvmrc` says 18)
- Using an API documented for `vX` while manifest pins `vY` where `Y ≠ X`

## Example

```
Diff adds: import { cache } from 'react'
Manifest shows: "react": "^17.0.2"

Grounding: WebSearch "react cache import version"
Result: `cache()` was introduced in React 18.2
Gap: [HIGH] Uses React 18+ API but project pins React 17.0.2 — will fail at runtime
```

Label such gaps under the **Dependency Compatibility** category (see Step 2f in SKILL.md, and [gap-categories.md §3](gap-categories.md)).
