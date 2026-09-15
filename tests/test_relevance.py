from research import relevant


def test_all_stop_words_question_passes():
    # 问题全是疑问词时不做过滤，宁可放过（避免除零和全灭）
    assert relevant("随便什么正文都行", "谁什么吗？") is True


def test_relevant_body_passes():
    assert relevant("挂谷猜想是调和分析中的未解决问题", "挂谷猜想") is True


def test_irrelevant_body_rejected():
    # 汽车配件页面对数学问题：实词覆盖率为 0
    assert relevant("菲尔,奔驰,宝马,汽车配件", "挂谷猜想") is False


def test_partial_coverage_below_ratio_rejected():
    # 10 个实词只命中 1 个，低于 0.3 阈值
    assert relevant("伺服", "伺服电机过载报警的原因有哪些") is False


def test_synonym_variant_passes():
    # 同义变体：问题写"日企"，正文写"日资企业"，修复前会被误杀
    body = "各省市日资企业数量排名，上海辽宁山东江苏的日资企业最多"
    assert relevant(body, "中国各省日企数量") is True


def test_unrelated_still_rejected_with_bigrams():
    # 汽车配件页面对数学问题：单字和二元组都几乎不重合
    assert relevant("菲尔,奔驰,宝马,汽车配件", "挂谷猜想") is False
