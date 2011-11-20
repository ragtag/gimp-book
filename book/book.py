#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Script for managing multiple pages in GIMP, intended for working with comic books,  illustrated childrens books,
# sketchbooks or similar.
#
# Copyright 2011 - Ragnar Brynjúlfsson
# TODO! Add license info
#
# http://queertales.com
import os, re, glob, sys
import hashlib
import json
import gtk
import gtk.glade
import gobject
from gimpfu import *
from gimpenums import *
from pprint import pprint


class Page():
    # Stores instances and information on a single page.
    def __init__ (self, page, parent, number):
        self.parent = parent # Links to the parent Book object.
        self.number = number # The page number of this page.
        self.pagepath = page # Path to the page.
        self.thumbpath = ""  # Path to the pages thumb.
        self.name = os.path.basename(self.pagepath)
        # Find or generate the thumbnail for the page.
        if not self.find_thumb():
            img = pdb.gimp_xcf_load(0, self.pagepath, os.path.basename(self.pagepath))
            pdb.gimp_file_save_thumbnail(img, self.pagepath)
            pdb.gimp_image_delete(img)
            self.find_thumb()
        self.thumbfile = gtk.gdk.pixbuf_new_from_file(self.thumbpath)
        self.thumb = gtk.Image()
        self.thumb.set_from_pixbuf(self.thumbfile)
        self.page = gtk.EventBox()
        self.page.add(self.thumb)
        self.page.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.page.connect("button_press_event", self.pageclicked) # No pun intended!

    def pageclicked(self, widget, event):
        # Dummy function to test page clicking. Currently just loads the image you clicked.
        if (event.button == 1):
            img = pdb.gimp_file_load(self.pagepath, self.pagepath)
            gimp.Display(img)
        elif (event.button == 3):
            self.popupmenu(event)

    def popupmenu(self, event):
        # Popup Menu for the thumbnail.
        # Move page, delete page, 
        m = gtk.Menu()
        o = gtk.MenuItem("Open Page")
        o.show()
        o.connect("activate", self.open)
        m.append(o)
        add = gtk.MenuItem("Add Page")
        add.show()
        add.connect("activate", self.add)
        m.append(add)
        move = gtk.MenuItem("Move Page to...")
        move.show()
        m.append(move)
        delete = gtk.MenuItem("Delete Page")
        delete.show()
        delete.connect("activate", self.delete)
        m.append(delete)
        m.popup(None, None, None, event.button, event.time, None)
        
    def open(self, widget):
        # Open the current page im GIMP.
        img = pdb.gimp_file_load(self.pagepath, self.pagepath)
        gimp.Display(img)

    def add(self, widget):
        # Add a page.
        current_page = self.number
        self.parent.shift_pages(self.number, self.parent.pagecount, True)
        # self.parent.add_page(current_page)

    def move(self, widget):
        # Move the current page to somewhere else in the order.
        # Open window to ask where to.
        pass

    def delete(self, widget):
        # Delete this page.
        #self.parent.delete_page(self)
        nextpage = self.number + 1
        self.parent.shift_pages(nextpage, self.parent.pagecount, False)

    def shift(self, pagenumber):
        # Move this page to pagenumber
        show_error_msg("Move page %s to %s" % (self.number, pagenumber)) 
        # self.number = pagenumber

    def find_thumb(self):
        # Find the pages thumbnail.
        file_hash = hashlib.md5('file://'+self.pagepath).hexdigest()
        thumb = os.path.join(os.path.expanduser('~/.thumbnails/large'), file_hash) + '.png'
        if os.path.exists(thumb):
            self.thumbpath = thumb
            return True
        else:
            thumb = os.path.join(os.path.expanduser('~/.thumbnails/normal'), file_hash) + '.png'
            if os.path.exists(thumb):
                self.thumbpath = thumb
                return True
            else:
                return False


