import pandas as pd
import os
import subprocess
from bs4 import BeautifulSoup
from html import unescape 

# Crosslists (course number in key actually points to class in value)
crosslists = {
    "CEG 5350": "CEG 4350",
    "CEG 6424": "CEG 4424",
    "EE 2011": "EE 2010",
    "EE 4910": "CEG 4980",
    "EE 4920": "CEG 4981",
    "EE 7840": "CEG 7550",
    "EE 7580": "CEG 7080",
    "CEG 6322": "CEG 4322",
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

# Read in html 

# making file names
input_file = 'Class Schedule Listing.html'
output_file = 'classes.txt'

def html_formatting(raw: str) -> str:

    # decodes HTML entities ("&amp;" -> "&")
    text = unescape(raw)

    # removes extra whitespace inside the text
    text = " ".join(text.split())

    # if a '>' exists, keep only the part after the last '>'
    if ">" in text:
        text = text.rsplit('>', maxsplit=1)[-1].strip()

    # makes sure no whitespace remains
    return text.strip()

# reads the file and parse it using soup
with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# sets tags and looks for ddtitle
tags = soup.select("a.ddtitle")

# if ddtitle isnt found, grab all <a> tags
if not tags:
    tags = soup.find_all("a")

# used to remove duplicates
seen = set()

# keeps the final unique lines in order
classes = []

# iterates through every <a> element
for tag in tags:
    raw_text = tag.get_text(" ", strip=True) # pulls out tesxt and trims
    line = html_formatting(raw_text) # runs it through formatting to clean it up

    # skip junk menu/navigation links
    if not line or line.startswith('['):
        continue
    
    # splits text up with '-'
    parts = line.split(" - ")

    # pulls out the title and the number of the course  then formats it
    if len(parts) >= 3:
        title = parts[0].strip()
        course = parts[2].strip()

        formatted = f"{title} - {course}" # example - Adv Artificial Intelligence - CS 7900
    else:
        continue  # skip anything that doesn’t match course format

    # if its new record it in seen and add the original formatted string to classes
    key = formatted.lower()
    if key not in seen:
        seen.add(key)
        classes.append(formatted)

# sort alphabetically
classes.sort(key=str.lower)

# writes one class per line
with open(output_file, "w", encoding="utf-8") as out:
    out.write("\n".join(classes) + "\n")

print(f"Wrote {len(classes)} unique lines to {output_file}")


if __name__ == '__main__':
    classes = []
    number = 0
    # Open HTML file in current working directory
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classes.txt'), 'r', encoding='utf-8') as file:
        for line in file:
            delineated = line.replace("\n", "").split(" - ")

            if not delineated[1].endswith("L"):
                number = number + 1

                classInfo = delineated[1].split(" ")

                if len(classInfo) != 2:
                    classInfo = ["UNKNOWN", '0000']

                # Set class information needed
                class_department = classInfo[0]
                class_number = classInfo[1]
                class_name = delineated[0]

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
        df.at[i, 'text'] = df.at[i, 'department'].upper() + ' ' + df.at[i, 'number']

        # Set role name
        df.at[i, 'role/link'] = df.at[i, 'text']

        # Set full class name
        df.at[i, 'long_name'] = df.at[i, 'name'].strip()
        
        # Get class in lowercase number
        lowercase_number = df.at[i, 'text'].replace(' ', '').lower()

        # Set channels to create
        df.at[i, 'create_channels'] = f'#{lowercase_number},0#Student Voice,2#TA Voice'
        
        # If class marked manually as crosslisted
        if df.at[i, 'text'] in crosslists:
            # Set role/link to be crosslisted class
            df.at[i, 'role/link'] = crosslists[df.at[i, 'text']]

            # Don't create any new channels
            df.at[i, 'create_channels'] = ''

    # Handle duplicate class numbers
    text_occurances = df.groupby(['text']).size()
    print(text_occurances)
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
