#!/usr/bin/env python
# -*- coding: utf-8 -*-
from chatgpt import Conversation


def main():
    conversation = Conversation()

    while True:
        user_input = input("> ")
        print(conversation.chat(user_input), end="\n\n")


if __name__ == "__main__":
    main()
