"""
Classifier evaluation within ARMORY
"""

import json
import sys
import logging
from importlib import import_module

import numpy as np

from armory.data import data

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def evaluate_classifier(config_path: str) -> None:
    """
    Evaluate a config file for classiifcation robustness against attack.
    """
    with open(config_path, "r") as fp:
        config = json.load(fp)

    model_config = config["model"]
    classifier_module = import_module(model_config["module"])
    classifier_fn = getattr(classifier_module, model_config["name"])
    classifier = classifier_fn(
        model_config["model_kwargs"], model_config["wrapper_kwargs"]
    )

    preprocessing_fn = getattr(classifier_module, "preprocessing_fn")

    clean_x, adv_x, labels = data.load(
        config["dataset"]["name"], preprocessing_fn=preprocessing_fn
    )

    # Evaluate the ART classifier on benign test examples
    logger.info("Predicting on clean dataset...")
    predictions = classifier.predict(clean_x)
    benign_accuracy = np.sum(np.argmax(predictions, axis=1) == labels) / len(labels)
    logger.info("Accuracy on benign test examples: {}%".format(benign_accuracy * 100))

    # Evaluate the ART classifier on adversarial examples from transfer attack
    logger.info("Predicting on adversarial dataset...")
    predictions = classifier.predict(adv_x)
    adversarial_accuracy = np.sum(np.argmax(predictions, axis=1) == labels) / len(
        labels
    )
    logger.info(
        "Accuracy on adversarial test examples: {}%".format(adversarial_accuracy * 100)
    )

    filepath = "outputs/evaluation-results.json"
    with open(filepath, "w") as f:
        output_dict = {
            "config": config,
            "results": {
                "baseline_accuracy": str(benign_accuracy),
                "adversarial_accuracy": str(adversarial_accuracy),
            },
        }
        json.dump(output_dict, f, sort_keys=True, indent=4)
    logger.info(f"Evaluation Results written to {filepath}")


if __name__ == "__main__":
    config_path = sys.argv[-1]
    evaluate_classifier(config_path)