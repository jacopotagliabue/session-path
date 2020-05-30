import json
import gensim
from snowflake_client import SnowflakeClient


def train_product_2_vec_model(sessions, min_c=2, size=48, window=3, iterations=20, ns_exponent=0.75):
    model = gensim.models.Word2Vec(
        sessions,
        min_count=min_c,
        size=size,
        window=window,
        iter=iterations,
        ns_exponent=ns_exponent
    )
    return model.wv


def get_products_in_session_from_snowflake(
    snowflake_client: SnowflakeClient,
    env_id: str,
    start_date: str,
    end_date: str,
    min_size: int=2,
    max_size: int=50
):
    sql_query = """
        SELECT
          a."SKUS"
        FROM
          (
            SELECT
              augmented_skus."session_id",
              ARRAY_AGG(augmented_skus."SKU") WITHIN GROUP (
                ORDER BY augmented_skus."server_timestamp_epoch_ms" ASC
              ) AS SKUS
            FROM
              (
                SELECT
                  ev."session_id",
                  ev."server_timestamp_epoch_ms",
                  LOWER(ev."product_sku") as sku
                FROM TOOSEO.SSOT.SESSIONIZED_PROD AS ev
                WHERE
                  ev."server_environment_id" = %(env_id)s AND
                  ev."user_device" != 'bot' AND
                  ev."server_date" >= %(start_date)s AND
                  ev."server_date" < %(end_date)s AND
                  ev."product_action" = 'detail'
              )augmented_skus
            GROUP BY augmented_skus."session_id"
          )a
        WHERE
          ARRAY_SIZE(a."SKUS") >= %(min_size)s AND
          ARRAY_SIZE(a."SKUS") < %(max_size)s
        ORDER BY a."session_id";
    """
    # get rows
    rows = snowflake_client.fetch_all(
        sql_query,
        params={
            'env_id': env_id,
            'start_date': start_date,
            'end_date': end_date,
            'min_size': min_size,
            'max_size': max_size
        },
        debug=True)

    # need to de-serialize from snowflake
    return [json.loads(s['SKUS']) for s in rows]


def calculate_prod_to_vecs(
    env_id: str,
    train_start: str,
    train_end: str,
    snowflake_client: SnowflakeClient
):
    sessions = get_products_in_session_from_snowflake(snowflake_client, env_id, train_start, train_end)
    prod2vec_model = train_product_2_vec_model(sessions)

    return prod2vec_model