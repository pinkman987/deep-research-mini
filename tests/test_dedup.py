from research import title_key


def test_whitespace_normalized():
    assert title_key("伺服 电机 概述") == title_key("伺服电机概述")


def test_seen_set_catches_variant_spacing():
    seen = {title_key("安川 伺服 维修实例")}
    assert title_key("安川伺服维修实例") in seen


def test_different_titles_not_collided():
    assert title_key("伺服电机概述") != title_key("步进电机概述")
