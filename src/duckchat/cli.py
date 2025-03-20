"""
CLI based AI chat application.
"""

import argparse
import atexit
import code
import json
import logging
import os
import re
import readline
import subprocess
import sys
import textwrap

import requests
import rich.console
from rich.markdown import Markdown

from duckchat import __version__
from duckchat.duckduckgo import (
    ChatApiClient,
    ChatApiResponse,
    PromptResponse,
)

# Dictionary mapping model aliases to their respective identifiers.
models = {
    "gpt-4o-mini": "gpt-4o-mini",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "llama": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "mistral": "mistralai/Mistral-Small-24B-Instruct-2501",
}


def create_argparser():
    """
    Create and configure the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        help="the model to be used for the chat. The list of "
        "available models can be printed with the --list-models option",
        default="gpt-4o-mini",
        choices=models.keys(),
    )

    parser.add_argument(
        "--list-models",
        help="list the models that can be used with the --model option and "
        "then exit the program. Do not start a chat",
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--file",
        help="append contents of file to prompt",
    )

    parser.add_argument(
        "--debug",
        help="print debug output",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--one-shot",
        metavar="PROMPT",
        help="execute the prompt and exit",
    )

    parser.add_argument(
        "--tts",
        action="store_true",
        help="enable text-to-speech (experimental)",
    )

    parser.add_argument(
        "--tts-lang",
        help="text-to-speech language. (en for English, de for German)"
        " default is en",
        default="en",
    )

    parser.add_argument(
        "--tts-rate",
        help="rate of the text-to-speech voice",
        type=float,
        default=1.1,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    parser.add_argument(
        "--print-file",
        help="(try to) extract a file from the AI answer. this works when the"
        " answer contains exactly one code block. intended for AI-driven"
        " in-place editing of a file (experimental)",
        action="store_true",
    )

    return parser


class UserInterface():
    """
    Custom output class for handling console interactions.

    Inherits from rich.console.Console to provide enhanced output formatting.
    """
    """
    Derived from an example in the Python documentation
    see: https://docs.python.org/3/library/readline.html
    """
    def __init__(self):
        self.output = rich.console.Console()
        # self.input = code.InteractiveConsole(None, "<console>")
        readline.parse_and_bind("tab: complete")

    def read_prompt(self):
        """
        Prompt the user for input until a non-empty response is received.

        Continuously asks the user for input until they provide a non-empty string.
        Displays an error message if the input is empty.

        Returns:
            str: The user's input prompt.
        """
        while True:
            prompt_prefix = "you: "
            prompt = input(prompt_prefix)
            if not prompt:
                self.output.print("[dark_red]Your prompt is empty!")
                continue
            return prompt

    def print_welcome_msg(self, args):
        """Print a welcome message to the console."""
        msg = f"[cyan]Welcome to duckchat-{__version__}, model: {args.model}"
        self.output.print(msg)
        self.output.print("---")

    def print_models(self, models):
        """
        Print the available models to the console.

        Args:
            models (dict): A dictionary of model aliases and their names.
        """
        for model_alias, model_name in models.items():
            self.output.print(model_alias, model_name)

    def error(self, message):
        """Print an error message to the console.

        Args:
            message (str): The error message to display.
        """
        self.output.print(f"[red]EE:[/] {message}")

    def print_answer(self, response, chat):
        """Process and print the AI's response to the console.

        Args:
            response (requests.Response): The response object from the AI.
            chat (Chat): The Chat instance managing the conversation.
        """
        self.output.print(f"[cyan]{chat.model}[default]: ", end="")
        #Output().print(Markdown(response.text()), end="")
        self.output.print(response.text())

    def print_cmd_help(self):
        """
        Print the cli --help
        """
        self.output.print(
            textwrap.dedent(
                """
            Available commands:

            listmodels - print available models
            setmodel [MODEL] - set the model. with no argument, print the current model
            help - display this help
        """
            )
        )


def init_logging(args):
    """
    Initialize logging for the application.

    Configures the logging level based on the provided command-line arguments.
    If the debug flag is set, the logging level is set to DEBUG; otherwise, it defaults to WARNING.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing the debug flag.

    Returns:
        logging.Logger: The configured logger instance.
    """
    log = logging.getLogger()
    if args.debug:
        logging.basicConfig()
        log.setLevel(logging.DEBUG)
    return log


def readfile(filename):
    """
    Read the contents of a file.

    Opens the specified file and returns its contents as a string.

    Args:
        filename (str): The path to the file to be read.

    Returns:
        str: The contents of the file.
    """
    with open(filename, encoding="utf8") as open_file:
        return open_file.read()


def spawn_shell(command_line):
    """
    Spawn a new interactive shell or execute a command in a subshell.

    If the command_line is "!", an interactive login shell is started.
    Otherwise, the command specified in command_line (excluding the leading
    character) is executed in a non-interactive shell with a custom prompt.

    Args:
     command_line (str): The command to execute or "!" to start an interactive shell.
    """
    command_line = command_line.lstrip("!")
    if not command_line:
        command_line = ["bash", "-li"]

    subprocess.run(
        command_line[1:],
        check=False,
        env={"PS2": "(exit to return) >"},
    )


def run_cmd(command_line, chat):
    """
    Parses and executes a command from the command line input.

    Args:
        command_line (str): The command line input, starting with a command character.
        chat (Chat): An instance of the Chat class that holds chat messages and model information.

    The function processes the command line input to extract the command and its arguments,
    and performs actions based on the command, such as clearing chat history, listing models,
    or setting the current model.

    Commands:
        - "newhist": Clears the chat messages.
        - "listmodels": Lists available models.
        - "setmodel": Sets the current model based on the provided argument.

    """
    command_line = command_line[1:]
    words = re.split(" +", command_line)
    command = words[0]

    if len(words) > 1:
        args = words[1:]
    else:
        args = []

    # if command == "m":
    print(command, args)

    if command == "newhist":
        chat.messages = []
    elif command == "listmodels":
        Output().print_models()
    elif command == "setmodel":
        if len(args):
            chat.model = models[args[0]]
        else:
            Output().print(chat.model)
    elif command == "help":
        Output().print_cmd_help()


def init_chat_api_client(args):
    """
    Create and initialize the chat client object
    """
    if args.model not in models:
        msg = (
            f"Model '{args.model}' is not available. "
            "List available models with --list-models"
        )
        raise ValueError(msg)

    api_client = ChatApiClient(
        "https://duckduckgo.com/duckchat/v1",
        models[args.model],
    )
    api_client.init_vqd()
    return api_client


def main():
    """
    Main entry point for the CLI chat application.

    Parses command-line arguments, initializes logging, and manages the chat session.
    If the --list-models option is provided, it lists available models and exits.
    Otherwise, it sets up the chat and enters a loop to handle user prompts and AI responses.
    """
    args = create_argparser().parse_args()
    init_logging(args)
    user_interface = UserInterface()
    user_interface.print_welcome_msg(args)

    try:
        chat = init_chat_api_client(args)

        if args.list_models:
            user_interface.print_models(models)
            return 0

        if args.one_shot:
            prompt = args.one_shot
            if args.file:
                prompt += " " + readfile(args.file)
            user_interface.print_answer(chat.prompt(prompt), chat)
            return 0

        while True:
            prompt = user_interface.read_prompt()

            if prompt.startswith("!"):
                spawn_shell(prompt)
                continue

            if prompt.startswith(":"):
                run_cmd(prompt, chat)
                continue

            user_interface.print_answer(chat.prompt(prompt), chat)

    except (KeyboardInterrupt, EOFError):
        print("")

    except requests.exceptions.HTTPError as err:
        user_interface.error(err)
        user_interface.error(err.response.text)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
