web: python manage.py collectstatic --no-input && python manage.py migrate --no-input && gunicorn autodocpro.wsgi --bind 0.0.0.0:$PORT --workers 2
