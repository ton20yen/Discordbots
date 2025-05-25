import discord
import challonge

tournament_embed = {}

async def call(message, player_table, roll_call_message_obj, player_name_list, team_battle_data, player_nick_list, name_to_tournament, nick_to_tournament, roll_call_end_message_obj, edit_flag):
    if (not(any(player_table))):
        embed = discord.Embed( # Embedを定義する
                            title="■トーナメント未指定エラー",
                            color=0xffc800, # フレーム色指定
                            description="先に!sコマンドでトーナメントを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        await message.channel.send(embed=embed)
        return roll_call_end_message_obj

    if roll_call_message_obj == None:
        embed = discord.Embed( # Embedを定義する
                            # title=tournament['name'],
                            color=0xffc800, # フレーム色指定
                            description="■点呼未開始エラー", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        embed.add_field(name="", value="点呼が開始されていません")
        await message.channel.send(embed=embed)
        return roll_call_end_message_obj
    else:
        if edit_flag == False:
            embed = discord.Embed( # Embedを定義する
                            # title=tournament['name'], # タイトル
                            color=0x0000ff, # フレーム色指定
                            description="■点呼集計開始", # Embedの説明文 必要に応じて
                            # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                            )
            embed.add_field(name="", value="点呼を集計します……")
            await message.channel.send(embed=embed)

        # 点呼結果表示
        if any(player_name_list):
            if team_battle_data == None:
                for tournament in set(list(name_to_tournament.values())):
                    member_count = 0
                    temp_tournament = challonge.tournaments.show(tournament)

                    embed = discord.Embed( # Embedを定義する
                                        title=temp_tournament['name'], # タイトル
                                        color=0x0000ff, # フレーム色指定
                                        description="■点呼未反応者一覧(自動更新)", # Embedの説明文 必要に応じて
                                        # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                        )

                    # 個人戦の場合
                    no_response_player = ''
                    no_response_player_nick = ''
                    # tournament_name = ''

                    for player_name in player_name_list:
                        if (name_to_tournament[player_name] == tournament):
                            member_count += 1
                            no_response_player += player_name.replace('_', '\_') + "\n"
                            # temp_tournament = challonge.tournaments.show(name_to_tournament[player_name])
                            # tournament_name += temp_tournament['name'] + "\n"

                    for player_nick in player_nick_list:
                        if (nick_to_tournament[player_nick] == tournament):
                            member_count += 1
                            no_response_player_nick += player_nick.replace('_', '\_') + "\n"

                    if member_count != 0:
                        embed.add_field(name="discordID",value=no_response_player)  # フィールドを追加
                        embed.add_field(name="表示名",value=no_response_player_nick) # フィールドを追加
                    else:
                        tournament_embed[tournament].clear_fields()
                        embed.description = "全員揃いました"

                    # embed.add_field(name="大会名",value=tournament_name) # フィールドを追加

                    tournament_embed[tournament] = embed
            else :
                # チーム戦の場合
                for tournament in set(list(name_to_tournament.values())):
                    temp_tournament = challonge.tournaments.show(tournament)

                    embed = discord.Embed( # Embedを定義する
                                        title=temp_tournament['name'], # タイトル
                                        color=0x0000ff, # フレーム色指定
                                        description="■点呼未反応者一覧(自動更新)", # Embedの説明文 必要に応じて
                                        # url=tournament_url # これを設定すると、タイトルが指定URLへのリンクになる
                                        )


                    no_response_player = ''
                    no_response_player_team = ''

                    for player_name in player_name_list:
                        no_response_player += player_name.replace('_', '\_') + "\n"
                        # no_response_player_team += member_to_team[player_name] + "\n"

                    # embed.add_field(name="所属チーム",value=no_response_player_team) # フィールドを追加
                    embed.add_field(name="表示名",value=no_response_player)  # フィールドを追加
                    tournament_embed[tournament] = embed
            if edit_flag == False:
                for tournament in tournament_embed.keys():
                    roll_call_end_message_obj[tournament] = await message.channel.send(embed=tournament_embed[tournament])
            else:
                for tournament in tournament_embed.keys():
                    await roll_call_end_message_obj[tournament].edit(embed=tournament_embed[tournament])
        else:
            if edit_flag == True:
                for tournament in tournament_embed.keys():
                    tournament_embed[tournament].clear_fields()
                    tournament_embed[tournament].add_field(name="",value="全員揃いました")  # フィールドを追加。
                    await roll_call_end_message_obj[tournament].edit(embed=tournament_embed[tournament])
                    del(roll_call_end_message_obj[tournament])
            else:
                embed.add_field(name="",value="全員揃っています")  # フィールドを追加。
                await message.channel.send(embed=embed)
    return roll_call_end_message_obj
