
<p float="left" align="left">
  <img src="https://user-images.githubusercontent.com/63305840/150650911-a3aba1cc-c2dd-4ced-9d60-0bd5ea1cfc8e.png" width="300" />
</p>


## Initialization

#### Create a virtual environment
``` python
python3 -m venv venv-backend
source venv-backend/bin/activate 
```

#### Install requirements.txt
```python
pip install -r requirements.txt
```

#### Create .env for local PostgreSQL database
```
LOCAL_DB_NAME=name-of-the-database
LOCAL_DB_USER=db-user-name
LOCAL_DB_PASSWORD=db-password
LOCAL_DB_HOST=host-you-want-to-use
LOCAL_DB_PORT=post-you-want-to-use
```

#### Migrate models
```python
python manage.py makemigrations
python manage.py migrate
````

#### Run
```python
python manage.py runserver
```
