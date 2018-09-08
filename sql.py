#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SQL操作マネージャー.
"""
import psycopg2
from psycopg2.extras import DictCursor
import define
from logging import getLogger
from urlparse import urlparse
import configuration

logger = getLogger('kiun_gauge')


class Sql:
    def __init__(self):
        self.conn = None

    def connect(self):
        """
            DBに接続.
        """
        db_url_env = configuration.DATABASE_URL
        logger.debug('DATABASE_URL = ' + db_url_env)
        db_url = urlparse(db_url_env)

        self.close()
        self.conn = psycopg2.connect(
            host=db_url.hostname,
            dbname=db_url.path[1:],
            port=db_url.port,
            user=db_url.username,
            password=db_url.password,
        )
        self.conn.autocommit = True
        logger.debug('connect Database.')

    def register_user(self, _id, _screen_id):
        """
            users にユーザー情報を登録.
            すでに存在する場合はscreen_idを更新.
        """
        if self.conn is not None:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO users (id, screen_id) VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET screen_id = %s
                """
                cur.execute(query, (_id, _screen_id, _screen_id))

                logger.debug('register user : id = %s, screen_id = %s', _id, _screen_id)

    def register_user_parameter(self, _id, _kiun_names, _kiun_values):
        """
            users_parameters にユーザーパラメーターを登録.
        """
        if (len(_kiun_names) != define.KIUN_ITEM_NUM or
                len(_kiun_values) != define.KIUN_ITEM_NUM):
            # 項目数エラー.
            return

        if self.conn is not None:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO users_parameters (id, kiun_names, kiun_values )
                    VALUES (%s, %s, %s)
                """

                cur.execute(query,
                            (_id, _kiun_names, _kiun_values))

                logger.debug('register user_parameter : id = %s', _id)
                logger.debug('-> kiun_name : %s', ','.join(_kiun_names))
                logger.debug('-> kiun_value : %s', ','.join(map(str, _kiun_values)))

    def update_user_parameter(self, _id, _kiun_names, _kiun_values):
        """
            users_parameters のユーザーパラメーターを更新.
        """
        if (len(_kiun_names) != define.KIUN_ITEM_NUM or
                len(_kiun_values) != define.KIUN_ITEM_NUM):
            # 項目数エラー.
            return

        if self.conn is not None:
            with self.conn.cursor() as cur:
                query = """
                    UPDATE users_parameters SET
                        kiun_names = %s, kiun_values = %s
                        WHERE id = %s
                """

                cur.execute(query,
                            (_kiun_names, _kiun_values, _id, ))

                logger.debug('update user_parameter : id = %s', _id)
                logger.debug('-> kiun_name : %s', ','.join(_kiun_names))
                logger.debug('-> kiun_value : %s', ','.join(map(str, _kiun_values)))

    def get_user_parameter(self, _id):
        """
            ユーザーのパラメーターを取得.
        """
        if self.conn is not None:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT * FROM users_parameters WHERE id = %s
                """
                cur.execute(query, (_id,))
                result = cur.fetchone()
                if result is None:
                    return None
                dict_result = dict(result)
                return dict_result

    def close(self):
        """
            DBの接続を解除.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.debug('disconnect Database.')

    def __del__(self):
        self.close()
