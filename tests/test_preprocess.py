from ml.preprocess import clean_text, validate_input


def test_clean_text_strips_urls_and_ips():
    raw = "Visit http://example.com you fool 8.8.8.8"
    cleaned = clean_text(raw)
    assert "http" not in cleaned
    assert "8.8.8.8" not in cleaned
    assert "you fool" in cleaned


def test_validate_input_rejects_empty():
    try:
        validate_input("   ")
        assert False, "expected ValueError"
    except ValueError:
        pass
