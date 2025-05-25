import sys
import discord
import threading
import datetime
import asyncio

### discord周りの設定
# Bot用トークン
TOKEN = "" # 公開用に削除済み

# インテントの生成
intents = discord.Intents.default()
intents.messages        = True    # on_message用Intent
intents.message_content = True    # message.content参照用
intents.members         = True    # on_member_join用Intent
intents.reactions       = True    # on_reaction_add用Intent
intents.dm_messages     = True

# クライアントの生成
client = discord.Client(intents=intents)

### Global Variables
lock = threading.RLock()        # 再起呼び出し対応ロック
answerers = {}
members = []

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):
    global answerers
    global members
    # 自分のメッセージを無効
    if message.author == client.user:
        return

    with lock:
        dt = datetime.datetime.now()
        # 自身宛のDMか判定
        if(type(message.channel) == discord.DMChannel) and (client.user == message.channel.me):
            # ねむさんのギルド取得
            nemu_guild = client.get_guild(836810678597582868)
            answerer = nemu_guild.get_member(message.author.id)

            if (str(message.content) == "reset"):
                await message.author.send("解答者の控室送りを実行します……")
                if not(any(answerers)):
                    await message.author.send("まだ誰も解答してません。\n処理を中断します")
                    return
                    
                file_name = dt.strftime('%Y%m%d%H%M%S') + '_answerers.txt'
                f = open(file_name, 'w', encoding='UTF-8')

                for answerer_key in answerers.keys():
                    f.write(str(answerer_key) + "\t" + str(answerers[answerer_key]) + "\n")

                # 出力用ファイルクローズ
                f.close()

                print(answerers)
                answerers.clear()

                async def member_remove_roll(member, guild, role):
                    await member.remove_roles(guild.get_role(role))
                    await member.move_to(guild.get_channel(1156743335927631942))

                async def member_move(member, guild):
                    if (guild.get_role(1157125018833129512) in member.roles):
                        await member_remove_roll(member, guild, 1157125018833129512)
                    if (guild.get_role(1157125345389068358) in member.roles):
                        await member_remove_roll(member, guild, 1157125345389068358)
                    if (guild.get_role(1157125401265590333) in member.roles):
                        await member_remove_roll(member, guild, 1157125401265590333)
                    if (guild.get_role(1157125440801079426) in member.roles):
                        await member_remove_roll(member, guild, 1157125440801079426)

                tsks = [asyncio.create_task(member_move(member, nemu_guild)) for member in members]
                await asyncio.gather(*tsks)

                members.clear()
                await message.author.send("解答者の控室送りが完了しました")

                return

            # 解答済みか判定
            if (nemu_guild.get_role(1157125018833129512) in answerer.roles) or (nemu_guild.get_role(1157125345389068358) in answerer.roles) or (nemu_guild.get_role(1157125401265590333) in answerer.roles) or (nemu_guild.get_role(1157125440801079426) in answerer.roles):
                await message.author.send("解答の変更は受け付けられません")
                return

            if ((str(message.content) == "A") or (str(message.content) == "a")):
                await answerer.add_roles(nemu_guild.get_role(1157125018833129512))
                await answerer.move_to(nemu_guild.get_channel(1156607971053285509))
                answerers[str(answerer.display_name)] = "A"
                members.append(answerer)
                await message.author.send("選択肢Aで解答を受理しました")
                return

            if ((str(message.content) == "B") or (str(message.content) == "b")):
                await answerer.add_roles(nemu_guild.get_role(1157125345389068358))
                await answerer.move_to(nemu_guild.get_channel(1156608100409810954))
                answerers[str(answerer.display_name)] = "B"
                members.append(answerer)
                await message.author.send("選択肢Bで解答を受理しました")
                return

            if ((str(message.content) == "C") or (str(message.content) == "c")):
                await answerer.add_roles(nemu_guild.get_role(1157125401265590333))
                await answerer.move_to(nemu_guild.get_channel(1156608181674459167))
                answerers[str(answerer.display_name)] = "C"
                members.append(answerer)
                await message.author.send("選択肢Cで解答を受理しました")
                return

            if ((str(message.content) == "D") or (str(message.content) == "d")):
                await answerer.add_roles(nemu_guild.get_role(1157125440801079426))
                await answerer.move_to(nemu_guild.get_channel(1156608246560342156))
                answerers[str(answerer.display_name)] = "D"
                members.append(answerer)
                await message.author.send("選択肢Dで解答を受理しました")
                return

            await message.author.send("解答はA、B、C、Dのいずれかでお送りください")

            return

    return

client.run(TOKEN)
