"""
Tests Spark-ML Linear converters
"""
import unittest
import warnings

import numpy as np
import torch

from hummingbird.ml._utils import sparkml_installed, pandas_installed
from hummingbird.ml import convert

if sparkml_installed() and pandas_installed():
    import pandas as pd
    from pyspark import SparkContext
    from pyspark.sql import SQLContext
    from pyspark.ml.linalg import Vectors
    from pyspark.ml.classification import LogisticRegression
    
    sc = SparkContext.getOrCreate()
    sql = SQLContext(sc)

class TestSparkMLLinear(unittest.TestCase):
    def _test_linear(self, classes, model_class=LogisticRegression):        
        n_features = 20
        n_total = 100
        np.random.seed(0)
        warnings.filterwarnings("ignore")
        X = np.random.rand(n_total, n_features)
        X = np.array(X, dtype=np.float32)
        y = np.random.randint(classes, size=(n_total,1))

        arr = np.concatenate([y, X], axis=1).reshape(n_total,-1)
        df = map(lambda x: (int(x[0]), Vectors.dense(x[1:])), arr)
        df = sql.createDataFrame(df,schema=["label", "features"])

        model = LogisticRegression()
        model = model.fit(df)

        torch_model = convert(model, "torch")
        self.assertTrue(torch_model is not None)
        np.testing.assert_allclose(
            np.array(model.transform(df).select("probability").collect()).reshape(-1, classes),
            torch_model.predict_proba(X), rtol=1e-06, atol=1e-06
        )

    # pyspark.ml.LogisticRegression with two classes
    @unittest.skipIf((not sparkml_installed) or (not pandas_installed), reason="Spark-ML test requires pyspark and pandas")
    def test_logistic_regression_binary(self):
        self._test_linear(2, model_class=LogisticRegression)

    # pyspark.ml.LogisticRegression with multi_class
    @unittest.skipIf((not sparkml_installed) or (not pandas_installed), reason="Spark-ML test requires pyspark and pandas")
    def test_logistic_regression_multi_class(self):
        self._test_linear(5, model_class=LogisticRegression)


if __name__ == "__main__":
    unittest.main()
