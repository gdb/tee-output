.PHONY: build upload

build:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*