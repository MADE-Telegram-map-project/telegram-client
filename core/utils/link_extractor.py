import re
from typing import List, Set, Union

from telethon.helpers import TotalList
from telethon.tl.patched import Message
from telethon.tl.types import (
    PeerChannel,
    MessageMediaWebPage,
    MessageEntityTextUrl,
    MessageEntityMention,
    MessageEntityUrl
)


about = '''
Такую латынь ты по учебникам не выучишь.\n
Канал переводчика интерфейсов ВК и Телеграма на латынь.\n\n
Автор: @llidd\n\n
Сенат заседает здесь: https://t.me/joinchat/xIaBoGI13iowNDFi\n\n
Столица: vk.com/latinapopacanski\n\n
Поддержать: 5536 9138 7636 6499'

Разместить рекламу: @Textodromo_HQ_bot — Big Data Science channel
Разместить вакансию: @TD_vacancy_bot

Найти копирайтера, редактора: @textodromo
Таргетолога, маркетолога: @reklamodromo

Работаем с юрлицами!

Big Data Science [RU] — канал о жизни Data Science.
Для сотрудничества: a.chernobrovov@gmail.com
🌏 — https://t.me/bdscience — Big Data Science channel (english version)
💼 — https://t.me/bds_job — channel about Data Science jobs and career

@RandomBot
'''

endpoints = "[\n\\s\t\\.\\,\\!\\?:;'\"/]"
username_pattern = re.compile("{}(@.+?){}".format(endpoints, endpoints))
link_pattern = re.compile("(t.me/.+?){}".format(endpoints))


def extract_fwd_channel(msg: Message) -> Union[int, None]:
    fwd_channel_id = None
    if msg.fwd_from is not None:
        if isinstance(msg.fwd_from.from_id, PeerChannel):
            fwd_channel_id = msg.fwd_from.from_id.channel_id

    return fwd_channel_id


def extract_usernames_from_text(text: str) -> List[str]:
    usernames_raw = re.findall(username_pattern, text)
    usernames = [
        u.lstrip("@") for u in usernames_raw
        if not u.lower().endswith("bot")]

    links_raw = re.findall(link_pattern, text)
    links = [l.lstrip("t.me/") for l in links_raw if "joinchat" not in l]

    potential_channels = usernames + links
    return potential_channels


def extract_usernames_from_entities(msg: Message) -> List[str]:
    text = msg.raw_text
    usernames = []
    if msg.entities is None:
        return usernames

    for ent in msg.entities:
        try:
            if isinstance(ent, MessageEntityMention):
                username = text[ent.offset + 1:ent.offset + ent.length]
                usernames.append(username)

            elif isinstance(ent, MessageEntityTextUrl):
                links = extract_usernames_from_text(ent.url + ' ')
                if len(links) == 1:
                    usernames.append(links[0])

            elif isinstance(ent, MessageEntityUrl):
                url = text[ent.offset:ent.offset + ent.length] + ' '
                links = extract_usernames_from_text(url)
                if len(links) == 1:
                    usernames.append(links[0])
        except Exception as e:
            print(repr(e))
    return usernames


def extract_usernames_from_media(msg: Message) -> List[str]:
    usernames = []
    if msg.media is None:
        return usernames
    try:
        if isinstance(msg.media, MessageMediaWebPage):
            d = msg.media.to_dict()
            if msg.media.webpage.type == "telegram_channel":
                url = msg.media.webpage.url + ' '
                links = extract_usernames_from_text(url)
                if len(links) == 1:
                    usernames.append(links[0])
    except Exception as e:
        print(repr(e))
    return usernames


def extract_usernames(channel_about: str, messages: TotalList) -> Set[str]:
    """ main func to release all neighbour channels """
    usernames = set(extract_usernames_from_text(channel_about))
    for msg in messages:
        fwd_channel = extract_fwd_channel(msg)
        if fwd_channel is not None:
            usernames.add(fwd_channel)

        ent_usernames = extract_usernames_from_entities(msg)
        med_usernames = extract_usernames_from_media(msg)

        for uname in ent_usernames:
            usernames.add(uname)
        for uname in med_usernames:
            usernames.add(uname)

    return usernames


if __name__ == "__main__":
    extract_usernames_from_text(about)
