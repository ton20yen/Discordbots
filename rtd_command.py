import discord
import yaml

async def call(message, player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num, team_roll_call_count):
    if (not(any(player_table))):
        embed = discord.Embed( # Embedを定義する
                            title="■トーナメント未指定エラー",
                            color=0xffc800, # フレーム色指定
                            description="先に!sコマンドでトーナメントを指定してください", # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )
        await message.channel.send(embed=embed)
        return

    team_battle_data = None

    # ローカルのyaml読み込み
    with open('TeamBattleData.yaml', 'r', encoding='utf-8') as f:
        team_battle_data = yaml.safe_load(f)

        print(team_battle_data)
        print("win: " + str(team_battle_data['win']))
        print("report_num: " + str(team_battle_data["report_num"]))
        print("member_num: " + str(team_battle_data["member_num"]))

        system_message = "チーム戦用データを読み込みました。"
        system_message += "\n" + "読み込んだ内容は下記の通りです。"
        system_message += "\n" + "チームメンバ数: " + str(team_battle_data["member_num"])
        system_message += "\n" + "勝利確定数: " + str(team_battle_data['win'])
        system_message += "\n" + "早稲田式: " + str(team_battle_data['waseda_flag'])
        system_message += "\n" + "トーナメント更新報告数: " + str(team_battle_data["report_num"])
        system_message += "\n" + "■参加チーム情報"

        player_name_list.clear()
        player_nick_list.clear()
        team_roll_call_count = {}
        for team in team_battle_data["teams"]:
            system_message += "\n" +  "・" + str(team["name"])
            loop_count = 0
            team_roll_call_count[str(team["name"])] = team["roll_call_count"]
            for member in team["member"]:
                player_name_list.append(str(team["member"][loop_count]))
                player_nick_list.append(str(team["member_id"][loop_count]))
                member_to_team[team["member"][loop_count]] = str(team["name"])
                member_id_to_team[team["member_id"][loop_count]] = str(team["name"])
                system_message += "\n" +  str(team["member"][loop_count])
                loop_count = loop_count + 1

        print("--- 点呼用データ作成確認 ---")
        print(team_roll_call_count)

        match_report_num.clear()
        embed = discord.Embed( # Embedを定義する
                            title="■チーム戦データ読み込み完了",
                            color=0x0000ff, # フレーム色指定
                            description=system_message, # Embedの説明文 必要に応じて
                            url="" # これを設定すると、タイトルが指定URLへのリンクになる
                            )

        await message.channel.send(embed=embed)

    return player_table, player_name_list, player_nick_list, member_to_team, member_id_to_team, match_report_num, team_battle_data, team_roll_call_count

