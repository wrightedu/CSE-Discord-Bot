#!/usr/bin/env python3
from zipfile import ZipFile
import os
import shutil
import subprocess
import platform
import random
import datetime
import argparse

"""
Parse arguments for moss_id.
"""
parser = argparse.ArgumentParser(description='none')
parser.add_argument('--id', type=str, help='Requires moss_id.')

args = parser.parse_args()

moss_id = args.id

# Code written by Ali Aljaffer

# Deciding on directory sep. Mac&Linux us '/' while Windows uses '\'
os_separator: str = "/" if platform.system() in ["Linux", "Darwin"] else "\\"

# TO-DO: implement moss_id argparse
# Get moss_id, check file, run Moss

# current directory
moss_path = os_separator + 'tmp' + os_separator + moss_id
unzipped_dir = moss_path + os_separator + 'unzipped'
named_dir = moss_path + os_separator + 'namedFiles'

# Haven't tested it with submissions of multiple java files but should handle

# Moss supports these languages

# C, C++, Java, C#, Python, Visual Basic, Javascript, FORTRAN, ML,
# Haskell, Lisp, Scheme, Pascal, Modula2, Ada,
# Perl, TCL, Matlab, VHDL, Verilog, Spice,
# MIPS assembly, a8086 assembly, a8086 assembly, HCL2.

test_exist = moss_path + os_separator + 'namedFiles'
if os.path.exists(test_exist) and os.listdir(test_exist):
    yes_or_no = str(input(
        "namedFiles already exists and contains files. Would you like to empty it?")).lower()
    if len(yes_or_no) == 0 or yes_or_no[0] == 'y':
        shutil.rmtree(test_exist)

# Choosing a file extension
# java_or_else = str(
#     input('Use .java file extension? if not, enter the file extension to use (.cpp,.py,etc)\n'))
# file_extension = '.java' if len(java_or_else) == 0 or java_or_else.lower()[
#     0] == 'y' else java_or_else
# # add . if not present
# file_extension = '.' + \
#     file_extension if file_extension[0] != '.' else file_extension
# print('Using {} as file extension and {} as directory seperator'.format(
#     file_extension, os_separator))

file_extension = '.java'


# Have your pilot-downloaded zip file inside tmp/moss_id
# Scan dir

if not os.path.exists(moss_path):
    os.mkdir(moss_path)

def get_last_name(file: str) -> str:
    """
    Gets the last name from file

    :param str file: The file name to get the last name from
    :return: Tries to split the file name. Should be successful as it follows the Pilot naming convention. If it files, just
        uses the file name itself
    """
    try:
        return file.split(' - ')[1].split()[1]
    except:
        return file


def unzip():
    """
    Unizps main zip file downloaded from Pilot into unzipped directory
    """
    try:
        shutil.rmtree(unzipped_dir)
    except:
        pass

    file_name = [file for file in os.listdir(moss_path) if file[-4:] == '.zip']

    file_name = file_name[0] if len(file_name) > 0 else None
    if not file_name:
        print('no additional zip files found')
        return
    with ZipFile(moss_path+os_separator+file_name, 'r') as zip:
        os.mkdir(unzipped_dir)
        zip.extractall(unzipped_dir)


def file_to_dir():
    """
    Finds .{file_extension} file submissions and turns them into the format lastName.java
    and moves them to namedFiles category
    """
    if not os.path.exists(moss_path+os_separator+'namedFiles'):
        os.mkdir(moss_path+os_separator+'namedFiles')
    if not os.path.exists(unzipped_dir):
        return
    for file_name in os.listdir(unzipped_dir):

        if file_name[-len(file_extension):] == file_extension:
            new_name = ''
            try:
                new_name = get_last_name(
                    file_name) + file_extension if file_name.index(' - ') else file_name
            except:
                new_name = file_name
            os.rename(unzipped_dir+os_separator+file_name,
                    moss_path+os_separator+'namedFiles'+os_separator+new_name)


# stores the date of the most recently processed submission
user_submissions_dates = dict()


def get_date_from_file(file_name):
    """
    Gets the date from a file_name. Uses splitting and formatting
    based on Pilot

    :param str file_name: The file name to get the date from
    :return datetime date_object: The extracted date as a datetime obj. If not found returns a string "NoDate"
    """
    try:
        date = str.join(' ', file_name.split(
            ' - ')[2].split(' ')[:3]).replace(',', '')
        time = str.join(' ', file_name.split(' - ')[2].split(' ')[3:])
        date = datetime.datetime.strptime(date, '%b %d %Y').date()
        time = datetime.datetime.strptime(time, '%I%M %p').time()
        date_object = datetime.datetime.combine(date, time)
        return date_object
    except:
        return "NoDate"


def is_more_recent(date_1, date_2):
    """
    checks if date_1: date is more recent compared to date_2:date

    :param date date_1: The first date to compare
    :param date date_2: The second date to compare
    :return True if date_1 is more recent than date_2, else False
    """
    if not isinstance(date_1, datetime.datetime) or not isinstance(date_2, datetime.datetime):
        return False
    else:
        # if date_1 is newer
        return date_1 > date_2


