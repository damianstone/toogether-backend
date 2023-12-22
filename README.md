
<p float="left" align="left">
  <img src="https://user-images.githubusercontent.com/63305840/150650911-a3aba1cc-c2dd-4ced-9d60-0bd5ea1cfc8e.png" width="300" />
</p>

## What's Toogerher app?
An app where users can create a group with their friends, match with other groups and hang out 

## Technologies
- ⚛️  Django REST framework
- 🔥 Websocket (channels)
- 📍 Geolocation with Gdal, Geos and Postgis
- 🧹 Frake8 and black
- 🐘 PostgreSQL
- 🖼️ Amazon S3
- 🔒 Token authentication

## Featues
### 👀 Basic
- Login and registration with auth token
- Create profile
- Report profiles
- Block profiles
- Password recovery with email verification

### 👤 Your profile
- Update your personal information
- Add photos

### 💃 Swipe single and group profiles
- Support single and group profiles
- Like
- Unlike
- Undo
  
### 🔗 Matchmaking algorithm
List based on
- Your location
- Age
- Gender
- Preferences
- Group sizes
- More above in this documentation!

### 🕺🏼 Create a group profile with your friends
- Create a groups
- Invite friends using unique link
- If admin (creator of the group): remove and add members
- If not admin, join to group using the link and leave 

### 💬 Group chat
- Group chat generated autmatically when joining our creating a group
- For know the chat just support text messages

### 💬 Matches and chats
- Chat with your matches
- Delete matches
- Report and block profiles

mailto: damianstonedev@gmail.com

<img width="3000" alt="toogether" src="https://github.com/toogether-app/toogether-backend/assets/63305840/8a984fe7-a470-47b7-bccc-2e550dac6352">

# Initialization

### Create a virtual environment

For IOS / Linux
``` python
python3 -m venv venv-people
source venv-people/bin/activate 
```

For Windows
``` python
python -m venv venv-people
venv-people\Scripts\activate.bat
```

### Install requirements.txt

```python
pip install -r requirements.txt
```

### Create .env for local PostgreSQL database

```
LOCAL_DB_NAME=name-of-the-database
LOCAL_DB_USER=db-user-name
LOCAL_DB_PASSWORD=db-password
LOCAL_DB_HOST=host-you-want-to-use
LOCAL_DB_PORT=post-you-want-to-use
```

### Migrations folder
Inside `api` create a new folder called `migrations` and inside add the following file:

```
__init__.py
```

### Installing Geospatial libraries
Depending on your operating systems the installation can be quite different
therefore we recommend you to follow the official documentation for this:

https://docs.djangoproject.com/en/4.1/ref/contrib/gis/install/geolibs/

### Migrate models

```python
python manage.py makemigrations
python manage.py migrate
```

### Create a super user account
Creating a superuser will give you administrative privileges, and most important, access to our local internal endpoints
for development purposes

When running the command, choose a memorable email and password

To create a superuser account, use the following command:

```python
python manage.py createsuperuser
```

### Run 

```python
python manage.py runserver
```

### Install Redis for WebSockets connectios
In the following link you can see the different installations for different operating systems
`https://redis.io/docs/getting-started/installation/`

### Run Redis
```bash
redis-server
```

### Stop Redis
```bash
killall redis-server
```

## Style Standards
To format the code in the project, simply run the following command in the root directory of the project:

```bash
black .
```
This command will automatically format all .py files in the project according to the black style guide, which adheres to the PEP 8 style guide

**Make sure you run this command before any pull request**

## Pull Requests

Before any merge to develop or rocket, it will be necessary to make a Pull Request and a code review.

Basic PR structure:

`your-branch` -> `feature-branch` -> `develop` -> `rocket`

### Steps for a Pull Request
1. Push your branch to the remote repository: git push
2.  Navigate to the GitHub website
3.  Create the pull request (PR) manually by selecting the correct `feature-branch` you are working on and clicking on the "New pull request" button
4.  Notify the team about your PR through our communication channel: Discord

## Deployment with Heroku

### Buildpakcs information

Geolocation: GDAL, Geos and PROJ: https://github.com/heroku/heroku-geo-buildpack


### Install Heroku CLI

Using the following link: https://devcenter.heroku.com/articles/heroku-cli

Login and check the apps
```bash
heroku login
heroku apps
```

### Before deploy

From the heroku branch run the following
```bash
python mangage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

In order to use the last builpacks of GDAL and Geos, make sure you do not have set BUILD_WITH_GEO_LIBRARIES

If you do, run the following command
```bash
heroku config:unset BUILD_WITH_GEO_LIBRARIES --app toogether-api
```

Besides, as we are collecting then static files manually, we need to disable the auto coollect static 
```bash
heroku config:set DISABLE_COLLECTSTATIC=1 --app toogether-api
```

### Push the latest changes 

```bash
git push heroku
```

### Manual deploy in Heroku 

Heroku website panel -> Deploy -> Manual branch deploy 


### After deployment

Delete all the folders and files inside the `static`, this is because when the code is deployed, 
the static files are automatically collected, but, in order to keep the repository clean, 
those files must be deleted once the deployment is successful.

### Troubleshooting

To check the logs 
```bash
heroku logs --tail --app toogether-api
```
## Project structure

### Views / Endpoints

The views in Together are divided into three main areas to cover the application's 
features: Profile views, Group views, and Swipe views.

### Profile views

In Together, there is a single data model for users known as the profile model. The distinction between a user and a profile is that a user may log into the app but has not yet created a profile.

`User views`
These views manage the basic functionality of the user model, such as creating and deleting a user.

`Profile Modelview`
This set of views manages all the actions that a user can perform on their profile, such as adding photos, updating information, and blocking other users.

### Grup Views

These endpoints manage all the actions related to groups, such as creating a group with friends and removing members.

### Swipe Views

The swipe views manage the "liking" functionality between users, as well as the `matchmaking algorithm`. This includes all the processes and calculations involved in determining the profiles that a user is matched with. These views are an integral part of the application as they enable the core user interaction and facilitate the potential formation of relationships.

# Matchmaking Algorithm

The matchmaking algorithm in Together is responsible for determining the matches between profiles and groups. This process is initiated when a user "likes" another profile or group.

The algorithm is implemented in the like function and uses several checks to determine the nature of the like being given. There are four possible scenarios for a like:

1. One profile to one profile
2. One profile to a group
3. A group to one profile
4. A group to another group

Each scenario is handled by a different function that performs the necessary operations to determine the match.

## Function Structure

### Inputs
- `request`: a Django request object
- `current_profile` or `current_group`: the profile or group making the like
- `liked_profile` or `liked_group` : the profile or group being liked

### Outputs
A Django response object containing:
- `details`: a string indicating the status of the like, either `LIKE`, `ALREADY_MATCHED`, `NEW_MATCH` or `SAME_MATCH`
- `group_match`: a string indicating whether the match was between groups: `NEITHER`, `BOTH`, `LIKED` or `CURRENT`
- `match_data`: the match serialization in case a new match was created, otherwise this field will not be present.
