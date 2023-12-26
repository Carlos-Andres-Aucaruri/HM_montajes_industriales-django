# HM montajes industriales application

## Setup

The first thing to do is to clone the repository:

```sh
$ git clone https://github.com/Andres-Breads/HM_montajes_industriales-django.git
$ cd HM_montajes_industriales-django
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ python -m venv env
$ source env/Scripts/activate
```

Then install the dependencies:

```sh
(env)$ pip install -r requirements.txt
```
Note the `(env)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `venv`.

Once `pip` has finished downloading the dependencies:
```sh
(env)$ python manage.py runserver
```
And navigate to `http://127.0.0.1:8000/`.

## Tests

To run the tests, `cd` into the directory where `manage.py` is:
```sh
(env)$ python manage.py test HMMontajes
```
