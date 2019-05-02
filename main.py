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

SPIDER_SLEEP_PERIOD = 0.5
RESULT_DIR = "result"
TF_RECORD_DIR = "tf_data"


def fetch_data(args):
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

        time.sleep(SPIDER_SLEEP_PERIOD)


def convert_data(args):
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

    # parse result files
    print("parsing result files (json format)")
    question_list = [json.loads(s) for s in result_list]

    # we use free questions only
    valid_question_list = [q for q in question_list if not q['data']['question']['isPaidOnly']]
    print("number of valid questions is {}".format(len(valid_question_list)))

    # convert to TFRecords and save to files
    converter = Converter(question_list=valid_question_list)
    if args.method == "normal":
        example_list = converter.convert(
            dest=TF_RECORD_DIR,
            limit_length=args.limit_length,
            limit_question=args.limit_question,
        )
        print(example_list[0])
    elif args.method == "pairwise":
        example_list = converter.convert_pairwise(
            dest=TF_RECORD_DIR,
            limit_length=args.limit_length,
            limit_question=args.limit_question,
        )
        print(example_list[0])
        print('Total: {}'.format(len(example_list)))
    elif args.method == "pairwise_self_sim":
        example_list = converter.convert_pairwise_self_sim(
            dest=TF_RECORD_DIR,
            limit_length=args.limit_length,
            limit_question=args.limit_question,
        )
        print(example_list[0])
        print('Total: {}'.format(len(example_list)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        help="Set action for the spider. Supported actions: fetch_data, convert_data",
        type=str,
        choices=["fetch_data", "convert_data"],
    )
    parser.add_argument(
        "--method",
        "-m",
        help="Set method for converting data. Supported methods: normal(default), pairwise, pairwise_self_sim",
        type=str,
        default="normal",
        choices=["normal", "pairwise", "pairwise_self_sim"],
    )
    parser.add_argument(
        "--limit_length",
        "-l",
        help="Set max length for tokens. Default: unlimited",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--limit_question",
        "-q",
        help="Set max question numbers to convert. Default: unlimited",
        type=int,
        default=None,
    )
    args = parser.parse_args()

    action_dict = {
        'fetch_data': fetch_data,
        'convert_data': convert_data,
    }

    if args.action in action_dict:
        action_dict[args.action](args)
    else:
        print("Invalid action \"{}\" specified".format(args.action))


if __name__ == "__main__":
    main()
