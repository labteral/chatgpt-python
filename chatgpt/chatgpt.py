#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import tls_client
import urllib.parse

from typing import List
from uuid import uuid4 as uuid
from urllib.error import HTTPError
from .errors import ChatgptError, ChatgptErrorCodes
from tls_client.sessions import TLSClientExeption


class HTTPSession:
    DEFAULT_TIMEOUT = 120

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self._session = tls_client.Session(client_identifier="chrome_107")
        self._timeout = timeout

    def request(self, *args, headers={}, **kwargs):
        send_headers = {
            "Host": "ask.openai.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://chat.openai.com/"
        }
        send_headers.update(headers)
        response = self._session.execute_request(
            *args, headers=send_headers, timeout_seconds=self._timeout, **kwargs)
        if response.status_code == 200:
            return response
        else:
            raise HTTPError(args[1], response.status_code,
                            response.text, response.headers, None)


class OpenAIAuthentication:

    def __init__(self, session: HTTPSession):
        self.session = session

    def _update_headers(self):
        pass

    def _request_authorize(self, url: str):
        try:
            response = self.session.request("GET", url)
        except HTTPError as e:
            if e.code == 302:
                if "state" in str(e):
                    return str(e).split("state=")[1].split("\">")[0]
            raise e
        raise HTTPError(url, 200, "Bad authorize request",
                        response.headers, None)

    def _request_signin(self, csrfToken: dict):
        payload = "callbackUrl=%2F&csrfToken={}&json=true".format(csrfToken)

        response = self.session.request("POST", "https://chat.openai.com/api/auth/signin/auth0?prompt=login",
                                        headers={
                                            "Host": "ask.openai.com",
                                            "Origin": "https://chat.openai.com",
                                            "Content-Length": "100",
                                            "Content-Type": "application/x-www-form-urlencoded",
                                        },
                                        data=payload)
        return response.json()

    def _request_csrf(self):
        response = self.session.request(
            "GET", "https://chat.openai.com/api/auth/csrf",)
        return response.json()

    def _request_login(self):
        response = self.session.request("GET", "https://chat.openai.com/auth/login", headers={
            "Host": "auth0.openai.com",
        })
        return response

    def _request_login_identifier(self, state: str):
        url = "https://auth0.openai.com/u/login/identifier?state={}".format(
            state)
        response = self.session.request("GET", url, headers={
            "Host": "auth0.openai.com",
        })
        if "alt=\"captcha\"" in response.text:
            raise HTTPError(
                url, 400, "Captcha needed", response.headers, None)
        return state

    def _request_login_identifier_post(self, state, email):
        try:
            url = "https://auth0.openai.com/u/login/identifier?state={}".format(
                state)

            email = urllib.parse.quote_plus(email)
            payload = "state={}&username={}&js-available=false&webauthn-available=true&is-brave=false&webauthn-platform-available=true&action=default".format(
                state, email)

            response = self.session.request("POST", url, headers={
                "Host": "auth0.openai.com",
                "Origin": "https://auth0.openai.com",
                "Referer": url,
                "Content-Type": "application/x-www-form-urlencoded",
            }, data=payload)

        except HTTPError as e:
            if e.code == 302:
                return state
            else:
                raise e
        raise HTTPError(url, 200, "Bad authorize request",
                        response.headers, None)

    def _request_login_password(self, state, email: str, password: str):
        url = "https://auth0.openai.com/u/login/password?state={}".format(
            state)
        email = urllib.parse.quote_plus(email)
        password = urllib.parse.quote_plus(password)
        payload = "state={}&username={}&password={}&action=default".format(
            state, email, password)
        try:
            response = self.session.request("POST", url, headers={
                "Host": "auth0.openai.com",
                "Origin": "https://auth0.openai.com",
                "Referer": url,
                "Content-Type": "application/x-www-form-urlencoded",
            }, data=payload)
        except HTTPError as e:
            if e.code == 302:
                return str(e).split("state=")[1].split("\">")[0]
            else:
                raise e
        raise HTTPError(url, 200, "Bad authorize request",
                        response.headers, None)

    def _request_authorize_access_token(self, state, new_state):
        response = self.session.request("GET", "https://auth0.openai.com/authorize/resume?state={}".format(
            new_state), headers={
            "Referer": "https://auth0.openai.com/u/login/password?state={}".format(state),
        }, allow_redirects=True)
        return response.cookies.get("__Secure-next-auth.session-token")

    def get_session(self):
        try:
            response = self.session.request(
                "GET", "https://chat.openai.com/api/auth/session", headers={
                    "Host": "ask.openai.com",
                    "Referer": "https://chat.openai.com/chat",
                })
            return response.json()
        except HTTPError as e:
            raise ChatgptError(
                "Error getting the session. You may have a wrong access token; try to login again or insert an access_token yourself.",
                ChatgptErrorCodes.LOGIN_ERROR) from e

    def login(self, username, password):
        try:
            self._request_login()
            csrf = self._request_csrf()
            sigin = self._request_signin(csrf["csrfToken"])
            state = self._request_authorize(sigin["url"])
            state = self._request_login_identifier(state)
            state = self._request_login_identifier_post(state, username)
            new_state = self._request_login_password(state, username, password)
            self._request_authorize_access_token(state, new_state)
            return self.get_session()
        except HTTPError as err:
            raise ChatgptError("Login error. Try again or insert the token yourself.",
                               ChatgptErrorCodes.LOGIN_ERROR) from err


