TRANSLATING GIMP BOOK

Gimp Book now supports .po files to simplify translation.

I've written a couple of helper scripts, to make it easier to setup translation on Linux. They require msginit and msgfmt, which should be installed on most distros by default (part of gettext). If you're on Windows, you can either try to run it through cygwin, or install the windows version of the gettext tools, or you can mail me at bug@ragnarb.com and I can make a .po file for you.

BEGIN TRANSLATING

To add a translation for a new language enter the locale folder and do the following on the command line:
./add_language.sh

You'll be asked to enter a two letter country code (e.g. no, de, fr etc.), and to enter you e-mail. Not that the e-mail address will be distributed with the language file, which will be publically available as part of Gimp Book.

This generates a .po file (e.g. no.po, de.po etc). You can use Poedit http:/poedit.net or any text editor to edit the .po file. You can look at the fr.po translation for reference.


COMPILING THE TRANSLATION

Gimp Book doesn't actually read the .po file, so you need to compile it into a .mo file, to use it. To do this run:
./comiple_language_file

Again, you'll be asked to enter a two letter code for the language you want to compile. This builds an .mo file in locale/xx/LC_MESSAGES/book.mo (where xx is your lanaguage code).

On Linux Gimp will by default use the LANG environment variable to check which language to run as. You can check what this is set to by running:
echo $LANG

If you want to test your translation, without swithing the language settings for the whole OS, you can do so by running gimp from the terminal like so:
export LANG=fr_FR.UTF-8
gimp

You can replace fr_FR.UTF-8, with the language used for your translation.

