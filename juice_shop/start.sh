uv add -r requirements.txt 
source .venv/bin/activate
python manage.py makemigrations store
python manage.py makemigrations
python manage.py migrate
python seed_data.py 
python manage.py runserver 0.0.0.0:8000
python manage.py runserver_plus --cert-file /home/user/Desktop/host/certs/cert.pem --key-file /home/user/Desktop/host/certs/key.pem 0.0.0.0:443
