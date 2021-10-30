from time import sleep

import pytest

from core.crawler import Crawler
from core.entities import FullChannelData, MediaChannelData, MessageData

ch1 = "latinapopacanski"
ch2 = 1149710531


# @pytest.mark.skip
def test_get_channel_full_and_chat_users(crawler):
    full1 = crawler.get_channel_full(ch1)
    sleep(5)
    full2 = crawler.get_channel_full(ch2)

    assert full1 == full2
    assert isinstance(full1, FullChannelData)
    assert isinstance(full1.linked_chat_id, int)
    assert full1.link == ch1

    users = crawler.get_linked_chat_members(full1.linked_chat_id)

    assert len(users) > 0
    

def test_get_header_media_counts(crawler):
    media = crawler.get_header_media_counts(ch2)
    assert isinstance(media, MediaChannelData)
    assert media.photo > 0
    sleep(1)



def test_get_messages_and_commenters(crawler):
    n_messages = 10
    messages = crawler.get_messages(ch2, n_messages)
    assert len(messages) == n_messages
    assert isinstance(messages[0], MessageData)
    assert messages[0].views > 0
    assert messages[0].message_id > 0
    sleep(2)

    for msg in messages:
        replies, commenters = crawler.get_replies(ch2, msg.message_id)
        sleep(1)

