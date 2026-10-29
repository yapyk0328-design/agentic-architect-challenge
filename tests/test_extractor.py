from web_summarizer.extractor import extract_main_content, is_sufficient_content


def test_extracts_article_and_removes_common_boilerplate():
    article = " ".join(f"useful-word-{index}" for index in range(100))
    html = f"""
    <html>
      <body>
        <nav>Navigation should not appear</nav>
        <article><h1>Useful title</h1><p>{article}</p></article>
        <footer>Footer should not appear</footer>
      </body>
    </html>
    """

    text = extract_main_content(html, url="https://example.com/article")

    assert "Useful title" in text
    assert "useful-word-50" in text
    assert "Navigation should not appear" not in text
    assert "Footer should not appear" not in text
    assert is_sufficient_content(text)


def test_short_content_is_not_sufficient():
    assert not is_sufficient_content("A very short page.")

