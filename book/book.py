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
# import sys
import hashlib
import json
import shutil
import gtk
import gobject
import urllib
from gimpfu import *
from gimpenums import *
from time import strftime

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
        print self.imagepath
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
            if float(os.stat(thumb).st_mtime) < float(os.stat(self.imagepath).st_mtime):
                return False
            self.thumbpix = gtk.gdk.pixbuf_new_from_file(thumb)
            self.path = thumb
            self.mtime = os.stat(thumb).st_mtime
            return True
        else:
            self.thumb = os.path.join(os.path.expanduser('~/.thumbnails/normal'), file_hash) + '.png'
            if os.path.exists(thumb):
                if float(os.stat(thumb).st_mtime) < float(os.stat(self.imagepath).st_mtime):
                    return False
                self.thumbpix = gtk.gdk.pixbuf_new_from_file(thumb)
                self.path = thumb
                self.mtime = os.stat(thumb).st_mtime
                return True
            else:
                return False

class NewBookWin(gtk.Window):
    # Interface for creating new books.
    def __init__(self, main):
        self.main = main
        # Create a new book.
        win = super(NewBookWin, self).__init__()
        self.set_title("Create a New Book...")
        self.set_size_request(400, 400)
        self.set_position(gtk.WIN_POS_CENTER)

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
        okbutton.connect("clicked", self.ok)
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

    def ok(self, widget):
        # Creates a new book.
        self.book = Book()
        self.book.make_book(self.destbutton.get_filename(), self.nameentry.get_text(), self.widthentry.get_value(), self.heightentry.get_value(), self.colormenu.get_active(), self.fillmenu.get_active())
        self.main.add_book(self.book)
        self.destroy()

