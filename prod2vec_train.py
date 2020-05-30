import json
import gensim
from snowflake_client import SnowflakeClient


def train_product_2_vec_model(sessions, min_c=2, size=48, window=3, iterations=20, ns_exponent=0.75):
    """
    Wrap gensim standard word2vec model, providing sensible parameters from other experiments with prod2vec.

    :param sessions: list of list of strings
    :param min_c: gensim param
    :param size: gensim param
    :param window: gensim param
    :param iterations: gensim param
    :param ns_exponent: gensim param
    :return: gensim Keyed Vector object after training
    """
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
    """
    Template function to get products in all sessions from a SQL database. Result is a list of list, each list
    containing the sequence of SKU for the products viewed in a shopping sessions.

    :param snowflake_client: Python class to connect to a remote database
    :param env_id: client id
    :param start_date: start date
    :param end_date: end date
    :param min_size: specify a minimum session length to avoid sessions too short (1 product)
    :param max_size: specify a maximum session length to avoid sessions that are suspiciously long (100 products)
    :return: list of lists of strings, each string is an SKU in a session
    """
    sql_query = """"""
    raise Exception("Need to implement this!")
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
        debug=False)

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