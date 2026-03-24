#!/bin/bash
# Bot aur Web server dono ek saath chalao
python bot.py &
gunicorn server:app --bind 0.0.0.0:$PORT
