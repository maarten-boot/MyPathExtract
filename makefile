LINE_LENGTH = 160
PL_LINTERS="eradicate,mccabe,pycodestyle,pyflakes"
PL_LINTERS="eradicate,mccabe,pycodestyle,pyflakes,pylint"

# E203 whitespace before ':' [pycodestyle]
# C901 '%s' is too complex (16) [mccabe]
# C0114 Missing module docstring [pylint]
# C0115 Missing class docstring [pylint]
# C0116 Missing function or method docstring [pylint]
# C0301 Line too long (%s/%s) [pylint] :: add :: # pylint: disable=line-too-long
# R0902 Too many instance attributes (15/7) [pylint] :: add:: # pylint: disable=too-many-instance-attributes
# C0103 Variable name "%s" doesn't conform to snake_case naming style [pylint]
# W0719 Raising too general exception: Exception [pylint]
# W0718 Catching too general exception Exception [pylint]
# R0915 Too many statements (51/50) [pylint]
PL_IGNORE="C0103,C0114,C0115,C0116,C0301,E203,C901,R0911,W0718,W0719,R0915"

PY_DIR = .
WHAT = myPathExtract.py

all: prep
	python3 $(WHAT)

prep: black pylama mypy

black:
	black \
		--line-length $(LINE_LENGTH) \
		$(PY_DIR)

pylama:
	pylama \
		--max-line-length $(LINE_LENGTH) \
		--linters $(PL_LINTERS) \
		--ignore $(PL_IGNORE) \
		$(PY_DIR)

mypy:
	mypy \
		--strict \
		--no-incremental \
		$(PY_DIR)

