#!/bin/sh
# Helper for adding support for a new language
echo "Pleasa enter a two letter language code you wish to create a translation file for (e.g. en, jp, fr, de)"
read translation_language
msginit --input=book.pot --locale=$translation_language
sed -i 's/ASCII/UTF-8/g' '$translation_language.po'
echo "Thank you for maing an effort to translate GIMP Book."
echo "You can now add your translations in the msgstr entries in the $translation_language.po file"
