import pytest
import pandas as pd
import numpy as np

from bentoml.handlers.dataframe_handler import (
    DataframeHandler,
    check_dataframe_column_contains,
)


def test_dataframe_request_schema():
    handler = DataframeHandler(
        input_dtypes={"col1": "int", "col2": "float", "col3": "string"}
    )

    schema = handler.request_schema["application/json"]["schema"]
    assert "object" == schema["type"]
    assert 3 == len(schema["properties"])
    assert "array" == schema["properties"]["col1"]["type"]
    assert "integer" == schema["properties"]["col1"]["items"]["type"]
    assert "number" == schema["properties"]["col2"]["items"]["type"]
    assert "string" == schema["properties"]["col3"]["items"]["type"]


def test_dataframe_handle_cli(capsys, tmpdir):
    def test_func(df):
        return df["name"][0]

    handler = DataframeHandler()

    json_file = tmpdir.join("test.json")
    with open(str(json_file), "w") as f:
        f.write('[{"name": "john","game": "mario","city": "sf"}]')

    test_args = ["--input={}".format(json_file)]
    handler.handle_cli(test_args, test_func)
    out, err = capsys.readouterr()
    assert out.strip().endswith("john")


def test_dataframe_handle_aws_lambda_event():
    test_content = '[{"name": "john","game": "mario","city": "sf"}]'

    def test_func(df):
        return df["name"][0]

    handler = DataframeHandler()
    success_event_obj = {
        "headers": {"Content-Type": "application/json"},
        "body": test_content,
    }
    success_response = handler.handle_aws_lambda_event(success_event_obj, test_func)

    assert success_response["statusCode"] == 200
    assert success_response["body"] == '"john"'

    error_event_obj = {
        "headers": {"Content-Type": "this_will_fail"},
        "body": test_content,
    }
    error_response = handler.handle_aws_lambda_event(error_event_obj, test_func)
    assert error_response["statusCode"] == 400


def test_check_dataframe_column_contains():
    df = pd.DataFrame(
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=["a", "b", "c"]
    )

    # this should pass
    check_dataframe_column_contains({"a": "int", "b": "int", "c": "int"}, df)
    check_dataframe_column_contains({"a": "int"}, df)
    check_dataframe_column_contains({"a": "int", "c": "int"}, df)

    # this should raise exception
    with pytest.raises(ValueError) as e:
        check_dataframe_column_contains({"required_column_x": "int"}, df)
    assert str(e.value).startswith("Missing columns: required_column_x")

    with pytest.raises(ValueError) as e:
        check_dataframe_column_contains(
            {"a": "int", "b": "int", "d": "int", "e": "int"}, df
        )
    assert str(e.value).startswith("Missing columns:")