class Conversation:
    DEFAULT_MODEL_NAME = "text-davinci-002-render"
    DEFAULT_CONFIG_PATH = "./config.json"

    _access_token: str = None
    _conversation_id: str = None
    _parent_message_id: str = None
    _email: str = None
    _password: str = None
    _model_name: str = DEFAULT_MODEL_NAME
    _session: HTTPSession = None
    _openai_authentication: OpenAIAuthentication = None
    _config_path = None

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
        email: str = None,
        password: str = None,
        conversation_id: str = None,
        parent_message_id: str = None,
        timeout:int = None
    ):
        """
        Args:
            config_path (str, optional): Configuration path from where information is going to be loaded. If a path is provided it will load the configuration into the attributes of Conversation. Defaults to None.
            access_token (str, optional): Access token used to authenticate into openai chatbot. Defaults to None.
            email (str): Email address. Defaults to None.
            password (str): Password. Defaults to None.
            conversation_id (str, optional): Conversation id with which the conversation starts. Defaults to None.
            parent_message_id (str, optional): Parent id with which the conversation starts. Defaults to None.
            timout (int, optional): Timeout duration in seconds.
        """

        if config_path is not None:
            self.load_config(config_path)
        elif os.path.exists(self.DEFAULT_CONFIG_PATH):
            self.load_config(self.DEFAULT_CONFIG_PATH)

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

        self._session = HTTPSession(timeout=timeout)
        self._openai_authentication = OpenAIAuthentication(self._session)

    def __remove_none_values(self, d):
        if not isinstance(d, dict):
            return d
        new_dict = {}
        for k, v in d.items():
            if v is not None:
                new_dict[k] = self.__remove_none_values(v)
        return new_dict

    def login(self, email, password):
        """Login to the openai and return the token

        Args:
            email (str): Email to login into openai chatgpt
            password (str): Password to login into openai chatgpt
        """
        self._email = email
        self._password = password
        session_info = self._openai_authentication.login(email, password)
        if session_info is not None:
            self._access_token = session_info["accessToken"]
        return session_info

    def get_session(self):
        """Get chatgpt actual session
        """
        session_info = self._openai_authentication.get_session()
        self._access_token = session_info["accessToken"]
        self.write_config(self._config_path)
        return session_info

    def load_config(self, config_path: str = DEFAULT_CONFIG_PATH):
        self._config_path = config_path
        try:
            config = {**self._default_file_config}
            with open(config_path, "r") as f:
                config.update(json.load(f))
            self._access_token = config["access_token"]
            self._conversation_id = config["conversation_id"]
            self._parent_message_id = config["parent_message_id"]
            self._email = config["email"]
            self._password = config["password"]
            return config

        except Exception as e:
            raise ChatgptError("Error loading the configuration file in \"{}\"".format(self._config_path),
                               ChatgptErrorCodes.CONFIG_FILE_ERROR) from e

    def write_config(self, config_path: str = DEFAULT_CONFIG_PATH):
        self._config_path = config_path
        try:
            config = {
                **self._default_file_config,
                "access_token": self._access_token,
                "conversation_id": self._conversation_id,
                "parent_message_id": self._parent_message_id,
                "email": self._email,
                "password": self._password
            }
            with open(self._config_path, "w") as f:
                json.dump(config, f, indent=4)

        except Exception as e:
            raise ChatgptError("Error writing the configuration file",
                               ChatgptErrorCodes.CONFIG_FILE_ERROR) from e

    def chat(self, message: List[str], retry_on_401: bool = True):
        if self._parent_message_id is None:
            self._parent_message_id = str(uuid())

        if isinstance(message, str):
            message = [message]

        if self._access_token is None and self._email and self._password:
            self.login(self._email, self._password)

        if self._access_token is None:
            raise ChatgptError(
                "Access token is not provided. Please, provide an access_token through the constructor, by loading the configuration file with a proper access_token or instead, you can provide an email and password.", ChatgptErrorCodes.INVALID_ACCESS_TOKEN)

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
        payload = json.dumps(self.__remove_none_values(payload))
        try:
            response = self._session.request(
                "POST", url, data=payload, headers={
                    "Authorization": "Bearer {}".format(self._access_token),
                    "Content-Type": "application/json",
                })
            payload = response.text
            last_item = payload.split(("data:"))[-2]
            result = json.loads(last_item)
            self._parent_message_id = self._message_id
            self._conversation_id = result["conversation_id"]
            self.write_config(self._config_path)
            text_items = result["message"]["content"]["parts"]
            text = "\n".join(text_items)
            postprocessed_text = text.replace(r"\n+", "\n")
            return postprocessed_text

        except HTTPError as ex:
            exception_message = "Unknown error"
            exception_code = ChatgptErrorCodes.UNKNOWN_ERROR
            error_code = ex.code
            if error_code in [401, 409]:
                self._access_token = None
                if retry_on_401:
                    if self._email and self._password:
                        self.login(self._email, self._password)
                        return self.chat(message, False)
                exception_message = "Please, provide a new access_token through the constructor, by loading the configuration file with a proper access_token or instead, you can provide an email and password."
                exception_code = ChatgptErrorCodes.INVALID_ACCESS_TOKEN

            elif error_code == 403:
                exception_message = str(ex.msg).split(
                    "h2>")[1].split("<")[0]

            elif error_code == 500:
                exception_message = ex.msg

            else:
                try:
                    exception_message = json.loads(ex.msg)["detail"]
                except ValueError:
                    exception_message = ex.msg

        except TLSClientExeption as ex:
            exception_message = str(ex)
            exception_code = ChatgptErrorCodes.TIMEOUT_ERROR

        except Exception as e:
            exception_message = str(e)
            exception_code = ChatgptErrorCodes.UNKNOWN_ERROR

        raise ChatgptError(
            exception_message, exception_code)

    def reset(self):
        self._message_id = None
        self._parent_message_id = None
        self._conversation_id = None
        self.write_config(self._config_path)
