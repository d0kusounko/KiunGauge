#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    機運ゲージメイン.
"""
import sys
import os

import tweepy
from flask import Flask, session, redirect, render_template, request, send_from_directory

import configuration
import define
from sql import Sql

# デフォルト文字コードをUTF-8に設定.
reload(sys)
sys.setdefaultencoding('utf-8')

# ロギング初期化.
from logging import getLogger, StreamHandler, DEBUG
logger = getLogger('kiun_gauge')
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# Flaskの起動.
app = Flask(__name__)
app.secret_key = configuration.SECRET_KEY     # sessionに必要.

# Twitter OAuthコールバックURL
TWITTER_OAUTH_CALLBACK_URL = configuration.ROOT_URL + '/twitter_auth_callback'


@app.route('/favicon.ico')
def favicon():
    """
        favicon設定.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    """
        rootページの表示.
    """
    twitter_login = False
    twitter_id = ''
    user_icon = ''
    kiun_names = None
    kiun_values = None

    # Twitter認証済みチェック.
    if twitter_is_auth():
        # 認証済.
        api = twitter_get_api()
        twitter_login = True
        twitter_user = api.me()
        twitter_id = twitter_user.screen_name
        user_icon = twitter_user.profile_image_url_https

        sql = Sql()
        sql.connect()
        param = sql.get_user_parameter(twitter_user.id)
        sql.close()

        kiun_names = param['kiun_names']
        kiun_values = param['kiun_values']

    # templates/index.html を使ってレンダリング.
    return render_template('index.html',
                           twitter_login=twitter_login, twitter_id=twitter_id, user_icon=user_icon,
                           kiun_names=kiun_names, kiun_values=kiun_values)


@app.route('/twitter_auth')
def twitter_auth():
    """
        Twitter認証.
        リクエストトークンを保存し, ユーザー認証ページにリダイレクト.
    """
    auth = tweepy.OAuthHandler(
        configuration.CONSUMER_KEY,
        configuration.CONSUMER_SECRET,
        TWITTER_OAUTH_CALLBACK_URL)

    try:
        redirect_url = auth.get_authorization_url()
        session['oauth_token'] = auth.request_token
        session['oauth_state'] = 'request'
    except tweepy.TweepError, e:
        logger.error(str(e))
        twitter_logout()

    # 認証用URLにリダイレクト.
    return redirect(redirect_url)


@app.route('/twitter_auth_callback', methods=['GET'])
def twitter_auth_callback():
    """
        Twitter認証コールバック.
        リクエストトークンよりアクセストークンを取得.
    """
    verifier = request.args.get('oauth_verifier')

    if verifier is None:
        # ログインしなかった場合は何もせずrootへ.
        return redirect(configuration.ROOT_URL)

    auth = tweepy.OAuthHandler(
        configuration.CONSUMER_KEY, configuration.CONSUMER_SECRET)
    auth.request_token = session['oauth_token']

    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError, e:
        logger.error(str(e))
        twitter_logout()
        return {}

    session['oauth_token'] = auth.access_token
    session['oauth_token_secret'] = auth.access_token_secret
    session['oauth_state'] = 'done'

    api = twitter_get_api()
    user = api.me()

    sql = Sql()
    sql.connect()

    # データベースのユーザー情報更新
    sql.register_user(user.id, user.screen_name)

    # 新規の場合はユーザーパラメーター初期化.
    param = sql.get_user_parameter(user.id)
    if param is None:
        initialize_user_parameter(user.id)

    sql.close()

    # rootページへ戻る.
    return redirect(configuration.ROOT_URL)


def twitter_get_api():
    """
        Twitter API取得.
    """
    auth = tweepy.OAuthHandler(
        configuration.CONSUMER_KEY, configuration.CONSUMER_SECRET)
    auth.set_access_token(session['oauth_token'], session['oauth_token_secret'])

    try:
        return tweepy.API(auth)
    except tweepy.TweepError, e:
        logger.error(str(e))
        twitter_logout()
        return {}


def twitter_is_auth():
    """
        Twitter認証済みかどうか.
    """
    if not session.get('oauth_state') is None:
        if session['oauth_state'] == 'done':
            return True
    return False


@app.route('/twitter_logout')
def twitter_logout():
    """
        Twitterログアウト.
    """
    del session['oauth_token'], session['oauth_token_secret'], session['oauth_state']
    # rootページへ戻る.
    return redirect(configuration.ROOT_URL)


