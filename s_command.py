import discord
import challonge
import concurrent.futures
import datetime

s_command_name_to_tournament = {}         # プレイヤーID -> トーナメントID 変換テーブル
s_command_nick_to_tournament = {}         # 表示名 ->  トーナメントID 変換テーブル
s_command_player_table = {}               # Challonge ID -> 名前 変換テーブル
s_command_all_player_name_by_tournament = {} # トーナメント別点呼用プレイヤーID一覧テーブル
s_command_all_player_nick_by_tournament = {} # トーナメント別点呼用プレイヤー表示名一覧テーブル
s_command_tournament_id_to_name = {}      # tournament_id → name
s_command_id_table = {}                   # 名前 -> Challonge ID 変換テーブル
s_command_player_name_list = []           # 点呼用プレイヤーID一覧リスト
s_command_player_nick_list = []           # 点呼用プレイヤー表示名一覧リスト

def set_tournament_data():
    global s_command_name_to_tournament
    global s_command_nick_to_tournament
    global s_command_player_table
    global s_command_all_player_name_by_tournament
    global s_command_all_player_nick_by_tournament
    global s_command_tournament_id_to_name
    global s_command_id_table
    global s_command_player_name_list
    global s_command_player_nick_list

    return s_command_tournament_id_to_name, s_command_player_table, s_command_id_table, s_command_nick_to_tournament, s_command_player_nick_list, s_command_player_name_list, s_command_name_to_tournament, s_command_all_player_name_by_tournament, s_command_all_player_nick_by_tournament

def get_tournament_data(tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament):
    global s_command_name_to_tournament
    global s_command_nick_to_tournament
    global s_command_player_table
    global s_command_all_player_name_by_tournament
    global s_command_all_player_nick_by_tournament
    global s_command_tournament_id_to_name
    global s_command_id_table
    global s_command_player_name_list
    global s_command_player_nick_list

    s_command_name_to_tournament = name_to_tournament
    s_command_nick_to_tournament = nick_to_tournament
    s_command_player_table = player_table
    s_command_all_player_name_by_tournament = all_player_name_by_tournament
    s_command_all_player_nick_by_tournament = all_player_nick_by_tournament
    s_command_tournament_id_to_name = tournament_id_to_name
    s_command_id_table = id_table
    s_command_player_name_list = player_name_list
    s_command_player_nick_list = player_nick_list

def delete_tournament_data(tournament_ID):
    global s_command_name_to_tournament
    global s_command_nick_to_tournament
    global s_command_player_table
    global s_command_all_player_name_by_tournament
    global s_command_all_player_nick_by_tournament
    global s_command_tournament_id_to_name
    global s_command_id_table
    global s_command_player_name_list
    global s_command_player_nick_list

    print("--- delete name data ---")
    for delete_name in s_command_all_player_name_by_tournament[tournament_ID]:
        if delete_name in s_command_player_name_list:
            s_command_player_name_list.remove(delete_name)
        if  delete_name in s_command_id_table:
            del s_command_id_table[delete_name]
        del s_command_name_to_tournament[delete_name]
    del s_command_all_player_name_by_tournament[tournament_ID]

    print("--- delete nick data ---")
    for delete_nick in s_command_all_player_nick_by_tournament[tournament_ID]:
        if delete_nick in s_command_player_nick_list:
            s_command_player_nick_list.remove(delete_nick)
        if  delete_nick in s_command_id_table:
            del s_command_id_table[delete_nick]
        del s_command_nick_to_tournament[delete_nick]
    del s_command_all_player_nick_by_tournament[tournament_ID]

    del s_command_tournament_id_to_name[tournament_ID]

    participants_data = challonge.participants.index(tournament_ID)
    for participant_data in participants_data:
        del s_command_player_table[str(participant_data['id'])]
    print("--- del complete ---")

def check_tournament_status(tournament_ID):
    tournament_data = challonge.tournaments.show(tournament_ID)

    if tournament_data['state'] == 'complete':
        delete_tournament_data(tournament_ID)
    else:
        update_time = tournament_data['updated_at']
        update_time = update_time.replace(tzinfo=None)
        timedelta = datetime.datetime.now() - update_time
        if timedelta.days > 1:
            delete_tournament_data(tournament_ID)

