# OMR Grade — Phase 0 Audit

Repo: eyadcsdev/OMR-Auto-Grading-System (branch `main`, Python 3.14, PySide6 desktop app).
No code was changed for this audit. Earlier in the session two fixes were made to `omr_core.py` / `gui.py` (see section 3).

## 1. What exists

| File | Lines | Role |
|---|---|---|
| omr_core.py | ~330 | Image -> answers (threshold + pixel counting) and drawing |
| gui.py | 785 | PySide6 UI, plus a lot of business logic |
| db.py | 177 | SQLite: `students`, `results` tables |
| analytics.py | 95 | pandas stats, matplotlib histogram, Excel export |

No tests, no requirements file, no CI. `tempCodeRunnerFile.py` is an empty stray file.

## 2. Why the current OMR is not reliable (omr_core.py)

1. **One grid assumption.** The image is resized to 700x700, the largest 4-point contour is warped, and the result is split into `questions x choices` equal cells. Any layout that is not a single bubble grid (our sheet: two columns, header, barcode, paper code, marks box) gets misaligned.
2. **Rectangle detection by Canny.** The page/box border on our sheet is faint pink, so contour detection often finds nothing or the wrong box (reproduced: "Could not detect answer key").
3. **Square resize destroys aspect ratio.** The sheet is ~1:4.5 in the crop; squashing it to 700x700 distorts the bubbles.
4. **Divisibility crash.** `np.vsplit(700, 12)` raised "array split does not result in an equal division" (fixed by trimming).
5. **Winner-takes-all.** `argmax` of white pixels per cell: a blank row returns option A, a double mark returns one of them, an ambiguous mark is guessed. There is no BLANK / MULTIPLE / AMBIGUOUS state and no confidence. Pixel counts include printed letters and outlines inside each cell, so empty rows are biased towards the option with more printed ink.
6. **Global Otsu threshold** only: shadows, glare and uneven light change the result.
7. **No image-quality check, no template, no registration markers.**
8. **Score is a percentage only**; marking, scoring and drawing are in the same function.

Mitigation done in this session (prototype only): the grid is cut out using the dark-pink "A|B|C|D" header, with fallbacks. It reads our 24-question master key's left column correctly (`2,2,3,1,0,0,0,0,2,2,3,3`) but is still a heuristic, not the production design.

## 3. Changes already made in the working tree (uncommitted)

- omr_core.py: `_extract_grid()` (header-based grid cut), whole-image fallback when no rectangle, divisibility-safe split.
- gui.py: defaults 12 questions and the real key.
- New test images in `Results/` (`key_tight_crop.png`, master key copy).

## 4. Application / data findings

- **DB schema:** `students(id, student_id UNIQUE, student_name, created_at)`, `results(id, student_id, student_name, exam_code, score, answers CSV, created_at)`. No exams table, no answer-key table, no foreign keys, no indexes, no audit data. The key is not saved with a result, so results cannot be re-graded or audited.
- **Privacy:** `omr_results.db`, three `.xlsx` files and `Results/*.png` are tracked in Git or lying in the repo. Corrected sheet images are stored as plain PNGs named by student ID. "Clear All Results" removes DB rows but leaves images; deleting a student leaves results and images.
- **Paths:** DB and `Results/` are relative to the current working directory.
- **Error handling:** no try/except around `process_omr`, `detect_answer_key`, or `save_to_db`; DB connections leak on exceptions; `cv2.imwrite` result is not checked.
- **Logic in the UI that must move to a domain layer:** key parsing/validation, save rules (exam code required), Excel import (header aliases, duplicate counting), filename convention, score display.
- **SQL injection:** none found (parameterized).
- **Reusable as logic:** student CRUD + duplicate rule, key validation, Excel header aliases and import stats, export columns, basic stats + 10-bin histogram, results log ordering.
- **Desktop-only (drop):** all PySide6, OpenCV camera loop, QFileDialog, pandas/matplotlib, sqlite3 relative path.

## 5. Environment (this machine)

| Need | Status |
|---|---|
| Git 2.55 | OK |
| Flutter/Dart, JDK 17, Android SDK + NDK + CMake, OpenCV Android SDK | **MISSING** (about 7 GB; install on D: — C: has 22 GB free, D: 49 GB) |
| iOS build | needs a Mac + Xcode (not possible on this PC) |
| Real Android phone | recommended for camera work |

## 6. Migration plan

Keep: the product workflow, DB entities (extended), student/exam rules, Excel columns.
Replace: omr_core.py with a template-driven C++/OpenCV engine; PySide6 UI with Flutter.
The Python code stays in the repo as a reference implementation and as a fast way to prototype and measure the algorithm against the regression images before porting to C++.

Branches (from `main` after committing/stashing current work): `feat/flutter-architecture`, `feat/camera`, `feat/native-omr`, `feat/template-system`, `feat/master-key`, `feat/student-grading`, `feat/human-review`, `feat/results`, `feat/cloud-sync`, `test/omr-regression`.

## 7. Open decisions / blockers before Phase 1

1. Install Flutter + Android toolchain on D: (needs your OK).
2. Google Stitch designs: not in the repo. Needed as the visual source of truth for Phase 1 UI.
3. Test data: the "18/24 = 75%" master/student pair (wrong: Q2, 6, 7, 9, 10, 17) is not in the repo. Only a master-key image of the left column exists. We need both full-page images (and a printed blank) to build the regression test and calibrate `mcq_24_v1`.
4. Registration markers: the real sheet has no 4 corner markers. Decide: (a) print/add markers on future sheets, or (b) register using the pink header + table border (works on this sheet, less robust).
5. Commit hygiene: remove `omr_results.db`, `*.xlsx`, `Results/*.png` from Git tracking (`.gitignore`) — needs your OK before touching history.
6. Supabase project and Sentry/PostHog accounts are needed only from Phase 12.
