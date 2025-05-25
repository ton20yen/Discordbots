import challonge
from challonge import api
import sys
import discord
import threading
import _json
import time
import datetime
import yaml
from yaml.loader import SafeLoader
import concurrent.futures
from dataclasses import dataclass

import rtd_command          # チームデータ読み込み
import pr_command           # 参加者登録
import sppr_command         # スプレッドシート利用参加者登録
import s_command            # トーナメント登録
import rcs_command          # 点呼開始
import rce_command          # 点呼集計
import ig_command           # 紅白戦関連
import r2on_command         # ランダム2on用
import r3on_command         # ランダム3on用
import addrole_command      # 大会用ロール付与用
import addrankrole_command  # ランバトロール付与用
import poll_command         # 似非アンケート
import inputcheck           # 入力チェック

### discord周りの設定
# Bot用トークン
TOKEN = "" # 公開用に削除済み

# インテントの生成
intents = discord.Intents.default() # 一括設定せず、個別に設定したい…
intents.messages        = True    # on_message用Intent
intents.message_content = True    # message.content参照用
intents.members         = True    # on_member_join用Intent
intents.reactions       = True    # on_reaction_add用Intent

# クライアントの生成
client = discord.Client(intents=intents)

### Challonge周りの設定
# Challongeのユーザ名とAPIキーをセット
challonge.set_credentials("", "") # 公開用に削除済み

### Global Variables
name_to_tournament = {}             # プレイヤーID -> トーナメントID 変換テーブル
nick_to_tournament = {}             # 表示名 ->  トーナメントID 変換テーブル
player_table = {}                   # Challonge ID -> 名前 変換テーブル
id_table = {}                       # 名前 -> Challonge ID 変換テーブル
player_name_list = []               # 点呼用プレイヤーID一覧リスト
player_nick_list = []               # 点呼用プレイヤー表示名一覧リスト
all_player_name_by_tournament = {}  # トーナメント別点呼用プレイヤーID一覧テーブル
all_player_nick_by_tournament = {}  # トーナメント別点呼用プレイヤー表示名一覧テーブル
open_tournament_list = []           # 実施中のトーナメントリスト
roll_call_message_obj = None        # 点呼メッセージオブジェクト
roll_call_end_message_obj = {}      # 点呼メッセージオブジェクト(key:トナメID value:メッセージオブジェクト)
reopen_match = {}                   # messageID -> matchID 変換テーブル
reopen_tournament = {}              # messageID -> tournamentID 変換テーブル
my_role_id = 0                      # 自身のroleID
my_member_obj = None                # 自身のmemberオブジェクト
lock = threading.RLock()            # 再起呼び出し対応ロック
tournament_url = "https://challonge.com/ja/"
tournament_id_to_name = {}          # tournament_id → name

# チーム戦関連
team_battle_data = None         # チーム戦用データ
member_to_team = {}             # チームメンバー -> チーム名変換テーブル
member_id_to_team = {}          # チームメンバー -> チーム名変換テーブル(discordID版)
match_report_num = {}           # 試合別総勝利報告数
reopen_score = {}               # 巻き戻し用スコア
team_roll_call_count = {}       # 点呼用カウント

