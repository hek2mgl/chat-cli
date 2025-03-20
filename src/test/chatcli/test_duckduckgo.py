"""
tests for chatcli.duckduckgo
"""
import pytest

from chatcli.duckduckgo import *


class TestApiResponse:
    @pytest.fixture
    def instance(self, mocker):
        http_response = mocker.Mock()
        http_response.headers = {"x-vqd-4": "1-1234567890"}
        instance = ApiResponse(http_response)
        return instance

    def test_vqd(self, instance):
        assert instance.vqd() == "1-1234567890"


class TestPromptResponse:
    @pytest.mark.parametrize(
        "param",
        [
            {
                # An empty response.
                # In real life, empty responses haven't been observed
                "response_lines": [],
                "expected_text": "",
            },
            {
                # A corrupted response, which is missing the prefix "data: "
                # Such a response hasn't been observed in real life. The test
                # is for the coverage.
                "response_lines": ["This line had no prefix".encode("utf-8")],
                "expected_text": None,
                "exception": ValueError,
            },
            {
                # this is a realistic response
                "response_lines": [
                    'data: {"message": "this"}\n'.encode("utf-8"),
                    "".encode("utf-8"),
                    'data: {"message": " is"}\n'.encode("utf-8"),
                    "".encode("utf-8"),
                    'data: {"message": " a"}\n'.encode("utf-8"),
                    "".encode("utf-8"),
                    'data: {"message": " test."}\n'.encode("utf-8"),
                    "".encode("utf-8"),
                    "data: [DONE]\n".encode("utf-8"),
                ],
                "expected_text": "this is a test.",
            },
        ],
    )
    def test__slurp_response_stream(self, param, mocker):
        response_lines = param.get("response_lines")
        expected_text = param.get("expected_text")
        exception_cls = param.get("exception")

        http_response = mocker.Mock()
        http_response.iter_lines.return_value = response_lines
        instance = PromptResponse(http_response)
        if exception_cls:
            with pytest.raises(exception_cls):
                instance._slurp_response_stream()
        else:
            assert instance._slurp_response_stream() == expected_text

    def test_text(self, mocker):
        http_response = mocker.Mock()
        instance = PromptResponse(http_response)
        slurp_response_stream_mock = mocker.patch.object(
            instance, "_slurp_response_stream"
        )

        slurp_response_stream_mock.return_value = "foo"

        assert instance.text() == "foo"
        assert instance.text() == "foo"

        # The second call should use the cached value, therefore '1'
        assert slurp_response_stream_mock.call_count == 1


class TestChatApiClient():
    @pytest.fixture
    def instance(self, mocker):
        instance = ChatApiClient("https://foo.bar", "test-model-1")
        return instance

    def test__get_session(self, instance, mocker):
        session = mocker.Mock(spec=[])
        constructor_mock = mocker.patch("requests.Session", return_value=session)
        assert instance._get_session()
        assert instance._get_session()

        # Only during the first invocation of _get_session(), a new Session
        # object gets initialized. During the second and subsequent
        # invocations, _get_session() must return the cached object
        assert constructor_mock.call_count == 1

    @pytest.mark.parametrize("vqd", ["4-1234", None])
    def test_status(self, instance, vqd, mocker):
        http_response = mocker.Mock()
        http_response.headers = {
            "x-vqd-4": vqd,
        }
        session = mocker.Mock(spec=["get"])
        session.get.return_value = http_response
        mocker.patch.object(instance, "_get_session", return_value=session)
        mocker.patch(
            "chatcli.cli.PromptResponse._slurp_response_stream", return_value="test"
        )

        if vqd is None:
            with pytest.raises(RuntimeError):
                assert instance.init_vqd() is None
        else:
            assert instance.init_vqd() is None

        session.get.assert_called_with(
            "https://foo.bar/status",
            headers={
                "x-vqd-accept": "1",
            },
        )

    def test_prompt(self, instance, mocker):
        http_response = mocker.Mock()
        http_response.headers = {
            "x-vqd-4": "4-2345",
        }
        session = mocker.Mock(spec=["post"])
        session.post.return_value = http_response
        mocker.patch.object(instance, "_get_session", return_value=session)
        mocker.patch(
            "chatcli.cli.PromptResponse._slurp_response_stream", return_value="test"
        )

        instance.prompt("test")
