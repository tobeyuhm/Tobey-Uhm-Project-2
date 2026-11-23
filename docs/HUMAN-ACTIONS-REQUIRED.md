# Before submitting: what only Tobey can do

1. **Read and own the decision.** Check every number in `docs/decision-memo.md` against `output/report.md`. If you change the action, range or triggers, edit `config/recommendation.json` and the memo, then run `python analysis.py`.
2. **Create the GitHub repo and push.** Create `tobeyuhm/Tobey-Uhm-Project-2` (public, or private with instructor access). Then run `git remote add origin https://github.com/tobeyuhm/Tobey-Uhm-Project-2.git` and `git push -u origin main`.
3. **Locked Changed-Input Record (AI closed the whole time):**
   1. Fill every `TO BE WRITTEN` field in `docs/locked-prediction.md`. Pick a value that is not already in the stress table.
   2. `git add docs/locked-prediction.md` -> `git commit -m "Locked prediction (AI off)"` -> `git push`.
   3. `python locked_test.py`, then commit and push `output/locked_test_result.*`.
   4. Write section 5 of `docs/validation-and-ai-use.md`: expected vs actual, decision effect, diagnosis.
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
