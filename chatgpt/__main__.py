#!/usr/bin/env python
# -*- coding: utf-8 -*-
from chatgpt import Conversation


def main():
    conversation = Conversation()

    while True:
        message = input('> ')
        if message.lower().strip() == 'exit':
            break
        print(conversation.chat(message), end='\n\n')


if __name__ == '__main__':
    main()
