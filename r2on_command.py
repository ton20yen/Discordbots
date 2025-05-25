import discord
import challonge
from challonge import api
import concurrent.futures
import random
import numpy

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
    challonge.participants.create(tournament_id, user)

async def create_team_data(message, team_battle_data, player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num):
    system_message = "ランダム2onを開始します"
    system_message += "\n" + "チームメンバーは下記の通りです。"
    system_message += "\n" + "■チーム組み合わせ"

    player_name_list.clear()
    player_nick_list.clear()
    for team in team_battle_data["teams"]:
        system_message += "\n" +  "・" + str(team["name"])
        loop_count = 0
        for loop_count in range(len(team["member"])):
            player_name_list.append(str(team["member"][loop_count]))
            player_nick_list.append(str(team["member_id"][loop_count]))
            member_to_team[team["member"][loop_count]] = str(team["name"])
            member_id_to_team[team["member_id"][loop_count]] = str(team["name"])
            loop_count = loop_count + 1

    match_report_num.clear()
    embed = discord.Embed( # Embedを定義する
                        title="■チーム戦データ読み込み完了",
                        color=0x0000ff, # フレーム色指定
                        description=system_message, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )

    await message.channel.send(embed=embed)

    print('--- トーナメント表作成完了 ---')

    return player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num

async def call(message, msg):
    if len(msg) <= 3:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="トーナメントIDと参加者募集メッセージのIDを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)
        return

    # channelIDとmsgIDに分割
    ids = []
    ids = msg[2].split('-')

    print('--- 参加者登録開始 ---')
    try:
        # 指定されたchannelIDとmsgIDを元にメッセージを特定
        poll_channel = message.guild.get_channel(int(ids[0]))
        poll_massage = await poll_channel.fetch_message(int(ids[1]))
    except:
        embed = discord.Embed( # Embedを定義する
                            title="■チャンネル/メッセージID指定エラー",
                            color=0xffc800, # フレーム色指定
                            description="指定されたメッセージが見つかりませんでした。以下3点を確認してください。\n①指定したメッセージが存在するチャンネルにbotの閲覧権限があるか\n②IDの指定順が「チャンネルID-メッセージID 大会ID」になっているか\n③指定したIDがあっているか", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        await message.channel.send(embed=embed)
        return

    tournaments = msg[3:] # トーナメント指定部分のみ取り出し

    if len(tournaments) > 1:
        error_embed = discord.Embed( # Embedを定義する
                title="■トーナメント指定数エラー",
                color=0xffc800, # フレーム色指定
                description="トーナメントの指定は1つまでです。", # Embedの説明文 必要に応じて
                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                )
        await message.channel.send(embed=error_embed)
        return

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
                return

    print('--- トーナメントの選別 & 初期化完了 ---')

    users = []
    # リアクション者を全員参加者として登録
    for poll_reaction in poll_massage.reactions:
        async for user in poll_reaction.users():
            if not(user.bot):
                users.append(user)

    # 適当に2人チームを作成
    random.shuffle(users)

    team_battle_data = {}
    team_battle_data["member_num"] = 2
    team_battle_data['win'] = 2
    team_battle_data['waseda_flag'] = True
    team_battle_data["report_num"] = 2
    team_battle_data["teams"] = []

    i = 0
    team_name = ""
    team_member = []
    team_member_id = []
    temp_users = users
    team_data = {}
    team_roll_call_count = {}

    for i in range( int((((len(temp_users)/2)*10)+5)/10) ):
        if len(users) == 1:
            team_user_A = users.pop(0)
            team_name = team_user_A.display_name + "チーム"
            team_member.append(team_user_A.display_name)
            team_member_id.append(team_user_A.name)
            team_roll_call_count[team_name] = 1

        else:
            team_user_A = users.pop(0)
            team_user_B = users.pop(0)
            team_name = team_user_A.display_name + "・" + team_user_B.display_name + "チーム"
            team_member.extend([team_user_A.display_name, team_user_B.display_name])
            team_member_id.extend([team_user_A.name, team_user_B.name])
            team_roll_call_count[team_name] = 2

        team_data["name"] = team_name
        team_data["member"] = team_member.copy()
        team_data["member_id"] = team_member_id.copy()
        team_data["roll_call_count"] = team_battle_data["member_num"]

        team_battle_data["teams"].append(team_data.copy())

        team_member.clear()
        team_member_id.clear()

    print(team_battle_data)

    # 並列で登録作業
    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(participant_entry, arg["name"], tournaments[0]) for arg in team_battle_data["teams"]]

    return team_battle_data, team_roll_call_count