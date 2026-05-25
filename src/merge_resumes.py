"""
Resume merge pipeline.

Usage:
    python3 src/merge_resumes.py \
        --source input/source.pdf \
        --input  input/input.pdf

Output: output_files/resume-merge-YYYY-MM-DD.pdf
"""

import argparse
import datetime
import json
import os
import re
import sys

import anthropic
import fitz  # PyMuPDF

# Load .env from project root if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

class PDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_text(self) -> str:
        doc = fitz.open(self.pdf_path)
        return "\n".join(page.get_text() for page in doc)


# ---------------------------------------------------------------------------
# Claude-powered comparison
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """\
You are a professional resume analyst. You will be given two resumes:

1. DESTINATION RESUME — the primary resume whose formatting and style must be preserved.
2. DONOR RESUME — a secondary resume that may contain additional jobs and skills.

Your task:
- Compare the two resumes.
- Identify jobs in the DONOR that are NOT already in the DESTINATION.
  Match jobs by employer name AND approximate date range. Treat the same employer
  at a different date range as a separate entry. Do NOT include duplicates.
- Identify skill categories or individual skills in the DONOR that are NOT in the DESTINATION.
- Identify education entries in the DONOR that are NOT already in the DESTINATION.
  Match education by institution and degree. Do NOT include duplicates.
- Adapt verbose numbered deliverables from the DONOR into concise bullet points
  matching the style used in the DESTINATION resume.
- Normalize all dates to "Mon YYYY" format (e.g. "Aug 2025").
- Sort missing_jobs in reverse chronological order (most recent first).

Return ONLY a JSON object with this exact schema — no markdown fences, no extra text:
{
  "missing_jobs": [
    {
      "company": "string",
      "title": "string",
      "dates": "string",
      "location": "string",
      "bullets": ["string", ...]
    }
  ],
  "missing_skills": [
    {
      "category": "string",
      "items": ["string", ...]
    }
  ],
  "missing_education": [
    {
      "degree": "string",
      "institution": "string",
      "dates": "string",
      "details": "string"
    }
  ]
}

If nothing is missing, return empty arrays for all keys.
"""


class ResumeComparator:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def compare(self, destination_text: str, donor_text: str) -> dict:
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_INSTRUCTIONS,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": f"DESTINATION RESUME:\n\n{destination_text}",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"DONOR RESUME:\n\n{donor_text}\n\nReturn JSON only.",
                }
            ],
        )
        return self._parse_response(response.content[0].text)

    @staticmethod
    def _parse_response(text: str) -> dict:
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(text.strip())


# ---------------------------------------------------------------------------
# HTML building
# ---------------------------------------------------------------------------

