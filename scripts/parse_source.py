import os
import io
import sys
import json
import re
import glob
from collections import OrderedDict
from tabulate import tabulate
import hashlib


path_script = os.path.abspath(os.path.dirname(__file__))
file_apks = ''
file_lists = 'data/data_lists.json'
file_permissions = 'data/data_permissions.json'
path_output_s = 'data/source/out'
path_output_r = 'data/rl/out'
path_rl = 'data/rl'
path_source = 'data/source'

# calls_per_file = 1000

d_rl_restr = {
'greylist-max-o': 'conditional_block_max_o',
'max-target-r': 'conditional_block_max_r',
'public-api,system-api,test-api,whitelist': 'public',
'system-api,whitelist': 'sdk',
'core-platform-api,public-api,sdk,system-api,test-api': 'public',
'public-api,sdk,system-api,test-api': 'public',
'core-platform-api,public-api,system-api,test-api,whitelist': 'public',
'lo-prio,max-target-o': 'conditional_block_max_o',
'test-api,unsupported': 'unsupported',
'blocked': 'blacklist',
'greylist-max-p': 'conditional_block_max_p',
'greylist': 'unsupported',
'sdk,system-api,test-api': 'sdk',
'system-api,test-api,whitelist': 'sdk',
'max-target-r,test-api': 'conditional_block_max_r',
'blacklist,test-api': 'blacklist',
'max-target-p': 'conditional_block_max_p',
'removed,unsupported': 'unsupported',
'blocked,test-api': 'blacklist',
'greylist,test-api': 'unsupported',
'lo-prio,max-target-o,test-api': 'conditional_block_max_o',
'unsupported': 'unsupported',
'blacklist': 'blacklist',
'greylist-max-q': 'conditional_block_max_q',
'lo-prio,max-target-r': 'conditional_block_max_r',
'blacklist,core-platform-api': 'blacklist',
'whitelist': 'sdk',
'core-platform-api,greylist-max-o': 'conditional_block_max_o',
'core-platform-api,greylist': 'unsupported',
'public-api,whitelist': 'public',
'core-platform-api,greylist-max-p': 'conditional_block_max_p',
'greylist-max-o,test-api': 'conditional_block_max_o',
'public-api,system-api,whitelist': 'public',
'greylist-max-q,test-api': 'conditional_block_max_q',
'core-platform-api,greylist-max-q': 'conditional_block_max_q',
'max-target-q': 'conditional_block_max_q',
'blocked,core-platform-api': 'blacklist',
'max-target-o': 'conditional_block_max_o',
'sdk': 'sdk',
'core-platform-api,lo-prio,max-target-o': 'conditional_block_max_o',
'max-target-q,test-api': 'conditional_block_max_q',
'core-platform-api,unsupported': 'unsupported',
'public-api,sdk': 'public',
'core-platform-api,max-target-q': 'conditional_block_max_q',
'core-platform-api,max-target-r': 'conditional_block_max_r',
'core-platform-api,max-target-p': 'conditional_block_max_p',
'core-platform-api,public-api,sdk': 'public',
'max-target-s': 'conditional_block_max_s',
}

d_restr_lower = {
'blacklist': [
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'sdk': [
  'public',
  'unsupported'
],
'conditional_block_max_o': [
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s'
],
'conditional_block_max_p': [
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s'
],
'conditional_block_max_q': [
  'conditional_block_max_r',
  'conditional_block_max_s'
],
'conditional_block_max_r': [
  'conditional_block_max_s'
],
'conditional_block_max_s': [],
'public': [],
'unsupported': [],
}

d_restr_all = {
'blacklist': [
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'sdk': [
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_o': [
  'sdk',
  'blacklist',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_p': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_q': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_r': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_s': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'public',
  'unsupported',
  ],
'public': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'unsupported',
],
'unsupported': [
  'sdk',
  'blacklist',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  ],
}

d_restr_all_rep = {
'blacklist': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'sdk': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_o': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_p': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_q': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_r': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'conditional_block_max_s': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
  ],
'public': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
],
'unsupported': [
  'blacklist',
  'sdk',
  'conditional_block_max_o',
  'conditional_block_max_p',
  'conditional_block_max_q',
  'conditional_block_max_r',
  'conditional_block_max_s',
  'public',
  'unsupported',
  ],
}

d_block_ver = {
  'conditional_block_max_o': '8',
  'conditional_block_max_p': '9',
  'conditional_block_max_q': '10',
  'conditional_block_max_r': '11',
  'conditional_block_max_s': '12',
}


def log_data(logfile, logtext, lineend):
  print(logtext, end=lineend)
  with io.open(f'{path_script}/{path_output_s}/{logfile}', 'a') as l:
    l.write(f'{logtext}{lineend}')


def get_filepaths(abspath_dir):

  paths_files = []

  for filename in glob.iglob(abspath_dir + '**/**', recursive=True):
    if os.path.isfile(filename):
      p = f'{abspath_dir}/{filename}'
      paths_files.append(filename)
  
  print(f'Found files: {len(paths_files)}')
  return paths_files


def get_restriction_lists(ver):

  for file in os.listdir(f'{path_script}/{path_rl}'):
    if str(ver) in file and 'flags' in file:
      path_file = f'{path_script}/{path_rl}/{file}'
      data = OrderedDict()
      data_raw = []
      data_list = []
      test_set = set()
      with io.open(f'{path_script}/{path_output_r}/test_{ver}.txt','w') as o:
        with io.open(path_file) as hf:
          for row in hf.readlines():
            data_raw.append(row.split(',')[0])
            row = row.replace('\n','')
            item_rls = row.split(',')
            rls = item_rls[1:]
            item = item_rls[0]
            item_l = re.split(';->|:',item)
            item_list = []
            if '$' in item_l[0]:
              item_list += item_l[0][1:].split('$',1)
            else:
              item_list = [item_l[0][1:],'']
            if '(' in item_l[1]:
              invocation_name,other = item_l[1].split('(')
              params,additional = other.split(')')
            else:
              invocation_name = item_l[1]
              params = ''
              additional = item_l[2]
            item_list += [invocation_name,params,additional]
            # if 'permission' not in row_list[0]:
              # print(1,end='')
            rls_str = ','.join(rls)
            row_list = item_list + [rls_str,row]
            row_str = ' | '.join(row_list)
            # sep = row_list[0].split('/')[0]
            # if row_list[2] != '<init>':
            #   try:
            #     call_self,call_sec = row_list[2].split(sep)
            #     call_sec = sep + call_sec
            #   except ValueError:
            #     call_self = row_list[2]
            #   data[call_self] = row_list
            o.write(f'{row_str}\n')
            # else:
            #   print(1)
            data_list.append(row_list)
          #   data.append(row_list)
          # tab = tabulate(data, tablefmt="github")
          # o.write(tab)
      # print(1)
      return data_list,data_raw


def parse_restriction_lists():

  vers = ['10','11','12','13']
  data = OrderedDict()
  s = set()
  for ver in vers:
    for file in os.listdir(f'{path_script}/{path_rl}'):
      if str(ver) in file and 'flags' in file:
        path_file = f'{path_script}/{path_rl}/{file}'
        with io.open(path_file) as hf:
          for row in hf.readlines():
            row = row.replace('\n','')
            item_rls = row.split(',')
            rls = item_rls[1:]
            item = item_rls[0]
            rls_str = ','.join(rls)
            try:
              restr = d_rl_restr[rls_str]
            except KeyError:
              restr = 'placeholder'
              if rls_str not in s:
                s.add(rls_str)
                print(rls_str)
            if item not in data.keys():
              data[item] = OrderedDict({
                'seen_in_lists': [int(ver)],
                'versions': OrderedDict({
                  ver: OrderedDict({
                    'restr_line': row,
                    'rls': rls,
                    'restr': restr
                  })
                })
              })
            else:
              if int(ver) not in data[item]['seen_in_lists']:
                data[item]['seen_in_lists'].append(int(ver))
                data[item]['versions'][ver] = OrderedDict({
                  'restr_line': row,
                  'rls': rls,
                  'restr': restr
                })
              else:
                print(1)
  with io.open(f'{path_script}/{path_output_r}/calls_in_restriction_lists.json','w') as jout:
    json.dump(data, jout, indent = 2)


def fix_mapping_2(name_end):
  vers = [10,11,12,13]
  if not name_end:
    print('provide name!')
    return
  pset = set()
  partset = set()
  with io.open(f'{path_script}/{path_output_s}/{name_end}.json','r') as jin:
    mapping = json.load(jin)

    for path,data in mapping.items():
      for v,item in data['versions'].items():
        p = item['perms']
        for i in range(len(p['perms'])):
          p['perms'][i] = p['perms'][i].replace('(','').replace(')','').replace('"','').replace('value = ','').replace('value=','')
          if 'conditional = true' in p['perms'][i]:
            p['params'] = ['conditional = true']
            p['perms'][i] = p['perms'][i].replace(',','').replace('conditional = true','')
          p['perms'][i] = p['perms'][i].strip()
          parts = p['perms'][i].split('.')
          pred = '.'.join(parts[:-1])
          partset.add(pred)
          pset.add(p['perms'][i])
        data['versions'][v]['perms'] = p
        # print(1)
      
      mapping[path] = data
  

  with io.open(f'{path_script}/{path_output_s}/{name_end}.json','w') as jout:
    json.dump(mapping, jout, indent = 2)
  
  with io.open(f'{path_script}/{path_output_s}/{name_end}_perms.txt','w') as jout:
    for p in pset:
      jout.write(f'{p}\n')
  
  with io.open(f'{path_script}/{path_output_s}/{name_end}_part.txt','w') as jout:
    for p in partset:
      jout.write(f'{p}\n')


def is_line_tag(line):
  line = line.strip()
  if not line.startswith('@'):
    return False
  if ' ' in line:
    return False
  if '_' in line:
    return False
  if '(' in line:
    return False
  consec_upper = 0
  for ch in line:
    if ch.isupper():
      consec_upper += 1
    else:
      consec_upper = 0
    if consec_upper > 1:
      return False
  return True


def count_reqperm_tag_one(path_file):
  
  count_reqperm = 0
  err = None
  with io.open(path_file) as f:
    try:
      content = f.readlines()
    except UnicodeDecodeError as err:
      return 0

    for i in range(len(content)):
      line = content[i].strip()
      line = re.sub(' +', ' ', line)
      if not line:
        continue
      if line.startswith('*') or line.startswith('//') or line.startswith('/*'):
        continue
      if line.startswith('+'):
        continue
      if '//' in line:
        line = line.split('//')[0].strip()

      if line.startswith('@RequiresPermission'):
        count_reqperm += 1
  
  return count_reqperm


def count_reqperm_tag(path_dir):

  abspath_dir = f'{path_script}/{path_dir}'
  folder_name_out = path_dir.replace('/','.')

  path_out = f'{path_script}/{path_output_s}/{folder_name_out}'
  if not os.path.exists(path_out):
    os.mkdir(path_out)
    paths_files = get_filepaths(abspath_dir)
    with io.open(f'{path_out}/filepaths.txt','w') as pout:
      for p in paths_files:
        prel = p.replace(abspath_dir,'')
        pout.write(f'{prel}\n')
  else:
    paths_files = []
    with io.open(f'{path_out}/filepaths.txt','r') as pout:
      for p in pout.readlines():
        paths_files.append(f'{abspath_dir}{p.strip()}')
  
  path_files_done = []
  if not os.path.exists(f'{path_out}/filepaths_done.txt'):
    with io.open(f'{path_out}/filepaths_done.txt','w') as dout:
      pass
  else:
    with io.open(f'{path_out}/filepaths_done.txt','r') as pin:
      for p in pin.readlines():
        pabs = abspath_dir + p.replace('\n','')
        path_files_done.append(pabs)

  file_name = 'calls_all'
  dict_calls = OrderedDict()

  count_reqperm = 0

  with io.open(f'{path_out}/filepaths_done.txt','a') as dout, io.open(f'{path_out}/{file_name}.json','a') as jout:
    while paths_files:
      path_file = None
      try:
        path_file = paths_files.pop()
      except IndexError:
        break

      if path_file not in path_files_done:
        count_reqperm_one = count_reqperm_tag_one(path_file)
        count_reqperm += count_reqperm_one
  
  print(count_reqperm)


def parse_permline(line,path_file):

  multi = False
  add = False
  p_which = None
  call = None
  if '@RequiresPermission.Read' in line:
    perm_type = 'read'
    req_type = '@RequiresPermission.Read'
    print(1)
  elif '@RequiresPermission.Write' in line:
    perm_type = 'write'
    print(1)
    req_type = '@RequiresPermission.Write'
  elif '@RequiresPermission(' in line:
    perm_type = 'basic'
    req_type = '@RequiresPermission'
  else:
    print(1)
  
  if not line.endswith(')'):
    if line.endswith('('):
      # @RequiresPermission(Manifest.permission.UPDATE_FONTS) public @ResultCode int updateFontFamily(
      perm_part,call_part = line.split(')')
      perm = perm_part.strip().replace(f'{req_type}(','').split(',')
      call = call_part.strip().split(' ')[-1].replace('(','') + '()'
      # print(1)
    else:
      multi = True
      if ' allOf = {' in line:
        req_type += '( allOf = {'
        p_which = 'all'
      elif 'allOf = {' in line:
        req_type += '(allOf = {'
        p_which = 'all'
      elif 'allOf={' in line:
        req_type += '(allOf={'
        p_which = 'all'
      elif 'value = ' in line:
        req_type += '(value = '
        add = True
      elif 'anyOf={' in line:
        req_type += '(anyOf={'
        p_which = 'any'
      elif 'anyOf = {' in line:
        req_type += '(anyOf = {'
        p_which = 'any'
      elif 'anyOf= {' in line:
        req_type += '(anyOf= {'
        p_which = 'any'
      elif 'anyOf =' in line:
        req_type += '(anyOf ='
        p_which = 'any'
      else:
        print(1)
      perm = line.replace(f'{req_type}','').replace(' ','')
      perm = perm.split(',')
      for p in perm:
        if len(perm)==1 and not p:
          perm = []
          add = True
        elif p:
          pass
        else:
          perm.remove(p)
  else:
    if 'allOf = {' in line:
      req_type += '(allOf = {'
      p_which = 'all'
    elif 'allOf={' in line:
      req_type += '(allOf={'
      p_which = 'all'
    elif 'value = ' in line:
      req_type += '(value = '
      add = True
    elif 'anyOf={' in line:
      req_type += '(anyOf={'
      p_which = 'any'
    elif 'anyOf = {' in line:
      req_type += '(anyOf = {'
      p_which = 'any'
    else:
      req_type += '('
    # line = line.replace()
    perm = line.replace(f'{req_type}','').replace(')','').replace('}','').replace(' ','')
    perm = perm.split(',')
  clean_perm = []
  for p in perm:
    p = p.replace('"','')
    if 'carrierprivileges' not in p and p != 'conditional=true' and p:
      if '"' in p:
        print(1)
      clean_perm.append(p)

  return clean_perm,perm_type,multi,add,p_which,call


