#!/bin/sh
# Merges code changes with translation files.
echo "This will merge changes in the code, with your translation .po file."
echo "Pleasa enter a two letter language code (e.g. en, jp, fr, de)"
read translation_language
if [ -f $translation_language.po ]
then
    msgmerge --output-file=$translation_language.po $translation_language.po book.pot
else
    echo "File '$translation_language.po' not found. Nothing to do."
fi
