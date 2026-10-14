import json
from unittest.mock import patch

import pytest

import research


def test_incremental_summary_keeps_global_citations_across_rounds():
    pages = [
        {"title": "网页甲", "url": "https://example.com/a", "body": "第一轮设备手册中的可靠原文证据足够长。"},
        {"title": "网页乙", "url": "https://example.com/b", "body": "第二轮维修手册中的不同原文证据足够长。"},
    ]

    def collect(_question, _queries, sources, _seen, **_kwargs):
        sources.append(pages[len(sources)])

    def ask(prompt):
        index = 1 if "网页乙" in prompt else 0
        source_id = index + 1
        assert f"[{source_id}] 标题：{pages[index]['title']}" in prompt
        assert f'"source_id":{source_id},' in prompt
        return json.dumps({"claims": [{"claim": f"结论{source_id}", "source_id": source_id, "evidence": pages[index]["body"]}]})

    with patch.object(research, "plan_queries", return_value=["q"]), patch.object(
        research, "collect", side_effect=collect
    ), patch.object(research, "ask", side_effect=ask), patch.object(
        research, "reflect", side_effect=[(False, ["q2"]), (True, [])]
    ):
        notes, sources = research.research("问题", max_rounds=2, log=lambda _: None)

    assert "- 结论：结论1 [1]" in notes
    assert "- 结论：结论2 [2]" in notes
    assert len(sources) == 2


def test_same_claim_from_another_source_keeps_both_evidence_blocks():
    seen = set()
    notes, _ = research._append_claims("", "- 结论：设备需要检修 [1]\n  证据原文：来源甲", seen)
    notes, added = research._append_claims(notes, "- 结论：设备需要检修 [2]\n  证据原文：来源乙", seen)
    assert added
    assert "[1]" in notes and "[2]" in notes
    repeated, added = research._append_claims(notes, "- 结论：设备需要检修 [2]\n  证据原文：来源乙", seen)
    assert not added and repeated == notes


@pytest.mark.parametrize("payload", [{"claims": None}, {"claims": "bad"}, {"claims": [None, "bad", {}]}])
def test_malformed_claim_structure_degrades_without_crashing(payload):
    with patch.object(research, "ask", return_value=json.dumps(payload)):
        result = research.summarize("问题", [{"title": "手册", "body": "足够长的设备维护原文证据文本内容。"}])
    assert result.startswith("材料不足")


def test_json_retry_contains_previous_output_and_error():
    with patch.object(research, "ask", side_effect=['{"claims": broken}', '{"claims": []}']) as ask:
        data, status = research._ask_json("prompt", "{")
    assert status == "ok" and data == {"claims": []}
    retry_prompt = ask.call_args_list[1].args[0]
    assert '{"claims": broken}' in retry_prompt
    assert "解析错误" in retry_prompt


def test_missing_json_is_retried_before_degrading():
    with patch.object(research, "ask", side_effect=["只有解释文字", '["新搜索词"]']) as ask:
        assert research.plan_queries("问题") == ["新搜索词"]
    assert ask.call_count == 2


def test_planning_and_reflection_handle_model_request_failure():
    with patch.object(research, "ask", side_effect=RuntimeError("service unavailable")):
        assert research.plan_queries("问题") == ["问题"]
        assert research.reflect("问题", "结论") == (False, ["问题"])


def test_summary_rejects_citation_outside_its_global_source_range():
    page = {"title": "第二轮手册", "body": "这是第二轮手册中长度足够的连续证据。"}
    payload = {"claims": [{"claim": "检修", "source_id": 1, "evidence": page["body"]}]}
    with patch.object(research, "ask", return_value=json.dumps(payload)):
        assert research.summarize("问题", [page], source_offset=4).startswith("材料不足")
