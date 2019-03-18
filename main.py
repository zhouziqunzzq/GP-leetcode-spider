#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : main.py
# @Author: harry
# @Date  : 19-3-17 下午7:41
# @Desc  : Main cli

import time
import os

from spider import Spider
from util import *


def main():
    # create dir for data storage
    cur_path = os.path.dirname(os.path.abspath(__file__))
    create_dir(os.path.join(cur_path, 'result'))

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
    result_path = os.path.join(cur_path, "result")
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


if __name__ == "__main__":
    main()
