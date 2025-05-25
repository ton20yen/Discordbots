import discord
import concurrent.futures
import datetime
import challonge

def search_author(target_message):
    if target_message.author.bot:
        return None
    if target_message.author.id == 0:
        # 公開用に削除済み
        return None

    return target_message.author

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
                        title="■ロール付与開始",
                        color=0x0000ff, # フレーム色指定
                        description="ロール付与を開始します。しばらくお待ちください……\n" + progress + "\n" + progress_bar, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    await progress_message.edit(embed=embed)

    return

async def add_role_from_channel(add_role_name, target_channel, progress_message):
    print("--- チャンネル指定でロール付与 ---")
    # 過去45日間の発言を取り出し
    target_messages = [target_message async for target_message in target_channel.history(limit=None ,after=(datetime.datetime.today() - datetime.timedelta(days=45)))]

    target_authors = []

    # ロール付与
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(search_author, target_message) for target_message in target_messages]
        for future in concurrent.futures.as_completed(futures):
            if future.result() != None:
                if not(future.result() in target_authors):
                    target_authors.append(future.result())

    compleat_num = 0

    for target_author in target_authors:
        await target_author.add_roles(add_role_name)
        compleat_num += 1
        await edit_progress_message(compleat_num, len(target_authors), progress_message)

    return target_authors

async def add_role_from_message(add_role_name, target_massage, progress_message):
    compleat_num = 0 
    estimate_num = 0

    for poll_reaction in target_massage.reactions:
        async for user in poll_reaction.users():
            estimate_num += 1

    print("--- メッセージ指定でロール付与 ---")
    # リアクション者を全員参加者として登録
    target_authors = []
    for poll_reaction in target_massage.reactions:
        async for user in poll_reaction.users():
            compleat_num += 1
            if user.bot:
                continue
            if user.id == 0:
                # 公開用に削除済み
                continue
            await user.add_roles(add_role_name)
            target_authors.append(user)

            await edit_progress_message(compleat_num, estimate_num, progress_message)

    return target_authors

async def add_role_from_challonge(add_role_name, target_participants, progress_message):
    print("--- challongeID指定でロール付与 ---")
    compleat_num = 0
    target_authors = []

    for target_participant in target_participants:
        if target_participant['misc'] == None:
            target_members = await progress_message.guild.query_members(target_participant['name'])
        else:
            target_members = await progress_message.guild.query_members(target_participant['misc'])

        print(target_members)
        if len(target_members) == 1:
            target_authors.append(target_members[0])
            await target_members[0].add_roles(add_role_name)
            compleat_num += 1
            await edit_progress_message(compleat_num, len(target_participants), progress_message)

        elif len(target_members) > 1:
            for target_member in target_members:
                if target_participant['misc'] != None:
                    if target_member.name == target_participant['misc']:
                        await target_member.add_roles(add_role_name)
                        target_authors.append(target_member)
                        break

                if target_member.display_name == target_participant['name']:
                    await target_member.add_roles(add_role_name)
                    target_authors.append(target_member)
                    break

            compleat_num += 1
            await edit_progress_message(compleat_num, len(target_participants), progress_message)

    return target_authors

async def call(message, msg):
    if len(msg) <= 3:
        embed = discord.Embed( # Embedを定義する
                            title="■引数エラー",
                            color=0xffc800, # フレーム色指定
                            description="引数の数が誤っています。", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)
        return

    # channelIDとmsgIDに分割
    ids = []
    ids = msg[2].split('-')

    role_name = msg[3] # 付与ロール名取り出し

    # 付与しようとしているロールがすでにないか確認
    create_role_flag = True
    for guildrole in message.guild.roles:
        if guildrole.name == role_name:
            add_role_name = guildrole
            create_role_flag = False
            break

    if create_role_flag:
        add_role_name = await message.guild.create_role(name=role_name, mentionable=True) # role生成

    target_participants = []
    try:
        # 指定されたchannelIDとmsgIDを元にメッセージを特定
        target_channel = message.guild.get_channel(int(ids[0]))
    except:
        try:
            # challongeから参加者を抽出
            # 参加者名でfetch、合致する人にロール付与
            target_participants = challonge.participants.index(ids[0])

        except:
            embed = discord.Embed( # Embedを定義する
                                title="■チャンネルID/challongeID指定エラー",
                                color=0xffc800, # フレーム色指定
                                description="指定されたチャンネルもしくはトーナメントが見つかりませんでした。以下3点を確認してください。\n①指定したチャンネルにbotの閲覧権限があるか\n②IDの指定順が「チャンネルID 付与ロール名」もしくは「challongeID 付与ロール名」になっているか\n③指定したIDがあっているか", # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )
            await message.channel.send(embed=embed)
            return

    # メッセージ指定がされているかで分岐
    specify_massage_flag = False
    if len(ids) > 1:
        try:
            specify_massage = await target_channel.fetch_message(int(ids[1]))
            specify_massage_flag = True
        except:
            embed = discord.Embed( # Embedを定義する
                                title="■メッセージID指定エラー",
                                color=0xffc800, # フレーム色指定
                                description="指定されたメッセージが見つかりませんでした。以下3点を確認してください。\n①指定したチャンネルにbotの閲覧権限があるか\n②IDの指定順が「チャンネルID-メッセージID 付与ロール名」になっているか\n③指定したIDがあっているか", # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )
            await message.channel.send(embed=embed)
            return

    progress_bar = "□□□□□□□□□□"
    embed = discord.Embed( # Embedを定義する
                        title="■ロール付与開始",
                        color=0x0000ff, # フレーム色指定
                        description="ロール付与を開始します。しばらくお待ちください……\n進捗率：0%\n" + progress_bar, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    progress_message = await message.channel.send(embed=embed)

    target_authors = []
    if specify_massage_flag:
        target_authors = await add_role_from_message(add_role_name, specify_massage, progress_message)
    else:
        if len(target_participants) == 0:
            target_authors = await add_role_from_channel(add_role_name, target_channel, progress_message)
        else:
            target_authors = await add_role_from_challonge(add_role_name, target_participants, progress_message)

    print("--- 付与完了 ---")

    discordID_List = []
    target_name_list = []
    for target_author in target_authors:
        target_name_list.append(target_author.display_name)
        discordID_List.append(target_author)

    target_name = ''
    for name in target_name_list:
        target_name += name.replace('_', '\_') + "\n"

    discordID = ''
    for id in discordID_List:
        discordID += str(id).replace('_', '\_') + "\n"

    description_word = "ロール付与が完了しました。付与した情報は下記の通りです。" + "\n"
    description_word += "人数：" + str(len(target_authors)) + "\n"
    description_word += "付与ロール名：" + str(add_role_name) + "\n"

    embed = discord.Embed( # Embedを定義する
                        title="■ロール付与完了",
                        color=0x0000ff, # フレーム色指定
                        description=description_word, # Embedの説明文 必要に応じて
                        url="" # これを設定すると、タイトルが指定URLへのリンクになる
                        )
    
    embed.add_field(name="discordID",value=discordID)  # フィールドを追加
    embed.add_field(name="表示名",value=target_name) # フィールドを追加

    await message.channel.send(embed=embed)

    return