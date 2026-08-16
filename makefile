
BUILDDIR = nydus-launcher
DEBDIR = nydus-launcher/debian
BYPRODUCTS = $(DEBDIR)/debhelper-build-stamp $(DEBDIR)/files $(DEBDIR)/*.substvars *.build *.buildinfo *.changes *.deb
BYPRODDIRS = $(DEBDIR)/.debhelper $(DEBDIR)/nydus-server $(DEBDIR)/nydus-cli $(DEBDIR)/nydus-client $(DEBDIR)/nydus-common $(DEBDIR)/nydus-users

.PHONY: all clean

all:
	cd $(BUILDDIR) && debuild -uc -us -b

clean:
	rm $(BYPRODUCTS)
	rm -r $(BYPRODDIRS)
