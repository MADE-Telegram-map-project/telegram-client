import asyncio
# from telethon import events, sync
import telethon
from telethon import functions, types
from telethon.sync import TelegramClient



# # api_hash from https://my.telegram.org, under API Development.
api_id: int = os.environ["API_ID"]
api_hash: str = os.environ["API_HASH"]

name = 'client1'

ch = "latinapopacanski"
# ch = "weirdreparametrizationtrick"
# ch = "bdscience_ru"
ch = 1232476793
client: TelegramClient = None

with TelegramClient(name, api_id, api_hash) as client:
    full = client(functions.channels.GetFullChannelRequest(
        channel=ch
    ))
    # print(full.stringify())

    # participants = client.get_participants(channel_username)
    # print()
    # client.get_stats(entity)
    # client.get_messages(entity)
    # client.iter_messages(entity)

    channel_peer = client.get_peer_id(ch)


    for i, message in enumerate(client.iter_messages(ch)):
        
        # if it's possible TODO
        if True:
            comments = client(
                functions.messages.GetRepliesRequest(
                    peer=channel_peer, 
                    msg_id=message.id, 
                    offset_id=0, 
                    offset_date=None, 
                    add_offset=0,
                    limit=0,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )
            commenters = [(x.id, x.username) for x in comments.users]

        print(message.stringify())
        
        if i == 0:
            break

    # res2 = functions.channels.GetMessagesRequest(channel=ch, id=None)
    # functions.channels.GetParticipantsRequest(channel, filter, offset, limit, hash)
    # functions.messages.


# client = TelegramClient(name, api_id, api_hash)
# client.start()


# print(client.get_me().stringify())

# client.send_message('visknot', 'Hello! Talking to you from Telethon')
# client.send_file('visknot', '/home/mr/Pictures/anm/-9Xuo8-K6Is.jpg')

# client.download_profile_photo('me')
# messages = client.get_messages('visknot')
# messages[0].download_media()

# @client.on(events.NewMessage(pattern='(?i)hi|hello'))
# async def handler(event):
#     await event.respond('Hey!')


# # client.get_messages()

# client.start()
# client.run_until_disconnected()


