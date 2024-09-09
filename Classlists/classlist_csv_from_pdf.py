#!/usr/bin/env python3

# run these first:
#ll python3-pip
# pip install tika
# pip install pandas

from tika import parser
import pandas as pd
import re

# Crosslists (course number in key actually points to class in value)
crosslists = {
    "CEG 5350": "CEG 4350",
    "CEG 6424": "CEG 4424",
    "EE 2011": "EE 2010",
    "EE 4910": "CEG 4980",
    "EE 4920": "CEG 4981",
    "EE 7840": "CEG 7550",
}

if __name__ == '__main__':
    text = parser.from_file('Look_Up_Classes.pdf')['content']
    # In order to get the PDF you must zoom out to 20% while printing the page
    # This ensures the all the data is on one line and it can be parsed correctly

    # Split text into groups separated by new lines
    # In the PDF, this manifests as different blocks of columns
    # Ex (where '---' denotes a break between groups):
    # C 73057 CEG 2350 01 Dayton 4.000 Operating System
    # Concepts and Usage
    # ---
    # TR 09:30
    # am-10:50
    # am
    # ---
    # 60 60 0 20 3 17 0 0 0 Kayleigh Elizabeth
    # Duncan (P)
    # ---
    sections = text.split('\n\n')

    # Find sections that contain class names
    class_rows = []
    for section in sections:
        # If the select column has nothing in it
        match = re.search(r'^\d{5}\s', section)

        # Select Column: Select the box in front of the CRN then choose Register or Add to Worksheet. You may see the following in place of the box. A blank means already registered, C means a
        # closed class, NR means not available for registration and SR means a student restriction (i.e. time ticket has not started, holds, or academic standing restrictions).
        if section.startswith('C ') or section.startswith('NR ') or section.startswith('SR ') or match:
            class_rows.append(section)


    # Get list of classes (number, name)
    classes = []
    for row in class_rows:
        if row.startswith('C ') or row.startswith('NR ') or row.startswith('SR '):
            class_department = row.split(' ')[2]
            class_number = row.split(' ')[3]
            class_name = ''
            for word in row.split(' ')[7:]:
                
                if word in {'M', 'T', 'W', 'R', 'F', 'MW', 'MF', 'WF', 'MWF', 'TR', 'MTWR'} or word[0].isdigit():
                    break
                else:
                    class_name += word.strip() + ' '
            class_name = class_name.strip().replace('\n', ' ')
        # If the select row has nothing in it set everything back one
        else:
            class_department = row.split(' ')[1]
            class_number = row.split(' ')[2]
            class_name = ''
            for word in row.split(' ')[6:]:
                if word in {'M', 'T', 'W', 'R', 'F', 'MW', 'MF', 'WF', 'MWF', 'TR', 'MTWR'} or word[0].isdigit():
                    break
                else:
                    # print(word)
                    class_name += word.strip() + ' '
            class_name = class_name.strip().replace('\n', ' ')

        # If not a lab or recitation
        if not any(x in ['L', 'R'] for x in class_number[-1]):
            # If not a reserved category
            if not any(x in class_name for x in ['Independent Study', 'Thesis', 'PhD Dissertation', 'HON', 'CPT', 'Internship']):
                # If not already added to classes
                if (class_department, class_number, class_name) not in classes:
                    # Add to class
                    classes.append((class_department, class_number, class_name))

    # Create CSV as PD dataframes
    df = pd.DataFrame(classes, columns=('department', 'number', 'name'))
    df['text'] = ''
    df['emoji'] = ''
    df['role/link'] = ''
    df['long_name'] = ''
    df['create_channels'] = ''

    for i, row in df.iterrows():
        row['text'] = row['department'].upper() + ' ' + row['number']
        row['role/link'] = row['text']
        row['long_name'] = row['name']
        lowercase_number = row['text'].replace(' ', '').lower()
        row['create_channels'] = f'#{lowercase_number},0#Student Voice,2#TA Voice'
        
        # If class crosslisted
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
                if 'microprocessor-based' in row['long_name'].lower():
                    print(row['long_name'].lower(), '|', name.lower(), row['long_name'].lower() == name.lower())
                if first_occurance is not None and row['long_name'].lower() == name.lower():
                    row['role/link'] = first_occurance['role/link']
                    row['create_channels'] = ''

                if row['long_name'].lower() == name.lower():
                    first_occurance = row

    # Drop original columns
    df = df.drop(['department', 'number', 'name'], axis=1)

    # Save to classlist
    df.to_csv('classlist.csv', index=False)
