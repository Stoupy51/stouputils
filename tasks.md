# stouputils cleanup plan

Audit of `stouputils/` at `1f27a2a2` (v26.3.1). Nothing has been modified yet.

## Baseline

| Metric | Value |
|---|---|
| Source | 114 modules, 17 048 lines, 14 285 non-blank |
| Docstrings | 5 220 lines, **37 % of all non-blank lines** |
| Sections | 226 `Args:`, 158 `Returns:` (131 under 70 chars), 94 `Examples:` (37 contain only doctests) |
| Tests | 467 doctests over 103 modules, all passing. No pytest, no `tests/` |
| Untested | 64 of 114 modules have zero effective doctests |
| Public API | 264 names in the flat `stouputils.*` namespace |
| Lint | `ruff check ./stouputils` clean, `sync_api.py --check` clean |

Regression command used throughout:

```bash
uv run --no-sync python -c "import stouputils as stp; raise SystemExit(stp.launch_tests('stouputils'))" \
  && uv run --no-sync ruff check ./stouputils --config ./pyproject.toml \
  && uv run --no-project python scripts/sync_api.py --check
```

## Constraints found during the audit

1. **`scripts/sync_api.py` owns every re-export block.** It regenerates the `from .x import (name as name, ...)` lists from the public top-level names of each module. A name leaves the flat namespace only by gaining a `_` prefix, by its module joining `INTERNAL` (scripts/sync_api.py:29), or by an explicit `__all__`. Every task that renames or deletes a public name ends with `python scripts/sync_api.py`, or CI's `--check` job fails.
2. **Doctests are the only test harness.** Any behaviour with no `>>>` today has no safety net, which is why Phase 1 exists.
3. **This is a published library.** Phase 4 is separated because it breaks importers. It needs an explicit go/no-go and a major version bump.
4. `# Lazy imports (PEP 810)` headers, the `ALWAYS_LAZY` marker and the `as name` re-export form are generated, not hand-written. Do not "simplify" them.

---

## Phase 1: Setup & Regression Testing

Only covers code that Phase 2 and Phase 3 actually touch. Independent of each other, all blocking on the phases below.

- [ ] **T001**: [Setup] Record the baseline above in a scratch file and confirm the regression command passes on a clean tree. (Justification: every later task is judged against 467/467 and three clean lint jobs.) *Tests: N/A. Blocks: everything.*

- [ ] **T002**: [Setup] Add doctests to `stouputils/continuous_delivery/release_common.py` for `validate_required_keys` (raising and non-raising) and for the two URL builders nested in `generate_changelog`. (Justification: 318 lines, **zero** doctests, and T019 plus T027-T030 rewrite its signatures.) *Tests: No. Blocks: T019, T027, T028, T029, T030.*

- [ ] **T003**: [Setup] Add doctests to `stouputils/parallel/common.py::normalize_parallel_params` covering `max_workers` as `-1`, as a float in `]0, 1]`, and as a float in `[-1, 0[`. (Justification: pure arithmetic with three branches, zero coverage, and T042 renames it.) *Tests: No. Blocks: T012, T031, T032, T042.*

- [ ] **T004**: [Setup] Add doctests to `stouputils/print/message.py` for `info` and `error`, writing into an `io.StringIO` passed as `file=` and asserting the rendered prefix. (Justification: 107 lines, zero coverage, and T013, T024 and T043 all change code that funnels through `info`.) *Tests: No. Blocks: T013, T024, T043.*

- [ ] **T005**: [Setup] Add doctests to `stouputils/version_pkg.py::VersionPrinter.render_tree` and `separators` using a stub `version_of`. (Justification: `indent_block` is the only tested method today, and T018 inlines `print_tree`.) *Tests: Partial. Blocks: T018.*

- [ ] **T006**: [Setup] Add a doctest to `stouputils/applications/automatic_docs/common.py::generate_version_selector` passing a fake `get_versions_function`. (Justification: the injection point exists precisely to make it testable and is unused; 135 lines with zero coverage, trimmed by T013.) *Tests: No. Blocks: T013.*

---

## Phase 2: Dead Code Cleanup & Docstrings (Low Risk)

