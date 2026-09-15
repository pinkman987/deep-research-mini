from research import validate_citations


def test_out_of_range_citation_flagged():
    issues = validate_citations("- 负载过大导致报警 [5]", 3)
    assert any("无效引用编号" in issue for issue in issues)


def test_bullet_without_citation_flagged():
    report = "- 这是一条没有任何引用编号的很长结论行用来测试校验器"
    issues = validate_citations(report, 3)
    assert any("无引用结论" in issue for issue in issues)


def test_clean_report_no_issues():
    report = (
        "- 负载过重是常见原因 [1]\n"
        "- 参数设置不当也会触发 [2]\n"
        "## 参考文献\n"
        "1. 来源甲  http://a\n"
        "2. 来源乙  http://b\n"
    )
    assert validate_citations(report, 2) == []
