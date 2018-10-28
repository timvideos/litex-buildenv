# Minimal makefile for Sphinx documentation
#

# Disable make's inbuilt rules
.SUFFIXES:

# You can set these variables from the command line.
TOPDIR        = $(realpath ..)
BUILDDIR      = _build
VENV_ROOT     = $(BUILDDIR)/_venv
SPHINXOPTS    =
SPHINXBUILD   = $(VENV_ROOT)/bin/sphinx-build
SPHINXPROJ    = LiteXBuildEnvironment
SOURCEDIR     = .

# Put it first so that "make" without argument is like "make help".
#-------------------------------------------
help: $(SPHINXBUILD)
	@$(SPHINXRUN) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help

# Set up a virtualenv
#-------------------------------------------
$(VENV_ROOT):
	mkdir -p $<

PYTHONPATH = $(TOPDIR)
export PYTHONPATH

$(VENV_ROOT)/bin/activate:
	virtualenv -p python3 $(VENV_ROOT)

ACTIVATE = source $(VENV_ROOT)/bin/activate


# Install the requirements into the virtualenv
#-------------------------------------------

$(VENV_ROOT)/requirements.stamp: requirements.txt $(VENV_ROOT)/bin/activate | $(VENV_ROOT)
	$(ACTIVATE); pip install -r requirements.txt
	@touch $(VENV_ROOT)/requirements.stamp

$(VENV_ROOT)/lite.stamp: $(VENV_ROOT)/bin/activate | $(VENV_ROOT)
	$(ACTIVATE); \
		for mod in ../third_party/lite*; do \
			if [ -f $$mod/setup.py ]; then \
				pip install $$mod; \
			fi; \
		done
	@touch $(VENV_ROOT)/lite.stamp


$(SPHINXBUILD): $(VENV_ROOT)/requirements.stamp $(VENV_ROOT)/lite.stamp
	@touch $<

distclean:
	rm -rf _build $(VENV_ROOT) .Makefile.d
	mkdir -p _build
	mkdir -p $(VENV_ROOT)

clean:
	rm -rf _doxygen verilog
	@$(ACTIVATE); $(SPHINXRUN) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

testenv:
	@$(ACTIVATE); $(VENV_ROOT)/bin/python3 -c "import sys; print(sys.path)"
	@# Test the import of third_party python libraries
	@$(ACTIVATE); \
		for moddir in ../third_party/migen ../third_party/lite*; do \
			if [ -f $$moddir/setup.py ]; then \
				export mod="$$(basename $$moddir)"; python -c "import $$mod; print($$mod)"; \
			fi; \
		done
	@# Test the import of top level gateware module
	@$(ACTIVATE); $(VENV_ROOT)/bin/python3 -c "import gateware; print(gateware)"

SPHINXRUN = $(ACTIVATE); $(VENV_ROOT)/bin/python3 $(VENV_ROOT)/bin/sphinx-build

.PHONY: distclean clean

# Generate targets for all the other sphinx commands.
#-------------------------------------------
SPHINXCMD = $(SPHINXRUN) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
SPHINXSUBCMD = $(SPHINXRUN) -M $$@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.Makefile.d: $(SPHINXBUILD) Makefile
	mkdir -p _doxygen
	$(SPHINXRUN) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) \
		| grep "^ " \
		| sed -e's/^ \+//' -e's|^\([^ ]*\) \+.*$$|\1: $(SPHINXBUILD)\n\t$(SPHINXSUBCMD)\n\n.PHONY: \1\n\n|' \
		> .Makefile.d

-include .Makefile.d

# Get the intersphinx inventory files.
#-------------------------------------------
INTERSPHINX_FILES := $(shell $(ACTIVATE) && python -c "import conf; print('\n'.join(n[-1][-1] for n in conf.intersphinx_mapping.values()))")
# Python only method for downloading the inv files.
#@URL="$(shell $(ACTIVATE); python3 -c "import conf; print([n[0] for n in conf.intersphinx_mapping.values() if n[-1][-1] == '$@'][0])")"; \
#    $(ACTIVATE); python -c "import urllib.request; url='$${URL}objects.inv'; print('Downloading '+url+' -> $@'); urllib.request.urlretrieve(url, '$@')"
$(INTERSPHINX_FILES): conf.py Makefile
	@mkdir -p _build/intersphinx/
	@rm -f $@
	@URL="$(shell $(ACTIVATE); python3 -c "import conf; print([n[0]+'/objects.inv' for n in conf.intersphinx_mapping.values() if n[-1][-1] == '$@'][0])")"; \
		wget "$$URL" -O "$@"
	@du -h $@
	@touch $@

inv: $(INTERSPHINX_FILES)
	@true

.PHONY: inv

# Wiki Documentation
#--------------------------------------------
wiki:
	if [ ! -d wiki ]; then \
		git clone git+ssh://github.com/timvideos/litex-buildenv.wiki.git wiki; \
	else \
		cd wiki; git pull; \
	fi

.PHONY: wiki

# Use sphinx-apidoc to auto-extract docstring
#--------------------------------------------
SPHINX_APIDOC = --follow-links --separate --module-first --append-syspath
apidoc:
	rm -rf apidoc
	sphinx-apidoc $(SPHINX_APIDOC) --implicit-namespaces -e -o apidoc/litex-buildenv ../ ../third_party ../doc ../build
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litedram ../third_party/litedram/litedram
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/liteeth ../third_party/liteeth/liteeth
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litepcie ../third_party/litepcie/litepcie
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litesata ../third_party/litesata/litesata
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litescope ../third_party/litescope/litescope
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/liteusb ../third_party/liteusb/liteusb
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litevideo ../third_party/litevideo/litevideo
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litex ../third_party/litex/litex
	sphinx-apidoc $(SPHINX_APIDOC) -o apidoc/third_party/litex ../third_party/migen/migen

.PHONY: apidoc

tools:
	rm -rf tools
	$(ACTIVATE); sphinx-apidoc --implicit-namespaces -o tools ../utils

.PHONY: utils
