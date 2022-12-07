#!/usr/bin/env python
# -*- coding: utf-8 -*-
from chatgpt import Conversation


def main():
    conversation = Conversation()

    while True:
        message = input('> ').lower().strip()

        if not message:
            continue

        if message == 'exit':
            break

        elif message == 'reset':
            conversation.reset()
            continue

        elif message == 'clear':
            print('\033c', end='')
            continue

        print(conversation.chat(message), end='\n\n')


if __name__ == '__main__':
    main()
