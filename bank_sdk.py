import requests

host = 'http://127.0.0.1:4567'
trading_token = '07e61d42-b66d-4af1-aa7f-8790c3997de4'

def send_money(to_id, amount, description):
    answer = requests.post(host + '/api/send', json={
        'token': trading_token,
        'account_id': to_id,
        'amount': amount,
        'description': description
    })

    return answer.json()

def ask_money(from_id, amount, description):
    answer = requests.post(host + '/api/ask', json={
        'token': trading_token,
        'account_id': from_id,
        'amount': amount,
        'description': description
    })

    return answer.json()

def verify_transaction(transaction_id, code):
    answer = requests.post(host + '/api/verify', json={
        "transaction_id": transaction_id,
        "code": code
    })

    return answer.json()

if __name__ == '__main__':
    # print(ask_money(86773763, 50, 'тестовая покупка'))
    # print(verify_transaction(3, 9797))
    print(send_money(1, 30, 'тест'))



