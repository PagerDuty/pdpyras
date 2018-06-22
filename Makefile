.PHONY: docs

docs: pdpyras/__init__.py
	cd docs && make html

test:
	cd tests && ./test_pdpyras.py

build: 
	python setup.py bdist

install: build
	python setup.py install 

%: build
