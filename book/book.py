#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Script for managing multiple pages in GIMP, intended for working with comic books, illustrated childrens books,
# sketchbooks or similar.
#
# Copyright 2011 - Ragnar Brynjúlfsson
# TODO! Add license info
#
# http://queertales.com
import os
# import re
# import glob
import sys
import hashlib
import json
import shutil
import gtk
import gobject
import urllib
from gimpfu import *
from gimpenums import *
from time import strftime
# from pprint import pprint

class Page():
    # Stores instances and information on a single page.
    def __init__ (self, page):
        # Set page variables.
        self.pagepath = page # Path to the page.
        self.name = os.path.basename(self.pagepath)
        self.thumb = Thumb(self.pagepath)

class Thumb():
    # Managing thumbnails, and creating new ones when needed.
    def __init__(self, imagepath):
        self.imagepath = imagepath
        if not self.find_thumb():
            self.build_thumb()
            if not self.find_thumb():
                show_error_msg('Failed to find or build thumb for %s.' % self.imagepath)

    def build_thumb(self):
        # Build or rebuild a thumb for the image.
        img = pdb.gimp_xcf_load(0, self.imagepath, self.imagepath)
        pdb.gimp_file_save_thumbnail(img, self.imagepath)
        pdb.gimp_image_delete(img)
        
    def find_thumb(self):
        # Find the pages thumbnail.
        # TODO! Fails with some obscure characters like !?* ...needs testing.
        imagepathuri = urllib.quote(self.imagepath.encode("utf-8"))
        file_hash = hashlib.md5('file://'+imagepathuri).hexdigest()
        thumb = os.path.join(os.path.expanduser('~/.thumbnails/large'), file_hash) + '.png'
        if os.path.exists(thumb):
            self.thumbpix = gtk.gdk.pixbuf_new_from_file(thumb)
            return True
        else:
            thumb = os.path.join(os.path.expanduser('~/.thumbnails/normal'), file_hash) + '.png'
            if os.path.exists(thumb):
                self.thumbpix = gtk.gdk.pixbuf_new_from_file(thumb)
                return True
            else:
                return False

