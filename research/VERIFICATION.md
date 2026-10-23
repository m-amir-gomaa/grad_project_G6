# Foundation verification

Checked 22 October 2026 in the shared NixOS workspace.

- **PDF scan:** 73 distinct linked PDF contents, 137 pages, 28 pages processed using Arabic/English OCR; no reported download or scan errors. The matched location observations were extracted from embedded text. The output contains 20 provisional labels and 648 observations, with zero approved scheduling spaces.
- **Persistence:** the local `tanta-university` draft profile contains 73 source-document versions, 20 candidates and 648 observations. SQLite integrity and foreign-key checks passed.
- **Regression suite:** `nix-shell --run 'uv run python -m unittest discover -s tests -v'` passed **24 tests**. Cases include university boundaries, immutable history, effective-date queries, changed PDF contents, Arabic labels, missing/duplicate student assignments, capacity, closures, travel, shared physical atoms, exam-room allocation, pins, and repair priorities.
- **Synthetic solve:** `nix-shell --run 'uv run python -m timetabling.demo'` returned `OPTIMAL` for both the baseline and lab-closure repair. Eleven events cover first/second/summer term labels. Four lab/practical events moved; post-solve validation reported no errors.
- **Dependency/runtime:** OR-Tools 9.15.6755; project Python dependencies locked in `uv.lock`. The Nix development shell supplies the native C++/zlib runtime and Poppler/Tesseract commands; Arabic and English OCR languages were verified.
- **Documentation:** local Markdown targets were checked for missing files.

The result is a tested small modelling foundation, not evidence of whole-faculty performance. No real Tanta enrolments, complete building model, production login/authorization, automated floor-plan interpretation, or deployed application were evaluated. The pilot's post-solve audit shares rule helpers with the solver.

See [architecture and algorithms](ARCHITECTURE-AND-ALGORITHMS.md) for the implemented boundary and [scan evidence](PDF-SPACE-REGISTRY.md) for unresolved physical identities.
