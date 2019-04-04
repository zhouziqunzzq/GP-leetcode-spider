#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : converter.py
# @Author: harry
# @Date  : 2019/3/29 下午4:27
# @Desc  : Converter to convert leetcode data to TFRecords

import tensorflow as tf
import json

from util import *
from tokenizer import Tokenizer


class Converter(object):
    def __init__(self, question_list: list):
        self.question_list = question_list.copy()
        self.question_list.reverse()
        self.question2id = dict()
        self.tags = set()
        self.tag2id = dict()
        self.words = set()
        self.word2id = dict()

    def add_question(self, question: object):
        self.question_list.append(question)

    def create_question2id(self) -> dict:
        self.question2id.clear()
        # id starts from 0
        qid = 0
        for q in self.question_list:
            self.question2id[q['data']['question']['titleSlug']] = qid
            qid += 1
        return self.question2id

    def create_tag2id(self) -> dict:
        # init tag set
        self.tags.clear()
        for q in self.question_list:
            for t in q['data']['question']['topicTags']:
                self.tags.add(t['slug'])

        self.tag2id.clear()
        # id starts from 0
        tid = 0
        for t in sorted(self.tags):
            self.tag2id[t] = tid
            tid += 1
        return self.tag2id

    def create_word2id(self) -> dict:
        # init word set
        self.words.clear()
        for q in self.question_list:
            cleaned_content = clean_empty_lines(clean_html(q['data']['question']['content']))
            # tokens = word_tokenize(cleaned_content)
            tokenizer = Tokenizer(cleaned_content)
            tokens = tokenizer.tokenize()
            for t in tokens:
                self.words.add(t.lower())

        self.word2id.clear()
        # id starts from 0
        wid = 0
        for w in sorted(self.words):
            self.word2id[w] = wid
            wid += 1
        return self.word2id

    def convert(self, dest: str,
                record_filename="leetcode.tfrecord",
                question_list_filename="question_list.txt",
                tag_list_filename="tag_list.txt",
                word_list_filename="word_list.txt") -> list:
        # create question list on need
        if len(self.question2id) == 0:
            self.create_question2id()
        with open(os.path.join(dest, question_list_filename), "w") as f:
            f.writelines([q + "\n" for q in self.question2id.keys()])

        # create tag list on need
        if len(self.tag2id) == 0:
            self.create_tag2id()
        with open(os.path.join(dest, tag_list_filename), "w") as f:
            f.writelines([t + "\n" for t in self.tag2id.keys()])

        # create word list on need
        if len(self.word2id) == 0:
            self.create_word2id()
        with open(os.path.join(dest, word_list_filename), "w") as f:
            f.writelines([w + "\n" for w in self.word2id.keys()])

        # convert to TFRecord
        example_list = []
        for q in self.question_list:
            topic_tags = q['data']['question']['topicTags']
            sim_qs = json.loads(q['data']['question']['similarQuestions'])
            sim_qs_id = []
            for sq in sim_qs:
                if sq['titleSlug'] in self.question2id:
                    sim_qs_id.append(self.question2id[sq['titleSlug']])

            example = tf.train.Example(
                features=tf.train.Features(feature={
                    'Text': tf.train.Feature(
                        bytes_list=tf.train.BytesList(
                            value=[clean_empty_lines(clean_html(
                                q['data']['question']['content']
                            )).encode('utf-8')]
                        )
                    ),
                    'Tags': tf.train.Feature(
                        int64_list=tf.train.Int64List(
                            value=[self.tag2id[t['slug']] for t in topic_tags]
                        )
                    ),
                    'Similar Questions': tf.train.Feature(
                        int64_list=tf.train.Int64List(
                            value=sim_qs_id
                        )
                    )
                })
            )
            example_list.append(example)

        # write out to disk
        with tf.python_io.TFRecordWriter(os.path.join(dest, record_filename)) as writer:
            for e in example_list:
                writer.write(e.SerializeToString())

        return example_list