### Dead code

- [ ] **T007**: [Dead Code] Remove the `if __name__ == "__main__":` blocks from `stouputils/print/__init__.py:78-121`, `stouputils/archive/__init__.py:32-33` and `stouputils/backup/__init__.py:46-47`. (Justification: `python -m stouputils.archive` executes a package's `__main__.py`, which none of these packages has, so the blocks are unreachable. The `print` one is a 44-line manual demo that also drags a `numpy` import into the package.) *Tests: No (unreachable). Independent.*

- [ ] **T008**: [Dead Code] Delete the tracked-adjacent artifacts `some_directory/` and `logfile.txt` from the repo root, and rewrite the doctests that create them (`stouputils/print/output_stream.py:29`, `stouputils/lock/__init__.py:18-21`) to write under `tempfile.mkdtemp()`. (Justification: `logfile.txt` is gitignored but `some_directory/` is not, so a doctest run leaves a directory ready to be committed by accident.) *Tests: Yes (both are doctest bodies). Independent.*

- [ ] **T009**: [Dead Code] Move the deprecated `update_documentation` shim out of `stouputils/applications/automatic_docs/__init__.py:118-122` into `stouputils/_deprecated.py`. (Justification: it forces a `# ruff: noqa: I001`, two imports below the generated re-export block, and the only 4-space-indented lines in that file. `_deprecated.py` already holds five shims of exactly this shape.) *Tests: No. Note: drops `automatic_docs.update_documentation`, keeps `stouputils.update_documentation`. Independent.*

- [ ] **T010**: [Dead Code] Delete the duplicated module docstring at the top of `stouputils/all_doctests/utils.py`. (Justification: byte-for-byte the docstring of `all_doctests/__init__.py`, image directive included, so Sphinx documents the same paragraph twice.) *Tests: No. Superseded by T023 if that runs first.*

### Docstrings

Rule applied in T011-T015: drop an `Args:` entry when the description restates the parameter name, drop a `Returns:` when it restates the annotation, drop the `Examples:` header when the body is nothing but `>>>` lines. Keep `Raises:` (the exception name appears nowhere else), keep `Source:`, keep every doctest.

- [ ] **T011**: [Docstrings] Trim `stouputils/continuous_delivery/` (`git.py`, `github.py`, `gitlab.py`, `release_common.py`, `pypi.py`, `pyproject.py`). (Justification: the densest area in the package: `cd_utils.py` is 50 % docstring, `git.py` 40 %, and it holds 28 of the 131 trivial `Returns:`. `pypi.py` has three functions whose entire docstring is "Returns: Return code of the subprocess.run call." over a one-line `subprocess.run`.) *Tests: Partial (`cd_utils.py` yes, the rest no; T002 first).*

- [ ] **T012**: [Docstrings] Trim `stouputils/io/`, `stouputils/parallel/`, `stouputils/version_pkg.py`, `stouputils/archive/repair/`. (Justification: 26 trivial `Returns:` between them. `parallel/common.py` carries six functions whose `Args:` reads "args: Tuple containing the function and the arguments list to pass to the function" above `args: tuple[Callable[[T], R], list[T]]`.) *Tests: Partial (T003, T005 first).*

- [ ] **T013**: [Docstrings] Trim `stouputils/print/`, `stouputils/decorators/`, `stouputils/collections/`, `stouputils/applications/`. (Justification: `print/colorizer.py` is eight trivial `Returns:` over eight short methods; `print/color_formatting.py` is 97 % docstring, almost all of it doctests worth keeping, wrapped in an `Examples:` header that adds nothing.) *Tests: Yes for `print/` and `collections/`, partial for the rest (T004, T006 first).*

- [ ] **T014**: [Docstrings] Remove the 37 `Examples:` headers whose body contains only doctests, repo-wide. (Justification: the `>>>` prompt already announces the example; the header costs a line and an indentation level in every one of them.) *Tests: Yes (the doctests themselves are the check). Depends: T011, T012, T013 to avoid conflicting edits.*

- [ ] **T015**: [Docstrings] Cut the module docstrings of `stouputils/installer/__init__.py` (82 of 89 lines), `stouputils/applications/__init__.py`, `stouputils/applications/upscaler/__init__.py` and `stouputils/applications/automatic_docs/__init__.py` down to what the module is plus one short example. (Justification: `automatic_docs/__init__.py` pastes a full GitHub Actions workflow into a docstring, `installer/__init__.py` pastes three complete usage scripts. Both duplicate the README and rot independently of it.) *Tests: No. Independent.*

- [ ] **T016**: [Docstrings] Delete the `Used by: :mod:...` trailer from every constant docstring in `stouputils/config.py`. (Justification: eleven hand-maintained reverse-dependency lists that no tool checks. The one under the `RESET`-to-`BOLD` block is also wrong: it attaches to `BOLD` alone, so Sphinx documents ten of the eleven colours with nothing.) *Tests: No. Independent.*

### Inlining

- [ ] **T017**: [Inlining] Inline `test_module_with_progress` from `stouputils/all_doctests/utils.py` into its single caller in `stouputils/all_doctests/launch.py:129`. (Justification: three lines of body, called once, in a 40-line file that exists only to hold it.) *Tests: Yes (the whole suite runs through it). Enables T033.*

- [ ] **T018**: [Inlining] Inline `VersionPrinter.print_tree` into `VersionPrinter.show` (`stouputils/version_pkg.py:192`, `:229`). (Justification: `print("\n".join(self.render_tree(name)))`, called once.) *Tests: Yes after T005. Depends: T005.*

- [ ] **T019**: [Inlining] Inline `check_existing_tag` and `prompt_delete_existing` into `handle_existing_tag` (`stouputils/continuous_delivery/release_common.py:87-142`). (Justification: three public functions and two callback parameters for one `requests.get`, one `input()` and two calls. Each is called exactly once, by the next one down.) *Tests: No (T002 first). Depends: T002.*

- [ ] **T020**: [Inlining] Inline `remove_colors` into its callers or keep it, but stop routing it through `remove_ansi` with a hand-passed pattern (`stouputils/print/utils.py:16`). (Justification: `remove_colors` is `remove_ansi(text, pattern=...)`; the two differ only by a regex constant, which belongs beside them as a module constant rather than as a default argument reached from a wrapper.) *Tests: Yes (10 doctests across both).*

---

## Phase 3: Architecture Flattening & Merging (Medium Risk)

### Style debt blocking everything else in `lock/`

- [ ] **T021**: [Simplification] Convert `stouputils/lock/` (`base.py`, `queue.py`, `re_entrant.py`, `redis_fifo.py`, `shared.py`, 1 039 lines) and `stouputils/ctx/common.py` from 4-space indentation to tabs. (Justification: the only six space-indented files in the package; every other module is tabs, per the repo convention. Do this **alone, in its own commit**, so the whitespace diff never hides a logic change.) *Tests: Yes (`lock/` has the second-largest doctest block in the package, 14 s of runtime). Blocks: T022.*

- [ ] **T022**: [Simplification] Move the doctest-only multiprocessing targets `_worker` and `_hold` (`stouputils/lock/base.py:118`, `:139`) next to the doctests that use them, or mark them clearly as fixtures in one place. (Justification: two module-level functions carrying `# pyright: ignore[reportUnusedFunction]` in production code, existing only so a doctest has something picklable to call.) *Tests: Yes. Depends: T021.*

### File merges

- [ ] **T023**: [Merge] Delete `stouputils/all_doctests/utils.py` and fold the remaining module docstring into `launch.py`. (Justification: after T017 the file holds nothing.) *Tests: Yes. Depends: T017.*

- [ ] **T024**: [Merge] Merge `stouputils/print/common.py` (40 lines) into `stouputils/print/utils.py`. (Justification: only `utils.py`, `message.py` and the generated re-export block import it. `common.py` holds one 8-line class and ten aliases; a whole module for it buys nothing.) *Tests: Yes. Watch: `PrintMemory` is shared mutable state, the merge must not duplicate it.*

- [ ] **T025**: [Merge] Merge `stouputils/io/utils.py` (29 lines, one function) into `stouputils/io/path.py`. (Justification: `safe_close` is the whole module; `path.py` is the natural home and already holds the file-handling helpers. One external caller to update, `parallel/capturer.py:12`.) *Tests: No. Independent.*

- [ ] **T026**: [Merge] Flatten `stouputils/archive/repair/` into `stouputils/archive/repair.py` and `stouputils/archive/scanner.py`, deleting the sub-package `__init__.py`. (Justification: a three-file package (23 + 160 + 319 lines) nested inside a four-file package, adding an import level and a re-export block for two modules.) *Tests: Yes (both modules carry doctests). Note: `python scripts/sync_api.py` after; `stouputils.archive.repair.X` import paths change.*

### Killing the callback plumbing in `continuous_delivery/`

This is the largest concentration of premature abstraction in the package: `PlatformConfig` already carries every platform difference as data, yet six one-line accessors are still passed as callbacks.

- [ ] **T027**: [Simplification] Replace `get_github_sha` / `get_gitlab_sha`, `get_github_commit_date` / `get_gitlab_commit_date`, `extract_github_commit_data` / `extract_gitlab_commit_data` with key-path fields on `PlatformConfig` (`sha_path`, `date_path`, `message_key`). Drop the `sha_extractor` and `date_extractor` parameters of `fetch_latest_tag` and `fetch_commits_since_tag`. (Justification: six public functions, each one dictionary lookup, wired through two callback parameters, to express a difference already expressed by the dataclass that both platforms build.) *Tests: No (T002 first). Depends: T002. Removes 6 names from the public API.*

- [ ] **T028**: [Simplification] Merge `delete_resource` and `delete_resource_unconditional` (`release_common.py:306`, `:322`) into `delete_resource(config, url, resource_name, check_first: bool = True)`. (Justification: the two bodies differ by one `if response.status_code == 200:`.) *Tests: No. Depends: T002.*

- [ ] **T029**: [Simplification] Fold `paginate_api` into `fetch_commits_since_tag`, or keep it and drop the `per_page` parameter that no caller passes. (Justification: one caller, and its `per_page=100` default silently has to match the `"per_page": "100"` string the caller puts in `params` for the pagination to terminate correctly. Coupling two arguments that must agree is worse than one function.) *Tests: No. Depends: T002.*

- [ ] **T030**: [Simplification] Collapse `validate_github_config` and `validate_gitlab_config` into one `validate_release_config(config, name_key)` in `release_common.py`. (Justification: identical bodies apart from the `project_name` / `project_path` key and the error string.) *Tests: No. Depends: T002.*

### Misc

- [ ] **T031**: [Simplification] Fix the "Private function" comments in `stouputils/parallel/common.py` (lines 20, 33, 65, 77, 121, 173, 232). (Justification: seven comments declaring functions private that are re-exported at `stouputils.starmap`, `stouputils.handle_parameters`, etc. Either the comment is wrong or the export is; T042 settles it, this task at minimum stops the file contradicting itself.) *Tests: Partial. Depends: T003.*

- [ ] **T032**: [Simplification] Drop `CPU_COUNT: int = Cfg.CPU_COUNT` (`parallel/common.py:17`) and read `Cfg.CPU_COUNT` at use sites. (Justification: the alias is captured at import time, so setting `Cfg.CPU_COUNT` afterwards changes `normalize_parallel_params` but not `stouputils.CPU_COUNT`. Two values for one setting.) *Tests: Partial. Note: `stouputils.CPU_COUNT` disappears unless re-exported by hand, so treat the removal itself as Phase 4 if that matters. Depends: T003.*

- [ ] **T033**: [Simplification] Give `stouputils/applications/automatic_docs/sphinx/__init__.py` and `.../highlighting/__init__.py` the same generated `name as name` re-export form as the rest of the package, instead of hand-written `__all__` lists. (Justification: the only two `__all__` lists in the package, and `sync_api.py` deliberately stops recursing at them (scripts/sync_api.py:`exports_of`), so those two subtrees silently opt out of the consistency check CI runs.) *Tests: No. Note: run `python scripts/sync_api.py` after.*

---

## Phase 4: Public API Surface (Breaking, needs explicit approval)

264 names sit in the flat namespace. These remove or rename some of them, so they need a major version bump and a line in the changelog. **Do not start without a go/no-go on each.**

- [ ] **T041**: [API] Rename the `TypeVar` re-exported as `stouputils.T` (`stouputils/image/cropping.py:17`) to `_NumberT`. (Justification: `stouputils.T` is a bare `TypeVar` in the top-level namespace of a published library, exported by accident because `sync_api.py` promotes every public top-level name. Anyone doing `from stouputils import *` gets it.) *Tests: Yes (cropping has doctests). Risk: low, nobody can be using it deliberately.*

- [ ] **T042**: [API] Prefix the pickling helpers of `stouputils/parallel/common.py` with `_` (`nice_wrapper`, `starmap`, `delayed_call`, `handle_parameters`, `normalize_parallel_params`, `run_sequential`, `set_process_priority`), and the doctest fixtures `doctest_square` / `doctest_slow` in `parallel/multi.py:20-24`. (Justification: nine names in the public API that the source itself documents as private or as test material. They must stay module-level for pickling; a `_` prefix does not affect that, and it is what `sync_api.py` reads to keep a name out of the namespace.) *Tests: Partial. Depends: T003, T031. Risk: medium, `set_process_priority` is plausibly used downstream.*

- [ ] **T043**: [API] Delete the ten backwards-compatibility constant aliases in `stouputils/print/common.py:15-24` and export `Cfg` instead. (Justification: a second definition of `RESET`, `RED`, ... `BAR_FORMAT` that must stay in step with `config.py` by hand and that decouples from it at import time, see T032.) *Tests: No. Risk: **high**, `stp.RED` and friends are the most likely names in downstream code. Consider keeping them and simply documenting them as aliases.*

- [ ] **T044**: [API] Delete `stouputils/_deprecated.py`. (Justification: five shims deprecated in v1.8.0 and v1.28.0; the package is at v26.3.1.) *Tests: No. Risk: medium.*

- [ ] **T045**: [API] Add `stouputils.continuous_delivery.release_common` and `.cd_utils` internals to `INTERNAL` in `scripts/sync_api.py:29`, or give `continuous_delivery/__init__.py` a curated `__all__`. (Justification: 73 of the 264 root names come from `continuous_delivery`, most of them helpers such as `paginate_api`, `handle_response`, `validate_required_keys` and `log_success` that only its own two platform modules call. The flat namespace should carry `upload_to_github`, `upload_to_gitlab`, `create_release` and the changelog entry points, not the plumbing.) *Tests: No. Risk: medium, and it is the single biggest reduction available.*

---

## Deliberately not proposed

- **`lazy.py` / `ALWAYS_LAZY`**: looks like a one-class abstraction over a `bool`, but PEP 810 requires an object with `__contains__` and the alternative is a per-module list. Keep.
- **`typing.py::is_generic_instance` overloads**: five `@overload` stubs for one function, but they are what makes `TypeIs` narrow correctly under pyright strict. Keep.
- **`decorators/common.py::safe_wraps`**: a `functools.wraps` replacement, which reads like reinvention until you hit the Sphinx-mock `TypeError` its docstring documents. Keep, and keep that docstring.
- **`print/message.py` `*c` variants**: seven two-line wrappers, and deleting them is tempting, but they are the documented half of the module's API (`infoc`, `debugc`, ...) and each is one keyword argument. Keep unless T045 curates them out.
- **`archive/repair/scanner.py`, `print/colorizer.py`, `version_pkg.py`**: recent, well-factored, docstring-heavy but not over-abstracted. They only need the Phase 2 docstring trim.
- **`lock/shared.py`**: 56 lines shared by `base.py` and `redis_fifo.py`, a real shared module rather than a leftover. Keep, tabs-only fix in T021.

## Suggested execution order

`T001` → Phase 1 (T002-T006, parallel) → T007-T010 → T011-T016 → T017-T020 → **T021 alone** → T022-T026 → T027-T030 → T031-T033 → stop for approval → Phase 4.

Run the regression command after every task. Run `python scripts/sync_api.py` after T009, T023, T025, T026, T027, T033 and every Phase 4 task.
