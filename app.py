import streamlit as st
from research import research, write_report, knowledge_fallback

st.set_page_config(page_title="DeepResearch-mini", page_icon="🔍", layout="wide")
st.title("🔍 DeepResearch-mini · 自主搜索型研究 Agent")
st.caption("输入研究问题，Agent 自动多轮搜索-阅读-反思，生成带引用的 Markdown 研究报告")

question = st.text_input("研究问题", placeholder="例如：伺服电机过载报警的原因有哪些？")

if st.button("开始研究", type="primary", disabled=not question.strip()):
    log_box = st.empty()          # 占位块：不断刷新显示进度日志
    log_lines = []

    def log(msg):
        log_lines.append(str(msg))
        log_box.code("\n".join(log_lines[-15:]), language=None)

    with st.spinner("多轮检索与总结中，约 1-3 分钟…"):
        notes, sources = research(question, log=log)
    log_box.container().empty()    # 先关进度区，spinner 随 with 结束自动消失

    if not sources:
        st.warning(notes + " 以下为模型基于自身知识的回答，未经联网核实。")
        st.markdown(knowledge_fallback(question))
    else:
        report = write_report(question, notes, sources)
        st.success(f"研究完成，共引用 {len(sources)} 篇来源")
        st.markdown(report)
        st.download_button("下载报告 report.md", report.encode("utf-8"),
                           file_name="report.md", mime="text/markdown")