# -*- coding: utf-8 -*-
import codecs
import re

delimiters = '(',')',' ',',','=','\'','"'
regexPattern = '|'.join(map(re.escape, delimiters))
ei = 'ErrorInfo'

rows = []
rows.append('Error codes')
rows.append('===========')
rows.append('|{:<40}|{:<10}|{:<75}|'.format("Error", "Error code", "Error description"))
rows.append('|{:-^40}|{:-^10}|{:-^75}|'.format("", "", ""))
import os
print(os.getcwd())
with codecs.open('../../../luna_admin/crutches_on_wheels/errors/errors.py', 'r', 'utf-8') as f:
    for line in f:
        tokens = re.split(regexPattern, line.strip())
        if ei in tokens:

            # remove empty strings
            tokens = list(filter(None, tokens))

            ei_i = tokens.index(ei) # 'ErrorInfo'
            ec_i = ei_i + 1 # error code
            ed_i = ec_i + 1 # error description starts from this token

            # skip error codes below 100 and non-numeric statuses
            ec = tokens[ec_i]
            if not ec.isdigit() or int(ec) < 100:
                continue

            # rebuild description line from tokens
            desc = ' '.join(tokens[ed_i:])

            # make table row
            tr = '|{:<40}|{:<10}|{:<75}|'.format(tokens[0], tokens[ec_i], desc)

            rows.append(tr)


with codecs.open('error_codes.md', 'w', 'utf-8') as f:
    for tr in rows:
        f.write(tr + '\r\n')