def extract_one(path_file):
  
  err = None
  with io.open(path_file) as f:
    try:
      content = f.readlines()
    except UnicodeDecodeError as err:
      return [],err
    
    invocations = [
      'public',
      'private',
      'protected'
    ]
    
    skip = [
      '@SuppressLint',
      '@SdkConstant',
      '@ContextHubTransaction',
      '@Deprecated',
      '@SystemApi',
      '@TestApi',
      '@SuppressAutoDoc',
      '@SuppressWarnings',
      '@IntRange',
      '@FloatRange',
      '@Override',
      '@BiometricConstants',
      '@WorkerThread',
      ]
    
    skip_sections = [
      '@RequiresFeature(',
      '@UnsupportedAppUsage(',
      '@UserHandleAware('
    ]

    file_name = path_file.split('/')[-1].split('.')[0]

    # if file_name == 'BluetoothSocket':
    #   print(1)
    
    blocks = []
    block_class = None
    block_class_indent = None
    block_class_inner_indents = []
    block_class_inner_indents_dict = OrderedDict()
    j = -1
    for i in range(len(content)):
      if i <= j:
        continue
      rawline = content[i].replace('\n','')
      line = content[i].strip().replace('\n','')
      line = re.sub(' +', ' ', line)
      if line.startswith('*') or line.startswith('//'):
        continue
      if line.startswith('+'):
        continue
      if line.startswith('/*'): # /*package*/
        if '*/' in line:
          line = line.split('*/')[1].strip()
        else:
          continue
      if line.endswith('*/'): # /*package*/
        if '/*' in line:
          line = line.split('/*')[0].strip()
        else:
          continue
      if '//' in line:
        line = line.split('//')[0].strip()
      if not line:
        continue
      line_indent = 0
      for ch in rawline:
        if ch == ' ':
          line_indent += 1
        else:
          break
      if block_class_indent != None and line_indent <= block_class_indent:
        block_class = None
        block_class_indent = None
        block_class_inner_indents = []
        block_class_inner_indents_dict = OrderedDict()
      if block_class_inner_indents:
        block_class = ''
        for index in range(len(block_class_inner_indents)):
          if block_class_inner_indents[index] < line_indent:
            block_class = f'{block_class}${block_class_inner_indents_dict[block_class_inner_indents[index]]}'
          else:
            for sind in range(index,len(block_class_inner_indents)):
              del block_class_inner_indents_dict[block_class_inner_indents[sind]]
            block_class_inner_indents = block_class_inner_indents[0:index]
            break
      if ' class ' in line:
        some_class = line.split('class')[1].strip().split(' ')[0]
        if not some_class == file_name or (block_class and block_class != some_class):
          if not block_class:
            block_class = line.split('class')[1].strip().split(' ')[0]
            block_class_indent = 0
            for ch in rawline:
              if ch == ' ':
                block_class_indent += 1
              else:
                break
            block_class_inner_indents.append(block_class_indent)
            block_class_inner_indents_dict[block_class_indent] = block_class
          else:
            block_class_inner = line.split('class')[1].strip().split(' ')[0]
            block_class_inner_indent = 0
            for ch in rawline:
              if ch == ' ':
                block_class_inner_indent += 1
              else:
                break
            if block_class_inner_indents:
              block_class = ''
              for index in range(len(block_class_inner_indents)):
                if block_class_inner_indents[index] < block_class_inner_indent:
                  block_class = f'{block_class}${block_class_inner_indents_dict[block_class_inner_indents[index]]}'
                else:
                  block_class = f'{block_class}${block_class_inner}'
                  for sind in range(index,len(block_class_inner_indents)):
                    del block_class_inner_indents_dict[block_class_inner_indents[sind]]
                  block_class_inner_indents = block_class_inner_indents[0:index]
                  block_class_inner_indents.append(block_class_inner_indent)
                  block_class_inner_indents_dict[block_class_inner_indent] = block_class_inner
                  break
              if block_class_inner_indent not in block_class_inner_indents_dict:
                block_class = f'{block_class}${block_class_inner}'
                block_class_inner_indents.append(block_class_inner_indent)
                block_class_inner_indents_dict[block_class_inner_indent] = block_class_inner
              if block_class.startswith('$'):
                block_class = block_class[1:]
                
            else:
              block_class_inner_indents.append(block_class_inner_indent)
              block_class_inner_indents_dict[block_class_inner_indent] = block_class_inner
              block_class = f'{block_class}${block_class_inner}'

      if line.startswith('@RequiresPermission'):
        block = []
        if block_class:
          if block_class.startswith('$'):
            block_class = block_class[1:]
          block.append(block_class)
        else:
          block.append('')
        is_section = False
        passed_invocation = False
        for j in range(i,len(content)):
          line_block = content[j].strip()
          line_block = re.sub(' +', ' ', line_block)
          if is_section and ')' not in line_block:
            continue
          elif is_section and ')' in line_block:
            is_section = False
            continue
          if line_block.startswith('*') or line_block.startswith('//'):
            continue
          if line_block.startswith('+'):
            continue
          if line_block.startswith('/*'): # /*package*/
            if '*/' in line_block:
              line_block = line_block.split('*/')[1].strip()
            else:
              continue
          if line_block.endswith('*/'): # /*package*/
            if '/*' in line_block:
              line_block = line_block.split('/*')[0].strip()
            else:
              continue
          if '//' in line_block:
            line_block = line_block.split('//')[0].strip()
          if not line_block:
            continue
          if True in [line_block.startswith(x) for x in skip_sections] and ')' not in line_block:
            is_section = True
            continue
          elif True in [line_block.startswith(x) for x in skip_sections] and ')' in line_block:
            continue
          if True in [line_block.startswith(x) for x in invocations]:
            passed_invocation = True
            if '(' in line_block:
              index_openbracket = line_block.index('(')
              if line_block[index_openbracket-1] == ' ':
                line_block = line_block[:index_openbracket-1] + line_block[index_openbracket:]
          if True in [line_block.startswith(x) for x in skip] and not passed_invocation:
            continue
          if is_line_tag(line_block) and not passed_invocation:
            continue
          block.append(line_block)
          if not line_block.startswith('@RequiresPermission') and \
          not line_block.endswith(',') and \
          (line_block.endswith('{') or line_block.endswith('{ }') or \
          ('=' in line_block and 'conditional = true' not in line_block and 'conditional=true' not in line_block) or \
          line_block.endswith(';')):
            blocks.append(block)
            break
    
    for x in range(len(blocks)):
      b = blocks[x]
      newb = []
      ch = False
      for y in range(len(b)):
        if ch:
          ch = False
          continue
        line_block = b[y]
        if line_block == '@RequiresPermission(':
          line_block = b[y] + b[y+1]
          ch = True
        newb.append(line_block)
      blocks[x] = newb
             
    
    # if blocks:
    #   print(1)
    return blocks,err


class ContinueI(Exception):
    pass


def compile_items(list_callitems,path_file):

  data_calls = []
  continue_i = ContinueI()
  count_exceptions = 0
  path_file_partial = '/'.join(path_file.split('/')[-3:])

  # if 'AlarmManager.java' in path_file:
  #   print(1)

  for content in list_callitems:

    P = False # collect permissions data
    M = False # multiline @RequiresPermission
    C = False # collect call
    I = False # collection instance
    A = False # collect additional @RequiresPermission params
    call = None
    data_call = None
    call_lines = None
    params = None
    block_class = None
    call_parts = None
    call_str = None


    try:

      for i in range(len(content)):

        if i == 0:
          block_class = content[i]
          continue
        line = content[i].strip()


        if line.startswith('@RequiresPermission') and not P:
          if ' Intent ' in line or ' @AllocateFlags ' in line: ################################## HERE
            raise continue_i
          I = True
          P = True
          # for j in range(i-10,i+10):
          #   print(content[j])
          dict_perms = OrderedDict({
            'basic': OrderedDict({
              'perms':[],
              'params':[],
              'req':[]
            }),
            'read': OrderedDict({
              'perms':[],
              'params':[],
              'req':[]
            }),
            'write': OrderedDict({
              'perms':[],
              'params':[],
              'req':[]
            })
          })
          perm,perm_type,M,A,req,call = parse_permline(line,path_file)

          if '@RequiresPermission(allOf={' in perm or 'carrierprivileges' in perm:
            print(1)
          for p in perm:
            if '@RequiresPermission(allOf={' in p or 'carrierprivileges' in p:
              print(1)
          # if M:
          #   print(1)
          for p in perm:
            if perm:
              dict_perms[perm_type]['perms'].append(p)
          list_perm_lines = [line]
          dict_perms[perm_type]['req'].append(req)
          if call:
            call_lines = [line]
            P = False
            C = True

        
        elif P and M and not A:
          if line.endswith('},'):
            perm = line.replace('},','')
            A = True
          elif line.endswith(','):
            perm = line.replace(',','')
          elif line.endswith('})'):
            perm = line.replace('})','')
            M = False
          elif line.endswith(')'):
            perm,params = line.split('}, ')
            dict_perms[perm_type]['params'].append(params[:-1])
            M = False
          elif line.startswith('})'):
            if line.endswith(';'):
              if 'static' in line and '=' in line:
                call_parts = line.split(' =')[0].split(' ')
                call = call_parts[-1]
                call_lines = [line]
                params = []
                C = False
                M = False
                P = False
              else:
                print(1)
            else:
              print(1)
          elif content[i+1].strip() == '})':
            perm = str(line)
            M = False
          else:
            print(1)
          if perm:
            dict_perms[perm_type]['perms'].append(perm)
            list_perm_lines.append(line)
          # else:
          #   list_perm_lines.append(line)
        

        elif P and M and A:
          list_perm_lines.append(line)
          perms = line.replace('{','').replace('}','').replace(' ','').split(',')
          if line.endswith(')'):
            for p in perms:
              if p:
                if '=' in p:
                  dict_perms[perm_type]['params'].append(p.replace(')',''))
                else:
                  dict_perms[perm_type]['perms'].append(p.replace(')',''))
            A = False
            M = False
          elif line.endswith(','):
            for p in perms:
              if p:
                if '=' in p:
                  dict_perms[perm_type]['params'].append(p.replace(',',''))
                else:
                  dict_perms[perm_type]['perms'].append(p.replace(',',''))
          else:
            if ' ' in line or ',' in line:
              print(1)
            else:
              if p:
                if '=' in p:
                  dict_perms[perm_type]['params'].append(line)
                else:
                  dict_perms[perm_type]['perms'].append(line)
              A = False


        elif line.startswith('@RequiresPermission') and P:
          perm,perm_type,M,A,req,call = parse_permline(line,path_file)

          if '@RequiresPermission(allOf={' in perm:
            print(1)
          for p in perm:
            if '@RequiresPermission(allOf={' in p:
              print(1)
          for p in perm:
            if p:
              dict_perms[perm_type]['perms'].append(p)
          list_perm_lines.append(line)
          dict_perms[perm_type]['req'].append(req)
          if call:
            call_lines = [line]
            P = False
            C = True

        elif '@RequiresPermission' not in line and P:
          P = False
          C = True
          call = None
          params = []
          call_lines = [line]
          call_str = line.replace('\n','')
          call_parts = call_str.split(' ')
          if 'static' in call_str and '=' in call_str:
            call_parts = call_str.split(' =')[0].split(' ')
            call = call_parts[-1]
            C = False
          elif '=' in call_str and call_str.endswith('null;'):
            call_parts = call_str.split(' =')[0].split(' ')
            call = call_parts[-1]
            C = False
          elif '=' in call_str and call_str.endswith('ArrayList<>();'):
            call_parts = call_str.split(' =')[0].split(' ')
            call = call_parts[-1]
            C = False
          elif call_parts[-1].endswith(';') and call_parts[-2] == '=':
            call_parts = call_str.split(' =')[0].split(' ')
            call = call_parts[-1]
            C = False
          elif call_str == '})':
            P = True
            continue
          else:
            call_parts = call_str.split(' ')
            for t in call_parts: ##
              if '(' in t and not call:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe and call_maybe:
                  call = call_maybe + '()'
                  param1 = t.replace(f'{call_maybe}(','')
                  if param1 != ')':
                    params.append(param1) #-------------
              elif '(' in t and call:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe and call_maybe:
                  call = call_maybe + '()' ##
                else:
                  params.append(call_maybe)
                param1 = t.split('(')[1]
                if param1 != ')':
                  params.append(param1)
              elif call:
                params.append(t) #----------------
            if call:
              if call_parts[-1] == '{': ##
                C = False
                if params:
                  params.remove('{')
                  if params:
                    params[-1] = params[-1][:-1]
              elif call_parts[-1].endswith('){'):
                C = False
                if params:
                  params[-1] = params[-1][:-2]
              elif call_parts[-1].endswith(');'):
                C = False
                if params:
                  params[-1] = params[-1][:-2]
              elif call_parts[-1].endswith(')'):
                C = False
                if params:
                  params[-1] = params[-1][:-1]
              elif call_parts[-1].endswith(','):
                if params:
                  params[-1] = params[-1][:-1]
              elif call_parts[-1].endswith('('):
                pass
              else:
                print(1)
            else:
              t = call_parts[-1]
              if '(' in t:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe and call_maybe:
                  call = call_maybe + '()'
            if not call:
              if call_parts[-1] == '{':
                call = call_parts[-2]
                C = False
              elif call_parts[-1] == '=':
                call = call_parts[-2]
                C = False
              elif call_str.endswith(';'):
                call = call_parts[-1][:-1]
                C = False
              elif content[i+1].strip().startswith('='):
                call = call_parts[-1]
                C = False
              else:
                print('',end='') #
                pass

        elif not P and C:
          call_str = line.replace('\n','').replace('{ }','{')
          call_parts = call_str.split(' ')
          call_lines.append(line)
          all_params_in = False
          if call and not params:
            params = []
          for t in call_parts[:-1]:
            if t == 'throws':
              all_params_in = True
              break
            params.append(t)
          if all_params_in:
            C = False
            params[-1] = re.sub('\)|\;|', '', params[-1])
          elif call_parts[-1] in ['{', '=']:
            C = False
            if not call:
              for t in call_parts: ##
                if '(' in t and not call:
                  call_maybe = t.split('(')[0]
                  if '@' not in call_maybe and call_maybe:
                    call = call_maybe + '()'
                    param1 = t.replace(f'{call_maybe}(','')
                    if param1 != ')':
                      params.append(param1)
                elif '(' in t and call:
                  call_maybe = t.split('(')[0]
                  if '@' not in call_maybe and call_maybe:
                    call = call_maybe + '()' ##
                  else:
                    params.append(call_maybe)
                  param1 = t.split('(')[1]
                  if param1 != ')':
                    params.append(param1)
                elif call:
                  params.append(t)
              # for t in call_parts[:-1]:
              #   if '(' in t:
              #     if ')' not in t:
              #       call_maybe,param2 = t.split('(')
              #       if call_maybe:
              #         call = call_maybe + '()'
              #       if param2:
              #         if not params:
              #           params = [param2]
              #         else:
              #           params.append(param2)
              #     else:
              #       call = t.split('(')[0] + '()'
              if not call:
                call = call_parts[-2]
            if params:
              if not params[-1][-1].isalpha():
                params[-1] = params[-1][:-1]
          elif call_parts[-1].endswith(','):
            params.append(call_parts[-1][:-1])
          elif call_parts[-1] == 'throws':
            C = False
            if params:
              params[-1] = params[-1][:-1]
          elif call and call_parts[-1].endswith(')'):
            C = False
            params.append(call_parts[-1][:-1])
          elif call and call_parts[-1].endswith(');'):
            C = False
            params.append(call_parts[-1][:-2])
          elif call and call_parts[-1][-1].isalpha():
            params.append(call_parts[-1])
          else:
            try:
              if content[i+1].strip().startswith(')'):
                C = False
                params.append(call_parts[-1])
              else:
                print(1)
            except IndexError:
              print(1)
        
        elif '@RequiresPermission' in line and P:
          # if line.startswith('@') and not line.startswith('@Nullable'):
          #   # print(1)
          #   continue
          if 'RequiresPermission' in path_file:
            continue
          P = False
          C = True
          call = None
          params = []
          call_lines = [line]
          call_str = line.replace('\n','')
          if 'static' in call_str and '=' in call_str:
            call_parts = call_str.split(' =')[0].split(' ')
            call = call_parts[-1]
            C = False
          else:
            call_parts = call_str.split(' ')
            for t in call_parts: ##
              if '(' in t and not call:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe and call_maybe:
                  call = call_maybe + '()'
                  param1 = t.replace(f'{call_maybe}(','')
                  if param1 != ')':
                    params.append(param1)
              elif '(' in t and call:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe and call_maybe:
                  call = call_maybe + '()' ##
                else:
                  params.append(call_maybe)
                param1 = t.split('(')[1]
                if param1 != ')':
                  params.append(param1)
              elif call:
                params.append(t)
            if call:
              if call_parts[-1] == '{': ##
                C = False
                if params:
                  params.remove('{')
                  params[-1] = params[-1][:-1]
              elif call_str.endswith(';') and not call_str.endswith(');'):
                call = call_parts[-1][:-1]
                C = False
              elif call_str.endswith(');'):
                params.append(call_parts[-1][:-2]) 
                C = False
              else:
                params.append(call_parts[-1]) ##
            else:
              t = call_parts[-1]
              if '(' in t:
                call_maybe = t.split('(')[0]
                if '@' not in call_maybe:
                  call = call_maybe + '()'
            if not call and call_parts[-1] == '{':
              call = call_parts[-2]
              C = False
          # print(1) ##
        
        if I and not P and not C:
          if not call:
            print(1)
          if call.endswith('('):
            call += ')'
          if call.endswith(')') and not call.endswith('()'):
            call = call[:-1]+'()'
          if call == '()':
            print(1)
          if call_lines == None:
            print(1)
          if list_perm_lines == None:
            print(1)
          if params == None:
            print(1)
          data_call = OrderedDict({
            'name': call,
            'class': block_class,
            'perm_lines': list_perm_lines,
            'call_lines': call_lines,
            'params': params,
            'perms': dict_perms,
            'path': path_file_partial,
          })
          data_calls.append(data_call)
          I = False
      
      if not data_call:
        print(1)
  
    except ContinueI:
      count_exceptions += 1
      continue
      
    
  # if data_calls:
    # print(path_file)
    # for d in data_calls: ##
    #   for k,v in d.items():
    #     print(f'{k}:\n {v}')
    #   print()
    # print('---------------------------------------------------------------------------')
  return data_calls,count_exceptions


