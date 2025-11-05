import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import *
from .db import tb

SESSION_STRING_SIZE = 351

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_id = message.from_user.id
    session = await tb.get_session(user_id)
    if session is None:
        await message.reply("**You are not logged in.**")
        return
    await tb.set_session(user_id, session=None)
    await message.reply("**Logout Successfully** ♦")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_id = message.from_user.id
    session = await tb.get_session(user_id)
    if session is not None:
        await message.reply("**You are already logged in. Please /logout first before logging in again.**")
        return

    # Start login process
    bot.pending_users[user_id] = {"step": "phone"}
    await message.reply("<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>\n\n<b>Send /cancel to cancel the process.</b>")

@Client.on_message(filters.private & filters.text)
async def handle_login_steps(bot: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in bot.pending_users:
        return
    
    user_data = bot.pending_users[user_id]
    
    if message.text == '/cancel':
        del bot.pending_users[user_id]
        return await message.reply('<b>Process cancelled!</b>')
    
    if user_data["step"] == "phone":
        phone_number = message.text
        client = Client(":memory:", API_ID, API_HASH)
        
        try:
            await client.connect()
            await message.reply("Sending OTP...")
            
            code = await client.send_code(phone_number)
            bot.pending_users[user_id] = {
                "step": "otp",
                "phone": phone_number,
                "code_hash": code.phone_code_hash,
                "client": client
            }
            
            await message.reply("Check your official Telegram account for OTP. If you got it, send it here as shown:\n\nIf OTP is `12345`, **send as** `1 2 3 4 5`.\n\n**Send /cancel to cancel.**")
            
        except PhoneNumberInvalid:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply('`PHONE_NUMBER` **is invalid.**')
        except Exception as e:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply(f"**Error sending code: {e}**")
    
    elif user_data["step"] == "otp":
        phone_code = message.text.replace(" ", "")
        client = user_data["client"]
        
        try:
            await client.sign_in(user_data["phone"], user_data["code_hash"], phone_code)
            
            # Generate session string
            string_session = await client.export_session_string()
            await client.disconnect()
            
            if len(string_session) < SESSION_STRING_SIZE:
                del bot.pending_users[user_id]
                return await message.reply('<b>Invalid session string</b>')
            
            # Store in database
            await tb.set_session(user_id, string_session)
            del bot.pending_users[user_id]
            
            await message.reply("<b>Account logged in successfully.\n\nIf you get any AUTH KEY related error, use /logout and /login again.</b>")
            
        except PhoneCodeInvalid:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply('**OTP is invalid.**')
        except PhoneCodeExpired:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply('**OTP is expired.**')
        except SessionPasswordNeeded:
            bot.pending_users[user_id]["step"] = "password"
            await message.reply('**Two-step verification is enabled. Please send your password.**\n\n**Send /cancel to cancel.**')
        except Exception as e:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply(f'**Error: {e}**')
    
    elif user_data["step"] == "password":
        client = user_data["client"]
        
        try:
            await client.check_password(password=message.text)
            
            # Generate session string
            string_session = await client.export_session_string()
            await client.disconnect()
            
            if len(string_session) < SESSION_STRING_SIZE:
                del bot.pending_users[user_id]
                return await message.reply('<b>Invalid session string</b>')
            
            # Store in database
            await tb.set_session(user_id, string_session)
            del bot.pending_users[user_id]
            
            await message.reply("<b>Account logged in successfully.\n\nIf you get any AUTH KEY related error, use /logout and /login again.</b>")
            
        except PasswordHashInvalid:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply('**Invalid password provided.**')
        except Exception as e:
            await client.disconnect()
            del bot.pending_users[user_id]
            return await message.reply(f'**Error with password: {e}**')
