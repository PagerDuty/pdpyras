.PHONY: docs

docs: pdpyras.py
	rm -fr ./docs && cd sphinx && make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

test:
	cd tests && ./test_pdpyras.py

dist: pdpyras.py
	python setup.py sdist

install: dist
	python setup.py install 

%: dist
