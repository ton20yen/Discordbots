import discord
import datetime
import time
import threading

### discord周りの設定
# Bot用トークン
TOKEN = "" # 公開用に削除済み

# インテントの生成
intents = discord.Intents.default() # 一括設定せず、個別に設定したい…
intents.messages        = True    # on_message用Intent
intents.message_content = True    # message.content参照用
intents.members         = True    # on_member_join用Intent
intents.reactions       = True    # on_reaction_add用Intent
intents.dm_messages     = True

# RAM
lock = threading.RLock()            # 再起呼び出し対応ロック
messeage_author_log = {}            # 誰が、いつ、何を書いたかのログ
black_list = []
black_list.extend(["https://discord.gg/sexleaks", "https://discord.gg/xsex", "https://discord.gg/CYNumE8ABr"])

messeage_edit_log = []              # 画像付きメッセージの誤検知避け用list
messeage_edit_flag = {}             # 画像付きメッセージの誤検知避け用dict
messeage_embed_flag = {}            # 埋め込み付きメッセージの誤検知避け用dict
https_last_time = {}                # 
last_author = None

# クライアントの生成
client = discord.Client(intents=intents, max_messages=65535)

def del_log(date_log, content_log):
    del(date_log[0])
    del(content_log[0])

    return date_log.copy(), content_log.copy()

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):

    dt = time.time()

    with lock:
        # 自分のメッセージを無効
        if message.author == client.user:
            return

        if ("@everyone" in message.content) or ("@here" in message.content):
            for ban_url in black_list:
                if ban_url in message.content:
                    print('--- ブラックリストを検知 ---')
                    print('--- スパムをBANしました ---')
                    print('name:' + str(message.author.name))
                    print('nick:' + str(message.author.nick))
                    print(message.content)
                    await message.author.ban(delete_message_days=7)

            # 全体メンションを検知
            if message.author.id in messeage_author_log:
                # 時間と内容を保存
                messeage_author_log[message.author.id]['date'].append(dt)
                messeage_author_log[message.author.id]['content'].append(message.content)

                while (messeage_author_log[message.author.id]['date'][-1] - messeage_author_log[message.author.id]['date'][0] > float(180)) or \
                    (len(messeage_author_log[message.author.id]['date']) > 3):
                    # 古いログを削除
                    messeage_author_log[message.author.id]['date'], messeage_author_log[message.author.id]['content'] = \
                    del_log(messeage_author_log[message.author.id]['date'], messeage_author_log[message.author.id]['content'])

                if len(messeage_author_log[message.author.id]['date']) == 3:
                    # 一定時間内に複数回検知したか
                    print('--- 一定時間内に複数回のメンションを検知 ---')
                    if (messeage_author_log[message.author.id]['content'][0] == messeage_author_log[message.author.id]['content'][1]) and \
                    (messeage_author_log[message.author.id]['content'][1] == messeage_author_log[message.author.id]['content'][2]):

                        if(type(message.author) is discord.User):
                            await message.guild.ban(user=message.author, delete_message_days=7, reason='スパム認定')
                            print('--- スパムをBANしました ---')
                            print('name:' + str(message.author.name))
                        else:
                            await message.author.ban(delete_message_days=7, reason='スパム認定')
                            print('--- スパムをBANしました ---')
                            print('name:' + str(message.author.name))
                            print('nick:' + str(message.author.nick))

                print(messeage_author_log)
                return

            else:
                message_date = []
                massage_content = []

                message_date.append(dt)
                massage_content.append(message.content)

                messeage_author_log[message.author.id] = {'date':message_date.copy(), 'content':massage_content.copy()}
                print(messeage_author_log)
        else:
            # 全体メンションでなければ過去ログ削除
            if message.author.id in messeage_author_log:
                del(messeage_author_log[message.author.id])
    return

def get_user_rank(roles):
    rank = ""

    for user_role in roles:
        if user_role.id == 1076311874573975602:
            rank = "ベテラン勢"
            break
        elif user_role.id == 1002737039411785749:
            rank = "中級/復帰勢"
            break
        elif user_role.id == 1067415878104256562:
            rank = "初級/初心者"
            break
        else:
            rank = "無所属"

    return rank

