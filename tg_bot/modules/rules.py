from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "pesan tidak ditemukan!" and from_pm:
            bot.send_message(user.id, "pintasan aturan untuk obrolan ini belum disetel dengan benar, minta admin untuk  "
                                      "memperbaiki ini.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "peraturan untuk *{}* adalah:\n\n{}".format(escape_markdown(chat.title), rules)

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(user.id, "admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
                                  "ini mungkin tidak berarti itu melanggar hukum!")
    elif rules:
        update.effective_message.reply_text("hubungi saya di pm untuk melihat peraturan grup ini, tekan tombol dibawah!",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="📝PERATURAN GRUP",
                                                                       url="t.me/{}?start={}".format(bot.username,
                                                                                                     chat_id))]]))
    else:
        update.effective_message.reply_text("admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
                                            "ini mungkin tidak berarti itu melanggar hukum!")


@run_async
@user_admin
def set_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("berhasil mengatur peraturan di grup ini.")


@run_async
@user_admin
def clear_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("berhasil menghapus peraturan!")


def __stats__():
    return "{} chats have rules set.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "obrolan ini telah menetapkan aturannya: `{}`".format(bool(sql.get_rules(chat_id)))


__help__ = """
 - /rules: dapatkan peraturan dalam suatu grup.

*Admin only:*
 - /setrules <peraturan anda>: pasang peraturan dalam suatu grup.
 - /clearrules: menghapus peraturan di dalam grup.
"""

__mod_name__ = "📝 Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
