#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from typing import List
import requests
import tls_client

import urllib.parse
from requests import HTTPError
from .errors import CallError
from uuid import uuid4 as uuid
from urllib.error import HTTPError as UrllibHTTPError


class OpenAIAuthentication():

    def __init__(self):
        self.session = tls_client.Session(client_identifier="chrome_107")

    def _update_headers(self):
        pass

    def _request(self, *args, headers={}, **kwargs):
        send_headers = {
            "Host": "ask.openai.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            'Referer': 'https://chat.openai.com/'
        }
        send_headers.update(headers)
        response = self.session.execute_request(
            *args, headers=send_headers, **kwargs)
        if response.status_code == 200:
            return response
        else:
            raise UrllibHTTPError(args[1], response.status_code,
                                  response.text, response.headers, None)

    def _request_authorize(self, url: str):
        try:
            response = self._request("GET", url)
        except UrllibHTTPError as e:
            if e.code == 302:
                return str(e).split("state=")[1].split("\">")[0]
            else:
                raise e
        raise UrllibHTTPError(url, 200, "Bad authorize request",
                              response.headers, None)

    def _request_signin(self, csrfToken: dict):
        payload = "callbackUrl=%2F&csrfToken={}&json=true".format(csrfToken)

        response = self._request("POST", "https://chat.openai.com/api/auth/signin/auth0?prompt=login",
                                 headers={
                                     'Host': 'ask.openai.com',
                                     'Origin': 'https://chat.openai.com',
                                     'Content-Length': '100',
                                     'Content-Type': 'application/x-www-form-urlencoded',
                                 },
                                 data=payload)
        return response.json()

    def _request_csrf(self):
        response = self._request(
            "GET", "https://chat.openai.com/api/auth/csrf",)
        return response.json()

    def _request_login(self):
        response = self._request("GET", "https://chat.openai.com/auth/login", headers={
            'Host': 'auth0.openai.com',
        })
        return response

    def _request_login_identifier(self, state: str):
        url = "https://auth0.openai.com/u/login/identifier?state={}".format(
            state)
        response = self._request("GET", url, headers={
            'Host': 'auth0.openai.com',
        })
        if "alt=\"captcha\"" in response.text:
            raise UrllibHTTPError(
                url, 400, "Captcha needed", response.headers, None)
        return state

    def _request_login_identifier_post(self, state, email):
        try:
            url = "https://auth0.openai.com/u/login/identifier?state={}".format(
                state)

            email = urllib.parse.quote_plus(email)
            payload = "state={}&username={}&js-available=false&webauthn-available=true&is-brave=false&webauthn-platform-available=true&action=default".format(
                state, email)

            response = self._request("POST", url, headers={
                'Host': 'auth0.openai.com',
                "Origin": "https://auth0.openai.com",
                "Referer": url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }, data=payload)

        except UrllibHTTPError as e:
            if e.code == 302:
                return state
            else:
                raise e
        raise UrllibHTTPError(url, 200, "Bad authorize request",
                              response.headers, None)

    def _request_login_password(self, state, email: str, password: str):

        url = "https://auth0.openai.com/u/login/password?state={}".format(
            state)
        email = urllib.parse.quote_plus(email)
        password = urllib.parse.quote_plus(password)
        payload = "state={}&username={}&password={}&action=default".format(
            state, email, password)

        try:
            response = self._request("POST", url, headers={
                'Host': 'auth0.openai.com',
                "Origin": "https://auth0.openai.com",
                "Referer": url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }, data=payload)
        except UrllibHTTPError as e:
            if e.code == 302:
                return str(e).split("state=")[1].split("\">")[0]
            else:
                raise e
        raise UrllibHTTPError(url, 200, "Bad authorize request",
                              response.headers, None)

    def _request_authorize_access_token(self, state, new_state):
        response = self._request("GET", "https://auth0.openai.com/authorize/resume?state={}".format(
            new_state), headers={
            "Referer": "https://auth0.openai.com/u/login/password?state={}".format(state),
        }, allow_redirects=True)
        return response.cookies.get("__Secure-next-auth.session-token")

    def get_session(self):
        response = self._request(
            "GET", "https://chat.openai.com/api/auth/session")
        return response.json()

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

        except UrllibHTTPError as err:
            print(str(err))


class Conversation:
    DEFAULT_MODEL_NAME = 'text-davinci-002-render'

    _access_token: str = None
    _conversation_id: str = None
    _parent_message_id: str = None
    _email: str = None
    _password: str = None
    _openai_authentication = None

    def __init__(
        self,
        model_name: str = None,
        conversation_id: str = None,
        parent_message_id: str = None,
        access_token: str = None,
        config_path: str = None
    ):

        if config_path is not None:
            self.load_config(config_path)

        self._model_name = model_name or self.DEFAULT_MODEL_NAME

        if self._access_token is None:
            self._access_token = access_token

        if self._conversation_id is None:
            self._conversation_id = conversation_id

        if self._parent_message_id is None:
            self._parent_message_id = parent_message_id

        self._message_id = self._parent_message_id
        self._openai_authentication = OpenAIAuthentication()

    def _remove_none_values(self, d):
        if not isinstance(d, dict):
            return d
        new_dict = {}
        for k, v in d.items():
            if v is not None:
                new_dict[k] = self._remove_none_values(v)
        return new_dict

    def login(self, email, password):
        self._email = email
        self._password = password
        session_info = self._openai_authentication.login(email, password)
        if session_info is not None:
            self._access_token = session_info["accessToken"]
        return session_info

    def get_session(self):
        session_info = self._openai_authentication.get_session()
        self._access_token = session_info["accessToken"]
        return session_info

    def load_config(self, config_path: str = None):
        if config_path is None:
            config_path = 'config.json'

        config = {
            "conversation_id": None,
            "parent_message_id": None,
            "access_token": None,
            "email": None,
            "password": None,
        }
        with open(config_path, 'r') as f:
            config.update(json.load(f))

        self._access_token = config['access_token']
        self._conversation_id = config['conversation_id']
        self._parent_message_id = config['parent_message_id']
        self._email = config['email']
        self._password = config['password']

    def chat(self, message: List[str], retry_on_401=True):

        if self._parent_message_id is None:
            self._parent_message_id = str(uuid())

        if isinstance(message, str):
            message = [message]

        if self._access_token is None and self._email and self._password:
            self.login(self._email, self._password)

        self._message_id = str(uuid())
        url = "https://chat.openai.com/backend-api/conversation"
        headers = {
            'Authorization': f'Bearer {self._access_token}',
        }
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

        payload = json.dumps(self._remove_none_values(payload))
        try:

            response = requests.request(
                "POST", url, headers=headers, data=payload)
            response.raise_for_status()
            payload = response.text
            last_item = payload.split(('data:'))[-2]
            result = json.loads(last_item)
            self._parent_message_id = self._message_id
            self._conversation_id = result["conversation_id"]
            text_items = result['message']['content']['parts']
            text = '\n'.join(text_items)
            postprocessed_text = text.replace(r'\n+', '\n')
            return postprocessed_text

        except HTTPError as ex:
            if retry_on_401 and ex.response.status_code in [401]:
                self._access_token = None
                if self._email and self._password:
                    self.login(self._email, self._password)
                    return self.chat(message, False)
            if ex.response.status_code == 403:
                raise CallError(str(ex.response.content).split("h2>")[1].split("<")[0])
            error_message = json.loads(ex.response.text)['detail']
            raise CallError(error_message)

    def reset(self):
        self._message_id = None
        self._parent_message_id = None
        self._conversation_id = None