class ExportWin(gtk.Window):
    # Windows for exporting the book in various formats.
    def __init__(self, main):
        # Build the export window.
        self.main = main
        win = super(ExportWin, self).__init__()
        self.set_title("Export Book...")
        self.set_size_request(350, 650)
        self.set_position(gtk.WIN_POS_CENTER)
        # Box for divding the window in three parts, name, page and buttons.
        cont = gtk.VBox(False, 4)
        self.add(cont)
        # Destination table
        destt = gtk.Table(4, 2, True)
        destl = gtk.Label("Destination Folder:")
        destd = gtk.FileChooserDialog("Export to", None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        destd.set_default_response(gtk.RESPONSE_OK)
        self.destb = gtk.FileChooserButton(destd)

        namel = gtk.Label("Name Pages Using:")
        namels = gtk.ListStore(gobject.TYPE_STRING)
        nameoptions = [ "Book Name", "Page Names", "Page Numbers", "Custom Name" ]
        for nameoption in nameoptions:
            namels.append([nameoption])
        self.namem = gtk.ComboBox(namels)
        namec = gtk.CellRendererText()
        self.namem.pack_start(namec, True)
        self.namem.add_attribute(namec, 'text', 0)
        self.namem.set_active(0)
        entl = gtk.Label("Custom Name:")
        self.namee = gtk.Entry(128)
        self.namee.set_sensitive(False)
        self.namem.connect("changed", self.name_option_changed)

        # Enable scaling and cropping
        self.enablescaletb = gtk.ToggleButton("Enable Resizing")
        self.enablescaletb.set_active(False)
        self.enablescaletb.connect("clicked", self.toggle_resize)
        self.enablecroptb = gtk.ToggleButton("Enable Crop")
        self.enablecroptb.set_active(False)
        self.enablecroptb.connect("clicked", self.toggle_crop)

        # Attach stuff to the table
        destt.attach(destl, 0,1,0,1)
        destt.attach(self.destb, 1,2,0,1)
        destt.attach(namel, 0,1,1,2)
        destt.attach(self.namem, 1,2,1,2)
        destt.attach(entl, 0,1,2,3)
        destt.attach(self.namee, 1,2,2,3)
        destt.attach(self.enablescaletb, 0,1,3,4)
        destt.attach(self.enablecroptb, 1,2,3,4)
        cont.add(destt)

        # Size frame
        self.sizef = gtk.Frame()
        self.sizef.set_sensitive(False)
        self.sizef.set_shadow_type(gtk.SHADOW_NONE)
        sizefl = gtk.Label("<b>Image Size</b>")
        sizefl.set_use_markup(True)
        self.sizef.set_label_widget(sizefl)
        cont.add(self.sizef)
        # Size table
        sizet = gtk.Table(1,2)
        sizel = gtk.Label("Size %:")
        sizea = gtk.Adjustment(100, 1, 65536, 1, 10)
        self.sizesb = gtk.SpinButton(sizea, 1, 1)
        self.sizesb.set_text("100")
        self.sizesb.set_numeric(True)
        self.sizesb.set_text("100")
        sizet.attach(sizel, 0,1,0,1)
        sizet.attach(self.sizesb, 1,2,0,1)
        self.sizef.add(sizet)

        # Crop frame
        self.cropf = gtk.Frame()
        self.cropf.set_sensitive(False)
        self.cropf.set_shadow_type(gtk.SHADOW_NONE)
        cropfl = gtk.Label("<b>Image Crop</b>")
        cropfl.set_use_markup(True)
        self.cropf.set_label_widget(cropfl)
        cont.add(self.cropf)
        # Crop table
        cropt = gtk.Table(4,2)
        cropwha = gtk.Adjustment(1024, 1, 65536, 1, 10)
        cropwl = gtk.Label("Width:")
        self.cropwsb = gtk.SpinButton(cropwha, 1, 0)
        self.cropwsb.set_numeric(True)
        self.cropwsb.set_text("100")
        crophl = gtk.Label("Height:")
        self.crophsb = gtk.SpinButton(cropwha, 1, 0)
        self.crophsb.set_numeric(True)
        self.crophsb.set_text("100")
        
        cropxya = gtk.Adjustment(0, 0, 65536, 1, 10)
        cropxl = gtk.Label("Offset X:")
        self.cropxsb = gtk.SpinButton(cropxya, 1, 0)
        self.cropxsb.set_text("0")
        self.cropxsb.set_numeric(True)
        cropyl = gtk.Label("Offset Y:")
        self.cropysb = gtk.SpinButton(cropxya, 1, 0)
        self.cropysb.set_text("0")
        self.cropysb.set_numeric(True)

        cropt.attach(cropwl, 0,1,0,1)
        cropt.attach(self.cropwsb, 1,2,0,1)
        cropt.attach(crophl, 0,1,1,2)
        cropt.attach(self.crophsb, 1,2,1,2)
        cropt.attach(cropxl, 0,1,2,3)
        cropt.attach(self.cropxsb, 1,2,2,3)
        cropt.attach(cropyl, 0,1,3,4)
        cropt.attach(self.cropysb, 1,2,3,4)
        self.cropf.add(cropt)

        # File format frame
        formatf = gtk.Frame()
        formatf.set_shadow_type(gtk.SHADOW_NONE)
        formatfl = gtk.Label("<b>File Formats</b>")
        formatfl.set_use_markup(True)
        formatf.set_label_widget(formatfl)
        cont.add(formatf)
        # Format table
        formatt = gtk.Table(3,2)
        formatl = gtk.Label("File Format:")
        formatls = gtk.ListStore(gobject.TYPE_STRING)
        formatoptions = [  "GIF image (*.gif)", "GIMP XCF image (*.xcf)", "JPEG image (*.jpg)", "PNG image (*.png)", "TIFF image (*.tif)" ]
        for formatoption in formatoptions:
            formatls.append([formatoption])
        self.formatm = gtk.ComboBox(formatls)
        formatc = gtk.CellRendererText()
        self.formatm.pack_start(formatc, True)
        self.formatm.add_attribute(formatc, 'text', 0)
        self.formatm.set_active(2) 
        self.formatm.connect("changed", self.format_changed)
        commentl = gtk.Label("Comment:")
        self.comment = gtk.Entry(256)

        self.gift = self.gif()
        #self.xcf()
        self.jpgt = self.jpg()
        self.pngt = self.png()
        self.tift = self.tif()

        formatt.attach(formatl, 0,1,0,1)
        formatt.attach(self.formatm, 1,2,0,1)
        formatt.attach(commentl, 0,1,1,2)
        formatt.attach(self.comment, 1,2,1,2)
        formatt.attach(self.gift, 0,2,2,3)
        formatt.attach(self.jpgt, 0,2,2,3)
        formatt.attach(self.pngt, 0,2,2,3)
        formatt.attach(self.tift, 0,2,2,3)
        formatf.add(formatt)

        # Done buttons
        doneb = gtk.HBox(True, 4)
        cancelb = gtk.Button("Cancel")
        cancelb.connect("clicked", self.close)
        exportb = gtk.Button("Export Pages")
        exportb.connect("clicked", self.export)
        doneb.pack_start(cancelb)
        doneb.pack_start(exportb)
        cont.add(doneb)

        self.show_all()
        self.format_changed(2)

    def gif(self):
        # GIF save options GUI.
        gift = gtk.Table(2,2)
        self.gifgrayscale = gtk.CheckButton("Convert to Grayscale")
        self.gifinterlace = gtk.CheckButton("Interlace")
        gifcommentl = gtk.Label("Comment:")
        self.gifcomment = gtk.Entry(256)
        gift.attach(self.gifgrayscale, 0,2,0,1)
        gift.attach(self.gifinterlace, 0,2,1,2)
        return gift

    def jpg(self):
        # JPEG save options GUI.
        jpgt = gtk.Table(8,2)
        jpgqualityl = gtk.Label("Quality:")
        jpgqualitya = gtk.Adjustment(85, 0, 100, 1, 10, 10)
        self.jpgquality = gtk.HScale(jpgqualitya)
        self.jpgquality.set_digits(0)
        jpgsmoothingl = gtk.Label("Smoothing:")
        jpgsmoothinga = gtk.Adjustment(0.00, 0.00, 1.00, 0.01, 0.1, 0.1)
        self.jpgsmoothing = gtk.HScale(jpgsmoothinga)
        self.jpgsmoothing.set_digits(2)
        self.jpgoptimize = gtk.CheckButton("Optimize")
        self.jpgoptimize.set_active(True)
        self.jpgprogressive = gtk.CheckButton("Progressive")
        self.jpgrestart = gtk.CheckButton("Restart Markers")
        self.jpgrestart.connect("clicked", self.jpgrestartchecked)
        jpgfreql = gtk.Label("Marker Frequency:")
        jpgfreqa = gtk.Adjustment(1, 1, 64, 1)
        self.jpgfreq = gtk.SpinButton(jpgfreqa)
        self.jpgfreq.set_sensitive(False)
        jpgsubl = gtk.Label("Subsampling:")
        jpgsubls = gtk.ListStore(gobject.TYPE_STRING)
        jpgsubos = [ "1x1,1x1,1x1 (best quality)", "2x1,1x1,1x1 (4:2:2)", "1x2,1x1,1x1", "2x2,1x1,1x1 (smallest file)" ]
        for jpgsubo in jpgsubos:
            jpgsubls.append([jpgsubo])
        jpgsubc = gtk.CellRendererText()
        self.jpgsub = gtk.ComboBox(jpgsubls)
        self.jpgsub.pack_start(jpgsubc, True)
        self.jpgsub.add_attribute(jpgsubc, 'text', 0)
        self.jpgsub.set_active(3)
        jpgdctl = gtk.Label("DCT Method:")
        jpgdctls = gtk.ListStore(gobject.TYPE_STRING)
        jpgdctos = [ "Float Integer", "Integer", "Floating-Point" ]
        for jpgdcto in jpgdctos:
            jpgdctls.append([jpgdcto])
        jpgdctc = gtk.CellRendererText()
        self.jpgdct = gtk.ComboBox(jpgdctls)
        self.jpgdct.pack_start(jpgdctc, True)
        self.jpgdct.add_attribute(jpgdctc, 'text', 0)
        self.jpgdct.set_active(1)
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
        return jpgt

    def jpgrestartchecked(self, restartcheckbox):
        # JPG restart has been checked.
        if restartcheckbox.get_active():
            self.jpgfreq.set_sensitive(True)
        else:
            self.jpgfreq.set_sensitive(False)

    def png(self):
        # PNG save options GUI.
        pngt = gtk.Table(8,2)
        self.pnginterlacing = gtk.CheckButton("Interlacing (Adam7)")
        self.pngbgcolor = gtk.CheckButton("Save background color")
        self.pnggamma = gtk.CheckButton("Save gamma")
        self.pnglayeroffset = gtk.CheckButton("Save layer offset")
        self.pngresolution = gtk.CheckButton("Save resolution")
        self.pngresolution.set_active(True)
        self.pngcreationtime = gtk.CheckButton("Save creation time")
        self.pngcreationtime.set_active(True)
        self.pngcoloroftransp = gtk.CheckButton("Save color values from transparent pixels")
        pngcompressl = gtk.Label("Compression level:")
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
        tifframel = gtk.Label("<b>Compression</b>")
        tifframel.set_use_markup(True)
        tifframe.set_label_widget(tifframel)
        tifvbox = gtk.VBox(False, 5)
        tifframe.add(tifvbox)
        self.tifnone = gtk.RadioButton(None, "None")
        tifvbox.pack_start(self.tifnone)
        self.tiflzw = gtk.RadioButton(self.tifnone, "LZW")
        tifvbox.pack_start(self.tiflzw)
        self.tifpackbits = gtk.RadioButton(self.tifnone, "Pack Bits")
        tifvbox.pack_start(self.tifpackbits)
        self.tifdeflate = gtk.RadioButton(self.tifnone, "Deflate")
        tifvbox.pack_start(self.tifdeflate)
        self.tifjpeg = gtk.RadioButton(self.tifnone, "JPEG")
        tifvbox.pack_start(self.tifjpeg)
        self.tifcoloroftransp = gtk.CheckButton("Save color values from transparent pixels")
        tift.attach(tifframe, 0,2,0,1)
        tift.attach(self.tifcoloroftransp, 0,2,1,2)
        return tift
        

    def toggle_resize(self, sizetb):
        # Enable/disable the image resize frame
        if sizetb.get_active():
            self.sizef.set_sensitive(True)
        else:
            self.sizef.set_sensitive(False)

    def toggle_crop(self, croptb):
        # Enable/disable the image resize frame
        if croptb.get_active():
            self.cropf.set_sensitive(True)
        else:
            self.cropf.set_sensitive(False)

    def name_option_changed(self, namem):
        # Enable entry field if name option is set to custom.
        if namem.get_active() == 3:
            self.namee.set_sensitive(True)
        else:
            self.namee.set_sensitive(False)

    def format_changed(self, formatm):
        # Enable/disable relevant file format options.
        ext = self.main.book.format_index_to_extension(self.formatm.get_active())
        self.gift.hide()
        self.jpgt.hide()
        self.pngt.hide()
        self.tift.hide()
        if ext == "gif":
            self.gift.show()
        elif ext == "jpg":
            self.jpgt.show()
        elif ext == "png":
            self.pngt.show()
        elif ext == "tif":
            self.tift.show()

    def export(self, button):
        # Pass self to Book, and tell it to export.
        outfolder = os.path.join(self.destb.get_filename(), self.main.book.bookname)
        if os.path.isdir(outfolder):
            overwrite = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, '"%s" exists, do you want to overwrite it?' % (outfolder))
            response = overwrite.run()
            if response == gtk.RESPONSE_YES:
                self.main.book.export_book(self)
                self.close(button)
            overwrite.destroy()
        else:
            self.main.book.export_book(self)
            self.close(button)

    def close(self, button):
        # Close this window
        self.destroy()


