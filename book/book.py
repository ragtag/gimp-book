#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GIMP Book
#  by Ragnar Brynjúlfsson
#
# DESCRIPTION
#   book.py is a plug-in for managing multiple pages in GIMP, for working with comic books, 
#   illustrated childrens books, sketchbooks, storyboards or similar.
#
# INSTALLATION
#   Drop the script in your plug-ins folder. On Linux this is ~/.gimp-2.8/plug-ins/
#
# VERSION
version = "current_version"
# AUTHOR 
author = [ 'Ragnar Brynjúlfsson <me@ragnarb.com>', ' ', 'Translators:', ' French - Patrick Depoix' ]
# COPYRIGHT
copyright = "Copyright 2011-2014 © Ragnar Brynjúlfsson"
# WEBSITE
website = "http://ragnarb.com/toolbox/gimp-book/"
plugin = "Gimp Book"
# LICENSE
license = """
GIMP Book
A plug-in for managing multiple pages in GIMP.
Copyright 2011-2014 Ragnar Brynjúlfsson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

import os
import hashlib
import json
import shutil
import gtk
import gobject
import urllib
import re
from sys import path
from gimpfu import *
from gimpenums import *
from time import strftime

# Translation implementation
import locale
import gettext
import gimp
 
APP_NAME = "book"
APP_DIR = gimp.directory # ~/.gimp-2.x
LOCALE_DIR = os.path.join(APP_DIR, 'plug-ins', 'locale') # location of .mo files (e.g. ~/gimp-2.x/plug-ins/locale/fr/LC_MESSAGES/fr.mo)

# Get the default language. On Windows you need to set the LANG variable.
DEFAULT_LANGUAGES = os.environ.get('LANG', '').split(':')
DEFAULT_LANGUAGES += ['en_US']
lc, encoding = locale.getdefaultlocale()
if lc:
    languages = [lc]
languages += DEFAULT_LANGUAGES
mo_location = LOCALE_DIR
 

# Initialize gettext
gettext.install(True, localedir=LOCALE_DIR, unicode=1)
gettext.find(APP_NAME, mo_location)
gettext.textdomain (APP_NAME)
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
language = gettext.translation(APP_NAME, mo_location, languages=languages, fallback=True)

# Define '_' function, so that strings will be with their correct translation.
_ = language.ugettext #use ugettext instead of getttext to avoid unicode errors


THUMBMIN=128
THUMBMAX=512

class Thumb():
    # Managing thumbnails, and creating new ones when needed.
    def __init__(self, imagepath, size, main):
        self.imagepath = imagepath # bla/pages/one.xcf
        self.size = size
        self.main = main
        imagename = os.path.split(imagepath)[1]
        self.thumbdir = os.path.join(os.path.split(os.path.split(imagepath)[0])[0], 'thumbs', str(size))
        self.path = os.path.join(self.thumbdir, imagename+'.png')
        self.get_thumb()

    def get_thumb(self):
        # Fetch the thumb, if it exists.
        if os.path.exists(self.path) and os.path.exists(self.imagepath):
            if float(os.stat(self.path).st_mtime) < float(os.stat(self.imagepath).st_mtime):
                self.build_thumb()
        else:
            if os.path.exists(self.imagepath):
                self.build_thumb()
        self.thumbpix = gtk.gdk.pixbuf_new_from_file(self.path)

    def build_thumb(self):
        # Build or rebuild a thumb for the image.
        self.main.progress.show()
        while gtk.events_pending():
            gtk.main_iteration()
        if not os.path.exists(self.thumbdir):
            os.makedirs(self.thumbdir)
        img = pdb.gimp_file_load(self.imagepath, self.imagepath)
        img.flatten()
        width = int(self.size) if img.width > img.height else int(float(img.width) / img.height * self.size)
        height = int(self.size) if img.height > img.width else int(float(img.height) / img.width * self.size)
        pdb.gimp_image_scale_full(img, width, height, 2)
        drw = pdb.gimp_image_get_active_layer(img)
        thumbname = os.path.split(self.path)[1]
        pdb.file_png_save(img, drw, self.path, thumbname, False, 9, False, False, False, True, True)
        pdb.gimp_image_delete(img)
        self.main.progress.hide()


class NTFileChooserButton(gtk.Button):
    # Hack for Windows to get a working FileChooserButton in Gimp 2.8.6+
    def get_filename(self):
        return self.filename

    def set_filename(self, filename):
        self.filename = filename
        self.set_label(filename[:24] + (filename[24:] and '...'))

class NewBookWin(gtk.Window):
    # Interface for creating new books.
    def __init__(self, main):
        self.main = main
        self.main.set_sensitive(False)
        # Create a new book.
        win = super(NewBookWin, self).__init__()
        self.set_transient_for(main)
        self.set_title(_("Create a New Book..."))
        self.set_size_request(400, 500)
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(10)

        # Box for divding the window in three parts, name, page and buttons.
        cont = gtk.VBox(False, 4)
        self.add(cont)

        # Split the book frame in 4.
        bookbox = gtk.VBox(False, 2)
        cont.add(bookbox)
        # Name entry field
        namebox = gtk.HBox(False, 2)
        bookbox.pack_start(namebox)
        namelabel = gtk.Label(_("Name:"))
        namelabel.set_size_request(80, 28)
        namelabel.set_alignment(0.0, 0.5)
        self.nameentry = gtk.Entry()
        self.nameentry.set_size_request(286, 28)
        namebox.pack_start(namelabel, expand=False, fill=False, padding=4)
        namebox.pack_start(self.nameentry, expand=False, fill=False, padding=4)
        # Destination dialog
        self.destdialog = gtk.FileChooserDialog(_("Create a New Book"), self.main, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self.destdialog.set_default_response(gtk.RESPONSE_OK)
        # Destination
        destbox = gtk.HBox(False, 2)
        bookbox.pack_start(destbox)
        destlabel = gtk.Label(_("Destination:"))
        destlabel.set_size_request(80, 32)
        destlabel.set_alignment(0.0, 0.5)
        if os.name == 'nt':
            home = os.path.expanduser("~")
            self.destbutton = NTFileChooserButton(home)
            self.destbutton.set_filename(home)
            self.destbutton.connect("clicked", self.ntdestdialog)
        else:
            self.destbutton = gtk.FileChooserButton(self.destdialog)
        self.destbutton.set_size_request(286, 28)
        destbox.pack_start(destlabel, expand=False, fill=False, padding=4)
        destbox.pack_start(self.destbutton, expand=False, fill=False, padding=4)
        
        # Frame for the page size and color space.
        pageframe = gtk.Frame()
        pageframe.set_shadow_type(gtk.SHADOW_NONE)
        pageframelabel = gtk.Label(_("<b>Page</b>"))
        pageframelabel.set_use_markup(True)
        pageframe.set_label_widget(pageframelabel)
        cont.add(pageframe)
        # Split the frame in 6
        pagebox = gtk.VBox(False, 2)
        pagebox.set_border_width(10)
        pageframe.add(pagebox)
        # Width and height fields.
        spinbuttonheight = 27
        if os.name == 'nt':
            spinbuttonheight = 22
        widthbox = gtk.HBox(False, 2)
        pagebox.pack_start(widthbox)
        widthlabel = gtk.Label(_("Width:"))
        widthlabel.set_size_request(80, spinbuttonheight)
        widthlabel.set_alignment(0.0, 0.5)
        widthadjust = gtk.Adjustment(2800, 1, 262144, 1, 100)
        self.widthentry = gtk.SpinButton(widthadjust)
        self.widthentry.set_size_request(80, spinbuttonheight)
        self.widthentry.set_value(2800)
        widthpixels = gtk.Label(_("pixels"))
        widthbox.pack_start(widthlabel, expand=False, fill=False, padding=2)
        widthbox.pack_start(self.widthentry, expand=False, fill=False, padding=2)
        widthbox.pack_start(widthpixels, expand=False, fill=False, padding=2)
        heightbox = gtk.HBox(False, 2)
        pagebox.pack_start(heightbox)
        heightlabel = gtk.Label(_("Height:"))
        heightlabel.set_size_request(80, spinbuttonheight)
        heightlabel.set_alignment(0.0, 0.5)
        heightadjust = gtk.Adjustment(4000, 1, 262144, 1, 100)
        self.heightentry = gtk.SpinButton(heightadjust)
        self.heightentry.set_size_request(80, spinbuttonheight)
        self.heightentry.set_value(4000)
        heightpixels = gtk.Label(_("pixels"))
        heightbox.pack_start(heightlabel, expand=False, fill=False, padding=2)
        heightbox.pack_start(self.heightentry, expand=False, fill=False, padding=2)
        heightbox.pack_start(heightpixels, expand=False, fill=False, padding=2)
        ppibox = gtk.HBox(False, 2)
        pagebox.pack_start(ppibox)
        ppilabel = gtk.Label(_("Resolution:"))
        ppilabel.set_size_request(80, spinbuttonheight)
        ppilabel.set_alignment(0.0, 0.5)
        ppiadjust = gtk.Adjustment(400, 1, 262144, 1, 100)
        self.ppientry = gtk.SpinButton(ppiadjust)
        self.ppientry.set_size_request(80, spinbuttonheight)
        self.ppientry.set_value(400)
        ppipixels = gtk.Label(_("pixels/in"))
        ppibox.pack_start(ppilabel, expand=False, fill=False, padding=2)
        ppibox.pack_start(self.ppientry, expand=False, fill=False, padding=2)
        ppibox.pack_start(ppipixels, expand=False, fill=False, padding=2)
        # Color space:
        colorbox = gtk.HBox(False, 2)
        pagebox.pack_start(colorbox)
        colorlabel = gtk.Label(_("Color Space:"))
        colorlabel.set_size_request(80, 28)
        colorlabel.set_alignment(0.0, 0.5)
        colorlist = gtk.ListStore(gobject.TYPE_STRING)
        colors = [ _("RBG color"), _("Grayscale") ]
        for color in colors:
            colorlist.append([color])
        self.colormenu = gtk.ComboBox(colorlist)
        self.colormenu.set_size_request(280, 28)
        colorcell = gtk.CellRendererText()
        self.colormenu.pack_start(colorcell, True)
        self.colormenu.add_attribute(colorcell, 'text', 0)
        self.colormenu.set_active(0)
        colorbox.pack_start(colorlabel, expand=False, fill=False, padding=2)
        colorbox.pack_start(self.colormenu, expand=False, fill=False, padding=2)
        # Background fill.
        fillbox = gtk.HBox(False, 2)
        pagebox.pack_start(fillbox)
        filllabel = gtk.Label(_("Fill with:"))
        filllabel.set_size_request(80, 28)
        filllabel.set_alignment(0.0, 0.5)
        filllist = gtk.ListStore(gobject.TYPE_STRING)
        fills = [ _("Foreground color"), _("Background color"), _("White"), _("Transparency") ]
        for fill in fills:
            filllist.append([fill])
        self.fillmenu = gtk.ComboBox(filllist)
        self.fillmenu.set_size_request(280, 28)
        fillcell = gtk.CellRendererText()
        self.fillmenu.pack_start(fillcell, True)
        self.fillmenu.add_attribute(fillcell, 'text', 0)
        self.fillmenu.set_active(2)
        fillbox.pack_start(filllabel, expand=False, fill=False, padding=2)
        fillbox.pack_start(self.fillmenu, expand=False, fill=False, padding=2)

        # Frame for guides for margins and bleed
        guideframe = gtk.Frame()
        guideframe.set_shadow_type(gtk.SHADOW_NONE)
        guideframelabel = gtk.Label(_("<b>Guides</b>"))
        guideframelabel.set_use_markup(True)
        guideframe.set_label_widget(guideframelabel)
        cont.add(guideframe)
        # Split the frame in 6
        guidebox = gtk.VBox(False, 2)
        guidebox.set_border_width(10)
        guideframe.add(guidebox)
        # Margin fields.
        topbox = gtk.HBox(False, 2)
        guidebox.pack_start(topbox)
        toplabel = gtk.Label(_("Top Margins:"))
        toplabel.set_size_request(120, spinbuttonheight)
        toplabel.set_alignment(0.0, 0.5)
        topadjust = gtk.Adjustment(0, 0, 262144, 1, 100)
        self.topentry = gtk.SpinButton(topadjust)
        self.topentry.set_size_request(80, spinbuttonheight)
        self.topentry.set_value(0)
        toppixels = gtk.Label(_("pixels"))
        topbox.pack_start(toplabel, expand=False, fill=False, padding=2)
        topbox.pack_start(self.topentry, expand=False, fill=False, padding=2)
        topbox.pack_start(toppixels, expand=False, fill=False, padding=2)
        bottombox = gtk.HBox(False, 2)
        guidebox.pack_start(bottombox)
        bottomlabel = gtk.Label(_("Bottom Margins:"))
        bottomlabel.set_size_request(120, spinbuttonheight)
        bottomlabel.set_alignment(0.0, 0.5)
        bottomadjust = gtk.Adjustment(0, 0, 262144, 1, 100)
        self.bottomentry = gtk.SpinButton(bottomadjust)
        self.bottomentry.set_size_request(80, spinbuttonheight)
        self.bottomentry.set_value(0)
        bottompixels = gtk.Label(_("pixels"))
        bottombox.pack_start(bottomlabel, expand=False, fill=False, padding=2)
        bottombox.pack_start(self.bottomentry, expand=False, fill=False, padding=2)
        bottombox.pack_start(bottompixels, expand=False, fill=False, padding=2)
        sidesbox = gtk.HBox(False, 2)
        guidebox.pack_start(sidesbox)
        sideslabel = gtk.Label(_("Side Margins:"))
        sideslabel.set_size_request(120, spinbuttonheight)
        sideslabel.set_alignment(0.0, 0.5)
        sidesadjust = gtk.Adjustment(0, 0, 262144, 1, 100)
        self.sidesentry = gtk.SpinButton(sidesadjust)
        self.sidesentry.set_size_request(80, spinbuttonheight)
        self.sidesentry.set_value(0)
        sidespixels = gtk.Label(_("pixels"))
        sidesbox.pack_start(sideslabel, expand=False, fill=False, padding=2)
        sidesbox.pack_start(self.sidesentry, expand=False, fill=False, padding=2)
        sidesbox.pack_start(sidespixels, expand=False, fill=False, padding=2)
        bleedbox = gtk.HBox(False, 2)
        guidebox.pack_start(bleedbox)
        bleedlabel = gtk.Label(_("Bleed:"))
        bleedlabel.set_size_request(120, spinbuttonheight)
        bleedlabel.set_alignment(0.0, 0.5)
        bleedadjust = gtk.Adjustment(0, 0, 262144, 1, 100)
        self.bleedentry = gtk.SpinButton(bleedadjust)
        self.bleedentry.set_size_request(80, spinbuttonheight)
        self.bleedentry.set_value(0)
        bleedpixels = gtk.Label(_("pixels"))
        bleedbox.pack_start(bleedlabel, expand=False, fill=False, padding=2)
        bleedbox.pack_start(self.bleedentry, expand=False, fill=False, padding=2)
        bleedbox.pack_start(bleedpixels, expand=False, fill=False, padding=2)
        
        # Buttons
        buttonbox = gtk.HBox(False, 2)
        cont.add(buttonbox)
        # Cancel
        cancelbutton = gtk.Button(_("Cancel"))
        cancelbutton.connect("clicked", self.cancel)
        buttonbox.pack_start(cancelbutton)
        # OK
        okbutton = gtk.Button(_("Ok"))
        okbutton.connect("clicked", self.ok)
        buttonbox.pack_start(okbutton)

        self.show_all()

    def ntdestdialog(self, input):
        # FileChooserButton bugs out on Windows after Gimp 2.8.4, so this is an alternative solution.
        response = self.destdialog.run()
        if response == gtk.RESPONSE_OK:
            self.destbutton.set_filename(self.destdialog.get_filename())
        self.destdialog.hide()

    def cancel(self, widget):
        # Cancel book creation and close the window.
        self.destroy()

    def ok(self, widget):
        # Creates a new book.
        self.main.close_book()
        self.book = Book(self.main)
        self.book.make_book(self.destbutton.get_filename(), self.nameentry.get_text(), self.widthentry.get_value(), self.heightentry.get_value(), self.ppientry.get_value(), self.colormenu.get_active(),  self.fillmenu.get_active(), self.topentry.get_value(), self.bottomentry.get_value(), self.sidesentry.get_value(), self.bleedentry.get_value())
        self.main.add_book(self.book)
        self.destroy()

    def __del__(self):
        # Destructor re-enables main window.
        self.main.set_sensitive(True)

class ExportWin(gtk.Window):
    # Windows for exporting the book in various formats.
    def __init__(self, main):
        # Build the export window.
        self.main = main
        win = super(ExportWin, self).__init__()
        self.set_transient_for(main)
        self.set_title(_("Export Book..."))
        self.set_size_request(500, 500)
        self.set_position(gtk.WIN_POS_CENTER)
        # Divide the window into two columns, as it doesn't fit on one 1024x768 screen. :)
        dtab = gtk.VBox()
        mtab = gtk.VBox()
        stab = gtk.VBox()
        ftab = gtk.VBox()
        self.tabs = gtk.Notebook()
        dtabl = gtk.Label(_("Destination"))
        self.tabs.append_page(dtab, dtabl)
        mtabl = gtk.Label(_("Margins"))
        self.tabs.append_page(mtab, mtabl)
        stabl = gtk.Label(_("Image Size"))
        self.tabs.append_page(stab, stabl)
        ftabl = gtk.Label(_("File Format"))
        self.tabs.append_page(ftab, ftabl)
        cont = gtk.VBox(False, 4)
        cont.add(self.tabs)
        self.add(cont)

        # Destination frame
        destframe = gtk.Frame()
        destframe.set_shadow_type(gtk.SHADOW_NONE)
        destframelabel = gtk.Label(_("<b>Destination</b>"))
        destframelabel.set_use_markup(True)
        destframe.set_label_widget(destframelabel)
        # Destination table
        destt = gtk.Table(4, 5, False)
        destl = gtk.Label(_("Destination Folder:"))
        self.destdialog = gtk.FileChooserDialog(_("Export to"), self.main, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self.destdialog.set_default_response(gtk.RESPONSE_OK)
        if os.name == 'nt':
            home = os.path.expanduser("~")
            self.destbutton = NTFileChooserButton(home)
            self.destbutton.set_filename(home)
            self.destbutton.connect("clicked", self.ntdestdialog)
        else:
            self.destbutton = gtk.FileChooserButton(self.destdialog)

        namel = gtk.Label(_("Name Pages Using:"))
        namels = gtk.ListStore(gobject.TYPE_STRING)
        for o in [ _("Book Name"), _("Page Names"), _("Page Numbers"), _("Custom Name") ]:
            namels.append([o])
        self.namem = gtk.ComboBox(namels)
        namec = gtk.CellRendererText()
        self.namem.pack_start(namec, False)
        self.namem.add_attribute(namec, 'text', 0)
        self.namem.set_active(0)
        entl = gtk.Label(_("Custom Name:"))
        self.namee = gtk.Entry(128)
        self.namee.set_sensitive(False)
        self.namem.connect("changed", self.name_option_changed)

        # Page range
        self.pagecount = len(self.main.book.pagestore)-1
        rangel = gtk.Label(_("Pages from/to:"))
        rangefroma = gtk.Adjustment(1, 0, self.pagecount, 1)
        self.rangefrom = gtk.SpinButton(rangefroma, 1, 1)
        self.rangefrom.connect("changed", self.rangefromchanged)
        rangetoa = gtk.Adjustment(self.pagecount, 0, self.pagecount, 1)
        self.rangeto = gtk.SpinButton(rangetoa, 1, 1,)
        self.rangeto.connect("changed", self.rangetochanged)

        # Layer tagging frame
        tagf = gtk.Frame()
        tagf.set_shadow_type(gtk.SHADOW_NONE)
        tagfl = gtk.Label(_("<b>Layer Tags</b>"))
        tagfl.set_use_markup(True)
        tagf.set_label_widget(tagfl)
        tagt = gtk.Table(2,3)

        tagshowl = gtk.Label(_("Show Layers Tagged With:"))
        self.tagshow = gtk.Entry(4048)
        taghidel = gtk.Label(_("Hide Layers Tagged With:"))
        self.taghide = gtk.Entry(4048)
        tagunl = gtk.Label(_("Action for Untagged Layers:"))
        tagunls = gtk.ListStore(gobject.TYPE_STRING)
        for o in [ _("Don't Touch"), _("Show"), _("Hide") ]:
            tagunls.append([o])
        self.tagunm = gtk.ComboBox(tagunls)
        tagunc = gtk.CellRendererText()
        self.tagunm.pack_start(tagunc, False)
        self.tagunm.add_attribute(tagunc, 'text', 0)
        self.tagunm.set_active(0)

        tagt.attach(taghidel, 0,1,0,1)
        tagt.attach(self.taghide, 1,2,0,1)
        tagt.attach(tagshowl, 0,1,1,2)
        tagt.attach(self.tagshow, 1,2,1,2)
        tagt.attach(tagunl, 0,1,2,3)
        tagt.attach(self.tagunm, 1,2,2,3)
        tagf.add(tagt)

        # Attach stuff to the table
        destt.attach(destl, 0,2,0,1)
        destt.attach(self.destbutton, 2,4,0,1)
        destt.attach(namel, 0,2,1,2)
        destt.attach(self.namem, 2,4,1,2)
        destt.attach(entl, 0,2,2,3)
        destt.attach(self.namee, 2,4,2,3)
        destt.attach(rangel, 0,2,3,4)
        destt.attach(self.rangefrom, 2,3,3,4)
        destt.attach(self.rangeto, 3,4,3,4)
        destt.attach(tagf, 0,4,4,5)
        destframe.add(destt)
        dtab.add(destframe)


        # Margin frame
        self.margf = gtk.Frame()
        self.margf.set_shadow_type(gtk.SHADOW_NONE)
        margfl = gtk.Label(_("<b>Margins</b>"))
        margfl.set_use_markup(True)
        self.margf.set_label_widget(margfl)
        mtab.add(self.margf)

        # Marg table
        margt = gtk.Table(5,2)
        margtopl = gtk.Label(_("Top:"))
        margtopa = gtk.Adjustment(0, -65536, 65536, 1, 10)
        self.margtop = gtk.SpinButton(margtopa, 1, 0)
        self.margtop.set_numeric(True)
        margbotl = gtk.Label(_("Bottom:"))
        margbota = gtk.Adjustment(0, -65536, 65536, 1, 10)
        self.margbot = gtk.SpinButton(margbota, 1, 0)
        self.margtop.set_numeric(True)
        marginnerl = gtk.Label(_("Inner:"))
        marginnera = gtk.Adjustment(0, -65536, 65536, 1, 10)
        self.marginner = gtk.SpinButton(marginnera, 1, 0)
        self.marginner.set_numeric(True)
        margouterl = gtk.Label(_("Outer:"))
        margoutera = gtk.Adjustment(0, -65536, 65536, 1, 10)
        self.margouter = gtk.SpinButton(margoutera, 1, 0)
        self.margouter.set_numeric(True)
        # Background color
        margcolf = gtk.Frame()
        margcolf.set_shadow_type(gtk.SHADOW_NONE)
        margcolfl = gtk.Label(_("<b>Background Color</b>"))
        margcolfl.set_use_markup(True)
        margcolf.set_label_widget(margcolfl)
        margcolt = gtk.Table(2,2)
        margcolml = gtk.Label(_("Use:"))
        margconts = gtk.ListStore(gobject.TYPE_STRING)
        for o in [ _("Page's Background Color"), _("Black"), _("White"), _("Custom Color") ]:
            margconts.append([o])
        self.margcolm = gtk.ComboBox(margconts)
        margcolc = gtk.CellRendererText()
        self.margcolm.pack_start(margcolc, True)
        self.margcolm.add_attribute(margcolc, 'text', 0)
        self.margcolm.set_active(0)
        self.margcolm.connect("changed", self.bg_color_changed)
        self.margcoll = gtk.Label(_("Background Color:"))
        self.margcoll.set_sensitive(False)
        self.margcol = gtk.ColorButton(gtk.gdk.Color(0,0,0))
        self.margcol.set_sensitive(False)

        margcolt.attach(margcolml, 0,1,0,1)
        margcolt.attach(self.margcolm, 1,2,0,1)
        margcolt.attach(self.margcoll, 0,1,1,2)
        margcolt.attach(self.margcol, 1,2,1,2)
        margcolf.add(margcolt)
        margt.attach(margtopl, 0,1,0,1)
        margt.attach(self.margtop, 1,2,0,1)
        margt.attach(margbotl, 0,1,1,2)
        margt.attach(self.margbot, 1,2,1,2)
        margt.attach(marginnerl, 0,1,2,3)
        margt.attach(self.marginner, 1,2,2,3)
        margt.attach(margouterl, 0,1,3,4)
        margt.attach(self.margouter, 1,2,3,4)
        margt.attach(margcolf,0,2,4,5)
        self.margf.add(margt)

        # Size frame
        self.templatew, self.templateh = self.main.book.get_template_size()
        self.wfactor = float(self.templateh) / float(self.templatew)
        self.hfactor = float(self.templatew) / float(self.templateh)
        self.scalef = gtk.Frame()
        self.scalef.set_shadow_type(gtk.SHADOW_NONE)
        scalefl = gtk.Label(_("<b>Image Size</b>"))
        scalefl.set_use_markup(True)
        self.scalef.set_label_widget(scalefl)
        stab.add(self.scalef)
        # Size table
        scalet = gtk.Table(3,4)
        scalewl = gtk.Label(_("Width:")) 
        scalewa = gtk.Adjustment(100, 1, 65536, 1, 10)
        self.scalew = gtk.SpinButton(scalewa, 1, 1)
        self.scalew.set_numeric(True)
        self.scalew.set_text("100")
        self.scalew.connect("value-changed", self.scalew_changed)
        scalehl = gtk.Label(_("Height:"))
        scaleha = gtk.Adjustment(100, 1, 65536, 1, 10)
        self.scaleh = gtk.SpinButton(scaleha, 1, 1)
        self.scaleh.set_numeric(True)
        self.scaleh.set_text("100")
        self.scaleh.connect("value-changed", self.scaleh_changed)
        self.scalelink = gtk.ToggleButton("]")
        self.scalelink.set_active(True)
        self.scalelink.connect("clicked", self.scalelink_toggled)
        scaletypels = gtk.ListStore(gobject.TYPE_STRING)
        for o in [ _("Percent"), _("Pixels") ]:
            scaletypels.append([o])
        self.scaletype = gtk.ComboBox(scaletypels)
        scaletypec = gtk.CellRendererText()
        self.scaletype.pack_start(scaletypec, True)
        self.scaletype.add_attribute(scaletypec, 'text', 0)
        self.scaletype.set_active(0)
        self.scaletype.connect("changed", self.scaletype_changed)

        interpl = gtk.Label(_("Interpolation:"))
        interpls = gtk.ListStore(gobject.TYPE_STRING)
        for o in [ _("None"), _("Linear"), _("Cubic"), _("Sinc (Lanczos3)") ]:
            interpls.append([o])
        self.interp = gtk.ComboBox(interpls)
        interpc = gtk.CellRendererText()
        self.interp.pack_start(interpc, True)
        self.interp.add_attribute(interpc, 'text', 0)
        self.interp.set_active(3)
        scalet.attach(scalewl, 0,1,0,1)
        scalet.attach(self.scalew, 1,2,0,1)
        scalet.attach(scalehl, 0,1,1,2)
        scalet.attach(self.scaleh, 1,2,1,2)
        scalet.attach(self.scalelink, 2,3,0,2)
        scalet.attach(self.scaletype, 3,4,1,2)
        scalet.attach(interpl, 0,2,2,3)
        scalet.attach(self.interp, 2,4,2,3)
        self.scalef.add(scalet)

        # File format frame
        formatf = gtk.Frame()
        formatf.set_shadow_type(gtk.SHADOW_NONE)
        formatfl = gtk.Label(_("<b>File Format</b>"))
        formatfl.set_use_markup(True)
        formatf.set_label_widget(formatfl)
        ftab.add(formatf)
        # Format table
        formatt = gtk.Table(2,2)
        formatl = gtk.Label(_("File Format:"))
        formatls = gtk.ListStore(gobject.TYPE_STRING)
        formatoptions = [  _("GIF image (*.gif)"), _("GIMP XCF image (*.xcf)"), _("JPEG image (*.jpg)"), _("OpenRaster (*.ora)"), _("Photoshop image (*.psd)"), _("PNG image (*.png)"), _("TIFF image (*.tif)") ]
        for formatoption in formatoptions:
            formatls.append([formatoption])
        self.formatm = gtk.ComboBox(formatls)
        formatc = gtk.CellRendererText()
        self.formatm.pack_start(formatc, True)
        self.formatm.add_attribute(formatc, 'text', 0)
        self.formatm.set_active(2) 
        self.formatm.connect("changed", self.format_changed)

        self.gift = self.gif()
        self.xcft = self.xcf()
        self.jpgt = self.jpg()
        self.orat = self.ora()
        self.psdt = self.psd()
        self.pngt = self.png()
        self.tift = self.tif()

        formatt.attach(formatl, 0,1,0,1)
        formatt.attach(self.formatm, 1,2,0,1)
        formatt.attach(self.gift, 0,2,1,2)
        formatt.attach(self.xcft, 0,2,1,2)
        formatt.attach(self.jpgt, 0,2,1,2)
        formatt.attach(self.orat, 0,2,1,2)
        formatt.attach(self.psdt, 0,2,1,2)
        formatt.attach(self.pngt, 0,2,1,2)
        formatt.attach(self.tift, 0,2,1,2)
        formatf.add(formatt)

        # Done buttons
        self.doneb = gtk.HBox(True, 4)
        cancelb = gtk.Button(_("Cancel"))
        cancelb.connect("clicked", self.close)
        exportb = gtk.Button(_("Export Pages"))
        exportb.connect("clicked", self.export)
        self.doneb.pack_start(cancelb)
        self.doneb.pack_start(exportb)
        cont.add(self.doneb)

        # Progress bar.
        self.progress = gtk.ProgressBar()
        cont.pack_end(self.progress, False, False, 0)

        self.show_all()
        self.progress.hide()
        self.format_changed(2)

    def ntdestdialog(self, input):
        # FileChooserButton bugs out on Windows after Gimp 2.8.4, so this is an alternative solution.
        response = self.destdialog.run()
        if response == gtk.RESPONSE_OK:
            self.destbutton.set_filename(self.destdialog.get_filename())
        self.destdialog.hide()

    def name_option_changed(self, namem):
        # Enable entry field if name option is set to custom.
        if namem.get_active() == 3:
            self.namee.set_sensitive(True)
        else:
            self.namee.set_sensitive(False)

    def rangefromchanged(self, sb):
        # Page from changed.
        if self.rangefrom.get_value() > self.rangeto.get_value():
            self.rangeto.set_value(self.rangefrom.get_value())

    def rangetochanged(self, sb):
        # Page to changed.
        if self.rangefrom.get_value() > self.rangeto.get_value():
            self.rangefrom.set_value(self.rangeto.get_value())

    def bg_color_changed(self, w):
        # The background color option was changed.
        if self.margcolm.get_active() == 3:
            self.margcoll.set_sensitive(True)
            self.margcol.set_sensitive(True)
        else:
            self.margcoll.set_sensitive(False)
            self.margcol.set_sensitive(False)

    def scalew_changed(self, sb):
        # Keep width and height relative, if scalelink is on.
        if self.scalelink.get_active():
            if self.scaletype.get_active(): # Pixels
                self.scaleh.set_value( self.scalew.get_value() * self.wfactor )
            else: # Percent
                self.scaleh.set_value(self.scalew.get_value())

    def scaleh_changed(self, sb):
        # Keep widht and height relative, if scalelink is on.
        if self.scalelink.get_active():
            if self.scaletype.get_active(): # Pixels
                self.scalew.set_value( self.scaleh.get_value() * self.hfactor )
            else: # Percent
                self.scalew.set_value(self.scaleh.get_value())

    def scalelink_toggled(self, scalelink):
        # Scale link has been toggled. Adjust numbers if link on.
        if scalelink.get_active(): # Link on
            self.scalew_changed(self.scalew)
            scalelink.set_label("]")
        else:
            scalelink.set_label(" ")

    def scaletype_changed(self, scaletype):
        # Scale type toggled between pixels and percent.
        if scaletype.get_active(): # Pixels
            self.scalew.set_value( int((self.scalew.get_value() / 100) * self.templatew) )
            if not self.scalelink.get_active():
                self.scaleh.set_value( self.scalew.get_value() * self.wfactor )
            self.scalew.set_digits(0)
            self.scaleh.set_digits(0)
        else: # Percent
            self.scalew.set_digits(1)
            self.scaleh.set_digits(1)
            self.scalew.set_value( (self.scalew.get_value() / self.templatew) * 100 )
            if not self.scalelink.get_active():
                self.scaleh.set_value(self.scalew.get_value())

    def format_changed(self, formatm):
        # Enable/disable relevant file format options.
        ext = self.main.book.format_index_to_extension(self.formatm.get_active())
        self.gift.hide()
        self.xcft.hide()
        self.jpgt.hide()
        self.orat.hide()
        self.psdt.hide()
        self.pngt.hide()
        self.tift.hide()
        if ext == "gif":
            self.gift.show()
        elif ext == "xcf":
            self.xcft.show()
        elif ext == "jpg":
            self.jpgt.show()
        elif ext == "ora":
            self.orat.show()
        elif ext == "psd":
            self.psdt.show()
        elif ext == "png":
            self.pngt.show()
        elif ext == "tif":
            self.tift.show()

    def gif(self):
        # GIF save options GUI.
        gift = gtk.Table(4,2)
        self.gifgrayscale = gtk.CheckButton(_("Convert to Grayscale"))
        gifcolorsl = gtk.Label(_("Colors:"))
        gifcolorsa = gtk.Adjustment(255, 2, 256, 1)
        self.gifcolors = gtk.SpinButton(gifcolorsa)
        gifdithl = gtk.Label(_("Color Dithering:"))
        gifdithls = gtk.ListStore(gobject.TYPE_STRING)
        for g in [ _("None"), _("Floyd-Steinberg (normal)"), _("Floyd-Steinberg (reduced color bleeding)"), _("Positioned") ]:
            gifdithls.append([g])
        gifdithc = gtk.CellRendererText()
        self.gifdith = gtk.ComboBox(gifdithls)
        self.gifdith.pack_start(gifdithc, True)
        self.gifdith.add_attribute(gifdithc, 'text', 0)
        self.gifdith.set_active(0)
        self.gifinterlace = gtk.CheckButton(_("Interlace"))
        gift.attach(self.gifgrayscale, 0,2,0,1)
        gift.attach(gifcolorsl, 0,1,1,2)
        gift.attach(self.gifcolors, 1,2,1,2)
        gift.attach(gifdithl, 0,1,2,3)
        gift.attach(self.gifdith, 1,2,2,3)
        gift.attach(self.gifinterlace, 0,2,3,4)
        return gift

    def xcf(self):
        # XCF save options GUI.
        xcft = gtk.Table(1,2)
        self.xcfflatten = gtk.CheckButton(_("Flatten"))
        self.xcfflatten.set_active(False)
        xcft.attach(self.xcfflatten, 0,2,0,1)
        return xcft

    def jpg(self):
        # JPEG save options GUI.
        jpgt = gtk.Table(9,2)
        jpgqualityl = gtk.Label(_("Quality:"))
        jpgqualitya = gtk.Adjustment(85, 0, 100, 1, 10, 10)
        self.jpgquality = gtk.HScale(jpgqualitya)
        self.jpgquality.set_digits(0)
        jpgsmoothingl = gtk.Label(_("Smoothing:"))
        jpgsmoothinga = gtk.Adjustment(0.00, 0.00, 1.00, 0.01, 0.1, 0.1)
        self.jpgsmoothing = gtk.HScale(jpgsmoothinga)
        self.jpgsmoothing.set_digits(2)
        self.jpgoptimize = gtk.CheckButton(_("Optimize"))
        self.jpgoptimize.set_active(True)
        self.jpgprogressive = gtk.CheckButton(_("Progressive"))
        self.jpgrestart = gtk.CheckButton(_("Restart Markers"))
        self.jpgrestart.connect("clicked", self.jpgrestartchecked)
        jpgfreql = gtk.Label(_("Marker Frequency:"))
        jpgfreqa = gtk.Adjustment(1, 1, 64, 1)
        self.jpgfreq = gtk.SpinButton(jpgfreqa)
        self.jpgfreq.set_sensitive(False)
        jpgsubl = gtk.Label(_("Subsampling:"))
        jpgsubls = gtk.ListStore(gobject.TYPE_STRING)
        jpgsubos = [ _("1x1,1x1,1x1 (best quality)"), _("2x1,1x1,1x1 (4:2:2)"), _("1x2,1x1,1x1"), _("2x2,1x1,1x1 (smallest file)") ]
        for jpgsubo in jpgsubos:
            jpgsubls.append([jpgsubo])
        jpgsubc = gtk.CellRendererText()
        self.jpgsub = gtk.ComboBox(jpgsubls)
        self.jpgsub.pack_start(jpgsubc, True)
        self.jpgsub.add_attribute(jpgsubc, 'text', 0)
        self.jpgsub.set_active(3)
        jpgdctl = gtk.Label(_("DCT Method:"))
        jpgdctls = gtk.ListStore(gobject.TYPE_STRING)
        jpgdctos = [ _("Float Integer"), _("Integer"), _("Floating-Point") ]
        for jpgdcto in jpgdctos:
            jpgdctls.append([jpgdcto])
        jpgdctc = gtk.CellRendererText()
        self.jpgdct = gtk.ComboBox(jpgdctls)
        self.jpgdct.pack_start(jpgdctc, True)
        self.jpgdct.add_attribute(jpgdctc, 'text', 0)
        self.jpgdct.set_active(1)
        jpgcommentl = gtk.Label(_("Comment:"))
        self.jpgcomment = gtk.Entry(256)
        jpgt.attach(jpgqualityl, 0,1,0,1)
        jpgt.attach(self.jpgquality, 1,2,0,1)
        jpgt.attach(jpgsmoothingl, 0,1,1,2)
        jpgt.attach(self.jpgsmoothing, 1,2,1,2)
        jpgt.attach(self.jpgoptimize, 0,2,2,3)
        jpgt.attach(self.jpgprogressive, 0,2,3,4)
        jpgt.attach(self.jpgrestart, 0,2,4,5)
        jpgt.attach(jpgfreql, 0,1,5,6)
        jpgt.attach(self.jpgfreq, 1,2,5,6)
        jpgt.attach(jpgsubl, 0,1,6,7)
        jpgt.attach(self.jpgsub, 1,2,6,7)
        jpgt.attach(jpgdctl, 0,1,7,8)
        jpgt.attach(self.jpgdct, 1,2,7,8)
        jpgt.attach(jpgcommentl, 0,1,8,9)
        jpgt.attach(self.jpgcomment, 1,2,8,9)
        return jpgt

    def jpgrestartchecked(self, restartcheckbox):
        # JPG restart has been checked.
        if restartcheckbox.get_active():
            self.jpgfreq.set_sensitive(True)
        else:
            self.jpgfreq.set_sensitive(False)

    def ora(self):
        # ORA save options GUI.
        orat = gtk.Table(1,2)
        self.oraflatten = gtk.CheckButton(_("Flatten"))
        self.oraflatten.set_active(False)
        orat.attach(self.oraflatten, 0,2,0,1)
        return orat

    def psd(self):
        # PSD save options GUI.
        psdt = gtk.Table(2,2)
        self.psdflatten = gtk.CheckButton(_("Flatten"))
        self.psdflatten.set_active(False)
        psdframe = gtk.Frame()
        psdframe.set_shadow_type(gtk.SHADOW_NONE)
        psdframel = gtk.Label(_("<b>Compression</b>"))
        psdframel.set_use_markup(True)
        psdframe.set_label_widget(psdframel)
        psdvbox = gtk.VBox(False, 5)
        psdframe.add(psdvbox)
        self.psdnone = gtk.RadioButton(None, _("None"))
        psdvbox.pack_start(self.psdnone)
        self.psdlzw = gtk.RadioButton(self.psdnone, _("LZW"))
        psdvbox.pack_start(self.psdlzw)
        self.psdpackbits = gtk.RadioButton(self.psdnone, _("Pack Bits"))
        psdvbox.pack_start(self.psdpackbits)
        psdt.attach(self.psdflatten, 0,2,0,1)
        psdt.attach(psdframe, 0,2,1,2)
        return psdt

    def png(self):
        # PNG save options GUI.
        pngt = gtk.Table(8,2)
        self.pnginterlacing = gtk.CheckButton(_("Interlacing (Adam7)"))
        self.pngbgcolor = gtk.CheckButton(_("Save background color"))
        self.pnggamma = gtk.CheckButton(_("Save gamma"))
        self.pnglayeroffset = gtk.CheckButton(_("Save layer offset"))
        self.pngresolution = gtk.CheckButton(_("Save resolution"))
        self.pngresolution.set_active(True)
        self.pngcreationtime = gtk.CheckButton(_("Save creation time"))
        self.pngcreationtime.set_active(True)
        self.pngcoloroftransp = gtk.CheckButton(_("Save color values from transparent pixels"))
        pngcompressl = gtk.Label(_("Compression level:"))
        pngcompressa = gtk.Adjustment(9, 0, 9, 1)
        self.pngcompress = gtk.HScale(pngcompressa)
        self.pngcompress.set_digits(0)
        pngt.attach(self.pnginterlacing, 0,2,0,1)
        pngt.attach(self.pngbgcolor, 0,2,1,2)
        pngt.attach(self.pnggamma, 0,2,2,3)
        pngt.attach(self.pnglayeroffset, 0,2,3,4)
        pngt.attach(self.pngresolution, 0,2,4,5)
        pngt.attach(self.pngcreationtime, 0,2,5,6)
        pngt.attach(self.pngcoloroftransp, 0,2,6,7)
        pngt.attach(pngcompressl, 0,1,7,8)
        pngt.attach(self.pngcompress, 1,2,7,8)
        return pngt

    def tif(self):
        # TIF save options GUI.
        tift = gtk.Table(2,1)
        # Save color
        tifframe = gtk.Frame()
        tifframe.set_shadow_type(gtk.SHADOW_NONE)
        tifframel = gtk.Label(_("<b>Compression</b>"))
        tifframel.set_use_markup(True)
        tifframe.set_label_widget(tifframel)
        tifvbox = gtk.VBox(False, 5)
        tifframe.add(tifvbox)
        self.tifnone = gtk.RadioButton(None, _("None"))
        tifvbox.pack_start(self.tifnone)
        self.tiflzw = gtk.RadioButton(self.tifnone, _("LZW"))
        tifvbox.pack_start(self.tiflzw)
        self.tifpackbits = gtk.RadioButton(self.tifnone, _("Pack Bits"))
        tifvbox.pack_start(self.tifpackbits)
        self.tifdeflate = gtk.RadioButton(self.tifnone, _("Deflate"))
        tifvbox.pack_start(self.tifdeflate)
        self.tifjpeg = gtk.RadioButton(self.tifnone, _("JPEG"))
        tifvbox.pack_start(self.tifjpeg)
        self.tifnone.set_active(True)
        self.tifcoloroftransp = gtk.CheckButton(_("Save color values from transparent pixels"))
        tift.attach(tifframe, 0,2,0,1)
        tift.attach(self.tifcoloroftransp, 0,2,1,2)
        return tift
        
    def export(self, button):
        # Pass self to Book, and tell it to export.
        self.tabs.set_sensitive(False)
        self.doneb.set_sensitive(False)
        self.progress.set_fraction(0)
        self.progress.set_text("")
        outfolder = os.path.join(self.destbutton.get_filename(), self.main.book.bookname)
        if os.path.isdir(outfolder):
            # TRANSLATORS: %s is a previously exported book
            overwrite = gtk.MessageDialog(self.main, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _('"%s" exists, do you want to overwrite it?') % (outfolder))
            response = overwrite.run()
            if response == gtk.RESPONSE_YES:
                overwrite.hide()
                self.progress.show()
                self.main.book.export_book(self)
                self.destroy()
            else:
                self.tabs.set_sensitive(True)
                self.doneb.set_sensitive(True)
            overwrite.destroy()
        else:
            self.progress.show()
            self.tabs.set_sensitive(False)
            self.doneb.set_sensitive(False)
            self.main.book.export_book(self)
            self.destroy()

    def close(self, button):
        # Close the export window.
        self.destroy()

    def __del__(self):
        # Destructor makes sure main window is sensitive.
        self.main.set_sensitive(True)


class Book():
    # Stores and manages the data for the book.
    def __init__(self, main):
        # Defines basic variables to store.
        # pagestore columns = pagename, thumb Pixbuf, thumb path
        self.pagestore = gtk.ListStore(str, gtk.gdk.Pixbuf, str)
        self.main = main     # Main windows.
        self.bookfile = ""   # The *.book for this book.
        self.bookname = ""   # The name of the book.
        self.pagepath = ""   # Path to the pages subfolder.
        self.trashpath = ""  # Path to trash folder.
        self.thumbpath = ""  # Path to the thumbs folder.
        self.selected = 0    # Index of the currently selected page, -1 if none.
        self.thumbsize = 256 # Defautl thumbnail size.
        self.thumbwidth = 256
        self.aspect = 1      # The aspect ratio of the page (a width 7 and height 10 page, is 0.7 aspect)

    def make_book(self, dest, name, w, h, r, color, fill, top, bottom, sides, bleed):
        # Build the files and folders needed for the book.
        width = int(w)
        height = int(h)
        resolution = int(r)
        if os.path.isdir(dest):
            if name:
                # Make folder dest/name
                fullpath = os.path.join(dest, name)
                if not os.path.isdir(fullpath):
                    os.makedirs(fullpath)
                # Make file dest/name/name.book
                metadata = json.dumps({ 'pages':[ 'Template.xcf' ] }, indent=4)
                bookfile = open(os.path.join(fullpath,name+".book"), "w")
                bookfile.write(metadata)
                bookfile.close()
                # Make folder dest/name/Pages and Trash
                if not os.path.isdir(os.path.join(fullpath,"pages")):
                    os.makedirs(os.path.join(fullpath,"pages"))
                if not os.path.isdir(os.path.join(fullpath,"trash")):
                    os.makedirs(os.path.join(fullpath,"trash"))
                if not os.path.isdir(os.path.join(fullpath,"thumbs")):
                    os.makedirs(os.path.join(fullpath,"thumbs"))
                # Make file dest/name/Template.xcf
                img = pdb.gimp_image_new(width, height, color)
                pdb.gimp_image_set_resolution(img, resolution, resolution)
                if color == 0:
                    bglayer = gimp.Layer(img, "Background", width, height, RGBA_IMAGE, 100, NORMAL_MODE)
                else:
                    bglayer = gimp.Layer(img, "Background", width, height, GRAYA_IMAGE, 100, NORMAL_MODE)
                if fill == 0:
                    bglayer.fill(FOREGROUND_FILL)
                elif fill == 1:
                    bglayer.fill(BACKGROUND_FILL)
                elif fill == 2:
                    bglayer.fill(WHITE_FILL)
                elif fill == 3:
                    bglayer.fill(TRANSPARENT_FILL)
                img.add_layer(bglayer, 0)
                # Add guides
                if top > 0 or bottom > 0 or sides > 0:
                    pt = top + bleed
                    pl = sides + bleed
                    pr = width - sides - bleed
                    pb = height - bottom - bleed
                    self.add_guide(_("Margins"), img, pt, pl, pr, pb)
                if bleed > 0:
                    pt = bleed
                    pl = bleed
                    pr = width - bleed
                    pb = height - bleed
                    self.add_guide(_("Bleed"), img,  pt, pl, pr, pb)
                pdb.gimp_xcf_save(0, img, None, os.path.join(fullpath, "pages", "Template.xcf") , "Template.xcf")

                # Load the newly created book.
                self.load_book(os.path.join(fullpath, name+".book"), self.main)
                return True
            else:
                show_error_msg(_("Name was left empty"))
        else:
            show_error_msg(_("Destination does not exist."))

    def add_guide(self, name, img,  pt, pl, pr, pb):
        coords = [
            pl,pt,pl,pt,pl,pt,
            pr,pt,pr,pt,pr,pt,
            pr,pb,pr,pb,pr,pb,
            pl,pb,pl,pb,pl,pb,
            pl,pt,pl,pt,pl,pt ]
        drw = pdb.gimp_image_get_active_layer(img)
        vector = pdb.gimp_vectors_new(img, name)
        pdb.gimp_vectors_set_visible(vector, True)
        pdb.gimp_image_add_vectors(img, vector, 0)
        pdb.gimp_vectors_stroke_new_from_points(vector, 0, 30, coords, True)


    def load_book(self, bookfile, mainwin):
        # Loads a selected book.
        if os.path.exists(bookfile):
            self.bookfile = bookfile
            self.bookname = os.path.splitext(os.path.basename(self.bookfile))[0]
            bookpath = os.path.dirname(self.bookfile)
            self.pagepath = os.path.join(bookpath, "pages")
            self.trashpath = os.path.join(bookpath, "trash")
            self.thumbpath = os.path.join(bookpath, "thumbs")
            self.thumbsize = 256
            # Load the pages.
            f = open(self.bookfile, "r")
            metatext = f.read()
            metadata = json.loads(metatext)
            f.close()
            if 'storyboardmode' in metadata:
                if metadata['storyboardmode']:
                    self.main.storyboardm.set_active(1)
                    self.main.storyboardmode = 1
                    self.main.thumbs.set_columns(0)
                else:
                    self.main.storyboardm.set_active(0)
                    self.main.storyboardmode = 1
                    self.main.thumbs.set_columns(2)
            if 'thumbsize' in metadata:
                self.thumbsize = metadata['thumbsize']
            progressstep = float(1.0 / len(metadata['pages']))
            progress = 0.0
            for p in metadata['pages']:
                mainwin.progress.show()
                # TRANSLATORS: %s is the name of a page being loaded
                mainwin.progress.set_text(_("Loading %s") % (p))
                while gtk.events_pending():
                    gtk.main_iteration()
                # Create a page object, and add to a list.
                thumb = Thumb(os.path.join(self.pagepath, p), self.thumbsize, self.main)
                self.pagestore.append((p, thumb.thumbpix, thumb.path))
                progress = progress + progressstep
                if progress > 1.0:
                    progress = 1.0
                mainwin.progress.set_fraction(progress)
                while gtk.events_pending():
                    gtk.main_iteration()
            self.pagestore.connect("row-deleted", self.row_deleted)
            self.pagestore.connect("row-inserted", self.row_inserted)
            self.pagestore.connect("row-changed", self.row_changed)
            mainwin.progress.hide()
            return True

    def row_deleted(self, pagestore, destination_index):
        self.save()

    def row_inserted(self, pagestore, destination_index, tree_iter):
        self.save()

    def row_changed(self, pagestore, destination_index, tree_iter):
        self.save()

    def open_page(self, iconview, number):
        # Open the page the user clicked in GIMP.
        number = number[0]
        pagetoopen = os.path.join(self.pagepath, self.pagestore[number][0])
        img = pdb.gimp_file_load(pagetoopen, pagetoopen)
        img.clean_all()
        gimp.Display(img)

    def save(self):
        # Dump the pagestore to the *.book file, saving the book.
        metadata = []
        for p in self.pagestore:
            if p[0]:
                metadata.append(p[0])
        savetofile = json.dumps({ 'storyboardmode': self.main.storyboardmode, 'thumbsize': self.thumbsize, 'pages': metadata }, indent=4)
        bookfile = open(self.bookfile, "w")
        bookfile.write(savetofile)
        bookfile.close()

    def add_page(self, p, dest):
        # Copy the template to a new page.
        try:
            p = p+'.xcf'
            unique = True
            for a in self.pagestore:
                if a[0] == p:
                    unique = False
            if unique:
                template = os.path.join(self.pagepath, self.pagestore[0][0])
                shutil.copy(template, os.path.join(self.pagepath, p))
                thumb = Thumb(os.path.join(self.pagepath, p), self.thumbsize, self.main)
                self.pagestore.insert(dest, ( p, thumb.thumbpix, thumb.path))
                return True
            else:
                show_error_msg(_("Page names must be unique"))
        except Exception, err:
            show_error_msg(err)

    def import_page(self, plist, dest):
        # Import a page from an external source.
        # TODO! Add support for format specific import settings, such as svg and pdf resolution.
        plist.sort(reverse=True)
        for p in plist:
            name,ext = os.path.splitext(os.path.basename(p))
            name = name+'.xcf'
            unique = True
            for a in  self.pagestore:
                if a[0] == name:
                    unique = False
            if unique:
                img = pdb.gimp_file_load(p, p)
                pdb.gimp_xcf_save(0, img, None, os.path.join(self.pagepath, name) , name)
                thumb = Thumb(os.path.join(self.pagepath, p), self.thumbsize, self.main)
                self.pagestore.insert(dest, (name, thumb.thumbpix, thumb.path))
            else:
                show_error_msg(_("Page name is not unique."))


    def open_page(self, iconview, number):
        # Open the page the user clicked in GIMP.
        number = number[0]
        pagetoopen = os.path.join(self.pagepath, self.pagestore[number][0])
        img = pdb.gimp_file_load(pagetoopen, pagetoopen)
        img.clean_all()
        gimp.Display(img)

    def dupli_page(self, p, dest):
        # Copy the template to a new page.
        try:
            p = p+'.xcf'
            unique = True
            for a in self.pagestore:
                if a[0] == p:
                    unique = False
            if unique:
                template = os.path.join(self.pagepath, self.pagestore[0][0])
                src = os.path.join(self.pagepath, self.pagestore[dest][0])
                shutil.copy(src, os.path.join(self.pagepath, p))
                thumb = Thumb(os.path.join(self.pagepath, p), self.thumbsize, self.main)
                self.pagestore.insert(dest, ( p, thumb.thumbpix, thumb.path))
                return True
            else:
                show_error_msg(_("Page names must be unique"))
        except Exception, err:
            show_error_msg(err)

    def rename_page(self, p):
        # Rename a page.
        p = p+".xcf"
        unique = True
        for a in self.pagestore:
            if a[0] == p:
                unique = False
            if unique:
                try:
                    oldthumb = self.pagestore[self.selected][0]
                    shutil.move(os.path.join(self.pagepath, self.pagestore[self.selected][0]), os.path.join(self.pagepath, p))
                    thumb = Thumb(os.path.join(self.pagepath,p), self.thumbsize, self.main)
                    self.pagestore[self.selected] = ((p, thumb.thumbpix, thumb.path))
                    self.delete_thumb(oldthumb)
                    return True
                except Exception, err:
                    show_error_msg(err)
            else:
                show_error_msg(_("Page names must be unique"))
            
    def delete_page(self):
        # Delete the selected page.
        try:
            p = self.pagestore[self.selected][0]
            shutil.move(os.path.join(self.pagepath, p), os.path.join(self.trashpath,strftime("%Y%m%d_%H%M%S_")+p))
            piter = self.pagestore.get_iter_from_string(str(self.selected))
            self.pagestore.remove(piter)
            self.delete_thumb(p)
            return True
        except Exception, err:
            show_error_msg(err)

    def delete_thumb(self, pagename):
        # Delete all sizes of a thumbnail by name
        for i in [ 32, 64, 128, 256, 512, 1024 ]:
            oldthumb = os.path.join(self.thumbpath, str(i), pagename+".png")
            if os.path.isfile(oldthumb):
                os.remove(oldthumb)

    def get_template_size(self):
        # Return the size of the template in pixels x,y
        template = os.path.join(self.pagepath, self.pagestore[0][0])
        img = pdb.gimp_file_load(template, template)
        return img.width, img.height

    def format_index_to_extension(self, formati):
        # Convert the format index to an extension.
        if formati == 0: # GIF
            return "gif"
        elif formati == 1: # XCF
            return "xcf"
        elif formati == 2: # JPEG
            return "jpg"
        elif formati == 3: # ORA
            return "ora"
        elif formati == 4: # PSD
            return "psd"
        elif formati == 5: # PNG
            return "png"
        elif formati == 6: # TIFF
            return "tif"
        else:
            show_error_msg(_("Format index out of range"))


    def export_book(self, expwin):
        # Export the entire book.
        outfolder = os.path.join(expwin.destbutton.get_filename(), self.bookname)
        namei = expwin.namem.get_active() # Index of type of name to use, book, page, number or custom.
        if not os.path.isdir(outfolder):
            os.makedirs(outfolder)
        # Page number padding needed.
        pagecount = len(self.pagestore)
        padding = 1
        if pagecount > 999:  # Damn...you've made a 1000+ page long comic book....nice work.
            padding = 4
        elif pagecount > 99:
            padding = 3
        elif pagecount > 9:
            padding = 2
        progress = 0.0
        progressstep = float(1.0 / (expwin.rangeto.get_value() - expwin.rangefrom.get_value() + 1))
        # Find file extension.
        ext = self.format_index_to_extension(expwin.formatm.get_active())
        # Loop through pages
        for i,p in enumerate(self.pagestore):
            if i >= expwin.rangefrom.get_value() and i <= expwin.rangeto.get_value():
                # Figure out the page name.
                original = os.path.join(self.pagepath, p[0])
                # TRANSLATORS: %s is the name of the page being exported
                expwin.progress.set_text(_("Exporting %s") % (p[0]))
                while gtk.events_pending():
                    gtk.main_iteration()
                pagenr = str(i).zfill(padding)
                name=""
                if namei == 0: # Book Name
                    name = pagenr+"_"+self.bookname+"."+ext
                elif namei == 1: # Page Names
                    name = pagenr+"_"+os.path.splitext(p[0])[0]+"."+ext
                elif namei == 2: # Page Number
                    name = pagenr+"."+ext
                elif namei == 3: # Custom Name
                    name = pagenr+"_"+expwin.namee.get_text()+"."+ext
                fullname = os.path.join(outfolder, name)
                img = pdb.gimp_file_load(original, original)
                # Show and hide tagged layers.
                hidetags = expwin.taghide.get_text().split(',')
                showtags = expwin.tagshow.get_text().split(',')
                regex = re.compile("\[(.*?)\]")
                for i in range(pdb.gimp_image_get_layers(img)[0]):
                    # Show and hide layers. Hide wins over show, if layer has two matching tags.
                    layername = pdb.gimp_layer_get_name(img.layers[i])
                    layertags = regex.findall(layername)
                    if set(hidetags) & set(layertags):
                        pdb.gimp_layer_set_visible(img.layers[i],False)
                    elif set(showtags) & set(layertags):
                        pdb.gimp_layer_set_visible(img.layers[i], True)
                    elif expwin.tagunm.get_active() == 1: # Show all by default.
                        pdb.gimp_layer_set_visible(img.layers[i], True)
                    elif expwin.tagunm.get_active() == 2: # Hide all by default.
                        pdb.gimp_layer_set_visible(img.layers[i], False)
                # Process image.
                if ext == "xcf" and not expwin.xcfflatten.get_active():
                    pass
                elif ext == "ora" and not expwin.oraflatten.get_active():
                    pass
                elif ext == "psd" and not expwin.psdflatten.get_active():
                    pass
                else:
                    img.flatten()
                drw = pdb.gimp_image_get_active_layer(img)
                # Add/Remove margins.
                # TODO! Add support or percentile margins...maybe.
                top = expwin.margtop.get_value()
                bottom = expwin.margbot.get_value()
                inner = expwin.marginner.get_value()
                outer = expwin.margouter.get_value()
                w = inner + outer + img.width
                h = top + bottom + img.height
                x = 0
                y = top
                if i%2 == 0: # Left hand page.
                    x = outer
                else: # Right hand page.
                    x = inner
                if not top == 0 or not bottom == 0 or not inner == 0 or not outer == 0:
                    if expwin.margcolm.get_active() == 1: # Black
                        pdb.gimp_context_set_background((0,0,0))
                    elif expwin.margcolm.get_active() == 2: # White
                        pdb.gimp_context_set_background((255,255,255))
                    elif expwin.margcolm.get_active() == 3: # Custom color
                        color = expwin.margcol.get_color()
                        pdb.gimp_context_set_background((color.red/257, color.green/257, color.blue/257))
                    pdb.gimp_image_resize(img, w, h, x, y)
                    pdb.gimp_layer_resize_to_image_size(drw)
                # Scale the image.
                nw = 0 
                nh = 0
                if expwin.scaletype.get_active(): # Pixel
                    nw = int(expwin.scalew.get_value())
                    nh = int(expwin.scaleh.get_value())
                else: # Percent
                    nw = int((expwin.scalew.get_value() / 100) * img.width)
                    nh = int((expwin.scaleh.get_value() / 100) * img.height)
                if not nw == img.width or not nh == img.height:
                    pdb.gimp_image_scale_full(img, nw, nh, expwin.interp.get_active())
                # Save the image.
                if ext == "gif":
                    # Convert to grayscale
                    if expwin.gifgrayscale.get_active():
                        pdb.gimp_image_convert_grayscale(img)
                    else:
                        # TODO! Maybe support custom palettes and other GIF options...but not for now.
                        pdb.gimp_image_convert_indexed(img,
                                                       expwin.gifdith.get_active(),
                                                       0,
                                                       expwin.gifcolors.get_value(),
                                                       False,
                                                       False,
                                                       "")
                        pdb.file_gif_save(img, drw, fullname, name,
                                          expwin.gifinterlace.get_active(),
                                          0,0,0)
                elif ext == "xcf":
                    pdb.gimp_file_save(img, drw, fullname, name)
                elif ext == "jpg":
                    quality = float(expwin.jpgquality.get_value() / 100)
                    restartfreq = 0
                    if expwin.jpgrestart.get_active():
                        restartfreq = expwin.jpgfreq.get_value()
                    pdb.file_jpeg_save(img, drw, fullname, name, quality,
                                       expwin.jpgsmoothing.get_value(),
                                       expwin.jpgoptimize.get_active(),
                                       expwin.jpgprogressive.get_active(),
                                       expwin.jpgcomment.get_text(),
                                       expwin.jpgsub.get_active(),
                                       0,
                                       restartfreq,
                                       expwin.jpgdct.get_active())
                elif ext == "ora":
                    pdb.file_openraster_save(img, drw, fullname, name)
                elif ext == "psd":
                    compress = 0
                    if expwin.psdlzw.get_active():
                        compress = 1
                    elif expwin.psdpackbits.get_active():
                        compress = 2
                    pdb.file_psd_save(img, drw, fullname, name, compress, 0)
                elif ext == "png":
                    pdb.file_png_save2(img, drw, fullname, name,
                                       expwin.pnginterlacing.get_active(),
                                       expwin.pngcompress.get_value(),
                                       expwin.pngbgcolor.get_active(),
                                       expwin.pnggamma.get_active(),
                                       expwin.pnglayeroffset.get_active(),
                                       expwin.pngresolution.get_active(),
                                       expwin.pngcreationtime.get_active(),
                                       1,
                                       expwin.pngcoloroftransp.get_active())
                elif ext == "tif":
                    compress = 0
                    if expwin.tiflzw.get_active():
                        compress = 1
                    elif expwin.tifpackbits.get_active():
                        compress = 2
                    elif expwin.tifdeflate.get_active():
                        compress = 3
                    elif expwin.tifjpeg.get_active():
                        compress = 4
                    pdb.file_tiff_save2(img, drw, fullname, name, compress, expwin.tifcoloroftransp.get_active())
                pdb.gimp_image_delete(img)
                progress = progress + progressstep
                expwin.progress.set_fraction(progress)
                while gtk.events_pending():
                    gtk.main_iteration()


    def update_thumbs(self):
        # Update all thumbnails that have changed.
        progress = 0.0
        self.main.progress.set_fraction(progress)
        self.main.progress.set_text("")
        pagecount = len(self.pagestore)
        for i,p in enumerate(self.pagestore):
            if p[0]:
                self.main.progress.set_text("Generating thumbnail for %s" % p[0])
                thumb = Thumb(os.path.join(self.pagepath,p[0]), self.thumbsize, self.main)
                self.thumbwidth = thumb.thumbpix.get_width()
                self.pagestore[i] = ((p[0], thumb.thumbpix, thumb.path))
            progress = float(i) / pagecount
            self.main.progress.set_fraction(progress)
        self.main.progress.hide()
        self.main.progress.set_text("")
        self.main.progress.set_fraction(0.0)


class Main(gtk.Window):
    # Builds a GTK windows for managing the pages of a book.
    def __init__ (self):
        window = super(Main, self).__init__()
        self.set_title(_("GIMP Book"))
        self.set_default_size(570, 400)
        self.set_position(gtk.WIN_POS_CENTER)
        self.loaded = False  # If there is a book loaded in the interface.
        self.connect('notify::is-active', self.update_thumbs)
        self.set_icon_name('gimp')
        self.storyboardmode = 0

        # Main menu
        mb = gtk.MenuBar()

        # File menu
        filemenu = gtk.Menu()
        i_file = gtk.MenuItem(_("File"))
        i_file.set_submenu(filemenu)
        
        agr = gtk.AccelGroup()
        self.add_accel_group(agr)

        file_new = gtk.ImageMenuItem(gtk.STOCK_NEW, agr)
        file_new.set_label(_("New Book..."))
        # TRANSLATORS: Do NOT translate <Control>. You can change N, if you want to use a different keyboard shortcut.
        # Same goes for all <Control> entires in this document.
        key, mod = gtk.accelerator_parse(_("<Control>N"))
        file_new.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_new.connect("activate", self.new_book)
        filemenu.append(file_new)

        file_open = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        file_open.set_label(_("Open Book..."))
        key, mod = gtk.accelerator_parse(_("<Control>O"))
        file_open.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_open.connect("activate", self.open_book)
        filemenu.append(file_open)

        sep1 = gtk.SeparatorMenuItem()
        filemenu.append(sep1)

        self.file_export = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        self.file_export.set_label(_("Export Book..."))
        key, mod = gtk.accelerator_parse(_("<Control>E"))
        self.file_export.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.file_export.connect("activate", self.export_win)
        self.file_export.set_sensitive(False)
        filemenu.append(self.file_export)

        sep2 = gtk.SeparatorMenuItem()
        filemenu.append(sep2)

        file_close = gtk.ImageMenuItem(gtk.STOCK_CLOSE, agr)
        file_close.set_label(_("Close Book..."))
        key, mod = gtk.accelerator_parse(_("<Control>W"))
        file_close.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_close.connect("activate", gtk.main_quit)
        filemenu.append(file_close)

        # View Menu
        self.viewmenu = gtk.Menu()
        i_view = gtk.MenuItem(_("View"))
        i_view.set_submenu(self.viewmenu)

        toolbar = gtk.CheckMenuItem()
        toolbar.set_label(_("Show Toolbar"))
        toolbar.set_active(True)
        toolbar.connect("activate", self.toggle_toolbar)
        self.viewmenu.append(toolbar)

        viewsep = gtk.SeparatorMenuItem()
        self.viewmenu.append(viewsep)

        self.storyboardm = gtk.CheckMenuItem()
        self.storyboardm.set_label(_("Storyboard Mode"))
        self.storyboardm.set_active(False)
        self.storyboardm.set_sensitive(False)
        self.storyboardm.connect("activate", self.toggle_storyboard_mode)
        self.viewmenu.append(self.storyboardm)

        self.zoomoutm = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT, agr)
        self.zoomoutm.set_label(_("Zoom Out"))
        key, mod = gtk.accelerator_parse(_("<Control>minus"))
        self.zoomoutm.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.zoomoutm.set_sensitive(False)
        self.zoomoutm.connect("activate", self.zoomout)
        self.viewmenu.append(self.zoomoutm)

        self.zoominm = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN, agr)
        self.zoominm.set_label(_("Zoom In"))
        key, mod = gtk.accelerator_parse(_("<Control>plus"))
        self.zoominm.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.zoominm.set_sensitive(False)
        self.zoominm.connect("activate", self.zoomin)
        self.viewmenu.append(self.zoominm)

        #self.direction = gtk.CheckMenuItem()
        #self.direction.set_label("Read Left to Right")
        #self.direction.set_active(True)
        #self.direction.connect("activate", self.toggle_reading_direction)
        #self.viewmenu.append(self.direction)

        # Pages Menu
        self.pagemenu = gtk.Menu()
        i_page = gtk.MenuItem(_("Pages"))
        i_page.set_submenu(self.pagemenu)

        self.openpage = gtk.MenuItem()
        self.openpage.set_sensitive(False)
        self.openpage.set_label(_("Open"))
        key, mod = gtk.accelerator_parse("Return")
        self.openpage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.openpage.connect("activate", self.open_page)
        self.pagemenu.append(self.openpage)
        self.openpage.show()

        self.addpage = gtk.MenuItem()
        self.addpage.set_sensitive(False)
        self.addpage.set_label(_("Add"))
        key, mod = gtk.accelerator_parse(_("<Control>A"))
        self.addpage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.addpage.connect("activate", self.ask_add_page)
        self.pagemenu.append(self.addpage)
        self.addpage.show()

        self.importpage = gtk.MenuItem()
        self.importpage.set_sensitive(False)
        self.importpage.set_label(_("Import"))
        key, mod = gtk.accelerator_parse(_("<Control>I"))
        self.importpage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.importpage.connect("activate", self.ask_import_page)
        self.pagemenu.append(self.importpage)
        self.importpage.show()

        self.duplipage = gtk.MenuItem()
        self.duplipage.set_sensitive(False)
        self.duplipage.set_label(_("Duplicate"))
        key, mod = gtk.accelerator_parse(_("<Control>D"))
        self.duplipage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.duplipage.connect("activate", self.ask_dupli_page)
        self.pagemenu.append(self.duplipage)
        self.duplipage.show()

        self.renamepage = gtk.MenuItem()
        self.renamepage.set_sensitive(False)
        self.renamepage.set_label(_("Rename"))
        key, mod = gtk.accelerator_parse(_("<Control>R"))
        self.renamepage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.renamepage.connect("activate", self.ask_rename_page)
        self.pagemenu.append(self.renamepage)
        self.renamepage.show()

        self.deletepage = gtk.MenuItem()
        self.deletepage.set_sensitive(False)
        self.deletepage.set_label(_("Delete"))
        key, mod = gtk.accelerator_parse("Delete")
        self.deletepage.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.deletepage.connect("activate", self.ask_delete_page)
        self.pagemenu.append(self.deletepage)
        self.deletepage.show()

        # Help Menu
        self.helpmenu = gtk.Menu()
        i_help = gtk.MenuItem(_("Help"))
        i_help.set_submenu(self.helpmenu)
        
        onlinehelp = gtk.MenuItem()
        self.urlbutton = gtk.LinkButton(website, _("Online Help"))
        onlinehelp.add(self.urlbutton)
        onlinehelp.connect("activate", self.online_help)
        self.helpmenu.append(onlinehelp)

        helpsep = gtk.SeparatorMenuItem()
        self.helpmenu.append(helpsep)

        about = gtk.MenuItem()
        about.set_label(_("About Gimp Book"))
        about.connect("activate", self.about)
        self.helpmenu.append(about)

        mb.append(i_file)
        mb.append(i_view)
        mb.append(i_page)
        mb.append(i_help)


        # Main toolbar
        self.icondir = os.path.join(gimp.directory, 'plug-ins', 'icons')
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        self.add_icon = gtk.Image()
        self.add_icon.set_from_file(os.path.join(self.icondir, 'add.png'))
        self.add_icon.show()
        self.add_page = gtk.ToolButton(self.add_icon)
        self.add_page.connect("clicked", self.ask_add_page)
        self.add_page.set_sensitive(False)
        self.add_page.set_tooltip_text(_("Add a new page."))

        self.imp_icon = gtk.Image()
        self.imp_icon.set_from_file(os.path.join(self.icondir, 'import.png'))
        self.imp_icon.show()
        self.imp_page = gtk.ToolButton(self.imp_icon)
        self.imp_page.connect("clicked", self.ask_import_page)
        self.imp_page.set_sensitive(False)
        self.imp_page.set_tooltip_text(_("Import page(s)"))

        self.dupli_icon = gtk.Image()
        self.dupli_icon.set_from_file(os.path.join(self.icondir, 'duplicate.png'))
        self.dupli_icon.show()
        self.dupli_page = gtk.ToolButton(self.dupli_icon)
        self.dupli_page.connect("clicked", self.ask_dupli_page)
        self.dupli_page.set_sensitive(False)
        self.dupli_page.set_tooltip_text(_("Duplicate the selected page."))

        self.ren_icon = gtk.Image()
        self.ren_icon.set_from_file(os.path.join(self.icondir, 'rename.png'))
        self.ren_icon.show()
        self.ren_page = gtk.ToolButton(self.ren_icon)
        self.ren_page.connect("clicked", self.ask_rename_page)
        self.ren_page.set_sensitive(False)
        self.ren_page.set_tooltip_text(_("Rename the selected page."))

        self.del_icon = gtk.Image()
        self.del_icon.set_from_file(os.path.join(self.icondir, 'delete.png'))
        self.del_icon.show()
        self.del_page = gtk.ToolButton(self.del_icon)
        self.del_page.connect("clicked", self.ask_delete_page)
        self.del_page.set_sensitive(False)
        self.del_page.set_tooltip_text(_("Delete the selected page."))

        self.toolbar.insert(self.add_page, 0)
        self.toolbar.insert(self.imp_page, 1)
        self.toolbar.insert(self.dupli_page, 2)
        self.toolbar.insert(self.ren_page, 3)
        self.toolbar.insert(self.del_page, 4)

        self.vbox = gtk.VBox(False, 2)
        self.vbox.pack_start(mb, False, False, 0)
        self.vbox.pack_start(self.toolbar, False, False, 0)

        self.thumbs = gtk.IconView()
        self.thumbs.set_text_column(0)
        self.thumbs.set_pixbuf_column(1)
        self.thumbs.set_reorderable(True)
        self.thumbs.set_columns(2)
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.thumbs)
        self.vbox.pack_start(self.scroll, True, True, 0)

        self.progress = gtk.ProgressBar()
        self.vbox.pack_end(self.progress, False, False, 0)

        self.add(self.vbox)
        self.connect("destroy", gtk.main_quit)
        self.show_all()
        self.progress.hide()
        return window    

    def online_help(self, widget):
        # Link to Gimp Registry page for this book.
        self.urlbutton.clicked()
    
    def about(self, widget):
        # About dialog.
        about = gtk.AboutDialog()
        about.set_name(plugin)
        about.set_version(version)
        about.set_authors(author)
        about.set_license(license)
        about.set_copyright(copyright)
        about.set_website(website)
        about.set_website_label(_("Visit Gimp Book at ragnarb.com"))
        response = about.run()
        if response == gtk.RESPONSE_CANCEL:
            about.destroy()

    def toggle_toolbar(self, widget):
        # Toggle the visibility of the toolbar.
        if widget.active:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def toggle_reading_direction(self, widget):
        # TODO! In development, not fully working.
        # Toggle reading direction between left-to-right and right-to-left.
        pagecount = len(self.book.pagestore)
        order = []
        show_error_msg(pagecount)
        for r in range(0, pagecount):
            show_error_msg(r)
            if r%2 == 0: # Even
                if r == pagecount-1:
                    order.append(r)
                else:
                    order.append(r+1)
            else: # Odd
                order.append(r-1)
        show_error_msg(order)
        self.book.pagestore.reorder(order)

    def update_thumbs(self, widget, arg):
        # Tell Book to update the thumbnails on window receiving focus.
        if self.is_active() and self.loaded:
            self.book.update_thumbs()
            # TODO! Right-to-left order of icons. Not working.
            #self.thumbs.scroll_to_path(':1', True, 0.0, 1.0)

    def new_book(self, widget):
        # Helper for opening up the New Book window.
        nb = NewBookWin(self)

    def open_book(self, widget):
        # Interface for opening an existing book.
        o = gtk.FileChooserDialog(_("Open Book"), self, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        o.set_default_response(gtk.RESPONSE_OK)
        f = gtk.FileFilter()
        f.set_name(_("GIMP Book"))
        f.add_pattern("*.book")
        o.add_filter(f)
        response = o.run()
        # filename = o.get_fielname()
        if response == gtk.RESPONSE_OK:
            o.hide()
            self.close_book()
            self.book = Book(self)
            self.book.load_book(o.get_filename(), self)
            self.show_book()
            self.loaded = True
            self.enable_controls()
        o.destroy()

    def add_book(self, book):
        # Add a book to the main window. You still new to show it.
        self.book = book
        self.loaded = True
        self.show_book()
        self.enable_controls()

    def show_book(self):
        # Load the pages into an IconView.
        self.thumbs.connect("selection-changed", self.select_page)
        self.thumbs.connect("item-activated", self.book.open_page)
        self.thumbs.connect("button-press-event", self.button_press, self.pagemenu)
        self.thumbs.set_model(self.book.pagestore)
        self.book.update_thumbs()
        self.zoomoutm.set_sensitive(True)
        self.zoominm.set_sensitive(True)
        self.thumbs.set_item_width(self.book.thumbwidth + 10)
        self.thumbs.select_path(0)
        self.update_title()

    def update_title(self):
        # Update the title bar.

        # TRANSLATORS: The %s(book_title)s, %s(selected_page)s and %(page_count)s need to be left in.
        # You can put them in a different order if needed.
        self.set_title(_("GIMP Book - %(book_title)s (page %(selected_page)s of %(page_count)s)") % { 'book_title': self.book.bookname, 'selected_page': self.book.selected, 'page_count': len(self.book.pagestore)-1 })

    def button_press(self, widget, event, menu):
        # Capture buttons presses on thumbs.
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            path = widget.get_path_at_pos(int(event.x), int(event.y))
            if path:
                widget.select_path(widget.get_path_at_pos(int(event.x), int(event.y)))
            menu.popup(None, None, None, event.button, event.time)
            pass
        
    def export_win(self, widget):
        # Settings for exporting the book.
        self.set_sensitive(False)
        exportWin = ExportWin(self)

    def select_page(self, thumbs):
        # A page has been selected.
        if self.thumbs.get_selected_items():
            self.book.selected = self.thumbs.get_selected_items()[0][0]
            self.update_title()
        else:
            self.book.selected = -1

    def ask_add_page(self, widget):
        # Add a new page to the current book.
        dest = self.book.selected
        if self.book.selected < 1:
            dest = len(self.book.pagestore)
        if self.loaded:
            response, text = self.name_dialog(_("Add a Page"), _("Enter Page Name: "))
            if response == gtk.RESPONSE_ACCEPT:
                if self.valid_name(text):
                    text = self.valid_name(text)
                    self.book.add_page(text, dest)
                    self.del_page.set_sensitive(True)
                    self.update_title()
        else:
            show_error_msg(_("You need to create or load a book, before adding pages to it."))

    def open_page(self, widget):
        # Open page from right click menu.
        if self.book.selected < 0:
            show_error_msg(_("No page selected to open."))
            return False
        self.book.open_page(self.thumbs, [self.book.selected])

    def ask_import_page(self, widget):
        # Import page dialog.
        dest = self.book.selected
        if self.book.selected < 1:
            dest = len(self.book.pagestore)
        if self.loaded:
            # Interface for opening an existing book.
            i = gtk.FileChooserDialog(_("Import Page(s)"), self, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            i.set_default_response(gtk.RESPONSE_OK)
            i.set_select_multiple(True)
            f = gtk.FileFilter()
            f.set_name(_("All Images"))
            f.add_pattern("*.bmp")
            f.add_pattern("*.gif")
            f.add_pattern("*.jpe")
            f.add_pattern("*.jpeg")
            f.add_pattern("*.jpg")
            f.add_pattern("*.ora")
            f.add_pattern("*.pdf")
            f.add_pattern("*.png")
            f.add_pattern("*.psd")
            f.add_pattern("*.psp")
            f.add_pattern("*.svg")
            f.add_pattern("*.tga")
            f.add_pattern("*.tif")
            f.add_pattern("*.tiff")
            f.add_pattern("*.xcf")
            i.add_filter(f)
            response = i.run()
            # filename = o.get_fielname()
            if response == gtk.RESPONSE_OK:
                i.hide()
                if self.valid_name(i.get_filename()):
                    self.book.import_page(i.get_filenames(), dest)
                    self.del_page.set_sensitive(True)
                    self.update_title()
            i.destroy()

    def ask_dupli_page(self, widget):
        # Duplicate the selected page.
        dest = self.book.selected
        if self.book.selected < 0:
            show_error_msg(_("No page selected to duplicate."))
            return False
        if self.loaded:
            response, text = self.name_dialog(_("Duplicate Page"), _("Enter Name of Duplicate: "))
            if response == gtk.RESPONSE_ACCEPT:
                if self.valid_name(text):
                    text = self.valid_name(text)
                    self.book.dupli_page(text, dest)
                    self.del_page.set_sensitive(True)
                    self.update_title()
        else:
            show_error_msg(_("You need to create or load a book, before adding pages to it."))

    def ask_rename_page(self, widget):
        # Rename the selected page.
        if self.book.selected < 0:
            show_error_msg(_("No page selected to rename."))
            return False
        if self.book.selected > -1:
            response, text = self.name_dialog(_("Rename Page"), _("Ente Page Name: "))
            if response == gtk.RESPONSE_ACCEPT:
                if self.valid_name(text):
                    text = self.valid_name(text)
                    self.book.rename_page(text)

    def ask_delete_page(self, widget):
        # Delete the selected page.
        if self.book.selected < 0:
            show_error_msg(_("No page selected to delete."))
            return False
        # TRANSLATORS: %s is the name of the page to be deleted
        areyousure = gtk.MessageDialog(self, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _('Delete page "%s"?') % (self.book.pagestore[self.book.selected][0]))
        response = areyousure.run()
        if response == gtk.RESPONSE_YES:
            self.book.delete_page()
            if len(self.book.pagestore) < 2:
                self.del_page.set_sensitive(False)
            self.update_title()
            areyousure.destroy()
        else:
            areyousure.destroy()

    def name_dialog(self, title, label):
        # Dialog for entering page names.
        dialog = gtk.Dialog(title,
                            self,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        hbox = gtk.HBox(False, 4)
        hbox.show()
        dialog.vbox.pack_start(hbox)
        label = gtk.Label(label)
        label.show()
        hbox.pack_start(label)
        entry = gtk.Entry()
        entry.set_activates_default(True)
        entry.show()
        hbox.pack_start(entry)
        response = dialog.run()
        text = entry.get_text()
        dialog.destroy()
        return response, text

    def valid_name(self, name):
        # Replaces illegal characters with _. Removes - and . from filename, and limits length to 255 characters, including extension.
        if len(name) < 1:
            show_error_msg(_("No page name entered."))
            return False
        loop = True
        while loop:
            if name[0] == "." or name[0] == "-":
                name = name[1:]
            else:
                loop = False
        illegalcs =  "\\", "/", ":", "*", "?", "\"", "<", "<", ">", "|", "^", "'", "!", "$", "@", "&", "(", ")", "+", "~", ",", "="
        for c in illegalcs:
            name = name.replace(c, "_")
        if len(name) > 251:
            name = name[:250]
            show_error_msg(_("Warning! Page name truncated to 255 characters."))
            return False
        if os.path.exists(os.path.join(self.book.pagepath, ("%s.xcf" % (name)))):
            # TODO! Support case insensitive names on Windows.
            # TRANSLATORS: %s is the name of an existnig conflictnig page.
            show_error_msg(_("A page called '%s.xcf' exists. Page names must be unique.") % (name))
            return False
        return name

    def enable_controls(self):
        # Enable the controles that are disabled when no book is loaded.
        self.add_page.set_sensitive(True)
        self.dupli_page.set_sensitive(True)
        self.ren_page.set_sensitive(True)
        self.imp_page.set_sensitive(True)
        self.file_export.set_sensitive(True)
        self.storyboardm.set_sensitive(True)
        if self.book.thumbsize >= THUMBMAX:
            self.zoomoutm.set_sensitive(True)
            self.zoominm.set_sensitive(False)
        elif self.book.thumbsize <= THUMBMIN:
            self.zoomoutm.set_sensitive(False)
            self.zoominm.set_sensitive(True)
        else:
            self.zoomoutm.set_sensitive(True)
            self.zoominm.set_sensitive(True)
        if len(self.book.pagestore) > 1:
            self.del_page.set_sensitive(True)
            self.deletepage.set_sensitive(True)
        self.openpage.set_sensitive(True)
        self.addpage.set_sensitive(True)
        self.duplipage.set_sensitive(True)
        self.renamepage.set_sensitive(True)
        self.deletepage.set_sensitive(True)
        self.importpage.set_sensitive(True)

    def toggle_storyboard_mode(self, widget):
        # Have the pages flow, rather than be shown in two columns. Handy for storyboarding.
        if int(self.thumbs.get_columns()) == 2:
            self.thumbs.set_columns(0)
            self.storyboardmode = 1
        else:
            self.thumbs.set_columns(2)
            self.storyboardmode = 0
            
    def zoomin(self, widget):
        # Display thumbnails larger.
        if self.book.thumbsize < THUMBMAX:
            self.book.thumbsize = int(self.book.thumbsize * 2)
        if self.book.thumbsize >= THUMBMAX:
            self.zoominm.set_sensitive(False)
        self.book.update_thumbs()
        self.zoomoutm.set_sensitive(True)
        self.thumbs.set_item_width(self.book.thumbwidth + 10)
        self.book.save()
    
    def zoomout(self, widget):
        # Display thumbnails smaller.
        if self.book.thumbsize > THUMBMIN:
            self.book.thumbsize = int(self.book.thumbsize / 2.0)
        if self.book.thumbsize <= THUMBMIN:
            self.zoomoutm.set_sensitive(False)
        self.book.update_thumbs()
        self.zoominm.set_sensitive(True)
        self.thumbs.set_item_width(self.book.thumbwidth + 10)
        self.book.save()

    def close_book(self):
        if self.loaded:
            self.thumbs.set_model()
            del self.book
            self.loaded = False

def show_book():
    # Display the book window.
    r = Main()
    gtk.main()

def show_error_msg( msg ):
    # Output error messages to the GIMP error console.
    origMsgHandler = pdb.gimp_message_get_handler()
    pdb.gimp_message_set_handler(ERROR_CONSOLE)
    pdb.gimp_message(msg)
    pdb.gimp_message_set_handler(origMsgHandler)


# This is the plugin registration function
register(
    "python_fu_book",    
    _("Tool for managing multiple pages of a comic book, childrens book, sketch book or similar."),
    "GNU GPL v3 or later.",
    "Ragnar Brynjúlfsson",
    "Ragnar Brynjúlfsson",
    _("July 2014"),
    "<Toolbox>/Windows/Book...",
    "",
    [
    ],  
    [],
    show_book,
)


main()


# FUTURE FEATURES & FIXES
#  HIGH
#  MEDIUM
# - Adjust layout in export window.
# - Left to right or right to left reading option when exporting.
# - Add Percent based margins.
#  LOW
# - Support color coding pages, making it easy to divide up the story into chapters or mark pages.



