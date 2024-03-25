import requests

url = "http://172.16.26.4:6667/translate/"
query = {"content": "Recently, a new type of Chinese home-made air defense missile system performed outstandingly in actual combat training."}
response = requests.post(url, json=query)
result = response.json()
print(result)