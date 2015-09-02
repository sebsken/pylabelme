#
# Copyright (C) 2011 Michael Pitidis, Hussein Abdulwahid, Sebastien Eskenazi.
#
# This file is part of Labelme.
#
# Labelme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Labelme is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labelme.  If not, see <http://www.gnu.org/licenses/>.
#

import json
import os.path
import sys

from base64 import b64encode, b64decode
from lxml import etree


ns={"Pns":"http://schema.primaresearch.org/PAGE/gts/pagecontent/2010-03-19"}

class LabelFileError(Exception):
    pass

class LabelFile(object):
    suffix=['.xml', '.lif'] #order matters !
    suffix1 = 'lif'
    suffix2 = 'xml'
    #the xml files that are ahndled are only the ones respecting the PAGE format
    #(http://schema.primaresearch.org/PAGE/gts/pagecontent/2010-03-19)

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.tree=None
        # self.imageData = None
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        if os.path.splitext(filename)[1].lower().split('.')[-1] == LabelFile.suffix1:
            try:
                with open(filename, 'rb') as f:
                    data = json.load(f)
                    imagePath = data['imagePath']
                    # imageData = b64decode(data['imageData'])
                    lineColor = data['lineColor']
                    fillColor = data['fillColor']
                    shapes = ((s['label'], s['points'], s['line_color'], s['fill_color'])\
                            for s in data['shapes'])
                    # Only replace data after everything is loaded.
                    self.shapes = shapes
                    self.imagePath = imagePath
                    # self.imageData = imageData
                    self.lineColor = lineColor
                    self.fillColor = fillColor
            except Exception, e:
                raise LabelFileError(e)
        else:
            try:
                tree = etree.parse(filename)
                PcGts = tree.getroot()
                if not (PcGts.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation']==\
                        "http://schema.primaresearch.org/PAGE/gts/pagecontent/2010-03-19 http://schema.primaresearch.org/PAGE/gts/pagecontent/2010-03-19/pagecontent.xsd"):
                    raise LabelFileError('Wrong xml schema. Only PAGE format xml files are accepted.\
                            See http://schema.primaresearch.org for more information.')
                Page = PcGts.find("Pns:Page", ns)
                imagePath = Page.get("imageFilename")
                # imageData = b64decode(data['imageData'])
                lineColor = [0, 255, 0, 128]
                fillColor = [255, 0, 0, 128]
                shapes1=[]
                for child in Page.find("."):
                    #print(child)
                    label=child.tag+"[@id='"+child.get("id")+"']"
                    points=[]
                    for p in child.findall('.//Pns:Coords//Pns:Point', ns):
                        points.append([float(p.get('x')), float(p.get('y'))])
                    shapes1.append({'label':label, 'points':points, 'line_color':lineColor, 'fill_color':fillColor})
                shapes = ((s['label'], s['points'], s['line_color'], s['fill_color']) for s in shapes1)
                # Only replace data after everything is loaded.
                self.tree=tree
                self.shapes = shapes
                self.imagePath = imagePath
                # self.imageData = imageData
                self.lineColor = lineColor
                self.fillColor = fillColor
            except Exception, e:
                raise LabelFileError(e)

    def save(self, filename, shapes, imagePath, imageData,
            lineColor=None, fillColor=None):
        if os.path.splitext(filename)[1].lower().split('.')[-1] == LabelFile.suffix1:
            try:
                with open(filename, 'wb') as f:
                    json.dump(dict(
                        shapes=shapes,
                        lineColor=lineColor, fillColor=fillColor,
                        imagePath=imagePath),
                        # imageData=b64encode(imageData)),
                        f, ensure_ascii=True, indent=2)
            except Exception, e:
                raise LabelFileError(e)
        elif self.tree is None:
            raise LabelFileError('No xml file loaded. Either open one or save as .lif/json file.')
        else:
            try:
                with open('.'.join(filename.split('.')[:-1])+'.lif', 'wb') as flif:
                    json.dump(dict(
                        shapes=shapes,
                        lineColor=lineColor, fillColor=fillColor,
                        imagePath=imagePath),
                        # imageData=b64encode(imageData)),
                        flif, ensure_ascii=True, indent=2)
            except Exception, e:
                raise LabelFileError(e)
            try:
                for shape in shapes:
                    coords=self.tree.find('//Pns:Page//'+shape['label']+'//Pns:Coords', ns)
                    #print (shape['label'])
                    coords.clear()
                    for p in shape['points']:
                        point=etree.SubElement(coords,'Point')
                        point.set('x',str(p[0]))
                        point.set('y',str(p[1]))
                        
                    #print(region.findall('.//'))
                self.tree.write(filename)
                        
            except Exception, e:
                raise LabelFileError(e)

    @staticmethod
    def isLabelFile(filename):
        return os.path.splitext(filename)[1].lower().split('.')[-1] == LabelFile.suffix1 or os.path.splitext(filename)[1].lower().split('.')[-1] == LabelFile.suffix2