class NewBookGUI(gtk.Window):
    # Interface for creating new books.
    def __init__(self, bookgui):
        self.book = bookgui.book
        self.bookgui = bookgui
        # Create a new book.
        win = super(NewBookGUI, self).__init__()
        self.set_title("Create a New Book...")
        self.set_size_request(300, 300)
        self.set_position(gtk.WIN_POS_CENTER)
        self.path = ""

        # TODO! Fix the layout, so that everything aligns properly.
        # Box for divding the window in three parts, name, page and buttons.
        cont = gtk.VBox(False, 4)
        self.add(cont)

        # Frame for the book name and path.
        bookframe = gtk.Frame()
        bookframe.set_shadow_type(gtk.SHADOW_NONE)
        bookframelabel = gtk.Label("<b>Book</b>")
        bookframelabel.set_use_markup(True)
        bookframe.set_label_widget(bookframelabel)
        cont.add(bookframe)
        # Split the book frame in 4.
        bookbox = gtk.VBox(False, 2)
        bookframe.add(bookbox)
        # Name entry field
        namebox = gtk.HBox(False, 2)
        bookbox.pack_start(namebox)
        namelabel = gtk.Label("Name:")
        self.nameentry = gtk.Entry()
        namebox.pack_start(namelabel)
        namebox.pack_start(self.nameentry)
        # Destination dialog
        destdialog = gtk.FileChooserDialog("Create a New Book", None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        destdialog.set_default_response(gtk.RESPONSE_OK)
        # Destination
        destbox = gtk.HBox(False, 2)
        bookbox.pack_start(destbox)
        destlabel = gtk.Label("Destination:")
        self.destbutton = gtk.FileChooserButton(destdialog)
        destbox.pack_start(destlabel)
        destbox.pack_start(self.destbutton)
        
        # Frame for the page size and color space.
        pageframe = gtk.Frame()
        pageframe.set_shadow_type(gtk.SHADOW_NONE)
        pageframelabel = gtk.Label("<b>Page</b>")
        pageframelabel.set_use_markup(True)
        pageframe.set_label_widget(pageframelabel)
        cont.add(pageframe)
        # Split the frame in 6
        pagebox = gtk.VBox(False, 2)
        pageframe.add(pagebox)
        # Width and height fields.
        widthbox = gtk.HBox(False, 2)
        pagebox.pack_start(widthbox)
        widthlabel = gtk.Label("Width:")
        widthadjust = gtk.Adjustment(1024, 1, 262144, 1, 100)
        self.widthentry = gtk.SpinButton(widthadjust)
        widthpixels = gtk.Label("pixels")
        widthbox.pack_start(widthlabel)
        widthbox.pack_start(self.widthentry)
        widthbox.pack_start(widthpixels)
        heightbox = gtk.HBox(False, 2)
        pagebox.pack_start(heightbox)
        heightlabel = gtk.Label("Height:")
        heightadjust = gtk.Adjustment(1024, 1, 262144, 1, 100)
        self.heightentry = gtk.SpinButton(heightadjust)
        heightpixels = gtk.Label("pixels")
        heightbox.pack_start(heightlabel)
        heightbox.pack_start(self.heightentry)
        heightbox.pack_start(heightpixels)
        # Color space:
        colorbox = gtk.HBox(False, 2)
        pagebox.pack_start(colorbox)
        colorlabel = gtk.Label("Color Space:")
        colorlist = gtk.ListStore(gobject.TYPE_STRING)
        colors = [ "RBG color", "Grayscale" ]
        for color in colors:
            colorlist.append([color])
        self.colormenu = gtk.ComboBox(colorlist)
        colorcell = gtk.CellRendererText()
        self.colormenu.pack_start(colorcell, True)
        self.colormenu.add_attribute(colorcell, 'text', 0)
        self.colormenu.set_active(0)
        colorbox.pack_start(colorlabel)
        colorbox.pack_start(self.colormenu)
        # Background fill.
        fillbox = gtk.HBox(False, 2)
        pagebox.pack_start(fillbox)
        filllabel = gtk.Label("Fill with:")
        filllist = gtk.ListStore(gobject.TYPE_STRING)
        fills = [ "Foreground color", "Background color", "White", "Transparency" ]
        for fill in fills:
            filllist.append([fill])
        self.fillmenu = gtk.ComboBox(filllist)
        fillcell = gtk.CellRendererText()
        self.fillmenu.pack_start(fillcell, True)
        self.fillmenu.add_attribute(fillcell, 'text', 0)
        self.fillmenu.set_active(1)
        fillbox.pack_start(filllabel)
        fillbox.pack_start(self.fillmenu)
        
        # Buttons
        buttonbox = gtk.HBox(False, 2)
        cont.add(buttonbox)
        # Help
        helpbutton = gtk.Button("Help")
        helpbutton.connect("clicked", self.help) # No pun intended!
        buttonbox.pack_start(helpbutton)
        # Cancel
        cancelbutton = gtk.Button("Cancel")
        cancelbutton.connect("clicked", self.cancel)
        buttonbox.pack_start(cancelbutton)
        # OK
        okbutton = gtk.Button("Ok")
        okbutton.connect("clicked", self.make_book)
        buttonbox.pack_start(okbutton)

        self.show_all()


    def help(self, widget):
        # Displays help for the new book dialog.
        helpdialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "TODO! Help for this window")
        helpdialog.run()
        helpdialog.destroy()

    def cancel(self, widget):
        # Cancel book creation and close the window.
        self.destroy()

    def make_book(self, widget):
        # Make a page.
        self.book.make_book(self.destbutton.get_filename(), self.nameentry.get_text(), self.widthentry.get_value(), self.heightentry.get_value(), self.colormenu.get_active(), self.fillmenu.get_active())
        self.bookgui.load_book(os.path.join(self.destbutton.get_filename(), self.nameentry.get_text(), self.nameentry.get_text(), ".book"))
        self.destroy()


