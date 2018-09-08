#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    機運ゲージ アプリケーション設定.
    環境変数より取得.
"""
import os

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ROOT_URL = os.environ['ROOT_URL']
SECRET_KEY = os.environ['SECRET_KEY']
DATABASE_URL = os.environ['DATABASE_URL']
