import os
from datetime import datetime
from pytz import timezone
from pyrogram import Client
from aiohttp import web
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN, LOG_CHANNEL

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route(request):
    return web.Response(text="<h3 align='center'><b>I am Alive</b></h3>", content_type='text/html')

async def web_server():
    app = web.Application(client_max_size=30_000_000)
    app.add_routes(routes)
    return app

class Bot(Client):
    def __init__(self):
        super().__init__(
            "AcceptronBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=200,
            sleep_threshold=15
        )
        self.pending_users = {}

    async def start(self):
        # Start web server
        app = web.AppRunner(await web_server())
        await app.setup()
        try:
            await web.TCPSite(app, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
            print("Web server started.")
        except Exception as e:
            print(f"Web server error: {e}")

        # Start bot
        await super().start()
        me = await self.get_me()
        print(f"Bot Started as {me.first_name}")
        
        # Send startup message to admin
        if isinstance(ADMIN, int) and ADMIN:
            try:
                await self.send_message(ADMIN, f"**{me.first_name} is started...**")
            except Exception as e:
                print(f"⚠️ Could not send startup message to admin: {e}")
        
        # Send startup message to log channel (if configured and valid)
        if LOG_CHANNEL:
            try:
                now = datetime.now(timezone("Asia/Kolkata"))
                msg = (
                    f"**{me.mention} is restarted!**\n\n"
                    f"📅 Date : `{now.strftime('%d %B, %Y')}`\n"
                    f"⏰ Time : `{now.strftime('%I:%M:%S %p')}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`"
                )
                await self.send_message(LOG_CHANNEL, msg)
                print("Startup message sent to log channel")
            except Exception as e:
                print(f"⚠️ Error sending to LOG_CHANNEL: {e}")
                print("Please check if the LOG_CHANNEL ID is correct and the bot has access to it")

    async def stop(self, *args):
        await super().stop()
        me = await self.get_me()
        print(f"{me.first_name} Bot stopped.")

if __name__ == "__main__":
    Bot().run()
