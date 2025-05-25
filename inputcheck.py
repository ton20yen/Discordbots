import challonge
import discord

async def chanellid(message, channelid):
    valid_flag = True

    try:
        message.guild.get_channel(channelid)
    except:
        valid_flag = False
    return valid_flag

async def messageid(message, channelid, msgid):
    valid_flag = True

    try:
        poll_massage = await message.member.fetch_message(msgid)
    except:
        valid_flag = False
    return valid_flag

async def challongeid(tournamentid):
    valid_flag = True
    
    try:
        challonge.tournaments.show(tournamentid)
    except:
            valid_flag = False
    return valid_flag
