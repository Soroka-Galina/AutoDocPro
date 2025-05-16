web: gunicorn autodocpro.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --log-file -
release: python manage.py migrate --no-input
