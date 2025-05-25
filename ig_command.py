import discord
import pandas as pd
import numpy as np
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

poll_massage = ""               # 紅白戦募集文
participants_list = {}          # 参加者リスト
participants_to_team = {}       # 参加者 -> 所属チーム
participants_rank = {}          # 参加者 -> ランク
participants_list_message = []  # 参加者リスト表示メッセージ
endpoll_flag = False            # 参加者募集終了フラグ (True:終了 False:募集中)

# リアクション追加時処理
async def on_reaction_add(team, user):
    global participants_list
    global participants_to_team
    global participants_rank
    global participants_list_message

    user_list = participants_list[str(team)]

    user_list[str(user.display_name).replace('_', '\_')] = False
    participants_to_team[str(user.display_name)] = str(team)
    participants_list[str(team)] = user_list
    participants_rank[str(user.display_name)] = get_user_rank(user.roles)

    await send_participants_list(participants_list_message, participants_list)

    return

# リアクション削除時処理
async def on_reaction_remove(team, user):
    global participants_list
    global participants_to_team
    global participants_rank
    global participants_list_message

    user_list = participants_list[str(team)]

    del user_list[str(user.display_name).replace('_', '\_')]
    del participants_to_team[str(user.display_name)]
    del participants_rank[str(user.display_name)]
    participants_list[str(team)] = user_list

    await send_participants_list(participants_list_message, participants_list)

    return

# リアクション全削除時処理
async def on_reaction_clear():
    global participants_list
    global participants_list_message
    global endpoll_flag

    endpoll_flag = True

    await send_participants_list(participants_list_message, participants_list)

    return

def get_user_rank(roles):
    rank = ""

    for user_role in roles:
        if user_role.id == 1262593475380117514:
            rank = "(優)"
            break
        if user_role.id == 1076311874573975602:
            rank = "(ベ)"
            break
        if user_role.id == 1002737039411785749:
            rank = "(中/復)"
            break
        if user_role.id == 1067415878104256562:
            rank = "(初)"
            break

    return rank

async def send_participants_list(message, participants_list):
    global poll_massage
    global participants_list_message
    global participants_rank
    global endpoll_flag

    # スプレッドシートからデータ取得
    Auth = "" # 公開用に削除済み
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Auth
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
    Client = gspread.authorize(credentials)

    SpreadSheet = Client.open_by_key("") # 公開用に削除済み
    RawData = SpreadSheet.worksheet("シート2")

    if endpoll_flag:
        embed = discord.Embed( # Embedを定義する
                        title="■紅白/対抗戦チームメンバーリスト",
                        color=0x0000ff, # フレーム色指定
                        description="紅白戦の新規エントリーは締め切られました", # Embedの説明文 必要に応じて
                        )
    else:
        embed = discord.Embed( # Embedを定義する
                        title="■紅白/対抗戦チームメンバーリスト",
                        color=0x0000ff, # フレーム色指定
                        description="紅白戦参加希望者はこちらへどうぞ -> " + poll_massage.jump_url, # Embedの説明文 必要に応じて
                        )

    team_num = 1
    for team in participants_list:
        member = ""
        lose_member = ""
        member_num = 0
        for participant in participants_list[team]:
            if participants_list[team][participant]:
                lose_member += "~~" + participant + participants_rank[participant] + "~~" + "\n"
            else:
                member_num += 1
                member += participant +  participants_rank[participant] + "\n"
        RawData.update_cell(4, team_num, member_num)
        team_num += 1
        embed.add_field(name=team+"チーム(残り:" + str(member_num) + "人)", value=member + lose_member)  # フィールドを追加。

    # print("--- test message ---")
    # print(participants_list_message)
    if (len(participants_list_message) == 0):
        # print("--- first loot ---")
        return await message.channel.send(embed=embed)
    elif(len(participants_list_message) == 1):
        # print("--- second loot ---")
        if participants_list_message == message:
            # print("--- edit loot ---")
            for list_message in participants_list_message:
                await list_message.edit(embed=embed)
        else:
            # print("--- send loot ---")
            return await message.channel.send(embed=embed)
    else:
        # print("--- third loot ---")
        if participants_list_message == message:
            for list_message in participants_list_message:
                await list_message.edit(embed=embed)
        else:
            return await message.channel.send(embed=embed)

    return

# コマンド受信時処理
async def call(message, msg):
    global poll_massage
    global participants_list
    global participants_to_team
    global participants_rank
    global participants_list_message
    global endpoll_flag

    if len(msg) <= 2:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="紅白/対抗戦参加者募集メッセージのIDを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)
        return poll_massage

    # channelIDとmsgIDに分割
    ids = []
    ids = msg[2].split('-')

    if len(ids) > 1:
        # 指定されたのが紅白戦参加者募集文
        try:
            # 指定されたchannelIDとmsgIDを元にメッセージを特定
            poll_channel = message.guild.get_channel(int(ids[0]))
            poll_massage = await poll_channel.fetch_message(int(ids[1]))
        except:
            embed = discord.Embed( # Embedを定義する
                                title="■チャンネル/メッセージID指定エラー",
                                color=0xffc800, # フレーム色指定
                                description="指定されたメッセージが見つかりませんでした。以下3点を確認してください。\n①指定したメッセージが存在するチャンネルにbotの閲覧権限があるか\n②IDの指定順が「チャンネルID-メッセージID」になっているか\n③指定したIDがあっているか", # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )
            await message.channel.send(embed=embed)
            return poll_massage

        participants_list = {}

        # リアクション者を全員参加者として登録
        for poll_reaction in poll_massage.reactions:
            user_list = {}
            async for user in poll_reaction.users():
                if not(user.bot):
                    user_list[str(user.display_name).replace('_', '\_')] = False
                    participants_to_team[str(user.display_name)] = str(poll_reaction)
                    participants_rank[str(user.display_name)] = get_user_rank(user.roles)
            participants_list[str(poll_reaction)] = user_list

        endpoll_flag = False
        participants_list_message.append(await send_participants_list(message, participants_list))

    else :
        # 指定されたのが死亡者
        print(participants_to_team[ids[0]])
        participants_list[participants_to_team[ids[0]]][ids[0]] = ~participants_list[participants_to_team[ids[0]]][ids[0]]
        # print(participants_list)
        try:
            if participants_list_message != None:
                await send_participants_list(participants_list_message, participants_list)
            else:
                embed = discord.Embed( # Embedを定義する
                        title="■紅白/対抗戦未開始エラー",
                        color=0xffc800, # フレーム色指定
                        description="紅白戦が開始されていません。\n先に紅白戦参加者募集文のIDを指定してください", # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
                await message.channel.send(embed=embed)
        except:
            embed = discord.Embed( # Embedを定義する
                    title="■参加者指定エラー",
                    color=0xffc800, # フレーム色指定
                    description="指定された参加者が見つかりませんでした。\n参加者名があっているか確認してください", # Embedの説明文 必要に応じて
                    url="" # これを設定すると、タイトルが指定URLへのリンクになる
                    )

    return poll_massage

