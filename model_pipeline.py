"""

This script runs a local Luigi pipeline that goes from zero to a fully trained and tested Ludwig model.
The pipeline stores the sequence of the intermediate models and feature files in a timestamp-based folder:
to re-run specific sequences, the folder name can be specified in the init process at the bottom.

The pipeline has four steps:

1. train prod2vec model on user behavior
2. prepare training and testing dataset as Ludwig-friendly csv files
3. define and train Ludwig model
4. re-load and test Ludwig model

If you already have files for embeddings and the dataset, you can also just try out ludwig with the stand-alone
script in the ludwig_playground folder.

"""

import os
import csv
import json
import numpy as np
from time import time
import luigi
from snowflake_client import SnowflakeClient
from dotenv import load_dotenv
# now import all the scripts we are gluing together
from prod2vec_train import calculate_prod_to_vecs
from ludwig_wrapper import train_with_ludwig, run_test_with_ludwig
from data_service import prepare_training_and_test_set
# load env variables from local file
load_dotenv(dotenv_path='.env', verbose=True)
# get a Snowflake instance for the entire pipeline
sf_client = SnowflakeClient(
                user=os.getenv('SNOWFLAKE_USER'),
                pwd=os.getenv('SNOWFLAKE_PWD'),
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                keep_alive=False
            )

def convert(o):
    """
    Helper function to json dump np.int64 objects to a local JSON

    :param o: object to convert
    :return: either a Python int or the original object
    """
    if isinstance(o, np.int64):
        return int(o)
    raise o


# Task 0 - Calculate Product Embeddings
class Prod2Vec(luigi.Task):
    """
    This class encapsulates the function training product embedding on browsing data; prod2vec embeddings are
    used by the final model to represent in-session intent for the shopper
    """

    def requires(self):
        return None

    def output(self):
        return luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'), 'prod2vec.tsv'))

    def run(self):
        """
        The function calculate_prod_to_vecs returns a gensim Keyed Vector object, which is then saved locally
        in the Glove format
        """
        prod2vec_model = calculate_prod_to_vecs(
            env_id=os.getenv('ENV_ID'),
            train_start=os.getenv('TRAIN_START'),
            train_end=os.getenv('TRAIN_END'),
            snowflake_client=sf_client
        )
        with open(self.output().path, "w") as f:
            for sku in prod2vec_model.vocab:
                f.write("{}\t{}\n".format(sku, '\t'.join(['{:.10f}'.format(_) for _ in prod2vec_model[sku]])))

        return


#  Task 1 - Prepare Training and Test Dataset
class PrepareDataset(luigi.Task):
    """
    This class encapsulates the function responsible to retrieve the dataset for training/testing.
    """

    def requires(self):
        return Prod2Vec()

    def output(self):
        return luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'), 'data.csv'))

    def run(self):
        """
        The function prepare_training_and_test_set returns a list of dictionary. Each dictionary is a row,
        with field: value structure - fields are: "sku_in_session" for in-session product interaction, "query"
        for the query made by the user, "path" as the target taxonomy path.
        """
        data_set = prepare_training_and_test_set(snowflake_client=sf_client,
                                                            env_id=os.getenv('ENV_ID'),
                                                            start_date=os.getenv('TRAIN_START'),
                                                            end_date=os.getenv('TRAIN_END'),
                                                            category_map_file=os.path.join('data', os.getenv('CATALOG_FILE')))
        # make sure there is data!
        assert len(data_set) > 0
        # write to final csv
        with open(self.output().path, 'w') as f:
            w = csv.DictWriter(f, data_set[0].keys())
            w.writeheader()
            for d in data_set:
                w.writerow(d)

        return


#  Task 2 - Train Wide-and-Deep Enc-Decoder
class LudwigTrain(luigi.Task):

    def requires(self):
        return {
            'data': PrepareDataset(),
            'embeddings': Prod2Vec()
        }

    def output(self):
        return luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'), 'train_stats.json'))

    def run(self):
        ludwig_model_definition = {
            'input_features': [
                {'name': 'skus_in_session', 'type': 'set',
                 'pretrained_embeddings': self.input()['embeddings'].path, 'embedding_size': 48,
                 'embeddings_trainable': False},
                {'name': 'query', 'type': 'text', 'encoder': 'rnn', 'level': 'char'}
            ],
            'combiner': {'type': 'concat', 'num_fc_layers': 2},
            'output_features': [
                {'name': 'path', 'cell_type': 'lstm', 'type': 'sequence'}
            ],
            'training': {'epochs': 100, 'early_stopping': 5}
        }
        train_stats = train_with_ludwig(model_definition=ludwig_model_definition,
                                        train_file_csv=self.input()['data'].path,
                                        target_model_path=luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'))).path
                                        )
        with open(self.output().path, 'w') as outfile:
            json.dump(train_stats, outfile)

        return


#  Task 3 - Test Deep Model
class LudwigTest(luigi.Task):

    def requires(self):
        return {
            'train': LudwigTrain(),
            'data': PrepareDataset()
        }

    def output(self):
        return luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'), 'test_stats.json'))

    def run(self):
        predictions, test_stats = run_test_with_ludwig(model_path=luigi.LocalTarget(os.path.join(os.getenv('PIPELINE_FOLDER'))).path,
                                                       test_file_csv=self.input()['data'].path)
        print("\n ======> Test accuracy (last): {}".format(test_stats['path']['last_accuracy']))
        with open(self.output().path, 'w') as outfile:
            json.dump(test_stats['path'], outfile, default=convert)

        return


if __name__ == '__main__':
    # just some paths we need
    MODELS_DIR = os.getenv('MODELS_DIR')
    print("Target folder is {}".format(MODELS_DIR))
    # create a local output folder
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    # attach a specific timestamp to the run
    pipeline_timestamp = str(int(time()))
    PIPELINE_FOLDER = os.path.join(MODELS_DIR, pipeline_timestamp)
    # create if does not exists
    if not os.path.exists(PIPELINE_FOLDER):
        os.makedirs(PIPELINE_FOLDER)
    # set folder as env for the entire process
    os.environ['PIPELINE_FOLDER'] = PIPELINE_FOLDER
    # just run pipeline locally
    luigi.build([LudwigTest()], local_scheduler=True)
