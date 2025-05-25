import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
from google.cloud import storage
import os
import discord

async def edit_progress_message(compleat_num, estimate_num, progress_message):
    compleat_percent = float(compleat_num / estimate_num) * 100
    progress = "進捗率：" + str(compleat_percent) + "%"

    if compleat_percent == 100:
        progress_bar = "■■■■■■■■■■"
    elif compleat_percent >= 90:
        progress_bar = "■■■■■■■■■□"
    elif compleat_percent >= 80:
        progress_bar = "■■■■■■■■□□"
    elif compleat_percent >= 70:
        progress_bar = "■■■■■■■□□□"
    elif compleat_percent >= 60:
        progress_bar = "■■■■■■□□□□"
    elif compleat_percent >= 50:
        progress_bar = "■■■■■□□□□□"
    elif compleat_percent >= 40:
        progress_bar = "■■■■□□□□□□"
    elif compleat_percent >= 30:
        progress_bar = "■■■□□□□□□□"
    elif compleat_percent >= 20:
        progress_bar = "■■□□□□□□□□"
    elif compleat_percent >= 10:
        progress_bar = "■□□□□□□□□□"
    else:
        progress_bar = "□□□□□□□□□□"


    embed = discord.Embed( # Embedを定義する
                        title="■ランバトロール付与開始",
                        color=0x0000ff, # フレーム色指定
                        description="ロール付与を開始します。しばらくお待ちください……\n" + progress + "\n" + progress_bar, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    await progress_message.edit(embed=embed)

    return

async def call(message, msg):
    Auth = "" # 公開用に削除済み
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Auth
    # storage_client = storage.Client()
    # buckets = list(storage_client.list_buckets())
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
    Client = gspread.authorize(credentials)

    SpreadSheet = Client.open_by_key(msg[2])
    RawData = SpreadSheet.worksheet("ロール付与者一覧")

    champion_rank_role = message.guild.get_role(1262593475380117514) # 月間優勝者ロール
    high_rank_role = message.guild.get_role(1090447764200095784) # 上位者ロール
    low_rank_role = message.guild.get_role(1090448284381876264)  # 参加者ロール

    target_name_list = []
    target_role = ""

    progress_bar = "□□□□□□□□□□"
    embed = discord.Embed( # Embedを定義する
                        title="■ランバトロール付与開始",
                        color=0x0000ff, # フレーム色指定
                        description="ロール付与を開始します。しばらくお待ちください……\n進捗率：0%\n" + progress_bar, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    progress_message = await message.channel.send(embed=embed)

    estimate_num = len(RawData.get_all_values())
    compleat_num = 0

    print("--- ランクマロール付与開始 ---")
    for target_data in RawData.get_all_values():
        compleat_num += 1
        add_roles = []
        if int(target_data[1]) > 4:
            if compleat_num == 1:
                add_roles.extend([high_rank_role, low_rank_role, champion_rank_role])
            else:
                add_roles.extend([high_rank_role, low_rank_role])
        else:
            add_roles.append(low_rank_role)

        target_members = await message.guild.query_members(target_data[0])

        for target_member in target_members:
            if target_member.name == target_data[0]:
                print(target_member.display_name)
                target_name_list.append(target_member.display_name)
                if len(add_roles) == 3:
                    target_role += "月間優勝者/上位者/参加者\n"
                elif len(add_roles) == 2:
                    target_role += "上位者/参加者\n"
                else:
                    target_role += "参加者\n"

                for add_role in add_roles:
                    await target_member.add_roles(add_role)
                break
        await edit_progress_message(compleat_num, estimate_num, progress_message)

    print("--- ランクマロール付与完了 ---")

    target_name = ''
    for name in target_name_list:
        target_name += name.replace('_', '\_') + "\n"

    description_word = "ロール付与が完了しました。付与した情報は下記の通りです。" + "\n"
    description_word += "人数：" + str(len(target_name_list))

    embed = discord.Embed( # Embedを定義する
                        title="■ロール付与完了",
                        color=0x0000ff, # フレーム色指定
                        description=description_word, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    
    embed.add_field(name="表示名",value=target_name) # フィールドを追加
    embed.add_field(name="付与ロール",value=target_role)  # フィールドを追加

    await message.channel.send(embed=embed)

    return