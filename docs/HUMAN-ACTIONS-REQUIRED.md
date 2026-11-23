# Before submitting: what only Tobey can do

0. **Read `docs/locked-prediction-instructions.md`** before closing AI for the locked record.
1. **Read and own the decision.** Check every number in `docs/decision-memo.md` against `output/report.md`. If you change the action, range or triggers, edit `config/recommendation.json` and the memo, then run `python analysis.py`.
2. **GitHub repo: done** (2026-11-23). https://github.com/tobeyuhm/Tobey-Uhm-Project-2, public; opens logged out. `git push` now works from this folder.
3. **Locked Changed-Input Record: done** (prediction `066734f`, run `a458ecc`, reconciliation in validation section 5). Read the reconciliation and change any wording that isn't how you'd say it.
4. **Verify the AI table** in `docs/validation-and-ai-use.md`, section 6:
   - Confirm that Labs 13-17 used Codex GPT-5, and correct it if a different tool or model was shown.
   - Fill the "Recommendation wording" disposition.
5. **Partner cold run:** record it in section 7, row 3 (Lab 20). If there was a failure, fix it and push.
6. **Hand checks** in `docs/data-card.md`, section 4 (two boxes).
7. **Record the videos** from `docs/video-scripts.md`:
   - Use the webcam inset and upload each as Unlisted with captions.
   - Correct the auto-captions and replace each `docs/transcript-video-N.txt` with the corrected text.
   - Video 2's locked-test lines need your actual result.
8. **Fill the manifest** `docs/project-submission-manifest.csv`: URLs, durations, access checks.
9. **Freeze it:** `git tag project2-submission` -> `git push --tags`. Attach `docs/decision-memo.md` and `docs/validation-and-ai-use.md` to Brightspace.
