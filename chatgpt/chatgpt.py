#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os

from requests import HTTPError
from typing import List
from uuid import uuid4 as uuid

from chatgpt.authentication import OpenAIAuthentication
from chatgpt.sessions import HTTPSession, HTTPTLSSession
from chatgpt.utils import get_utc_now_datetime
from .errors import ChatgptError, ChatgptErrorCodes
from tls_client.sessions import TLSClientExeption
from datetime import datetime, timedelta
from pathlib import Path


class Conversation:

    DEFAULT_MODEL_NAME = "text-davinci-002-render"
    DEFAULT_CONFIG_PATH = "config.json"
    DEFAULT_CACHE_PATH = ".chatgpt"
    DEFAULT_ACCESS_TOKEN_SECONDS_TO_EXPIRE = 1800
    DEFAULT_ENVIRONMENT_CHATGPT_HOME = "CHATGPT_HOME"
    __environment = os.environ.get(DEFAULT_ENVIRONMENT_CHATGPT_HOME)
    if __environment:
        __environment = str(Path(__environment).absolute())
        DEFAULT_CACHE_PATH = os.path.join(__environment, DEFAULT_CACHE_PATH)
        DEFAULT_CONFIG_PATH = os.path.join(__environment, DEFAULT_CONFIG_PATH)

    _email: str = None
    _password: str = None

    _access_token: str = None
    _access_token_seconds_to_expire: int = DEFAULT_ACCESS_TOKEN_SECONDS_TO_EXPIRE
    _access_token_expire: datetime = None
    _chatgpt_session_expire: datetime = None

    _conversation_id: str = None
    _parent_message_id: str = None
    _model_name: str = DEFAULT_MODEL_NAME

    _config_path = None
    _cache_file_path = None
    _cache_file = True

    _tls_session: HTTPTLSSession = None
    _openai_authentication: OpenAIAuthentication = None
    _cookies = {}
    _proxy = None
    _timeout = None

    _default_file_config = {
        "conversation_id": None,
        "parent_message_id": None,
        "access_token": None,
        "email": None,
        "password": None,
    }

    def __init__(
        self,
        config_path: str = None,
        access_token: str = None,
        access_token_seconds_to_expire: int = None,
        email: str = None,
        password: str = None,
        conversation_id: str = None,
        parent_message_id: str = None,
        proxy: str = None,
        timeout: int = None,
        cache_file: bool = True,
        cache_file_path: str = None
    ):
        """
        Args:
            config_path (str, optional): Configuration path from where information is going to be loaded. If a path is provided it will load the configuration into the attributes of Conversation. Defaults to None.
            access_token (str, optional): Access token used to authenticate into openai chatbot. Defaults to None.
            email (str): Email address. Defaults to None.
            password (str): Password. Defaults to None.
            conversation_id (str, optional): Conversation id with which the conversation starts. Defaults to None.
            parent_message_id (str, optional): Parent id with which the conversation starts. Defaults to None.
            proxy (str, optional): Proxy to use for requests. Defaults to None.
            timeout (int, optional): Timeout duration in seconds.
        """

        if config_path is not None:
            self.load_config(config_path)

        elif os.path.exists(self.DEFAULT_CONFIG_PATH):
            self.load_config(self.DEFAULT_CONFIG_PATH)

        if cache_file_path is None and self._cache_file_path is None:
            self._cache_file_path = self.DEFAULT_CACHE_PATH

        if os.path.exists(self._cache_file_path):
            self.load_config(self._cache_file_path)

        if access_token is not None:
            self._access_token = access_token

        if email is not None:
            self._email = email

        if password is not None:
            self._password = password

        if self._conversation_id is None:
            self._conversation_id = conversation_id

        if self._parent_message_id is None:
            self._parent_message_id = parent_message_id

        if cache_file is False:
            self._cache_file = False

        if proxy is not None:
            self._proxy = proxy

        if timeout is not None:
            self._timeout = timeout

        if access_token_seconds_to_expire is not None:
            self._access_token_seconds_to_expire = access_token_seconds_to_expire

        self._tls_session = HTTPTLSSession(
            timeout=self._timeout, proxy=self._proxy, cookies=self._cookies)

        self._session = HTTPSession(
            timeout=self._timeout, proxy=self._proxy, cookies=self._cookies)

        self._openai_authentication = OpenAIAuthentication(self._tls_session)

    def __remove_none_values(self, d):
        if not isinstance(d, dict):
            return d
        new_dict = {}
        for k, v in d.items():
            if v is not None:
                new_dict[k] = self.__remove_none_values(v)
        return new_dict

    def _set_access_token_expiration(self, seconds: int = None):
        """Set an expiration time for the access_token..

        Args:
            days (int): Days for token expiration.
        """
        if seconds is None:
            seconds = self._access_token_seconds_to_expire
        self._access_token_expire = get_utc_now_datetime() + timedelta(seconds=seconds)

    def _process_chatgpt_session(self, session_info):
        if session_info is not None and "accessToken" in session_info:
            self._access_token = session_info["accessToken"]
            self._cookies = self._tls_session.cookies
            if "." in session_info["expires"]:
                session_info["expires"] = session_info["expires"].split(".")[
                    0] + "+00:00"
            self._chatgpt_session_expire = datetime.fromisoformat(
                session_info["expires"])
            self._set_access_token_expiration()
            self.write_cache()
            return session_info
        raise ChatgptError("Failed obtaining the access token. Please retry.",
                           ChatgptErrorCodes.LOGIN_ERROR)

    def login(self, email, password):
        """Login to the openai and return the token

        Args:
            email (str): Email to login into openai chatgpt
            password (str): Password to login into openai chatgpt
        """
        self._email = email
        self._password = password
        session_info = self._openai_authentication.login(email, password)
        return self._process_chatgpt_session(session_info)

    def get_session(self):
        """Get chatgpt actual session
        """
        session_info = self._openai_authentication.get_session()
        return self._process_chatgpt_session(session_info)

    def load_config(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Load Conversation attributes by reading from a file

        Args:
            config_path (str, optional): Name of the file from where to read attributes from. Defaults to config.json.

        """

        if config_path is None:
            config_path = self.DEFAULT_CONFIG_PATH
        if os.path.exists(config_path):
            self._config_path = config_path
            try:
                config = {}
                with open(config_path, "r") as f:
                    config.update(json.load(f))

                for key, value in config.items():
                    if value is not None:
                        if key == "access_token_expiration":
                            self._access_token_expire = datetime.fromisoformat(
                                value)
                        elif key == "chatgpt_session_expire":
                            self._chatgpt_session_expire = datetime.fromisoformat(
                                value)
                        elif hasattr(self, "_{}".format(key)):
                            setattr(self, "_{}".format(key), value)

                return config

            except Exception as e:
                raise ChatgptError("Error loading the configuration file in \"{}\"".format(self._config_path),
                                   ChatgptErrorCodes.CONFIG_FILE_ERROR) from e

    def write_cache(self, cache_path: str = None):
        """Write the conversation attributes inside a file.

        Args:
            cache_path (str, optional): Path where to write the data for caching purposes. Defaults to .chatgpt.
        """

        if self._cache_file and self._cache_file_path is not None:

            if cache_path is not None:
                self._cache_file_path = cache_path
            try:
                access_token_expiration = None
                chatgpt_session_expiration = None
                if self._access_token_expire is not None:
                    access_token_expiration = self._access_token_expire.isoformat()
                if self._chatgpt_session_expire is not None:
                    chatgpt_session_expiration = self._chatgpt_session_expire.isoformat()

                config = {
                    "conversation_id": self._conversation_id,
                    "parent_message_id": self._parent_message_id,
                    "cookies": self._cookies,
                    "access_token": self._access_token,
                    "access_token_expiration": access_token_expiration,
                    "chatgpt_session_expire": chatgpt_session_expiration
                }
                with open(self._cache_file_path, "w") as f:
                    json.dump(config, f, indent=4)

            except Exception as e:
                raise ChatgptError("Error writing the configuration file",
                                   ChatgptErrorCodes.CONFIG_FILE_ERROR) from e

    def stream(self, message: List[str], retry_on_401: bool = True, only_new_characters: bool = True):
        """Generator that allows you to retrieve messages as you are receiving them.

        Args:
            message (List[str]): Message or list of messages to send to the server.
            retry_on_401 (bool, optional): Retry login if it fails. Defaults to True.

        Yields:
            str: The text of the message as you are receiving it.
        """
        stream_text_result = ""
        chunk_buffer = ""
        response = self.chat(message, retry_on_401, True, True)
        for chunk in response.iter_content(chunk_size=1024):
            chunk_buffer += chunk.decode("utf-8").replace("data: ", "")
            chunk_arr = chunk_buffer.split("}\n\n")
            if not chunk_arr[-1].endswith("}\n\n"):
                chunk_buffer = chunk_arr[-1]
            len_arr = len(chunk_arr)

            if len_arr > 1:
                if chunk_arr[0] == "[DONE]":
                    break
                try:
                    for i in range(0, len_arr - 1):
                        data = json.loads(chunk_arr[i] + "}")
                        message = data["message"]
                        parts = message["content"]["parts"]
                        self._parent_message_id = message["id"]
                        self._conversation_id = data["conversation_id"]
                        if parts:
                            if only_new_characters:
                                yield parts[0].replace(stream_text_result, "")
                            else:
                                yield parts[0]
                            stream_text_result = parts[0]
                except Exception as e:
                    pass
        self.write_cache()
        return

    def chat(self, message: List[str], retry_on_401: bool = True, direct_response: bool = False, stream=False):
        """Send a message and wait for the server to fully answer to return the message.

        Args:
            message (List[str]): Message or list of messages to send to the server.
            retry_on_401 (bool, optional): Retry login if it fails. Defaults to True.
            direct_response (bool, optional): Return the response of request instead of the parsed message. Defaults to False.
            stream (bool, optional): Execute chat with stream. Note that you will be better off by using stream since it does the processing for you. Defaults to False.
        """
        if self._parent_message_id is None:
            self._parent_message_id = str(uuid())

        if isinstance(message, str):
            message = [message]
        try:
            if self._access_token_expire is not None:
                if self._access_token_expire < get_utc_now_datetime() and self._chatgpt_session_expire > get_utc_now_datetime():
                    self.get_session()

            if self._access_token is None:
                if self._cookies and self._chatgpt_session_expire:
                    if self._chatgpt_session_expire > get_utc_now_datetime():
                        self.get_session()

            if self._access_token is None and self._email and self._password:
                self.login(self._email, self._password)

            if self._access_token is None:
                raise ChatgptError(
                    "No access token. Please, provide an access_token or email and password through the constructor/config file.", ChatgptErrorCodes.INVALID_ACCESS_TOKEN)

            self._message_id = str(uuid())

            url = "https://chat.openai.com/backend-api/conversation"
            payload = {
                "action": "next",
                "messages": [
                    {
                        "id": self._message_id,
                        "role": "user",
                        "content": {
                                "content_type": "text",
                                "parts": message
                        }
                    }
                ],
                "conversation_id": self._conversation_id,
                "parent_message_id": self._parent_message_id,
                "model": self._model_name
            }
            headers = {
                "Authorization": "Bearer {}".format(self._access_token),
                "Content-Type": "application/json",
            }
            payload = json.dumps(self.__remove_none_values(payload))

            response = self._session.request(
                "POST", url, data=payload, headers=headers, stream=stream)
            if direct_response:
                return response

            payload = response.text
            last_item = payload.split(("data:"))[-2]
            result = json.loads(last_item)
            self._parent_message_id = self._message_id
            self._conversation_id = result["conversation_id"]
            self.write_cache()
            text_items = result["message"]["content"]["parts"]
            text = "\n".join(text_items)
            postprocessed_text = text.replace(r"\n+", "\n")
            return postprocessed_text

        except HTTPError as ex:
            exception_message = "Unknown error"
            exception_code = ChatgptErrorCodes.UNKNOWN_ERROR
            error_code = ex.response.status_code
            reason = ex.response.content
            if error_code in [401, 409]:
                self._access_token = None
                if retry_on_401:
                    if (self._email and self._password):
                        self.login(self._email, self._password)
                        return self.chat(message, False)
                exception_message = "Please, provide a new access_token through the constructor, by loading the configuration file with a proper access_token or instead, you can provide an email and password."
                exception_code = ChatgptErrorCodes.INVALID_ACCESS_TOKEN

            elif error_code == 403:
                exception_message = str(reason).split(
                    "h2>")[1].split("<")[0]

            elif error_code == 500:
                exception_message = reason

            else:
                try:
                    exception_message = json.loads(reason)["detail"]
                    if error_code == 429:
                        exception_message = exception_message + \
                            ". You may need to reset the actual conversation."
                except ValueError:
                    exception_message = reason

        except ChatgptError as ex:
            exception_message = ex.message
            exception_code = ex.code
            if exception_code == ChatgptErrorCodes.SESSION_ERROR:
                self._chatgpt_session_expire = get_utc_now_datetime()
                self._tls_session._cookies = {}
                self._cookies = {}
                self._session._cookies = {}
                self._access_token = None
                self.write_cache()
                return self.chat(message, False, direct_response=direct_response, stream=stream)
            elif (exception_code == ChatgptErrorCodes.LOGIN_ERROR or exception_code == ChatgptErrorCodes.TIMEOUT_ERROR) and retry_on_401:
                return self.chat(message, False, direct_response=direct_response, stream=stream)

        except TLSClientExeption as ex:
            exception_message = str(ex)
            exception_code = ChatgptErrorCodes.TIMEOUT_ERROR

        except Exception as e:
            exception_message = str(e)
            exception_code = ChatgptErrorCodes.UNKNOWN_ERROR

        raise ChatgptError(
            exception_message, exception_code)

    def reset(self):
        """Reset the conversation
        """
        self._message_id = None
        self._parent_message_id = None
        self._conversation_id = None
        self.write_cache()

    def clean_auth(self):
        """Clean the current authentication information
        """
        self._access_token = None
        self._cookies = None
        self._access_token = None
        self._chatgpt_session_expire = None
        self._access_token_expire = None
        self.write_cache()
