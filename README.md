# Agentic Architect Challenge

This repository contains the Part 1 system design, Part 2 webpage summarizer, and Part 3 document agent for the Developer Intern challenge.

## Contents

- [`docs/part1-system-design.md`](docs/part1-system-design.md): customer-support email agent architecture.
- [`docs/email-agent-flowchart.png`](docs/email-agent-flowchart.png): Part 1 workflow diagram.

- [`docs/part2-technical-implementation.md`](docs/part2-technical-implementation.md): robust webpage scraping and concise summarization design.

- `src/web_summarizer/`: Part 2 implementation.

- `tests/`: deterministic Part 2 and calculator tests that do not call external websites or model APIs.

- [`docs/sample-product-faq.md`](docs/sample-product-faq.md): the single sample document used by Part 3.

- [`docs/part3-practical-evaluation.md`](docs/part3-practical-evaluation.md): Part 3 design and verification notes.
- [`output/pdf/agentic-architect-challenge-summary.pdf`](output/pdf/agentic-architect-challenge-summary.pdf): one-page architecture, trade-offs, and failure-handling summary.

- `src/document_agent/`: Part 3 document question-answering agent with session memory and an optional calculator tool.

## Part 2 Setup

Requirements:

- Python 3.11 or newer
- Chromium through Playwright if you want to test JavaScript-rendered pages

Create and activate a virtual environment, then install the project:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,browser]"
python -m playwright install chromium
```

You can run offline mode immediately after installation. It needs no API key.

## Run Part 2 Offline

Test a regular webpage with static HTTP fetching:

```powershell
summarize-webpage "https://quotes.toscrape.com/" --offline --no-browser
```

Test a JavaScript-rendered webpage with Playwright fallback:

```powershell
summarize-webpage "https://quotes.toscrape.com/js/" --offline
```

`--offline` uses a local extractive summarizer. It can test fetching, extraction, browser fallback, chunking, and the final length guardrail, but its writing quality is different from an AI-generated summary. `--no-browser` disables the Playwright fallback.

The command prints JSON with fields such as:

```json
{
  "url": "https://example.com/article",
  "summary": "A concise summary of the webpage.",
  "fetch_method": "static-http",
  "source_word_count": 2480,
  "chunk_count": 3,
  "summary_word_count": 112
}
```

## Run Tests

```powershell
pytest
```

The 18 unit tests use local HTML and fake fetchers and check the calculator. They do not require an API key or internet connection.

Manual offline checks completed:

- `https://quotes.toscrape.com/`: `fetch_method` was `static-http`; the final summary was 132 words.
- `https://quotes.toscrape.com/js/`: `fetch_method` was `playwright`; the final summary was 149 words.

Both final summaries stayed within the default 150-word limit. Long-content chunking and map-reduce routing are covered by unit tests rather than these two short webpages.

## Run Part 3

Part 3 uses a Gemini API model. Google offers a limited Free Tier for certain models; check your project and selected model in Google AI Studio before running it. Create a Gemini API key in Google AI Studio. From the project directory, copy the template and edit the local `.env` file (skip the copy if you already have `.env`):

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in `GEMINI_API_KEY` and `GEMINI_MODEL` with your own key and a model listed as Free Tier for your project. Save the file, then run:

```powershell
document-agent
```

Try this conversation in one session:

```text
My name is Alex.
What is the price of the Pro plan?
What is my name?
How much do 3 months of the Pro plan cost?
What is the refund policy?
exit
```

The agent should remember Alex, answer the document question, print `[calculator called]` only for the calculation, and say the document does not specify a refund policy. Session memory is in memory only and clears when you exit. Never commit `.env` or your API key.

Manual live Gemini verification completed successfully:

- The agent answered that the Pro plan costs `$12 per month` based on the sample document.
- It remembered that the user's name was Alex later in the same session.
- It called the calculator only for the three-month cost and returned `$36`.
- It stated that the document does not specify a refund policy.

## Important Limitations

- Some websites prohibit automated scraping in their terms or `robots.txt`; deployment should enforce an allowlist and site-specific policy.
- Login-protected, CAPTCHA-protected, or anti-bot pages are intentionally not bypassed.
- The Playwright fallback is more resource-intensive than static HTTP fetching and should be concurrency-limited in production.
- Model-generated summaries are non-deterministic. The implementation applies hard word and bullet limits, while factual quality should also be evaluated with representative datasets.

