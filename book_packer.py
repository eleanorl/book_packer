import re
import glob
import sys
import bisect

class Book:
	#This represents a single book
	def printbook(self,f,last):
		#Writes attributes of the book to a JSON file with appropriate formatting
		#Leaves fields blank if they have not been attained
		f.write('\t\t\t\t{\n')
		f.write('\t\t\t\t\t"title": "'+self.title+'",\n')
		f.write('\t\t\t\t\t"author": "'+self.author+'",\n')
		f.write('\t\t\t\t\t"price": "'+self.price+' USD",\n')
		f.write('\t\t\t\t\t"shipping_weight": "'+str(self.weight)+' pounds'+'",\n')
		f.write('\t\t\t\t\t"isbn-10": "'+self.isbn+'"\n')
		if(last==True):
			f.write('\t\t\t\t}\n')
		else:
			f.write('\t\t\t\t},\n')
	def __init__(self,url):
		#Scrapes an html page for book attributes
		#Initialize all attributes to blank
		self.title=''
		self.author=''
		self.editor=''
		self.price=''
		self.weight=-1
		self.isbn=''
		f=open(url,'r')
		#Scan through each line until it finds something with relevant information using Regex
		for line in f:
			if(self.title==''):
				m=re.match('.*"btAsinTitle"  >(.*) <',line)
				if(m!=None):
					self.title=m.group(1).split('<')[0]
					continue
			if(self.author==''):
				m=re.match('.*>(.*)</a.*Author.*',line)
				if(m!=None):
					a=line.split('</a>')
					for i in a[0:-1]:
						self.author=self.author+(i.split('>')[-1]+', ')
					self.author=self.author[0:-2]
					continue
				#Some books don't have author listed, use editor instead
				m=re.match('.*>(.*)</a.*Editor.*',line)
				if(m!=None):
					a=line.split('</a>')
					for i in a[0:-1]:
						self.author=self.author+(i.split('>')[-1]+', ')
					self.author=self.author[0:-2]
					continue
			if(self.price==''):
				m=re.match('.*"priceLarge">(.*)</b></span>',line)
				if(m!=None):
					self.price=m.group(1)
					continue
				#Some pages are formatted slightly differently for Price
				m=re.match('.*price bxgy-item-price">(.*)</span><span class="price">',line)
				if(m!=None):
					self.price=m.group(1)
					continue
			if(self.weight==-1):		
				m=re.match('.*Shipping Weight:</b> (.*) pound.*',line)
				if(m!=None):
					self.weight=float(m.group(1))
					continue
			if(self.isbn==''):		
				m=re.match('.*ISBN-10:</b> (.*)</li>',line)
				if(m!=None):
					self.isbn=m.group(1)
					continue
class Library:
	#This represents a collection of books
	def __init__(self):
		#Initializing with no books
		self.nbooks=0
		self.booklist=[]
	def addbook(self,book):
		#Adds a book to the collection
		self.nbooks=self.nbooks+1
		self.booklist.append(book)
	def printlibrary(self,f):
		#Print all books in the collection to JSON file with appropriate formatting
		f.write('\t\t\t"contents": [\n')
		for i in self.booklist[0:-1]:
			i.printbook(f,False);
		self.booklist[-1].printbook(f,True)
		f.write('\t\t\t]\n')
	def sortbyweight(self):
		#Sort the collection of books by decreasing weight
		self.booklist.sort(key=lambda x: x.weight,reverse=True)
class Box:
	#This represents a packing box, with a collection of books inside
	def __init__(self,ID):
		#Initialing to an empty box with no books
		self.lib=Library()
		self.weight=0.0
		self.id=ID
	def addbook(self,book):
		#Add a book to the box, increment weight
		self.lib.addbook(book)
		self.weight=self.weight+book.weight
	def printbox(self,f,last):
		#Write the attributes and content of the box a JSON file, with appropriate formatting
		f.write('\t\t{\n')
		f.write('\t\t\t"id": '+str(self.id)+',\n')
		f.write('\t\t\t"totalWeight": "'+str(self.weight)+' pounds",\n')
		self.lib.printlibrary(f)
		if(last==True):
			f.write('\t\t}\n')
		else:
			f.write('\t\t},\n')
class Boxes:
	#This is the collection of all boxes
	def __init__(self,maxweight):
		#initialize with one empty box
		self.boxlist=[Box(0)]
		self.nboxes=1
		#weight remaining in boxes
		self.remain=[maxweight]
	def addbox(self,maxweight):
		#Add an empty box
		self.boxlist.append(Box(0))
		self.nboxes=self.nboxes+1
		self.remain.append(maxweight)
	def addbook(self,book,max_weight):
		#This uses the Best Fit Decrease Algorithm
		#Boxes remain in Decreasing weight order
		#Use bisection to locate where to insert new book
		i=bisect.bisect_left(self.remain,book.weight)
		if(i>=self.nboxes):
			self.addbox(max_weight)
		self.boxlist[i].addbook(book)
		self.remain[i]=self.remain[i]-book.weight
		#resort using bisection
		j=bisect.bisect_left(self.remain[0:i],self.remain[i])
		self.remain=self.remain[0:j]+[self.remain[i]]+self.remain[j:i]+self.remain[i+1:]
		self.boxlist=self.boxlist[0:j]+[self.boxlist[i]]+self.boxlist[j:i]+self.boxlist[i+1:]
	def printboxes(self,f):
		#Write the content each box to a JSON file, with appropriate formatting
		f.write('{\n')
		f.write('\t"Boxes": [\n')
		for i in self.boxlist[0:-1]:
			i.printbox(f,False)
		self.boxlist[-1].printbox(f,True)
		f.write('\t]\n')
		f.write('}\n')
	def assignids(self):
		for i in range(0,self.nboxes):
			self.boxlist[i].id=i+1

#This is the Maximum weight for the boxes, can be simply changed if need be.
max_weight=10.0
#Oupt file
f = open('packing_list.JSON', 'w')
#Library of all books from html files
allBooks=Library()
for i in glob.glob("./data/*.html"):
	#Create new Book object from file
	newbook=Book(i)
	#Check if it's overweight
	if newbook.weight>max_weight:
		print('Warning: "' + newbook.title +'" is over '+str(max_weight)+' pound weight limit and cannot be packed.  We will attempt to pack the rest of the books.')
	else:
		allBooks.addbook(Book(i))
#Sort Library by weight for best fit decreasing algorithm
allBooks.sortbyweight()
#Initialize collection of boxes
allBoxes=Boxes(max_weight);
#Pack books into boxes in decreasing weight order
for book in allBooks.booklist:
	allBoxes.addbook(book,max_weight)
#Because boxes move around, we only assign ids at the end
allBoxes.assignids()
#Write Packing Slip
allBoxes.printboxes(f)
#Give warning if couldn't pack in N boxes
N=int(sys.argv[1])
if(N<allBoxes.nboxes):
	print('Warning: We packed your books into '+str(allBoxes.nboxes)+' boxes instead of the '+str(N)+' that you requested.')
print('Please see the packing list at packing_list.JSON')