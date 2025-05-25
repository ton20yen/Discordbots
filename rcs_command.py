import discord

async def call(message, player_table, roll_call_message_obj):
    if (not(any(player_table))):
        embed = discord.Embed( # Embedを定義する
                            title="■トーナメント未指定エラー",
                            color=0xffc800, # フレーム色指定
                            description="先に!sコマンドでトーナメントを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        await message.channel.send(embed=embed)
        return

    print('--- 点呼開始 ---')
    emoji = "\N{OK HAND SIGN}"
    embed = discord.Embed( # Embedを定義する
                        # title=tournament['name'], # タイトル
                        color=0x0000ff, # フレーム色指定
                        description="■点呼開始", # Embedの説明文 必要に応じて
                        # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                        )

    roll_call_message = "点呼を開始します"
    roll_call_message += "\n" + "各トーナメント参加者はこのメッセージに" + emoji + "でリアクションをお願いします"
    embed.add_field(name="",value=roll_call_message)  # フィールドを追加。

    roll_call_message_obj = await message.channel.send(embed=embed)
    await roll_call_message_obj.add_reaction(emoji)
    # print(roll_call_message_obj.guild.members)
    return roll_call_message_obj

