.PHONY: docs

docs: pdpyras.py
	rm -r ./docs && cd sphinx && make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

test:
	cd tests && ./test_pdpyras.py

build:
	python setup.py sdist

install: build
	python setup.py install 

%: build
