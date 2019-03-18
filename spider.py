#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : spider.py
# @Author: harry
# @Date  : 19-3-17 下午7:13
# @Desc  : LeetCode spider class

import os
import re

import requests
from requests import Response


class Spider(object):
    def __init__(self):
        self.base_url = "https://leetcode.com/"
        self.api = {
            'graphql': {
                'method': 'POST',
                'endpoint': 'graphql/'
            },
            'question_all': {
                'method': 'GET',
                'endpoint': 'api/problems/all/'
            }
        }
        self.payload_data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'payload_data'
        )
        self.headers_dict = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) Chrome/73.0.3683.75 Safari/537.36",
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        self.html_cleaner = re.compile('<.*?>')

    def get_api_url(self, api_name: str) -> str:
        return self.base_url + self.api[api_name]['endpoint']

    def get_api_method(self, api_name: str) -> str:
        return self.api[api_name]['method']

    def get_question_data_payload(self, title_slug: str) -> str:
        f = open(
            os.path.join(self.payload_data_path, 'question_data.txt'),
            "r"
        )
        data = f.read()
        f.close()
        return data % title_slug

    def get_question_data(self, title_slug) -> Response:
        response = requests.request(
            self.get_api_method("graphql"),
            self.get_api_url("graphql"),
            data=self.get_question_data_payload(title_slug),
            headers=self.headers_dict
        )
        return response

    def get_question_list(self) -> Response:
        response = requests.request(
            self.get_api_method("question_all"),
            self.get_api_url("question_all"),
            headers=self.headers_dict
        )
        return response
