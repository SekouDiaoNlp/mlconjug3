"""
mlconjug.py

Main entry point for verb conjugation using a hybrid approach:
- Rule-based conjugation via Verbiste for known verbs
- Machine learning fallback for unknown verbs

This module exposes the `Conjugator` class.
"""

from .PyVerbiste import Verbiste
from .conjug_manager import ConjugManager
from .constants import *
from .verbs import *
from .feature_extractor import extract_verb_features
from .dataset import DataSet
from .models import Model
from .utils import logger

from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor
from zipfile import ZipFile
import joblib
from importlib import resources
import numpy as np


VERBS = {
    "fr": VerbFr,
    "en": VerbEn,
    "es": VerbEs,
    "it": VerbIt,
    "pt": VerbPt,
    "ro": VerbRo,
}


class Conjugator:
    """
    Main class for verb conjugation.

    Combines:
    - Verbiste dictionary-based conjugation
    - Machine learning fallback for unknown verbs
    """

    def __init__(self, language="fr", model=None, backend="legacy"):
        """
        Initialize a conjugator instance.

        Parameters
        ----------
        language : str, optional
            Language code used for conjugation, by default "fr".
        model : Model or estimator, optional
            Trained model used for ML fallback on unknown verbs. If None,
            the pre-trained packaged model for `language` is loaded.
        backend : str, optional
            Data backend identifier. Supported values are:
            - "legacy" : Verbiste XML/JSON resources
            - "unimorph" : UniMorph JSON resources

        Raises
        ------
        ValueError
            If `backend` is not one of "legacy" or "unimorph".

        Examples
        --------
        >>> Conjugator(language="fr")
        >>> Conjugator(language="fr", backend="unimorph")
        """
        self.language = language
        self.backend = backend

        if backend == "legacy":
            self.conjug_manager = Verbiste(language=language)
            if not getattr(self.conjug_manager, "verbs", None):
                self.backend = "unimorph"
                self.conjug_manager = ConjugManager(language=language, use_unimorph=True)
        elif backend == "unimorph":
            self.conjug_manager = ConjugManager(language=language, use_unimorph=True)
        else:
            raise ValueError(
                "Unsupported backend. Allowed values are 'legacy' or 'unimorph'."
            )

        if model is None:
            resource_path = resources.files(RESOURCE_PACKAGE).joinpath(
                PRE_TRAINED_MODEL_PATH[language]
            )

            try:
                with resource_path.open("rb") as stream:
                    with ZipFile(stream) as content:
                        with content.open(
                            f"trained_model-{self.language}-final.pickle"
                        ) as archive:
                            model = joblib.load(archive)
                self.set_model(model)
            except FileNotFoundError:
                logger.warning(
                    _(
                        "Pre-trained model archive not found; ML fallback disabled for this session."
                    )
                )
                self.model = None
        else:
            if isinstance(model, Model):
                self.set_model(model)
            else:
                logger.warning(
                    _("Using a non-Model estimator. Compatibility is not guaranteed.")
                )
                self.model = model

    def __repr__(self):
        return f"{__name__}.{self.__class__.__name__}(language={self.language})"

    def conjugate(self, verbs, subject="abbrev"):
        if isinstance(verbs, str):
            return self._conjugate(verbs, subject)

        with ProcessPoolExecutor() as executor:
            return list(
                executor.map(self._conjugate, verbs, [subject] * len(verbs))
            )

    @lru_cache(maxsize=1024)
    def _conjugate(self, verb, subject="abbrev"):
        verb = verb.lower()

        # ---------------------------
        # RULE-BASED PATH
        # ---------------------------
        if verb in self.conjug_manager.verbs:
            verb_info = self.conjug_manager.get_verb_info(verb)

            # guard against corrupted/empty Verbiste entries
            if verb_info is None:
                return None

            conjug_info = self.conjug_manager.get_conjug_info(verb_info.template)

            # prevent Verb(None) crash
            if verb_info is None or conjug_info is None:
                return None

            return VERBS[self.language](verb_info, conjug_info, subject)

        # ---------------------------
        # ML FALLBACK PATH
        # ---------------------------
        if self.model is None:
            logger.warning(
                _("Please provide an instance of a mlconjug3.mlconjug3.Model")
            )
            return None

        prediction = self.model.predict([verb])[0]

        template = None
        confidence_score = None

        # ---------------------------
        # TEMPLATE RESOLUTION
        # ---------------------------
        if isinstance(prediction, (int, np.integer)):
            try:
                templates = self.conjug_manager.templates

                # guard empty / corrupted templates
                if not templates:
                    return None

                template = templates[int(prediction)]
            except Exception:
                return None

        elif isinstance(prediction, str):
            template = prediction

        else:
            return None

        # ---------------------------
        # PROBABILITY HANDLING
        # ---------------------------
        try:
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba([verb])[0]

                if hasattr(self.model, "pipeline"):
                    classes = self.model.pipeline.classes_
                elif hasattr(self.model, "classes_"):
                    classes = self.model.classes_
                else:
                    classes = None

                if classes is not None and prediction in classes:
                    class_index = list(classes).index(prediction)
                    confidence_score = round(float(proba[class_index]), 3)

        except Exception:
            confidence_score = None

        # ---------------------------
        # FINAL VERB BUILD (SAFE)
        # ---------------------------
        try:
            colon_index = template.index(":")
            index = -len(template[colon_index + 1:])
            root = verb if index == 0 else verb[:index]
        except Exception:
            return None

        verb_info = VerbInfo(verb, root, template)
        conjug_info = self.conjug_manager.get_conjug_info(template)

        # final guard against corrupted conjugation data
        if verb_info is None or conjug_info is None:
            return None

        verb_object = VERBS[self.language](
            verb_info,
            conjug_info,
            subject,
            predicted=True  # <-- IMPORTANT FIX
        )

        if confidence_score is not None:
            verb_object.confidence_score = confidence_score

        return verb_object

    def set_model(self, model):
        """
        Set the ML fallback model used for unknown verbs.

        Parameters
        ----------
        model : Model
            Trained `mlconjug3.models.Model` instance.

        Raises
        ------
        ValueError
            If `model` is not an instance of `Model`.
        """
        if not isinstance(model, Model):
            logger.warning(
                _("Please provide an instance of a mlconjug3.mlconjug3.Model")
            )
            raise ValueError("Invalid model type")

        self.model = model
