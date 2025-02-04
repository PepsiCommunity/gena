import requests

main_url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
api_key = "TOKEN"

class Dialog:
    def __init__(self):
        self.messages = {}

    def prompt(self, id, promt):

        if id in self.messages:
            self.messages[id].append({
                        "role": "user",
                        "text": promt
                        })
        else:
            self.messages[id] = [{
                        "role": "user",
                        "text": promt
                        }]
        
        body = {
            "modelUri": f"gpt://b1gktqso6nmdrbdj5td4/yandexgpt/latest",
            "generationOptions": {
                "stream": False,
                "temperature": "0.6",
                "maxTokens": "7400"
            },
            "messages": self.messages.get(id, []),
        }

        headers = {'Authorization': f'Api-Key {api_key}'}
        response = requests.post(main_url, 
                                 headers=headers, 
                                 json=body)
        res = response.json()
        if response.status_code == 200:
            response = res['result']['alternatives'][0]['message']["text"]
        else:
            response = "Извините, я не могу дать ответ на этот вопрос"

        self.messages[id].append({
                        "role": "assistant",
                        "text": response
                        })
        
        return response
