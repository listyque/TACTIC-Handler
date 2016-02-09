from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

# from bs4 import BeautifulSoup

import re

def currentHyperlink(cursor):

    # Select current word
    cursor.select(QtGui.QTextCursor.WordUnderCursor)

    # Parse html of selection
    # soup = BeautifulSoup(cursor.selection().toHtml())
    
    # Grab <a> tag
    # a = soup.a

    # Try to find and return a link, else None
    # return a.get("href") if a else None
    return 'Assa'
    
def openHyperlink(hyperlink):

    # Parse link
    link = QtCore.QUrl().fromUserInput(hyperlink)
    
    # Open url in default browser
    QtGui.QDesktopServices.openUrl(link)

def removeHyperlink(cursor):

    # This function is called when the url is already selected
    # so we can get the selected text right away
    text = cursor.selectedText()

    # Replace hyperlink with the unformatted text
    cursor.insertText(text,QtGui.QTextCharFormat())

class Link(QtGui.QDialog):
    
    def __init__(self, parent = None, forEditing = False):

        QtGui.QDialog.__init__(self,parent)

        self.parent = parent

        self.cursor = self.parent.text.textCursor()

        self.forEditing = forEditing

        self.initUI()

    def initUI(self):

        # Label and LineEdit for Hyperlink
        urlLabel = QtGui.QLabel("Hyperlink to:",self)
        
        self.urlField = QtGui.QLineEdit(self)

        # Label and LineEdit for text field (to display link as)
        textLabel = QtGui.QLabel("Display as: ",self)

        self.textField = QtGui.QLineEdit(self)

        if self.forEditing:

            # Set url to current link if for editing
            self.urlField.setText(currentHyperlink(self.cursor))

            # And fill the text field with the current selection
            self.textField.setText(self.cursor.selectedText())

        else:
            
            # Set current selection as URL (if any, else empty string)
            self.urlField.setText(self.cursor.selectedText())

        # Button for inserting link
        insertButton = QtGui.QPushButton("Insert",self)
        insertButton.clicked.connect(self.insert)

        # Layout
        layout = QtGui.QGridLayout()

        layout.addWidget(urlLabel,0,0)
        layout.addWidget(self.urlField,0,1)

        layout.addWidget(textLabel,1,0)
        layout.addWidget(self.textField,1,1)

        layout.addWidget(insertButton,2,0,1,2)

        self.setLayout(layout)

        # Set fixed size (no resizing possible)
        self.setFixedSize(300,150)
        self.move(500,500)
        
        self.setWindowTitle("Insert hyperlink")

    def insert(self):

        # Get text from LineEdits and make use of QUrl's
        # parsing (e.g. add http:// if necessary)
        url = QtCore.QUrl().fromUserInput(self.urlField.text())

        text = self.textField.text()

        # HTML link (convert url back to parsed url string)
        link = "<a href=\"{}\">{}</a>".format(url.toString(),text)

        # If we need to remove the word beneath
        if self.forEditing:

            # Select the word
            self.cursor.select(QtGui.QTextCursor.WordUnderCursor)

            # Remove it
            self.cursor.removeSelectedText()
        
        # Insert this link
        self.cursor.insertHtml(link)

        # Close window after
        self.close()
