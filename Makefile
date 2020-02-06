%: dist

dist: pdpyras.py setup.py
	rm -f dist/* && python setup.py sdist

docs/index.html: pdpyras.py README.rst CHANGELOG.rst sphinx/source/index.rst
	rm -fr ./docs && cd sphinx && make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

docs: docs/index.html

install: dist
	python setup.py install 

testpublish: dist
	./publish-test.sh

publish: dist
	twine upload dist/*.tar.gz