# 紅白戦関連
ig_poll_message_obj = None  # 紅白戦参加者募集メッセージオブジェクト

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):
    global player_table
    global id_table
    global roll_call_message_obj
    global roll_call_end_message_obj
    global my_role_id
    global my_member_obj
    global player_name_list
    global player_nick_list
    global all_player_name_by_tournament
    global all_player_nick_by_tournament
    global name_to_tournament
    global nick_to_tournament
    global reopen_match
    global reopen_tournament
    global tournament_url
    global open_tournament_list
    global team_battle_data
    global member_to_team
    global member_id_to_team
    global match_report_num
    global reopen_score
    global team_roll_call_count
    global tournament_id_to_name
    global ig_poll_message_obj

    with lock:

        # 自分のメッセージを無効
        if message.author == client.user:
            return

        dt = datetime.datetime.now()
        # メッセージを分割
        msg = []
        msg = message.content.split()

        if (msg == []):
            # Intentsの設定をミスなければ通らない
            return

        # サーバーでのBotロールを取得
        if(my_member_obj == None):
            my_member_obj = await message.guild.fetch_member(client.user.id)

        if any(message.role_mentions):
            for role in my_member_obj.roles:
                if role.name == "WinnerReportBot":
                    my_role_id = role.id

        def reset_rams():
            global player_table
            global id_table
            global roll_call_message_obj
            global roll_call_end_message_obj
            global player_name_list
            global player_nick_list
            global all_player_name_by_tournament
            global all_player_nick_by_tournament
            global name_to_tournament
            global nick_to_tournament
            global reopen_match
            global reopen_tournament
            global open_tournament_list
            global team_battle_data
            global member_to_team
            global member_id_to_team
            global match_report_num
            global reopen_score

            name_to_tournament = {}             # プレイヤーID -> トーナメントID 変換テーブル
            nick_to_tournament = {}             # 表示名 ->  トーナメントID 変換テーブル
            player_table = {}                   # Challonge ID -> 名前 変換テーブル
            id_table = {}                       # 名前 -> Challonge ID 変換テーブル
            player_name_list = []               # 点呼用プレイヤーID一覧リスト
            player_nick_list = []               # 点呼用プレイヤー表示名一覧リスト
            all_player_name_by_tournament = {}  # トーナメント別点呼用プレイヤーID一覧テーブル
            all_player_nick_by_tournament = {}  # トーナメント別点呼用プレイヤー表示名一覧テーブル
            open_tournament_list = []           # 実施中のトーナメントリスト
            roll_call_message_obj = None        # 点呼メッセージオブジェクト
            roll_call_end_message_obj = {}      # 点呼メッセージオブジェクト
            reopen_match = {}                   # messageID -> matchID 変換テーブル
            reopen_tournament = {}              # messageID -> tournamentID 変換テーブル

            # チーム戦関連
            team_battle_data = None         # チーム戦用データ
            member_to_team = {}             # チームメンバー -> チーム名変換テーブル
            member_id_to_team = {}          # チームメンバー -> チーム名変換テーブル(discordID版)
            match_report_num = {}           # 試合別総勝利報告数
            reopen_score = {}               # 巻き戻し用スコア
            return

        # 最初が自身へのメンションか判定
        if (msg[0] == '<@' + str(client.user.id) + '>') or (msg[0] == '<@&' + str(my_role_id) + '>'):
            # print(len(msg))
            if len(msg) > 1:
                print(dt.strftime('[%Y-%m-%d %H:%M:%S]') + ' メッセージ受信: ' + str(msg[1]))

                # Team読み込みコマンドを受信
                if str(msg[1]) == '!rtd': # readteamdata
                    player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num, team_battle_data, team_roll_call_count \
                    = await rtd_command.call(message, player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num, team_roll_call_count)

                    return

                if str(msg[1]) == '!addrankrole': # addrankrole
                    await addrankrole_command.call(message, msg)

                    return

                if str(msg[1]) == '!addrole': # readteamdata
                    await addrole_command.call(message, msg)

                    return

                # Team戦データ破棄コマンドを受信
                if str(msg[1]) == '!dtd': # deleatTeamData
                    team_battle_data = None
                    member_to_team.clear()
                    member_id_to_team.clear()
                    match_report_num.clear()
                    reopen_score.clear()

                    embed = discord.Embed( # Embedを定義する
                                        title="■チーム戦データ廃棄完了",
                                        color=0x0000ff, # フレーム色指定
                                        description="チーム戦用データを廃棄しました", # Embedの説明文 必要に応じて
                                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                        )

                    await message.channel.send(embed=embed)

                    return

                # 紅白戦開始コマンドを受信
                if str(msg[1]) == '!ig': # intrasquad game
                    ig_poll_message_obj = await ig_command.call(message, msg)

                    return

                # 参加者登録コマンドを受信
                if str(msg[1]) == '!pr': # participant registration
                    await pr_command.call(message, msg, ts_flag=False)

                    return

                # アンケート作成コマンドを受信、排他等の振り分けはpoll_command.py側でやる
                # TODO : quick pollよろしくbotメンションなしで反応するようにする
                # TODO : 正式リリースまで(3月29日まで)はメンションを付けないと反応しない仕様とする
                if str(msg[1]) == '?expoll' or str(msg[1]) == '?poll': # poll
                    await poll_command.call(message, msg)

                    return

                # スプレッドシート利用の参加者登録コマンドを受信
                if str(msg[1]) == '!sppr': # spreadsheet participant registration
                    await sppr_command.call(message, msg)

                    return

                # ランダム2on
                if str(msg[1]) == '!r2on':
                    if len(msg) <= 2:
                        return

                    state_of_progress = []
                    state_of_progress.extend(["実行中……", "未実施", "未実施"])

                    async def edit_progress_message(state_of_progress, progress_message):
                        state_message = "参加者登録：" + state_of_progress[0] + "\n"
                        state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                        state_message += "点呼開始：" + state_of_progress[2]

                        embed = discord.Embed( # Embedを定義する
                                            title="■ランダム2on2トーナメント開始処理受付",
                                            color=0x0000ff, # フレーム色指定
                                            description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                        return await progress_message.edit(embed=embed)

                    state_message = "参加者登録：" + state_of_progress[0] + "\n"
                    state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                    state_message += "点呼開始：" + state_of_progress[2]
                    embed = discord.Embed( # Embedを定義する
                                        title="■ランダム2on2トーナメント開始処理受付",
                                        color=0x0000ff, # フレーム色指定
                                        description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                        )

                    progress_message = await edit_progress_message(state_of_progress, await message.channel.send(embed=embed))

                    reset_rams()

                    team_battle_data, team_roll_call_count \
                    = await r2on_command.call(message, msg)

                    state_of_progress[0] = "完了"
                    state_of_progress[1] = "実行中……"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    msg.remove(msg[2]) # トーナメント指定部分のみ取り出し
                    tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament = \
                    await s_command.call(message, msg, client.user, tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament)

                    state_of_progress[1] = "完了"
                    state_of_progress[2] = "実行中……"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num \
                    = await r2on_command.create_team_data(message, team_battle_data ,player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num)

                    roll_call_message_obj = await rcs_command.call(message, player_table, roll_call_message_obj)
                    if any(roll_call_end_message_obj):
                        roll_call_end_message_obj = await rce_command.call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=True)

                    state_of_progress[2] = "完了"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    return
                # ランダム3on
                if str(msg[1]) == '!r3on':
                    if len(msg) <= 2:
                        return

                    state_of_progress = []
                    state_of_progress.extend(["実行中……", "未実施", "未実施"])

                    async def edit_progress_message(state_of_progress, progress_message):
                        state_message = "参加者登録：" + state_of_progress[0] + "\n"
                        state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                        state_message += "点呼開始：" + state_of_progress[2]

                        embed = discord.Embed( # Embedを定義する
                                            title="■ランダム3on3トーナメント開始処理受付",
                                            color=0x0000ff, # フレーム色指定
                                            description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                        return await progress_message.edit(embed=embed)

                    state_message = "参加者登録：" + state_of_progress[0] + "\n"
                    state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                    state_message += "点呼開始：" + state_of_progress[2]
                    embed = discord.Embed( # Embedを定義する
                                        title="■ランダム3on3トーナメント開始処理受付",
                                        color=0x0000ff, # フレーム色指定
                                        description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                        )

                    progress_message = await edit_progress_message(state_of_progress, await message.channel.send(embed=embed))

                    reset_rams()

                    team_battle_data, team_roll_call_count \
                    = await r3on_command.call(message, msg)

                    state_of_progress[0] = "完了"
                    state_of_progress[1] = "実行中……"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    msg.remove(msg[2]) # トーナメント指定部分のみ取り出し
                    tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament = \
                    await s_command.call(message, msg, client.user, tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament)

                    state_of_progress[1] = "完了"
                    state_of_progress[2] = "実行中……"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num \
                    = await r3on_command.create_team_data(message, team_battle_data ,player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num)

                    roll_call_message_obj = await rcs_command.call(message, player_table, roll_call_message_obj)
                    if any(roll_call_end_message_obj):
                        roll_call_end_message_obj = await rce_command.call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=True)

                    state_of_progress[2] = "完了"
                    progress_message = await edit_progress_message(state_of_progress, progress_message)

                    return
                # リセット(開始前に戻す)コマンドを受信
                if str(msg[1]) == '!reset': # reset
                    if len(msg) <= 2:
                        embed = discord.Embed( # Embedを定義する
                                            title="■引数エラー",
                                            color=0xffc800, # フレーム色指定
                                            description="トーナメントIDを指定してください", # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                        await message.channel.send(embed=embed)
                        return
                    
                    challonge.tournaments.reset(msg[2])
                    return

                # 開始コマンドを受信
                if str(msg[1]) == '!s': # start
                    tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament = \
                    await s_command.call(message, msg, client.user, tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament)
                    return

                elif str(msg[1]) == '!ts': # tournment start 登録、受付開始、点呼を一緒くたに開始する
                    if len(msg) <= 3:
                        embed = discord.Embed( # Embedを定義する
                                            title="■引数エラー",
                                            color=0xffc800, # フレーム色指定
                                            description="トーナメントIDと参加者募集メッセージのIDを指定してください", # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )

                        await message.channel.send(embed=embed)
                        return

                    state_of_progress = []
                    state_of_progress.extend(["実行中……", "未実施", "未実施"])

                    async def edit_progress_message(state_of_progress, progress_message):
                        state_message = "参加者登録：" + state_of_progress[0] + "\n"
                        state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                        state_message += "点呼開始：" + state_of_progress[2]

                        embed = discord.Embed( # Embedを定義する
                                            title="■トーナメント開始処理受付",
                                            color=0x0000ff, # フレーム色指定
                                            description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                        return await progress_message.edit(embed=embed)

                    state_message = "参加者登録：" + state_of_progress[0] + "\n"
                    state_message += "勝利報告受付開始：" + state_of_progress[1] + "\n"
                    state_message += "点呼開始：" + state_of_progress[2]
                    embed = discord.Embed( # Embedを定義する
                                        title="■トーナメント開始処理受付",
                                        color=0x0000ff, # フレーム色指定
                                        description="トーナメントを開始します。しばらくお待ちください…\n" + state_message, # Embedの説明文 必要に応じて
                                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                        )

                    progress_message = await edit_progress_message(state_of_progress, await message.channel.send(embed=embed))

                    start_time = time.time()
                    if await pr_command.call(message, msg, ts_flag=True):
                        state_of_progress[0] = "完了"
                        state_of_progress[1] = "実行中……"
                        progress_message = await edit_progress_message(state_of_progress, progress_message)
                        print(time.time()-start_time)

                        msg.remove(msg[2]) # トーナメント指定部分のみ取り出し
                        tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament = \
                        await s_command.call(message, msg, client.user, tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament)
                        print(time.time()-start_time)

                        state_of_progress[1] = "完了"
                        state_of_progress[2] = "実行中……"
                        progress_message = await edit_progress_message(state_of_progress, progress_message)

                        roll_call_message_obj = await rcs_command.call(message, player_table, roll_call_message_obj)
                        if any(roll_call_end_message_obj):
                            roll_call_end_message_obj = await rce_command.call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=True)

                        state_of_progress[2] = "完了"
                        progress_message = await edit_progress_message(state_of_progress, progress_message)

                    print(time.time()-start_time)

                    return

                # 点呼
                elif str(msg[1]) == '!rcs': # roll call start
                    roll_call_message_obj = await rcs_command.call(message, player_table, roll_call_message_obj)
                    if any(roll_call_end_message_obj):
                        roll_call_end_message_obj = await rce_command.call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=True)
                    return

                elif str(msg[1]) == '!rce': # roll call end
                    roll_call_end_message_obj = await rce_command.call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=False)
                    return
            print(dt.strftime('【%Y/%m/%d %H:%M:%S.%f】') + ' 勝利報告受理')
            print("報告者名")
            print("message.author = " + str(message.author))
            print("message.author.global_name = " + str(message.author.global_name))
            print("message.author.nick = " + str(message.author.nick))

            # 勝利報告を受信
            # メンションのみ
            if (not(any(player_table))):
                embed = discord.Embed( # Embedを定義する
                                            title="■トーナメント未指定エラー",
                                            color=0xffc800, # フレーム色指定
                                            description="先に!sコマンドでトーナメントを指定してください", # Embedの説明文 必要に応じて
                                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                await message.channel.send(embed=embed)
                return

            temp_score = []
            tournament_id = ""

            # 勝利者名から報告対象のトーナメントIDとプレイヤーIDを返却する
            def get_report_id(winner_name):
                tournament_id = ""
                player_id = None
                if winner_name in id_table:
                    player_id = id_table[winner_name]
                    # 報告対象トナメを逆引き
                    if winner_name in name_to_tournament:
                        tournament_id = name_to_tournament[winner_name]
                    if winner_name in nick_to_tournament:
                        tournament_id = nick_to_tournament[winner_name]
                return tournament_id, player_id

            # 勝者名なし
            if len(msg) == 1:
                player_id = None
                author_list = []

                author_list.append(str(message.author))                 # discordID
                author_list.append(str(message.author.name))            # プロフィール
                author_list.append(str(message.author.global_name))     # プロフィール
                author_list.append(str(message.author.nick))            # サーバープロフィール
                author_list.append(str(message.author.display_name))    # 表示名

                try:
                    if team_battle_data != None:
                        # チーム戦時
                        for author in author_list:
                            # 報告者がメンバーとして登録されてるか確認
                            if author in member_to_team:
                                report_id = get_report_id(member_to_team[author])
                            elif author in member_id_to_team:
                                report_id = get_report_id(member_id_to_team[author])

                            if report_id[1] != None:
                                break
                            
                    else :
                        # 個人戦時
                        for author in author_list:
                            report_id = get_report_id(author)
                            if report_id[1] != None:
                                break
                except:
                    error_msg = "報告者名がトーナメント表上に存在しません"
                    error_msg += '\n' + "途中で名前を変更した場合は再度 !s コマンドを使用しbotを更新してください"
                    error_msg += '\n' + "報告者名: " + str(message.author) + " もしくは " + str(message.author.nick)
                    embed = discord.Embed( # Embedを定義する
                                            # title=tournament['name'],
                                            color=0xffc800, # フレーム色指定
                                            description="■報告者未登録エラー", # Embedの説明文 必要に応じて
                                            # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                    embed.add_field(name="", value=error_msg)
                    await message.channel.send(embed=embed)
                    return

                player_id = report_id[1]
                tournament_id = report_id[0]

                if player_id == None:
                    # TODO: 報告時にトナメがオープン状態かどうかの判定を入れる
                    # ついでにこの辺の存在しないエラーを関数化してまとめる
                    error_msg = "報告者名がトーナメント表上に存在しません"
                    error_msg += '\n' + "途中で名前を変更した場合は再度 !s コマンドを使用しbotを更新してください"
                    error_msg += '\n' + "報告者名: " + str(message.author) + " もしくは " + str(message.author.nick)
                    embed = discord.Embed( # Embedを定義する
                                            # title=tournament['name'],
                                            color=0xffc800, # フレーム色指定
                                            description="■報告者未登録エラー", # Embedの説明文 必要に応じて
                                            # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                    embed.add_field(name="", value=error_msg)
                    await message.channel.send(embed=embed)
                    return

            # 勝者名 or スコア付き
            elif len(msg) == 2:
                # 勝利者名だった場合
                if(str(msg[1]) in id_table):
                    report_id = get_report_id(str(msg[1]))
                    player_id = report_id[1]
                    tournament_id = report_id[0]
                elif((str(msg[1]) in member_to_team)):
                    report_id = get_report_id(member_to_team[str(msg[1])])
                    player_id = report_id[1]
                    tournament_id = report_id[0]
                elif((str(msg[1]) in member_id_to_team)):
                    report_id = get_report_id(member_id_to_team[str(msg[1])])
                    player_id = report_id[1]
                    tournament_id = report_id[0]
                else:
                    # スコアかもしれない場合
                    if '-' in msg[1]:
                        temp_score = msg[1].split('-')
                    else:
                        # フォーマットが違うので勝利者と判断
                        # TODO: 報告時にトナメがオープン状態かどうかの判定を入れる
                        # ついでにこの辺の存在しないエラーを関数化してまとめる
                        error_msg = "報告者名がトーナメント表上に存在しません"
                        error_msg += '\n' + "途中で名前を変更した場合は再度 !s コマンドを使用しbotを更新してください"
                        error_msg += '\n' + "報告者名: " + str(message.author) + " もしくは " + str(message.author.nick)
                        embed = discord.Embed( # Embedを定義する
                                                # title=tournament['name'],
                                                color=0xffc800, # フレーム色指定
                                                description="■報告者未登録エラー", # Embedの説明文 必要に応じて
                                                # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                                )
                        embed.add_field(name="", value=error_msg)
                        await message.channel.send(embed=embed)

                        return

                    # スコアだったので報告者を勝利者として検索
                    player_id = None
                    author_list = []

                    author_list.append(str(message.author))             # discordID
                    author_list.append(str(message.author.name))        # プロフィール
                    author_list.append(str(message.author.global_name)) # プロフィール
                    author_list.append(str(message.author.nick))        # サーバープロフィール

                    if team_battle_data != None:
                        # チーム戦時
                        for author in author_list:
                            # 報告者がメンバーとして登録されてるか確認
                            if author in member_to_team:
                                report_id = get_report_id(member_to_team[author])
                            elif author in member_id_to_team:
                                report_id = get_report_id(member_id_to_team[author])
                            
                    else :
                        # 個人戦時
                        for author in author_list:
                            report_id = get_report_id(author)
                            if report_id[1] != None:
                                break

                    player_id = report_id[1]
                    tournament_id = report_id[0]

                    if player_id == None:
                        # TODO: 報告時にトナメがオープン状態かどうかの判定を入れる
                        # ついでにこの辺の存在しないエラーを関数化してまとめる
                        error_msg = "報告者名がトーナメント表上に存在しません"
                        error_msg += '\n' + "途中で名前を変更した場合は再度 !s コマンドを使用しbotを更新してください"
                        error_msg += '\n' + "報告者名: " + str(message.author) + " もしくは " + str(message.author.nick)
                        embed = discord.Embed( # Embedを定義する
                                                # title=tournament['name'],
                                                color=0xffc800, # フレーム色指定
                                                description="■報告者未登録エラー", # Embedの説明文 必要に応じて
                                                # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                                )
                        embed.add_field(name="", value=error_msg)
                        await message.channel.send(embed=embed)
                        return

            # 勝利者名+スコアの場合
            elif len(msg) == 3:
                # 勝利者名がトーナメント表上に存在するか確認
                if(str(msg[1]) in id_table) or (str(msg[1]) in member_to_team) or (str(msg[1]) in member_id_to_team):
                    if team_battle_data != None:
                        # チーム戦時
                        if str(msg[1]) in member_to_team:
                            report_id = get_report_id(member_to_team[str(msg[1])])
                        if str(msg[1]) in member_id_to_team:
                            report_id = get_report_id(member_id_to_team[str(msg[1])])
                    else :
                        # 個人戦時
                        report_id = get_report_id(str(msg[1]))

                    player_id = report_id[1]
                    tournament_id = report_id[0]

                else:
                    # TODO: 報告時にトナメがオープン状態かどうかの判定を入れる
                    # ついでにこの辺の存在しないエラーを関数化してまとめる
                    error_msg = "報告者名がトーナメント表上に存在しません"
                    error_msg += '\n' + "途中で名前を変更した場合は再度 !s コマンドを使用しbotを更新してください"
                    error_msg += '\n' + "報告者名: " + str(message.author) + " もしくは " + str(message.author.nick)
                    embed = discord.Embed( # Embedを定義する
                                            # title=tournament['name'],
                                            color=0xffc800, # フレーム色指定
                                            description="■報告者未登録エラー", # Embedの説明文 必要に応じて
                                            # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                            )
                    embed.add_field(name="", value=error_msg)
                    await message.channel.send(embed=embed)
                    return

                if '-' in msg[2]:
                    temp_score = msg[2].split('-')
                else:
                    # フォーマットが違うので勝利者と判断
                    embed = discord.Embed( # Embedを定義する
                                        # title=tournament['name'],
                                        color=0xffc800, # フレーム色指定
                                        description="■フォーマットエラー", # Embedの説明文 必要に応じて
                                        # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                        )
                    embed.add_field(name="", value="スコア報告がフォーマットと異なっています")
                    await message.channel.send(embed=embed)

                    return

            else:
                embed = discord.Embed( # Embedを定義する
                                    # title=tournament['name'],
                                    color=0xffc800, # フレーム色指定
                                    description="■フォーマットエラー", # Embedの説明文 必要に応じて
                                    # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                    )
                embed.add_field(name="", value="勝利報告の引数が超過しています")
                await message.channel.send(embed=embed)
                return

            # print(player_id)
            def get_next_match(open_matchs):
                if any(open_matchs):
                    # 報告可能な試合が複数ある場合は最もラウンド数が若いものを対象とする
                    min_round = 99
                    next_match = open_matchs[0]
                    for open_match in open_matchs:
                        if min_round > open_match['round']:
                            min_round = open_match['round']
                            next_match = open_match
                    return next_match

            # 報告対象の試合を抽出
            open_matchs = challonge.matches.index(tournament_id, state='open', participant_id=player_id)
            # print(open_matchs)

            if any(open_matchs):
                reportable_match = get_next_match(open_matchs)

                # 報告者が1Pか2Pかの判定
                if (str(reportable_match['player1_id']) == str(player_id)):
                    loser_id = reportable_match['player2_id']
                    if temp_score == []:
                        score = '1-0'
                    else:
                        score = temp_score[0] + '-' + temp_score[1]
                elif(str(reportable_match['player2_id']) == str(player_id)):
                    loser_id = reportable_match['player1_id']
                    if temp_score == []:
                        score = '0-1'
                    else:
                        score = temp_score[1] + '-' + temp_score[0]
                else:
                    await message.channel.send('player名が一致しません') # 実運用上はでないはず
                    return
            else:
                embed = discord.Embed( # Embedを定義する
                                    # title=tournament['name'],
                                    color=0xffc800, # フレーム色指定
                                    description="■報告対象試合なしエラー", # Embedの説明文 必要に応じて
                                    # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                    )
                embed.add_field(name="", value='組み合わせが確定していない、あるいは試合が終了している状態で勝利報告はできません')
                await message.channel.send(embed=embed)
                return

            if team_battle_data == None:
                # トーナメント表更新
                challonge.matches.update(tournament_id, reportable_match['id'], scores_csv=score, winner_id=player_id)

                # 報告対象の試合を抽出
                open_matchs = challonge.matches.index(tournament_id, state='open', participant_id=player_id)
                # print(open_matchs)

                next_match = get_next_match(open_matchs)

                score = score.split("-")
                comp_message = "下記の通りトーナメント表を更新しました"
                comp_message += "\n" + "(" + score[0] + ") " + player_table[str(reportable_match['player1_id'])].replace('_', '\_') + " VS " + player_table[str(reportable_match['player2_id'])].replace('_', '\_') + " (" + score[1] + ")"
                comp_message += "\n" + "トーナメント表：" + tournament_url + tournament_id

                if any(open_matchs):
                    comp_message += "\n\n" + "次の対戦は下記の通りです。"
                    comp_message += "\n" + player_table[str(next_match['player1_id'])].replace('_', '\_') + " VS " + player_table[str(next_match['player2_id'])].replace('_', '\_')

                tournament_data = challonge.tournaments.show(tournament_id)

                if tournament_data['tournament_type'] != "single elimination":
                    # 報告対象の試合を抽出
                    loser_open_matchs = challonge.matches.index(tournament_id, state='open', participant_id=loser_id)
                    loser_next_match = get_next_match(loser_open_matchs)

                    if any(loser_open_matchs):
                        comp_message += "\n" + player_table[str(loser_next_match['player1_id'])].replace('_', '\_') + " VS " + player_table[str(loser_next_match['player2_id'])].replace('_', '\_')

                embed = discord.Embed( # Embedを定義する
                        title=tournament_id_to_name[tournament_id],
                        color=0x0000ff, # フレーム色指定
                        description="■勝利報告受付完了", # Embedの説明文 必要に応じて
                        url=tournament_url + tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                        )
                
                embed.add_field(name="",value=comp_message)  # フィールドを追加。

                # 巻き戻し用のデータを保存
                emoji = "\N{RIGHTWARDS ARROW WITH HOOK}"
                comp_message_obj = await message.channel.send(embed=embed)
                await comp_message_obj.add_reaction(emoji)
                reopen_match[comp_message_obj.id] = reportable_match['id']
                reopen_tournament[comp_message_obj.id] = tournament_id
            else:
                temp_match_num = []
                if match_report_num.get(str(reportable_match['id'])) == None:
                    temp_match_num = [0, 0, 0]
                    # 初回報告
                    # 報告者が1Pか2Pかの判定
                    if (str(reportable_match['player1_id']) == str(player_id)):
                        match_report_num[str(reportable_match['id'])] = [1, 1, 0]
                    elif(str(reportable_match['player2_id']) == str(player_id)):
                        match_report_num[str(reportable_match['id'])] = [1, 0, 1]
                    else:
                        await message.channel.send('player名が一致しません') # 実運用上はでないはず
                        return
                else:
                    for report_num in match_report_num[str(reportable_match['id'])]:
                        temp_match_num.append(report_num)
    
                    match_report_num[str(reportable_match['id'])][0] = match_report_num[str(reportable_match['id'])][0] + 1
                    if (str(reportable_match['player1_id']) == str(player_id)):
                        match_report_num[str(reportable_match['id'])][1] = match_report_num[str(reportable_match['id'])][1] + 1
                    elif(str(reportable_match['player2_id']) == str(player_id)):
                        match_report_num[str(reportable_match['id'])][2] = match_report_num[str(reportable_match['id'])][2] + 1
                    else:
                        await message.channel.send('player名が一致しません') # 実運用上はでないはず

                print(match_report_num)

                # temp_tournament = challonge.tournaments.show(tournament_id)
                comp_message = "勝利報告を受理しました。現在のスコアは下記の通りです。"
                comp_message += "\n" + "(" + str(match_report_num[str(reportable_match['id'])][1]) + ") " + player_table[str(reportable_match['player1_id'])].replace('_', '\_') + " VS " + player_table[str(reportable_match['player2_id'])].replace('_', '\_') + " (" + str(match_report_num[str(reportable_match['id'])][2]) + ")"
                comp_message += "\n" + "トーナメント表：" + tournament_url + tournament_id

                embed = discord.Embed( # Embedを定義する
                        title=tournament_id_to_name[tournament_id],
                        color=0x0000ff, # フレーム色指定
                        description="■勝利報告受付完了", # Embedの説明文 必要に応じて
                        url=tournament_url + tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                        )
                
                embed.add_field(name="",value=comp_message)  # フィールドを追加。
                # 巻き戻し用のデータを保存
                emoji = "\N{HEAVY MINUS SIGN}"
                comp_message_obj = await message.channel.send(embed=embed)
                await comp_message_obj.add_reaction(emoji)
                reopen_score[comp_message_obj.id] = temp_match_num
                reopen_match[comp_message_obj.id] = reportable_match['id']
                reopen_tournament[comp_message_obj.id] = tournament_id

                if match_report_num[str(reportable_match['id'])][0] >= team_battle_data["report_num"]:
                    # 早稲田式の時 かつ 勝敗未決定の場合はChallongeへの反映を行わない
                    if team_battle_data["waseda_flag"]:
                        if(match_report_num[str(reportable_match['id'])][2] == match_report_num[str(reportable_match['id'])][1]):
                            return

                    score = str(match_report_num[str(reportable_match['id'])][1]) + "-" + str(match_report_num[str(reportable_match['id'])][2])

                    player_score = score.split("-")
                    if player_score[0] > player_score[1]:
                        challonge.matches.update(tournament_id, reportable_match['id'], scores_csv=score, winner_id=reportable_match['player1_id'])
                    else:
                        challonge.matches.update(tournament_id, reportable_match['id'], scores_csv=score, winner_id=reportable_match['player2_id'])
 
                    comp_message = "下記の通りトーナメント表を更新しました"
                    comp_message += "\n" + "(" + player_score[0] + ") " + player_table[str(reportable_match['player1_id'])].replace('_', '\_') + " VS " + player_table[str(reportable_match['player2_id'])].replace('_', '\_') + " (" + player_score[1] + ")"
                    comp_message += "\n" + "トーナメント表：" + tournament_url + tournament_id

                    embed = discord.Embed( # Embedを定義する
                            title=tournament_id_to_name[tournament_id],
                            color=0x0000ff, # フレーム色指定
                            description="■トーナメント反映完了", # Embedの説明文 必要に応じて
                            url=tournament_url + tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                            )
                    
                    embed.add_field(name="",value=comp_message)  # フィールドを追加。

                    # 巻き戻し用のデータを保存
                    emoji = "\N{RIGHTWARDS ARROW WITH HOOK}"
                    comp_message_obj = await message.channel.send(embed=embed)
                    await comp_message_obj.add_reaction(emoji)
                    reopen_score[comp_message_obj.id] = temp_match_num
                    reopen_match[comp_message_obj.id] = reportable_match['id']
                    reopen_tournament[comp_message_obj.id] = tournament_id

    return

# リアクションを検知した時に呼ばれる
@client.event
async def on_raw_reaction_add(payload):
    global roll_call_message_obj
    global roll_call_end_message_obj
    global ig_poll_message_obj
    global player_name_list
    global tournament_url
    global team_battle_data
    global match_report_num
    global reopen_score
    global member_to_team
    global team_roll_call_count

    user = payload.member

    # botは無視
    if user.bot:
        return

    reaction_channel = await client.fetch_channel(payload.channel_id)
    reaction_massage = await reaction_channel.fetch_message(payload.message_id)

    dt = datetime.datetime.now()
    # 報告済み試合巻き戻し処理
    # 一回でも報告されているか判定
    if any(reopen_match):
        # リアクションされたのが更新完了メッセージ
        if reaction_massage.id in reopen_match:
            # かつredo
            if payload.emoji.name == "\N{RIGHTWARDS ARROW WITH HOOK}":
                # 巻き戻し処理
                reopen_match_id = reopen_match.pop(reaction_massage.id)
                reopen_tournament_id = reopen_tournament.pop(reaction_massage.id)
                challonge.matches.reopen(reopen_tournament_id, reopen_match_id)

                # チーム戦はスコア情報も一個前に戻す
                if team_battle_data != None:
                    match_report_num[str(reopen_match_id)] = reopen_score[reaction_massage.id]

                reopen_result = challonge.matches.show(reopen_tournament_id, reopen_match_id)
                reopen_result_message = "下記試合を報告前の状態に戻しました\n"
                reopen_result_message += player_table[str(reopen_result['player1_id'])].replace('_', '\_') + " VS " + player_table[str(reopen_result['player2_id'])].replace('_', '\_')
                reopen_result_message += "\n" + "トーナメント表：" + tournament_url + reopen_tournament_id
                temp_tournament = challonge.tournaments.show(reopen_tournament_id)

                embed = discord.Embed( # Embedを定義する
                        title=temp_tournament['name'],
                        color=0x0000ff, # フレーム色指定
                        description="■巻き戻し実行", # Embedの説明文 必要に応じて
                        url=tournament_url+reopen_tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                        )
                
                embed.add_field(name="",value=reopen_result_message)  # フィールドを追加。

                print(dt.strftime('[%Y-%m-%d %H:%M:%S]') + ' 巻き戻し実行')
                print('巻き戻し実行者')
                print('user: ' + str(user))
                print('user.name: ' + str(user.name))
                print('user.nick: ' + str(user.nick))
                print('user.global_name: ' + str(user.global_name))

                await reaction_channel.send(embed=embed)
                return
            # スコア情報巻き戻し
            if payload.emoji.name == "\N{HEAVY MINUS SIGN}":
                print(match_report_num)
                print(reopen_score)

                # 巻き戻し処理
                reopen_match_id = reopen_match.pop(reaction_massage.id)
                reopen_tournament_id = reopen_tournament.pop(reaction_massage.id)
                match_report_num[str(reopen_match_id)] = reopen_score[reaction_massage.id]

                reopen_result = challonge.matches.show(reopen_tournament_id, reopen_match_id)
                reopen_result_message = "スコア報告前の状態に戻しました\n"
                reopen_result_message += "(" + str(match_report_num[str(reopen_match_id)][1]) + ") "
                reopen_result_message += player_table[str(reopen_result['player1_id'])].replace('_', '\_') + " VS " + player_table[str(reopen_result['player2_id'])].replace('_', '\_')
                reopen_result_message += " (" + str(match_report_num[str(reopen_match_id)][2]) + ")"
                reopen_result_message += "\n" + "トーナメント表：" + tournament_url + reopen_tournament_id

                if match_report_num[str(reopen_match_id)][0] == 0:
                    match_report_num[str(reopen_match_id)] = None

                temp_tournament = challonge.tournaments.show(reopen_tournament_id)

                embed = discord.Embed( # Embedを定義する
                        title=temp_tournament['name'],
                        color=0x0000ff, # フレーム色指定
                        description="■巻き戻し実行", # Embedの説明文 必要に応じて
                        url=tournament_url+reopen_tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                        )
                
                embed.add_field(name="",value=reopen_result_message)  # フィールドを追加。

                print(dt.strftime('[%Y-%m-%d %H:%M:%S]') + ' 巻き戻し実行')
                print('巻き戻し実行者')
                print('user: ' + str(user))
                print('user.name: ' + str(user.name))
                print('user.nick: ' + str(user.nick))
                print('user.global_name: ' + str(user.global_name))

                await reaction_channel.send(embed=embed)
                return

    if not(ig_poll_message_obj == None):
        if reaction_massage.id == ig_poll_message_obj.id:
            await ig_command.on_reaction_add(payload.emoji, user)

    # 点呼処理
    # 点呼が始まってなければ何もしない
    if roll_call_message_obj == None:
        return

    # リアクション先が点呼メッセージか判定
    if reaction_massage.id == roll_call_message_obj.id:
        user_list = []
        user_list.append(user)
        user_list.append(user.name)
        user_list.append(user.nick)
        user_list.append(user.global_name)
        # print(user_list)

        # 参加者リストにリアクション者がいればリストから除去
        last_user_name = ""
        call_flag = False

        if team_battle_data != None:
            # print("--- 点呼テスト ---")
            # print(team_roll_call_count)
            for user_name in user_list:
                if user_name in player_nick_list:
                    del player_name_list[player_nick_list.index(user_name)]
                    player_nick_list.remove(user_name)
                    last_user_name = member_id_to_team[user_name]

                    # valueError 'xxx チーム' is not in list
                    # チームがそろう前にキーを消してしまっている、キー消去タイミングを制御すべし
                    team_roll_call_count[last_user_name] = team_roll_call_count[last_user_name] - 1
                    if (team_roll_call_count[last_user_name] <= 0):
                        del all_player_name_by_tournament[nick_to_tournament[last_user_name]][all_player_nick_by_tournament[nick_to_tournament[last_user_name]].index(last_user_name)]

                        all_player_nick_by_tournament[nick_to_tournament[last_user_name]].remove(last_user_name)
                        if not(any(all_player_nick_by_tournament[nick_to_tournament[last_user_name]])):
                            call_flag = True

            for user_name in user_list:
                if user_name in player_name_list:
                    del player_nick_list[player_name_list.index(user_name)]
                    player_name_list.remove(user_name)
                    last_user_name = member_to_team[user_name]
                    
                    team_roll_call_count[last_user_name] = team_roll_call_count[last_user_name] - 1
                    if (team_roll_call_count[last_user_name] <= 0):
                        del all_player_nick_by_tournament[name_to_tournament[last_user_name]][all_player_name_by_tournament[name_to_tournament[last_user_name]].index(last_user_name)]

                        all_player_name_by_tournament[name_to_tournament[last_user_name]].remove(last_user_name)
                        if not(any(all_player_name_by_tournament[name_to_tournament[last_user_name]])):
                            call_flag = True

        else:
            for user_name in user_list:
                if user_name in player_name_list:
                    del player_nick_list[player_name_list.index(user_name)]
                    player_name_list.remove(user_name)
                    last_user_name = user_name
                    
                    del all_player_nick_by_tournament[name_to_tournament[last_user_name]][all_player_name_by_tournament[name_to_tournament[last_user_name]].index(last_user_name)]
                    all_player_name_by_tournament[name_to_tournament[last_user_name]].remove(last_user_name)
                    if not(any(all_player_name_by_tournament[name_to_tournament[last_user_name]])):
                        call_flag = True

            for user_name in user_list:
                if user_name in player_nick_list:
                    del player_name_list[player_nick_list.index(user_name)]
                    player_nick_list.remove(user_name)
                    last_user_name = user_name
                    
                    del all_player_name_by_tournament[nick_to_tournament[last_user_name]][all_player_nick_by_tournament[nick_to_tournament[last_user_name]].index(last_user_name)]
                    all_player_nick_by_tournament[nick_to_tournament[last_user_name]].remove(last_user_name)
                    if not(any(all_player_nick_by_tournament[nick_to_tournament[last_user_name]])):
                        call_flag = True

        if call_flag == True:
            if last_user_name in nick_to_tournament:
                tournament = challonge.tournaments.show(nick_to_tournament[last_user_name])
                tournament_id = nick_to_tournament[last_user_name]
            elif last_user_name in name_to_tournament:
                tournament = challonge.tournaments.show(name_to_tournament[last_user_name])
                tournament_id = name_to_tournament[last_user_name]

            embed = discord.Embed( # Embedを定義する
                    title=tournament['name'],
                    color=0x0000ff, # フレーム色指定
                    description="■大会別点呼完了通知", # Embedの説明文 必要に応じて
                    url=tournament_url + tournament_id # これを設定すると、タイトルが指定URLへのリンクになる
                    )
            embed.add_field(name="",value="上記大会の点呼が完了しました！")  # フィールドを追加。
            await reaction_channel.send(embed=embed)

        # 点呼集計更新
        if any(roll_call_end_message_obj):
            roll_call_end_message_obj = await rce_command.call(reaction_massage, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag=True)

        # トーナメント開始タイミングを全トナメ分そろった、から、個別のトナメがでそろったに変更する
        roll_call_tournament = []

        if team_battle_data == None:
            for player_name in player_name_list:
                roll_call_tournament.append(name_to_tournament[player_name])
            
            if set(roll_call_tournament) != set(list(name_to_tournament.values())):
                end_roll_call_tournaments = set(list(name_to_tournament.values())) - set(roll_call_tournament)
                for end_roll_call_tournament in end_roll_call_tournaments:
                    start_tournament = challonge.tournaments.show(end_roll_call_tournament)
                    print(start_tournament['state'])
                    if start_tournament['state'] == 'pending':
                        challonge.tournaments.start(end_roll_call_tournament)
        else:
            if not(any(player_name_list)):
                tournament = ""
                if last_user_name in nick_to_tournament:
                    tournament = challonge.tournaments.show(nick_to_tournament[last_user_name])
                    challonge.tournaments.start(nick_to_tournament[last_user_name])
                elif last_user_name in name_to_tournament:
                    tournament = challonge.tournaments.show(name_to_tournament[last_user_name])
                    challonge.tournaments.start(name_to_tournament[last_user_name])

        if not(any(player_name_list)):
            print(dt.strftime('[%Y-%m-%d %H:%M:%S]') + ' 点呼完了')
            embed = discord.Embed( # Embedを定義する
                    # title=tournament['name'],
                    color=0x0000ff, # フレーム色指定
                    description="■全大会点呼完了", # Embedの説明文 必要に応じて
                    # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                    )
            embed.add_field(name="",value="全員の点呼が完了しました！")  # フィールドを追加。

            await reaction_channel.send(embed=embed)

    return

# リアクション除去を検知した時に呼ばれる
@client.event
async def on_raw_reaction_remove(payload):
    global ig_poll_message_obj

    # 紅白戦用参加者募集メッセージ
    if not(ig_poll_message_obj == None):

        reaction_channel = await client.fetch_channel(payload.channel_id)
        reaction_massage = await reaction_channel.fetch_message(payload.message_id)

        if reaction_massage.id == ig_poll_message_obj.id:
            guild = client.get_guild(payload.guild_id)
            user = guild.get_member(payload.user_id)
            await ig_command.on_reaction_remove(payload.emoji, user)

    return

# リアクション除去を検知した時に呼ばれる
@client.event
async def on_raw_reaction_clear(payload):
    global ig_poll_message_obj

    # 紅白戦用参加者募集メッセージ
    if not(ig_poll_message_obj == None):
        if payload.message_id == ig_poll_message_obj.id:
            await ig_command.on_reaction_clear()
            ig_poll_message_obj= None

    return

client.run(TOKEN)
