from research import mark_fetched_page, mark_raw_url, new_seen_state, title_key, url_key


def test_whitespace_normalized():
    assert title_key("伺服 电机 概述") == title_key("伺服电机概述")


def test_seen_set_catches_variant_spacing():
    seen = {title_key("安川 伺服 维修实例")}
    assert title_key("安川伺服维修实例") in seen


def test_different_titles_not_collided():
    assert title_key("伺服电机概述") != title_key("步进电机概述")


def test_url_key_ignores_fragment_tracking_and_default_port():
    first = "https://Example.com:443/article/?id=7&utm_source=test#section"
    second = "https://example.com/article?id=7"
    assert url_key(first) == url_key(second)


def test_raw_url_layer_catches_normalized_duplicate():
    seen = new_seen_state()
    assert mark_raw_url("https://example.com/a?utm_source=x", seen) is False
    assert mark_raw_url("https://example.com/a", seen) is True


def test_final_url_layer_catches_two_redirects_to_same_page():
    seen = new_seen_state()
    first = {"url": "https://search.test/redirect/1", "title": "文章一"}
    second = {"url": "https://search.test/redirect/2", "title": "文章二"}

    assert mark_fetched_page(first, "https://site.test/page", seen) == ""
    assert mark_fetched_page(second, "https://site.test/page#top", seen) == "最终URL"


def test_title_layer_catches_spacing_and_case_variant():
    seen = new_seen_state()
    first = {"url": "https://site.test/a", "title": "Servo E-05 排查"}
    second = {"url": "https://site.test/b", "title": " servo  E-05排查 "}

    assert mark_fetched_page(first, first["url"], seen) == ""
    assert mark_fetched_page(second, second["url"], seen) == "标题"
