#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from chatgpt import Conversation

conversation = Conversation()

# Python generator to stream the message in chunks.
# the chunk give you a new part of the final message.
for chunk in conversation.stream("We are going to start a conversation. I will speak English and you will speak Portuguese."):
    # print chunk without line break
    print(chunk, end="")
    # flush terminal output
    sys.stdout.flush()

# this conversation chat instead is going to wait until the response is completely received.
print(conversation.chat("What's the color of the sky?"))

# The AI will forget it was speaking Portuguese
conversation.reset()
print(conversation.chat("What's the color of the sun?"))
