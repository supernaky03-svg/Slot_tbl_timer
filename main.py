import os
import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI()
active_games = {}

# Environment မှ URLs များကို ဆွဲယူခြင်း
URL_START = os.getenv("URL_START")
URL_LOCK = os.getenv("URL_LOCK")
URL_END = os.getenv("URL_END")

async def custom_sleep(seconds: int, group_id: str):
    for _ in range(seconds):
        if not active_games.get(group_id, False):
            return False 
        await asyncio.sleep(1)
    return True

async def game_loop(group_id: str, duration: int):
    active_games[group_id] = True
    print(f"🚀 Group {group_id} အတွက် {duration} စက္ကန့် ပွဲစဉ် စတင်ပါပြီ...")
    print(f"🔗 URL_START ပါဝင်မှု: {URL_START}") # URL ဝင်/မဝင် Logs တွင် စစ်ဆေးရန်
    
    async with httpx.AsyncClient() as client:
        while active_games.get(group_id, False):
            try:
                # ၁။ ဂိမ်းစတင်ရန် TBL သို့ လှမ်းခေါ်ခြင်း
                if URL_START: 
                    print("👉 Calling URL_START...")
                    res = await client.get(URL_START)
                    print(f"✅ TBL မှ တုံ့ပြန်မှု (Start): {res.status_code}")
                else:
                    print("❌ ERROR: URL_START မရှိပါ! Render Environment ကို စစ်ဆေးပါ။")
                
                lock_time = duration - 10 if duration > 10 else duration
                if not await custom_sleep(lock_time, group_id): break
                
                # ၂။ လောင်းကြေးပိတ်ရန် TBL သို့ လှမ်းခေါ်ခြင်း
                if URL_LOCK: 
                    print("👉 Calling URL_LOCK...")
                    await client.get(URL_LOCK)
                
                if not await custom_sleep(10, group_id): break
                
                # ၃။ ရလဒ်ထုတ်ရန် TBL သို့ လှမ်းခေါ်ခြင်း
                if URL_END: 
                    print("👉 Calling URL_END...")
                    await client.get(URL_END)
                
                if not await custom_sleep(3, group_id): break
                    
            except Exception as e:
                print(f"❌ Error in group {group_id}: {e}")
                await asyncio.sleep(5)

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
    print("🛑 ပွဲစဉ်ကို ရပ်တန့်လိုက်ပါပြီ။")
    return {"status": "stopped"}

