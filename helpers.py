import json
import threading
from datetime import datetime
from flask import request, abort, jsonify, render_template
from config import *
from sentry_sdk import capture_exception
import sys, os


def gts():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S - ")

def validate(data, rules):
    for rule in rules:
        if not data.get(rule[0]) or not isinstance(data.get(rule[0]), data[1]):
            return False, rule[2]
    return True, ""



def log(error, terminating=False):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

    if PRODUCTION:
        capture_exception(error)

    if terminating:
        print(gts(), exc_type, fname, exc_tb.tb_lineno, error, "CRITICAL")
    else:
        print(gts(), exc_type, fname, exc_tb.tb_lineno, error)


def safe(func):
    def wrapper(*args, **kargs):
        try:
            return func(request.json, *args, **kargs)
        except Exception as e:
            log(e, True)
            abort(500)

    wrapper.__name__ = func.__name__
    return wrapper


def delayed(delay, f, args):
    timer = threading.Timer(delay, f, args=args)
    timer.start()


def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))
