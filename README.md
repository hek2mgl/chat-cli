# chatcli

This is a command-line interface (CLI) based AI chat application that allows users to interact with the various 
AI models offered by [DuckDuckGo's AI chat](https://duck.ai). Other models and providers may be added later.

## Features

- **Interactive AI chat**: at your fingertips
- **One-shot Prompts**: Run a single prompt and exit.
- **File Input**: Append contents of a file to your prompt. (Allows to modify files easily)
- **Run shell commands from inside the chat**
- **Pipe shell output into the chat**
- **Text to speech support (experimental)**: Listen to AI generated stories while coding :)! 
- **Model Selection**: Choose from a variety of AI models for your chat.

## Installation

```console
git clone https://github.com/hek2mgl/chatcli
cd chatcli
python3 -mvenv venv
source venv/bin/activate
pip install .
chatcli --help
```

## Usage

### Example Commands

1. **Start an interative chat with the default model**:

```console
chatcli
```

2. **List available models**:

```console
chatcli --list-models
```

3. **Use a specific model**:

```console
chatcli --model claude-3-haiku
```

4. **Run a one-shot prompt**:

```console
chatcli --oneshot "What is the capital of France?"
# short version
chatcli -s "What is the capital of France?"
```

5. **The prompt from the file (implies --oneshot)**:

```console
chatcli -f my_prompt.txt
chatcli -s 'summarize' -f my_text.txt
chatcli -s 'translate' -f my_text.txt
chatcli -s 'remove trailing whitespace' -f my_code.py
some_program_with_error_msg | chatcli -s 'explain' -f /dev/stdin
```

6. **Text to speech support (experimental)**

chatcli supports text to speech (tts) via the Google text to speak API.

Note! You need a working speaker to hear the voice.

Note! The AI answers will be sent to Google's text to speech API. chatcli
will not share account credentials or login at Google, but if you are
concerned about your privacy don't use this feature.

```console
chatcli --tts
chatcli --tts -s 'hello world'
```

6. **Enable debug output**:

```console
chatcli --debug
```

## Chat commands

**Start a in interactive shell**

To start an interactive shell type `!`

```
you:!
```

`exit` the shell to return to the chat

**Run a shell command**

To run a shell commmand, type `!` and the command:

```
you:!ls -al
you:!vi my.txt
you:!ssh server.xyz.org
```

## Logging

The application uses Python's built-in logging module. If the `--debug` flag is set, the logging level is 
set to DEBUG; otherwise, it defaults to WARNING.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs 
feature requests.

## License

This project is licensed under the Apache License Version 2.0. See the LICENSE file for more details.

## Acknowledgments

- Thanks to [DuckDuckGo](https://duckduckgo.com) for their [AI chat](https://duck.ai), which is the backend for this tool.
- Thanks to [textualize/rich](https://github.com/Textualize/rich) for the markdown renderer.

