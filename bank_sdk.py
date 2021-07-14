import requests

host = 'http://127.0.0.1:4567'
trading_token = '477c4c92-6da9-473d-802b-f62e7d0dd604'

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
    print(verify_transaction(3, 9797))



