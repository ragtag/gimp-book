gimp-book
=========
GIMP Book is a script for managing multiple pages in the GIMP, it's great for creating comic books, illustrated books, sketch books or similar. It opens a separete window with thumbnails of all your pages, where you can add, delete, sort and rename them. Once you're done you can export your book to various formats, for web or print.

<p style="text-align: center;">
  <img loading="lazy" class="aligncenter" src="http://ragtag.net/xternal/gimp-book/GIMP%20Book%20-%20interface.jpg" alt="" width="466" height="450" />
</p>

&nbsp;

#### IMPORTANT!

Creating a comic book is a lot of work, work you don't want to loose, so make sure you backup all your files regularly!

## Download

You can download the latest version of [GIMP Book here][1], older versions can be found [here][2]. To see what has changed between versions, look in the [changelog][3].

## Installation

Unzip the .zip file, and copy the content into **/home/your-name/.config/GIMP/2.10/plug-ins** on Linux or **C:\Users\your-name\Appdata\Roaming\GIMP\2.10\plug-ins** in Windows. The next time you start the GIMP, you should find it under the Windows menu. GIMP Book was written for GIMP 2.8 (but should work in 2.6 and 2.10) and Python 2.7. If you're using Python 2.5, you need to install the json module manually.

If you're unsure where GIMP looks for plug-ins, you can go the Edit>Preferences in GIMP, and check the paths under Folders>Plug-ins. Note that the default plug-ins path changed from GIMP 2.8 to 2.10.

Note, I've changed the versioning of GIMP Book to the more standard convention of major.minor.patch as of version 1.0.0. The previous version was 2014.2 rev 82.

## Creating a Book

Begin by opening the GIMP, and the GIMP Book interface from the Windows>Book... menu. You'll be presented with an empty Book window, in which you can choose File>New Book (Ctrl-N).

In the Create a New Book dialog, enter the name of your book and choose a destination folder to save it to. Select the width and height of your book, resolution, if to use color or grayscale, and a background color.

Here you can also define top, bottom and side margin guides, as well as bleed guides. These will create paths in your template page that can be used as a reference when drawing. If you set them to zero, no path are created.

When you're happy with your setting, hit OK, and GIMP Book will create a folder at the chosen destination, with the name of your book, a couple of subfolders and a .book file.

### The Template

After creating a new book, you'll see a Template.xcf thumbnail in your Book window. This is used as a template for all new pages that you add. You can double click it to open it in the GIMP, and make any adjustments to it you like. It's a good idea to spend some time on it, making sure the size and resolution is correct, adding a default set of layers and layergroups, adding guides and any other elements you will need on all the pages of your book. You can adjust the template at any time later, but changes to it will only affect new pages created from that point on, not existing ones.

The template is always shown as the first page of the book. It is numbered as page zero when exporting, and is not exported by default.

## Saving Your Book

There is no need to save your book. When you add pages, move them around, or delete them, GIMP Book saves those changes instantly. The only thing you need to save are the individual .xcf pages, when you work on them in GIMP.

## Opening an Existing Book

To open a book simply choose File>Open Book... from the Book window, and use the standard open dialog to locate your .book file. The book will open in the Book window, and you can start working on it. If thumbnails have not been generated for your book, loading it will take a short while as new thumbnails are generated.

## Managing Pages

### Opening a page

There are several ways to open pages in the GIMP, from GIMP Book. You can double click the page, hit the Return key with the page selected, right click it and choose Open from the pop-up menu or choose Pages>Open from the main menu. Once you're done working on a page, simply save and close it in the GIMP. The pages thumbnail updates as soon as the GIMP Book window receives focus.

### Adding a Page

To add a new page based on your template simply choose Pages>Add (Ctrl+A). You will be asked to give the page a name. Use a unique and descriptive name that helps you identify the page. Pagenumbers are added on export, so you don't need to number your pages, unless you want to. New pages are added to the end of the book, if no page is selected, or at the selected page if one is.

### Duplicating a Page

With a page selected, choose Pages>Duplicate (Ctrl+D). You will be asked to enter a name for the newly created page.

### Renaming a Page

Select the page you want to rename, and choose Pages>Rename (Ctrl+R). Enter a new name, and you're done. Make sure you don't have the page open in the GIMP before renaming it.

### Deleting a Page

To delete a page, simply select the page, and hit the Delete button. You'll be asked to confirm that you really want to delete the page. Make sure you don't have the page open in GIMP, before deleting it.

When you delete a page in GIMP Book, it is not deleted permanently, but moved to your\_book/trash/date\_pagename.xcf, in case you want to get something from it later. You can freely delete the content of your_book/trash, if you want to free up disk space.

### Importing Pages

You can import pages to your book by simply choosing Pages>Import Page(s), and selecting the page(s) you want to import. This can be handy for importing scanned sketches. The pages will show up at the resolution they are in, and will ignore the template you are using. On import they are converted to .xcf files. Importing supports most of the common image file format.

While import does support .svg and .pdf, it does not display any dialog letting you chose what resolution or page to retrive from those file format. If you need to import these formats, you're probably better of importing them manually into the GIMP first, and saving them out as .xcf files, which you can then import into GIMP Book.

Note that you can use the import feature to retrive pages you have previously deleted from you book. You can find these in [your\_book]/trash/[date]\_[pagename].xcf.

### Sorting Pages

To reorder the pages, simply drag them around to where you want them.

