import random

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.exceptions import BadRequest
from aiogram.types import ContentType, Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.dispatcher.filters import BoundFilter

import asyncio
from random import choice

import core


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: Message):
        return True


TOKEN = ''
bot = Bot(TOKEN, parse_mode='Markdown')
dp = Dispatcher(bot)

dp.filters_factory.bind(AdminFilter)
group = -1001609870701


@dp.message_handler(content_types=ContentType.NEW_CHAT_MEMBERS)
async def new_members(msg):
    members = msg.new_chat_members
    cfg = core.get_cfg()
    grp = await bot.get_chat(msg.chat.id)
    if cfg['on']:
        for member in members:
            tg_id = member.id
            name = member.first_name
            # await msg.delete()
            
            restricted_permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            await bot.restrict_chat_member(msg.chat.id, tg_id, permissions=restricted_permissions)
            
            rk = InlineKeyboardMarkup()
            fruits = random.sample(cfg['emoji_list'], 5)
            right = '👨‍🦳'
            buttons = []
            for fruit in fruits:
                if fruit == right:
                    rightbutton = InlineKeyboardButton(text=f'{fruit}', callback_data=f'captcha_right+{tg_id}')
                    buttons.append(rightbutton)
                else:
                    buttons.append(InlineKeyboardButton(text=f'{fruit}', callback_data='pass'))
            rk.row(*buttons)
            welcome = cfg['message'] \
                .replace("USER", f'[{name}](tg://user?id={tg_id})') \
                .replace("GROUP", str(grp.title)) \
                .replace("RIGHT", str(right))
            if cfg['welcome_image']:
                welcomemsg = await bot.send_photo(msg.chat.id,
                                                  photo=cfg['welcome_image'],
                                                  caption=welcome,
                                                  reply_markup=rk,
                                                  parse_mode='Markdown')
            else:
                welcomemsg = await bot.send_message(msg.chat.id, welcome, reply_markup=rk, parse_mode='Markdown')

            await remove(welcomemsg, str(msg.from_user.id), int(cfg['time']))
    else:
        for member in members:
            tg_id = member.id
            name = member.first_name
            await msg.delete()
            welcome = cfg['message'] \
                .replace("USER", f'[{name}](tg://user?id={tg_id})') \
                .replace("GROUP", str(grp.title)) \
                .replace("RIGHT", '')
            if cfg['welcome_image']:
                welcomemsg = await bot.send_photo(msg.chat.id,
                                                  photo=cfg['welcome_image'],
                                                  caption=welcome,
                                                  parse_mode='Markdown')
            else:
                welcomemsg = await bot.send_message(msg.chat.id, welcome, parse_mode='Markdown')
            await asyncio.sleep(int(cfg['time']))
            await welcomemsg.delete()


@dp.message_handler(content_types=ContentType.LEFT_CHAT_MEMBER)
async def byebye(msg):
    await msg.delete()

@dp.message_handler(commands=['enable'], is_admin=True)
async def enable_captcha(msg):
    cfg = core.get_cfg()
    cfg['on'] = True
    core.update_cfg(cfg)

    resp = 'Captcha is now Enabled ✅'
    await msg.answer(resp)

@dp.message_handler(commands=['disable'], is_admin=True)
async def disable_captcha(msg):
    cfg = core.get_cfg()
    cfg['on'] = False
    core.update_cfg(cfg)

    resp = 'Captcha is now Disabled ❌'
    await msg.answer(resp)

@dp.message_handler(commands=['message'], is_admin=True)
async def change_message(msg):
    cfg = core.get_cfg()
    cfg['message'] = msg.get_args()
    core.update_cfg(cfg)

    resp = f'Welcome message is now:\n\n{cfg["message"]}'
    await msg.answer(resp)

@dp.message_handler(commands=['time'], is_admin=True)
async def change_time(msg):
    cfg = core.get_cfg()
    try:
        cfg['time'] = int(msg.get_args())
        core.update_cfg(cfg)
        resp = f'Updated time to complete captcha to *{cfg["time"]} seconds*'
    except ValueError:
        resp = 'Time to complete captcha has to be an integer ❌'

    await msg.answer(resp)

@dp.message_handler(commands=['emoji'], is_admin=True)
async def change_emoji_list(msg):
    cfg = core.get_cfg()
    new = msg.get_args().split()
    if len(new) >= 5:
        cfg["emoji_list"] = new
        core.update_cfg(cfg)

        resp = f'New emoji list:\n{cfg["emoji_list"]}'
    else:
        resp = 'I need *at least 5* emojis to work properly :('
    await msg.answer(resp)


async def remove(message, member_id, time):
    print(1)
    await asyncio.sleep(time)
    try:
        await message.delete()
        await bot.kick_chat_member(message.chat.id, member_id)
        await bot.unban_chat_member(message.chat.id, member_id)
    except Exception:
        pass


@dp.callback_query_handler(lambda call: True)
async def callback_inline(call):
    if call.message:
        tg_id = str(call.from_user.id)
        if 'captcha_right' in call.data:
            mtg_id = call.data[call.data.index('+')+1:]
            if str(mtg_id) == tg_id:
                good_boy = ChatPermissions(can_send_messages=True,
                                           can_invite_users=True,
                                           can_send_media_messages=True,
                                           can_send_other_messages=True)
                await bot.restrict_chat_member(call.message.chat.id,
                                               call.from_user.id,
                                               permissions=good_boy)
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.answer_callback_query(call.id, '✅ You\'re now verified!', show_alert=True)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
