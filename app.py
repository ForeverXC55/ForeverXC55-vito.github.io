from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from pyecharts.charts import Bar, Pie, Line
from pyecharts import options as opts

app = Flask(__name__)


def get_word_counts(url):
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    # 处理网页内容，获取词条数量
    text = soup.get_text()  # 获取网页文本内容

    # 使用正则表达式或其他方法对文本进行处理，例如去除特殊字符、分词等
    # 以下示例使用正则表达式提取单词
    words = re.findall(r'\b\w+\b', text)  # 提取单词

    # 使用Counter类进行词频统计
    word_counts = Counter(words)

    # 筛选出最有意义的词条
    filtered_word_counts = Counter()
    for word, count in word_counts.most_common():
        # 根据自己的需求进行筛选
        if 2 <= len(word) <= 5 and count >= 1:  # 词条长度大于等于 2 且词频大于等于 1
            filtered_word_counts[word] = count
        if len(filtered_word_counts) >= 20:
            break

    return filtered_word_counts


def process_word_counts(word_counts):
    # 对词条数量进行处理，转为Pyecharts所需的数据格式
    sorted_word_counts = word_counts.most_common()  # 按词频降序排序

    # 提取词条和对应的数量
    x_data = [word for word, count in sorted_word_counts]
    y_data = [count for word, count in sorted_word_counts]

    return x_data, y_data


def generate_bar_chart(x_data, y_data):
    # 生成柱状图
    bar = (
        Bar()
        .add_xaxis(x_data)
        .add_yaxis("Word Count", y_data)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Word Count Bar Chart"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
        )
    )

    return bar.render_embed()  # 返回图表的HTML代码片段


def generate_pie_chart(x_data, y_data):
    # 生成饼状图
    pie = (
        Pie()
        .add("", [list(z) for z in zip(x_data, y_data)])
        .set_global_opts(title_opts=opts.TitleOpts(title="Word Count Pie Chart"))
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{b}: {c}", font_size=10, position="inside")
        )
        .set_colors(["#C1232B", "#27727B", "#FCCE10", "#E87C25", "#B5C334"])
        .set_global_opts(legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c}", font_size=10))
        .set_global_opts(legend_opts=opts.LegendOpts(type_="scroll", pos_top="20%", pos_left="80%"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Word Count Pie Chart", pos_left="center"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="30%", pos_left="80%"),
        )
    )

    return pie.render_embed()  # 返回图表的HTML代码片段


def generate_line_chart(x_data, y_data):
    # 生成折线图
    line = (
        Line()
        .add_xaxis(x_data)
        .add_yaxis("Word Count", y_data)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Word Count Line Chart"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
        )
    )

    return line.render_embed()  # 返回图表的HTML代码片段


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        word_counts = get_word_counts(url)
        x_data, y_data = process_word_counts(word_counts)
        bar_chart_html = generate_bar_chart(x_data, y_data)
        pie_chart_html = generate_pie_chart(x_data, y_data)
        line_chart_html = generate_line_chart(x_data, y_data)
        return render_template('index.html', chart_html=[bar_chart_html, pie_chart_html, line_chart_html])
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