@app.route('/kiun_update', methods=['POST'])
def kiun_update():
    """
        機運更新.
    """
    print 'kiun_update test!' + request.method

    if request.method == 'POST':

        data = request.form.to_dict(flat=False)
        values = [int(s) for s in data['values']]   # 機運値の文字列リストを数値に変換.

        api = twitter_get_api()
        user = api.me()

        sql = Sql()
        sql.connect()
        param = sql.get_user_parameter(user.id)

        # 機運値をツイート.
        tweet_kiun_gauge(api, param['kiun_names'], values)

        # 機運がMAXになった項目をチェック.
        kiun_max_names = []
        kiun_max_values_index = []
        for i, val in enumerate(values):
            if val == 10:
                kiun_max_names.append(param['kiun_names'][i])
                kiun_max_values_index.append(i)

        # 機運がMAXになった際のツイート.
        if len(kiun_max_names) >= 1:
            tweet_kiun_max(api, kiun_max_names)

        # 0に戻す.
        if len(kiun_max_values_index) >= 1:
            for max_i in kiun_max_values_index:
                values[max_i] = 0

        # 機運値をデータベースに更新.
        sql.update_user_parameter(user.id, param['kiun_names'], values)

        sql.close()

    # templates/kiun_update.html を使ってレンダリング.
    return render_template('kiun_update.html', kiun_max_names=kiun_max_names)


@app.route('/settings')
def settings():
    """
        機運設定.
    """

    # 機運名一覧取得.
    api = twitter_get_api()
    user = api.me()

    sql = Sql()
    sql.connect()
    param = sql.get_user_parameter(user.id)
    sql.close()

    kiun_names = param['kiun_names']

    # templates/settings.html を使ってレンダリング.
    return render_template('settings.html', kiun_names=kiun_names)


@app.route('/settings_apply', methods=['POST'])
def settings_apply():
    """
        機運設定適用.
    """

    # POSTデータ取得.
    data = request.form.to_dict(flat=False)
    logger.debug( data['kiun_names'] )

    # 設定更新.
    api = twitter_get_api()
    user = api.me()

    sql = Sql()
    sql.connect()
    param = sql.get_user_parameter(user.id)

    for i, name in enumerate(data['kiun_names']):
        # 機運名が変更された項目は機運ゲージを0にする.
        if name != param['kiun_names'][i]:
            param['kiun_values'][i] = 0

    sql.update_user_parameter(user.id, data['kiun_names'], param['kiun_values'])
    sql.close()

    # rootページへ戻る.
    return redirect(configuration.ROOT_URL)


def initialize_user_parameter(twitter_user_id):
    """
        ユーザーの設定情報を初期化.
    """
    kiun_names = define.KIUN_DEFAULT_NAME
    kiun_values = [0, 0, 0, 0, 0]

    sql = Sql()
    sql.connect()
    sql.register_user_parameter(twitter_user_id, kiun_names, kiun_values)
    sql.close()


def tweet_kiun_gauge(api, kiun_names, kiun_values):
    """
        機運ゲージをツイートする.
    """

    # ツイート文作成.
    tweet_str = ''
    for i, name in enumerate(kiun_names):

        if name:
            # 機運名
            tweet_str += name + ' '

            # 機運値
            for i_value in range(10):
                if i_value < kiun_values[i]:
                    tweet_str += '■'
                else:
                    tweet_str += '□'

            tweet_str += '\n'

    tweet_str += '\n#機運ゲージ\n' + configuration.ROOT_URL

    # ツイート.
    try:
        api.update_status(tweet_str)
    except tweepy.TweepError, e:
        if e.api_code == 187:   # 重複ツイートエラーは無視.
            pass
        else:
            logger.error(str(e))
            twitter_logout()
            return {}


def tweet_kiun_max(api, kiun_max_names):
    """
        MAXになった機運をツイートする.
    """

    # ツイート文作成.
    tweet_str = ''
    for i, name in enumerate(kiun_max_names):

        if i >= 1:
            tweet_str += 'と'

        # 機運名
        tweet_str += name

    tweet_str += 'の機運高まってきた'

    # ツイート.
    try:
        api.update_status(tweet_str)
    except tweepy.TweepError, e:
        if e.api_code == 187:   # 重複ツイートエラーは無視.
            pass
        else:
            logger.error(str(e))
            twitter_logout()
            return {}


# main
if __name__ == "__main__":
    # webサーバー立ち上げ.
    logger.debug('kiun_gauge app start.')
    app.run()
