"""
DuckDuckGo - chat api client
"""
import json
import logging

import requests


# pylint: disable=too-few-public-methods
class ChatApiResponse:
    """
    Base class for DuckDuckGo chat api requests.
    """

    def __init__(self, requests_response):
        self.http_response = requests_response

    def vqd(self):
        """
        The DuckDuckGo api is using custom HTTP header values which need
        to be sent with every request. Their value is changing with every
        api response.
        """
        return self.http_response.headers["x-vqd-4"]

    def vqd_hash1(self):
        """
        The DuckDuckGo api is using custom HTTP header values which need
        to be sent with every request. Their value is changing with every
        api response.
        """
        return self.http_response.headers["x-vqd-hash-1"]


class PromptResponse(ChatApiResponse):
    """
    Encapsulate reading the text/event-stream and represent the
    response as String
    """

    def __init__(self, requests_response):
        super().__init__(requests_response)
        self._response_text = None

    def _slurp_response_stream(self):
        """
        The mime-type of the duckduckgo chat api response is
        text/event-stream and consists of multiple chunks. Each
        chunk consists of a json dict prefixed by the string 'data: '.

        The event stream ends with the string 'data: [DONE]'.

        Example event strem:

        data: {"message": "this", "model": "...", "created": "..."}
        data: {"message": " is", "model": "...", "created": "..."}
        data: {"message": " a", "model": "...", "created": "..."}
        data: {"message": " test", "model": "...", "created": "..."}
        data: {"model": "...", "created": "..."} # no message
        data: [DONE]

        See also: doc/example_curl.sh
        """
        buffer = ""
        for line in self.http_response.iter_lines():
            line = line.decode("utf8").strip()
            if not line:
                continue
            if line == "data: [DONE]":
                break
            if not line.startswith("data: "):
                raise ValueError(f"Bad format: {line}")

            data = json.loads(line.replace("data: ", ""))
            msg = data.get("message", "")
            buffer += msg

        return buffer

    def text(self):
        """
        Return the HTTP response as text
        """
        if self._response_text is None:
            self._response_text = self._slurp_response_stream()
        return self._response_text


class ChatApiClient:
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
        self.vqd_hash1 = None
        self.log = logging.getLogger("chat")
        self._session = None

    def _get_session(self):
        if self._session is None:
            self.log.debug("Create session")
            self._session = requests.Session()
        return self._session

    def init_vqd(self):
        """
        Set up the chat session by initializing the HTTP session and retrieving the VQD token.

        Raises:
            Exception: If the VQD token cannot be retrieved.
        """
        self.log.debug("Initializing")
        session = self._get_session()
        headers = {
            "x-vqd-accept": "1",
        }
        url = self.base_url + "/status"
        self.log.debug("Getting vqd from %s", url)
        http_response = session.get(url, headers=headers)
        http_response.raise_for_status()

        api_response = ChatApiResponse(http_response)
        self.vqd = api_response.vqd()
        self.vqd_hash1 = api_response.vqd_hash1()

        self.log.debug("Obtained vqd: %s", self.vqd)

        if not self.vqd:
            raise RuntimeError("Failed to obtain vqd")

        return api_response

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
        session = self._get_session()
        url = self.base_url + "/chat"

        headers = {
            "x-vqd-4": self.vqd,
            "x-vqd-hash-1": self.vqd_hash1,
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
        }

        payload = json.dumps(
            {
                "model": self.model,
                "messages": self.messages,
            }
        )

        http_response = session.post(
            url,
            headers=headers,
            data=payload,
        )

        http_response.raise_for_status()
        headers = dict(
            zip(
                http_response.headers.keys(),
                http_response.headers.values(),
            ),
        )
        self.log.debug("response headers %s", json.dumps(headers, indent=2))

        result = PromptResponse(http_response)
        new_vqd = result.vqd()

        self.log.debug("vqd changed: %s -> %s", self.vqd, new_vqd)

        self.vqd = new_vqd
        self.messages.append({"content": result.text(), "role": "assistant"})

        return result
