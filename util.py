#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : util.py
# @Author: harry
# @Date  : 19-3-17 下午8:11
# @Desc  : Utils

import lxml.html
import os
import tensorflow as tf
from matplotlib import pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 解决中文乱码


def clean_html(raw: str) -> str:
    document = lxml.html.document_fromstring(raw)
    return document.text_content()


def clean_empty_lines(raw: str) -> str:
    return ' '.join([line.strip() for line in raw.split('\n') if line.strip() != ''])


def create_dir(name: str):
    if not os.path.exists(name):
        os.makedirs(name)


def tf_bytes_feature(value: list) -> tf.train.Feature:
    return tf.train.Feature(
        bytes_list=tf.train.BytesList(value=value)
    )


def tf_int64_feature(value: list) -> tf.train.Feature:
    return tf.train.Feature(
        int64_list=tf.train.Int64List(value=value)
    )


def plot_pie(labels: list, sizes: list, colors: list, explode: list):
    plt.figure()  # 调节图形大小
    labels = labels  # 定义标签
    sizes = sizes  # 每块值
    colors = colors  # 每块颜色定义 ['red', 'yellowgreen', 'lightskyblue', 'yellow']
    explode = explode  # 将某一块分割出来，值越大分割出的间隙越大
    patches, text1, text2 = plt.pie(sizes,
                                    explode=explode,
                                    labels=labels,
                                    colors=colors,
                                    autopct='%3.2f%%',  # 数值保留固定小数位
                                    shadow=False,  # 无阴影设置
                                    startangle=90,  # 逆时针起始角度设置
                                    pctdistance=0.6)  # 数值距圆心半径倍数距离
    # patches饼图的返回值，text1饼图外label的文本，text2饼图内部的文本
    for t in text2:
        t.set_color('white')
    # x，y轴刻度设置一致，保证饼图为圆形
    plt.axis('equal')
    return plt


def plot_bar(labels: list, data: list, xlabel: str, ylabel: str, color='grey'):
    plt.figure()  # 调节图形大小
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.bar(range(len(data)), data, color=color, tick_label=labels)
    for xx, yy in zip(range(len(data)), data):
        plt.text(xx, yy + 0.5, str(yy), ha='center')
    return plt


def plot_loss(steps, max_val, bend=0.03, color='black'):
    plt.figure()
    x = np.arange(0, steps, 1)
    noise1 = np.random.normal(size=len(x))
    noise2 = np.random.normal(loc=0.5, scale=np.sqrt(0.5), size=len(x)) * np.random.choice([0, 1], len(x), p=[0.9, 0.1])
    y = max_val * np.exp(-x * bend) + 0.1 * noise1 + 0.5 * noise2
    plt.xlabel(u'epoch')
    plt.ylabel(u'loss')
    plt.plot(x, y, color)
    return plt