def unzip_inner_zip_files():
    """
    deals with leftover zip files that were submitted as zips in pilot
    creates temp lastName.dir folders that the .zip gets extracted to
    """
    i = 0
    if not os.path.exists(unzipped_dir):
        return
    for zipped_file in os.listdir(unzipped_dir):
        user_last_name = get_last_name(zipped_file)
        # Skip non-zip files
        if zipped_file[-4:] != '.zip':
            continue
        stored_user_date = user_submissions_dates.get(user_last_name, "NoDate")
        current_user_date = get_date_from_file(zipped_file)
        # If stored is newer than current file, skip
        if stored_user_date != "NoDate" and is_more_recent(stored_user_date, current_user_date):
            continue
        with ZipFile(unzipped_dir+os_separator+zipped_file, 'r') as zf:
            temp_dir = unzipped_dir+os_separator + \
                (user_last_name)+'.dir'
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
            else:
                shutil.rmtree(temp_dir)
                os.mkdir(temp_dir)
            zf.extractall(temp_dir)
            # update the last name to have the latest date
            user_submissions_dates[user_last_name] = current_user_date

            i += 1


def find_file_extension_files(search_path):
    """
    searches for .{file_extension} files and notes the directory title which is the last name so we can move it later
    to namedFiles
    gets abs paths of the .{file_extension} files

    :param str search_path: The path that the search tree/walk will start from.

    :return list[str] results: Contains the absolute paths to source code files found.
    :return list[str] titles: The student last names. Duplicates will ahve a random number attached at the end. Should probably change that
    """
    results = []
    titles = []  # names of students
    title = 'dummyName'
    # Wlaking top-down from the root
    i = 1
    for root, moss_path, files in os.walk(search_path):
        source_code_files = []
        # title = parent folder name. just so we save the name of the student that we are currently in
        title = root.split(
            os_separator)[-1] if root.split(os_separator)[-1][-4:] == '.dir' else title
        i += 1
        source_code_files = [os.path.join(root, file)
                    for file in files if file[-len(file_extension):] == file_extension and file[0:2] != '._']  # '._' is a MacOS thing
        if source_code_files:
            for i in range(len(source_code_files)):
                titles.append(title)
            results.extend(source_code_files)
    titles = list(map(lambda x: x+str(random.choice(range(0, 100)))
                    if x == 'dummyName' else x, titles))
    return results, titles

# moves files in list
def move_files(zip_files_paths, student_names):
    """
    searches for .{file_extension} files and notes the directory title which is the last name so we can move it later
    to namedFiles
    gets abs paths of the .{file_extension} files

    :param list[str] zip_files_paths:
    """
    random_number = str(1)
    for i in range(len(student_names)):
        file_path = zip_files_paths[i]
        # New path for the file
        new_path = named_dir+os_separator+student_names[i]
        # If it already exists, add a random number to it
        if os.path.exists(new_path):
            new_path = new_path.split(file_extension)[
                0]+random_number+file_extension
            random_number = str(int(random_number)+1)
        os.rename(file_path, new_path)
    # If it doesn't exist, DO NO RMTREE
    if not os.path.exists(unzipped_dir):
        return
    shutil.rmtree(unzipped_dir)


# unzip big pilot zip
unzip()
# make .{file_extension} files into dirs
file_to_dir()
# make .zip files into dirs of lastName.dir format
unzip_inner_zip_files()

# get all .{file_extension} file abs paths
zip_dirs, titles = find_file_extension_files(unzipped_dir)
i = 0
# Fill missing titles using zip_dirs
while len(zip_dirs) > len(titles) and len(titles)+i < len(titles)-1:
    titles.append(zip_dirs[len(titles)+i].split('/')[3])
    i += 1

# Adds the {file_extension} to each title (last name) if it doesn't exist already.
titles = list(
    map(lambda x: (x[0:len(x)-len(file_extension)+1] if len(x) > len(file_extension) else x)+file_extension, titles))

# Print results of operation
print('Found {} {} and {} .zip submissions.'.format(
    len(os.listdir(named_dir)), file_extension, len(zip_dirs)))

# move .{file_extension} files into namedFiles
move_files(zip_dirs, titles)

# # run moss!
subprocess.Popen(
    f'.{os_separator}utils{os_separator}WSU_mossnet.pl -i {moss_id} {moss_path}{os_separator}namedFiles{os_separator}*{file_extension}', shell=True)

# WIP
# mossum = input('run mossum too?').lower()[0] == 'y'
# if mossum:
#     percentage = input('what\'s the lower limit %')
#     percentage = int(percentage[:-1]) if percentage[-1] == '%' else int(percentage)
#     link = input('provide link')
#     subprocess.Popen('mossum -p {} {}'.format(percentage,link), shell=True)
