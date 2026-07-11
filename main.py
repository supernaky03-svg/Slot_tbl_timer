import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI()

# ဂိမ်းလည်ပတ်နေသည့် Group များကို မှတ်သားထားမည့် နေရာ
active_games = {}

# ⚠️ သင့် Bots.Business မှ Webhook URL များကို ဤနေရာတွင် အစားထိုးပါ
URL_START = "https://api.bots.business/v1/bots/xxxx/webhook?command=sys_startRound&bot_api_key=yyyy"
URL_LOCK = "https://api.bots.business/v1/bots/xxxx/webhook?command=sys_lockRound&bot_api_key=yyyy"
URL_END = "https://api.bots.business/v1/bots/xxxx/webhook?command=sys_endRound&bot_api_key=yyyy"

async def custom_sleep(seconds: int, group_id: str):
    """
    စောင့်နေစဉ်အတွင်း /stopGame နှိပ်လိုက်ပါက ချက်ချင်းရပ်တန့်နိုင်ရန် 
    ၁ စက္ကန့်ချင်းစီ စစ်ဆေးသည့် Sleep Function
    """
    for _ in range(seconds):
        if not active_games.get(group_id, False):
            return False  # ရပ်တန့်ရန် အချက်ပြပါက ချက်ချင်းထွက်မည်
        await asyncio.sleep(1)
    return True

async def game_loop(group_id: str, duration: int):
    """ ပွဲစဉ်များကို ဆက်တိုက်လည်ပတ်ပေးမည့် အဓိက အင်ဂျင် """
    active_games[group_id] = True
    
    async with httpx.AsyncClient() as client:
        while active_games.get(group_id, False):
            try:
                # ၁။ ပွဲစဉ်စတင်ခြင်း
                await client.get(URL_START)
                
                # ၂။ လောင်းကြေးပိတ်ချိန်အထိ စောင့်ခြင်း (Duration ထဲမှ ၁၀ စက္ကန့်နုတ်မည်)
                lock_time = duration - 10 if duration > 10 else duration
                if not await custom_sleep(lock_time, group_id):
                    break
                
                # ၃။ လောင်းကြေးပိတ်ခြင်း
                await client.get(URL_LOCK)
                
                # ၄။ ရလဒ်ထွက်ရန် ၁၀ စက္ကန့် စောင့်ခြင်း
                if not await custom_sleep(10, group_id):
                    break
                
                # ၅။ ရလဒ်ထုတ်ခြင်း (အလျော်အစားရှင်းခြင်း)
                await client.get(URL_END)
                
                # ၆။ နောက်ပွဲမစခင် ၃ စက္ကန့် နားခြင်း
                if not await custom_sleep(3, group_id):
                    break
                    
            except Exception as e:
                print(f"Error in group {group_id}: {e}")
                await asyncio.sleep(5) # Error တက်ပါက ၅ စက္ကန့်နားပြီးမှ ပြန်စမည်

# 🟢 UptimeRobot မှ လှမ်း Ping ရန် နေရာ (Bot အိပ်မသွားစေရန်)
@app.get("/")
def ping():
    return {"status": "alive", "message": "Bot is running perfectly!"}

# 🟢 ဂိမ်းစတင်ရန် API
@app.get("/start")
async def start_game(group_id: str, duration: int = 60):
    if active_games.get(group_id, False):
        return {"status": "already_running", "group_id": group_id}
    
    # Background တွင် ဂိမ်းကို စတင်မောင်းနှင်မည်
    asyncio.create_task(game_loop(group_id, duration))
    return {"status": "started", "group_id": group_id, "duration": duration}

# 🔴 ဂိမ်းရပ်တန့်ရန် API
@app.get("/stop")
def stop_game(group_id: str):
    active_games[group_id] = False
    return {"status": "stopped", "group_id": group_id}
  
