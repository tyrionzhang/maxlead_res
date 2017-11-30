import difflib
import re

def get_diff_str(content_list):
    line_list = []
    for i, content in enumerate(content_list, 0):
        for k, con in enumerate(content_list, 0):
            if not i == k:
                a_con = content['content'].replace('.','\n')
                a_con = a_con.replace(',','\n')
                a_con = a_con.replace('!','\n')
                a_con = a_con.replace('?','\n')
                a_con = a_con.replace(';','\n')
                b_con = con['content'].replace('.','\n')
                b_con = b_con.replace(',','\n')
                b_con = b_con.replace('!','\n')
                b_con = b_con.replace('?','\n')
                b_con = b_con.replace(';','\n')
                content_line = a_con.splitlines()
                con_line = b_con.splitlines()
                d = difflib.Differ()
                diff = list(d.compare(content_line, con_line))
                for line in diff:
                    if not line[0] == "+" and not line[0] == "-":
                       line_list.append(line)
    return line_list