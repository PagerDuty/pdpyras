.PHONY: docs

docs: pdpyras/__init__.py
	python -c 'import pdpyras; print(pdpyras.__doc__)' > README.rst
	cd docs && make html

test:
	cd tests && ./test_pdpyras.py

build: pdpyras/__init__.py
	python setup.py bdist_egg

install: pdpyras/__init__.py
	python setup.py install 
