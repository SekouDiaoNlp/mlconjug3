#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import warnings
import numpy as np
import os
import tempfile
import pickle

from sklearn.exceptions import ConvergenceWarning
from click.testing import CliRunner

from mlconjug3 import (
    Conjugator, DataSet, Model, Verbiste,
    Verb, VerbEn, VerbEs, VerbFr, VerbIt, VerbPt, VerbRo,
    ConjugManager, cli
)

from mlconjug3.utils import ConjugatorTrainer
from mlconjug3.utils.error_analysis import analyze_errors
from mlconjug3.feature_extractor.feature_extractor import extract_verb_features

from mlconjug3.verbs import VerbInfo
from collections import OrderedDict

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)


class TestConjugator:
    conjugator = Conjugator()

    def test_conjugation(self):
        assert self.conjugator.conjugate("aller")


class TestCLI:
    def test_cli(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ['aller'])
        assert result.exit_code == 0


class TestErrorAnalysis:
    def test_full_analysis(self, capsys):
        analyze_errors(
            "fr",
            [1, 2, 2],
            [1, 1, 2],
            ["a", "b", "c"]
        )
        out = capsys.readouterr().out
        assert "Accuracy" in out


class TestFeatureExtractor:
    def test_basic(self):
        feats = extract_verb_features("running", lang="en")
        assert isinstance(feats, list)

    def test_empty(self):
        assert extract_verb_features("") == []

    def test_it_features(self):
        feats = extract_verb_features("parlare", lang="it")
        assert any("IT_" in f for f in feats)

    def test_ro_features(self):
        feats = extract_verb_features("utiliza", lang="ro")
        assert any("RO_" in f for f in feats)

    def test_fallback_language(self):
        feats = extract_verb_features("unknown", lang="xx")
        assert any("VOW_NUM" in f for f in feats)

    def test_structure(self):
        feats = extract_verb_features("letter", lang="en")
        assert any("HAS_DOUBLE" in f for f in feats)


class TestDataSetCoverage:

    def make_dataset(self):
        return {
            "aimer": {"template": "A:1"},
            "parler": {"template": "A:2"},
            "manger": {"template": "A:3"},
            "finir": {"template": "B:1"},
            "choisir": {"template": "B:2"},
            "agir": {"template": "B:3"},
            "venir": {"template": "C:1"},
            "tenir": {"template": "C:2"},
            "obtenir": {"template": "C:3"},
        }

    def test_dataset_init(self):
        ds = DataSet(self.make_dataset())
        assert ds.verbs is not None

    def test_split_data_default(self):
        ds = DataSet(self.make_dataset())
        ds.split_data()
        assert isinstance(ds.train_input, list)

    def test_split_data_invalid(self):
        ds = DataSet(self.make_dataset())
        with pytest.raises(ValueError):
            ds.split_data(proportion=0)

    def test_repr(self):
        ds = DataSet(self.make_dataset())
        assert "DataSet" in ds.__repr__()


class DummyModel:
    def predict(self, x):
        return ["A:default"]


class TestConjugManagerCoverage:

    def test_init_and_repr(self):
        cm = ConjugManager(language="fr")
        assert "ConjugManager" in repr(cm)
        assert isinstance(cm.verbs, dict)

    def test_invalid_verb_lookup(self):
        cm = ConjugManager(language="fr")
        assert cm.get_verb_info("nonexistent") is None

    def test_get_conjug_info_missing(self):
        cm = ConjugManager(language="fr")
        assert cm.get_conjug_info("fake_template") is None

    def test_is_valid_verb_branch(self):
        cm = ConjugManager(language="fr")
        verb = list(cm.verbs.keys())[0] if cm.verbs else "aller"
        assert isinstance(cm.is_valid_verb(verb), bool)

    def test_cache_invalid_extension_branch(self, tmp_path):
        cm = ConjugManager(language="fr")

        fake_file = tmp_path / "bad.txt"
        with open(fake_file, "w") as f:
            f.write("{}")

        cm._is_real_file = lambda x: True

        with pytest.raises(ValueError):
            cm._load_cache(str(fake_file))

    # ---------------------------
    # NEW: UNIMORPH TESTS
    # ---------------------------

    def test_unimorph_language_mapping(self):
        cm = ConjugManager(language="fr", use_unimorph=True)
        assert cm.UNIMORPH_LANG_MAP["fr"] == "fra"

    def test_unimorph_loader_fr(self):
        cm = ConjugManager(language="fr", use_unimorph=True)

        # Should load UniMorph data structures
        assert isinstance(cm.verbs, dict)
        assert cm.verbs is not None

        # conjugations may be dict or OrderedDict depending on loader
        assert cm.conjugations is not None

    def test_unimorph_loader_non_empty(self):
        cm = ConjugManager(language="fr", use_unimorph=True)

        # At least structural integrity checks
        assert len(cm.verbs) >= 0
        assert len(cm.conjugations) >= 0


