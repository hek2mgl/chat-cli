# CLI Based AI Chat Application

This is a command-line interface (CLI) based AI chat application that allows users to interact with various 
AI models. The application supports multiple models and provides options for one-shot prompts, file input, 
and debugging.

## Features

- **Model Selection**: Choose from a variety of AI models for your chat.
- **One-shot Prompts**: Run a single prompt and exit.
- **File Input**: Append contents of a file to your prompt.
- **Model Listing**: List available models without starting a chat.

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - `requests`
  - `rich`

These requirements will be installed together with duckchat:

```bash
pip install .
```

## Usage

### Command-Line Arguments

- `--model`: Specify the AI model to use (default: `gpt-4o-mini`).
- `--list-models`: List available models and exit.
- `-f`, `--file`: Append contents of a specified file to the prompt.
- `--debug`: Enable debug output.
- `--oneshot`: Run a single prompt and exit.
- `--print-file`: Print only the specified file when the AI is supposed to handle a file.

### Example Commands

1. **Start a chat with the default model**:
   ```bash
   python chat.py
   ```

2. **List available models**:
   ```bash
   python chat.py --list-models
   ```

3. **Use a specific model**:
   ```bash
   python chat.py --model claude-3-haiku
   ```

4. **Run a one-shot prompt**:
   ```bash
   python chat.py --oneshot "What is the capital of France?"
   ```

5. **Append a file to the prompt**:
   ```bash
   python chat.py -f my_prompt.txt
   ```

6. **Enable debug output**:
   ```bash
   python chat.py --debug
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

Thanks to DuckDuckGo for their chat application at https://duck.ai, which is the backend for this tool.