def extract_calls_permissions(path_dir):

  abspath_dir = f'{path_script}/{path_dir}'
  folder_name_out = path_dir.replace('/','.')

  path_out = f'{path_script}/{path_output_s}/{folder_name_out}'
  if not os.path.exists(path_out):
    os.mkdir(path_out)
    paths_files = get_filepaths(abspath_dir)
    with io.open(f'{path_out}/filepaths.txt','w') as pout:
      for p in paths_files:
        prel = p.replace(abspath_dir,'')
        pout.write(f'{prel}\n')
  else:
    paths_files = []
    with io.open(f'{path_out}/filepaths.txt','r') as pout:
      for p in pout.readlines():
        paths_files.append(f'{abspath_dir}{p.strip()}')
  
  path_files_done = []
  if not os.path.exists(f'{path_out}/filepaths_done.txt'):
    with io.open(f'{path_out}/filepaths_done.txt','w') as dout:
      pass
  else:
    with io.open(f'{path_out}/filepaths_done.txt','r') as pin:
      for p in pin.readlines():
        pabs = abspath_dir + p.replace('\n','')
        path_files_done.append(pabs)

  file_name = 'calls_w_perms'
  dict_calls = OrderedDict()

  reqperm_count = 0
  total_count = 0

  with io.open(f'{path_out}/filepaths_done.txt','a') as dout, io.open(f'{path_out}/{file_name}.json','a') as jout:
    while paths_files:
      path_file = None
      try:
        path_file = paths_files.pop()
      except IndexError:
        break

      if path_file not in path_files_done:
        reqperm_count_one = count_reqperm_tag_one(path_file)
        # if reqperm_count_one:
        #   print(reqperm_count_one)
        list_callitems,err = extract_one(path_file)
        if len(list_callitems) < reqperm_count_one:
          print(1)
        if not err:
          if list_callitems:
            list_callitems_parsed,count_exceptions = compile_items(list_callitems,path_file)
            if len(list_callitems_parsed) < reqperm_count_one - count_exceptions:
              print(1)
            for data_item in list_callitems_parsed:
              
              total_count += 1
              path_rel = path_file.replace(f'{path_script}/{path_dir}','')
              hashl = hashlib.sha1(str(data_item).encode()).hexdigest()
              dict_calls[hashl] = OrderedDict({
                'name': data_item['name'],
                'class': data_item['class'],
                'perms': data_item['perms'],
                'params': data_item['params'],              
                'call_lines': data_item['call_lines'], 
                'perm_lines': data_item['perm_lines'],
                'path_file': path_rel
                })
              jline = json.dumps({hashl : dict_calls[hashl]})
              jout.write(f'{jline}\n')
            jout.flush()
        prel = path_file.replace(abspath_dir,'')
        dout.write(f'{prel}\n')
        dout.flush()

  # with io.open(f'{path_out}/{file_name}.json','w') as jout:
  #   for xh, xm in dict_calls.items():
  #     temp_jdict = {xh: xm}
  #     jline = json.dumps(temp_jdict)
  #     jout.write(jline + "\n")

  print(f'ITEMS: {total_count}')
  print('-----------------------------------------------------------')