class HTMLBuilder:
    def __init__(self, template_html: str):
        self.template = template_html

    def build(self, merge_data: dict) -> str:
        html = self.template
        html = self._apply_env_contact(html)
        html = self._inject_jobs(html, merge_data.get("missing_jobs", []))
        html = self._inject_skills(html, merge_data.get("missing_skills", []))
        html = self._inject_education(html, merge_data.get("missing_education", []))
        return html

    @staticmethod
    def _apply_env_contact(html: str) -> str:
        name     = os.getenv("RESUME_OWNER_NAME")
        location = os.getenv("RESUME_OWNER_LOCATION")
        phone    = os.getenv("RESUME_OWNER_PHONE")
        email    = os.getenv("RESUME_OWNER_EMAIL")
        website  = os.getenv("RESUME_OWNER_WEBSITE")
        github   = os.getenv("GITHUB_URL")
        linkedin = os.getenv("LINKEDIN_URL")

        if name:
            html = re.sub(r"<h1>[^<]*</h1>", f"<h1>{name.upper()}</h1>", html, count=1)
        if location:
            html = re.sub(r'<div class="contact">[^<]*</div>', f'<div class="contact">{location}</div>', html, count=1)
        if phone or email or linkedin:
            linkedin_tag = f'<a href="{linkedin}">LinkedIn</a>' if linkedin else "LinkedIn"
            parts = " | ".join(filter(None, [phone, email, linkedin_tag]))
            html = re.sub(r'<div class="contact">.*?(gmail|email|phone|\d{3}-\d{3}|LinkedIn).*?</div>', f'<div class="contact">{parts}</div>', html, count=1, flags=re.IGNORECASE | re.DOTALL)
        if github or website:
            parts = " | ".join(filter(None, [github, website]))
            html = re.sub(r'<div class="contact">[^<]*(github|gitgub|hometask|http)[^<]*</div>', f'<div class="contact">{parts}</div>', html, count=1, flags=re.IGNORECASE)

        return html

    @staticmethod
    def _job_block(job: dict) -> str:
        bullets_html = "\n".join(
            f"    <li>{b}</li>" for b in job.get("bullets", [])
        )
        location = job.get("location", "")
        return (
            f'\n<div class="job">\n'
            f'  <div class="job-header"><span>{job["company"]}</span>'
            f'<span>{job["dates"]}</span></div>\n'
            f'  <div class="job-subheader"><span>{job["title"]}</span>'
            f'<span>{location}</span></div>\n'
            f"  <ul>\n{bullets_html}\n  </ul>\n"
            f"</div>\n"
        )

    def _inject_jobs(self, html: str, jobs: list) -> str:
        if not jobs:
            return html
        insertion = "".join(self._job_block(j) for j in jobs)
        # Insert all new jobs immediately before <h2>Education</h2>
        return html.replace("<h2>Education</h2>", insertion + "<h2>Education</h2>", 1)

    @staticmethod
    def _inject_skills(html: str, skills: list) -> str:
        if not skills:
            return html
        new_items = "\n".join(
            f'  <li><b>{s["category"]}</b>: {", ".join(s["items"])}</li>'
            for s in skills
        )
        return html.replace("</ul>\n\n<h2>Agentic", new_items + "\n</ul>\n\n<h2>Agentic", 1)

    @staticmethod
    def _inject_education(html: str, education: list) -> str:
        if not education:
            return html
        new_paras = "\n".join(
            f'  <p><b>{e["degree"]}</b>, {e["institution"]}, {e["dates"]}.'
            + (f' {e["details"]}' if e.get("details") else "") + "</p>"
            for e in education
        )
        return html.replace("</div>\n\n<h2>Publications", new_paras + "\n</div>\n\n<h2>Publications", 1)


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------

class PDFRenderer:
    def render(self, html_content: str, output_path: str) -> str:
        try:
            from weasyprint import HTML as WeasyprintHTML
        except ImportError:
            print(
                "ERROR: weasyprint is not installed.\n"
                "Install it with:\n"
                "  brew install pango cairo libffi\n"
                "  pip3 install weasyprint",
                file=sys.stderr,
            )
            sys.exit(1)

        WeasyprintHTML(string=html_content).write_pdf(output_path)
        return output_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def _load_template_html() -> str:
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "resume_merged.html",
    )
    if not os.path.exists(template_path):
        print(
            f"ERROR: HTML template not found at {template_path}\n"
            "The file 'templates/resume_merged.html' must exist as the styling template.",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(template_path, encoding="utf-8") as f:
        return f.read()


def run_merge(source_path: str, input_path: str, output_dir: str) -> str:
    print("Extracting text from PDFs...")
    destination_text = PDFExtractor(source_path).extract_text()
    donor_text = PDFExtractor(input_path).extract_text()

    print("Comparing resumes with Claude...")
    client = anthropic.Anthropic()
    merge_data = ResumeComparator(client).compare(destination_text, donor_text)

    missing_jobs = merge_data.get("missing_jobs", [])
    missing_skills = merge_data.get("missing_skills", [])
    missing_education = merge_data.get("missing_education", [])
    print(f"  Found {len(missing_jobs)} missing job(s), {len(missing_skills)} missing skill category(s), {len(missing_education)} missing education entry(s).")

    print("Building merged HTML...")
    template_html = _load_template_html()
    merged_html = HTMLBuilder(template_html).build(merge_data)

    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"resume-merge-{date_str}.pdf")

    print(f"Rendering PDF to {output_path}...")
    PDFRenderer().render(merged_html, output_path)

    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge two PDF resumes, adding missing jobs, skills, and education to the destination."
    )
    parser.add_argument("--source", required=True, help="Path to destination/primary resume PDF")
    parser.add_argument("--input", required=True, help="Path to donor/secondary resume PDF")
    parser.add_argument("--output", default="output_files", help="Output directory (default: output_files/)")
    args = parser.parse_args()

    for path, label in [(args.source, "--source"), (args.input, "--input")]:
        if not os.path.exists(path):
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    result = run_merge(args.source, args.input, args.output)
    print(f"\nDone. Merged resume written to: {result}")
