import time
import json
from redis.asyncio import Redis
from config.config import Config


class RedisService:
    def __init__(self):
        self.cache = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )

    async def set_user_state(self, number, state_data):
        state_data['timestamp'] = str(time.time())
        encoded_data = {k: json.dumps(v) for k, v in state_data.items()}
        await self.cache.hset(number, mapping=encoded_data)

    async def get_user_state(self, number):
        user_data = await self.cache.hgetall(number)
        if not user_data:
            return None

        return {
            key: json.loads(value)
            for key, value in user_data.items()
        }

    async def update_user_state(self, number, key, value):
        await self.cache.hset(number, key, json.dumps(value))

    async def delete_user_state(self, number):
        await self.cache.delete(number)
