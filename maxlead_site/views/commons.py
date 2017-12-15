import difflib
from maxlead_site.models import Log

def get_diff_str(content_list):
    line_list = []
    if content_list:
        for i, content in enumerate(content_list, 0):
            for k, con in enumerate(content_list, 0):
                if not i == k:
                    a_con = content['content']
                    b_con = con['content']
                    if a_con and b_con:
                        a_con = a_con.replace('.','\n')
                        a_con = a_con.replace(',','\n')
                        a_con = a_con.replace('!','\n')
                        a_con = a_con.replace('?','\n')
                        a_con = a_con.replace(';','\n')
                        content_line = a_con.splitlines()

                        b_con = b_con.replace('.','\n')
                        b_con = b_con.replace(',','\n')
                        b_con = b_con.replace('!','\n')
                        b_con = b_con.replace('?','\n')
                        b_con = b_con.replace(';','\n')
                        con_line = b_con.splitlines()

                        d = difflib.Differ()
                        diff = list(d.compare(content_line, con_line))
                        for line in diff:
                            if not line[0] == "+" and not line[0] == "-":
                               line_list.append(line)
    return line_list

def loger(description,user,name=''):
    log_obj = Log(description=description,user=user,name=name)
    log_obj.id
    log_obj.save()
    return log_obj.id