import httpx
import logging
from requests_toolbelt.multipart.encoder import MultipartEncoder
from config.config import Config


class WhatsAppService:
    @staticmethod
    async def send_request(endpoint, params=None, method='POST'):
        try:
            headers = {
                'Authorization': f"Bearer {Config.WHAPI_TOKEN}"
            }
            url = f"{Config.WHAPI_API_URL}/{endpoint}"
            async with httpx.AsyncClient() as client:
                if not params:
                    response = await client.request(method, url, headers=headers)
                    return response.json()

                if 'media' in params:
                    return await WhatsAppService._send_media_request(client, url, params, headers)

                return await WhatsAppService._send_json_request(client, url, params, headers, method)

        except httpx.RequestError as e:
            logging.error(f"WhatsApp API Request Error: {e}")
            return None

    @staticmethod
    async def _send_media_request(client, url, params, headers):
        try:
            details = params.pop('media').split(';')
            with open(details[0], 'rb') as file:
                multipart_data = MultipartEncoder(
                    fields={**params, 'media': (details[0], file, details[1])}
                )
                headers['Content-Type'] = multipart_data.content_type
                response = await client.post(url, data=multipart_data, headers=headers)
                return response.json()
        except Exception as e:
            logging.error(f"Media Request Error: {e}")
            return None

    @staticmethod
    async def _send_json_request(client, url, params, headers, method):
        try:
            headers['Content-Type'] = 'application/json'
            print(headers)
            response = await client.request(method, url, json=params, headers=headers)
            return response.json()
        except Exception as e:
            logging.error(f"JSON Request Error: {e}")
            return None
