import discord
import challonge
from challonge import api
import concurrent.futures
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import storage
import os

async def edit_progress_message(task_state, progress_message):
    task_message = "トーナメント確認/初期化：" + task_state[0]
    task_message += "\n" + "参加者確認：" + task_state[1]
    task_message += "\n" + "トーナメント表作成：" + task_state[2]

    embed = discord.Embed( # Embedを定義する
                        # title=this_tournament['name'],
                        color=0x0000ff, # フレーム色指定
                        description="■参加者登録開始", # Embedの説明文 必要に応じて
                        # url="https://challonge.com/ja/" + str(tournament) # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    embed.add_field(name="", value='参加者登録を開始します……\n--- 登録作業中 しばらくお待ちください ---\n'+task_message)  # フィールドを追加。
    await progress_message.edit(embed=embed)

    return

def remove_invalid_tournments(tournament):
    valid_flag = True

    # 有効なトナメのみ登録対象とするための下準備
    try:
        api.fetch("DELETE", "tournaments/%s/participants/%s" % (tournament, 'clear'))
    except:
        try:
            challonge.tournaments.reset(tournament)
            api.fetch("DELETE", "tournaments/%s/participants/%s" % (tournament, 'clear'))
        except:
            valid_flag = False

    return valid_flag, tournament

def participant_entry(user, tournament_id):
    challonge.participants.create(tournament_id, user.display_name, misc=str(user))

def create_tournments(user, tournament):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(participant_entry, arg, tournament) for arg in user[tournament]]

    this_tournament = challonge.tournaments.show(tournament)

    registration_massage =  '参加者登録が完了しました'
    registration_massage += '\n' + '今回の参加者は' + str(this_tournament['participants_count']) + '名です'
    registration_massage += '\n' + '引き続き勝利報告受付を開始する場合は!sコマンドを使用してください'

    embed = discord.Embed( # Embedを定義する
                        title=this_tournament['name'],
                        color=0x0000ff, # フレーム色指定
                        description="■参加者登録完了", # Embedの説明文 必要に応じて
                        url="https://challonge.com/ja/" + str(tournament) # これを設定すると、タイトルが指定URLへのリンクになる
                        )

    embed.add_field(name="", value=registration_massage)  # フィールドを追加。

    print('--- 参加者登録完了 ---')
    return embed

async def call(message, msg):
    if len(msg) != 2:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="引数の数が誤っています。botへのメンションとコマンドのみにしてください。", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)
        return False

    # スプレッドシートからデータ取得
    Auth = "add-rankmatch-role-a607f1ee6806.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Auth
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
    Client = gspread.authorize(credentials)

    SpreadSheet = Client.open_by_key("") # 公開用に削除済み
    RawData = SpreadSheet.worksheet("登録用シート")
    # print(RawData.get_all_values())

    sheet_all_values = RawData.get_all_values()

    tournaments = []

    first_flag = True
    for sheet_values in sheet_all_values:
        # print(sheet_values)
        if first_flag:
            first_flag = False
            continue
        tournaments.append(sheet_values[0])

    task_state = []
    task_state.extend(["実行中……","未完了","未完了"])

    task_message = "トーナメント確認/初期化：" + task_state[0]
    task_message += "\n" + "参加者確認：" + task_state[1]
    task_message += "\n" + "トーナメント表作成：" + task_state[2]

    embed = discord.Embed( # Embedを定義する
                        # title=this_tournament['name'],
                        color=0x0000ff, # フレーム色指定
                        description="■参加者登録開始", # Embedの説明文 必要に応じて
                        # url="https://challonge.com/ja/" + str(tournament) # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    embed.add_field(name="", value='参加者登録を開始します……\n--- 登録作業中 しばらくお待ちください ---\n'+task_message)  # フィールドを追加。
    progress_message = await message.channel.send(embed=embed)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        remove_invalid_futures = [executor.submit(remove_invalid_tournments, tournament) for tournament in tournaments]
        for remove_invalid_future in concurrent.futures.as_completed(remove_invalid_futures):
            valid_flag, t_id = remove_invalid_future.result()

            if valid_flag == False:
                tournaments.remove(t_id) # 指定ミスってるトナメは登録対象外として処理
                error_embed = discord.Embed( # Embedを定義する
                        title="■トーナメント指定エラー",
                        color=0xffc800, # フレーム色指定
                        description="指定されたトーナメントが見つかりませんでした。\nIDがあっているか確認してください", # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
        
                error_embed.add_field(name="指定されたトーナメントID", value=t_id)  # フィールドを追加。
                await message.channel.send(embed=error_embed)

                count = 0
                for sheet_values in sheet_all_values:
                    # print(sheet_values)
                    if sheet_values[0] == t_id:
                        sheet_all_values.pop(count)
                        break
                    count += 1

    print(sheet_all_values)
    print('--- トーナメントの選別 & 初期化完了 ---')

    task_state[0] = "完了"
    task_state[1] = "実行中……"
    await edit_progress_message(task_state, progress_message)

    # シートから参加者を抽出
    users = []
    all_users = []
    not_found_users = []

    first_flag = True

    for sheet_values in sheet_all_values:
        # print(sheet_values)
        if first_flag:
            first_flag = False
            continue
        count = 0
        for sheet_value in sheet_values:
            if count == 0:
                count += 1
                continue
            target_members = await message.guild.query_members(sheet_value)

            if len(target_members) == 1:
                users.append(target_members[0])
            elif len(target_members) > 1:
                missing_flag = True
                for target_member in target_members:
                    if target_member.display_name == sheet_value:
                        missing_flag = False
                        users.append(target_member)
                        break
                if missing_flag:
                    not_found_users.append(sheet_value)
            else:
                not_found_users.append(sheet_value)
        all_users.append(users.copy())
        users.clear()

    if len(not_found_users) > 0:
        error_embed = discord.Embed( # Embedを定義する
                title="■参加者指定エラー",
                color=0xffc800, # フレーム色指定
                description="指定された参加者が見つかりませんでした。\n表示名があっているか確認してください", # Embedの説明文 必要に応じて
                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                )

        missing_user = ""
        for not_found_user in not_found_users:
            missing_user += not_found_user + "\n"

        error_embed.add_field(name="指定された参加者名", value=missing_user)  # フィールドを追加。
        await message.channel.send(embed=error_embed)

    task_state[1] = "完了"
    task_state[2] = "実行中……"
    await edit_progress_message(task_state, progress_message)

    tournament_index = {}
    i = 0
    for tournament in tournaments:
        tournament_index[tournament] = all_users[i]
        i += 1

    # 並列で登録作業
    with concurrent.futures.ThreadPoolExecutor() as executor:
        create_tournments_futures = [executor.submit(create_tournments, tournament_index, tournament) for tournament in tournaments]
        for create_tournments_future in concurrent.futures.as_completed(create_tournments_futures):
            await message.channel.send(embed=create_tournments_future.result())

    task_state[2] = "完了"
    await edit_progress_message(task_state, progress_message)
    print('--- トーナメント表作成完了 ---')
    return True

