
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

## Project structure

### Views
In Together the views are divided into the following areas, which cover the main features of the application

- Profile views
- Group views
- Swipe views 

#### Profile views
In Toogether there is only one data model for the user, which is called a profile. 
However, in the views a difference between the profile and the user is made.

`User views` (or named like this) 
those in charge of the most basic of the model, 
such as creating the user, deleting it, and handling relevant information for Adins

`Profile Modelview`
these views cover all the actions that the user can do in their profile, 
such as adding photos, updating information, blocking users, etc.


# Deployment using Amazon Elastic Beanstalk

### Deploy using EB CLI
```bash
eb deploy
```

### After deployment
Delete all the folders and files inside the `static`, this is because when the code is deployed, the static files are automatically collected, but, in order to keep the repository clean and without "cache", those files must be deleted once the deployment is successful.
