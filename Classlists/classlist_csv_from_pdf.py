#!/usr/bin/env python3

# run these first:
# sudo apt install python3-pip
# pip install pandas

from bs4 import BeautifulSoup
import pandas as pd
import re
import os

# Crosslists (course number in key actually points to class in value)
crosslists = {
    "CEG 5350": "CEG 4350",
    "CEG 6424": "CEG 4424",
    "EE 2011": "EE 2010",
    "EE 4910": "CEG 4980",
    "EE 4920": "CEG 4981",
    "EE 7840": "CEG 7550",
}

# Name in string for classes that should NOT be included (IE: Recitation)
forbidden = {
    "Laboratory",
    "Recitation",
    "Independent Study",
    "Thesis",
    "PhD Dissertation",
    "HON",
    "CPT",
    "Internship",
}

if __name__ == '__main__':
    # Open HTML file in current working directory
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Look Up Classes.html'), 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Put content of HTML file into HTML parser
    parser = BeautifulSoup(html_content, 'html.parser')

    # Find table with classes
    table = parser.find('table', {'class': 'datadisplaytable'})

    # Get list of classes (number, name)
    classes = []
    for row in table.find_all('tr'):
        # Get all table data cells
        cells = row.find_all('td')
        
        # If not in a header row, add class to list
        if len(cells) is not 0:
            print(cells[7].get_text(strip=True))
            break