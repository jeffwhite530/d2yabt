#!/usr/bin/env python3
"""Builds the package.
"""



import setuptools



setuptools.setup(
	name="d2yabt",
	version="1.0.2",
	author="Jeff White",
	author_email="44498114+jeffwhite530@users.noreply.github.com",
	description="A diagnostic bundle analyzer for D2iQ products",
	long_description=open("README.md", "r").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/jeffwhite530/d2yabt",
	package_dir={
		"d2yabt": "lib/d2yabt",
	},
	packages=[
		"d2yabt",
		"d2yabt.dcos",
		"d2yabt.service",
		"d2yabt.konvoy",
	],
	scripts=[
		"bin/yabt",
	],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: BSD License",
		"Operating System :: OS Independent",
	],
	install_requires=[
		"pandas",
	],
	python_requires='>=3.6',
)

