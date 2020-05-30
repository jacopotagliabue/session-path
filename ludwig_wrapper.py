from ludwig.api import LudwigModel
from logging import DEBUG


def train_with_ludwig(model_definition, train_file_csv, target_model_path):
    model = LudwigModel(model_definition, logging_level=DEBUG)
    print("Starting Ludwig training now on {}...".format(train_file_csv))
    train_stats = model.train(data_csv=train_file_csv)
    print("Ludwig training complete, saving now...")
    model.save(target_model_path)

    return train_stats


def run_test_with_ludwig(model_path, test_file_csv):
    model = LudwigModel.load(model_path)
    predictions, test_stats = model.test(data_csv=test_file_csv)
    model.close()

    return predictions, test_stats



