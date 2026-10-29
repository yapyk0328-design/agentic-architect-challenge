from web_summarizer.guardrails import (
    count_bullets,
    count_words,
    enforce_summary_guardrail,
    guardrail_violations,
)


def test_reports_word_and_bullet_violations():
    summary = "\n".join(f"- point {index} with words" for index in range(7))

    violations = guardrail_violations(
        summary,
        max_words=10,
        max_bullets=5,
    )

    assert "summary exceeds 10 words" in violations
    assert "summary exceeds 5 bullet points" in violations


def test_guardrail_enforces_hard_output_boundary():
    summary = "\n".join(
        f"- Sentence {index} contains several useful words."
        for index in range(8)
    )

    result = enforce_summary_guardrail(
        summary,
        max_words=25,
        max_bullets=5,
    )

    assert count_words(result) <= 25
    assert count_bullets(result) <= 5