class Book():
    # Stores and manages the data for the book.
    def __init__(self):
        # Defines basic variables to store.
        self.loaded = False  # If there is a book loaded in the interface.
        self.pagecount = 0  # Number of pages in this book.
        self.bookfile = ""  # The *.book for this book.
        self.bookname = ""  # The name of the book.
        self.bookpath = ""  # The path to the folder containing the book.
        self.pagepath = ""  # Path to the "pages" subfolder.
        self.trashpath = "" # Path to trash folder.
        self.pages = []     # List for storing page objects.
        self.selected = -1  # Index of the currently selected page, -1 if none.

    def make_book(self, dest, name, w, h, color, fill):
        # Build the files and folders needed for the book.
        width = int(w)
        height = int(h)
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
                # Make file dest/name/Template.xcf
                img = pdb.gimp_image_new(width, height, color)
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
                pdb.gimp_xcf_save(0, img, None, os.path.join(fullpath, "pages", "Template.xcf") , "Template.xcf")
                # Load the newly created book.
                self.load_book(os.path.join(fullpath, name+".book"))
                # TODO! Check if everything was created correctly.
                return True
            else:
                show_error_msg("Name was left empty")
        else:
            show_error_msg("Destination does not exist.")

    def load_book(self, bookfile):
        # Loads a selected book.
        # TODO! Fix bug when loading a second book.
        if os.path.exists(bookfile):
            self.loaded = True
            self.bookfile = bookfile
            self.bookname = os.path.splitext(os.path.basename(self.bookfile))[0]
            self.bookpath = os.path.dirname(self.bookfile)
            self.pagepath = os.path.join(self.bookpath, "pages")
            self.trashpath = os.path.join(self.bookpath, "trash")
            # Load the pages.
            f = open(self.bookfile, "r")
            metatext = f.read()
            metadata = json.loads(metatext)
            f.close()
            pagelist = metadata['pages']
            for p in pagelist:
                # Create a page object, and add to a list.
                self.pagecount += 1
                self.pages.append(Page(os.path.join(self.pagepath, p)))
            return True


    def move_page(self, pagestore, destination_index, tree_iterator):
        # Move a page around in the book.
        if self.selected > -1:
            destination = destination_index[0]
            if not destination == self.selected:
                movingpage = self.pages.pop(self.selected)
                if destination < self.selected:
                    self.pages.insert(destination, movingpage)
                else:
                    self.pages.insert(destination-1, movingpage)
                self.write_pages()

    def open_page(self, iconview, number):
        # Open the page the user clicked in GIMP.
        number = number[0]
        img = pdb.gimp_file_load(self.pages[number].pagepath, self.pages[number].pagepath)
        img.clean_all()
        gimp.Display(img)

    def write_pages(self):
        # Writes self.pages to the *.book file.
        metadata = []
        for p in self.pages:
            metadata.append(p.name)
        savetofile = json.dumps({ 'pages': metadata }, indent=4)
        bookfile = open(os.path.join(self.bookpath,self.bookname+".book"), "w")
        bookfile.write(savetofile)
        bookfile.close()

    def add_page(self, pagetitle, dest):
        # Copy the template to a new page.
        try:
            shutil.copy(self.pages[0].pagepath, os.path.join(self.pagepath, pagetitle))
            p = Page(os.path.join(self.pagepath, pagetitle))
            self.pages.insert(dest, p)
            self.write_pages()
            return True
        except Exception, err:
            show_error_msg(err)

    def delete_page(self):
        # Delete the selected page.
        try:
            shutil.move(self.pages[self.selected].pagepath, os.path.join(self.trashpath,strftime("%Y%m%d_%H%M%S_")+self.pages[self.selected].name))
            self.pages.pop(self.selected)
            self.write_pages()
            return True
        except Exception, err:
            show_error_msg(err)

    def rename_page(self, pagetitle):
        # Rename a page.
        try:
            shutil.move(self.pages[self.selected].pagepath, os.path.join(self.pagepath, pagetitle))
            p = Page(os.path.join(self.pagepath, pagetitle))
            self.pages[self.selected] = p
            self.write_pages()
            return True
        except Exception, err:
            show_error_msg(err)
            

