# ChemData
Web-based management tools for groups in chemical education and science.

Login with **admin test_1234**

Install
-
- ```conda create --name ChemData```
- ```conda activate ChemData```

**Install requirements via pip**
(look for requirements.txt or install everything at once: ```pip install -r requirements.txt```)

- ```python manage.py runserver```
(```python manage.py runserver 0.0.0.0:80``` to run on localhost/ + edit settings.py for mobile testing)


Development Notes
- 

Storage is based on https://django-treebeard.readthedocs.io/en/latest/tutorial.html

Load Default Data
-
```python manage.py loaddata ./chemmanager/fixtures/units.json```