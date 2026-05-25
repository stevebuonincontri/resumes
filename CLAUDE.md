# Resume Merge Workspace

This project provides a Claude Code skill (`/resume-merge`) that intelligently merges two PDF resumes: it identifies jobs, skills, and education entries present in a secondary resume that are missing from a primary resume, then produces a single dated PDF output.

---

## Directory Layout

```
resumes/
├── CLAUDE.md              ← this file
├── .env                   ← secrets and personal vars (never committed)
├── .gitignore
├── .claude/
│   ├── settings.json      ← project permissions
│   └── commands/
│       └── resume-merge.md  ← /resume-merge slash command
├── src/
│   └── merge_resumes.py   ← Python pipeline
├── notebook/
│   └── resume_merge.ipynb ← interactive exploration notebook
├── docs/
│   └── plan.txt           ← plain-text implementation plan
├── templates/
│   └── resume_merged.html ← CSS/layout template for PDF generation
├── input_files/           ← legacy input folder (preserved)
└── output_files/          ← generated PDFs written here
```

---

## Input Convention

Create an `input/` folder and place exactly two PDFs in it before running the skill:

| Filename | Role |
|---|---|
| `source.pdf` | **Destination** — the primary resume whose formatting and style is preserved |
| `input.pdf` | **Donor** — the secondary resume that jobs/skills are pulled from |

The pipeline adds to `source.pdf` anything found in `input.pdf` that is not already present. The originals are never modified.

---

## Usage

### Via Claude Code slash command (recommended)
```
/resume-merge
```
Claude will confirm the input files exist, run the pipeline, and report the output path.

### Via command line
```bash
python3 src/merge_resumes.py \
  --source input/source.pdf \
  --input input/input.pdf
```

### Via Jupyter notebook (for debugging/exploration)
```bash
jupyter notebook notebook/resume_merge.ipynb
```

---

## Output

A single PDF file written to `output_files/resume-merge-YYYY-MM-DD.pdf`.

No intermediate HTML file is saved.

---

## Dependencies

**Already installed:**
- `anthropic` 0.84.0+
- `PyMuPDF` (`fitz`) 1.27+
- `Jinja2` 3.1+
- `reportlab` 4.5+

**Needs install:**
```bash
# macOS system dependency (required by weasyprint)
brew install pango cairo libffi

# Python packages
pip3 install weasyprint python-dotenv
```

**Verify all imports:**
```bash
python3 -c "import fitz, anthropic, weasyprint; print('all dependencies ok')"
```

---

## Environment

Fill in `.env` with your values. The pipeline loads it automatically at startup (requires `pip3 install python-dotenv`). Alternatively, export variables manually:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Variables in `.env`:
| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required — Claude API access |
| `RESUME_OWNER_NAME` | Your full name |
| `RESUME_OWNER_EMAIL` | Contact email |
| `RESUME_OWNER_PHONE` | Contact phone |
| `RESUME_OWNER_LOCATION` | City, ST ZIP |
| `RESUME_OWNER_WEBSITE` | Personal/portfolio URL |
| `LINKEDIN_URL` | Full LinkedIn profile URL |
| `GITHUB_USERNAME` | GitHub handle |
| `GITHUB_URL` | Full GitHub profile URL |
| `GITHUB_TOKEN` | Personal access token (for API calls) |
| `GITHUB_REPO` | Repository name |

---

## How It Works

1. **Extract** — `PyMuPDF` pulls raw text from both PDFs
2. **Compare** — Claude (`claude-sonnet-4-6`) receives the destination resume as cached context and the donor resume as the user message; it returns a JSON object listing missing jobs, skills, and education entries
3. **Build** — `HTMLBuilder` first substitutes contact info (name, phone, email, GitHub URL, website) from `.env` into the template, then injects missing jobs, skills, and education into `templates/resume_merged.html`
4. **Render** — `WeasyPrint` converts the in-memory HTML to PDF, honoring the `@page` CSS rules for Letter-size output

---

## Legacy Folders

- `input_files/` — original input PDFs (preserved, not used by the new pipeline)
- `output_files/` — destination for all generated PDFs
