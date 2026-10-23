# 药物临床研究证据助手

一个用 Python、LLM 和 Streamlit 做的临床研究证据问答项目。

我有生物统计和临床研究背景，所以想从熟悉的问题出发：研究纳入了哪些患者？主要终点是什么？治疗计划持续多久？回答的依据在哪里？

这个项目围绕 ribociclib 的 NATALEE 试验，让用户在提问后，既能看到回答，也能展开查看引用的原文。

[English](README.md) · [项目报告](docs/project_report.md)

## 能做什么

- 自由输入英文问题，搜索全部资料或指定文档。
- 根据检索片段生成回答，并标注段落引用。
- 展开原文，核对回答是否有依据。
- 检索证据不足时明确说明。
- 保存问答和检索记录，方便回头检查。

目前收录四份公开资料，涉及同一项 NATALEE 研究，包括 FDA 公告、研究设计、四年随访和生活质量报告。只收录选定正文，不包含图、表和补充材料。

## 实现过程

**整理文档 → 检索段落 → LLM 生成回答 → 展示原文依据**

每个段落都保留文档、研究、章节和段落编号。当前页面使用关键词检索，把最多三个片段交给模型回答。

开发时，我比较过关键词、Embedding 语义检索、RRF 混合检索和 IDF 加权检索。在这些小规模评估中，更复杂的方法没有稳定胜出，所以目前保留了简单的关键词方案。

我也用八道问题做了问答回归检查，借助 AI 对照原文审核，审核结果仍待本人确认。已知的检索失败也保留在记录中。这些检查不能代表系统的整体准确率。

具体实验结果、失败案例和设计取舍放在[项目报告](docs/project_report.md)中。

## 如何运行

开发环境：macOS、Python 3.10.9。

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

创建 `.env` 文件，填入 API key：

```text
OPENAI_API_KEY=your_api_key_here
```

不要把 `.env` 提交到 Git。回答模型配置在 `scripts/ask_evidence.py` 中，需要相应的模型访问权限，API 调用会产生费用。

启动页面：

```bash
python -m streamlit run app.py --server.address 127.0.0.1
```

当前问答流程直接读取处理好的段落和元数据，不需要先生成 embedding。全新环境安装还没有验证。

## 可以试试

在页面中选择相关文档，然后输入：

- Was the NATALEE trial blinded?
- How long was ribociclib treatment planned to last?
- What was the median age of participants?
- What was the prespecified primary HRQOL endpoint?

这些只是示例，用户可以自由提问。目前主要按英文问题开发和评估。

## 使用边界

这是一个学习和求职展示原型，不用于临床决策，不支持联网搜索、治疗推荐或药物疗效排名。

它可能漏掉已有证据，生成的回答和引用也需要核对。“检索片段不足”不代表原始论文没有答案。

评估问题数量有限，部分在开发时已经使用过。目前没有开展真实用户测试，也没有验证实际节省时间的效果。