def set_participant_info(participant, tournament):
    global s_command_name_to_tournament
    global s_command_nick_to_tournament
    global s_command_player_table
    global s_command_all_player_name_by_tournament
    global s_command_all_player_nick_by_tournament
    global s_command_tournament_id_to_name
    global s_command_id_table
    global s_command_player_name_list
    global s_command_player_nick_list

    s_command_player_table[str(participant['id'])] = str(participant['name'])
    s_command_id_table[str(participant['name'])] = str(participant['id'])
    s_command_nick_to_tournament[str(participant['name'])] = tournament
    temp_nick = str(participant['name'])
    if not(participant['name'] in s_command_player_nick_list):
        s_command_player_nick_list.append(str(participant['name']))

    if participant['misc'] != None:
        temp_name = str(participant['misc'])
        if not(participant['misc'] in s_command_player_name_list):
            s_command_player_name_list.append(str(participant['misc']))
        s_command_name_to_tournament[str(participant['misc'])] = tournament
        s_command_id_table[str(participant['misc'])] = str(participant['id'])
    else :
        temp_name = str(participant['name'])
        if not(participant['name'] in s_command_player_name_list):
            s_command_player_name_list.append(str(participant['name']))
        s_command_name_to_tournament[str(participant['name'])] = tournament

    return temp_nick, temp_name

def start_tournament(tournament, botname):
    global s_command_name_to_tournament
    global s_command_nick_to_tournament
    global s_command_player_table
    global s_command_all_player_name_by_tournament
    global s_command_all_player_nick_by_tournament
    global s_command_tournament_id_to_name
    global s_command_id_table
    global s_command_player_name_list
    global s_command_player_nick_list

    try:
        temp_tournament = challonge.tournaments.show(tournament)

        participants = challonge.participants.index(temp_tournament['id'])
        s_command_tournament_id_to_name[tournament] = temp_tournament['name']

        temp_name_list = []
        temp_nick_list = []

        print("--- check tournament status ---")
        for tournament_ID in list(s_command_all_player_name_by_tournament.keys()):
            print(tournament_ID)
            check_tournament_status(tournament_ID)
        print("--- check tournament end ---")

        # 参加者とトーナメントID紐づけ処理 & 点呼用リスト作成処理
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(set_participant_info, participant, tournament) for participant in participants]
            for future in concurrent.futures.as_completed(futures):
                temp_nick_list.append(future.result()[0])
                temp_name_list.append(future.result()[1])

        # print(s_command_id_table)
        list(set(s_command_player_name_list))
        list(set(s_command_player_nick_list))
        list(set(temp_name_list))
        list(set(temp_nick_list))
        s_command_all_player_name_by_tournament[tournament] = temp_name_list
        s_command_all_player_nick_by_tournament[tournament] = temp_nick_list

        start_message = "トーナメントの勝利報告を受け付け開始します"
        start_message += '\n' + "勝利者はこのBotへメンションのみを飛ばしてください(下記文章をコピー&ペーストしてメッセージ送信でOK)"
        start_message += '\n' + '@' + str(botname)
        start_message += '\n\n' + "■トーナメント情報"
        # start_message += '\n' + "参加人数：" + str(len(challonge.participants.index(tournament)))
        start_message += '\n' + "参加人数：" + str(len(participants))
        start_message += '\n' + "大会形式：" + temp_tournament['tournament_type']
        start_message += '\n' + "トーナメント表：" + "https://challonge.com/ja/" + str(tournament)

        embed = discord.Embed( # Embedを定義する
                            title=temp_tournament['name'],
                            color=0x0000ff, # フレーム色指定
                            description="■勝利報告受付開始", # Embedの説明文 必要に応じて
                            url="https://challonge.com/ja/" + str(tournament) # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        embed.add_field(name="", value=start_message)  # フィールドを追加。

    except:
        embed = discord.Embed( # Embedを定義する
                            title="■トーナメント指定エラー",
                            color=0xffc800, # フレーム色指定
                            description="指定されたトーナメントが見つかりませんでした。\nIDがあっているか確認してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        
        embed.add_field(name="指定されたトーナメントID", value=tournament)  # フィールドを追加。

    return embed

async def call(message, msg, botname, tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament):
    if len(msg) <= 2:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="トーナメントIDを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        await message.channel.send(embed=embed)
        return

    print('--- 参加者情報紐づけ開始 ---')
    # 参加者名とIDを紐づけ
    tournaments = msg[2:]
    
    get_tournament_data(tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament)

    print('--- トーナメント情報取得完了 ---')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(start_tournament, tournament, botname) for tournament in tournaments]
        for future in concurrent.futures.as_completed(futures):
            await message.channel.send(embed=future.result())

    print('--- トーナメント毎の設定完了 ---')
    tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament = set_tournament_data()
    print(id_table) # 参加者一覧表示
    print('--- 参加者情報紐づけ完了 ---')

    return tournament_id_to_name, player_table, id_table, nick_to_tournament, player_nick_list, player_name_list, name_to_tournament, all_player_name_by_tournament, all_player_nick_by_tournament

