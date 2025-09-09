from app.slack_parser import parse_slack_payload


def test_parse_text_and_blocks():
    payload = {
        "text": "Base text",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Header"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Section body"}},
            {"type": "divider"},
            {"type": "context", "elements": [
                {"type": "plain_text", "text": "ctx"},
            ]},
        ],
    }
    parsed = parse_slack_payload(payload)
    assert "Base text" in parsed.text
    assert "Header" in parsed.text
    assert "Section body" in parsed.text
    assert "ctx" in parsed.text


def test_parse_attachments_media():
    payload = {
        "attachments": [
            {"image_url": "https://example.com/a.png", "title": "A"},
            {"thumb_url": "https://example.com/b.jpg", "fallback": "B"},
            {"file_url": "https://example.com/file.pdf", "title": "Doc"},
        ]
    }
    parsed = parse_slack_payload(payload)
    assert len(parsed.images) == 2
    assert len(parsed.documents) == 1


