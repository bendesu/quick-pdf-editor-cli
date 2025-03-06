create_requirements:
	pip freeze > requirements.txt

install:
	pip install -r requirements.txt

build: install
	pyinstaller --onefile --clean --noconfirm main.py
