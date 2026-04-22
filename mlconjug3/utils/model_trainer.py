"""
This module provides the ConjugatorTrainer class for training, evaluating,
and saving machine learning models used for verb conjugation.

It supports:
- Dataset splitting
- Model training via mlconjug3 pipeline
- Evaluation against ground truth templates
- Serialization of trained models
"""

import multiprocessing
import mlconjug3
import pickle
import numpy as np
from functools import partial
from time import time


class ConjugatorTrainer:
    """
    Trainer class for ML-based verb conjugation models.

    This class orchestrates:
    - Dataset preparation
    - Model training
    - Evaluation of template prediction accuracy
    - Persistence of trained models

    Parameters
    ----------
    lang : str
        Target language code (e.g., "fr", "en", "es").
    output_folder : str
        Directory where the trained model will be saved.
    split_proportion : float
        Train/test split ratio for the dataset.
    dataset : DataSet
        Dataset object providing verbs and templates.
    model : Model
        Machine learning model to train.

    Attributes
    ----------
    lang : str
        Language of the training pipeline.
    output_folder : str
        Output directory for serialized model.
    split_proportion : float
        Dataset split ratio.
    dataset : DataSet
        Dataset instance used for training.
    model : Model
        Machine learning model instance.
    conjugator : Conjugator
        `mlconjug3` conjugator wrapper that uses the configured model.
    """

    def __init__(self, lang, output_folder, split_proportion, dataset, model):
        self.lang = lang
        self.output_folder = output_folder
        self.split_proportion = split_proportion
        self.dataset = dataset
        self.model = model

        # Initialize Conjugator wrapper
        self.conjugator = mlconjug3.Conjugator(
            self.lang,
            model=self.model,
        )

    def train(self):
        """
        Train the conjugation model using the provided dataset split.

        Steps:
        - Splits dataset into train/test sets
        - Trains model on verb samples and template labels
        - Reports completion status
        """
        np.random.seed(42)

        # Split dataset
        self.dataset.split_data(proportion=self.split_proportion)

        # Train model
        self.conjugator.model.train(
            self.dataset.verbs_list,
            self.dataset.templates_list,
        )

        print(f"{self.lang} model successfully trained.")

    def predict(self):
        """
        Generate predictions for all verbs in the dataset.

        Returns
        -------
        list or numpy.ndarray
            Predicted template indices.
        """
        return self.model.predict(self.dataset.verbs_list)

    def evaluate(self):
        """
        Evaluate model accuracy against ground truth templates.

        Computes:
        - Accuracy score
        - Number of mismatches
        - Total number of samples

        Prints evaluation summary.
        """
        predictions = self.model.predict(self.dataset.verbs_list)

        score = len(
            [a == b for a, b in zip(predictions, self.dataset.templates_list) if a == b]
        ) / len(predictions)

        misses = len(
            [a != b for a, b in zip(predictions, self.dataset.templates_list) if a != b]
        )

        entries = len(predictions)

        print(
            f"The score of the {self.lang} model is {score} "
            f"with {misses} misses out of {entries} entries."
        )

    def save(self):
        """
        Save trained model to disk using pickle serialization.

        Output format:
        trained_model-{lang}.pickle
        """
        with open(
            f"{self.output_folder}/trained_model-{self.lang}.pickle", "wb"
        ) as file:
            pickle.dump(self.model, file)