# サーバー脱退者を検知したときに呼ばれる
@client.event
async def on_raw_member_remove(payload):
    description = "加入日：" + str(payload.user.joined_at)
    description += "\n" +"脱退日：" + str(datetime.datetime.now())

    color = 0x0000ff
    post_channel = await client.fetch_channel(1292337737080504330)
    description += "\n" + "脱退者：" + payload.user.display_name + "(" + str(payload.user) + ")"
    description += "\n" + "脱退者所属：" + get_user_rank(payload.user.roles)
    embed = discord.Embed( # Embedを定義する
                            title="■サーバー脱退者検知",
                            color=color, # フレーム色指定
                            description=description, # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

    embed.set_author(name=(payload.user.display_name + "(" + str(payload.user) + ")"),
                    icon_url=payload.user.display_avatar
                    )

    await post_channel.send(embed=embed)

    return

# サーバー参加者を検知したときに呼ばれる
@client.event
async def on_member_join(member):
    dm_member = member.guild.get_member() # 公開用に削除済み

    dt = datetime.datetime.now()
    print(dt.strftime('[%Y-%m-%d %H:%M:%S]') + ' サーバーに新しく人が来ました!')
    print(str(member.display_name) + ': ' + str(member))
    dm_message =  '■天則交流用サーバーに新しく人が来ました'
    dm_message += '\n' + '表示名: ' + str(member.display_name)
    dm_message += '\n' + '@' + str(member)

    dm_message =  '\n' + str(member.mention)
    dm_message += '\n' + 'はじめまして！'
    dm_message += '\n'
    dm_message += '\n' + 'まずは下記のどちらかにプロフィールを書き込んでください！'
    dm_message += '\n' + '初心者、久しぶりにやる方はこちら： https://discord.com/channels/836810678597582868/1016188606173421669'
    dm_message += '\n' + '実力に自信のある方はこちら： https://discord.com/channels/836810678597582868/1076116359416651806'
    dm_message += '\n'
    dm_message += '\n' + 'その後、 ' + str(dm_member.mention) + 'と数戦対戦し実力に応じたロール(初心者・初級者、中級者・復帰勢、ベテラン勢のいずれか)を付与いたします。'
    dm_message += '\n' + '対戦を行う準備が整いましたら ' + str(dm_member.mention) + ' までダイレクトメッセージを送ってください！'
    # dm_message += '\n' + 'その後、副管理人( ' + str(temp_member_a.mention) + ' もしくは ' + str(temp_member_b.mention) + ' )と数戦対戦し実力に応じたロール(初心者・初級者、中級者・復帰勢、ベテラン勢のいずれか)を付与いたします。'
    # dm_message += '\n' + '対戦を行う準備が整いましたら 副管理人( ' + str(temp_member_a.mention) + 'と ' + str(temp_member_b.mention) + ' )までダイレクトメッセージを送ってください！'
    # dm_message += '\n' + '※副管理人の都合により、対戦可能な時間は21:00(JST)以降となります。'
    dm_message += '\n' + 'ロールによって自分が戦いたい相手を見つけやすくなりますのでご協力をおねがいします！ '
    dm_message += '\n'
    dm_message += '\n' + 'ここのサーバーでは対戦補助ツールとしてオートパンチ(接続補助)/ソクロール(対戦環境改善)/Giuroll(対戦環境改善)の導入を推奨しております。'
    dm_message += '\n' + '・https://discordapp.com/channels/836810678597582868/1073050281782292512'
    dm_message += '\n' + '・https://discordapp.com/channels/836810678597582868/1071255150351618068'
    dm_message += '\n' + '・https://discord.com/channels/836810678597582868/1297183790690603009'
    dm_message += '\n' + 'よかったらこちらもご覧ください！'
    dm_message += '\n' + '※ポート開放ができる方はオートパンチは不要です'

    dm_message += '\n\n' + 'For overseas players'
    dm_message += '\n' + 'I ask you to read this message link at least once.：' + 'https://discord.com/channels/836810678597582868/999561213451190322/1370600070847660053'
    dm_message += '\n' + 'Thanks for reading'

    await dm_member.send(dm_message)

    return

# リアクションを検知した時に呼ばれる
@client.event
async def on_raw_reaction_add(payload):
    user = payload.member

    reaction_channel = await client.fetch_channel(payload.channel_id)
    reaction_massage = await reaction_channel.fetch_message(payload.message_id)

    # リアクションされたのが利用規約メッセージ
    if reaction_massage.id == 0: # 公開用に削除済み
        # かつ 指定された絵文字
        if payload.emoji.name == "nemu_defo":
            nemu_guild = client.get_guild() # 公開用に削除済み
            await user.add_roles(nemu_guild.get_role()) # 公開用に削除済み
            dm_member = nemu_guild.get_member() # 公開用に削除済み
            # dm_member = member.guild.get_member() # 公開用に削除済み

            dm_message =  '■はじめにお読みくださいのメッセージにリアクションされました'
            dm_message += '\n' + '表示名: ' + str(user.display_name)
            dm_message += '\n' + '@' + str(user)
            await dm_member.send(dm_message)

            return

    return

# メッセージ編集/削除ログ保存
async def save_for_message_edit_log(befor_message, delete_flag):
    global last_author

    if befor_message.author.bot:
        return

    # 無視するチャンネルリスト
    ignore_channels = []
    ignore_channels.extend([1103207507180130364, 1234705273978093619, 1078275519654674502, 1078275638995202110, 1126500212286967849, 1162011220623249418, 1179762961783468098, 1179774522115752016])
    ignore_channels.extend([1119790494491349102, 1015989636671221880, 1119790679170748437, 1251362344131629159, 1119792016558129272])
    ignore_channels.extend([1015989695613763745, 1016004995398778931, 1181788202781126746, 1016005065359753216, 1074714156080566322])
    ignore_channels.extend([1016657834009710602, 1074714238205055108, 1076152297110913064, 1076152399821025351, 1126853274935492718, 1126853335027298395, 1159844525498441869, 1159844670726213653, 1159855553678422076])

    ignore_words = []
    ignore_words.extend([":5232", ":6980" , ":7500", ":7720", ":8072"])
    ignore_words.extend([":10350", ":10480", ":10624", ":10800", ":10801", ":10809", ":11222", ":11376", ":11874", ":12288", ":12528", ":14080", ":17603"])
    ignore_words.extend([":20800", ":21818", ":25488", "25600", ":27600", ":28800", ":29200"])
    ignore_words.extend([":53776", ":55551", ":55983"])
    ignore_words.extend([":63151"])
    ignore_words.extend(["再募", "さいぼ", "再ぼ"])

    if befor_message.channel.id in ignore_channels:
        for ignore_word in ignore_words:
            if (ignore_word in befor_message.content):
                print("--- 対戦募集文の変更を検知しました ---")
                return

    description = "編集日：" + str(datetime.datetime.now())
    description += "\n" + "メッセージがあったChannel名：" + str(befor_message.channel)

    if delete_flag:
        color = 0xffc800
        # post_channel = await client.fetch_channel(1248418800584360028) # 削除チャンネル
        post_channel = await client.fetch_channel(1248079613062549574) # 編集チャンネル
        description += "\n\n" + "--- 以下削除前メッセージ ---" + "\n" + befor_message.content
        embed = discord.Embed( # Embedを定義する
                                title="■メッセージ削除検知",
                                color=color, # フレーム色指定
                                description=description, # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )
    else:
        color = 0x0000ff
        post_channel = await client.fetch_channel(1248079613062549574)
        description += "\n" + "編集されたメッセージへのリンク：" + befor_message.jump_url
        description += "\n\n" + "--- 以下編集前メッセージ ---" + "\n" + befor_message.content
        embed = discord.Embed( # Embedを定義する
                                title="■メッセージ編集検知",
                                color=color, # フレーム色指定
                                description=description, # Embedの説明文 必要に応じて
                                url="" # これを設定すると、タイトルが指定URLへのリンクになる
                                )

    embed.set_author(name=(befor_message.author.display_name + "(" + str(befor_message.author) + ")"),
                    icon_url=befor_message.author.display_avatar
                    )

    attachments_files = []
    if any(befor_message.attachments):
        for attachment in befor_message.attachments:
            try:
                attachments_files.append(await attachment.to_file(use_cached=True))
            except:
                break

    target_thread = None
    for thread in post_channel.threads:
        if thread.name == str(befor_message.author):
            title_message = "■スレッド更新通知"
            target_thread = thread
            description = "下記スレッドを更新しました。\n" + target_thread.jump_url
            break

    if target_thread == None:
        title_message = "■スレッド新規作成通知"
        target_thread = await post_channel.create_thread(name=str(befor_message.author))
        description = "スレッドを新規作成しました。作成したスレッドは下記です。\n" + target_thread.jump_url

    await target_thread.send(embed=embed, files=attachments_files)

    embed = discord.Embed( # Embedを定義する
                            title=title_message,
                            color=color, # フレーム色指定
                            description=description, # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
    embed.set_author(name=(befor_message.author.display_name + "(" + str(befor_message.author) + ")"),
                    icon_url=befor_message.author.display_avatar
                    )

    if last_author == befor_message.author:
        print("--- 連続でメッセージ編集を検知しました ---")
        return
    else:
        await post_channel.send(embed=embed)
        last_author = befor_message.author

    return

# メッセージ編集を検知した際に呼ばれる
@client.event
async def on_raw_message_edit(payload):
    if payload.cached_message != None:
        if payload.cached_message.author.bot:
            return

        with lock:
            if any(payload.cached_message.attachments):
                if payload.message_id in messeage_edit_log:
                    # print("--- 画像貼り付け2回目 ---")
                    if messeage_edit_flag[payload.message_id]:
                        await save_for_message_edit_log(payload.cached_message, False)
                        messeage_edit_flag[payload.message_id] = False
                    else:
                        messeage_edit_flag[payload.message_id] = True

                else:
                    # print("--- 画像貼り付け初回 ---")
                    messeage_edit_log.append(payload.message_id)
                    messeage_edit_flag[payload.message_id] = False
            else:
                if "http" in payload.cached_message.content:
                    # print("--- URLを検知 ---")
                    if not(payload.message_id in https_last_time):
                        https_last_time[payload.message_id] = time.time()
                    else:
                        # print(time.time() - https_last_time[payload.message_id])
                        if (time.time() - https_last_time[payload.message_id]) < 0.5:
                            # print("--- 0.5s経ってないので無視 ---")
                            return
                        https_last_time[payload.message_id] = time.time()
                        await save_for_message_edit_log(payload.cached_message, False)
                else:
                    await save_for_message_edit_log(payload.cached_message, False)

    return

# メッセージ削除を検知した際に呼ばれる
@client.event
async def on_raw_message_delete(payload):
    if payload.cached_message != None:
        if payload.cached_message.author.bot:
            return

        await save_for_message_edit_log(payload.cached_message, True)

    return

client.run(TOKEN)
