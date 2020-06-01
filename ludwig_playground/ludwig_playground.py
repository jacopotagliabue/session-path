"""

This script is a stand-alone entry point to train SessionPath with Ludwig starting from existing files.
You will need a prod2vec.tsv for embeddings and a data.csv for the training set - sample formats are included
in this folder.

The hello_ludwig script is a simple function that wraps Ludwig training and testing methods, with a couple of options
to let you easily try out model behavior on specific input pairs, or avoid training if you wish to re-use
the model in the folder.

"""

import os
from logging import DEBUG
from ludwig.api import LudwigModel

# script variables
FOLDER = os.path.dirname(os.path.abspath(__file__))  # folder is the current one with the playground script
LUDWIG_MODEL_DEFINITION = {
    'input_features': [
        {'name': 'skus_in_session', 'type': 'set',
         'pretrained_embeddings': 'prod2vec.tsv', 'embedding_size': 48,
         'embeddings_trainable': False},
        {'name': 'query', 'type': 'text', 'encoder': 'rnn', 'level': 'char'}
    ],
    'combiner': {'type': 'concat', 'num_fc_layers': 2},
    'output_features': [
        {'name': 'path', 'cell_type': 'lstm', 'type': 'sequence'}
    ],
    'training': {'epochs': 100, 'early_stopping': 5}
}
DATASET = 'data.csv'
# if false, skip training, if true, train and test on dataset from scratch
# after model is trained once, you can set it to False to just generate predictions
IS_TRAINING = True
PREDICTIONS = {
    'skus_in_session': ['SKU_123'],
    'query': ['nike jordan']
}
# if not empty, it needs to follow ludwig specs: https://uber.github.io/ludwig/api/LudwigModel/#predict


def train_and_test(model_definition, dataset_file, target_folder):
    model = LudwigModel(model_definition, logging_level=DEBUG)
    train_stats = model.train(data_csv=dataset_file)
    model.save(target_folder)
    # optionally a separate test file can be supplied OR
    # Ludwig built-in "split" column mechanism can be used
    predictions, test_stats = model.test(data_csv=dataset_file)
    print(test_stats['combined']['accuracy'])
    model.close()


def do_predictions(prediction_dictionary, target_folder):
    # reload the model
    model = LudwigModel.load(target_folder)
    # get predictions
    predictions = model.predict(data_dict=prediction_dictionary)
    for input_q, input_skus, output in zip(prediction_dictionary['query'],
                               prediction_dictionary['skus_in_session'],
                               predictions['path_predictions']):
        print("\nInput: <{}, {}>, predicted path: {}".format(input_q,
                                                           input_skus,
                                                           ' > '.join([o for o in output if o != '<PAD>'])
                                                           ))

    return


def hello_ludwig(model_definition, ludwig_folder, is_training, dataset_file, prediction_dictionary):
    if is_training:
        print("\n===> Now training...")
        train_and_test(model_definition, dataset_file, ludwig_folder)
    # if predictions are supplied, run predictions
    if prediction_dictionary:
        print("\n===>Now predicting user-supplied rows...")
        do_predictions(prediction_dictionary, ludwig_folder)

    # all done
    print("\n\nAll done! See you, space cowboy...")
    return


if __name__ == "__main__":
    hello_ludwig(model_definition=LUDWIG_MODEL_DEFINITION,
                 ludwig_folder=FOLDER,
                 is_training=IS_TRAINING,
                 dataset_file=DATASET,
                 prediction_dictionary=PREDICTIONS)