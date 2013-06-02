#!/bin/sh
# Rebuilds the pot file, if the code has been updated.
# Translators don't need to do this.
while true
do
echo -n "This only needs to be run if the source code has been updated. Continue (y/n)?"
read CONFIRM
case $CONFIRM in
y|Y|YES|yes|Yes) break ;;
n|N|no|NO|No)
echo Aborting 
exit
;;
*) echo Please enter only y or n
esac
done

echo "Generating new book.pot file"

xgettext  -c --language=Python --keyword=_ --from-code=UTF-8 --package-name=gimp_book --copyright-holder='Ragnar Brynjúlfsson' --msgid-bugs-address=bug@ragnarb.com --output=book.pot ../book.py
if [ -f book.pot ]
then
    sed -i 's/SOME DESCRIPTIVE TITLE./GIMP Book./g' book.pot
    sed -i 's/(C) YEAR/(C) 2013/g' book.pot
    sed -i 's/This file is distributed under the same license as the PACKAGE package./This file is distirbuted under the GNU General Public License version 3, or later./g' book.pot
    sed -i 's/FIRST AUTHOR <EMAIL@ADDRESS>, YEAR./Ragnar Brynjúlfsson <bug@ragnarb.com>, 2013./g' book.pot
fi


