# -*- mode: makefile-gmake; coding: utf-8 -*-

all:

install: clean
	python3 setup.py install \
	--prefix=$(DESTDIR)/usr/ \
        --install-layout=deb

.PHONY: clean
clean:
	$(RM) -rf build/
	find -name "*.pyc" -delete
	find -name "__pycache__" -delete