class Book():
    # Stores and manages the data for the book.
    def __init__(self):
        # Defines basic variables to store.
        # pagestore columns = pagenmae, thumb Pixbuf, thumb path, thumb mtime
        self.pagestore = gtk.ListStore(str, gtk.gdk.Pixbuf, str, str)
        self.bookfile = ""  # The *.book for this book.
        self.bookname = ""  # The name of the book.
        self.pagepath = ""  # Path to the "pages" subfolder.
        self.trashpath = "" # Path to trash folder.
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
        if os.path.exists(bookfile):
            self.bookfile = bookfile
            self.bookname = os.path.splitext(os.path.basename(self.bookfile))[0]
            bookpath = os.path.dirname(self.bookfile)
            self.pagepath = os.path.join(bookpath, "pages")
            self.trashpath = os.path.join(bookpath, "trash")
            # Load the pages.
            f = open(self.bookfile, "r")
            metatext = f.read()
            metadata = json.loads(metatext)
            f.close()
            for p in metadata['pages']:
                # Create a page object, and add to a list.
                thumb = Thumb(os.path.join(self.pagepath, p))
                self.pagestore.append((p, thumb.thumbpix, thumb.path, thumb.mtime))
            self.pagestore.connect("row-deleted", self.row_deleted)
            self.pagestore.connect("row-inserted", self.row_inserted)
            self.pagestore.connect("row-changed", self.row_changed)
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
        savetofile = json.dumps({ 'pages': metadata }, indent=4)
        bookfile = open(self.bookfile, "w")
        bookfile.write(savetofile)
        bookfile.close()

    def add_page(self, p, dest):
        # Copy the template to a new page.
        try:
            p = p+".xcf"
            unique = True
            for a in self.pagestore:
                if a[0] == p:
                    unique = False
            if unique:
                template = os.path.join(self.pagepath, self.pagestore[0][0])
                shutil.copy(template, os.path.join(self.pagepath, p))
                thumb = Thumb(os.path.join(self.pagepath, p))
                self.pagestore.insert(dest, ( p, thumb.thumbpix, thumb.path, thumb.mtime))
                return True
            else:
                show_error_msg("Page names must be unique")
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
                    shutil.move(os.path.join(self.pagepath, self.pagestore[self.selected][0]), os.path.join(self.pagepath, p))
                    thumb = Thumb(os.path.join(self.pagepath,p))
                    self.pagestore[self.selected] = ((p, thumb.thumbpix, thumb.path, thumb.mtime))
                    return True
                except Exception, err:
                    show_error_msg(err)
            else:
                show_error_msg("Page names must be unique")
            
    def delete_page(self):
        # Delete the selected page.
        try:
            p = self.pagestore[self.selected][0]
            shutil.move(os.path.join(self.pagepath, p), os.path.join(self.trashpath,strftime("%Y%m%d_%H%M%S_")+p))
            piter = self.pagestore.get_iter_from_string(str(self.selected))
            self.pagestore.remove(piter)
            return True
        except Exception, err:
            show_error_msg(err)

    def format_index_to_extension(self, formati):
        # Convert the format index to an extension.
        if formati == 0: # GIF
            return "gif"
        elif formati == 1: # XCF
            return "xcf"
        elif formati == 2: # JPEG
            return "jpg"
        elif formati == 3: # PNG
            return "png"
        elif formati == 4: # TIFF
            return "tif"
        else:
            show_error_msg("Format index out of range")


    def export_book(self, expwin):
        # Export the entire book.
        outfolder = os.path.join(expwin.destb.get_filename(), self.bookname)
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
        # Find file extension.
        ext = self.format_index_to_extension(expwin.formatm.get_active())
        # Loop through pages
        for i,p in enumerate(self.pagestore):
            # Figure out the page name.
            original = os.path.join(self.pagepath, p[0])
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
            # Process image.
            img = pdb.gimp_file_load(original, original)
            img.flatten()
            if expwin.enablescaletb.get_active():
                scale = expwin.sizesb.get_value() / 100
                w = img.width
                h = img.height
                nw = int(scale * w)
                nh = int(scale * h)
                print "Scaling page %s" % (p)
                # img.resize(nw, nh, 0, 0)
            if expwin.enablecroptb.get_active():
                # Run crop code.
                print "Cropping page %s" % (p)
            # Save the image.
            drw = pdb.gimp_image_get_active_layer(img)
            if ext == "gif":
                # Convert to grayscale
                if expwin.gifgrayscale.get_active():
                    pdb.gimp_image_convert_grayscale(img)
                # TODO! Images need to be converted to indexed color first, and more options are needed. :(
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
                                   expwin.comment.get_text(),
                                   expwin.jpgsub.get_active(),
                                   0,
                                   restartfreq,
                                   expwin.jpgdct.get_active())
            elif ext == "tif":
                pass
            pdb.gimp_image_delete(img)

    def update_thumbs(self):
        # Update all thumbnails that have changed.
        for i,p in enumerate(self.pagestore):
            if p[0]:
                if not str(os.stat(p[2]).st_mtime) == p[3]:
                    thumb = Thumb(os.path.join(self.pagepath,p[0]))
                    self.pagestore[i] = ((p[0], thumb.thumbpix, thumb.path, thumb.mtime))


