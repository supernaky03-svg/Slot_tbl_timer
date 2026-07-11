import os
import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI()

# ဂိမ်းလည်ပတ်နေသည့် Group များကို မှတ်သားရန်
active_games = {}

# Browser အယောင်ဆောင်ရန် Header (403 Error မတက်စေရန်)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

# Environment မှ Webhook URLs များကို ဆွဲယူခြင်း
URL_START = os.getenv("URL_START")
URL_LOCK = os.getenv("URL_LOCK")
URL_END = os.getenv("URL_END")

async def custom_sleep(seconds: int, group_id: str):
    """ဂိမ်းရပ်လိုက်ပါက ချက်ချင်းရပ်တန့်နိုင်ရန် စောင့်ဆိုင်းခြင်း"""
    for _ in range(seconds):
        if not active_games.get(group_id, False):
            return False 
        await asyncio.sleep(1)
    return True

async def game_loop(group_id: str, duration: int):
    active_games[group_id] = True
    print(f"🚀 Group {group_id} အတွက် {duration} စက္ကန့် ပွဲစဉ် စတင်ပါပြီ...")
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        while active_games.get(group_id, False):
            try:
                # ၁။ ပွဲစဉ်စတင်ခြင်း
                if URL_START: 
                    print("👉 Calling URL_START...")
                    res = await client.get(URL_START)
                    print(f"✅ TBL Start Response: {res.status_code}")
                
                # လောင်းကြေးပိတ်ချိန်အထိ စောင့်ခြင်း
                lock_time = duration - 10 if duration > 10 else duration
                if not await custom_sleep(lock_time, group_id): break
                
                # ၂။ လောင်းကြေးပိတ်ခြင်း
                if URL_LOCK: 
                    print("👉 Calling URL_LOCK...")
                    await client.get(URL_LOCK)
                
                if not await custom_sleep(10, group_id): break
                
                # ၃။ ရလဒ်ထုတ်ခြင်း
                if URL_END: 
                    print("👉 Calling URL_END...")
                    await client.get(URL_END)
                
                # နောက်ပွဲမစခင် ၃ စက္ကန့် နားခြင်း
                if not await custom_sleep(3, group_id): break
                    
            except Exception as e:
                print(f"❌ Error in group {group_id}: {e}")
                await asyncio.sleep(5) # Error တက်လျှင် ၅ စက္ကန့်နားပါ

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

