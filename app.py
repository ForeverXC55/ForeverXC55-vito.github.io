import jieba
import numpy as np
import pandas as pd
import altair as alt
from flask import Flask
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from matplotlib import pyplot as plt
from pyecharts.charts import WordCloud, Line, Pie, Bar, Scatter
from pyecharts import options as opts
import streamlit as st
from streamlit_echarts import st_pyecharts
from zhon import hanzi
import seaborn as sns

app = Flask(__name__)


def get_word_counts(url):
    """
    python爬虫
    该函数用于爬取网页中的词条以及词条数量
    :param url: 带爬取网页的url
    :return: 返回过滤后的词条以及数量封装到Count对象中
    """

    # 发送GET请求并获取响应
    response = requests.get(url)

    # 根据文本的内容来推测它的编码方式，防止中文乱码输出。
    response.encoding = response.apparent_encoding

    # 使用BeautifulSoup解析响应文本
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
        if len(filtered_word_counts) >= 15:
            break

    return filtered_word_counts


# 生成柱状图
def generate_bar_chart(data):
    """
       用pyecharts生成柱状图。
       参数:data (dict): 包含词频统计的字典。
       返回:无
       """
    bar = (
        Bar()
        .add_xaxis(list(data.keys()))
        .add_yaxis("词频", list(data.values()))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="柱状图-pyecharts"),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
        )

    )
    st_pyecharts(bar)


# 生成饼图
def generate_pie_chart(data):
    """
       用pyecharts生成饼图。
       参数:data (dict): 包含词频统计的字典。
       返回:无
       """
    pie = (
        Pie()
        .add("", list(data.items()))
        .set_colors(["#C1232B", "#27727B", "#FCCE10", "#E87C25", "#B5C334"])
        .set_global_opts(
            title_opts=opts.TitleOpts(title="饼图-pyecharts", pos_left="left"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="30%", pos_left="80%"),
            graphic_opts=[
                opts.GraphicGroup(
                    graphic_item=opts.GraphicItem(left="center", top="center", z=100),
                    children=[
                        opts.GraphicRect(
                            graphic_item=opts.GraphicItem(left="center", top="center"),
                            graphic_shape_opts=opts.GraphicShapeOpts(width=600, height=600),
                            graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(fill="#fff"),
                        )
                    ],
                )
            ],
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", font_size=10))
    )
    st_pyecharts(pie)


# 生成折线图
def generate_line_chart(data):
    """
       用pyecharts生成折线图。
       参数:data (dict): 包含词频统计的字典。
       返回:无
       """
    line = (
        Line()
        .add_xaxis(list(data.keys()))
        .add_yaxis("词频", list(data.values()))
        .set_global_opts(title_opts=opts.TitleOpts(title="折线图-pyecharts"))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
        )
    )
    st_pyecharts(line)


def generate_wordcloud(counts):
    """
    用pyecharts生成词云图。
    参数:counts (dict): 包含词频统计的字典。
    返回:无
    """

    # 提取词条和对应的词频
    words = list(counts.keys())
    word_counts = [(word, counts[word]) for word in words]

    # 创建 WordCloud 对象并进行配置
    wordcloud = (
        WordCloud()  # 实例化 WordCloud 对象
        .add("", word_counts, word_size_range=[20, 100])  # 添加词频数据到词云图中
        .set_global_opts(title_opts=opts.TitleOpts(title="词云图-pyecharts"))  # 设置词云图的标题
    )

    # 使用 st_pyecharts 函数渲染并显示词云图
    st_pyecharts(wordcloud)


def generate_scatter_chart(counts):
    """
        用pyecharts生成散点图。
        参数:counts (dict): 包含词频统计的字典。
        返回:无
        """
    scatter = (
        Scatter()
        .add_xaxis(xaxis_data=list(counts.keys()))
        .add_yaxis(series_name="", y_axis=list(counts.values()))
        .set_global_opts(title_opts=opts.TitleOpts(title="散点图"))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
        )
    )
    st_pyecharts(scatter)


