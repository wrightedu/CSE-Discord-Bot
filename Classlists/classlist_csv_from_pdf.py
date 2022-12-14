#!/usr/bin/env python
from tika import parser
import pandas as pd

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
                
                if word in {'M', 'T', 'W', 'R', 'F', 'MW', 'MF', 'WF', 'MWF', 'TR'} or word[0].isdigit():
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
                if word in {'M', 'T', 'W', 'R', 'F', 'MW', 'MF', 'WF', 'MWF', 'TR'} or word[0].isdigit():
                    break
                else:
                    # print(word)
                    class_name += word.strip() + ' '
            class_name = class_name.strip().replace('\n', ' ')

        # Add to class list if all the following conditions are true:
        # If not a lab
        if not class_number.endswith('L'):
            # If not a recitation
            if not class_number.endswith('R'):
                # If not an independent study
                if 'Independent Study' not in class_name:
                    # If not a thesis
                    if 'Thesis' not in class_name:
                        # If not a PhD Dissertation or PhD Dissertation Research
                        if 'PhD Dissertation' not in class_name:
                            # If not an honors section of a course:
                            if 'HON' not in class_name:
                                # If not whatever CPT is
                                if 'CPT' not in class_name:
                                    # If not already added
                                    if (class_department, class_number, class_name) not in classes:
                                        classes.append((class_department, class_number, class_name))

    # Create CSV as PD dataframe
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

    # Handle duplicate class numbers
    text_occurances = df.groupby(['text']).size()
    for class_number, count in text_occurances.iteritems():
        if count > 1:
            for i, row in df.iterrows():
                if row['text'].lower() == class_number.lower():
                    row['text'] = row['text'] + ' (' + row['name'] + ')'
                    row['role/link'] = row['text']
                    text_channel_name = ('-'.join(row['role/link'].lower().replace('(', ' ').replace(')', ' ').strip().split(' '))).replace('--', '-')
                    row['create_channels'] = f'#{text_channel_name},0#Student Voice,2#TA Voice'

    # Handle cross lists
    name_occurances = df.groupby(['long_name']).size()
    for name, count in name_occurances.iteritems():
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
