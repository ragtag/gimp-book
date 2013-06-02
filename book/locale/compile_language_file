#!/bin/sh
# Helper for compiling .po files to .mo files
echo "Pleasa enter a two letter language code you wish to compile to a .mo file (e.g. en, jp, fr, de)"
read translation_language

if [ -f $translation_language.po ]
then
    echo "Compiling $translation_language.po into a .mo file"
    mkdir -p $translation_language/LC_MESSAGES
    msgfmt $translation_language.po --output-file $translation_language/LC_MESSAGES/book.mo
else
    echo "File '$translation_language.po' not found. Aborting!"
fi
