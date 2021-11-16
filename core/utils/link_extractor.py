import re
from typing import List, Set, Tuple, Union
from sqlalchemy.orm import relation

from telethon.helpers import TotalList
from telethon.tl.patched import Message
from telethon.tl.types import (
    PeerChannel,
    MessageMediaWebPage,
    MessageEntityTextUrl,
    MessageEntityMention,
    MessageEntityUrl
)

from core.entities import ChannelRelationData
from core.utils.web import extract_subscribers

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
@another_bot 
@kposffffffffffffkposffffffffffffdss
@ffkaab
@endless'''
# usernames https://core.telegram.org/method/account.checkUsername
# Accepted characters: A-z (case-insensitive), 0-9 and underscores.
# Length: 5-32 characters.

accepted_username = "[A-Za-z0-9_]{5,32}"
link_pattern = re.compile("(t.me/{})".format(accepted_username))
username_pattern = re.compile("[^A-Za-z0-9_](@{})".format(accepted_username))


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
            # print(repr(e))
            pass
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
        # print(repr(e))
        pass
    return usernames


def extract_usernames(
    channel_id: int,
    channel_about: str, 
    messages: TotalList) -> Tuple[List[ChannelRelationData], int, int, int]:
    """ main func to release all neighbour channels """
    head_usernames = set(extract_usernames_from_text(channel_about))
    direct_usernames = set()
    fwd_ids = set()

    for msg in messages:
        fwd_channel = extract_fwd_channel(msg)
        if fwd_channel is not None:
            fwd_ids.add(fwd_channel)

        ent_usernames = extract_usernames_from_entities(msg)
        med_usernames = extract_usernames_from_media(msg)

        for uname in ent_usernames:
            direct_usernames.add(uname)
        for uname in med_usernames:
            direct_usernames.add(uname)
    
    relations = []
    for uname in head_usernames:
        if extract_subscribers(uname) != -1:  # check that username is channel
            relations.append(ChannelRelationData(
                channel_id,
                to_channel_link=uname,
                type="header", 
            ))
    for uname in direct_usernames:
        if extract_subscribers(uname) != -1:  # check that username is channel
            relations.append(ChannelRelationData(
                channel_id,
                to_channel_link=uname,
                type="direct", 
            ))
    for idx in fwd_ids:
        relations.append(ChannelRelationData(
            channel_id,
            to_channel_id=idx,
            type="forward", 
        ))

    return relations, len(head_usernames), len(direct_usernames), len(fwd_ids)


if __name__ == "__main__":
    unames = extract_usernames_from_text(about)
    print(unames)

    rels, _, _, _ = extract_usernames(1149710531, about, [])
    for r in rels:
        print(r)