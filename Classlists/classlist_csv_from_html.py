#!/usr/bin/env python3

# pip install pandas
# pip install beautifulsoup4

from bs4 import BeautifulSoup
import pandas as pd
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
        if len(cells) != 0:
            # Set class information needed
            class_department = cells[2].get_text(strip=True)
            class_number = cells[3].get_text(strip=True)
            class_name = cells[7].get_text(strip=True).replace('\n', ' ')

            # If class isn't already added, isn't a lab or recitation, and doesn't contain a forbidden word, add to list
            if (class_department, class_number, class_name) not in classes and not any(x in ['L', 'R'] for x in class_number[-1]) and not any(x in class_name for x in forbidden):
                classes.append((class_department, class_number, class_name))

    # Create CSV as PD dataframes
    df = pd.DataFrame(classes, columns=('department', 'number', 'name'))
    df['text'] = ''
    df['emoji'] = ''
    df['role/link'] = ''
    df['long_name'] = ''
    df['create_channels'] = ''
    
    # Loop through each class
    for i, row in df.iterrows():
        # Set class name to follow ([A-Z]{3} [0-9]{3})
        row['text'] = row['department'].upper() + ' ' + row['number']

        # Set role name
        row['role/link'] = row['text']

        # Set full class name
        row['long_name'] = row['name']
        
        # Get class in lowercase number
        lowercase_number = row['text'].replace(' ', '').lower()

        # Set channels to create
        row['create_channels'] = f'#{lowercase_number},0#Student Voice,2#TA Voice'
        
        # If class marked manually as crosslisted
        if row['text'] in crosslists:
            # Set role/link to be crosslisted class
            row['role/link'] = crosslists[row['text']]

            # Don't create any new channels
            row['create_channels'] = ''

    # Handle duplicate class numbers
    text_occurances = df.groupby(['text']).size()
    for class_number, count in text_occurances.items():
        if count > 1:
            for i, row in df.iterrows():
                if row['text'].lower() == class_number.lower():
                    row['text'] = row['text'] + ' (' + row['name'] + ')'
                    row['role/link'] = row['text']
                    text_channel_name = ('-'.join(row['role/link'].lower().replace('(', ' ').replace(')', ' ').strip().split(' '))).replace('--', '-')
                    row['create_channels'] = f'#{text_channel_name},0#Student Voice,2#TA Voice'

    # Handle cross lists
    name_occurances = df.groupby(['long_name']).size()
    for name, count in name_occurances.items():
        if count > 1:
            # Get first occurance of name
            first_occurance = None
            for i, row in df.iterrows():
                # If first occurance found and currently on future occurance
                # if 'microprocessor-based' in row['long_name'].lower():
                    # print(row['long_name'].lower(), '|', name.lower(), row['long_name'].lower() == name.lower())
                if first_occurance is not None and row['long_name'].lower() == name.lower():
                    row['role/link'] = first_occurance['role/link']
                    row['create_channels'] = ''

                if row['long_name'].lower() == name.lower():
                    first_occurance = row

    # Drop original columns
    df = df.drop(['department', 'number', 'name'], axis=1)

    # Save to classlist
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classlist.csv'), index=False)