def main():
    """
    主函数，用于生成网页词条数爬取的可视化结果。
    参数:无
    返回:无
    """
    st.title("网页词条数爬取")

    url = st.text_input("Enter a URL:")

    # 在侧边栏生成下拉框，用于选择图表类型
    result_type = st.sidebar.selectbox("请选择图表类型：", ["柱状图", "饼图", "折线图", "词云图", "散点图", "回归图", "直方图", "成对关系图", "数据表格"])

    # 在侧边栏生成下拉框，用于选择生成图表的框架
    frame_options = ["pyecharts + streamlit_echarts.st_pyecharts", "altair + st.altair_chart"]
    if result_type == "词云图" or result_type == "散点图":
        frame_options.remove("altair + st.altair_chart")
    elif result_type == "回归图" or result_type == "直方图" or result_type == "成对关系图":
        frame_options.remove("pyecharts + streamlit_echarts.st_pyecharts")
        frame_options.remove("altair + st.altair_chart")
        frame_options.append("seaborn")
    elif result_type == "数据表格":
        frame_options.remove("pyecharts + streamlit_echarts.st_pyecharts")
        frame_options.remove("altair + st.altair_chart")
        frame_options.append("streamlit")
    frame_type = st.sidebar.selectbox("请选择生成图表的框架：", frame_options)

    if st.button("提交") or url:
        try:
            word_count = get_word_counts(url)

            # 获取网页词条数的字典，并将其转换为两个列表
            words = list(word_count.keys())  # 词条列表
            counts = list(word_count.values())  # 词条对应的数量列表

            # 创建一个包含词条和数量的数据框，并选择数量最大的前15个词条
            df = pd.DataFrame({'word': words, 'count': counts})
            df = df.nlargest(15, 'count')

            if result_type == "柱状图" and frame_type == "altair + st.altair_chart":
                st.subheader("柱状图-altair")
                # 创建柱状图对象并设置编码（X轴为word，Y轴为count，tooltip显示word和count）
                chart = alt.Chart(df).mark_bar(orient='vertical').encode(
                    x=alt.X('word:N', axis=alt.Axis(labelAngle=45)),  # 设置X轴为离散值，标签倾斜45度
                    y='count:Q',  # 设置Y轴为数量
                    tooltip=['word', 'count']  # 鼠标悬停时显示的信息
                ).properties(
                    width=800,
                    height=600,
                    title="页面关键字数量"
                )
            elif result_type == "柱状图" and frame_type == "pyecharts + streamlit_echarts.st_pyecharts":
                generate_bar_chart(word_count)
                return None

            elif result_type == "饼图" and frame_type == "altair + st.altair_chart":
                st.subheader("饼图-altair")
                chart = alt.Chart(df).mark_arc().encode(
                    color=alt.Color('word:N', scale=alt.Scale(scheme='category20b')),
                    angle='count',
                    tooltip=['word', 'count']
                ).properties(
                    width=600,
                    height=600,
                    title="页面关键字分布"
                )
            elif result_type == "饼图" and frame_type == "pyecharts + streamlit_echarts.st_pyecharts":
                generate_pie_chart(word_count)
                return None

            elif result_type == "折线图" and frame_type == "altair + st.altair_chart":
                st.subheader("折线图-altair")
                chart = alt.Chart(df).mark_line().encode(
                    x='word:N',
                    y='count:Q',
                    tooltip=['word', 'count']
                ).properties(
                    width=800,
                    height=600,
                    title="页面关键字趋势"
                )
            elif result_type == "折线图" and frame_type == "pyecharts + streamlit_echarts.st_pyecharts":
                generate_line_chart(word_count)
                return None

            elif result_type == "词云图":

                st.subheader("词云图-pyecharts")
                generate_wordcloud(word_count)
                return None

            elif result_type == "散点图":

                st.subheader("散点图-pyecharts")
                generate_scatter_chart(word_count)
                return None

            elif result_type == "回归图":

                st.subheader("回归图-seaborn")

                # 将'word'列转换为单独的数值数组
                x_values = np.arange(len(df['word']))

                fig, ax = plt.subplots()  # 创建一个图形对象和一个坐标轴对象

                sns.regplot(x=x_values, y='count', data=df, ax=ax)  # 绘制回归图，x轴为词条索引，y轴为词条数量

                st.pyplot(fig)  # 在网页上显示图形

                return None

            elif result_type == "直方图":

                st.subheader("直方图-seaborn")

                # 绘制直方图
                fig, ax = plt.subplots()  # 创建图形对象
                sns.distplot(df['count'], ax=ax)
                st.pyplot(fig)
                return None

            elif result_type == "成对关系图":

                st.subheader("成对关系图-seaborn")

                # 绘制成对关系图
                fig = sns.pairplot(df)
                st.pyplot(fig.fig)
                return None

            elif result_type == "数据表格":

                st.subheader("数据表格-streamlit")
                # 在页面上添加一个滑动条，用于选择表格的宽度
                table_width = st.slider("选择表格宽度", min_value=200, max_value=1200, value=800, step=100)
                # 在页面上显示数据表格，设置表格的宽度为用户选择的宽度
                st.dataframe(df, width=table_width)
                return None

            # 关闭警告信息的显示
            st.set_option('deprecation.showPyplotGlobalUse', False)
            # 在页面上显示相应的图表
            st.altair_chart(chart)


        except requests.exceptions.RequestException as e:
            st.error(f"发生错误：{e}")


if __name__ == "__main__":
    main()
