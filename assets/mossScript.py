from zipfile import ZipFile
import os
import shutil
import subprocess
import platform
import random
import datetime

# Deciding on directory sep. Mac&Linux us '/' while Windows uses '\'
os_separator: str = "/" if platform.system() in ["Linux", "Darwin"] else "\\"


# current directory
curr_dir = os.path.abspath('.') + os_separator

# Haven't tested it with submissions of multiple java files but should handle

# Moss supports these languages

# C, C++, Java, C#, Python, Visual Basic, Javascript, FORTRAN, ML,
# Haskell, Lisp, Scheme, Pascal, Modula2, Ada,
# Perl, TCL, Matlab, VHDL, Verilog, Spice,
# MIPS assembly, a8086 assembly, a8086 assembly, HCL2.

test_exist = curr_dir+os_separator+'StudentCode'+os_separator+'namedFiles'
if os.path.exists(test_exist) and os.listdir(test_exist):
    y_n = str(input(
        "namedFiles already exists and contains files. Would you like to empty it?")).lower()
    if len(y_n) == 0 or y_n[0] == 'y':
        shutil.rmtree(test_exist)

# Choosing a file extension
java_or_else = str(
    input('Use .java file extension? if not, enter the file extension to use (.cpp,.py,etc)\n'))
file_extension = '.java' if len(java_or_else) == 0 or java_or_else.lower()[
    0] == 'y' else java_or_else
# add . if not present
file_extension = '.' + \
    file_extension if file_extension[0] != '.' else file_extension
print('Using {} as file extension and {} as directory seperator'.format(
    file_extension, os_separator))


# Have your pilot-downloaded zip file inside current dir/StudentCode/
# Scan dir
dir = '.'+os_separator+'StudentCode'
if not os.path.exists(dir):
    os.mkdir(dir)

unzipped_dir = dir+os_separator+'unzipped'

named_dir = dir+os_separator+'namedFiles'


def get_last_name(file: str) -> str:
    """
    gets the last name from file
    """
    try:
        return file.split(' - ')[1].split()[1]
    except:
        return file


def unzip():
    """
    unizps main zip file downloaded from Pilot into unzipped directory
    """
    try:
        shutil.rmtree(unzipped_dir)
    except:
        pass

    file_name = [file for file in os.listdir(dir) if file[-4:] == '.zip']

    file_name = file_name[0] if len(file_name) > 0 else None
    if not file_name:
        print('no additional zip files found')
        return
    with ZipFile(dir+os_separator+file_name, 'r') as zip:
        os.mkdir(unzipped_dir)
        zip.extractall(unzipped_dir)


def file_to_dir():
    """
    Finds .{file_extension} file submissions and turns them into the format lastName.java
    and moves them to namedFiles category
    """
    if not os.path.exists(dir+os_separator+'namedFiles'):
        os.mkdir(dir+os_separator+'namedFiles')
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
                      curr_dir+dir+os_separator+'namedFiles'+os_separator+new_name)


# stores the date of the most recently processed submission
user_submissions_dates = dict()


def getDate(file_name):
    """
    Gets the date from a file_name. Uses splitting and formatting
    based on Pilot
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


def isMoreRecent(d1, d2):
    """
    checks if d1: date is more recent compared to d2:date
    """
    if not isinstance(d1, datetime.datetime) or not isinstance(d2, datetime.datetime):
        return False
    else:
        # if d1 is newer
        return d1 > d2


def dealWithZip():
    """
    deals with leftover zip files that were submitted as zips in pilot
    creates temp lastName.dir folders that the .zip gets extracted to
    """
    i = 0
    if not os.path.exists(unzipped_dir):
        return
    for zipped_file in os.listdir(unzipped_dir):
        user_last_name = get_last_name(zipped_file)
        if zipped_file[-4:] != '.zip':
            continue
        stored_user_date = user_submissions_dates.get(user_last_name, "NoDate")
        current_user_date = getDate(zipped_file)
        # If stored is newer than current file, skip
        if stored_user_date != "NoDate" and isMoreRecent(stored_user_date, current_user_date):
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
    """
    results = []
    titles = []  # names of students
    title = 'dummyName'
    # Wlaking top-down from the root
    i = 1
    for root, dir, files in os.walk(search_path):
        code_files = []
        # title = parent folder name. just so we save the name of the student that we are currently in
        title = root.split(
            os_separator)[-1] if root.split(os_separator)[-1][-4:] == '.dir' else title
        i += 1
        code_files = [os.path.join(root, file)
                      for file in files if file[-len(file_extension):] == file_extension and file[0:2] != '._']  # '._' is a MacOS thing
        if code_files:
            for i in range(len(code_files)):
                titles.append(title)
            results.extend(code_files)
    titles = list(map(lambda x: x+str(random.choice(range(0, 100)))
                      if x == 'dummyName' else x, titles))
    return results, titles

# moves files in list


def moveFiles(lst, titles):
    """
    searches for .{file_extension} files and notes the directory title which is the last name so we can move it later
    to namedFiles
    gets abs paths of the .{file_extension} files
    """
    silly_number = str(1)
    for i in range(len(titles)):
        file_path = lst[i]
        new_path = named_dir+os_separator+titles[i]
        if os.path.exists(new_path):
            new_path = new_path.split(file_extension)[
                0]+silly_number+file_extension
            silly_number = str(int(silly_number)+1)
        os.rename(file_path, new_path)
    if not os.path.exists(unzipped_dir):
        return
    shutil.rmtree(unzipped_dir)


# unzip big pilot zip
unzip()
# make .{file_extension} files into dirs
file_to_dir()
# make .zip files into dirs of lastName.dir format
dealWithZip()

# get all .{file_extension} file abs paths
zip_dirs, titles = find_file_extension_files(unzipped_dir)
i = 0
# Fill missing titles using zip_dirs
while len(zip_dirs) > len(titles) and len(titles)+i < len(titles)-1:
    titles.append(zip_dirs[len(titles)+i].split('/')[3])
    i += 1

titles = list(
    map(lambda x: (x[0:len(x)-len(file_extension)+1] if len(x) > len(file_extension) else x)+file_extension, titles))
print('Found {} {} and {} .zip submissions.'.format(
    len(os.listdir(named_dir)), file_extension, len(zip_dirs)))
# move .{file_extension} files into namedFiles
moveFiles(zip_dirs, titles)

# # run moss!
subprocess.Popen(
    f'.{os_separator}moss .{os_separator}StudentCode{os_separator}namedFiles{os_separator}*{file_extension}', shell=True)

# WIP
# mossum = input('run mossum too?').lower()[0] == 'y'
# if mossum:
#     percentage = input('what\'s the lower limit %')
#     percentage = int(percentage[:-1]) if percentage[-1] == '%' else int(percentage)
#     link = input('provide link')
#     subprocess.Popen('mossum -p {} {}'.format(percentage,link), shell=True)
