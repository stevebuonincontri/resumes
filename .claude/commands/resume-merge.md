# Resume Merge

Merge two PDF resumes: pull jobs, skills, and education entries from `input/input.pdf` that are missing from `input/source.pdf`, and produce a dated PDF in `output_files/`. The source resume formatting is preserved exactly. Neither input file is modified.

## Steps

1. **Check inputs exist.** Verify both files are present:
   - `input/source.pdf` (destination — formatting is preserved)
   - `input/input.pdf` (donor — missing content is pulled from here)

   If either file is missing, tell the user which file is absent and stop.

2. **Check weasyprint is installed.**
   ```bash
   python3 -c "import weasyprint" 2>/dev/null || echo "MISSING"
   ```
   If it prints `MISSING`, inform the user they need to run:
   ```bash
   brew install pango cairo libffi
   pip3 install weasyprint
   ```
   Then stop and wait for them to install it.

3. **Run the merge pipeline.**
   ```bash
   python3 src/merge_resumes.py \
     --source input/source.pdf \
     --input input/input.pdf
   ```

4. **Report the result.**
   - On success: print the output file path (format: `output_files/resume-merge-YYYY-MM-DD.pdf`)
   - On error: show the full error output and suggest:
     - Check that `ANTHROPIC_API_KEY` is set in the environment
     - Check that `weasyprint` is installed (`pip3 install weasyprint`)
     - Check that both input PDFs are readable

## Output

A single PDF file at `output_files/resume-merge-YYYY-MM-DD.pdf`. No HTML file is saved.

## Example prompts

- "Merge my two resumes and save the result."
- "Update the source resume using the other input resume, keeping the source formatting and adding any missing jobs, education, or skills."
- "Take `input/source.pdf` and enrich it with jobs and education from `input/input.pdf`."
