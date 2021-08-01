import json
import datetime
import time
from TwitterAPI import TwitterAPI

keys = open('keys').read().split('\n')
client = TwitterAPI(keys[0], keys[1], keys[2], keys[3])

schedule = json.loads(open('schedule').read())

nearests = []

for group in schedule:
    nearest = (datetime.timedelta.max.days, datetime.date.min, '')
    for item in group:
        tmp = datetime.datetime.strptime(item['date'], '%Y/%m/%d')
        date = datetime.date(tmp.year, tmp.month, tmp.day)
        rem = (date - datetime.date.today()).days
        if 0 <= rem and rem < nearest[0]:
            nearest = (rem, date, item['description'])
    if nearest[0] != datetime.timedelta.max:
        nearests.append(nearest)

nearests.sort()

def is_valid_tweet(s):
    count = 0
    for c in s:
        code = ord(c)
        if 0x0000 <= code <= 0x10FF or 0x2000 <= code <= 0x200D or 0x2010 <= code <= 0x201F or 0x2032 <= code <= 0x2037:
            count += 1
        else:
            count += 2
    return count <= 280

text = ''
for (rem, date, description) in nearests:
    date = date.strftime('%m/%d')
    if rem == 0:
        tmp = text + '今日（' + date + '）は【' + description + '】当日！\n'
    else:
        tmp = text + '' + description + '（' + date + '）まであと' + str(rem) + '日\n'
    if is_valid_tweet(tmp):
        text = tmp
    else:
        break

r = client.request('statuses/update', {'status': text})
print(r.text)

for i in range(8000):
    last_id = open('last_id').read().strip()

    response = client.request('statuses/mentions_timeline', {'since_id': last_id}).text
    print(response)
    replies = json.loads(response)

    last_id = int(last_id)

    for reply in replies:
        received_text = reply['text']
        received_id = reply['id']
        last_id = max(last_id, int(received_id))
        received_from = reply['user']['id']
        exclamation = received_text.find('!')
        if exclamation == -1:
            pass
        else:
            response = client.request('friendships/lookup', {'user_id': received_from}).text
            print(response)
            is_following = 'following' in json.loads(response)[0]['connections']
            command = received_text[exclamation + 1:].split(maxsplit = 1)[0]
            print(command)
            if command == 'list':
                schedule = json.loads(open('schedule').read())
                item_list = []
                for group in schedule:
                    for item in group:
                        tmp = datetime.datetime.strptime(item['date'], '%Y/%m/%d')
                        date = datetime.date(tmp.year, tmp.month, tmp.day)
                        description = item['description']
                        item_list.append((date, description))
                item_list.sort()
                i = 0
                reply_to = received_id
                while i < len(item_list):
                    text = ''
                    for (date, description) in item_list[i:]:
                        tmp = text + date.strftime('%m/%d') + ' ' + description + '\n'
                        if is_valid_tweet(tmp):
                            text = tmp
                            i += 1
                        else:
                            break
                    response = client.request('statuses/update', {'status': text, 'in_reply_to_status_id': reply_to, 'auto_populate_reply_metadata': 'true'}).text
                    print(response)
                    reply_to = json.loads(response)['id']
    open('last_id', mode='w').write(str(last_id))
    time.sleep(10)
