"""
CLI based AI chat application.
"""

import argparse
import json
import logging
import os
import sys

import requests
from rich.console import Console
from rich.prompt import Prompt

# Dictionary mapping model aliases to their respective identifiers.
models = {
    "gpt-4o-mini": "gpt-4o-mini",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "llama": "claude-3-haiku-20240307",
    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
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
        help="The model which should be used for the chat. The list of "
        "available models can be print with the --list-models option",
        default="gpt-4o-mini",
    )

    parser.add_argument(
        "--list-models",
        help="List the models which can be used with the --model option and "
        "then exit the program. Do not start a chat.",
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--file",
        help="Append contents of file to prompt",
    )

    parser.add_argument(
        "--debug",
        help="Add debug output",
        action="store_true",
    )

    parser.add_argument(
        "--oneshot",
        metavar="PROMPT",
        help="Run prompt and exit",
    )

    parser.add_argument(
        "--print-file",
        help="When the AI is supposed a file, print only this file."
        " Useful for patching and in place edits",
        action="store_true",
    )

    return parser


class Output(Console):
    """
    Custom output class for handling console interactions.

    Inherits from rich.console.Console to provide enhanced output formatting.
    """

    def hello(self):
        """Print a welcome message to the console."""
        print("Welcome to aipy cli chat", file=sys.stderr)

    def print_models(self):
        """Print the available models to the console.

        Args:
            models (dict): A dictionary of model aliases and their names.
        """
        for model_alias, model_name in models.items():
            print(model_alias, model_name)

    def error(self, message):
        """Print an error message to the console.

        Args:
            message (str): The error message to display.
        """
        self.print("[red]EE:[/] " + str(message))

    def print_answer(self, response, chat, args):
        """Process and print the AI's response to the console.

        Args:
            response (requests.Response): The response object from the AI.
            chat (Chat): The Chat instance managing the conversation.
            args (argparse.Namespace): The parsed command-line arguments.
        """
        buffer = ""
        for line in response.iter_lines(decode_unicode=True):
            line = line.strip()
            chat.log.debug("read line %s", line)
            if not line:
                continue
            if line == "data: [DONE]":
                break

            if not line.startswith("data: "):
                raise ValueError(f"Bad format: {line}")

            data = json.loads(line.replace("data: ", ""))
            msg = data.get("message", "")
            buffer += msg

        chat.messages.append({"content": msg, "role": "assistant"})

        printing = False
        for ln, line in enumerate(buffer.split("\n")):
            if "```" in line and not printing and args.print_file:
                printing = True
                continue

            if "```" in line and printing and args.print_file:
                printing = False
                continue

            if printing or not args.print_file:
                if ln == 0 and not args.oneshot:
                    line = f"🤖 [cyan]{args.model}[default]: {line}"
                Output().print(line)


class Chat:
    """
    Class to manage the chat session with the AI model.

    Attributes:
        base_url (str): The base URL for the AI service.
        model (str): The model identifier to use for the chat.
        messages (list): List of messages exchanged in the chat.
        vqd (str): VQD token for session management.
        session (requests.Session): HTTP session for making requests.
        log (logging.Logger): Logger for debugging and information.
    """

    def __init__(self, url, model):
        """
        Initialize the Chat instance.

        Args:
            url (str): The base URL for the AI service.
            model (str): The model identifier to use for the chat.
        """
        self.base_url = url
        self.model = model
        self.messages = []
        self.vqd = None
        self.session = None
        self.log = logging.getLogger("chat")

    def setup(self):
        """
        Set up the chat session by initializing the HTTP session and retrieving the VQD token.

        Raises:
            Exception: If the VQD token cannot be retrieved.
        """
        self.log.debug("Initializing")
        self.log.debug("Create session")
        self.session = requests.Session()
        headers = {
            "x-vqd-accept": "1",
        }
        url = self.base_url + "/status"
        self.log.debug("Getting vqd from %s", url)
        response = self.session.get(url, headers=headers)
        response.raise_for_status()

        self.vqd = response.headers.get("x-vqd-4")
        self.log.debug("Received vqd: %s", self.vqd)
        if not self.vqd:
            raise RuntimeError("Failed to retrieve VQD")
        self.log.debug("Initialized. Ok")

    def prompt(
        self,
        msg,
    ):
        """
        Send a message to the AI model and receive a response.

        Args:
            msg (str): The message to send to the AI.

        Returns:
            requests.Response: The response object from the AI.

        Raises:
            requests.exceptions.HTTPError: If the request to the AI service fails.
        """
        self.messages.append({"content": msg, "role": "user"})
        url = self.base_url + "/chat"

        headers = {
            "x-vqd-4": self.vqd,
            "Content-Type": "application/json",
            "Accept": "text/plain",
        }

        payload = json.dumps(
            {
                "model": self.model,
                "messages": self.messages,
            }
        )

        response = self.session.post(
            url,
            headers=headers,
            data=payload,
        )

        response.raise_for_status()

        new_vqd = response.headers["x-vqd-4"]
        self.log.debug("vqd changed: %s -> %s", self.vqd, new_vqd)
        self.vqd = new_vqd
        return response


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


def input_prompt():
    """
    Prompt the user for input until a non-empty response is received.

    Continuously asks the user for input until they provide a non-empty string.
    Displays an error message if the input is empty.

    Returns:
        str: The user's input prompt.
    """
    while True:
        username = os.environ.get("USER", "me")
        prompt = Prompt.ask(f"🦆 [yellow]{username}").strip()
        if not prompt:
            Output().print("[dark_red]Your prompt is empty!")
            continue
        return prompt


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


def main():
    """
    Main entry point for the CLI chat application.

    Parses command-line arguments, initializes logging, and manages the chat session.
    If the --list-models option is provided, it lists available models and exits.
    Otherwise, it sets up the chat and enters a loop to handle user prompts and AI responses.
    """
    args = create_argparser().parse_args()
    init_logging(args)
    output = Output()

    if args.list_models:
        output.print_models()
        return 0

    if args.model not in models:
        output.error(
            f"Model '{args.model}' is not available. "
            "List available models with --list-models"
        )
        return 1

    chat = Chat(
        "https://duckduckgo.com/duckchat/v1",
        models[args.model],
    )

    chat.setup()

    try:
        while True:
            if args.oneshot:
                prompt = args.oneshot
                if args.file:
                    prompt += " " + readfile(args.file)
            else:
                prompt = input_prompt()
                if prompt == "\\exit":
                    Output().print("bye!")
                    break
            Output().print_answer(chat.prompt(prompt), chat, args)
            if args.oneshot:
                break

    except (KeyboardInterrupt, EOFError):
        print("")
        return 1

    except requests.exceptions.HTTPError as err:
        Output().error(err)
        Output().error(err.response.text)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
