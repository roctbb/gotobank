python3 bank_bot.py >> bank_log.txt 2>&1 & disown
python3 bank_server.py >> server_log.txt 2>&1 & disown
python3 bank_jobs.py >> jobs_log.txt 2>&1 & disown