class Main(gtk.Window):
    # Builds a GTK windows for managing the pages of a book.
    def __init__ (self):
        window = super(Main, self).__init__()
        self.set_title("Book")
        self.set_size_request(600, 600)
        self.set_position(gtk.WIN_POS_CENTER)
        self.loaded = False  # If there is a book loaded in the interface.
        self.connect('notify::is-active', self.update_thumbs)

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

        self.file_export = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        self.file_export.set_label("Export Book...")
        key, mod = gtk.accelerator_parse("<Control>E")
        self.file_export.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.file_export.connect("activate", self.export_win)
        self.file_export.set_sensitive(False)
        filemenu.append(self.file_export)

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
        self.add_page = gtk.ToolButton(gtk.STOCK_NEW)
        self.add_page.connect("clicked", self.ask_add_page)
        self.add_page.set_sensitive(False)
        self.add_page.set_tooltip_text("Add a new page.")
        self.del_page = gtk.ToolButton(gtk.STOCK_DELETE)
        self.del_page.connect("clicked", self.ask_delete_page)
        self.del_page.set_sensitive(False)
        self.del_page.set_tooltip_text("Delete the selected page.")
        self.ren_page = gtk.ToolButton(gtk.STOCK_PROPERTIES)
        self.ren_page.connect("clicked", self.ask_rename_page)
        self.ren_page.set_sensitive(False)
        self.ren_page.set_tooltip_text("Rename the selected page.")
        toolbar.insert(self.add_page, 0)
        toolbar.insert(self.del_page, 1)
        toolbar.insert(self.ren_page, 2)

        self.vbox = gtk.VBox(False, 2)
        self.vbox.pack_start(mb, False, False, 0)
        self.vbox.pack_start(toolbar, False, False, 0)

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
        
        self.add(self.vbox)
        self.connect("destroy", gtk.main_quit)
        self.show_all()
        return window    

    def update_thumbs(self, widget, arg):
        # Tell Book to update the thumbnails on window receiving focus.
        if self.is_active() and self.loaded:
            self.book.update_thumbs()

    def new_book(self, widget):
        # Helper for opening up the New Book window.
        self.close_book()
        nb = NewBookWin(self)

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
            self.book = Book()
            self.book.load_book(o.get_filename())
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
        self.thumbs.set_model(self.book.pagestore)
        self.set_title("GIMP Book - %s" % (self.book.bookname))
        self.show_all()
        
    def export_win(self, widget):
        # Settings for exporting the book.
        exportWin = ExportWin(self)

    def select_page(self, thumbs):
        # A page has been selected.
        if self.thumbs.get_selected_items():
            self.book.selected = self.thumbs.get_selected_items()[0][0]
        else:
            self.book.selected = -1

    def ask_add_page(self, widget):
        # Add a new page to the current book.
        dest = self.book.selected
        if self.book.selected < 1:
            dest = len(self.book.pagestore)
        if self.loaded:
            response, text = self.name_dialog("Add a Page", "Enter Page Description: ")
            if response == gtk.RESPONSE_ACCEPT:
                if text:
                    self.book.add_page(text, dest)
                else:
                    show_error_msg("No page name entered.")
        else:
            show_error_msg("You need to create or load a book, before adding pages to it.")

    def ask_rename_page(self, widget):
        # Rename the selected page.
        if self.book.selected > -1:
            response, text = self.name_dialog("Rename Page", "Ente Page Description: ")
            if response == gtk.RESPONSE_ACCEPT:
                if text:
                    self.book.rename_page(text)

    def ask_delete_page(self, widget):
        # Delete the selected page.
        areyousure = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, 'Delete page "%s"?' % (self.book.pagestore[self.book.selected][0]))
        response = areyousure.run()
        if response == gtk.RESPONSE_YES:
            self.book.delete_page()
            areyousure.destroy()

    def name_dialog(self, title, label):
        # Dialog for entering page names.
        # TODO! Show message on illegal characters and duplicate file creation.
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

    def enable_controls(self):
        # Enable the controles that are disabled when no book is loaded.
        self.add_page.set_sensitive(True)
        self.del_page.set_sensitive(True)
        self.ren_page.set_sensitive(True)
        self.file_export.set_sensitive(True)

    def show_progress(self):
        # Add a progress bar to the bottom of the window.
        self.progress = gtk.ProgressBar()
        self.progress.size_allocate(gtk.gdk.Rectangle(0, 0, 200, 5))
        self.progress.queue_resize()
        self.vbox.pack_end(self.progress)

    def remove_progress(self):
        self.progress.destroy()

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
