import json
import csv
from snowflake_client import SnowflakeClient


def get_sku_2_target_facet(category_map_file):
    """
    Template function that accepts a file containing at least product identifiers (SKU) and the associated
    category path, e.g. for nike shoes XYZ the mapping will be "XYZ" -> "shoes nike basketball"

    :param category_map_file: file path
    :return: dictionary mapping each sku to the space-separated list of nodes in the relevant category path
    """
    sku_2_cat = {}
    with open(category_map_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raise Exception("Need to implement this!")
            # extract from the mapping file the SKU and make sure to format the category path properly
            # sku_2_cat[row['sku']] = ' '.join([])

    return sku_2_cat


def get_session_data_from_snowflake(
    snowflake_client: SnowflakeClient,
    env_id: str,
    start_date: str,
    end_date: str
):
    """
    Template function that accepts a database client (Snowflake connection), client and timestamp parameters
    and return a list of dictionary - each row should contain "BEFORE_SKUS" as an array of strings, as product
    identifiers of interactions in the session, "QUERY_STRING" as the issued query, "CLICKED_PRODUCTS", as an array of
    strings, as product identifiers of what was clicked after the query in the result page.

    :param snowflake_client: Python class to connect to a remote database
    :param env_id: client id
    :param start_date: start date
    :param end_date: end date
    :return: list of dictionaries, each dictionary is a row as specified above
    """
    # need to fill the query here!
    sql_query = """ """
    raise Exception("Need to implement this!")
    # get rows
    rows = snowflake_client.fetch_all(
        sql_query,
        params={
            'env_id': env_id,
            'start_date': start_date,
            'end_date': end_date
        },
        debug=False)

    data = []
    # need to deserialize SF data
    for r in rows:
        r['QUERY_STRING'] = r['QUERY_STRING'].lower().strip()
        r['BEFORE_SKUS'] = [_.lower() for _ in json.loads(r['BEFORE_SKUS'])]
        r['CLICKED_PRODUCTS'] = [_.lower() for _ in json.loads(r['CLICKED_PRODUCTS'])]

    return data


def normalize_and_augment_rows(rows, category_map_file):
    """
    Given dataset and mappig sku->target path, build the final dataset composed by in-session interaction with SKUs,
    the query issued by the shopper, the target category path, which is what the model should predict in the end.

    :param rows: list of dictionaries containing session data
    :param category_map_file: path of the category mapping file
    :return: list of dictionaries, each row is a sample for the model - SKUs, query, target category path
    """
    sku_2_target_facet = get_sku_2_target_facet(category_map_file)
    final_rows = []
    for row in rows:
        target_cats = [sku_2_target_facet[_] for _ in row['CLICKED_PRODUCTS'] if _ in sku_2_target_facet]
        # skip if no target sku
        if len(target_cats) == 0:
            continue
        final_rows.append({
            'query': row['QUERY_STRING'],
            'skus_in_session': ' '.join(row['BEFORE_SKUS']),
            'path': target_cats[0]  # take the first target cat
        })

    return final_rows


def prepare_training_and_test_set(snowflake_client, env_id, start_date, end_date, category_map_file):
    rows = get_session_data_from_snowflake(snowflake_client, env_id, start_date, end_date)
    cleaned_rows = normalize_and_augment_rows(rows, category_map_file)

    return cleaned_rows