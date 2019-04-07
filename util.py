#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : util.py
# @Author: harry
# @Date  : 19-3-17 下午8:11
# @Desc  : Utils

import lxml.html
import os
import tensorflow as tf


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
