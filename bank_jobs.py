from bank_server import *
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(timetable_manager.iterate, 'interval', minutes=1, args=(app, ))
scheduler.start()
