import os
import time

import default_prompts
import texts
import stg
import tools
from tools import *


def main_bot(bot_id, token, prompt, welcome, status):
    if status == "0":
        return
    bot = telebot.TeleBot(token, parse_mode="Markdown")

    print("Бот @"+bot.get_me().username + " запущен")

    @bot.message_handler(commands=['start'])
    def start_msg(message):
        chat_id = message.chat.id
        if message.chat.type == 'private':
            pick("usages/" + str(chat_id), [{
                "bot_id": bot_id,
                "history": [{"role": "user", "parts": [prompt]},
                            {"role": "model", "parts": ["Хорошо, договорились!"]}]
            }])
            bot.send_message(chat_id, welcome)

    @bot.message_handler(commands=['bot_update'])
    def restart_bot(message):
        tools.sys_exit = True

    @bot.message_handler(content_types=['text'])
    def send_text(message):
        chat_id = message.chat.id
        if message.chat.type == 'private':
            history = None
            ai_response = None
            if str(chat_id) not in os.listdir("usages"):
                pick("usages/" + str(chat_id), [{
                    "bot_id": bot_id,
                    "history": [{"role": "user", "parts": [prompt]},
                                {"role": "model", "parts": ["Хорошо, договорились!"]}]
                    }])
            all_bots = unpick("usages/" + str(chat_id))
            for bot_info in all_bots:
                if bot_info["bot_id"] == bot_id:
                    history = bot_info["history"]
                    ai_response = stg.generate_response(history, message.text).replace("*", "")
                    history.append({"role": "user", "parts": [message.text]})
                    history.append({"role": "model", "parts": [ai_response]})

            all_bots = unpick("usages/" + str(chat_id))
            for bot_info in all_bots:
                if bot_info["bot_id"] == bot_id:
                    all_bots.remove(bot_info)
            all_bots.append({"bot_id": bot_id, "history": history})
            pick("usages/" + str(chat_id), all_bots)

            bot.send_message(chat_id, ai_response)

    while True:
        try:
            bot.polling()
        except:
            pass


for i in ExcelReader("data/database.xlsx").read_to_dicts():
    def run_bot():
        main_bot(
            bot_id=i["ID"],
            token=i["Token"],
            prompt=default_prompts.about_developers["ru"]+"\n\n"+open("data/"+i["Prompt"], "r", encoding="utf-8").read(),
            welcome=i["Welcome msg"],
            status=i["Status"])
    threading.Thread(target=run_bot, daemon=True).start()


while True:
    try:
        if tools.sys_exit:
            break
        time.sleep(10)
    except KeyboardInterrupt:
        break

exit(0)