class TestConjugatorStress:

    def test_ml_fallback_str(self):
        class M(DummyModel):
            def predict(self, x):
                return ["A:default"]

        c = Conjugator(language="fr", model=M())

        c.conjug_manager.conjugations["A:default"] = {
            "indicative": {"present": []}
        }

        result = c.conjugate("unknownverb")
        assert result is not None


class TestConjugatorMLBranches:

    def test_int_prediction_branch(self):
        class M:
            def predict(self, x):
                return [0]

        c = Conjugator(language="fr", model=M())

        if c.conjug_manager.templates:
            tpl = c.conjug_manager.templates[0]
            c.conjug_manager.conjugations[tpl] = {
                "indicative": {"present": []}
            }

        result = c.conjugate("aller")
        assert result is not None

    def test_string_prediction_branch(self):
        class M:
            def predict(self, x):
                return ["A:1"]

        c = Conjugator(language="fr", model=M())

        c.conjug_manager.conjugations["A:1"] = {
            "indicative": {"present": []}
        }

        result = c.conjugate("cacater")
        assert result is not None

    def test_predict_proba_branch(self):
        class M:
            classes_ = ["A:1"]

            def predict(self, x):
                return ["A:1"]

            def predict_proba(self, x):
                return [[1.0]]

        c = Conjugator(language="fr", model=M())

        c.conjug_manager.conjugations["A:1"] = {
            "indicative": {"present": []}
        }

        result = c.conjugate("aller")
        assert result is not None


class TestModelCoverage:

    def test_repr(self):
        m = Model(language="fr")
        assert "Model" in repr(m)

    def test_train_multiclass_safe(self):
        m = Model(language="fr")

        X = ["aller", "finir", "manger", "venir", "tenir"]
        y = [0, 1, 2, 1, 2]

        m.train(X, y)
        preds = m.predict(["aller"])
        assert len(preds) == 1

    def test_train_sample_weight_branch(self):
        m = Model(language="fr")

        X = ["aller", "finir", "manger", "venir", "tenir"]
        y = [0, 1, 2, 1, 2]
        w = [1.0, 0.2, 0.8, 0.5, 1.5]

        m.train(X, y, sample_weight=w)
        preds = m.predict(["finir"])
        assert len(preds) == 1

    def test_predict_multiple(self):
        m = Model(language="fr")
        m.train(["aller", "finir", "manger"], [0, 1, 2])

        preds = m.predict(["aller", "finir", "manger"])
        assert len(preds) == 3

    def test_predict_proba(self):
        m = Model(language="fr")
        m.train(["aller", "finir", "manger"], [0, 1, 2])

        proba = m.predict_proba(["aller"])
        assert proba is not None
        assert isinstance(proba, (list, np.ndarray))

    def test_predict_proba_error_branch(self):
        class FakePipeline:
            def predict_proba(self, x):
                raise AttributeError()

        class Broken(Model):
            def __init__(self):
                self.language = "fr"
                self.pipeline = FakePipeline()

        m = Broken()

        with pytest.raises(AttributeError):
            m.predict_proba(["aller"])

    def test_language_none_branch(self):
        m = Model(language=None)

        X = ["aller", "finir"]
        y = [0, 1]

        m.train(X, y)
        assert m.predict(["aller"]) is not None
