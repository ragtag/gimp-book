# -*- coding: utf-8 -*-
 
import os, sys
import locale
import gettext
import gimp
 
# Change this variable to your app name!
#  The translation files will be under
#  @LOCALE_DIR@/@LANGUAGE@/LC_MESSAGES/@APP_NAME@.mo
APP_NAME = "book"
 
# This is ok for maemo. Not sure in a regular desktop:
#APP_DIR = os.path.join (sys.prefix, 'share')
APP_DIR = gimp.directory
LOCALE_DIR = os.path.join(APP_DIR, 'plug-ins', 'i18n') # .mo files will then be located in APP_Dir/i18n/LANGUAGECODE/LC_MESSAGES/
print LOCALE_DIR 
# Now we need to choose the language. We will provide a list, and gettext
# will use the first translation available in the list
#
#  In maemo it is in the LANG environment variable
#  (on desktop is usually LANGUAGES)
DEFAULT_LANGUAGES = os.environ.get('LANG', '').split(':')
DEFAULT_LANGUAGES += ['en_US']
 
lc, encoding = locale.getdefaultlocale()
if lc:
    languages = [lc]
# Concat all languages (env + default locale),
#  and here we have the languages and location of the translations
languages += DEFAULT_LANGUAGES
mo_location = LOCALE_DIR

languages = 'fr_FR'
 
# Lets tell those details to gettext
#  (nothing to change here for you)
gettext.install(True, localedir=LOCALE_DIR, unicode=1)
 
gettext.find(APP_NAME, mo_location)
 
gettext.textdomain (APP_NAME)
 
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")

print "LANGUAGES"
print languages
#language = gettext.translation(APP_NAME, mo_location, languages=languages, fallback=True)
language = gettext.translation(APP_NAME, mo_location, languages=languages, fallback=True)
