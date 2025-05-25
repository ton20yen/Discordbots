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

async def call(message, msg, ts_flag):
    if len(msg) <= 3:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="トーナメントIDと参加者募集メッセージのIDを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)
        return False

    # channelIDとmsgIDに分割
    ids = []
    ids = msg[2].split('-')

    print('--- 参加者登録開始 ---')
    specify_role_flag = False
    try:
        # 指定されたchannelIDとmsgIDを元にメッセージを特定
        poll_channel = message.guild.get_channel(int(ids[0]))
        poll_massage = await poll_channel.fetch_message(int(ids[1]))
    except:
        try:
            # ロール指定か判定
            ids[0] = ids[0].replace('<@&', '')
            ids[0] = ids[0].replace('>', '')
            specify_role = message.guild.get_role(int(ids[0]))
            specify_role_flag = True
        except:
            embed = discord.Embed( # Embedを定義する
                                title="■チャンネル/メッセージID指定エラー",
                                color=0xffc800, # フレーム色指定
                                description="指定されたメッセージが見つかりませんでした。以下3点を確認してください。\n①指定したメッセージが存在するチャンネルにbotの閲覧権限があるか\n②IDの指定順が「チャンネルID-メッセージID 大会ID」になっているか\n③指定したIDがあっているか", # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )
            await message.channel.send(embed=embed)
            return False

    tournaments = msg[3:] # トーナメント指定部分のみ取り出し

    if ts_flag == False:
        embed = discord.Embed( # Embedを定義する
                            # title=this_tournament['name'],
                            color=0x0000ff, # フレーム色指定
                            description="■参加者登録開始", # Embedの説明文 必要に応じて
                            # url="https://challonge.com/ja/" + str(tournament) # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        embed.add_field(name="", value='参加者登録を開始します……\n--- 登録作業中 しばらくお待ちください ---')  # フィールドを追加。
        await message.channel.send(embed=embed)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        remove_invalid_futures = [executor.submit(remove_invalid_tournments, tournament) for tournament in tournaments]
        for remove_invalid_future in concurrent.futures.as_completed(remove_invalid_futures):
            valid_flag, t_id = remove_invalid_future.result()

            if ts_flag == False:
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

    print('--- トーナメントの選別 & 初期化完了 ---')

    users = []
    if specify_role_flag:
        users = specify_role.members
    else:
        # リアクション者を全員参加者として登録
        for poll_reaction in poll_massage.reactions:
            async for user in poll_reaction.users():
                if not(user.bot):
                    users.append(user)

    # 大会数で人数を割る
    random.shuffle(users)
    tournament_user = numpy.array_split(users, len(tournaments))

    tournament_index = {}
    i = 0
    for tournament in tournaments:
        tournament_index[tournament] = tournament_user[i]
        i += 1

    # 並列で登録作業
    with concurrent.futures.ThreadPoolExecutor() as executor:
        create_tournments_futures = [executor.submit(create_tournments, tournament_index, tournament) for tournament in tournaments]
        for create_tournments_future in concurrent.futures.as_completed(create_tournments_futures):
            if ts_flag == False:
                await message.channel.send(embed=create_tournments_future.result())

    print('--- トーナメント表作成完了 ---')
    return True