def stats_methods(name_end):

  data_calls_tot = OrderedDict({
    '10':set(),
    '11':set(),
    '12':set(),
    '13':set(),
  })

  for item in sorted(os.listdir(f'{path_script}/{path_output_s}')):
    item_path = f'{path_script}/{path_output_s}/{item}'
    if os.path.isdir(item_path) and item.endswith(name_end):

      if '10' in item:
        ver = '10'
      elif '11' in item:
        ver = '11'
      elif '12' in item:
        ver = '12'
      elif '13' in item:
        ver = '13'
      else:
        raise Exception
        
      with io.open(f'{item_path}/calls_w_perms.json','r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              # pf = v['path_file'].split('.')[0]
              # pc = f'{pf}_{k}'
              hashl = hashlib.sha1(str(v).encode()).hexdigest()
              data_calls_tot[ver].add(hashl)
        del k,v,line,xline,jdata
  
  stot = set()
  for ver, s in data_calls_tot.items():
    print(f'{ver}, {len(s)}')
    for h in s:
      stot.add(h)
  print(len(stot))


def compile_mapping(name_end):
  
  vers = [10,11,12,13]
  if not name_end:
    print('provide name!')
    return
  mapping_calls = OrderedDict()

  logfile = f'log_compile_mapping_{name_end}.txt'
  regex = re.compile('[^a-zA-Z0-9_@[]]')
  # resplit = re.split(';|Landroid|Ljavax|Ljava|Lcom|Lorg|Llibcore|Lsun|Ldalvik|Ljdk')
  not_params = [
    # 'String',
  ]
  # not_params.append(str(set(['I'])))
  # not_params.append(str(set(['V'])))
  skip_items = [
    # 'data.source.10.base-refs_heads_android10-s3-release',
    # 'data.source.11.base-refs_heads_android11-s1-release',
    # 'data.source.12.base-refs_heads_android12-s5-release',
    # 'data.source.13.base-refs_heads_android13-s3-release',
  ]
  param_types = {
    'I': 'int',
    '[I': 'int[]',
    'J': 'long',
    '[J': 'long[]',
    'Z': 'boolean',
    '[Z': 'boolean[]',
    'F': 'float',
    '[F': 'float[]',
    'B': 'byte',
    '[B': 'byte[]',
    'C': 'char',
    '[C': 'char[]',
    'D': 'double',
    '[D': 'double[]',
    'S': 'short',
    '[S': 'short[]',
    # 'L': 'interface',
    'V': 'void',
  }
  params_set = set()

  rls = OrderedDict()
  for ver in vers:
    _,rls[ver] = get_restriction_lists(ver)

  for item in sorted(os.listdir(f'{path_script}/{path_output_s}')):
    item_path = f'{path_script}/{path_output_s}/{item}'
    if os.path.isdir(item_path) and item.endswith(name_end):
      if item in skip_items:
        continue
      
      log_data(logfile,f'\n{item}','\n') # --uncomment
      if '10' in item:
        ver = 10
      elif '11' in item:
        ver = 11
      elif '12' in item:
        ver = 12
      elif '13' in item:
        ver = 13
      else:
        raise Exception
      
      data_list,_ = get_restriction_lists(ver)

      data_rl = OrderedDict()
      for line in data_list:
        if line[0] not in data_rl.keys():
          data_rl[line[0]] = [line,]
        else:
          data_rl[line[0]].append(line)

      
      data_calls = OrderedDict()
        
      with io.open(f'{item_path}/calls_w_perms.json','r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for h,cv in jdata.items():
              pf = cv['path_file'].split('.')[0]
              k = cv['name']
              pc = f'{pf}#{k}#{h}'
              if not pc in data_calls:
                data_calls[pc] = cv
              else:
                check = data_calls[pc]
                print(1)
        del h,cv,pf,k,pc,line,xline,jdata
      
      h_used = []
      calls_wo_method = 0
      calls_tot = 0
      c_many = 0
      c_one = 0
      c_none = 0
      for path,lists in data_rl.items():

        endl = ' ' * (120 - len(path))
        log_data(logfile,f'  {ver}  {path}',endl) # --uncomment
        path_count = 0
        funcs_by_path = OrderedDict()
        for path_func in data_calls.keys():
          p1 = path.split('/')[-1]
          p2 = path_func.split('#')[0].split('/')[-1]
          if path in path_func and p1 == p2:
            funcs_by_path[path_func.split('#')[2]] = path_func

        for l in lists:
          call = None
          h_use = None
          path_func_use = None
          
          # if '/LightsManager' in l[0]:
          #   print(1)
          # if 'BluetoothA2dp' in l[0]:
          #   print(1)
          # if '/TunerConfiguration' in l[0]:
          #   print(1)
          # if '/TelephonyCallback' in l[0]:
          #   print(1)
          # if '/AudioRecord' in l[0]:
          #   print(1) # --breakpoint # --uncomment
          # else:
          #   continue

          calls_tot += 1
          if l[2] == '<init>':
            method = l[1]
            if not method:
              method = l[0].split('/')[-1]
          elif l[2] == '<clinit>':
            method = l[0].split('/')[-1]
          else:
            method = l[2]
          
          # if method == 'getLteOnCdmaMode':
          #   print(1)
          # if method == 'getMsisdn':
          #   print(1)
          # if method == 'getVoiceMessageCount':
          #   print(1)

          func_similar = OrderedDict()
          for h,path_func in funcs_by_path.items():
            func = regex.sub('', path_func.split('#')[1]).replace('()','')
            if func == method and h not in h_used:
              func_similar[h] = path_func
          
          # m_class = l[1]
          # m_params = l[3]#+';'+l[4]
          # m_params_pathlist = re.split(';|Landroid|Ljavax|Ljava|Lcom|Lorg|Llibcore|Lsun|Ldalvik|Ljdk',m_params)

          # for param in m_params_pathlist:
          #   if param:
          #     if '/' not in param:
          #       params_set.add(param)
          # if func_similar:
          #   print(1)
          
          if len(func_similar.keys()) > 1:
            c_many += 1
            m_class = l[1]
            m_params = l[3]#+';'+l[4]
            m_params_pathlist = re.split(';|Landroid|Ljavax|Ljava|Lcom|Lorg|Llibcore|Lsun|Ldalvik|Ljdk',m_params)

            # m_params_list_pre = [x.split('/')[-1].split('$')[-1] for x in m_params_pathlist]
            m_params_list = []
            add_to_l = False
            for param in m_params_pathlist:
              if add_to_l and '/' not in param:
                print(1)
              if param:
                if '/' in param:
                  param = param.split('/')[-1].split('$')[-1]
                  if add_to_l:
                    param = param + '[]'
                    add_to_l = False
                  m_params_list.append(param)
                else:
                  cntrl = -1
                  for x in range(len(param)):
                    if x <= cntrl:
                      continue
                    char = param[x]
                    if char == '[':
                      try:
                        m_param = param[x] + param[x+1]
                        m_param_val = param_types[m_param]
                        cntrl = x+1
                      except IndexError:
                        add_to_l = True
                        continue
                    else:
                      m_param_val = param_types[char]
                    m_params_list.append(m_param_val)
                
            m_datal = []
            m_matches = []
            m_matches_partial = OrderedDict()
            m_params_paths = []
            for h,path_func in func_similar.items():
              
              func_data = data_calls[path_func]
              func_class = func_data['class']
              params_class = []
              params_paths = []
              matches = True
              for param in func_data['params']:
                if param.startswith('@'):
                  continue
                if '<' in param:
                  param = param.split('<')[0]
                if '.' in param:
                  param = param.split('.')[-1]
                  param_path = '$'.join(param.split('.'))
                  params_paths.append(param_path)
                  m_params_paths.append(h)
                param = regex.sub('', param)
                if not param:
                  continue
                if param == 'throws': # --breakpoint
                  break
                if param[0].isupper():
                  params_class.append(param)
                if '[]' in param and not param.endswith('[]'):
                  param = param.split('[]')[0]+'[]'
                if param in param_types.values():
                  params_class.append(param)
              m_datal.append(func_data)
              m_datal.append(params_class)

              if params_class != m_params_list:
                matches = False
              if m_class != func_class:
                matches = False
              if params_paths:
                for parp in params_paths:
                  if parp not in m_params:
                    matches = False
              

              # if len(params_class) == len(m_params_list):
              #   for param in m_params_list:
              #     if len(m_params_list) == 0:
              #       break
              #     if param not in params_class:
              #       matches = False
              #     if params_class.count(param) != m_params_list.count(param):
              #       matches = False
              # else:
              #   matches = False
              m_matches_partial[h] = []
              for param in params_class:
                if param in m_params_list:
                  m_matches_partial[h].append(param)
              if matches:
                m_matches.append(h)

            if len(m_matches) > 1:
              m_matches_2 = []
              if m_params_paths:
                for maybe_h in m_matches:
                  if maybe_h in m_params_paths:
                    m_matches_2.append(maybe_h)
                if len(m_matches_2) > 1:
                  print(1)
                else:
                  h_use = m_matches_2[0]
                  path_func_use = func_similar[h_use]
              else:
                print(1) # --breakpoint
            elif len(m_matches) == 0:
              c_none += 1
              calls_wo_method += 1
              continue
            else:
              h_use = m_matches[0]
              path_func_use = func_similar[h_use]
          elif len(func_similar.keys()) == 1:
            c_one += 1
            for h,path_func in func_similar.items():
              h_use = h
              path_func_use = path_func
          else:
            c_none += 1
            pass

          if not func_similar:
            calls_wo_method += 1
            continue
          
          h_used.append(h_use)
          func = path_func_use.split('#')[1].replace('()','')
          if func == method:

            path_count += 1
            func_data = data_calls[path_func]

            call = l[6].split(',')[0]

            if call not in mapping_calls.keys():
              mapping_calls[call] = OrderedDict({
                'seen_in_source': [ver],
                'seen_in_lists': [],
                'versions': OrderedDict({})
              })
              mapping_calls[call]['versions'][str(ver)] = OrderedDict({
                'version': str(ver),
                'invocation': path_func,
                'perms': func_data['perms'],
                'rl': l[5],
                'restr': d_rl_restr[l[5]],
                'restr_line': l[6],
                'perms_changed': None,
                'restrs_changed': None,
                'alt': None
              })
            else:
              if str(ver) not in mapping_calls[call]['versions'].keys():
                mapping_calls[call]['seen_in_source'].append(ver)
                mapping_calls[call]['versions'][str(ver)] = OrderedDict({
                  'version': str(ver),
                  'invocation': path_func,
                  'perms': func_data['perms'],
                  'rl': l[5],
                  'restr': d_rl_restr[l[5]],
                  'restr_line': l[6],
                  'perms_changed': None,
                  'restrs_changed': None,
                  'alt': None
                })
              else:
                CHECK = mapping_calls[call]
                print(1) # --breakpoint
          
          if func_similar and not call:
            print(1) # --breakpoint
        log_data(logfile,path_count,'\n')
      
      not_used = []
      methods_tot = 0
      for k in data_calls.keys():
        methods_tot += 1
        khash = k.split('#')[-1]
        if khash not in h_used:
          not_used.append(k)
      log_data(logfile,f'--- METHODS TOTAL : {methods_tot} ---','\n')
      log_data(logfile,f'--- NOT USED      : {len(not_used)} ---','\n')
      for k in not_used:
        log_data(logfile,k,'\n')
      
      log_data(logfile,f'CALLS TOTAL          : {calls_tot}','\n')
      log_data(logfile,f'CALLS WITH METHOD    : {len(h_used)}','\n')
      log_data(logfile,f'CALLS WITHOUT METHOD : {calls_wo_method}','\n')

  # for pr in params_set:
  #   log_data('paramsvariants.txt',pr,'\n')

  with io.open(f'{path_script}/{path_output_s}/{name_end}.json','w') as jout:
    json.dump(mapping_calls, jout, indent = 2)
  log_data(logfile,f'\ntotal calls w perms: {len(mapping_calls)}','')
  

  changes = get_changes()
  for call,data in mapping_calls.items():

    for ver in vers:
      if call in rls[ver]:
        data['seen_in_lists'].append(ver)
    
    ver_prev = data['seen_in_source'][0]
    for ver in data['seen_in_source'][1:]:
      if data['versions'][f'{ver}']['perms'] != data['versions'][f'{ver_prev}']['perms']:
        data['versions'][f'{ver}']['perms_changed'] = True
      else:
        data['versions'][f'{ver}']['perms_changed'] = False
      if data['versions'][f'{ver}']['restr'] != data['versions'][f'{ver_prev}']['restr']:
        # a1 =data['versions'][f'{ver_prev}']['l_restrictions']
        # a2 =data['versions'][f'{ver}']['l_restrictions']
        data['versions'][f'{ver}']['restrs_changed'] = True
      else:
        data['versions'][f'{ver}']['restrs_changed'] = False
      ver_prev = ver
    
    for ver in data['seen_in_source']:
      if ver != 10:
        if call in changes[str(ver)].keys():
          data['versions'][str(ver)]['alt'] = changes[str(ver)][call]

    mapping_calls[call] = data

  with io.open(f'{path_script}/{path_output_s}/{name_end}_calls.json','w') as jout:
    json.dump(mapping_calls, jout, indent = 2)
    

def get_changes():

  changes = OrderedDict()
  for item in os.listdir(f'{path_script}/{path_source}'):
    if os.path.isfile(f'{path_script}/{path_source}/{item}') and 'changes' in item:
      with io.open(f'{path_script}/{path_source}/{item}','r') as cin:
        ver = item.split('-')[1]
        changes[ver] = OrderedDict()
        for line in cin.readlines():
          # print(1)
          alt = None
          call = line.split(' ')[0]
          if '# Use new ' in line:
            line = line.replace('# Use new ','# Use ')
          if '# Use' in line and 'instead' in line:
            alt = line.split('# Use')[1].strip().split('instead')[0].strip()#.replace('#','')
          elif '# Use' in line:
            part = line.split('# Use')[1].strip()
            if ')' in part:
              alt = part.split(')')[0] + ')'
            else:
              alt = part.split(' ')[0]
          if alt and alt.endswith('.'):
            alt = alt[:-1]
          if alt and alt.endswith(' public API'):
            alt = alt.replace(' public API','')
          
          if alt:
            changes[ver][call] = alt

          # if alt:
          #   print(line[:-1])
          #   print(alt)
          #   print()
  
  return changes


def stats_mapping(name):
  vers = ['10','11','12','13']
  if not name:
    print('provide name!')
    return
  with io.open(f'{path_script}/{path_output_s}/{name}.json','r') as jin:
    mapping = json.load(jin)

    dstats = OrderedDict()
    dstats['items'] = 0
    dstats['items_unique'] = set()
    dstats['items_per_source'] = OrderedDict()
    dstats['items_per_nonsdk'] = OrderedDict()
    dstats['items_source_combs'] = OrderedDict()
    dstats['items_nonsdk_combs'] = OrderedDict()
    dstats['items_perms_changed'] = OrderedDict({
      '10-11': 0,
      '11-12': 0,
      '12-13': 0
    })
    dstats['items_perms_unique'] = set()
    dstats['items_perms_count'] = OrderedDict()
    dstats['items_perms_type'] = OrderedDict({
      'basic': [],
      'read': [],
      'write': [],
      'tot': []
    })
    dstats['items_multiperm'] = OrderedDict({
      'basic': [],
      'read': [],
      'write': [],
      'tot': []
    })
    dstats['items_multiperm_req'] = OrderedDict({
      'basic': OrderedDict({'any':0,'all':0}),
      'read': OrderedDict({'any':0,'all':0}),
      'write': OrderedDict({'any':0,'all':0}),
      'tot': OrderedDict({'any':0,'all':0})
    })
    dstats['items_perms_params_count'] = OrderedDict()

    dstats['items_calls_counts'] = []
    dstats['calls_restrictions_lists_count'] = OrderedDict()
    dstats['calls_restrictions_count'] = OrderedDict()
    dstats['items_restrs_changed'] = OrderedDict({
      '10-11': 0,
      '11-12': 0,
      '12-13': 0
    })


    for ver in vers:
      dstats[ver] = OrderedDict()
      dstats[ver]['items'] = 0
      dstats['items_per_source'][ver] = 0
      dstats['items_per_nonsdk'][ver] = 0
      dstats[ver]['items_perms_unique'] = set()
      dstats[ver]['items_perms_count'] = OrderedDict()
      dstats[ver]['items_perms_type'] = OrderedDict({
        'basic': [],
        'read': [],
        'write': [],
        'tot': []
      })
      dstats[ver]['items_multiperm'] = OrderedDict({
        'basic': [],
        'read': [],
        'write': [],
        'tot': []
      })
      dstats[ver]['items_multiperm_req'] = OrderedDict({
        'basic': OrderedDict({'any':0,'all':0}),
        'read': OrderedDict({'any':0,'all':0}),
        'write': OrderedDict({'any':0,'all':0}),
        'tot': OrderedDict({'any':0,'all':0})
      })
      dstats[ver]['items_perms_params_count'] = OrderedDict()

      dstats[ver]['items_calls_counts'] = []
      dstats[ver]['calls_restrictions_lists_count'] = OrderedDict()
      dstats[ver]['calls_restrictions_count'] = OrderedDict()


    for path,data in mapping.items():
      dstats['items'] += 1

      dstats['items_unique'].add(path)

      for v in data['seen_in_source']:
        dstats['items_per_source'][str(v)] += 1

      for v in data['seen_in_lists']:
        dstats['items_per_nonsdk'][str(v)] += 1

      scomb = str(data['seen_in_source'])
      if scomb not in dstats['items_source_combs']:
        dstats['items_source_combs'][scomb] = 1
      else:
        dstats['items_source_combs'][scomb] += 1

      lcomb = str(data['seen_in_lists'])
      if lcomb not in dstats['items_nonsdk_combs']:
        dstats['items_nonsdk_combs'][lcomb] = 1
      else:
        dstats['items_nonsdk_combs'][lcomb] += 1

      for v,d in data['versions'].items():
        if v == '11':
          if d['perms_changed']:
            dstats['items_perms_changed']['10-11'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['10-11'] += 1
        if v == '12':
          if d['perms_changed']:
            dstats['items_perms_changed']['11-12'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['11-12'] += 1
        if v == '13':
          if d['perms_changed']:
            dstats['items_perms_changed']['12-13'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['12-13'] += 1
        
        for ptype,pd in d['perms'].items():
          if pd['perms']:
            for p in pd['perms']:
              dstats['items_perms_unique'].add(p)

              if p not in dstats['items_perms_count']:
                dstats['items_perms_count'][p] = 1
              else:
                dstats['items_perms_count'][p] += 1

            dstats['items_perms_type'][ptype].append(path)
            dstats['items_perms_type']['tot'].append(path)

            if len(pd['perms']) > 1:
              dstats['items_multiperm'][ptype].append(path)
              dstats['items_multiperm']['tot'].append(path)

              dstats['items_multiperm_req'][ptype][pd['req'][0]] += 1
              dstats['items_multiperm_req']['tot'][pd['req'][0]] += 1
            
            if pd['params']:
              for param in pd['params']:
                if param not in dstats['items_perms_params_count'].keys():
                  dstats['items_perms_params_count'][param] = 1
                else:
                  dstats['items_perms_params_count'][param] += 1
            
        dstats['items_calls_counts'].append(len(d['restr_lines']))

        for rl in d['l_restriction_lists']:
          if rl not in dstats['calls_restrictions_lists_count'].keys():
            dstats['calls_restrictions_lists_count'][rl] = 1
          else:
            dstats['calls_restrictions_lists_count'][rl] += 1
        
        for rl in d['l_restrictions']:
          if rl not in dstats['calls_restrictions_count'].keys():
            dstats['calls_restrictions_count'][rl] = 1
          else:
            dstats['calls_restrictions_count'][rl] += 1


      for v,d in data['versions'].items():
        dstats[v]['items'] += 1
        if dstats[v]['items_perms_type']['read']:
          print(1)
        if dstats[v]['items_perms_type']['write']:
          print(1)

        for ptype,pd in d['perms'].items():
          if pd['perms']:
            for p in pd['perms']:
              dstats[v]['items_perms_unique'].add(p)

              if p not in dstats[v]['items_perms_count']:
                dstats[v]['items_perms_count'][p] = 1
              else:
                dstats[v]['items_perms_count'][p] += 1

            dstats[v]['items_perms_type'][ptype].append(path)
            dstats[v]['items_perms_type']['tot'].append(path)

            if len(pd['perms']) > 1:
              dstats[v]['items_multiperm'][ptype].append(path)
              dstats[v]['items_multiperm']['tot'].append(path)

              dstats[v]['items_multiperm_req'][ptype][pd['req'][0]] += 1
              dstats[v]['items_multiperm_req']['tot'][pd['req'][0]] += 1
            
            if pd['params']:
              for param in pd['params']:
                if param not in dstats[v]['items_perms_params_count'].keys():
                  dstats[v]['items_perms_params_count'][param] = 1
                else:
                  dstats[v]['items_perms_params_count'][param] += 1
            
        dstats[v]['items_calls_counts'].append(len(d['restr_lines']))

        for rl in d['l_restriction_lists']:
          if rl not in dstats[v]['calls_restrictions_lists_count'].keys():
            dstats[v]['calls_restrictions_lists_count'][rl] = 1
          else:
            dstats[v]['calls_restrictions_lists_count'][rl] += 1
        
        for rl in d['l_restrictions']:
          if rl not in dstats[v]['calls_restrictions_count'].keys():
            dstats[v]['calls_restrictions_count'][rl] = 1
          else:
            dstats[v]['calls_restrictions_count'][rl] += 1

    del d,data,jin,lcomb,p,param,path,pd,ptype,rl,scomb,v,ver
      
    # print(1)
    s = dstats['items']
    print(f'items total: {s}')
    s = len(dstats['items_unique'])
    print(f'items unique: {s}')
    print('items per source version:')
    for v in vers:
      s = dstats['items_per_source']
      print(f'  {v}: {s[v]}')
    print('items linked per nonsdk file version:')
    for v in vers:
      s = dstats['items_per_nonsdk']
      print(f'  {v}: {s[v]}')
    print('source version combinations for items:')
    ss = dstats['items_source_combs']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('nonsdk version combinations for items:')
    ss = dstats['items_nonsdk_combs']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    print('item permissions changed between versions:')
    ss = dstats['items_perms_changed']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    s = len(dstats['items_perms_unique'])
    print(f'unique permissions seen: {s}')
    pmaxn = max(dstats['items_perms_count'].items(), key=lambda x: x[1])
    pminn = min(dstats['items_perms_count'].items(), key=lambda x: x[1])
    print(f'  most times seen - {pmaxn[0]}: {pmaxn[1]}')
    print(f'  least times seen - {pminn[0]}: {pminn[1]}')
    print('permissions required:')
    ss = dstats['items_perms_type']
    for k,v in ss.items():
      print(f'  {k}: {len(v)}')
    print('multiple permissions required:')
    ss = dstats['items_multiperm']
    for k,v in ss.items():
      print(f'  {k}: {len(v)}')
    print('multiple permissions requirements:')
    ss = dstats['items_multiperm_req']
    for k,v in ss.items():
      print(f'  {k}')
      for f,b in v.items():
        print(f'    {f}: {b}')
    print('parameters for permission requirements:')
    ss = dstats['items_perms_params_count']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    s = sum(dstats['items_calls_counts'])
    print(f'total calls for items with perms: {s}')
    s = min(dstats['items_calls_counts'])
    print(f'minimum calls for items with perms: {s}')
    s = max(dstats['items_calls_counts'])
    print(f'maximum calls for items with perms: {s}')
    s = round(sum(dstats['items_calls_counts'])/len(dstats['items_calls_counts']),3)
    print(f'average calls for items with perms: {s}')
    print('restriction lists combinations for calls:')
    ss = dict(sorted(dstats['calls_restrictions_lists_count'].items(), key=lambda item: item[1],reverse=True))
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('restrictions for calls:')
    ss = dict(sorted(dstats['calls_restrictions_count'].items(), key=lambda item: item[1],reverse=True))
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('item calls restrictions changed between versions:')
    ss = dstats['items_restrs_changed']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    for ver in vers:
      print('unique permissions seen:')
      s = len(dstats[ver]['items_perms_unique'])
      print(f'  {ver} {s}')
    for ver in vers:
      print(f'{ver}')
      pmaxn = max(dstats[ver]['items_perms_count'].items(), key=lambda x: x[1])
      pminn = min(dstats[ver]['items_perms_count'].items(), key=lambda x: x[1])
      print(f'  most times seen - {pmaxn[0]}: {pmaxn[1]}')
      print(f'  least times seen - {pminn[0]}: {pminn[1]}')
    print('permissions required:')
    for ver in vers:
      print(f'{ver}')
      ss = dstats[ver]['items_perms_type']
      for k,v in ss.items():
        print(f'    {k}: {len(v)}')
    print('multiple permissions required:')
    for ver in vers:
      print(f'{ver}')
      ss = dstats[ver]['items_multiperm']
      for k,v in ss.items():
        print(f'    {k}: {len(v)}')
    print('multiple permissions requirements:')
    for ver in vers:
      print(f'  {ver}')
      ss = dstats[ver]['items_multiperm_req']
      for k,v in ss.items():
        print(f'  {k}')
        for f,b in v.items():
          print(f'    {f}: {b}')
    print('parameters for permission requirements:')
    for ver in vers:
      print(f'  {ver}')
      ss = dstats[ver]['items_perms_params_count']
      for k,v in ss.items():
        print(f'    {k}: {v}')
    print()

    for ver in vers:
      print(f'{ver}')
      s = sum(dstats[ver]['items_calls_counts'])
      print(f'  total calls for items with perms: {s}')
      s = min(dstats[ver]['items_calls_counts'])
      print(f'  minimum calls for items with perms: {s}')
      s = max(dstats[ver]['items_calls_counts'])
      print(f'  maximum calls for items with perms: {s}')
      s = sum(dstats[ver]['items_calls_counts'])/len(dstats[ver]['items_calls_counts'])
      print(f'  average calls for items with perms: {s}')
    print('restriction lists combinations for calls:')
    for ver in vers:
      print(f'  {ver}')
      ss = dict(sorted(dstats[ver]['calls_restrictions_lists_count'].items(), key=lambda item: item[1],reverse=True))
      for k,v in ss.items():
        print(f'    {k}: {v}')
    print('restrictions for calls:')
    for ver in vers:
      print(f'  {ver}')
      ss = dict(sorted(dstats[ver]['calls_restrictions_count'].items(), key=lambda item: item[1],reverse=True))
      for k,v in ss.items():
        print(f'    {k}: {v}')
    print()


def stats_mapping_calls(name):
  vers = ['10','11','12','13']
  if not name:
    print('provide name!')
    return
  with io.open(f'{path_script}/{path_output_s}/{name}.json','r') as jin:
    mapping = json.load(jin)

    dstats = OrderedDict()
    dstats['items'] = 0
    dstats['items_unique'] = set()
    dstats['items_per_source'] = OrderedDict()
    dstats['items_per_nonsdk'] = OrderedDict()
    dstats['items_source_combs'] = OrderedDict()
    dstats['items_nonsdk_combs'] = OrderedDict()
    dstats['items_perms_changed'] = OrderedDict({
      '10-11': 0,
      '11-12': 0,
      '12-13': 0
    })
    dstats['items_perms_unique'] = set()
    dstats['items_perms_count'] = OrderedDict()
    dstats['items_perms_type'] = OrderedDict({
      'basic': [],
      'read': [],
      'write': [],
      'tot': []
    })
    dstats['items_multiperm'] = OrderedDict({
      'basic': [],
      'read': [],
      'write': [],
      'tot': []
    })
    dstats['items_multiperm_req'] = OrderedDict({
      'basic': OrderedDict({'any':0,'all':0}),
      'read': OrderedDict({'any':0,'all':0}),
      'write': OrderedDict({'any':0,'all':0}),
      'tot': OrderedDict({'any':0,'all':0})
    })
    dstats['items_perms_params_count'] = OrderedDict()

    dstats['items_calls_counts'] = []
    dstats['calls_restrictions_lists_count'] = OrderedDict()
    dstats['calls_restrictions_count'] = OrderedDict()
    dstats['items_restrs_changed'] = OrderedDict({
      '10-11': 0,
      '11-12': 0,
      '12-13': 0
    })
    dstats['alt_count'] = 0


    for ver in vers:
      dstats[ver] = OrderedDict()
      dstats[ver]['items'] = 0
      dstats['items_per_source'][ver] = 0
      dstats['items_per_nonsdk'][ver] = 0
      dstats[ver]['items_perms_unique'] = set()
      dstats[ver]['items_perms_count'] = OrderedDict()
      dstats[ver]['items_perms_type'] = OrderedDict({
        'basic': [],
        'read': [],
        'write': [],
        'tot': []
      })
      dstats[ver]['items_multiperm'] = OrderedDict({
        'basic': [],
        'read': [],
        'write': [],
        'tot': []
      })
      dstats[ver]['items_multiperm_req'] = OrderedDict({
        'basic': OrderedDict({'any':0,'all':0}),
        'read': OrderedDict({'any':0,'all':0}),
        'write': OrderedDict({'any':0,'all':0}),
        'tot': OrderedDict({'any':0,'all':0})
      })
      dstats[ver]['items_perms_params_count'] = OrderedDict()

      dstats[ver]['items_calls_counts'] = []
      dstats[ver]['calls_restrictions_lists_count'] = OrderedDict()
      dstats[ver]['calls_restrictions_count'] = OrderedDict()
    
      dstats[ver]['alt_count'] = 0


    for path,data in mapping.items():
      dstats['items'] += 1

      dstats['items_unique'].add(path)

      for v in data['seen_in_source']:
        dstats['items_per_source'][str(v)] += 1

      for v in data['seen_in_lists']:
        dstats['items_per_nonsdk'][str(v)] += 1

      scomb = str(data['seen_in_source'])
      if scomb not in dstats['items_source_combs']:
        dstats['items_source_combs'][scomb] = 1
      else:
        dstats['items_source_combs'][scomb] += 1

      lcomb = str(data['seen_in_lists'])
      if lcomb not in dstats['items_nonsdk_combs']:
        dstats['items_nonsdk_combs'][lcomb] = 1
      else:
        dstats['items_nonsdk_combs'][lcomb] += 1

      for v,d in data['versions'].items():
        if v == '11':
          if d['perms_changed']:
            dstats['items_perms_changed']['10-11'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['10-11'] += 1
        if v == '12':
          if d['perms_changed']:
            dstats['items_perms_changed']['11-12'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['11-12'] += 1
        if v == '13':
          if d['perms_changed']:
            dstats['items_perms_changed']['12-13'] += 1
          if d['restrs_changed']:
            dstats['items_restrs_changed']['12-13'] += 1
        
        for retype in ['basic','read','write']:
          if d['perms'][retype]['perms']:
            for p in d['perms'][retype]['perms']:
              dstats['items_perms_unique'].add(p.split('.')[-1])

              if p not in dstats['items_perms_count']:
                dstats['items_perms_count'][p.split('.')[-1]] = 1
              else:
                dstats['items_perms_count'][p.split('.')[-1]] += 1

            dstats['items_perms_type'][retype].append(path)
            dstats['items_perms_type']['tot'].append(path)

            if len(d['perms'][retype]['perms']) > 1:
              dstats['items_multiperm'][retype].append(path)
              dstats['items_multiperm']['tot'].append(path)

              if d['perms'][retype]['req'][0]:
                dstats['items_multiperm_req'][retype][d['perms'][retype]['req'][0]] += 1
                dstats['items_multiperm_req']['tot'][d['perms'][retype]['req'][0]] += 1
            
            if d['perms'][retype]['params']:
              for param in d['perms'][retype]['params']:
                if param not in dstats['items_perms_params_count'].keys():
                  dstats['items_perms_params_count'][param] = 1
                else:
                  dstats['items_perms_params_count'][param] += 1
      
        if d['alt']:
          dstats['alt_count'] += 1
            


      for v,d in data['versions'].items():
        dstats[v]['items'] += 1

        for retype in ['basic','read','write']:
          if d['perms'][retype]['perms']:
            for p in d['perms'][retype]['perms']:
              dstats[v]['items_perms_unique'].add(p.split('.')[-1])

              if p not in dstats[v]['items_perms_count']:
                dstats[v]['items_perms_count'][p.split('.')[-1]] = 1
              else:
                dstats[v]['items_perms_count'][p.split('.')[-1]] += 1

            dstats[v]['items_perms_type'][retype].append(path)
            dstats[v]['items_perms_type']['tot'].append(path)

            if len(d['perms'][retype]['perms']) > 1:
              dstats[v]['items_multiperm'][retype].append(path)
              dstats[v]['items_multiperm']['tot'].append(path)
              
              if d['perms'][retype]['req'][0]:
                dstats[v]['items_multiperm_req'][retype][d['perms'][retype]['req'][0]] += 1
                dstats[v]['items_multiperm_req']['tot'][d['perms'][retype]['req'][0]] += 1
            
            if d['perms'][retype]['params']:
              for param in d['perms'][retype]['params']:
                if param not in dstats[v]['items_perms_params_count'].keys():
                  dstats[v]['items_perms_params_count'][param] = 1
                else:
                  dstats[v]['items_perms_params_count'][param] += 1
        
        if d['alt']:
          dstats[v]['alt_count'] += 1

    del d,data,jin,lcomb,p,param,path,scomb,v,ver
      
    # print(1)
    s = dstats['items']
    print(f'items total: {s}')
    s = len(dstats['items_unique'])
    print(f'items unique: {s}')
    print('items per source version:')
    for v in vers:
      s = dstats['items_per_source']
      print(f'  {v}: {s[v]}')
    print('items linked per nonsdk file version:')
    for v in vers:
      s = dstats['items_per_nonsdk']
      print(f'  {v}: {s[v]}')
    print('source version combinations for items:')
    ss = dstats['items_source_combs']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('nonsdk version combinations for items:')
    ss = dstats['items_nonsdk_combs']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    print('item permissions changed between versions:')
    ss = dstats['items_perms_changed']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    s = len(dstats['items_perms_unique'])
    print(f'unique permissions seen: {s}')
    pmaxn = max(dstats['items_perms_count'].items(), key=lambda x: x[1])
    pminn = min(dstats['items_perms_count'].items(), key=lambda x: x[1])
    print(f'  most times seen - {pmaxn[0]}: {pmaxn[1]}')
    print(f'  least times seen - {pminn[0]}: {pminn[1]}')
    print('permissions required:')
    ss = dstats['items_perms_type']
    for k,v in ss.items():
      print(f'  {k}: {len(v)}')
    print('multiple permissions required:')
    ss = dstats['items_multiperm']
    for k,v in ss.items():
      print(f'  {k}: {len(v)}')
    print('multiple permissions requirements:')
    ss = dstats['items_multiperm_req']
    for k,v in ss.items():
      print(f'  {k}')
      for f,b in v.items():
        print(f'    {f}: {b}')
    print('parameters for permission requirements:')
    ss = dstats['items_perms_params_count']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    print(f'average calls for items with perms: {s}')
    print('restriction lists combinations for calls:')
    ss = dict(sorted(dstats['calls_restrictions_lists_count'].items(), key=lambda item: item[1],reverse=True))
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('restrictions for calls:')
    ss = dict(sorted(dstats['calls_restrictions_count'].items(), key=lambda item: item[1],reverse=True))
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print('item calls restrictions changed between versions:')
    ss = dstats['items_restrs_changed']
    for k,v in ss.items():
      print(f'  {k}: {v}')
    print()

    for ver in vers:
      print('unique permissions seen:')
      s = len(dstats[ver]['items_perms_unique'])
      print(f'  {ver} {s}')
    for ver in vers:
      print(f'{ver}')
      pmaxn = max(dstats[ver]['items_perms_count'].items(), key=lambda x: x[1])
      pminn = min(dstats[ver]['items_perms_count'].items(), key=lambda x: x[1])
      print(f'  most times seen - {pmaxn[0]}: {pmaxn[1]}')
      print(f'  least times seen - {pminn[0]}: {pminn[1]}')
    print('permissions required:')
    for ver in vers:
      print(f'{ver}')
      ss = dstats[ver]['items_perms_type']
      for k,v in ss.items():
        print(f'    {k}: {len(v)}')
    print('multiple permissions required:')
    for ver in vers:
      print(f'{ver}')
      ss = dstats[ver]['items_multiperm']
      for k,v in ss.items():
        print(f'    {k}: {len(v)}')
    print('multiple permissions requirements:')
    for ver in vers:
      print(f'  {ver}')
      ss = dstats[ver]['items_multiperm_req']
      for k,v in ss.items():
        print(f'  {k}')
        for f,b in v.items():
          print(f'    {f}: {b}')
    print('parameters for permission requirements:')
    for ver in vers:
      print(f'  {ver}')
      ss = dstats[ver]['items_perms_params_count']
      for k,v in ss.items():
        print(f'    {k}: {v}')
    print()
    s = dstats['alt_count']
    print(f'alternatives total: {s}')
    print('alternatives per version:')
    for v in vers:
      s = dstats[v]['alt_count']
      print(f'  {v}: {s}')


def compare_call_perm_reqs(name_calls_wperms,name_calls_all):

  vers = ['10','11','12','13']
  vers_to_api = {'10':'29','11':'30','12':'31','13':'33'}
  if not name_calls_wperms:
    print('provide name!')
    return
  if not name_calls_all:
    print('provide name!')
    return
  with io.open(f'{path_script}/{path_output_s}/{name_calls_wperms}.json','r') as jin:
    mapping_wperms = json.load(jin)
  with io.open(f'{path_script}/{path_output_r}/{name_calls_all}.json','r') as jin:
    mapping_all = json.load(jin)
  with io.open(f'{path_script}/{file_permissions}','r') as jin:
    mapping_permissions = OrderedDict()
    for line in jin.readlines():
      jline = json.loads(line)
      for k,v in jline.items():
        p = k.split('.')[-1]
        if p not in mapping_permissions.keys():
          mapping_permissions[p] = v
        else:
          print(1)
  del line,jline,k,v,p,jin


  data_comp = OrderedDict()
  for call_wperm,data_callperm in mapping_wperms.items():
    
    data_call = mapping_all[call_wperm]
    data_comp[call_wperm] = OrderedDict()
    for ver in vers:
      in_lists = None
      in_source = None
      if int(ver) in data_callperm['seen_in_lists']:
        in_lists = True
      else:
        in_lists = False
      
      if int(ver) in data_callperm['seen_in_source']:
        in_source = True
      else:
        in_source = False

      if not in_lists and not in_source:
        data_comp[call_wperm][ver] = OrderedDict({
          'in_lists': False,
          'in_source_wperm': False,
          'invocation': None,
          'perms_list': None,
          'perms_req': None,
          'perm_param': None,
          'call_rl': None,
          'perm_rl_list': None,
          'call_restr': None,
          'perm_restr_list': None
        })

      elif in_lists and in_source:
        inv = data_callperm['versions'][ver]['invocation']
        perm_list = data_callperm['versions'][ver]['perms']['basic']['perms']
        perm_req = data_callperm['versions'][ver]['perms']['basic']['req']
        if len(perm_req) > 1:
          print(1)
        else:
          perm_req = perm_req[0]
        perm_param = data_callperm['versions'][ver]['perms']['basic']['params']
        call_rl = ','.join(data_call['versions'][ver]['rls'])
        call_restr = data_call['versions'][ver]['restr']
        perm_rl_list = []
        perm_restr_list = []
        for perm in perm_list:
          perm = perm.split('.')[-1].split(',')[0]
          try:
            perm_rl = mapping_permissions[perm]['versions'][vers_to_api[ver]]['restriction_list']
            perm_restr = mapping_permissions[perm]['versions'][vers_to_api[ver]]['restriction']
          except KeyError:
            for key in data_call.keys():
              if perm in key:
                print(1)
            else:
              print(f'no info on permission {perm}')
              perm_rl = None
              perm_restr = None
          perm_rl_list.append(perm_rl)
          perm_restr_list.append(perm_restr)
        data_comp[call_wperm][ver] = OrderedDict({
          'in_lists': True,
          'in_source_wperm': True,
          'invocation': inv,
          'perms_list': perm_list,
          'perms_req': perm_req,
          'perm_param': perm_param,
          'call_rl': call_rl,
          'perm_rl_list': perm_rl_list,
          'call_restr': call_restr,
          'perm_restr_list': perm_restr_list
        })
      
      elif in_lists and not in_source:
        call_rl = ','.join(data_call['versions'][ver]['rls'])
        call_restr = data_call['versions'][ver]['restr']
        perm_rl_list = []
        perm_restr_list = []
        data_comp[call_wperm][ver] = OrderedDict({
          'in_lists': True,
          'in_source_wperm': False,
          'invocation': None,
          'perms_list': None,
          'perms_req': None,
          'perm_param': None,
          'call_rl': call_rl,
          'perm_rl_list': perm_rl_list,
          'call_restr': call_restr,
          'perm_restr_list': perm_restr_list
        })
      
      else:
        data_comp[call_wperm][ver] = OrderedDict({
          'in_lists': False,
          'in_source_wperm': True,
          'invocation': None,
          'perms_list': None,
          'perms_req': None,
          'perm_param': None,
          'call_rl': None,
          'perm_rl_list': None,
          'call_restr': None,
          'perm_restr_list': None
        })

      try:
        del call_restr,call_rl,in_lists,in_source,perm_rl_list,perm_restr_list
      except UnboundLocalError:
        pass
      try:
        del inv,perm,perm_list,perm_req,perm_restr,perm_rl
      except UnboundLocalError:
        pass

  
  with io.open(f'{path_script}/{path_output_s}/call_perm_reqs.json','w') as jout:
    json.dump(data_comp, jout, indent = 2)


def stats_compare_call_perm_reqs(name):

  vers = ['10','11','12','13']
  if not name:
    print('provide name!')
    return
  with io.open(f'{path_script}/{path_output_s}/{name}.json','r') as jin:
    mapping = json.load(jin)
  del jin

  dstats = OrderedDict()
  dstats['calls'] = []
  dstats['invocations'] = []
  dstats['perms'] = []
  dstats['where'] = OrderedDict({
    'none': 0,
    'lists_only': 0,
    'source_only': 0,
    'both': 0
  })
  dstats['reqs'] = OrderedDict({
    'none': 0,
    'any':  0,
    'all':  0
  })
  dstats['compare'] = OrderedDict({
    'ok': 0,
    'perm < call': 0,
    'perm < call invocations list': [],
    'perm < call combinations set': set(),
    'perm < call combinations dict': OrderedDict()
  })
  dstats['perm < call'] = OrderedDict({
    'blacklist': [],
    'sdk': [],
    'public': [],
    'unsupported': [],
    'conditional_block_max_o': [],
    'conditional_block_max_p': [],
    'conditional_block_max_q': [],
    'conditional_block_max_r': [],
    'conditional_block_max_s': [],
  })

  for ver in vers:
    dstats[ver] = OrderedDict()
    dstats[ver]['calls'] = []
    dstats[ver]['invocations'] = []
    dstats[ver]['perms'] = []
    dstats[ver]['where'] = OrderedDict({
      'none': 0,
      'lists_only': 0,
      'source_only': 0,
      'both': 0
    })
    dstats[ver]['reqs'] = OrderedDict({
      'none': 0,
      'any':  0,
      'all':  0
    })
    dstats[ver]['compare'] = OrderedDict({
      'ok': 0,
      'perm < call': 0,
      'perm < call invocations list': [],
      'perm < call combinations set': set(),
      'perm < call combinations dict': OrderedDict()
    })
    dstats[ver]['perm < call'] = []
    dstats[ver]['perm < call'] = OrderedDict({
      'blacklist': [],
      'sdk': [],
      'public': [],
      'unsupported': [],
      'conditional_block_max_o': [],
      'conditional_block_max_p': [],
      'conditional_block_max_q': [],
      'conditional_block_max_r': [],
      'conditional_block_max_s': [],
    })

  tc = 0
  for call,data in mapping.items():
    for ver in vers:

      data_item = data[ver]
      dstats['calls'].append(call)
      dstats[ver]['calls'].append(call)
      dstats['invocations'].append(data_item['invocation'])
      dstats[ver]['invocations'].append(data_item['invocation'])

      if data_item['perms_list']:
        for perm in data_item['perms_list']:
          dstats['perms'].append(perm)
          dstats[ver]['perms'].append(perm)

      if data_item['in_lists'] and data_item['in_source_wperm']:
        dstats['where']['both'] += 1
        dstats[ver]['where']['both'] += 1
      elif data_item['in_lists'] and not data_item['in_source_wperm']:
        dstats['where']['lists_only'] += 1
        dstats[ver]['where']['lists_only'] += 1
      elif not data_item['in_lists'] and data_item['in_source_wperm']:
        dstats['where']['source_only'] += 1
        dstats[ver]['where']['source_only'] += 1
      elif not data_item['in_lists'] and not data_item['in_source_wperm']:
        dstats['where']['none'] += 1
        dstats[ver]['where']['none'] += 1
      else:
        print(1)

      if data_item['perms_req'] == None:
        dstats['reqs']['none'] += 1
        dstats[ver]['reqs']['none'] += 1
      elif data_item['perms_req'] == 'any':
        dstats['reqs']['any'] += 1
        dstats[ver]['reqs']['any'] += 1
      elif data_item['perms_req'] == 'all':
        dstats['reqs']['all'] += 1
        dstats[ver]['reqs']['all'] += 1
      else:
        print(1)
      
      if data_item['perms_list']:
        ok = True
        call_restr = data_item['call_restr']
        perm_restrs = data_item['perm_restr_list']
        compares = []
        lowers = set()
        lowers_add = False
        for pr in perm_restrs:
          # if not pr:
          #     tc +=1
          # if pr:
          #   if 'conditional_block_max_r' in pr and call_restr == 'blacklist':
              # "12": {
              #   "in_lists": true,
              #   "in_source_wperm": true,
              #   "invocation": "release/core/java/android/view/displayhash/DisplayHashManager/setDisplayHashThrottlingEnabled()",
              #   "perms_list": [
              #     "android.Manifest.permission.READ_FRAME_BUFFER"
              #   ],
              #   "perms_req": null,
              #   "call_rl": "blocked,test-api",
              #   "perm_rl_list": [
              #     "lo-prio,max-target-r"
              #   ],
              #   "call_restr": "blacklist",
              #   "perm_restr_list": [
              #     "conditional_block_max_r"
              #   ]
              # },
              # print(1)
          if pr in d_restr_all[call_restr] or not pr:
            compares.append(False)
            lowers_add = True
          else:
            compares.append(True)
        if lowers_add:
          for pr in perm_restrs:
            if not pr:
              # tc +=1
              pr = 'UNKNOWN'
            lowers.add(pr)
        perms_req = data_item['perms_req']
        if perms_req == None or perms_req == 'all':
          if True not in compares:
            ok = False
        elif perms_req == 'any':
          if False in compares:
            ok = False
        if ok:
          dstats['compare']['ok'] += 1
          dstats[ver]['compare']['ok'] += 1
        else:
          if not data_item['perm_param']:
            dstats['compare']['perm < call'] += 1
            dstats[ver]['compare']['perm < call'] += 1
            dstats['compare']['perm < call invocations list'].append(data_item['invocation'])
            dstats[ver]['compare']['perm < call invocations list'].append(data_item['invocation'])
            lowers = sorted(list(lowers))
            infoline = f'{call_restr}|{perms_req}|{lowers}'
            dstats['compare']['perm < call combinations set'].add(infoline)
            dstats[ver]['compare']['perm < call combinations set'].add(infoline)
            if infoline not in dstats['compare']['perm < call combinations dict'].keys():
              dstats['compare']['perm < call combinations dict'][infoline] = [call]
            else:
              dstats['compare']['perm < call combinations dict'][infoline].append(call)
            if infoline not in dstats[ver]['compare']['perm < call combinations dict'].keys():
              dstats[ver]['compare']['perm < call combinations dict'][infoline] = [call]
            else:
              dstats[ver]['compare']['perm < call combinations dict'][infoline].append(call)
            dstats['perm < call'][call_restr].append(call)
            dstats[ver]['perm < call'][call_restr].append(call)
  
  td = []
  # for ver in vers:
  #   dstats[ver]['compare']['perm < call combinations dict'] = OrderedDict(sorted(dstats[ver]['compare']['perm < call combinations dict'].items()))
  #   for k,v in dstats[ver]['compare']['perm < call combinations dict'].items():
  #     # print(f'{k} : {len(v)}')
  #     td.append([k,len(v)])
  for il,_ in sorted(dstats['compare']['perm < call combinations dict'].items()):
    tl = [il,]
    for ver in vers:
      try:
        tl.append(len(dstats[ver]['compare']['perm < call combinations dict'][il]))
      except KeyError:
        tl.append(0)
    tl.append(len(dstats['compare']['perm < call combinations dict'][il]))
    td.append(tl)

  print(tabulate(td,tablefmt='github'))
    # print(1)
  print('TOTAL')
  s = len(dstats['calls'])
  print(f'calls total: {s}')
  s = len(set(dstats['calls']))
  print(f'calls unique: {s}')
  s = len(set(dstats['invocations']))
  print(f'invocations unique: {s}')
  s = len(set(dstats['perms']))
  print(f'perms unique: {s}')
  print()
  for k,v in dstats['where'].items():
    print(f'items in {k}: {v}')
  print()
  print('permission requirements')
  for k,v in dstats['reqs'].items():
    print(f'  {k}: {v}')
  print()
  print('compare permissions restrictions to call restrictions')
  for k,v in dstats['compare'].items():
    if type(v) == int:
      print(f'  {k}: {v}')
    elif type(v) == list:
      s = len(set(v))
      print(f'  perm < call invocations: {s}')
  
  print()
  print('permissions restrictions lower than call restrictions')
  for k,v in dstats['perm < call'].items():
    vv = len(v)
    print(f'  {k}: {vv}')
  
  print('\n')
  print('BY VERSIONS')
  for ver in vers:
    print(f'version {ver}')
    s = len(dstats[ver]['calls'])
    print(f'  calls total: {s}')
    s = len(set(dstats[ver]['calls']))
    print(f'  calls unique: {s}')
    s = len(set(dstats[ver]['invocations']))
    print(f'  invocations unique: {s}')
    s = len(set(dstats[ver]['perms']))
    print(f'  perms unique: {s}')
    print()
    for k,v in dstats[ver]['where'].items():
      print(f'  items in {k}: {v}')
    print()
    print(' permission requirements')
    for k,v in dstats[ver]['reqs'].items():
      print(f'    {k}: {v}')
    print()
    print(' compare permissions restrictions to call restrictions')
    for k,v in dstats[ver]['compare'].items():
      if type(v) == int:
        print(f'  {k}: {v}')
      elif type(v) == list:
        s = len(set(v))
        print(f'  perm < call invocations: {s}')
    print()
    print(' permissions restrictions lower than call restrictions')
    for k,v in dstats[ver]['perm < call'].items():
      vv = len(v)
      print(f'    {k}: {vv}')


def query_call_perm_reqs(name):

  vers = ['10','11','12','13']
  if not name:
    print('provide name!')
    return
  with io.open(f'{path_script}/{path_output_s}/{name}.json','r') as jin:
    mapping = json.load(jin)
  del jin

  for call,data in mapping.items():
    for ver in vers:

      data_item = data[ver]
      if data_item['call_restr'] == 'public' and data_item['perms_req'] == None and data_item['perm_restr_list']:
        if data_item['perm_restr_list'][0] == 'blacklist':
          print(2)


def perm_to_calls(perm):

  vers = ['10','11','12','13']
  vers_to_api = {'10':'29','11':'30','12':'31','13':'33'}

  if not perm:
    print('so, no perm?')
    return
  print()
  print(perm)

  with io.open(f'{path_script}/{path_output_s}/call_perm_reqs.json','r') as jin:
    mapping_callperm = json.load(jin)
  del jin

  for call,data in mapping_callperm.items():
    
    in_vers = []
    in_vers_not = []
    tot = 0
    alsos = dict()
    for ver,data_item in data.items():
      also = None
      req = data_item['perms_req']
      if not data_item['perms_list']:
        continue
      c = None
      for p in data_item['perms_list']:
        if perm == p.split('.')[-1] and (not req or req == 'any'):
          in_vers.append(ver)
          c = True
        elif perm == p.split('.')[-1] and req == 'all':
          in_vers.append(ver)
          c = True
          also = [x.split('.')[-1] for x in data_item['perms_list'] if x.split('.')[-1] != perm]
          alsos[ver] = also
          # print(1)
      tot += 1
      if not c:
        in_vers_not.append(ver)
    
    if in_vers:
      print(len(in_vers),'/',tot,end=' ')

      if len(in_vers) < tot:
        print(call.split('(')[0], end = ' ')
        print('in:',in_vers,'not in:',in_vers_not)
      else:
        print(call.split('(')[0])
      if alsos:
        print(f'also needs: {alsos}')


def table_rl():

  with io.open(f'{path_script}/{path_output_r}/calls_in_restriction_lists.json') as jout:
    calls = json.load(jout)
  
  with io.open(f'{path_script}/{path_output_s}/release_calls.json') as jout:
    m_calls = json.load(jout)
  
  headers = ['category','a10','a11','a12','a13']
  restrs_dict = {} 
  restrs_list = []
  
  for call,data in calls.items():
    kcall = call.split(',')[0]
    # if kcall in m_calls:
    for api,item in data['versions'].items():
        # if not api in m_calls[kcall]['versions']:
        #   continue
        
        if api == '10':
          restr = item['restr']
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a10'] = restrs_dict[restr]['a10'] + 1
          else:
            restrs_dict[restr] = {'a10':1,'a11':0,'a12':0,'a13':0}
        if api == '11':
          restr = item['restr']
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a11'] = restrs_dict[restr]['a11'] + 1
          else:
            restrs_dict[restr] = {'a10':0,'a11':1,'a12':0,'a13':0}
        if api == '12':
          restr = item['restr']
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a12'] = restrs_dict[restr]['a12'] + 1
          else:
            restrs_dict[restr] = {'a10':0,'a11':0,'a12':1,'a13':0}
        if api == '13':
          restr = item['restr']
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a13'] = restrs_dict[restr]['a13'] + 1
          else:
            restrs_dict[restr] = {'a10':0,'a11':0,'a12':0,'a13':1}
  
  done_r = []
  for restr in restrs_dict.keys():
    if restrs_dict[restr]['a10'] != 0 and restr not in done_r:
      restr_list = [restr,restrs_dict[restr]['a10'],restrs_dict[restr]['a11'],\
                    restrs_dict[restr]['a12'],restrs_dict[restr]['a13']]
      restrs_list.append(restr_list)
      done_r.append(restr)
  for restr in restrs_dict.keys():
    if restrs_dict[restr]['a11'] != 0 and restr not in done_r:
      restr_list = [restr,restrs_dict[restr]['a10'],restrs_dict[restr]['a11'],\
                    restrs_dict[restr]['a12'],restrs_dict[restr]['a13']]
      restrs_list.append(restr_list)
      done_r.append(restr)
  for restr in restrs_dict.keys():
    if restrs_dict[restr]['a12'] != 0 and restr not in done_r:
      restr_list = [restr,restrs_dict[restr]['a10'],restrs_dict[restr]['a11'],\
                    restrs_dict[restr]['a12'],restrs_dict[restr]['a13']]
      restrs_list.append(restr_list)
      done_r.append(restr)
  for restr in restrs_dict.keys():
    if restrs_dict[restr]['a13'] != 0 and restr not in done_r:
      restr_list = [restr,restrs_dict[restr]['a10'],restrs_dict[restr]['a11'],\
                    restrs_dict[restr]['a12'],restrs_dict[restr]['a13']]
      restrs_list.append(restr_list)
      done_r.append(restr)
  
  total_list = ['total',]
  for i in range(1,5):
    tot = 0
    for l in restrs_list:
      tot += l[i]
    total_list.append(tot)
  restrs_list.append(total_list)

  restrs_list.sort(key = lambda row: row[0])
  print(tabulate(restrs_list, headers, tablefmt="github"))
  print()


def table_blacklist_change_by_api():
  print(f'-------------BLACKLIST CHANGES BY API-------------')
  headers = ['blacklist_change','a10','a11','a12','a13']
  all_apis = [10,11,12,13]
  cat_dict = {} # {'restr':{inA9:x,inA10:x,inA11:x,inA12:x}}
  cat_list = [] # ['restr',inA9,inA10,inA11,inA12]

  with io.open(f'{path_script}/{path_output_r}/calls_in_restriction_lists.json') as jout:
    calls = json.load(jout)
  
  with io.open(f'{path_script}/{path_output_s}/release_calls.json') as jout:
    m_calls = json.load(jout)
  
  for call,data in calls.items():
    kcall = call.split(',')[0]
    if kcall in m_calls:
      apis = data['seen_in_lists']
      categories = []
      for api in all_apis:
        
        if api in apis:
          restr = data['versions'][str(api)]['restr']
          categories.append(restr)
        else:
          categories.append('none')

        cat_dict[call] = categories
  histories_dict = {}
  tabl_data = []
  for perm in cat_dict.keys():
    categories = cat_dict[perm]
    history = ''
    for i in range(len(categories)):
      history += categories[i]
      if i != 3:
        history += '>'
    if history not in histories_dict.keys():
      histories_dict[history] = 1
    else:
      histories_dict[history] = histories_dict[history] + 1
  
  tabl_line = ['newly_added',0,0,0,0]
  for h in histories_dict.keys():
    categories = h.split('>')
    if categories[0] == 'blacklist':
      tabl_line[1] += histories_dict[h]
    if categories[0] == 'none' and categories[1] == 'blacklist':
      tabl_line[2] += histories_dict[h]
    if categories[1] == 'none' and categories[2] == 'blacklist':
      tabl_line[3] += histories_dict[h]
    if categories[2] == 'none' and categories[3] == 'blacklist':
      tabl_line[4] += histories_dict[h]
  tabl_data.append(tabl_line)
  
  tabl_line = ['removed','-',0,0,0]
  for h in histories_dict.keys():
    categories = h.split('>')
    if categories[0] == 'blacklist' and categories[1] == 'none':
      tabl_line[2] += histories_dict[h]
    if categories[1] == 'blacklist' and categories[2] == 'none':
      tabl_line[3] += histories_dict[h]
    if categories[2] == 'blacklist' and categories[3] == 'none':
      tabl_line[4] += histories_dict[h]
  tabl_data.append(tabl_line)
  
  tabl_line_m = ['moved','-',0,0,0]

  tabl_line_bs = ['  blacklist → sdk','-',0,0,0]
  for h in histories_dict.keys():
    categories = h.split('>')
    if categories[0] == 'blacklist' and categories[1] == 'sdk':
      tabl_line_bs[2] += histories_dict[h]
    if categories[1] == 'blacklist' and categories[2] == 'sdk':
      tabl_line_bs[3] += histories_dict[h]
    if categories[2] == 'blacklist' and categories[3] == 'sdk':
      tabl_line_bs[4] += histories_dict[h]
  for j in range(2,5):
    tabl_line_m[j] += tabl_line_bs[j]

  
  tabl_line_bp = ['  blacklist → public','-',0,0,0]
  for h in histories_dict.keys():
    categories = h.split('>')
    if categories[0] == 'blacklist' and categories[1] == 'public':
      tabl_line_bp[2] += histories_dict[h]
    if categories[1] == 'blacklist' and categories[2] == 'public':
      tabl_line_bp[3] += histories_dict[h]
    if categories[2] == 'blacklist' and categories[3] == 'public':
      tabl_line_bp[4] += histories_dict[h]
  for j in range(2,5):
    tabl_line_m[j] += tabl_line_bp[j]
  
  tabl_line_ub = ['  unsupported → blacklist','-',0,0,0]
  for h in histories_dict.keys():
    categories = h.split('>')
    if categories[0] == 'unsupported' and categories[1] == 'blacklist':
      tabl_line_ub[2] += histories_dict[h]
    if categories[1] == 'unsupported' and categories[2] == 'blacklist':
      tabl_line_ub[3] += histories_dict[h]
    if categories[2] == 'unsupported' and categories[3] == 'blacklist':
      tabl_line_ub[4] += histories_dict[h]
  for j in range(2,5):
    tabl_line_m[j] += tabl_line_ub[j]
  
  tabl_data.append(tabl_line_m)
  tabl_data.append(tabl_line_bs)
  tabl_data.append(tabl_line_bp)
  tabl_data.append(tabl_line_ub)

  total_list = ['total',]
  for j in range(0,4):
    tot = 0
    for h in histories_dict.keys():
      categories = h.split('>')
      if categories[j] == 'blacklist':
        tot += histories_dict[h]
    total_list.append(tot)
  tabl_data.append(total_list)

  print(tabulate(tabl_data, headers, tablefmt="github"))
  print()


def count_stuff():

  lines = """/services/core/java/com/android/server/content/ContentService#putCache()#fcd01b715ee17536265950c8058b6c2c1483b4e0
/services/core/java/com/android/server/content/ContentService#getCache()#7d093326cf70b3763fcdfeaa4a04669d2c5a73b4
/services/core/java/com/android/server/inputmethod/InputMethodManagerService#onCommand()#6b23ce0fd0b31856e5164a986148db3b574dd30e
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#setListener()#745c1e8043b102b3bba44e00505461f90a9dc573
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#startBugreport()#d2a8bc2a756c6aecc1ed2266e9e8f8eb2f79eb44
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#cancelBugreport()#cc1d62c4e1198d8dfaf081c2d70f80e2903c47ba
/packages/SettingsLib/src/com/android/settingslib/bluetooth/LocalBluetoothManager#create()#2701a158af49a7c0bac20a0c74ed7ff2157b4ed3
/telephony/java/android/telephony/TelephonyManager#setAllowedNetworkTypesForReason()#adcb3ad22e3ecae55b2ec1277af920ed051b636c
/telephony/java/android/telephony/TelephonyManager#getAllowedNetworkTypesForReason()#9f71772df137a0cfc4aa29881288c100f4dcf7cb
/telephony/java/android/telephony/TelephonyManager#getEffectiveAllowedNetworkTypes()#5e6989a7a3e465422ef0d7bb81df2c4a334f05d1
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotifications()#56f06d850cb90755f716c8cb6cf136ffa3e0b28e
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotificationsWithAttribution()#bc241c844c3b270b4ae98427404773ac6550f0a4
/services/core/java/com/android/server/notification/NotificationManagerService#getNotificationHistory()#2a3b095b5c987d4f8aedc0cef388753a5c662ea2
/services/core/java/com/android/server/content/ContentService#putCache()#fcd01b715ee17536265950c8058b6c2c1483b4e0
/services/core/java/com/android/server/content/ContentService#getCache()#7d093326cf70b3763fcdfeaa4a04669d2c5a73b4
/services/core/java/com/android/server/inputmethod/InputMethodManagerService#onCommand()#6b23ce0fd0b31856e5164a986148db3b574dd30e
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#startBugreport()#f664dd4d2c16524b89791ff849071f1472b99294
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#cancelBugreport()#cc1d62c4e1198d8dfaf081c2d70f80e2903c47ba
/services/core/java/com/android/server/wm/WindowManagerService#showGlobalActions()#e9df4075d41e2ba573b756899fef8a858a05d541
/core/java/android/os/SystemConfigManager#getDisabledUntilUsedPreinstalledCarrierAssociatedAppEntries()#5fd61e4b93603ad93a7c382ee091f98995a873d6
/packages/Shell/src/com/android/shell/BugreportRequestedReceiver#onReceive()#3fdb762958122c57907f81bbc662d339442a5e33
/packages/SettingsLib/src/com/android/settingslib/bluetooth/LocalBluetoothManager#create()#2701a158af49a7c0bac20a0c74ed7ff2157b4ed3
/services/core/java/com/android/server/app/GameManagerService#getAvailableGameModes()#6091d3fc16cec6dcab6a57fb26f37f25ee1731ed
/services/core/java/com/android/server/app/GameManagerService#setGameMode()#2fc2caa0600d6adcab7959e73295c0ad5c58db2f
/services/core/java/com/android/server/BluetoothModeChangeHelper#onAirplaneModeChanged()#9d93e4ba8ddac35b1b4cc9d55c999fd260e00a82
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotifications()#56f06d850cb90755f716c8cb6cf136ffa3e0b28e
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotificationsWithAttribution()#bc241c844c3b270b4ae98427404773ac6550f0a4
/services/core/java/com/android/server/notification/NotificationManagerService#getNotificationHistory()#2a3b095b5c987d4f8aedc0cef388753a5c662ea2
/services/core/java/com/android/server/graphics/fonts/FontManagerService#getFontConfig()#eabefd312e290295bb92efd3404b5d8cc29960c6
/services/core/java/com/android/server/graphics/fonts/FontManagerService#updateFontFamily()#f846ccab1d6ce5ca08af8ee6f12879e066e9797f
/services/core/java/com/android/server/content/ContentService#putCache()#fcd01b715ee17536265950c8058b6c2c1483b4e0
/services/core/java/com/android/server/content/ContentService#getCache()#7d093326cf70b3763fcdfeaa4a04669d2c5a73b4
/services/core/java/com/android/server/inputmethod/InputMethodManagerService#onCommand()#6b23ce0fd0b31856e5164a986148db3b574dd30e
/services/core/java/com/android/server/pm/verify/domain/DomainVerificationManagerInternal#getDomainVerificationInfo()#629ad5d865f3394502149801cf582c0452cec8cc
/services/core/java/com/android/server/pm/verify/domain/DomainVerificationManagerInternal#setDomainVerificationStatusInternal()#e4c2cc79896d3822ff3b489d88717779b1e242b1
/services/core/java/com/android/server/BluetoothManagerService#onAirplaneModeChanged()#9604638892e3bb718244ff84d3a834000eae15a7
/services/core/java/com/android/server/BluetoothManagerService#checkBluetoothPermissions()#8187eb9928779287a5939c4bf9dbbc0ee2f706cf
/services/core/java/com/android/server/BluetoothManagerService#disableBle()#b3e4f10b407e21253c0d8c0148359c77f90a6339
/services/core/java/com/android/server/BluetoothManagerService#continueFromBleOnState()#d7c752f3bdcf1b8e3da685df53ca50ef2aef6a6c
/services/core/java/com/android/server/BluetoothManagerService#sendBrEdrDownCallback()#15e1eb2395f00a700527e4da1f882479b309d825
/services/core/java/com/android/server/BluetoothManagerService#unbindAndFinish()#ff5a5f3697037ad682733463b6ecd43ffcdd66b9
/services/core/java/com/android/server/BluetoothManagerService#restartForReason()#f2bbec73053e84ba0d6344be58c29d83a5de2f52
/services/core/java/com/android/server/BluetoothManagerService#handleEnable()#652926d897da83418464c343b1a01fb3b4ca42f9
/services/core/java/com/android/server/BluetoothManagerService#handleDisable()#cf78bfb517303ec94ee33f46dcbf55a0708b6eda
/services/core/java/com/android/server/BluetoothManagerService#bluetoothStateChangeHandler()#1ca51e434a03d38598342cf17684f1ec919ebd72
/services/core/java/com/android/server/BluetoothManagerService#recoverBluetoothServiceFromError()#6bcc3fc98573bb660a62462a2034d1d6b3e07f41
/services/core/java/com/android/server/BluetoothManagerService#checkConnectPermissionForDataDelivery()#e31ccecbfb65c5b775b948253819e5afa7413aa4
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#startBugreport()#f664dd4d2c16524b89791ff849071f1472b99294
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#cancelBugreport()#9fee6cecfe90e31c89fc9de97d491f0f6b2fd594
/services/core/java/com/android/server/BluetoothAirplaneModeListener#handleAirplaneModeChange()#e83e98e8c15f27a818224ac88cec0b624a23d912
/services/core/java/com/android/server/wm/WindowManagerService#showGlobalActions()#e9df4075d41e2ba573b756899fef8a858a05d541
/errorprone/tests/res/android/foo/IColorService#red()#dc14f00e4d0bb8e685d6e49721d7ac97b0170a7c
/errorprone/tests/res/android/foo/IColorService#redAndBlue()#9450955e05b76a886995be23c7f13ce5288ce6e1
/errorprone/tests/res/android/foo/IColorService#redOrBlue()#12b35a86d9498218304aaa32d693c65ad58ff95c
/packages/Shell/src/com/android/shell/BugreportRequestedReceiver#onReceive()#3fdb762958122c57907f81bbc662d339442a5e33
/packages/SettingsLib/src/com/android/settingslib/bluetooth/LocalBluetoothManager#create()#2701a158af49a7c0bac20a0c74ed7ff2157b4ed3
/services/companion/java/com/android/server/companion/virtual/audio/VirtualAudioController#onRecordingConfigChanged()#5889a7a96efb6656d3472d96aea439a33f6bd941
/services/companion/java/com/android/server/companion/virtual/audio/VirtualAudioController#findRecordingConfigurations()#4bebfa760a2d3c7d4953d78e1804c4e9522c24b4
/services/companion/java/com/android/server/companion/virtual/VirtualDeviceImpl#onAudioSessionStarting()#182827de38b1e19c7045284c88e36eec7163eb35
/services/companion/java/com/android/server/companion/virtual/VirtualDeviceImpl#onAudioSessionEnded()#c8af4096c2996d3b78af226c2fddead03d978d39
/services/core/java/com/android/server/audio/AudioService#registerDeviceVolumeDispatcherForAbsoluteVolume()#76f0b292945d79234c46853bc65aa8a6c711ad80
/services/core/java/com/android/server/WallpaperUpdateReceiver#isUserSetWallpaper()#3595f2bc2084144f4c365584a55416578718a3c0
/services/core/java/com/android/server/app/GameServiceProviderInstanceImpl#createGameSession()#5452ae3a9d75379f06243c10240674ac3c29be17
/services/core/java/com/android/server/app/GameServiceProviderInstanceImpl#takeScreenshot()#21b041e0553c2c18aca24846bfa75ac01d44cc05
/services/core/java/com/android/server/app/GameServiceProviderInstanceImpl#restartGame()#ca937da6928b6ee2b99bd3c62c54191308fd831b
/services/core/java/com/android/server/app/GameManagerService#getAvailableGameModes()#6091d3fc16cec6dcab6a57fb26f37f25ee1731ed
/services/core/java/com/android/server/app/GameManagerService#getGameModeInfo()#a7945e0629b171389573f86a1e10ed909bcf57d9
/services/core/java/com/android/server/app/GameManagerService#setGameMode()#2fc2caa0600d6adcab7959e73295c0ad5c58db2f
/services/core/java/com/android/server/app/GameManagerService#isAngleEnabled()#ca6c10b041f3c7fda8aea54cfa5811bac0984ace
/services/core/java/com/android/server/app/GameManagerService#notifyGraphicsEnvironmentSetup()#9e458c56f403d09cadd42cb8f7719d9ee7929bc5
/services/core/java/com/android/server/app/GameManagerService#setGameServiceProvider()#968404e459c1fa54f81af8e56fa0985548b81d75
/services/core/java/com/android/server/app/GameManagerService#updateUseAngle()#c947448bc96eec7c5fa3e6b1d1bc6b7ff5fc9bb7
/services/core/java/com/android/server/app/GameManagerService#setGameModeConfigOverride()#6d64305c0b2eb06ce4b98641da16a48ed570db23
/services/core/java/com/android/server/app/GameManagerService#resetGameModeConfigOverride()#f76beca7842bc89eacb81813614914956fe679b2
/services/core/java/com/android/server/location/LocationManagerService#setAutomotiveGnssSuspended()#04a6bb064135f94d21c0ef7dd2e400218ace3988
/services/core/java/com/android/server/location/LocationManagerService#isAutomotiveGnssSuspended()#3b500cb604836f0e5a5a916d7d00b376193718ef
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotifications()#56f06d850cb90755f716c8cb6cf136ffa3e0b28e
/services/core/java/com/android/server/notification/NotificationManagerService#getHistoricalNotificationsWithAttribution()#bc241c844c3b270b4ae98427404773ac6550f0a4
/services/core/java/com/android/server/notification/NotificationManagerService#getNotificationHistory()#2a3b095b5c987d4f8aedc0cef388753a5c662ea2
/services/core/java/com/android/server/graphics/fonts/FontManagerService#getFontConfig()#eabefd312e290295bb92efd3404b5d8cc29960c6
/services/core/java/com/android/server/graphics/fonts/FontManagerService#updateFontFamily()#f846ccab1d6ce5ca08af8ee6f12879e066e9797f
/services/core/java/com/android/server/content/ContentService#putCache()#fcd01b715ee17536265950c8058b6c2c1483b4e0
/services/core/java/com/android/server/content/ContentService#getCache()#7d093326cf70b3763fcdfeaa4a04669d2c5a73b4
/services/core/java/com/android/server/inputmethod/InputMethodManagerService#onCommand()#6b23ce0fd0b31856e5164a986148db3b574dd30e
/services/core/java/com/android/server/pm/verify/domain/DomainVerificationManagerInternal#getDomainVerificationInfo()#629ad5d865f3394502149801cf582c0452cec8cc
/services/core/java/com/android/server/pm/verify/domain/DomainVerificationManagerInternal#setDomainVerificationStatusInternal()#e4c2cc79896d3822ff3b489d88717779b1e242b1
/services/core/java/com/android/server/pm/DexOptHelper#performPackageDexOptUpgradeIfNeeded()#dab2e50c7cd8e8d48449a4cf9ba11dfb44d83c16
/services/core/java/com/android/server/power/PowerManagerService#isLowPowerStandbySupported()#df85b4e58bd0cb548d1adb135f127d0b1b000e7a
/services/core/java/com/android/server/power/PowerManagerService#setLowPowerStandbyEnabled()#0e13811b724ecbace312d8373029b42f12f44095
/services/core/java/com/android/server/power/PowerManagerService#setLowPowerStandbyActiveDuringMaintenance()#247ddac860a0e8a42251f59aca222f753ee3950a
/services/core/java/com/android/server/power/PowerManagerService#forceLowPowerStandbyActive()#ae8a31a1cd514db0a87fb963c385a5772a9518f1
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#startBugreport()#f664dd4d2c16524b89791ff849071f1472b99294
/services/core/java/com/android/server/os/BugreportManagerServiceImpl#cancelBugreport()#9fee6cecfe90e31c89fc9de97d491f0f6b2fd594
/services/core/java/com/android/server/wm/WindowManagerService#addKeyguardLockedStateListener()#a35783ab9ba1aa1f9c5171b4712f0b5020f9ee5b
/services/core/java/com/android/server/wm/WindowManagerService#removeKeyguardLockedStateListener()#0d5e01b9b238c370af9707b727bf51914cdf3969
/services/core/java/com/android/server/wm/WindowManagerService#showGlobalActions()#e9df4075d41e2ba573b756899fef8a858a05d541
/services/core/java/com/android/server/wm/WindowManagerService#registerTaskFpsCallback()#e6dfd345d0a39735e538b697eadcea247e76a723
/services/core/java/com/android/server/wm/WindowManagerService#unregisterTaskFpsCallback()#cd8bf3e0cf6f90d969b9c2ba736e877540024c91
/services/accessibility/java/com/android/server/accessibility/AccessibilityManagerService#setSystemAudioCaptioningEnabled()#e885777cbca3d021b9ff8d66291485caf69fa32b
/services/accessibility/java/com/android/server/accessibility/AccessibilityManagerService#setSystemAudioCaptioningUiEnabled()#ccaac6d3e0999bd7992ccf72c17cad042d1f09d1
/errorprone/tests/res/android/foo/IColorService#red()#dc14f00e4d0bb8e685d6e49721d7ac97b0170a7c
/errorprone/tests/res/android/foo/IColorService#redAndBlue()#9450955e05b76a886995be23c7f13ce5288ce6e1
/errorprone/tests/res/android/foo/IColorService#redOrBlue()#12b35a86d9498218304aaa32d693c65ad58ff95c
/packages/Shell/src/com/android/shell/BugreportRequestedReceiver#onReceive()#3fdb762958122c57907f81bbc662d339442a5e33
/packages/SettingsLib/src/com/android/settingslib/bluetooth/LocalBluetoothManager#create()#2701a158af49a7c0bac20a0c74ed7ff2157b4ed3"""

  sline = set()
  for line in lines.split('\n'):
    sline.add(line)
  print(len(sline))

  slist = sorted(list(sline))
  for line in slist:
    print(line)




if __name__ == '__main__':
  # res = get_restriction_lists(10)
  # changes = get_changes()

  # extract_calls_permissions('data/source/10/base-refs_heads_android10-s3-release/core')
  # extract_calls_permissions('data/source/11/base-refs_heads_android11-s1-release/core')
  # extract_calls_permissions('data/source/12/base-refs_heads_android12-s5-release/core')
  # extract_calls_permissions('data/source/13/base-refs_heads_android13-s3-release/core')
  # compile_mapping('core')
  # fix_mapping('core')

  # extract_calls_permissions('data/source/10/base-refs_heads_android10-s3-release')
  # extract_calls_permissions('data/source/11/base-refs_heads_android11-s1-release')
  # extract_calls_permissions('data/source/12/base-refs_heads_android12-s5-release')
  # extract_calls_permissions('data/source/13/base-refs_heads_android13-s3-release')
  # stats_methods('release')
  # compile_mapping('release')
  # fix_mapping('release')
  # fix_mapping_2('release_checked')
  # stats_mapping('release_checked')
  # calls_mapping('release_checked')
  # fix_calls_mapping('release_calls')
  # stats_mapping_calls('release_calls')
  # parse_restriction_lists()
  # compare_call_perm_reqs('release_calls','calls_in_restriction_lists')
  # stats_compare_call_perm_reqs('call_perm_reqs')
  # query_call_perm_reqs('call_perm_reqs')
  # perm_to_calls('BACKUP')
  # perm_to_calls('CHANGE_COMPONENT_ENABLED_STATE')
  # perm_to_calls('CONNECTIVITY_INTERNAL')
  # perm_to_calls('DEVICE_POWER')
  # perm_to_calls('GRANT_RUNTIME_PERMISSIONS')
  # perm_to_calls('INSTALL_PACKAGES')
  # perm_to_calls('INTERACT_ACROSS_USERS')
  # perm_to_calls('INTERNAL_SYSTEM_WINDOW')
  # perm_to_calls('MANAGE_APP_OPS_MODES')
  # perm_to_calls('OVERRIDE_WIFI_CONFIG')
  # perm_to_calls('PEERS_MAC_ADDRESS')
  # perm_to_calls('READ_INSTALL_SESSIONS')
  # perm_to_calls('READ_PRIVILEDGED_PHONE_STATE')
  # perm_to_calls('REBOOT')
  # perm_to_calls('START_ACTIVITIES_FROM_BACKGROUND')
  # perm_to_calls('STATUS_BAR')
  # perm_to_calls('SUBSTITUTE_NOTIFICATION_APP_NAME')
  # perm_to_calls('SUBSTITUTE_SHARE_TARGET_APP_NAME_AND_ICON')
  # perm_to_calls('TETHER_PRIVILEGED')
  # perm_to_calls('UPDATE_APP_OPS_STATS')
  # perm_to_calls('WRITE_SECURE_SETINGS')
  # perm_to_calls('MANAGE_ROLES_FROM_CONTROLLER')
  # perm_to_calls('PERMISSION_MAINLINE_NETWORK_STACK')
  # perm_to_calls('MANAGE_SIM_ACCOUNTS')
  # perm_to_calls('ACCESS_LAST_KNOWN_CELL_ID')
  # table_rl()
  # table_blacklist_change_by_api()
  count_stuff()





# "alt": "Landroid/net/wifi/WifiManager;->setVerboseLoggingEnabled(Z)V,system-api,whitelist"