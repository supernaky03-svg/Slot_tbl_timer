import os
import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI()

active_games = {}

# 🟢 Render Environment ထဲမှ Webhook URL များကို လှမ်းယူခြင်း
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
    
    async with httpx.AsyncClient() as client:
        while active_games.get(group_id, False):
            try:
                if URL_START: await client.get(URL_START)
                
                lock_time = duration - 10 if duration > 10 else duration
                if not await custom_sleep(lock_time, group_id): break
                
                if URL_LOCK: await client.get(URL_LOCK)
                
                if not await custom_sleep(10, group_id): break
                
                if URL_END: await client.get(URL_END)
                
                if not await custom_sleep(3, group_id): break
                    
            except Exception as e:
                print(f"Error in group {group_id}: {e}")
                await asyncio.sleep(5)

@app.get("/")
def ping():
    return {"status": "alive", "message": "Bot is running perfectly!"}

@app.get("/start")
async def start_game(group_id: str, duration: int = 60):
    if active_games.get(group_id, False):
        return {"status": "already_running"}
    
    asyncio.create_task(game_loop(group_id, duration))
    return {"status": "started", "duration": duration}

@app.get("/stop")
def stop_game(group_id: str):
    active_games[group_id] = False
    return {"status": "stopped"}
    
