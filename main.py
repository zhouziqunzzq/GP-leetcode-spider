#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : main.py
# @Author: harry
# @Date  : 19-3-17 下午7:41
# @Desc  : Main cli

import time
import os
import argparse
import json

from spider import Spider
from converter import Converter
from util import *

RESULT_DIR = "result"
TF_RECORD_DIR = "tf_data"


def fetch_data():
    # create dir for data storage
    cur_path = os.path.dirname(os.path.abspath(__file__))
    create_dir(os.path.join(cur_path, RESULT_DIR))

    spider = Spider()

    # fetch question list and save to a file
    question_list = spider.get_question_list()
    question_list_f = open(os.path.join(cur_path, "question_list.json"), 'w')
    question_list_f.write(question_list.text)
    question_list_f.close()

    question_list = question_list.json()
    # print(question_list)
    # print(len(question_list['stat_status_pairs']))

    # fetch all question data
    question_list = question_list['stat_status_pairs']
    result_path = os.path.join(cur_path, RESULT_DIR)
    cnt = 0
    tot = len(question_list)
    for q in question_list:
        cnt += 1
        print('progress {}/{}'.format(str(cnt), str(tot)))

        slug = q['stat']['question__title_slug']
        print('fetching {} ...'.format(slug))

        d = spider.get_question_data(slug)
        qf = open(os.path.join(result_path, str(q['stat']['question_id']) + '.json'), 'w')
        qf.write(d.text)
        qf.close()

        # d = d.json()
        # content = d['data']['question']['content']
        # print(clean_empty_lines(clean_html(content)))

        time.sleep(0.5)


def convert_data():
    # create dir
    cur_path = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(cur_path, RESULT_DIR)
    tf_data_path = os.path.join(cur_path, TF_RECORD_DIR)
    create_dir(tf_data_path)

    # read in result
    print("loading result files from disk")
    result_files = [f for f in os.listdir(result_path)
                    if os.path.isfile(os.path.join(result_path, f))]
    print("{} files detected".format(len(result_files)))
    result_list = []
    for f in result_files:
        ff = open(os.path.join(result_path, f), 'r')
        result_list.append(ff.read())
        ff.close()
    print("result files loaded successfully")
    # print(result_list[0])

    # parse result files
    print("parsing result files (json format)")
    question_list = [json.loads(s) for s in result_list]

    # we use free questions only
    valid_question_list = [q for q in question_list if not q['data']['question']['isPaidOnly']]
    print("number of valid questions is {}".format(len(valid_question_list)))

    # convert to TFRecords and save to files
    converter = Converter(question_list=valid_question_list)
    example_list = converter.convert(dest=TF_RECORD_DIR)
    print(example_list[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        help="Set action for the spider. Supported actions: fetch_data, convert_data",
        type=str,
    )
    args = parser.parse_args()

    action_dict = {
        'fetch_data': fetch_data,
        'convert_data': convert_data,
    }

    if args.action in action_dict:
        action_dict[args.action]()
    else:
        print("Invalid action \"{}\" specified".format(args.action))


if __name__ == "__main__":
    main()
