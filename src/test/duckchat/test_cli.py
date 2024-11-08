from pdb import set_trace as bp

import pytest
import requests

from duckchat.cli import *


def test_create_argparser():
    create_argparser()


class TestUserInterface:
    @pytest.fixture
    def instance(self):
        return UserInterface()

    def test_print_welcome_msg(self, instance, mocker):
        args = mocker.Mock()
        instance.print_welcome_msg(args)

    def test_print_models(self, instance, mocker):
        instance.print_models({
            "model_a_short_name": "model_a",
            "model_b_short_name": "model_b",
        })

    def test_error(self, instance):
        instance.error("test")

    def test_print_answer(self, instance, mocker):

        response = mocker.Mock(spec=["text"])
        response.text.return_value = "foo bar"
        chat = mocker.Mock()
        args = mocker.Mock()
        args.print_file = False
        assert instance.print_answer(response, chat) is None

    def test_print_cmd_help(self, instance):
        assert instance.print_cmd_help() is None


@pytest.mark.parametrize("debug", [True, False])
def test_init_logging(debug, mocker):
    args = mocker.Mock()
    args.debug = debug
    assert init_logging(args)


@pytest.mark.parametrize("cli_arg_debug", [True, False])
@pytest.mark.parametrize("cli_arg_list_models", [True, False])
@pytest.mark.parametrize("cli_arg_model", ["gpt-4o-mini", "unknown"])
@pytest.mark.parametrize("cli_arg_one_shot", ["one shot prompt", None])
@pytest.mark.parametrize("cli_arg_file", ["test.file", None])
@pytest.mark.parametrize("prompt_exception", [None, requests.exceptions.HTTPError])
def test_main(
    cli_arg_debug,
    cli_arg_list_models,
    cli_arg_model,
    cli_arg_one_shot,
    cli_arg_file,
    prompt_exception,
    mocker,
):
    cli_args = mocker.Mock(["list_models"])
    cli_args.debug = cli_arg_debug
    cli_args.file = cli_arg_file
    cli_args.list_models = cli_arg_list_models
    cli_args.model = cli_arg_model
    cli_args.one_shot = cli_arg_one_shot
    argparser = mocker.Mock()
    argparser.parse_args.return_value = cli_args
    mocker.patch("duckchat.cli.create_argparser", return_value=argparser)
    mocker.patch("duckchat.cli.readfile", return_value="test")
    mocker.patch("duckchat.cli.UserInterface.read_prompt", return_value="test prompt")
    mocker.patch("duckchat.cli.init_chat_api_client")
    prompt_response = mocker.Mock(spec=["text"])
    prompt_response.text.return_value = "test response"

    if cli_arg_list_models:
        assert main() == 0
    elif cli_arg_model == "unknown":
        assert main() == 1
    elif prompt_exception:
        mocker.patch(
            "duckchat.cli.ChatApi.prompt",
            side_effect=requests.exceptions.HTTPError(response=mocker.Mock()),
        )
        assert main() == 1
    else:
        # An EOFError needs to get injected to break the UI endless loop
        mocker.patch("duckchat.cli.ChatApiClient.prompt", side_effect=[prompt_response, EOFError])
        assert main() == 0
