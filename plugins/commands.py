from pyrogram import Client, filters, enums
from pyrogram.errors import *
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
import asyncio
from Script import text
from .db import tb
from .fsub import get_fsub

@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    if await tb.get_user(message.from_user.id) is None:
        await tb.add_user(message.from_user.id, message.from_user.first_name)
        if LOG_CHANNEL:
            try:
                await client.send_message(
                    LOG_CHANNEL,
                    text.LOG.format(message.from_user.mention, message.from_user.id)
                )
            except Exception as e:
                print(f"Error sending to log channel: {e}")
    
    if IS_FSUB and not await get_fsub(client, message): 
        return
        
    await message.reply_text(
        text.START.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f"https://telegram.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about'),
             InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help')],
            [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⇆', url=f"https://telegram.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
        ])
    )

@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMIN))
async def total_users(client, message):
    try:
        users = await tb.get_all_users()
        await message.reply(
            f"👥 **Total Users:** {len(users)}", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 Close", callback_data="close")]])
        )
    except Exception as e:
        r = await message.reply(f"❌ *Error:* `{str(e)}`")
        await asyncio.sleep(30)
        await r.delete()

@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message):
    show = await message.reply("**Please Wait.....**")
    user_data = await tb.get_session(message.from_user.id)
    if user_data is None:
        return await show.edit("**To accept join requests, please /login first.**")

    try:
        acc = Client("joinrequest", session_string=user_data, api_id=API_ID, api_hash=API_HASH)
        await acc.connect()
    except Exception as e:
        return await show.edit("**Your login session has expired. Use /logout first, then /login again.**")

    await show.edit("**Forward a message from your Channel or Group (with forward tag).\n\nMake sure your logged-in account is an admin there with full rights.**")
    
    # Wait for forwarded message
    client.pending_users[message.from_user.id] = {"step": "waiting_forward", "acc": acc, "msg": show}

@Client.on_message(filters.private)
async def handle_forwarded_message(client, message):
    user_id = message.from_user.id
    
    if user_id not in client.pending_users:
        return
    
    user_data = client.pending_users[user_id]
    
    if user_data.get("step") != "waiting_forward":
        return
    
    # Check if message is forwarded using the new API
    if not message.forward_origin:
        return
    
    acc = user_data["acc"]
    show = user_data["msg"]
    
    try:
        if message.forward_from_chat and message.forward_from_chat.type not in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
            chat_id = message.forward_from_chat.id
            try:
                info = await acc.get_chat(chat_id)
            except Exception as e:
                await acc.disconnect()
                del client.pending_users[user_id]
                return await show.edit("**Error: Ensure your account is admin in this Channel/Group with required rights.**")
        else:
            await acc.disconnect()
            del client.pending_users[user_id]
            return await message.reply("**Message not forwarded from a valid Channel/Group.**")

        await message.delete()
        await show.edit("**Accepting all join requests... Please wait.**")
        
        try:
            count = 0
            while True:
                join_requests = []
                async for req in acc.get_chat_join_requests(chat_id):
                    join_requests.append(req)
                
                if not join_requests:
                    break
                    
                for request in join_requests:
                    try:
                        await acc.approve_chat_join_request(chat_id, request.user.id)
                        count += 1
                    except Exception as e:
                        print(f"Error approving request: {e}")
                        
                await asyncio.sleep(1)
                
            await show.edit(f"**✅ Successfully accepted {count} join requests.**")
            
        except Exception as e:
            await show.edit(f"**An error occurred:** `{str(e)}`")
        finally:
            await acc.disconnect()
            del client.pending_users[user_id]
            
    except Exception as e:
        await show.edit(f"**Error:** `{str(e)}`")
        await acc.disconnect()
        del client.pending_users[user_id]

@Client.on_chat_join_request()
async def approve_new(client, m):
    if not NEW_REQ_MODE:
        return
    try:
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            await client.send_message(
                m.from_user.id,
                f"{m.from_user.mention},\n\n𝖸𝗈𝗎𝗋 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖳𝗈 𝖩𝗈𝗂𝗇 {m.chat.title} 𝖧𝖺𝗌 𝖡𝖾𝖾𝗇 𝖠𝖼𝖼𝖾𝗉𝗍𝖾𝖽."
            )
        except:
            pass
    except Exception as e:
        # Only log unexpected errors, ignore common ones
        error_msg = str(e)
        if "USER_ALREADY_PARTICIPANT" not in error_msg and "HIDE_REQUESTER_MISSING" not in error_msg:
            print(f"Error in auto-approve: {error_msg}")
