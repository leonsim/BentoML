import pytest

import bentoml  # noqa: E402
from bentoml.artifact import PickleArtifact  # noqa: E402


class TestModel(object):
    def predict(self, df):
        df["age"] = df["age"].add(5)
        return df

    def evaluate(self, input_data):
        return [10, 24]


@bentoml.artifacts([PickleArtifact("model")])
@bentoml.env()
class TestBentoService(bentoml.BentoService):
    """My RestServiceTestModel packaging with BentoML
    """

    @bentoml.api(bentoml.handlers.DataframeHandler, input_dtypes={"age": "int"})
    def predict(self, df):
        """predict expects dataframe as input
        """
        return self.artifacts.model.predict(df)

    @bentoml.api(bentoml.handlers.ImageHandler)
    def evaluate(self, input_data):
        return self.artifacts.model.evaluate(input_data)


@pytest.fixture()
def bento_service():
    """Create a new TestBentoService
    """
    test_model = TestModel()
    return TestBentoService.pack(model=test_model)


@pytest.fixture()
def bento_archive_path(bento_service, tmpdir):  # pylint:disable=redefined-outer-name
    """Create a new TestBentoService, saved it to tmpdir, and return full saved_path
    """
    saved_path = bento_service.save(str(tmpdir))
    return saved_path