class NewBook(gtk.Window):
    # Interface for creating new books.
    def __init__(self, book):
        self.book = book
        # Create a new book.
        win = super(NewBook, self).__init__()
        self.set_title("Create a New Book...")
        self.set_size_request(300, 300)
        self.set_position(gtk.WIN_POS_CENTER)
        self.path = ""

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
        # Build the files and folders needed for the book.
        dest = self.destbutton.get_filename()
        name = self.nameentry.get_text()
        width = int(self.widthentry.get_text())
        height = int(self.heightentry.get_text())
        color = self.colormenu.get_active()
        fill = self.fillmenu.get_active()
        if os.path.isdir(dest):
            if name:
                # Make folder dest/name
                fullpath = os.path.join(dest, name)
                if not os.path.isdir(fullpath):
                    os.makedirs(fullpath)
                # Make file dest/name/name.book
                metadata = json.dumps({ 'pages':[ ] }, indent=4)
                bookfile = open(os.path.join(fullpath,name+".book"), "w")
                bookfile.write(metadata)
                bookfile.close()
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
                pdb.gimp_xcf_save(0, img, None, os.path.join(fullpath, "Template.xcf") , "Template.xcf")
                # Make folder dest/name/Pages
                if not os.path.isdir(os.path.join(fullpath,"pages")):
                    os.makedirs(os.path.join(fullpath,"pages"))
                # Load the newly created book.
                self.book.load_book(os.path.join(fullpath, name+".book"))
                # Kill the window. TODO! Check if everything was created correctly.
                self.destroy()
            else:
                show_error_msg("Name was left empty")
        else:
            show_error_msg("Destination does not exist.")



