# Resume Merge

A Claude Code skill that intelligently merges two PDF resumes. It identifies jobs, skills, and education entries present in a donor resume that are missing from a primary resume, then produces a single dated PDF output — preserving the primary resume's formatting.

---

## How It Works

1. **Extract** — PyMuPDF pulls raw text from both PDFs
2. **Compare** — Claude (`claude-sonnet-4-6`) compares the two resumes and returns a JSON object listing missing jobs, skills, and education entries
3. **Build** — Contact info from `.env` and all missing entries are injected into the HTML template
4. **Render** — WeasyPrint converts the in-memory HTML to a Letter-size PDF

Prompt caching reduces API costs ~90% on repeated runs against the same source resume.

---

## Setup

### 1. Install system dependencies (macOS)

```bash
brew install pango cairo libffi
```

### 2. Install Python packages

```bash
pip3 install weasyprint python-dotenv
```

### 3. Verify

```bash
python3 -c "import fitz, anthropic, weasyprint; print('all dependencies ok')"
```

### 4. Configure `.env`

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...

RESUME_OWNER_NAME=Your Name
RESUME_OWNER_EMAIL=you@example.com
RESUME_OWNER_PHONE=+1 555 000 0000
RESUME_OWNER_LOCATION=City, ST ZIP
RESUME_OWNER_WEBSITE=https://yoursite.com
LINKEDIN_URL=https://linkedin.com/in/yourhandle
GITHUB_USERNAME=yourhandle
GITHUB_URL=https://github.com/yourhandle
GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-repo
```

---

## Input Files

Place two PDFs in `input_files/` before running:

| File | Role |
|---|---|
| `source.pdf` | **Destination** — primary resume whose formatting is preserved |
| `input.pdf` | **Donor** — secondary resume that jobs/skills are pulled from |

The originals are never modified.

---

## Usage

### Via Claude Code slash command (recommended)

```
/resume-merge
```

Claude confirms the input files exist, runs the pipeline, and reports the output path.

### Via command line

```bash
python3 src/merge_resumes.py \
  --source input_files/source.pdf \
  --input input_files/input.pdf
```

### Via Jupyter notebook (for debugging)

```bash
jupyter notebook notebook/resume_merge.ipynb
```

---

## Output

```
output_files/resume-merge-YYYY-MM-DD.pdf
```

No intermediate HTML file is saved.

---

## Project Structure

```
resumes/
├── .env                          secrets (never committed)
├── .claude/
│   ├── settings.json             project permissions
│   └── commands/
│       └── resume-merge.md       /resume-merge slash command
├── src/
│   └── merge_resumes.py          Python pipeline
├── notebook/
│   └── resume_merge.ipynb        interactive debugging notebook
├── docs/
│   └── plan.txt                  implementation plan
├── templates/
│   └── resume_merged.html        CSS/layout template for PDF generation
├── input_files/                  input PDFs
└── output_files/                 generated PDFs
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | 0.84.0+ | Claude API client |
| `PyMuPDF` (`fitz`) | 1.27+ | PDF text extraction |
| `Jinja2` | 3.1+ | templating |
| `weasyprint` | latest | HTML-to-PDF rendering |
| `python-dotenv` | latest | `.env` loading |
