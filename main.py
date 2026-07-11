import os
import asyncio
from fastapi import FastAPI
from telethon import TelegramClient
from telethon.sessions import StringSession

app = FastAPI()
active_games = {}

# Environment variables မှ Data များကို ဆွဲယူခြင်း
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "") 

# Telethon Client တည်ဆောက်ခြင်း
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def custom_sleep(seconds: int, group_id: str):
    """ဂိမ်းရပ်တန့်လိုက်ပါက ချက်ချင်းသိနိုင်ရန် Custom Sleep"""
    for _ in range(seconds):
        if not active_games.get(group_id, False):
            return False 
        await asyncio.sleep(1)
    return True

async def game_loop(group_id: str, duration: int):
    active_games[group_id] = True
    print(f"🚀 Group {group_id} အတွက် {duration} စက္ကန့် ပွဲစဉ် စတင်ပါပြီ...")
    
    lock_time = duration - 10 if duration > 10 else duration
    
    while active_games.get(group_id, False):
        try:
            # ၁။ TBL Bot ကို ပွဲစရန် အချက်ပေးခြင်း (Duration ပါ တစ်ပါတည်း လှမ်းရိုက်ခိုင်းခြင်း)
            print(f"👉 Sending /sys_startRound {duration}")
            await client.send_message(int(group_id), f"/sys_startRound {duration}")
            
            if not await custom_sleep(lock_time, group_id): break
            
            # ၂။ TBL Bot ကို လောင်းကြေးပိတ်ရန် အချက်ပေးခြင်း
            print("👉 Sending /sys_lockRound")
            await client.send_message(int(group_id), "/sys_lockRound")
            
            if not await custom_sleep(10, group_id): break
            
            # ၃။ TBL Bot ကို ရလဒ်ထုတ်ရန် အချက်ပေးခြင်း
            print("👉 Sending /sys_endRound")
            await client.send_message(int(group_id), "/sys_endRound")
            
            # နောက်တစ်ပွဲ မစမီ ၃ စက္ကန့် အနားပေးခြင်း
            if not await custom_sleep(3, group_id): break
                
        except Exception as e:
            print(f"❌ Telegram sending error in group {group_id}: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Server စတက်သည်နှင့် Telegram သို့ ချိတ်ဆက်မည်"""
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Error: SESSION_STRING မှားယွင်းနေသည် သို့မဟုတ် သက်တမ်းကုန်နေပါသည်။")
    else:
        print("✅ Telegram Userbot သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")

@app.on_event("shutdown")
async def shutdown_event():
    await client.disconnect()

@app.get("/")
def ping():
    return {"status": "alive"}

@app.get("/start")
async def start_game(group_id: str, duration: int = 60):
    if active_games.get(group_id, False):
        return {"status": "already_running"}
    
    asyncio.create_task(game_loop(group_id, duration))
    return {"status": "started"}

@app.get("/stop")
def stop_game(group_id: str):
    active_games[group_id] = False
    print(f"🛑 Group {group_id} ၏ ပွဲစဉ်ကို ရပ်တန့်လိုက်ပါပြီ။")
    return {"status": "stopped"}

