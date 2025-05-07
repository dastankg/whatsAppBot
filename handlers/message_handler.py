import httpx

from lexicons.lexicon_mapping import LEXICON_MAPPING
from services.redis_service import RedisService
from services.whapi_service import WhatsAppService

from datetime import datetime, timedelta


class MessageHandler:
    def __init__(self):
        self.redis_service = RedisService()
        self.whapi_service = WhatsAppService()

    async def process_message(self, message: dict):
        number = message.get('from')
        text = message.get('text', {}).get('body', '').strip()
        if not number or not text:
            return

        state = await self.redis_service.get_user_state(number)
        if not state:
            await self.start_conversation(number)
            return
        if state.get('stage') == 'awaiting_queue_info':
            if text.isdigit():
                office_id = int(text)
                # Используем номер телефона клиента из WhatsApp
                client_number = number

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(
                            "http://127.0.0.1:8080/queue/join",
                            json={
                                "office_id": office_id,
                                "client_number": client_number
                            }
                        )
                        if response.status_code == 201:
                            await self.whapi_service.send_request('messages/text', params={
                                "to": number,
                                "body": "✅ Вы успешно встали в очередь!"
                            })
                        else:
                            await self.whapi_service.send_request('messages/text', params={
                                "to": number,
                                "body": f"❌ Ошибка: {response.text}"
                            })
                    except Exception as e:
                        await self.whapi_service.send_request('messages/text', params={
                            "to": number,
                            "body": f"❌ Ошибка связи с сервером очереди: {str(e)}"
                        })

                # После вставки в очередь — вернуть пользователя обратно в меню
                await self.redis_service.set_user_state(number, {"stage": "menu"})
                return
            else:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": "⚠️ Неверный формат. Пожалуйста, отправьте только номер офиса.\nПример:\n3"
                })
                return
        if state.get('stage') == 'awaiting_office_queue':
            if text.isdigit():
                office_id = int(text)

                async with httpx.AsyncClient() as client:
                    try:
                        # Обновленный запрос для получения информации об очереди
                        response = await client.get(
                            f"http://127.0.0.1:8080/queue/position?office_id={office_id}&phone={number}")
                        if response.status_code == 200:
                            data = response.json()
                            total_people = data.get('общее колво', 0)

                            # Формируем сообщение в зависимости от наличия клиента в очереди
                            if 'сообщение' in data:
                                message = f"👥 {data['сообщение']}. В очереди сейчас {total_people} человек(а)."
                            else:
                                position = data.get('лично ваша очередь', 0)
                                message = f"👥 Ваша позиция в очереди: {position}. Всего в очереди {total_people} человек(а)."

                            await self.whapi_service.send_request('messages/text', params={
                                "to": number,
                                "body": message
                            })
                        else:
                            await self.whapi_service.send_request('messages/text', params={
                                "to": number,
                                "body": f"❌ Ошибка при получении очереди: {response.text}"
                            })
                    except Exception as e:
                        await self.whapi_service.send_request('messages/text', params={
                            "to": number,
                            "body": f"❌ Ошибка связи с сервером очереди: {str(e)}"
                        })

                # После ответа вернуть пользователя в главное меню
                await self.redis_service.set_user_state(number, {"stage": "menu"})
                return
            else:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": "⚠️ Пожалуйста, отправьте только номер офиса.\nПример:\n3"
                })
                return

        lang = state.get('lang', 'ru')
        stage = state.get('stage')

        # --- Проверка на блокировку пользователя ---
        if stage == 'blocked':
            blocked_until = state.get('blocked_until')
            if blocked_until:
                now = datetime.utcnow()
                unblock_time = datetime.fromisoformat(blocked_until)
                if now < unblock_time:
                    return  # Блокировка еще действует — игнорировать сообщение
                else:
                    await self.redis_service.set_user_state(number, {'lang': lang, 'stage': 'menu'})
                    await self.send_menu(number, lang)
                    return

        # --- Обработка выбора языка ---
        if stage == 'choose_language':
            if text == '1':
                lang = 'kg'
            elif text == '2':
                lang = 'ru'
            else:
                await self.start_conversation(number)
                return

            await self.redis_service.set_user_state(number, {'lang': lang, 'stage': 'menu'})
            await self.send_menu(number, lang)
            return

        if text == '0':
            await self.send_menu(number, lang)
            return

        await self.handle_menu_selection(number, text, lang)

    async def start_conversation(self, number: str):
        await self.redis_service.set_user_state(number, {'stage': 'choose_language'})
        await self.whapi_service.send_request('messages/text', params={
            "to": number,
            "body": LEXICON_MAPPING['ru']['start']
        })

    async def send_menu(self, number: str, lang: str):
        lexicon = LEXICON_MAPPING.get(lang, LEXICON_MAPPING['ru'])
        await self.redis_service.update_user_state(number, 'stage', 'menu')
        await self.whapi_service.send_request('messages/text', params={
            "to": number,
            "body": lexicon['menu']
        })

    async def handle_menu_selection(self, number: str, text: str, lang: str):
        lexicon = LEXICON_MAPPING.get(lang, LEXICON_MAPPING['ru'])

        entry = lexicon.get(text)
        print(entry)
        if not entry:
            await self.send_menu(number, lang)
            return

        message_text, link = entry

        # --- Пункт "7" — оператор ---
        if text == '7':
            # Отправляем сообщение из лексикона, как обычно
            if link:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": f"{message_text}\n\nПодробнее: {link}"
                })
            else:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": message_text
                })

            # Ставим блокировку на 2 часа
            two_hours_later = datetime.utcnow() + timedelta(hours=2)
            await self.redis_service.set_user_state(number, {
                'lang': lang,
                'stage': 'blocked',
                'blocked_until': two_hours_later.isoformat()
            })
            return
        if text == '8':
            await self.start_join_queue_process(number)
            return
        if text == '9':
            await self.start_check_queue_process(number)
            return

        if link:
            await self.whapi_service.send_request('messages/text', params={
                "to": number,
                "body": f"{message_text}\n\nПодробнее: {link}"
            })
        else:
            await self.whapi_service.send_request('messages/text', params={
                "to": number,
                "body": message_text
            })

    async def start_join_queue_process(self, number: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://127.0.0.1:8080/offices")
                if response.status_code == 200:
                    data = response.json()
                    offices = data.get('offices', [])

                    if not offices:
                        await self.whapi_service.send_request('messages/text', params={
                            "to": number,
                            "body": "❌ Офисы не найдены. Попробуйте позже."
                        })
                        return

                    office_list_text = "🏢 Доступные офисы:\n\n"
                    for office in offices:
                        office_list_text += f"{office['ID']}: {office['Name']} ({office['Address']})\n"

                    office_list_text += "\n✍️ Отправьте номер офиса, чтобы встать в очередь.\nПример:\n3"

                    await self.whapi_service.send_request('messages/text', params={
                        "to": number,
                        "body": office_list_text
                    })

                    # Установить стадию ожидания номера офиса
                    await self.redis_service.set_user_state(number, {
                        "stage": "awaiting_queue_info"
                    })
                else:
                    await self.whapi_service.send_request('messages/text', params={
                        "to": number,
                        "body": "❌ Ошибка при получении списка офисов."
                    })
            except Exception as e:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": f"❌ Не удалось получить список офисов: {str(e)}"
                })

    async def start_check_queue_process(self, number: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://127.0.0.1:8080/offices")
                if response.status_code == 200:
                    data = response.json()
                    offices = data.get('offices', [])

                    if not offices:
                        await self.whapi_service.send_request('messages/text', params={
                            "to": number,
                            "body": "❌ Офисы не найдены. Попробуйте позже."
                        })
                        return

                    office_list_text = "🏢 Доступные офисы для проверки очереди:\n\n"
                    for office in offices:
                        office_list_text += f"{office['ID']}: {office['Name']} ({office['Address']})\n"

                    office_list_text += "\n✍️ Отправьте номер офиса, чтобы узнать очередь.\nПример:\n3"

                    await self.whapi_service.send_request('messages/text', params={
                        "to": number,
                        "body": office_list_text
                    })

                    # Установить стадию ожидания выбора офиса для просмотра очереди
                    await self.redis_service.set_user_state(number, {
                        "stage": "awaiting_office_queue"
                    })
                else:
                    await self.whapi_service.send_request('messages/text', params={
                        "to": number,
                        "body": "❌ Ошибка при получении списка офисов."
                    })
            except Exception as e:
                await self.whapi_service.send_request('messages/text', params={
                    "to": number,
                    "body": f"❌ Не удалось получить список офисов: {str(e)}"
                })