## Views

### Stoyboard Mode

Storyboard mode toggles the page view between two column book view, and a flowing storyboard view that fills the width of the Book window. To toggle between the two modes, use the View>Storyboard Mode menu.

### Read from Right to Left

Lists the pages from right to left, rather than left to right. Handy when drawing manga.

### Zoom In/Out

This displays the pages at different zoom level. The first time you zoom in or out, the thumbnails are regenerated at that zoom level, which will take a few seconds, once that is done, switching zoom level should be pretty much instant.

## Exporting Your Book

Once you're finished with your book, you can export it to several different formats. To do this simply choose File>Export Book&#8230; from the menu in the Book window.

### Destination Tab

At the top of the tab, you can choose the name of the folder you want to export your book to. GIMP Book will create a new folder with the name of your book at that destination, and fill it with images in the format you specify.

For naming the pages you can choose between using the name of the book (e.g. 1_My Book.jpg), the name of the pages, simply using page numbers with no name, or using a custom name that you enter in the Custom Name field.

You can choose the page range you wish to export. Page 0 is the template, which you probably don't want to include in your export.

### Layer Tags

Layer tags are used to hide or show tagged layers. It can be used for doing multi-lingual comics, to hide sketch layers, and so on. To tag a layer simply put any tag between square brackets [] in the layer name. For instance "[en] Speech Buble" or "[sketch] Car Chase". Layers can have multiple tags, but if the tags match both hide and show, show wins.

To hide or show layers, simply enter a comma separated list of tags, without the square brackets [], in the appropriate hide or show field (e.g. "en,de,no,sketch"). On export, layers matching the tag will be hidden or shown, before exporting.

For the remining layers, that don't match any tag, you can choose to either leave their visibility as is, hide or show them.

You can tag layer groups too in GIMP 2.7 or later. If you hide a layer group, everything within it will be hidden independently of the tag used on those layers.

### Margins Tab

On export you can change the margins of your pages. This is similar to Canvas Size in GIMP, but uses relative page margins instead of width and height and an offset. Negative values, vill crop the image, while positive will make the canvas bigger. You can choose between using the background color saved in the image, black, white or a custom color, for the background when you make the image bigger.

&nbsp;

### Image Size Tab

The image size tab is basically the same as the standard GIMP one. You can choose width or height, as pixels or percentiles, and choose the interpolation method to use. GIMP Book uses the template for you book, to decide the aspect ratio, when choosing scale values.

### File Format Tab

You can choose to export your book as a sequence of gif, xcf, jpg, ora, psd, png or tiff files. The save options for the different file formats are basically the same as in GIMP. For xcf, ora and psd, you can choose not to flatten the image, keeping layer data intact to work on the files further in other programs such as MyPaint or Krita (both of which support OpenRastar .ora).

When you've chosen all your export options, hit the Export Pages button, and GIMP Book will start processing your pages. This can take a short while, as each page needs to be loaded, possibly modified, and then saved out again.

## GIMP Book in Your Language

GIMP Book is now available in French thanks to Patrick Depoix. On Linux, if your operating system is set to French (i.e. the LANG variable is defined as fr_FR), it will automatically show up in French. Windows unfortunately doesn't set the LANG variable, but if you set it system wide, it should work there too.

If you would like to help out with translations, check out the ReadMe in the locale folder. I appreciate the help.

## Known Bugs & Limitations

  * utf-8 names (i.e. Chinese, Japanese etc) for pages and books do not work properly on Windows.
  * GIMP Book has NOT been tested on OSX, but should work.
  * Import does not yet support any options on importing files such as pdf or svg (resolution, page etc.).

If you find additional bugs, you can register them over at [GitHub][4], or comment below.

## Behind the Scenes

If you just want to use GIMP Book, you can stop reading here. If, on the other hand, you want to know a little bit more about what it does behind the scenes, then keep reading.

### The File Format

GIMP Book stores the pages of your book in a simple file structure that looks like this.

<pre>MyBook/
      |-- MyBook.book
      |-- pages
      |   `-- Template.xcf
      |-- thumbs
      |   `-- 256
      `-- trash</pre>

All your pages and the Template are stored in the pages folder as plain .xcf files. Any pages you delete are moved to the trash folder. The thumbs folder contanis automatically generated thumbnails of your pages, at different sizes. GIMP Book only touches the xcf files on a few occassions, when adding, duplicating, renaming, deleting or importing pages.

### The *.book File

The *.book file, is a simple JSON text file, that contains a list of your pages in the order they are shown. That looks like this:

<pre>{
        "storyboardmode": 1,
        "thumbsize": 256,
        "pages": [
            "template.xcf",
            "Outside the Museum.xcf",
            "Burglar Climbing in Window.xcf",
            "Knocing Out Security Guard.xcf"
        ]
    }</pre>

When you move pages around, all that happens is that the list of pages in the \*.book file is changed. The \*.book file keeps no record of pages that have been deleted. It also tracks your current zoom level (thumbsize), and if storyboardmode is enabled.

Any time you do changes, such as move, rename, add or delete a page, the *.book file is automatically updated.

 [1]: https://ragnarb.com/downloads/gimp-book/gimp_book_1.1.0.zip
 [2]: https://ragnarb.com/downloads/gimp-book/
 [3]: https://ragnarb.com/downloads/gimp-book/changelog.txt
 [4]: https://github.com/ragtag/gimp-book/issues

