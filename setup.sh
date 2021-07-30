sudo pip3 install -r requirements.txt
sudo cp bank_nginx.conf /etc/nginx/sites-enabled/
sudo systemctl restart nginx
sudo certbot --nginx -d bank.goto.msk.ru
cp config.py.example config.py
