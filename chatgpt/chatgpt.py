#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uuid import uuid4 as uuid
import json
import requests
from .errors import CallError


class Conversation:
    DEFAULT_MODEL_NAME = 'text-davinci-002-render'

    def __init__(
        self,
        model_name: str = None,
        conversation_id: str = None,
        parent_message_id: str = None,
        access_token: str = None,
    ):
        self.load_config()

        self._model_name = model_name or self.DEFAULT_MODEL_NAME

        if self._access_token is None:
            self._access_token = access_token

        if self._conversation_id is None:
            self._conversation_id = conversation_id

        if self._first_parent_message_id is None:
            self._first_parent_message_id = parent_message_id
        self._message_id = self._first_parent_message_id

    def load_config(self, config_path: str = None):
        if config_path is None:
            config_path = 'config.json'

        with open(config_path, 'r') as f:
            config = json.load(f)

        self._access_token = config['access_token']
        self._conversation_id = config['conversation_id']
        self._first_parent_message_id = config['parent_message_id']

    def chat(self, message: str):
        self._parent_message_id = self._message_id
        self._message_id = str(uuid())

        url = "https://chat.openai.com/backend-api/conversation"

        payload = json.dumps(
            {
                "action": "next",
                "messages": [
                    {
                        "id": self._message_id,
                        "role": "user",
                        "content": {
                            "content_type": "text",
                            "parts": [message]
                        }
                    }
                ],
                "conversation_id": self._conversation_id,
                "parent_message_id": self._parent_message_id,
                "model": self._model_name
            }
        )
        headers = {
            'Authorization': f'Bearer {self._access_token}',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        payload = response.text

        try:
            last_item = payload.split(('data:'))[-2]
            text_items = json.loads(last_item)['message']['content']['parts']
            text = '\n'.join(text_items)
            postprocessed_text = text.replace(r'\n+', '\n')
            return postprocessed_text
        except IndexError:
            error_message = json.loads(payload)['detail']
            raise CallError(error_message)

    def reset(self):
        self._message_id = self._first_parent_message_id
