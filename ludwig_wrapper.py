from ludwig.api import LudwigModel
from logging import DEBUG


def train_with_ludwig(model_definition, train_file_csv, target_model_path):
    """
    Wrap around Ludwig training routine.

    :param model_definition: dictionary defining deep learning architecture with Ludwig conventions
    :param train_file_csv: path to csv file for training
    :param target_model_path: target path to store the model after training
    :return: dictionary with training stats for human debug
    """
    model = LudwigModel(model_definition, logging_level=DEBUG)
    print("Starting Ludwig training now on {}...".format(train_file_csv))
    train_stats = model.train(data_csv=train_file_csv)
    print("Ludwig training complete, saving now...")
    model.save(target_model_path)

    return train_stats


def run_test_with_ludwig(model_path, test_file_csv):
    """
    Wrap around Ludwig testing.

    :param model_path: path in which already trained model is
    :param test_file_csv: path to csv file with test data points
    :return: predictions from the model and dictionary with stats for human debug
    """
    model = LudwigModel.load(model_path)
    predictions, test_stats = model.test(data_csv=test_file_csv)
    model.close()

    return predictions, test_stats



