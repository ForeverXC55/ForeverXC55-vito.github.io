import jieba
import numpy as np
import pandas as pd
import altair as alt
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

from matplotlib import pyplot as plt
from nltk import PorterStemmer
from nltk.corpus import stopwords
from pyecharts.charts import Bar, Pie, Line, WordCloud
from pyecharts import options as opts
import streamlit as st
from streamlit_echarts import st_pyecharts
from zhon import hanzi
import seaborn as sns

app = Flask(__name__)


def get_word_counts(url):
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')

    # 处理网页内容，获取文本
    text = soup.get_text()

    # 去除数字和特殊字符
    text = re.sub(r'[{}]'.format(hanzi.punctuation), '', text)

    # 使用jieba分词
    words = jieba.cut(text)

    # 使用Counter类进行词频统计
    word_counts = Counter(words)

    # 停用词列表
    stop_words = ['的', '了', '和', '是', '在', '我', '你', '他', '她']  # 根据需求添加更多停用词

    # 筛选出最有意义的词条，并排除停用词
    filtered_word_counts = Counter()
    for word, count in word_counts.most_common():
        # 根据自己的需求进行筛选
        if 2 <= len(word) <= 5 and count >= 1 and word not in stop_words:  # 词条长度在2到5之间，词频大于等于1，并且不在停用词列表中
            filtered_word_counts[word] = count
        if len(filtered_word_counts) >= 20:
            break

    return filtered_word_counts


def generate_wordcloud(counts):
    # 生成词云
    words = list(counts.keys())
    word_counts = [(word, counts[word]) for word in words]

    wordcloud = (
        WordCloud()
        .add("", word_counts, word_size_range=[20, 100])
        .set_global_opts(title_opts=opts.TitleOpts(title="词云图"))
    )

    st_pyecharts(wordcloud)


def main():
    st.title("网页词条数爬取")

    url = st.text_input("Enter a URL:")
    if st.button("提交") or url:
        try:
            word_count = get_word_counts(url)

            words = list(word_count.keys())
            counts = list(word_count.values())

            df = pd.DataFrame({'word': words, 'count': counts})
            df = df.nlargest(15, 'count')

            # 选择要显示的结果
            result_type = st.selectbox("选择显示类型", ["柱状图", "饼图", "折线图", "词云图", "回归图", "直方图", "成对关系图", "数据表格"])  # 添加瀑布图选项

            if result_type == "柱状图":
                st.subheader("柱状图")
                chart = alt.Chart(df).mark_bar(orient='vertical').encode(
                    x=alt.X('word:N', axis=alt.Axis(labelAngle=45)),
                    y='count:Q',
                    tooltip=['word', 'count']
                ).properties(
                    width=800,
                    height=600,
                    title="页面关键字数量"
                )

            elif result_type == "饼图":
                st.subheader("饼图")
                chart = alt.Chart(df).mark_arc().encode(
                    color=alt.Color('word:N', scale=alt.Scale(scheme='category20b')),
                    angle='count',
                    tooltip=['word', 'count']
                ).properties(
                    width=800,
                    height=600,
                    title="页面关键字分布"
                )

            elif result_type == "折线图":
                st.subheader("折线图")
                chart = alt.Chart(df).mark_line().encode(
                    x='word:N',
                    y='count:Q',
                    tooltip=['word', 'count']
                ).properties(
                    width=800,
                    height=600,
                    title="页面关键字趋势"
                )
                # 显示动态线图
                # st.altair_chart(chart, use_container_width=True)


            elif result_type == "词云图":
                st.subheader("词云图")
                generate_wordcloud(word_count)
                return None


            elif result_type == "回归图":
                st.subheader("回归图")

                # 将'word'列转换为单独的数值数组
                x_values = np.arange(len(df['word']))
                fig, ax = plt.subplots()
                sns.regplot(x=x_values, y='count', data=df, ax=ax)  # 将图形对象ax传递给sns.regplot()
                st.pyplot(fig)
                return None

            elif result_type == "直方图":
                st.subheader("直方图")

                # 绘制直方图
                fig, ax = plt.subplots()  # 创建图形对象
                sns.distplot(df['count'], ax=ax)
                st.pyplot(fig)
                return None

            elif result_type == "成对关系图":
                st.subheader("成对关系图")

                # 绘制成对关系图
                fig = sns.pairplot(df)
                st.pyplot(fig.fig)
                return None
            elif result_type == "数据表格":
                st.subheader("数据表格")
                table_width = st.slider("选择表格宽度", min_value=200, max_value=1200, value=800, step=100)
                st.dataframe(df, width=table_width)
                return None

            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.altair_chart(chart)


        except requests.exceptions.RequestException as e:
            st.error(f"发生错误：{e}")


if __name__ == "__main__":
    main()
