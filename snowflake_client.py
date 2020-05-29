import sys
import snowflake.connector
from snowflake.connector import DictCursor


class SnowflakeClient:

    def __init__(self, user, pwd, account, keep_alive=False):
        self.snowflake_client = snowflake.connector.connect(
            user=user,
            password=pwd,
            account=account,
            client_session_keep_alive=keep_alive
        )

        return

    def fetch_one(self, query, params=None):
        cs = self.snowflake_client.cursor(DictCursor)
        try:
            cs.execute(query, params)
            one_row = cs.fetchone()
        finally:
            cs.close()
        return one_row

    def fetch_all(self, query, params=None, debug=False):
        cs = self.snowflake_client.cursor(DictCursor)
        rows = None
        try:
            cs.execute(query, params)
            rows = cs.fetchall()
        except:
            print("Unexpected error:", sys.exc_info()[0])
        finally:
            cs.close()

        if rows and debug:
            print('SF debug: # rows {}, first {}'.format(len(rows), rows[0]))

        return rows
