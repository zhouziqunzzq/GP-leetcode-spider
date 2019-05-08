#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : converter.py
# @Author: harry
# @Date  : 2019/3/29 下午4:27
# @Desc  : Converter to convert leetcode data to TFRecords

import tensorflow as tf
import json
import random

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
        # insert special tags
        self.tag2id["<PAD>"] = 0
        # normal id starts from 1
        tid = 1
        for t in sorted(self.tags):
            self.tag2id[t] = tid
            tid += 1
        return self.tag2id

    def create_word2id(self) -> dict:
        # init word set
        self.words.clear()
        for q in self.question_list:
            tokens = Converter.tokenize_raw_text(q['data']['question']['content'])
            for t in tokens:
                self.words.add(t.lower())

        self.word2id.clear()
        # insert special tokens
        self.word2id["<PAD>"] = 0
        self.word2id["<UNK>"] = 1

        # normal token id starts from 2
        wid = 2
        for w in sorted(self.words):
            self.word2id[w] = wid
            wid += 1
        return self.word2id

    @staticmethod
    def tokenize_raw_text(raw_text: str) -> list:
        tokenizer = Tokenizer(clean_empty_lines(clean_html(raw_text)))
        return tokenizer.tokenize()

    def tokenize_raw_text_to_id(self, raw_text: str, limit_length=None) -> list:
        # we assume that self.word2id is valid
        assert len(self.word2id) > 0
        assert limit_length is None or (isinstance(limit_length, int) and limit_length >= 0)
        rst = [self.word2id[t.lower()] for t in Converter.tokenize_raw_text(raw_text=raw_text)]
        if limit_length is None:
            return rst
        else:
            return rst[:limit_length]

    def write_metadata(self, dest: str,
                       question_list_filename="question_list.txt",
                       tag_list_filename="tag_list.txt",
                       word_list_filename="word_list.txt"):
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

    def convert(self, dest: str,
                record_filename="leetcode.tfrecord",
                question_list_filename="question_list.txt",
                tag_list_filename="tag_list.txt",
                word_list_filename="word_list.txt",
                limit_length=None,
                limit_question=None, ) -> list:
        self.write_metadata(dest=dest,
                            question_list_filename=question_list_filename,
                            tag_list_filename=tag_list_filename,
                            word_list_filename=word_list_filename)

        # convert to TFRecord
        example_list = []

        assert limit_question is None or (
                isinstance(limit_question, int) and 0 <= limit_question <= len(self.question_list))
        q_list = self.question_list
        if limit_question is not None:
            q_list = q_list[:limit_question]

        for q in q_list:
            topic_tags = q['data']['question']['topicTags']
            sim_qs = json.loads(q['data']['question']['similarQuestions'])
            sim_qs_id = []
            for sq in sim_qs:
                if sq['titleSlug'] in self.question2id:
                    sim_qs_id.append(self.question2id[sq['titleSlug']])

            example = tf.train.Example(
                features=tf.train.Features(feature={
                    'Text': tf_bytes_feature([
                        clean_empty_lines(clean_html(
                            q['data']['question']['content'])).encode('utf-8')]),
                    'Tokens': tf_int64_feature(
                        self.tokenize_raw_text_to_id(
                            q['data']['question']['content'], limit_length=limit_length)),
                    'Tags': tf_int64_feature([self.tag2id[t['slug']] for t in topic_tags]),
                    'Similar Questions': tf_int64_feature(sim_qs_id),
                })
            )
            example_list.append(example)

        # write out to disk
        with tf.python_io.TFRecordWriter(os.path.join(dest, record_filename)) as writer:
            for e in example_list:
                writer.write(e.SerializeToString())

        return example_list

    def convert_pairwise(self, dest: str,
                         num_negative_sample=5,
                         record_filename="leetcode_pairwise.tfrecord",
                         question_list_filename="question_list.txt",
                         tag_list_filename="tag_list.txt",
                         word_list_filename="word_list.txt",
                         limit_length=None,
                         limit_question=None) -> list:
        self.write_metadata(dest=dest,
                            question_list_filename=question_list_filename,
                            tag_list_filename=tag_list_filename,
                            word_list_filename=word_list_filename)

        # convert to TFRecord using pairwise method
        example_list = []
        question_set = set(self.question2id.keys())

        assert limit_question is None or (
                isinstance(limit_question, int) and 0 <= limit_question <= len(self.question_list))
        q_list = self.question_list
        if limit_question is not None:
            q_list = q_list[:limit_question]

        for q in q_list:
            # only use questions that have similar questions
            sim_qs = json.loads(q['data']['question']['similarQuestions'])
            if len(sim_qs) == 0:
                continue

            sim_q_set = set([sq['titleSlug'] for sq in sim_qs
                             if sq['titleSlug'] in self.question2id])
            dis_sim_q_set = question_set - sim_q_set
            topic_tags = q['data']['question']['topicTags']

            # create pairs
            for sim_q in sim_q_set:
                neg_sample_set = random.sample(dis_sim_q_set, num_negative_sample)
                dis_sim_q_set -= set(neg_sample_set)
                for dis_q in neg_sample_set:
                    sim_q_obj = self.question_list[self.question2id[sim_q]]
                    dis_q_obj = self.question_list[self.question2id[dis_q]]
                    sim_q_topic_tags = sim_q_obj['data']['question']['topicTags']
                    dis_q_topic_tags = dis_q_obj['data']['question']['topicTags']

                    # now create one pairwise example
                    example = tf.train.Example(
                        features=tf.train.Features(feature={
                            # pivot question
                            'Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        q['data']['question']['content'])).encode('utf-8')]),
                            'Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    q['data']['question']['content'], limit_length=limit_length)),
                            'Tags': tf_int64_feature([self.tag2id[t['slug']] for t in topic_tags]),
                            # similar question
                            'Similar Question Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        sim_q_obj['data']['question']['content'])).encode('utf-8')]),
                            'Similar Question Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    sim_q_obj['data']['question']['content'], limit_length=limit_length)),
                            'Similar Question Tags': tf_int64_feature(
                                [self.tag2id[t['slug']] for t in sim_q_topic_tags]),
                            # dissimilar question
                            'Dissimilar Question Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        dis_q_obj['data']['question']['content'])).encode('utf-8')]),
                            'Dissimilar Question Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    dis_q_obj['data']['question']['content'], limit_length=limit_length)),
                            'Dissimilar Question Tags': tf_int64_feature(
                                [self.tag2id[t['slug']] for t in dis_q_topic_tags]),
                        })
                    )
                    example_list.append(example)

        # write out to disk
        with tf.python_io.TFRecordWriter(os.path.join(dest, record_filename)) as writer:
            for e in example_list:
                writer.write(e.SerializeToString())

        return example_list

    def convert_pairwise_self_sim(self, dest: str,
                                  num_negative_sample=5,
                                  record_filename="leetcode_pairwise_self_sim.tfrecord",
                                  question_list_filename="question_list.txt",
                                  tag_list_filename="tag_list.txt",
                                  word_list_filename="word_list.txt",
                                  limit_length=None,
                                  limit_question=None) -> list:
        self.write_metadata(dest=dest,
                            question_list_filename=question_list_filename,
                            tag_list_filename=tag_list_filename,
                            word_list_filename=word_list_filename)

        # convert to TFRecord using pairwise method with self-sim only
        example_list = []
        question_set = set(self.question2id.keys())

        assert limit_question is None or (
                isinstance(limit_question, int) and 0 <= limit_question <= len(self.question_list))
        q_list = self.question_list
        if limit_question is not None:
            q_list = q_list[:limit_question]

        for q in q_list:
            # similar question is the same as itself
            sim_q_set = set()
            sim_q_set.add(q['data']['question']['titleSlug'])

            sim_qs = json.loads(q['data']['question']['similarQuestions'])
            real_sim_q_set = set([sq['titleSlug'] for sq in sim_qs
                                  if sq['titleSlug'] in self.question2id])

            dis_sim_q_set = question_set - sim_q_set - real_sim_q_set
            topic_tags = q['data']['question']['topicTags']

            # create pairs
            for sim_q in sim_q_set:
                neg_sample_set = random.sample(dis_sim_q_set, num_negative_sample)
                dis_sim_q_set -= set(neg_sample_set)
                for dis_q in neg_sample_set:
                    sim_q_obj = self.question_list[self.question2id[sim_q]]
                    dis_q_obj = self.question_list[self.question2id[dis_q]]
                    sim_q_topic_tags = sim_q_obj['data']['question']['topicTags']
                    dis_q_topic_tags = dis_q_obj['data']['question']['topicTags']

                    # now create one pairwise example
                    example = tf.train.Example(
                        features=tf.train.Features(feature={
                            # pivot question
                            'Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        q['data']['question']['content'])).encode('utf-8')]),
                            'Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    q['data']['question']['content'], limit_length=limit_length)),
                            'Tags': tf_int64_feature([self.tag2id[t['slug']] for t in topic_tags]),
                            # similar question
                            'Similar Question Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        sim_q_obj['data']['question']['content'])).encode('utf-8')]),
                            'Similar Question Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    sim_q_obj['data']['question']['content'], limit_length=limit_length)),
                            'Similar Question Tags': tf_int64_feature(
                                [self.tag2id[t['slug']] for t in sim_q_topic_tags]),
                            # dissimilar question
                            'Dissimilar Question Text': tf_bytes_feature([
                                clean_empty_lines(
                                    clean_html(
                                        dis_q_obj['data']['question']['content'])).encode('utf-8')]),
                            'Dissimilar Question Tokens': tf_int64_feature(
                                self.tokenize_raw_text_to_id(
                                    dis_q_obj['data']['question']['content'], limit_length=limit_length)),
                            'Dissimilar Question Tags': tf_int64_feature(
                                [self.tag2id[t['slug']] for t in dis_q_topic_tags]),
                        })
                    )
                    example_list.append(example)

        # write out to disk
        with tf.python_io.TFRecordWriter(os.path.join(dest, record_filename)) as writer:
            for e in example_list:
                writer.write(e.SerializeToString())

        return example_list

    def convert_pairwise_txt(self, dest: str,
                             num_negative_sample=5,
                             text_filename="leetcode_pairwise.txt",
                             relation_filename="leetcode_pairwise_relation.txt",
                             question_list_filename="question_list.txt",
                             tag_list_filename="tag_list.txt",
                             word_list_filename="word_list.txt",
                             limit_length=None,
                             limit_question=None):
        self.write_metadata(dest=dest,
                            question_list_filename=question_list_filename,
                            tag_list_filename=tag_list_filename,
                            word_list_filename=word_list_filename)

        # convert to text and relation txt files using pairwise method
        text_file = open(os.path.join(dest, text_filename), 'w')
        relation_file = open(os.path.join(dest, relation_filename), 'w')
        question_set = set(self.question2id.keys())

        assert limit_question is None or (
                isinstance(limit_question, int) and 0 <= limit_question <= len(self.question_list))
        q_list = self.question_list
        if limit_question is not None:
            q_list = q_list[:limit_question]

        # write out question text
        for q in q_list:
            q_txt = clean_empty_lines(clean_html(q['data']['question']['content']))
            if limit_length is not None and len(q_txt) > limit_length:
                q_txt = q_txt[:limit_length]
            text_file.write(q_txt + '\n')

        # write out relations
        for q in q_list:
            # only use questions that have similar questions
            sim_qs = json.loads(q['data']['question']['similarQuestions'])
            if len(sim_qs) == 0:
                continue

            sim_q_set = set([sq['titleSlug'] for sq in sim_qs
                             if sq['titleSlug'] in self.question2id])
            dis_sim_q_set = question_set - sim_q_set

            # create pairs
            for sim_q in sim_q_set:
                neg_sample_set = random.sample(dis_sim_q_set, num_negative_sample)
                dis_sim_q_set -= set(neg_sample_set)
                for dis_q in neg_sample_set:
                    q_id = self.question2id[q['data']['question']['titleSlug']]
                    sim_q_id = self.question2id[sim_q]
                    dis_q_id = self.question2id[dis_q]
                    relation_file.write("{} {} {}\n".format(q_id, sim_q_id, dis_q_id))

        text_file.close()
        relation_file.close()

        return