class BookGUI(gtk.Window):
    # Builds a GTK windows for managing the pages of a book.
    def __init__ (self):
        self.book = Book()
        self.pagestore = gtk.ListStore(str, gtk.gdk.Pixbuf, bool)

        window = super(BookGUI, self).__init__()
        self.w, self.h = 600, 600
        self.set_title("Book")
        self.set_size_request(self.w, self.h)
        self.set_position(gtk.WIN_POS_CENTER)
        self.path = ""
        
        # Main menu
        mb = gtk.MenuBar()

        filemenu = gtk.Menu()
        i_file = gtk.MenuItem("File")
        i_file.set_submenu(filemenu)
        
        agr = gtk.AccelGroup()
        self.add_accel_group(agr)

        file_new = gtk.ImageMenuItem(gtk.STOCK_NEW, agr)
        file_new.set_label("New Book...")
        key, mod = gtk.accelerator_parse("<Control>N")
        file_new.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_new.connect("activate", self.new_book)
        filemenu.append(file_new)

        file_open = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        file_open.set_label("Open Book...")
        key, mod = gtk.accelerator_parse("<Control>O")
        file_open.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_open.connect("activate", self.open_book)
        filemenu.append(file_open)

        sep1 = gtk.SeparatorMenuItem()
        filemenu.append(sep1)

        file_export = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        file_export.set_label("Export Book...")
        key, mod = gtk.accelerator_parse("<Control>E")
        file_export.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_export.connect("activate", self.export_book_gui)
        filemenu.append(file_export)

        sep2 = gtk.SeparatorMenuItem()
        filemenu.append(sep2)

        file_close = gtk.ImageMenuItem(gtk.STOCK_CLOSE, agr)
        file_close.set_label("Close Book...")
        key, mod = gtk.accelerator_parse("<Control>W")
        file_close.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        file_close.connect("activate", gtk.main_quit)
        filemenu.append(file_close)

        mb.append(i_file)

        # Main toolbar
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        new_page = gtk.ToolButton(gtk.STOCK_NEW)
        new_page.connect("clicked", self.add_page)
        delete_page = gtk.ToolButton(gtk.STOCK_DELETE)
        delete_page.connect("clicked", self.delete_page)
        rename_page = gtk.ToolButton(gtk.STOCK_PROPERTIES)
        rename_page.connect("clicked", self.rename_page)
        toolbar.insert(new_page, 0)
        toolbar.insert(delete_page, 1)
        toolbar.insert(rename_page, 2)

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)
        vbox.pack_start(toolbar, False, False, 0)

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(self.scroll, True, True, 0)

        self.add(vbox)
        self.connect("destroy", gtk.main_quit)
        self.show_all()
        return window    

    def new_book(self, widget):
        # Helper for opening up the New Book window.
        self.close_book()
        nb = NewBookGUI(self)
        del nb

    def open_book(self, widget):
        # Interface for opening an existing book.
        o = gtk.FileChooserDialog("Open Book", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        o.set_default_response(gtk.RESPONSE_OK)
        f = gtk.FileFilter()
        f.set_name("GIMP Book")
        f.add_pattern("*.book")
        o.add_filter(f)
        response = o.run()
        if response == gtk.RESPONSE_OK:
            self.close_book()
            if self.book.load_book(o.get_filename()):
                self.load_book(o.get_filename())
        o.destroy()

    def load_book(self, bookfile):
        # Load the pages into an IconView.
        for p in self.book.pages:
            self.pagestore.append((p.name, p.thumb.thumbpix, True))
        self.pagestore.connect("row-inserted", self.book.move_page)
        self.thumbs = gtk.IconView(self.pagestore)
        self.thumbs.set_text_column(0)
        self.thumbs.set_pixbuf_column(1)
        self.thumbs.set_reorderable(True)
        self.thumbs.set_columns(2)
        self.thumbs.connect("selection-changed", self.select_page)
        self.thumbs.connect("item-activated", self.book.open_page)
        self.scroll.add(self.thumbs)
        self.set_title("GIMP Book - %s" % (self.book.bookname))
        self.show_all()
        
    def export_book_gui(self, widget):
        # Settings for exporting the book.
        print("Open export GUI")

    def select_page(self, thumbs):
        # A page has been selected.
        if self.thumbs.get_selected_items():
            self.book.selected = self.thumbs.get_selected_items()[0][0]
        else:
            self.book.selected = -1

    def add_page(self, widget):
        # Add a new page to the current book.
        # TODO! Show message on illegal characters and duplicate file creation.
        dest = self.book.selected
        if self.book.selected < 1:
            dest = len(self.book.pages)
        if self.book.loaded:
            response, text = self.name_dialog("Add a Page", "Enter Page Description: ")
            if response == gtk.RESPONSE_ACCEPT:
                if text:
                    pagetitle = text+".xcf"
                    unique = True
                    for p in self.book.pages:
                        if pagetitle == p.name:
                            unique = False
                            break
                    if unique:
                        if self.book.add_page(pagetitle, dest):
                            self.pagestore.insert(dest, (self.book.pages[dest].name, self.book.pages[dest].thumb.thumbpix, True))
                    else:
                        show_error_msg("The page name must be unique. Page '%s' already exists." % (pagetitle))
                else:
                    show_error_msg("No page name entered.")
        else:
            show_error_msg("You need to create or load a book, before adding pages to it.")
            # TODO! Disable toolbutton, if no book is loaded.

    def delete_page(self, widget):
        # Delete the selected page.
        areyousure = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, 'Delete page "%s"?' % (self.book.pages[self.book.selected].name))
        response = areyousure.run()
        if response == gtk.RESPONSE_YES:
            if self.book.delete_page():
                del self.pagestore[self.book.selected]
        areyousure.destroy()

    def rename_page(self, widget):
        # Rename the selected page.
        # TODO! Show message on illegal characters and duplicate file creation.
        if self.book.selected > -1:
            response, text = self.name_dialog("Rename Page", "Ente Page Description: ")
            if response == gtk.RESPONSE_ACCEPT:
                if text:
                    pagetitle = text+".xcf"
                    unique = True
                    for p in self.book.pages:
                        if pagetitle == p.name:
                            unique = False
                            break
                    if unique:
                        if self.book.rename_page(pagetitle):
                            del self.pagestore[self.book.selected]
                            self.pagestore.insert(self.book.selected, (self.book.pages[self.book.selected].name, self.book.pages[self.book.selected].thumb.thumbpix, True))
                    else:
                        show_error_msg("The page title must be unique.")
                        

    def name_dialog(self, title, label):
        # Dialog for entering page names.
        dialog = gtk.Dialog(title,
                            None,
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

    def close_book(self):
        # Closes the currently open book.
        self.pagestore = gtk.ListStore(str, gtk.gdk.Pixbuf, bool)
        self.book = Book()


def show_book():
    # Display the book window.
    r = BookGUI()
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
    "Tool for managing multiple pages of a comic book, childrens book or your sketch book.",
    "GNU GPL v2 or later.",
    "Ragnar Brynjúlfsson",
    "Ragnar Brynjúlfsson",
    "July 2011",
    "<Toolbox>/Windows/Book...",
    "",
    [
    ],  
    [],
    show_book,
)

main()