class Book(gtk.Window):
    # Builds a GTK windows for managing the pages of a book.
    def __init__ (self):
        self.loaded = False # If there is a book loaded in the interface.
        self.pagecount = 0  # Number of pages in this book.
        self.bookfile = ""  # The *.book for this book.
        self.bookname = ""  # The name of the book.
        self.bookpath = ""  # The path to the folder containing the book.
        self.pagepath = ""  # Path to the "pages" subfolder.
        self.pages = []     # List for storing page objects.
        self.selected = -1  # Index of the currently selected page, -1 if none.
        self.left2right = True  # Read from left to right.
        self.spreads = True     # Show two and two pages together, rather than individual ones.
        self.firstpage = True   # Have the first page stand alone, even if self.spreads is true.

        window = super(Book, self).__init__()
        self.w, self.h = 300, 600
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

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)

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
        toolbar.insert(new_page, 0)
        toolbar.insert(delete_page, 1)

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)
        vbox.pack_start(toolbar, False, False, 0)

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(self.scroll, True, True, 0)
        # self.hbox = gtk.HBox(False, 2)
        #vbox.pack_start(self.hbox, False, False, 0)

        self.add(vbox)
        self.connect("destroy", gtk.main_quit)
        self.show_all()
        return window    

    def new_book(self, widget):
        # Helper for opening up the New Book window.
        nb = NewBook(self)

    def open_book(self, widget):
        # Interface for opening an existing book.
        o = gtk.FileChooserDialog("Create a New Book", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        o.set_default_response(gtk.RESPONSE_OK)
        f = gtk.FileFilter()
        f.set_name("GIMP Book")
        f.add_pattern("*.book")
        o.add_filter(f)
        response = o.run()
        if response == gtk.RESPONSE_OK:
            self.load_book(o.get_filename())
        o.destroy()
        

    def load_book(self, book):
        # Loads a selected book.
        if os.path.exists(book):
            self.loaded = True
            self.bookfile = book
            self.bookname = os.path.splitext(os.path.basename(book))[0]
            self.bookpath = os.path.dirname(book)
            self.pagepath = os.path.join(self.bookpath, "pages")
            # Load the pages.
            metadata = json.dumps({ 'pages':[ ] }, indent=4)
            bookfile = open(self.bookfile, "r")
            metatext = bookfile.read()
            metadata = json.loads(metatext)
            bookfile.close()
            pagelist = metadata['pages']
            for p in pagelist:
                # Create a page object, and add to a list.
                self.pagecount += 1
                self.pages.append(Page(os.path.join(self.pagepath, p),self, self.pagecount))

            # Load the pages into an IconView.
            self.pagestore = gtk.ListStore(str, gtk.gdk.Pixbuf, bool)
            for p in self.pages:
                self.pagestore.append((p.name, p.thumbfile, True))
            self.pagestore.connect("rows-reordered", self.drag_callback)
            self.pagestore.connect("row-inserted", self.drag_callback)
            thumbs = gtk.IconView(self.pagestore)
            thumbs.set_text_column(0)
            thumbs.set_pixbuf_column(1)
            thumbs.set_reorderable(True)
            thumbs.set_columns(2)
            thumbs.connect("selection-changed", self.selection)
            thumbs.connect("item-activated", self.open_page)
            self.scroll.add(thumbs)
            #for p in self.pages:
            #    self.hbox.pack_start(p.page, False, False, 0)
            self.set_title("Book - %s" % (self.bookname))
            self.show_all()
        else:
            show_error_msg("Unable to find book "+book)

    def open_page(self, iconview, number):
        # Open the page the user clicked in GIMP.
        number = number[0]
        pprint(book.pages[number].pagepath)
        img = pdb.gimp_file_load(book.pages[number].pagepath, book.pages[number].pagepath)
        gimp.Display(img)

    def selection(self, thumbs):
        # A page has been selected.
        pagenumber = thumbs.get_selected_items()
        if pagenumber:
            self.selected = pagenumber[0]
        else:
            self.selected = -1
        print("Page %s selected." % (self.selected))

    def drag_callback(self, pagestore, destination_index, tree_iterator):
        # Pages have been dragged around.
        destination = destination_index[0]
        selected = self.selected[0]
        if destination > selected:
            destination = (destination - 1)
        print("Page %s moved to %s" % (selected, destination))
        # Shifting pages around.
        last = len(self.pages)-1
        # Remove the page.
        tmpage = self.pages[selected]
        if last > selected:
            index = selected + 1
            for p in self.pages[selected+1:last]:
                self.pages[index-1] = self.pages[index]
            del self.pages[last]
        # Add the page back in.
        if destination == last:
            self.pages[last] = tmpage
        else:
            pass

    def shift_pages(start, forward):
        # Shifting the pages.
        direction = 1
        if not forward:
            direction = -1
        last = len(self.pages)-1
        if last > start:
            index = start + 1
            for p in self.pages[start+1:]:
                self.pages[index+direction] = self.pages[index]


    def add_page(self, widget):
        # Add a new page to the current book.
        # TODO! Define page number where to add the page.
        if self.path:
            try:
                img = pdb.gimp_image_new(800, 800, 0)
                pdb.gimp_xcf_save(0, img, None, self.path+"/aaa.xcf", "aaa.xcf")
                show_error_msg("Adding a page")
                # TODO! Add a page object.
            except Exception, e:
                show_error_msg(e.message)
                sys.exit(1)
        else:
            show_error_msg("You need to create a book, before adding pages to it.")

    def delete_page(self, widget):
        # Delete the selected page.
        show_error_msg("Deleting a page")


    def open_book_old(self, widget):
        # Opens up a new book project
        #self.pagecount = 10

        #for i in xragne(self.pagecount):
        #    pass

        # Images
        try:
            self.boyd = gtk.gdk.pixbuf_new_from_file("/home/ragnar/Projects/sketches/ref/boyd.jpg")
        except Exception, e:
            show_error_msg(e.message)
            sys.exit(1)

        image1 = gtk.Image()
        image1.set_from_pixbuf(self.boyd)
        image2 = gtk.Image()
        image2.set_from_pixbuf(self.boyd)
        self.hbox.pack_start(image1, False, False, 0)
        self.hbox.pack_start(image2, False, False, 0)
        self.show_all()



def show_book():
    # Display the book window.
    r = Book()
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
