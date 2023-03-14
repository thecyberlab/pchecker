from ast import Or
import io
import os
from collections import OrderedDict
import json
import statistics
import copy
from tabulate import tabulate


path_script = os.path.abspath(os.path.dirname(__file__))
file_apks = 'data/sets_all_meta_all_valid.json'
file_lists = 'data/data_lists.json'
file_permissions = 'data/data_permissions.json'
folder_adb_data = 'data/adb_parsed'
folder_input_ok = 'data/adb_parsed/ok'

sources_good = [
    'androgalaxy_2019',
    'androidapkfree_2020',
    'apkgod_2020',
    'apkmaza_2020',
    'fdroid_2020',
    'appsapk_com_2020',
    'apkpure_2021',
    'crackshash_2021',
    'crackhash_2022',
    ]

sources_bad = [
    ]

sources_all = [
    ]

misc = [
  'phone_crackhash_2022'
]

sources_none = [
  'none'
]
sources_dummy = [
  'dummy'
]

vers = ['10','11','12','13']
apis = [29,30,31,33]
ver_to_api = OrderedDict({'10':29,'11':30,'12':31,'13':33})
api_to_ver = OrderedDict({'29':10,'30':11,'31':12,'33':13})
test_apis = [29,30,31,32,33]
# test_apis = [31,32,33]

dict_andro_maps = dict()
with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
  for line in rif:
    xline = line.replace("\n", "").strip()
    if xline:
      jdata = json.loads(xline)
      for k,v in jdata.items():
        if not k in dict_andro_maps:
          dict_andro_maps[k] = v
del k,v,line,xline,jdata

apps_working = OrderedDict()
for source in sources_good:
  apps_working[source] = []

for file in os.listdir(f'{path_script}/{folder_input_ok}'):
  path_file = f'{path_script}/{folder_input_ok}/{file}'
  source = file.replace('_working.txt','')
  with io.open(path_file) as oks:
    for line in oks.readlines():
      line = line.replace('\n','')
      apps_working[source].append(line)
del file,path_file,source,line

set_apps_working = set()
for source,apps in apps_working.items():
  for app in apps:
    set_apps_working.add(app)


def get_file_lines(data_path):
  if not os.path.isfile(data_path):
    print("PATH -> ", data_path)
    raise AssertionError("ERROR: unsupported source, has to be a FILE")

  content = list()
  with io.open(data_path, 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        content.append(xline)
  return(content)


def parse_perm_dict(adb_dict):

    perm_granted = False
    is_signature = False
    at_install = False
    if "params_bool" in adb_dict:
      if adb_dict["params_bool"] == True:
        perm_granted = True
        if "params" in adb_dict:
          if "prot=signature" in adb_dict["params"]:
            is_signature = True
          if "INSTALLED" in adb_dict["params"]:
            at_install = True

    pres = OrderedDict()
    pres["granted"] = perm_granted
    pres["is_signature"] = is_signature
    pres["at_install"] = at_install

    return(pres)


def get_apk_meta(file_apks):
  jlines = get_file_lines(file_apks)

  data_json = OrderedDict()
  for item in jlines:
    jtem = json.loads(item)
    for k,v in jtem.items():
      data_json[k] = v

  dict_apk_api = OrderedDict()
  for ksha1, kmeta in data_json.items():

    apk_sha1 = kmeta["sha1"]
    apk_in_sets = kmeta["in_sets"]
    apk_api = kmeta["api_level_to_use"] # api_level_to_use max_sdk_version target_sdk_version

    perm_meta = OrderedDict()

    perm_meta["apk_sha1"] = apk_sha1
    perm_meta["api"] = apk_api

    dict_apk_api[kmeta["sha1"]] = perm_meta
  
  return dict_apk_api


def get_perm_comb(dict_andro_maps,p,cur_api):
  tag = dict_andro_maps[p]['versions'][str(cur_api)]['tag']
  restr = dict_andro_maps[p]['versions'][str(cur_api)]['restriction']
  prot = dict_andro_maps[p]['versions'][str(cur_api)]['protection']
  status = dict_andro_maps[p]['versions'][str(cur_api)]['status']
  usage = dict_andro_maps[p]['versions'][str(cur_api)]['usage']
  type = dict_andro_maps[p]['versions'][str(cur_api)]['type']
  restr = restr.replace('XXX','missing')
  combination = f'{tag} + {restr} + {prot} + {status} + {usage} + {type}'
  return combination


def is_apk_runnable(apk_meta):
  stat_ok = True
  if 'INSTALL' in apk_meta['err_type'] or 'EMPTY FILE install' in apk_meta['err_reason']:
    stat_ok = False
  elif 'RUN' in apk_meta['err_type'] or 'EMPTY FILE run' in apk_meta['err_reason']:
    stat_ok = False
  elif 'STOP' in apk_meta['err_type']:
    stat_ok = False
  return stat_ok


#############################################################################################
#############################################################################################
#############################################################################################

def get_perms_in_files(file_lists,file_permissions):
  perm_count = 0
  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      perm_count += 1

  perm_count_m = 0
  missing_list = ['missing',0,0,0,0]
  with io.open(f'{path_script}/{file_permissions}') as inp:
    for line in inp.readlines():
      perm_count_m += 1

  print(f'# OF PERMISSIONS IN RESTRICTION LISTS: {perm_count}')
  print(f'# OF PERMISSIONS IN MANIFESTS: {perm_count_m}')
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_restr_list_combs_by_api(file_lists,file_permissions):
  headers = ['restr_list','a10','a11','a12','a13']
  restrs_dict = {} # {'restr':{ina10:x,ina11:x,ina12:x,ina13:x}}
  restrs_list = [] # ['restr',ina10,ina11,ina12,ina13]
  perm_count = 0

  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      perm_count += 1
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis = data[perm]['seen_in_lists']
      if 29 in apis:
        restr = data[perm]['versions']['29']['lists']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a10'] = restrs_dict[restr]['a10'] + 1
        else:
          restrs_dict[restr] = {'a10':1,'a11':0,'a12':0,'a13':0}
      if 30 in apis:
        restr = data[perm]['versions']['30']['lists']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a11'] = restrs_dict[restr]['a11'] + 1
        else:
          restrs_dict[restr] = {'a10':0,'a11':1,'a12':0,'a13':0}
      if 31 in apis:
        restr = data[perm]['versions']['31']['lists']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a12'] = restrs_dict[restr]['a12'] + 1
        else:
          restrs_dict[restr] = {'a10':0,'a11':0,'a12':1,'a13':0}
      if 33 in apis:
        restr = data[perm]['versions']['33']['lists']
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

  perm_count_m = 0
  missing_list = ['missing',0,0,0,0]
  with io.open(f'{path_script}/{file_permissions}') as inp:
    for line in inp.readlines():
      perm_count_m += 1
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis_l = data[perm]['seen_in_lists']
      apis_m = data[perm]['seen_in_manifests']
      if 29 in apis_m:
        if 29 not in apis_l:
          missing_list[1] += 1 
      if 30 in apis_m:
        if 30 not in apis_l:
          missing_list[2] += 1 
      if 31 in apis_m:
        if 31 not in apis_l:
          missing_list[3] += 1 
      if 33 in apis_m:
        if 33 not in apis_l:
          missing_list[4] += 1 
  restrs_list.append(missing_list)

  total_list = ['total',]
  for i in range(1,5):
    tot = 0
    for l in restrs_list:
      tot += l[i]
    total_list.append(tot)
  restrs_list.append(total_list)
  
  print(f'-------------RESTRICTION LIST COMBINATIONS BY API-------------')
  print(tabulate(restrs_list, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_restr_lists_by_api(file_lists,file_permissions):
  print(f'RESTRICTION LISTS BY API')
  headers = ['restr_list','a10','a11','a12','a13']
  restrs_dict = {} # {'restr':{ina10:x,ina11:x,ina12:x,ina13:x}}
  restrs_list = [] # ['restr',ina10,ina11,ina12,ina13]

  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis = data[perm]['seen_in_lists']
      if 29 in apis:
        restrs = data[perm]['versions']['29']['lists'].split(',')
        for restr in restrs:
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a10'] = restrs_dict[restr]['a10'] + 1
          else:
            restrs_dict[restr] = {'a10':1,'a11':0,'a12':0,'a13':0}
      if 30 in apis:
        restrs = data[perm]['versions']['30']['lists'].split(',')
        for restr in restrs:
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a11'] = restrs_dict[restr]['a11'] + 1
          else:
            restrs_dict[restr] = {'a10':0,'a11':1,'a12':0,'a13':0}
      if 31 in apis:
        restrs = data[perm]['versions']['31']['lists'].split(',')
        for restr in restrs:
          if restr in restrs_dict.keys():
            restrs_dict[restr]['a12'] = restrs_dict[restr]['a12'] + 1
          else:
            restrs_dict[restr] = {'a10':0,'a11':0,'a12':1,'a13':0}
      if 33 in apis:
        restrs = data[perm]['versions']['33']['lists'].split(',')
        for restr in restrs:
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

  missing_list = ['missing',0,0,0,0]
  with io.open(f'{path_script}/{file_permissions}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis_l = data[perm]['seen_in_lists']
      apis_m = data[perm]['seen_in_manifests']
      if 29 in apis_m:
        if 29 not in apis_l:
          missing_list[1] += 1 
      if 30 in apis_m:
        if 30 not in apis_l:
          missing_list[2] += 1 
      if 31 in apis_m:
        if 31 not in apis_l:
          missing_list[3] += 1 
      if 33 in apis_m:
        if 33 not in apis_l:
          missing_list[4] += 1 
  restrs_list.append(missing_list)

  total_list = ['total',]
  for i in range(1,5):
    tot = 0
    for l in restrs_list:
      tot += l[i]
    total_list.append(tot)
  restrs_list.append(total_list)

  print(tabulate(restrs_list, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_list_categories_by_api(file_lists,file_permissions):
  print(f'-------------RESTRICTION CATEGORIES BY API-------------')
  headers = ['category','a10','a11','a12','a13']
  restrs_dict = {} # {'restr':{inA9:x,inA10:x,inA11:x,inA12:x}}
  restrs_list = [] # ['restr',inA9,inA10,inA11,inA12]

  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis = data[perm]['seen_in_lists']
      if 29 in apis:
        restr = data[perm]['versions']['29']['restriction']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a10'] = restrs_dict[restr]['a10'] + 1
        else:
          restrs_dict[restr] = {'a10':1,'a11':0,'a12':0,'a13':0}
      if 30 in apis:
        restr = data[perm]['versions']['30']['restriction']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a11'] = restrs_dict[restr]['a11'] + 1
        else:
          restrs_dict[restr] = {'a10':0,'a11':1,'a12':0,'a13':0}
      if 31 in apis:
        restr = data[perm]['versions']['31']['restriction']
        if restr in restrs_dict.keys():
          restrs_dict[restr]['a12'] = restrs_dict[restr]['a12'] + 1
        else:
          restrs_dict[restr] = {'a10':0,'a11':0,'a12':1,'a13':0}
      if 33 in apis:
        restr = data[perm]['versions']['33']['restriction']
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
  
  missing_list = ['missing',0,0,0,0]
  with io.open(f'{path_script}/{file_permissions}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis_l = data[perm]['seen_in_lists']
      apis_m = data[perm]['seen_in_manifests']
      if 29 in apis_m:
        if 29 not in apis_l:
          missing_list[1] += 1 
      if 30 in apis_m:
        if 30 not in apis_l:
          missing_list[2] += 1 
      if 31 in apis_m:
        if 31 not in apis_l:
          missing_list[3] += 1 
      if 33 in apis_m:
        if 33 not in apis_l:
          missing_list[4] += 1 
  restrs_list.append(missing_list)

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


#############################################################################################
#############################################################################################
#############################################################################################

def table_category_change_by_api(file_lists,file_permissions):
  print(f'-------------RESTRICTION CATEGORY CHANGES BETWEEN APIS-------------')
  headers = ['category_change','#']
  cat_dict = {} # {'restr':{inA9:x,inA10:x,inA11:x,inA12:x}}
  cat_list = [] # ['restr',inA9,inA10,inA11,inA12]

  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis = data[perm]['seen_in_lists']
      categories = []
      if 29 in apis:
        restr = data[perm]['versions']['29']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 30 in apis:
        restr = data[perm]['versions']['30']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 31 in apis:
        restr = data[perm]['versions']['31']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 33 in apis:
        restr = data[perm]['versions']['33']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      cat_dict[perm] = categories
  histories_dict = {}
  histories_list = []
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
  histories_dict_sorted = dict(sorted(histories_dict.items(), key=lambda x: x[1], reverse=True))
  for history in histories_dict_sorted.keys():
    histories_list.append([history,histories_dict_sorted[history]])

  total_list = ['total',]
  for i in range(1,2):
    tot = 0
    for l in histories_list:
      tot += l[i]
    total_list.append(tot)
  histories_list.append(total_list)

  histories_list.sort(key = lambda row: row[0])
  print(tabulate(histories_list, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_blacklist_change_by_api(file_lists,file_permissions):
  print(f'-------------BLACKLIST CHANGES BY API-------------')
  headers = ['blacklist_change','a10','a11','a12','a13']
  cat_dict = {} # {'restr':{inA9:x,inA10:x,inA11:x,inA12:x}}
  cat_list = [] # ['restr',inA9,inA10,inA11,inA12]

  with io.open(f'{path_script}/{file_lists}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      apis = data[perm]['seen_in_lists']
      categories = []
      if 29 in apis:
        restr = data[perm]['versions']['29']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 30 in apis:
        restr = data[perm]['versions']['30']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 31 in apis:
        restr = data[perm]['versions']['31']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      if 33 in apis:
        restr = data[perm]['versions']['33']['restriction']
        categories.append(restr)
      else:
        categories.append('none')
      cat_dict[perm] = categories
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


#############################################################################################
#############################################################################################
#############################################################################################

def get_rput_by_api(file_lists,file_permissions):
  data_28 = {'tag':[],'restriction':[],'protection':[],'status':[],'usage':[],'type':[]}
  data_29 = {'tag':[],'restriction':[],'protection':[],'status':[],'usage':[],'type':[]}
  data_30 = {'tag':[],'restriction':[],'protection':[],'status':[],'usage':[],'type':[]}
  data_31 = {'tag':[],'restriction':[],'protection':[],'status':[],'usage':[],'type':[]}
  data_33 = {'tag':[],'restriction':[],'protection':[],'status':[],'usage':[],'type':[]}
  set_tag = set()
  set_restr = set()
  set_prot = set()
  set_status = set()
  set_usage = set()
  set_type = set()
  done_perms = []
  with io.open(f'{path_script}/{file_permissions}') as inp:
    for line in inp.readlines():
      data = json.loads(line)
      perm = [key for key in data.keys()][0]
      perm_name = perm.split('.')[-1]
      done_perms.append(perm_name)
      apis_manifest = data[perm]['seen_in_manifests']
      apis_lists = data[perm]['seen_in_lists']
      apis = list(set(apis_manifest + apis_lists))
      if 28 in apis:
        tag = data[perm]['versions']['28']['tag']
        data_28['tag'].append(tag)
        set_tag.add(tag)
        restr = data[perm]['versions']['28']['restriction'].replace('XXX','does_not_exist')
        data_28['restriction'].append(restr)
        set_restr.add(restr)
        prot = data[perm]['versions']['28']['protection']
        data_28['protection'].append(prot)
        set_prot.add(prot)
        status = data[perm]['versions']['28']['status']
        data_28['status'].append(status)
        set_status.add(status)
        usage = data[perm]['versions']['28']['usage']
        data_28['usage'].append(usage)
        set_usage.add(usage)
        type = data[perm]['versions']['28']['type']
        data_28['type'].append(type)
        set_type.add(type)
      if 29 in apis:
        tag = data[perm]['versions']['29']['tag']
        data_29['tag'].append(tag)
        set_tag.add(tag)
        restr = data[perm]['versions']['29']['restriction'].replace('XXX','missing')
        data_29['restriction'].append(restr)
        set_restr.add(restr)
        prot = data[perm]['versions']['29']['protection']
        data_29['protection'].append(prot)
        set_prot.add(prot)
        status = data[perm]['versions']['29']['status']
        data_29['status'].append(status)
        set_status.add(status)
        usage = data[perm]['versions']['29']['usage']
        data_29['usage'].append(usage)
        set_usage.add(usage)
        type = data[perm]['versions']['29']['type']
        data_29['type'].append(type)
        set_type.add(type)
      if 30 in apis:
        tag = data[perm]['versions']['30']['tag']
        data_30['tag'].append(tag)
        set_tag.add(tag)
        restr = data[perm]['versions']['30']['restriction'].replace('XXX','missing')
        data_30['restriction'].append(restr)
        set_restr.add(restr)
        prot = data[perm]['versions']['30']['protection']
        data_30['protection'].append(prot)
        set_prot.add(prot)
        status = data[perm]['versions']['30']['status']
        data_30['status'].append(status)
        set_status.add(status)
        usage = data[perm]['versions']['30']['usage']
        data_30['usage'].append(usage)
        set_usage.add(usage)
        type = data[perm]['versions']['30']['type']
        data_30['type'].append(type)
        set_type.add(type)
      if 31 in apis:
        tag = data[perm]['versions']['31']['tag']
        data_31['tag'].append(tag)
        set_tag.add(tag)
        restr = data[perm]['versions']['31']['restriction'].replace('XXX','missing')
        data_31['restriction'].append(restr)
        set_restr.add(restr)
        prot = data[perm]['versions']['31']['protection']
        data_31['protection'].append(prot)
        set_prot.add(prot)
        status = data[perm]['versions']['31']['status']
        data_31['status'].append(status)
        set_status.add(status)
        usage = data[perm]['versions']['31']['usage']
        data_31['usage'].append(usage)
        set_usage.add(usage)
        type = data[perm]['versions']['31']['type']
        data_31['type'].append(type)
        set_type.add(type)
      if 33 in apis:
        tag = data[perm]['versions']['33']['tag']
        data_33['tag'].append(tag)
        set_tag.add(tag)
        restr = data[perm]['versions']['33']['restriction'].replace('XXX','missing')
        data_33['restriction'].append(restr)
        set_restr.add(restr)
        prot = data[perm]['versions']['33']['protection']
        data_33['protection'].append(prot)
        set_prot.add(prot)
        status = data[perm]['versions']['33']['status']
        data_33['status'].append(status)
        set_status.add(status)
        usage = data[perm]['versions']['33']['usage']
        data_33['usage'].append(usage)
        set_usage.add(usage)
        type = data[perm]['versions']['33']['type']
        data_33['type'].append(type)
        set_type.add(type)
  
  return data_28,data_29,data_30,data_31,data_33


#############################################################################################
#############################################################################################
#############################################################################################

def table_comb_of_rput_by_api(data_29,data_30,data_31,data_33,a=True,r=True,p=True,s=True,u=True,t=True):
  print(f'-------------RPUT COMBINATIONS BY API-------------')
  sets = [data_28,data_29,data_30,data_31,data_33]
  tabl_name = 'combination by'
  if a:
    tabl_name += ' tag,'
  if r:
    tabl_name += ' restriction,'
  if p:
    tabl_name += ' protection,'
  if s:
    tabl_name += ' status,'
  if u:
    tabl_name += ' usage,'
  if t:
    tabl_name += ' type,'
  tabl_name = tabl_name[:-1]
  tabl_headers = [tabl_name,'a10','a11','a12','a13']
  tabl_data = []
  combinations = []

  for d_set in sets:
    combs_r = {}
    for i in range(len(d_set['restriction'])):
      tag = d_set['tag'][i]
      restr = d_set['restriction'][i]
      prot = d_set['protection'][i]
      status = d_set['status'][i]
      usage = d_set['usage'][i]
      type = d_set['type'][i]

      comb_l = []
      if a:
        comb_l.append(tag)
      if r:
        comb_l.append(restr)
      if p:
        comb_l.append(prot)
      if s:
        comb_l.append(status)
      if u:
        comb_l.append(usage)
      if t:
        comb_l.append(type)

      comb_r = ''
      for item in comb_l:
        comb_r += f'{item} + '
      comb_r = comb_r[:-3]

      if comb_r not in combinations:
        combinations.append(comb_r)

  dict_tabl_data = OrderedDict()
  for c in combinations:
    dict_tabl_data[c] = []

  for d_set in sets:
    combs_r = {}
    for i in range(len(d_set['restriction'])):
      tag = d_set['tag'][i]
      restr = d_set['restriction'][i]
      prot = d_set['protection'][i]
      status = d_set['status'][i]
      usage = d_set['usage'][i]
      type = d_set['type'][i]

      comb_l = []
      if a:
        comb_l.append(tag)
      if r:
        comb_l.append(restr)
      if p:
        comb_l.append(prot)
      if s:
        comb_l.append(status)
      if u:
        comb_l.append(usage)
      if t:
        comb_l.append(type)

      comb_r = ''
      for item in comb_l:
        comb_r += f'{item} + '
      comb_r = comb_r[:-3]

      if comb_r not in combs_r.keys():
        combs_r[comb_r] = 1
      else: 
        combs_r[comb_r] = combs_r[comb_r] + 1

    for c in dict_tabl_data.keys():
      if c in combs_r.keys():
        dict_tabl_data[c].append(combs_r[c])
      else:
        dict_tabl_data[c].append(0)

  for c in dict_tabl_data.keys():
    tabl_line = []
    tabl_line.append(c)
    for n in dict_tabl_data[c]:
      tabl_line.append(n)
    tabl_data.append(tabl_line)

  tabl_data.sort(key = lambda row: row[1], reverse=True)

  total_list = ['total',]
  for i in range(1,6):
    tot = 0
    for l in tabl_data:
      tot += l[i]
    total_list.append(tot)
  tabl_data.append(total_list)

  tabl_data.sort(key = lambda row: row[0])
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_apk_in_datasets(file_apks):
  print(f'-------------APKS IN DATASETS-------------')
  jlines = get_file_lines(file_apks)

  data_json = OrderedDict()
  for item in jlines:
      jtem = json.loads(item)
      for k,v in jtem.items():
          data_json[k] = v

  to_add_json_log = OrderedDict()
  for ksha1, kmeta in data_json.items():

    apk_sha1 = kmeta["sha1"]
    apk_in_sets = kmeta["in_sets"]

    perm_meta = OrderedDict()

    perm_meta["apk_sha1"] = apk_sha1
    perm_meta["in_sets"] = apk_in_sets

    to_add_json_log[kmeta["sha1"]] = perm_meta

  results_all = OrderedDict()

  results_all["tot_apk_files"] = 0
  results_all["tot_set_apk"] = OrderedDict()

  for source in sources_all:
    results_all["tot_set_apk"][source] = 0
  
  for fhash,item in to_add_json_log.items():

    results_all["tot_apk_files"] += 1

    xfile_sha1 = item["apk_sha1"].strip()
    xfile_in_sets = item["in_sets"].strip()

    results_all["tot_set_apk"][xfile_in_sets] += 1
  
  headers = ['source','year','# apk']
  tabl_data = []

  for source in sources_good:
    tabl_line = []
    name = source[:-5]
    year = source.split('_')[-1]
    n_apk = results_all["tot_set_apk"][source]
    tabl_line = [name,year,n_apk]
    tabl_data.append(tabl_line)
  tabl_line = []
  name = 'Total good'
  year = ''
  n_apk = 0
  for source in sources_good:
    n_apk += results_all["tot_set_apk"][source]
  tabl_line = [name,year,n_apk]
  tabl_data.append(tabl_line)

  for source in sources_bad:
    tabl_line = []
    name = source
    year = source.split('_')[-1]
    n_apk = results_all["tot_set_apk"][source]
    tabl_line = [name,year,n_apk]
    tabl_data.append(tabl_line)
  tabl_line = []
  name = 'Total bad'
  year = ''
  n_apk = 0
  for source in sources_bad:
    n_apk += results_all["tot_set_apk"][source]
  tabl_line = [name,year,n_apk]
  tabl_data.append(tabl_line)

  tabl_line = []
  name = 'Total all'
  year = ''
  n_apk = 0
  for source in sources_all:
    n_apk += results_all["tot_set_apk"][source]
  tabl_line = [name,year,n_apk]
  tabl_data.append(tabl_line)

  print(tabulate(tabl_data, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_api_in_datasets(file_apks):
  print(f'-------------APIS IN DATASETS-------------')
  jlines = get_file_lines(file_apks)

  data_json = OrderedDict()
  for item in jlines:
      jtem = json.loads(item)
      for k,v in jtem.items():
          data_json[k] = v

  to_add_json_log = OrderedDict()
  for ksha1, kmeta in data_json.items():

    apk_sha1 = kmeta["sha1"]
    apk_in_sets = kmeta["in_sets"]
    apk_api = kmeta["api_level_to_use"] # api_level_to_use max_sdk_version

    perm_meta = OrderedDict()

    perm_meta["apk_sha1"] = apk_sha1
    perm_meta["in_sets"] = apk_in_sets
    perm_meta["api"] = apk_api

    to_add_json_log[kmeta["sha1"]] = perm_meta

  results_all = OrderedDict()

  results_all["tot_apk_files"] = 0
  results_all["tot_set_apk"] = OrderedDict()

  for source in sources_all:
    results_all["tot_set_apk"][source] = OrderedDict()
    for u in range(1,34):
      results_all["tot_set_apk"][source][u] = 0

  for fhash,item in to_add_json_log.items():

    results_all["tot_apk_files"] += 1

    xfile_sha1 = item["apk_sha1"].strip()
    xfile_in_sets = item["in_sets"].strip()
    xfile_api = item["api"]

    if xfile_api in range(1,34):
      results_all["tot_set_apk"][xfile_in_sets][xfile_api] += 1
  
  headers = ['source','8(27)','9(28)','10(29)','11(30)','12(31,32)','13(33)',]
  tabl_data = []

  for source in sources_all:
    tabl_line = []
    name = source
    n_8 = results_all["tot_set_apk"][source][27]
    n_9 = results_all["tot_set_apk"][source][28]
    n_10 = results_all["tot_set_apk"][source][29]
    n_11 = results_all["tot_set_apk"][source][30]
    n_12 = results_all["tot_set_apk"][source][31]
    n_121 = results_all["tot_set_apk"][source][32]
    n_13 = results_all["tot_set_apk"][source][33]
    tabl_line = [name,n_8,n_9,n_10,n_11,n_12+n_121,n_13]
    tabl_data.append(tabl_line)

  name = 'Total'
  tabl_line = [name,]
  for n in range(1,7):
    n_apk = 0
    for line in tabl_data:
      n_apk += line[n]
    tabl_line.append(n_apk)
  tabl_data.append(tabl_line)

  print(tabulate(tabl_data, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_api_all_in_datasets(file_apks,prop):
  print(f'-------------APIS IN DATASETS-------------')
  jlines = get_file_lines(file_apks)

  data_json = OrderedDict()
  for item in jlines:
      jtem = json.loads(item)
      for k,v in jtem.items():
          data_json[k] = v

  to_add_json_log = OrderedDict()
  for ksha1, kmeta in data_json.items():

    apk_sha1 = kmeta["sha1"]
    apk_in_sets = kmeta["in_sets"]
    apk_api = kmeta[prop] # api_level_to_use max_sdk_version

    perm_meta = OrderedDict()

    perm_meta["apk_sha1"] = apk_sha1
    perm_meta["in_sets"] = apk_in_sets
    perm_meta["api"] = apk_api

    to_add_json_log[kmeta["sha1"]] = perm_meta

  results_all = OrderedDict()

  results_all["tot_apk_files"] = 0
  results_all["tot_set_apk"] = OrderedDict()

  for source in sources_all:
    results_all["tot_set_apk"][source] = OrderedDict()
    for u in range(1,34):
      results_all["tot_set_apk"][source][u] = 0

  for fhash,item in to_add_json_log.items():

    results_all["tot_apk_files"] += 1

    xfile_sha1 = item["apk_sha1"].strip()
    xfile_in_sets = item["in_sets"].strip()
    xfile_api = item["api"]

    if xfile_api in range(1,34):
      results_all["tot_set_apk"][xfile_in_sets][xfile_api] += 1

  
  headers = ['source']
  for i in range(1,34):
    headers.append(str(i))
  tabl_data = []

  for source in sources_all:
    tabl_line = []
    name = source
    tabl_line.append(name)
    for i in range(1,34):
      n = results_all["tot_set_apk"][source][i]
      tabl_line.append(n)
    tabl_data.append(tabl_line)

  name = 'Total'
  tabl_line = [name,]
  for n in range(1,34):
    n_apk = 0
    for line in tabl_data:
      n_apk += line[n]
    tabl_line.append(n_apk)
  tabl_data.append(tabl_line)

  print(tabulate(tabl_data, headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def comb_of_rput_by_api(data_29,data_30,data_31,data_33,r=True,p=True,u=True,t=True):
  sets = [data_29,data_30,data_31,data_33]
  combinations = []

  for d_set in sets:
    for i in range(len(d_set['restriction'])):
      restr = d_set['restriction'][i]
      prot = d_set['protection'][i]
      usage = d_set['usage'][i]
      type = d_set['type'][i]

      comb_l = []
      if r:
        comb_l.append(restr)
      if p:
        comb_l.append(prot)
      if u:
        comb_l.append(usage)
      if t:
        comb_l.append(type)

      comb_r = ''
      for item in comb_l:
        comb_r += f'{item} + '
      comb_r = comb_r[:-3]

      if comb_r not in combinations:
        combinations.append(comb_r)
  
  return combinations


#############################################################################################
#############################################################################################
#############################################################################################

def table_perm_analysis_sources(file_permissions,folder_adb_data,sources,version,data_28,data_29,data_30,data_31,data_33):
  print(f'-------------PERMISSIONS REQUESTED/GRANTED IN SOURCES-------------')
  print(f'-------------VERSION: {version}, SOURCES: {sources}')
  combs = comb_of_rput_by_api(data_28,data_29,data_30,data_31,data_33,r=True,p=True,u=False,t=False)
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
      for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
              jdata = json.loads(xline)
              for k,v in jdata.items():
                  if not k in dict_andro_maps:
                      dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  perm_flags_9 = dict()
  perm_flags_10 = dict()
  perm_flags_11 = dict()
  perm_flags_12 = dict()
  perm_flags_13 = dict()

  for perm, data in dict_andro_maps.items():
    apis_manifest = data['seen_in_manifests']
    apis_lists = data['seen_in_lists']
    apis = list(set(apis_manifest + apis_lists))

    if 28 in apis:
        restr_9 = 'does_not_exist'
    else:
        restr_9 = 'missing'
    if 28 in data['seen_in_manifests']:
        prot_9 = data['versions']['28']['protection']
    else:
        prot_9 = 'unknown'

    if 29 in apis:
        restr_10 = data['versions']['29']['restriction']
    else:
        restr_10 = 'missing'
    if 29 in data['seen_in_manifests']:
        prot_10 = data['versions']['29']['protection']
    else:
        prot_10 = 'unknown'

    if 30 in apis:
        restr_11 = data['versions']['30']['restriction']
    else:
        restr_11 = 'missing'
    if 30 in data['seen_in_manifests']:
        prot_11 = data['versions']['30']['protection']
    else:
        prot_11 = 'unknown'
    
    if 31 in apis:
        restr_12 = data['versions']['31']['restriction']
    else:
        restr_12 = 'missing'
    if 31 in data['seen_in_manifests']:
        prot_12 = data['versions']['31']['protection']
    else:
        prot_12 = 'unknown'
    
    if 33 in apis:
        restr_13 = data['versions']['33']['restriction']
    else:
        restr_13 = 'missing'
    if 33 in data['seen_in_manifests']:
        prot_13 = data['versions']['33']['protection']
    else:
        prot_13 = 'unknown'

    perm_comb_9 = f'{restr_9} + {prot_9}'
    perm_comb_10 = f'{restr_10} + {prot_10}'
    perm_comb_11 = f'{restr_11} + {prot_11}'
    perm_comb_12 = f'{restr_12} + {prot_12}'
    perm_comb_13 = f'{restr_13} + {prot_13}'

    perm_flags_9[perm] = perm_comb_9
    perm_flags_10[perm] = perm_comb_10
    perm_flags_11[perm] = perm_comb_11
    perm_flags_12[perm] = perm_comb_12
    perm_flags_13[perm] = perm_comb_13

  del data,perm,perm_comb_9,perm_comb_12

  if version == 9:
    perm_flags = perm_flags_9
    folder_data = f'{folder_adb_data}/adb_vm'
    api = '28'
  elif version == 10:
    perm_flags = perm_flags_10
    folder_data = f'{folder_adb_data}/pixel_29'
    api = '29'
  elif version == 12:
    perm_flags = perm_flags_12
    folder_data = f'{folder_adb_data}/pixel_31'
    api = '31'
  else:
    raise Exception

  # #############################################################################

  tabl_headers = ['restr+prot combination',]
  for source in sources: ################## SOURCES
    tabl_headers.append(f'{source} have')
    tabl_headers.append(f'{source} granted')

  tabl_data = []
  for comb in combs:
      
      apk_have = {}
      apk_grant = {}

      tabl_res = []
      tabl_res.append(comb)

      for source in sources: ################## SOURCES

          have = 0
          granted = 0
          dict_adb_data_lines = OrderedDict()

          with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
              for line in rif:
                  xline = line.replace("\n", "").strip()
                  if xline:
                      jdata = json.loads(xline)
                      for k,v in jdata.items():
                          if not k in dict_adb_data_lines:
                              dict_adb_data_lines[k] = v
          del k,v,line,xline,jdata

          tot_res = OrderedDict()
          tot_res["tot_perms_requested"] = 0

          tot_res["tot_perms_granted_core"] = 0
          tot_res["tot_perms_not_granted_core"] = 0

          for sha1, meta in dict_adb_data_lines.items():
              res = OrderedDict()
              res["tot_perms_requested"] = 0

              res["tot_perms_granted_core"] = 0
              res["tot_perms_not_granted_core"] = 0

              res["perms_requested"] = list()

              res["perms_granted_core"] = list()
              res["perms_not_granted_core"] = list()

              ##### INSTALL #####
              if "install permissions" in meta:
                  for k,v in meta["install permissions"].items():
                      if k in dict_andro_maps:
                          if perm_flags[k] == comb:

                              # parse PERMISSION results
                              pdec = parse_perm_dict(v)

                              if pdec["granted"] == True:
                                  if not k in res["perms_granted_core"]:
                                    # if dict_andro_maps[k]['versions'][api]['deprecated'] == True:
                                      res["perms_granted_core"].append(k)
                                      if source not in apk_grant.keys():
                                          apk_grant[source] = {sha1:[k,]}
                                      else:
                                          if sha1 not in apk_grant[source].keys():
                                              apk_grant[source] = {sha1:[k,]}
                                          else:
                                              apk_grant[source][sha1].append(k)
                                      
                              else:
                                  if not k in res["perms_not_granted_core"]:
                                      res["perms_not_granted_core"].append(k)

              ##### REQUESTED #####
              if "requested permissions" in meta:
                  for k,v in meta["requested permissions"].items():
                      if k in dict_andro_maps:
                          if perm_flags[k] == comb:
                              if not k in res["perms_requested"]:
                                # if dict_andro_maps[k]['versions'][api]['deprecated'] == True:
                                  res["perms_requested"].append(k)
                                  if source not in apk_have.keys():
                                          apk_have[source] = {sha1:[k,]}
                                  else:
                                      if sha1 not in apk_have[source].keys():
                                          apk_have[source] = {sha1:[k,]}
                                      else:
                                          apk_have[source][sha1].append(k)

              res["tot_perms_requested"] = len( res["perms_requested"] )
              res["tot_perms_granted_core"] = len( res["perms_granted_core"] )
              res["tot_perms_not_granted_core"] = len( res["perms_not_granted_core"] )

              tot_res["tot_perms_requested"] = tot_res["tot_perms_requested"] + res["tot_perms_requested"]
              tot_res["tot_perms_granted_core"] = tot_res["tot_perms_granted_core"] + res["tot_perms_granted_core"]
              tot_res["tot_perms_not_granted_core"] = tot_res["tot_perms_not_granted_core"] + res["tot_perms_not_granted_core"]

          tabl_res.append(tot_res["tot_perms_requested"])
          tabl_res.append(tot_res["tot_perms_granted_core"])

      tabl_data.append(tabl_res)

      # if apk_have:
      #     print(f'    have:')
      #     for key in apk_have.keys():
      #         for sha in apk_have[key].keys():
      #             print(f'        {key} - {sha} - {apk_have[key][sha]}')
      #             break
      # if apk_grant:
      #     print(f'    granted:')
      #     for key in apk_grant.keys():
      #         for shgranted:')
      #     for key in apk_grant.keys():
      #         for sha in apk_grant[key].keys():
      #             print(f'        {key} - {sha} - {apk_grant[key][sha]}')
      #             break
      # if not apk_have and not apk_grant:
      #     print('     NONE')

  tabl_data.sort(key = lambda row: row[0])
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()

  #############################################################################################

  tabl_headers = ['restr+prot combination','min','max','avg']

  tabl_data = []
  for comb in combs:
      tabl_res = []
      tabl_res.append(comb)

      comb_counts = []

      for source in sources:

          have = 0
          granted = 0
          # load ADB log
          dict_adb_data_lines = OrderedDict()

          with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
              for line in rif:
                  xline = line.replace("\n", "").strip()
                  if xline:
                      jdata = json.loads(xline)
                      for k,v in jdata.items():
                          if not k in dict_adb_data_lines:
                              dict_adb_data_lines[k] = v
          del k,v,line,xline,jdata

          for sha1, meta in dict_adb_data_lines.items():
              res = OrderedDict()
              res["tot_perms_requested"] = 0

              res["perms_requested"] = list()

              ##### REQUESTED #####
              if "requested permissions" in meta:
                  for k,v in meta["requested permissions"].items():
                      if k in dict_andro_maps:
                          if perm_flags[k] == comb:
                            if not k in res["perms_requested"]:
                                res["perms_requested"].append(k)

              res["tot_perms_requested"] = len( res["perms_requested"] )

              comb_counts.append(res["tot_perms_requested"])
      min_n = min(comb_counts)
      max_n = max(comb_counts)
      avg_n = int(statistics.mean(comb_counts))
      tabl_res.append(min_n)
      tabl_res.append(max_n)
      tabl_res.append(avg_n)

      tabl_data.append(tabl_res)

  tabl_data.sort(key = lambda row: row[0])
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_perms_by_rp(data_28,data_29,data_30,data_31,data_33):
  print(f'-------------PERMISSIONS BY RESTRICTION/PROTECTION-------------')
  sets = [data_28,data_29,data_30,data_31,data_33]
  tabl_headers = ['restriction \\ protection','signature','internal','system','normal','dangerous',]
  tabl_data = []
  set_restr = set()
  set_prot = set()

  for d_set in sets:
      for i in range(len(d_set['restriction'])):
          restr = d_set['restriction'][i]
          prot = d_set['protection'][i]

          set_restr.add(restr)
          set_prot.add(prot)

  count = 9
  for d_set in sets:
      tabl_data = []

      dict_tabl_data = OrderedDict()
      for r in set_restr:
          ps = OrderedDict()
          for p in set_prot:
              ps[p] = 0
          dict_tabl_data[r] = ps

      for i in range(len(d_set['restriction'])):
          restr = d_set['restriction'][i]
          prot = d_set['protection'][i]

          dict_tabl_data[restr][prot] = dict_tabl_data[restr][prot] + 1
      
      for r in dict_tabl_data.keys():
          tabl_line = [r,]
          tabl_line.append(dict_tabl_data[r]['signature'])
          tabl_line.append(dict_tabl_data[r]['internal'])
          tabl_line.append(dict_tabl_data[r]['system'])
          tabl_line.append(dict_tabl_data[r]['normal'])
          tabl_line.append(dict_tabl_data[r]['dangerous'])

          tabl_data.append(tabl_line)
      
      tabl_data.sort(key = lambda row: row[0],)
      print(count)
      count += 1
      print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
      print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_granted_by_rp(file_permissions,folder_adb_data,folder_name,version,data,sources):
  print(f'-------------PERMISSIONS GRANTED BY RESTRICTION/PROTECTION, ON VERSION {version}-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception

  sets = [data]
  tabl_headers = ['','signature','internal','system','normal','dangerous',]
  tabl_data = []
  set_restr = set()
  set_prot = set()

  for d_set in sets:
    for i in range(len(d_set['restriction'])):
      restr = d_set['restriction'][i]
      prot = d_set['protection'][i]

      set_restr.add(restr)
      set_prot.add(prot)

  for d_set in sets:
    tabl_data = []

    dict_tabl_data = OrderedDict()
    for r in set_restr:
      ps = OrderedDict()
      for p in set_prot:
        ps[p] = 0
        ps[f'{p}_granted'] = 0
      dict_tabl_data[r] = ps

    for i in range(len(d_set['restriction'])):
      restr = d_set['restriction'][i]
      prot = d_set['protection'][i]

      dict_tabl_data[restr][prot] = dict_tabl_data[restr][prot] + 1
    
    dict_adb_data_lines = OrderedDict()

    for source in sources:

      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
        
    for apk,meta in dict_adb_data_lines.items():
      granted_perms = meta['install permissions'].keys()
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if int(api) in apis:
            tag = dict_andro_maps[p]['versions'][api]['tag']
            restr = dict_andro_maps[p]['versions'][api]['restriction']
            if int(api) == 28:
              restr = restr.replace('XXX','does_not_exist')
            else:
              restr = restr.replace('XXX','missing')
            prot = dict_andro_maps[p]['versions'][api]['protection']
            status = dict_andro_maps[p]['versions'][api]['status']
            usage = dict_andro_maps[p]['versions'][api]['usage']
            type = dict_andro_maps[p]['versions'][api]['type']
            dict_tabl_data[restr][f'{prot}_granted'] = dict_tabl_data[restr][f'{prot}_granted'] + 1
    
    for r in dict_tabl_data.keys():
      tabl_line = [r,]
      tabl_line.append(dict_tabl_data[r]['signature_granted'])
      try:
        tabl_line.append(dict_tabl_data[r]['internal_granted'])
      except:
        tabl_line.append(0)
      try:
        tabl_line.append(dict_tabl_data[r]['system_granted'])
      except:
        tabl_line.append(0)
      tabl_line.append(dict_tabl_data[r]['normal_granted'])
      tabl_line.append(dict_tabl_data[r]['dangerous_granted'])

      tabl_data.append(tabl_line)
    
    tabl_data.sort(key = lambda row: row[0], reverse=True)
    print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
    print()


#############################################################################################
#############################################################################################
#############################################################################################

def print_combinations(file_permissions,folder_adb_data,folder_name,version,sources):
  print(f'-------------COMBINATIONS, ON VERSION {version}-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
    with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
      for line in rif:
        xline = line.replace("\n", "").strip()
        if xline:
          jdata = json.loads(xline)
          for k,v in jdata.items():
            if not k in dict_adb_data_lines:
              dict_adb_data_lines[k] = v
    try:
      del k,v,line,xline,jdata
    except UnboundLocalError:
      pass
      
  set_combs = set()
  for p in dict_andro_maps.keys():
    apis_manifest = dict_andro_maps[p]['seen_in_manifests']
    apis_lists = dict_andro_maps[p]['seen_in_lists']
    apis = list(set(apis_manifest + apis_lists))
    if int(api) in apis:
      tag = dict_andro_maps[p]['versions'][api]['tag']
      restr = dict_andro_maps[p]['versions'][api]['restriction']
      prot = dict_andro_maps[p]['versions'][api]['protection']
      status = dict_andro_maps[p]['versions'][api]['status']
      usage = dict_andro_maps[p]['versions'][api]['usage']
      type = dict_andro_maps[p]['versions'][api]['type']
      comb = f'{tag} + {restr} + {prot} + {status} + {usage} + {type}'
      set_combs.add(comb)
  
  for c in set_combs:
    print(c)


#############################################################################################
#############################################################################################
#############################################################################################

def print_combinations_in_apks(file_permissions,folder_adb_data,folder_name,version,sources):
  print(f'-------------COMBINATIONS IN APKS, ON VERSION {version}-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
      
  set_combs = set()
  for apk,meta in dict_adb_data_lines.items():
    granted_perms = meta['install permissions'].keys()
    for p in granted_perms:
      if p in dict_andro_maps.keys():
        apis_manifest = dict_andro_maps[p]['seen_in_manifests']
        apis_lists = dict_andro_maps[p]['seen_in_lists']
        apis = list(set(apis_manifest + apis_lists))
        if int(api) in apis:
          tag = dict_andro_maps[p]['versions'][api]['tag']
          restr = dict_andro_maps[p]['versions'][api]['restriction']
          prot = dict_andro_maps[p]['versions'][api]['protection']
          status = dict_andro_maps[p]['versions'][api]['status']
          usage = dict_andro_maps[p]['versions'][api]['usage']
          type = dict_andro_maps[p]['versions'][api]['type']
          comb = f'{tag} + {restr} + {prot} + {status} + {usage} + {type}'
          set_combs.add(comb)
  
  for comb in set_combs:
    print(comb)


#############################################################################################
#############################################################################################
#############################################################################################

def count_apk_perms(file_permissions,folder_adb_data,folder_name,sources,perms):
  
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
    
  apks_violate = OrderedDict()

  list_perms = perms.split('\n')

  for c in list_perms:
    apks_violate[c] = []
      
  # set_combs = set()
  for apk,meta in dict_adb_data_lines.items():
    
    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      cur_api = int(cur_api[0])
    else:
      print(1)

    if cur_api in test_apis:
      granted_perms = [x for x in meta['install']['requested permissions'].keys() 
                          if x in meta['run']['requested permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          if p in list_perms:
            if apk not in apks_violate[p]:
              apks_violate[p].append(apk)

  return apks_violate


#############################################################################################
#############################################################################################
#############################################################################################

def combine_apks(list_dicts):
  dict_combined = OrderedDict()
  for d in list_dicts:
    for perm in d.keys():
      dict_combined[perm] = []
  
  for d in list_dicts:
    for perm,apks in d.items():
      for apk in apks:
        dict_combined[perm].append(apk)

  tabl_headers = ['perm','# apk']
  tabl_data = []
  for perm,list_apks in dict_combined.items():
    tabl_line = [perm,len(set(list_apks))]
    tabl_data.append(tabl_line)

  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def combine_apks_apis(list_dicts,folder_names,sources):

  dict_adb_data_lines = OrderedDict()

  for folder_name in folder_names:
    folder_data = f'{folder_adb_data}/{folder_name}'
    for source in sources:

      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                if is_apk_runnable(v):
                  dict_adb_data_lines[k] = v
              else:
                pass
      
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass

  dict_combined = OrderedDict()
  for d in list_dicts:
    for perm in d.keys():
      dict_combined[perm] = []
  
  for d in list_dicts:
    for perm,apks in d.items():
      for apk in apks:
        dict_combined[perm].append(apk)

  count_apis = ['29','30','31','32','33']
  tabl_headers = ['perm','# apk'] + count_apis
  tabl_data = []

  for perm,list_apks in dict_combined.items():
    set_apks = set(list_apks)
    api_counts = OrderedDict()
    for a in count_apis:
      api_counts[a] = 0
    for apk in set_apks:
      meta = dict_adb_data_lines[apk]
      cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
      cur_api = [x for x in cur_apis if x != None]
      if len(cur_api) == 1:
        # if cur_api == ['']:
        #   continue
        cur_api = int(cur_api[0])
      else:
        print(1)
      api_counts[str(cur_api)] += 1
    tabl_line = [perm,len(set_apks)]
    for a in count_apis:
      tabl_line.append(api_counts[a])
    tabl_data.append(tabl_line)

  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def print_bad_combinations_in_apks(file_permissions,folder_adb_data,folder_name,version,sources):
  print(f'-------------COMBINATIONS IN APKS, ON VERSION {version}-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
    
  apks_violate = OrderedDict()
  bad_combs = [
    'sdk + public + normal + relevant + general + RUNTIME PERMISSIONS',
    'sdk + public + normal + backw_comp + general + RUNTIME PERMISSIONS',
    'sdk + public + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + normal + relevant + general + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + restricted + INSTALL PERMISSIONS',
    'hide + conditional_block_max_r + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + normal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + general + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + restricted + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + general + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS',
  ]

  
  for c in bad_combs:
    apks_violate[c] = OrderedDict()
    for source in sources:
      apks_violate[c][source] = OrderedDict()
      
  set_combs = set()
  for apk,meta in dict_adb_data_lines.items():
    granted_perms = meta['install permissions'].keys()
    for p in granted_perms:
      if p in dict_andro_maps.keys():
        apis_manifest = dict_andro_maps[p]['seen_in_manifests']
        apis_lists = dict_andro_maps[p]['seen_in_lists']
        apis = list(set(apis_manifest + apis_lists))
        if int(api) in apis:
          tag = dict_andro_maps[p]['versions'][api]['tag']
          restr = dict_andro_maps[p]['versions'][api]['restriction']
          prot = dict_andro_maps[p]['versions'][api]['protection']
          status = dict_andro_maps[p]['versions'][api]['status']
          usage = dict_andro_maps[p]['versions'][api]['usage']
          type = dict_andro_maps[p]['versions'][api]['type']
          comb = f'{tag} + {restr} + {prot} + {status} + {usage} + {type}'
          set_combs.add(comb)
          if comb in bad_combs:
            inset = meta['in_sets']
            if apk not in apks_violate[comb][inset].keys():
              apks_violate[comb][inset][apk] = [p,]
            else:
              apks_violate[comb][inset][apk].append(p)
  
  for comb in bad_combs:
    print(comb)
    for source in apks_violate[comb].keys():
      print(f'  {source}')
      for apk in apks_violate[comb][source].keys():
        print(f'    {apk}')
        for p in apks_violate[comb][source][apk]:
          print(f'      {p}')


#############################################################################################
#############################################################################################
#############################################################################################

def bad_combinations_in_apks(file_permissions,folder_adb_data,folder_name,sources,show_combs=True):
  print(f'-------------COMBINATIONS IN APKS, {folder_name}-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
    
  apks_violate = OrderedDict()

  bad_combs_all = [
    'sdk + public + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + normal + relevant + general + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + restricted + INSTALL PERMISSIONS',
    'hide + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + blacklist + signature + relevant + general + INSTALL PERMISSIONS',
    'system + sdk + normal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + general + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + restricted + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + general + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + dangerous + relevant + general + RUNTIME PERMISSIONS',
  ]

  bad_combs_req = [
    'hide + conditional_block_max_o + normal + relevant + general + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + conditional_block_max_o + signature + relevant + restricted + INSTALL PERMISSIONS',
    'hide + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS',
    'hide + blacklist + signature + relevant + general + INSTALL PERMISSIONS',
    'system + sdk + normal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + general + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + signature + relevant + restricted + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + general + INSTALL PERMISSIONS',
    'system + sdk + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS',
    'system + sdk + dangerous + relevant + general + RUNTIME PERMISSIONS',
  ]
  for c in bad_combs_req:
    apks_violate[c] = OrderedDict()
    for source in sources:
      apks_violate[c][source] = OrderedDict()
  
  tot_apks = set()
  set_combs = set()
  for apk,meta in dict_adb_data_lines.items():

    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      # if cur_api == ['']:
      #   continue
      cur_api = int(cur_api[0])
    else:
      print(1)
    if cur_api in test_apis:
      granted_perms = [x for x in meta['install']['requested permissions'].keys() 
                          if x in meta['run']['requested permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            comb = get_perm_comb(dict_andro_maps,p,cur_api)
            set_combs.add(comb)
            if comb in bad_combs_req:
              inset = meta['in_sets']
              if apk not in apks_violate[comb][inset].keys():
                apks_violate[comb][inset][apk] = [p,]
                tot_apks.add(apk)
              else:
                apks_violate[comb][inset][apk].append(p)
  
  perms_set_tot = set()
  print('REQUESTED:')
  perms_set = set()
  for comb in bad_combs_req:
    # perms_set = set()
    if show_combs:
      print(comb)
    for source in apks_violate[comb].keys():
      # print(f'  {source}')
      for apk in apks_violate[comb][source].keys():
        # print(f'    {apk}, {source}')
        for p in apks_violate[comb][source][apk]:
          perms_set.add(p)
          perms_set_tot.add(p)
          
    perms_list_req = sorted(list(perms_set))
    # for p in perms_list_req:
    #   print(p)
    
  # perms_list = sorted(list(perms_set))
  # for p in perms_list:
  #   print(p)
  
  # print()
  # print(len(tot_apks))
  # print()


  for c in bad_combs_all:
    apks_violate[c] = OrderedDict()
    for source in sources:
      apks_violate[c][source] = OrderedDict()
  
  tot_apks = set()
  set_combs = set()
  for apk,meta in dict_adb_data_lines.items():

    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      # if cur_api == ['']:
      #   continue
      cur_api = int(cur_api[0])
    else:
      print(1)
    if cur_api in test_apis:
      granted_perms = [x for x in meta['install']['install permissions'].keys() 
                          if x in meta['run']['install permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            comb = get_perm_comb(dict_andro_maps,p,cur_api)
            set_combs.add(comb)
            if comb in bad_combs_all:
              inset = meta['in_sets']
              if apk not in apks_violate[comb][inset].keys():
                apks_violate[comb][inset][apk] = [p,]
                tot_apks.add(apk)
              else:
                apks_violate[comb][inset][apk].append(p)
  
  print('GRANTED:')
  perms_set = set()
  for comb in bad_combs_all:
    # perms_set = set()
    if show_combs:
      print(comb)
    for source in apks_violate[comb].keys():
      # print(f'  {source}')
      for apk in apks_violate[comb][source].keys():
        # print(f'    {apk}, {source}')
        for p in apks_violate[comb][source][apk]:
          perms_set.add(p)
          perms_set_tot.add(p)
          
    perms_list_grn = sorted(list(perms_set))
    # for p in perms_list_grn:
    #   print(p)
    
  # perms_list = sorted(list(perms_set))
  # for p in perms_list:
  #   print(p)
  
  # print()
  # print(len(tot_apks))
  # print()

  # print('TOTAL:')
  perms_list_tot = sorted(list(perms_set_tot))
  # for p in perms_list_tot:
    # print(p)
  
  # print()

  return perms_list_req,perms_list_grn,perms_list_tot


#############################################################################################
#############################################################################################
#############################################################################################

def table_granted_by_tp(file_permissions,folder_adb_data,version,data):
  print(f'-------------EXAMPLE GRANTING BY TYPE, VERSION {version}-------------')
  sets = [data]
  tabl_headers = ['','normal','adb granted','signature','adb granted','dangerous','adb granted','internal','adb granted','system','adb granted',]
  tabl_data = []
  set_type = set()
  set_prot = set()

  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  for d_set in sets:
    for i in range(len(d_set['restriction'])):
      type = d_set['type'][i]
      prot = d_set['protection'][i]

      set_type.add(type)
      set_prot.add(prot)

  for d_set in sets:
    tabl_data = []

    dict_tabl_data = OrderedDict()
    for r in set_type:
      ps = OrderedDict()
      for p in set_prot:
        ps[p] = 0
        ps[f'{p}_granted'] = 0
      dict_tabl_data[r] = ps

    for i in range(len(d_set['restriction'])):
      type = d_set['type'][i]
      prot = d_set['protection'][i]

      dict_tabl_data[type][prot] = dict_tabl_data[type][prot] + 1
    
    dict_adb_data_lines = OrderedDict()

    if version == 9:
      file_data = f'{folder_adb_data}/own/vmapks_adb_permissions.json'
      api = '28'
    elif version == 12:
      file_data = f'{folder_adb_data}/own/phoneapks_adb_permissions.json'
      api = '31'
    else:
      raise Exception
    # /home/user01/Desktop/test_apk/outputs/dumps/vmapks_adb_permissions.json
    with io.open(f'{path_script}/{file_data}', 'r') as rif:
      for line in rif:
        xline = line.replace("\n", "").strip()
        if xline:
          jdata = json.loads(xline)
          for k,v in jdata.items():
            if not k in dict_adb_data_lines:
              dict_adb_data_lines[k] = v
    del k,v,line,xline,jdata

    install_perms_adb = dict_adb_data_lines['allperms']['install permissions']

    for perm in install_perms_adb.keys():
      try:
        type = dict_andro_maps[perm]['versions'][api]['type']
        prot = dict_andro_maps[perm]['versions'][api]['protection']
        dict_tabl_data[type][f'{prot}_granted'] = dict_tabl_data[type][f'{prot}_granted'] + 1
      except:
        pass
    
    for r in dict_tabl_data.keys():
      tabl_line = [r,]
      tabl_line.append(dict_tabl_data[r]['normal'])
      tabl_line.append(dict_tabl_data[r]['normal_granted'])
      tabl_line.append(dict_tabl_data[r]['signature'])
      tabl_line.append(dict_tabl_data[r]['signature_granted'])
      tabl_line.append(dict_tabl_data[r]['dangerous'])
      tabl_line.append(dict_tabl_data[r]['dangerous_granted'])
      if version == 12:
        tabl_line.append(dict_tabl_data[r]['internal'])
        tabl_line.append(dict_tabl_data[r]['internal_granted'])
        tabl_line.append(dict_tabl_data[r]['system'])
        tabl_line.append(dict_tabl_data[r]['system_granted'])
      elif version == 9:
        tabl_line.append(0)
        tabl_line.append(0)
        tabl_line.append(0)
        tabl_line.append(0)

      tabl_data.append(tabl_line)
    
    tabl_data.sort(key = lambda row: row[0])
    print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
    print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_granted_by_attr_attr(file_permissions,folder_adb_data,folder_name,version,data,sources,attr1,attr2):
  # 'tag'  'restriction' 'protection' 'status' 'usage' 'type'
  print(f'-------------GRANTING BY {attr1}/{attr2} , VERSION {version}-------------')
  sets = [data]
  # tabl_headers = ['','normal','adb granted','signature','adb granted','dangerous','adb granted','internal','adb granted','system','adb granted',]
  tabl_headers = ['',]
  tabl_data = []
  set_attr1 = set()
  set_attr2 = set()

  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception

  for d_set in sets:
    for i in range(len(d_set['restriction'])):
      attr1_value = d_set[attr1][i]
      attr2_value = d_set[attr2][i]

      set_attr1.add(attr1_value)
      set_attr2.add(attr2_value)

  for d_set in sets:
    tabl_data = []

    dict_tabl_data = OrderedDict()
    for r in set_attr1:
      ps = OrderedDict()
      for p in set_attr2:
        ps[p] = 0
        ps[f'{p}_requested'] = 0
        ps[f'{p}_granted'] = 0
      dict_tabl_data[r] = ps

    for i in range(len(d_set['restriction'])):
      attr1_value = d_set[attr1][i]
      attr2_value = d_set[attr2][i]

      dict_tabl_data[attr1_value][attr2_value] = dict_tabl_data[attr1_value][attr2_value] + 1
    
    dict_adb_data_lines = OrderedDict()

    for source in sources:

      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
        
    for apk,meta in dict_adb_data_lines.items():

      requested_perms = meta['requested permissions'].keys()
      for p in requested_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if int(api) in apis:
            attr1_value = dict_andro_maps[p]['versions'][api][attr1]
            attr2_value = dict_andro_maps[p]['versions'][api][attr2]
            if attr1 == 'restriction':
              if int(api) == 28:
                attr1_value = attr1_value.replace('XXX','does_not_exist')
              else:
                attr1_value = attr1_value.replace('XXX','missing')
            if attr2 == 'restriction':
              if int(api) == 28:
                attr2_value = attr2_value.replace('XXX','does_not_exist')
              else:
                attr2_value = attr2_value.replace('XXX','missing')
            dict_tabl_data[attr1_value][f'{attr2_value}_requested'] = dict_tabl_data[attr1_value][f'{attr2_value}_requested'] + 1

      granted_perms = meta['install permissions'].keys()
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if int(api) in apis:
            attr1_value = dict_andro_maps[p]['versions'][api][attr1]
            attr2_value = dict_andro_maps[p]['versions'][api][attr2]
            if attr1 == 'restriction':
              if int(api) == 28:
                attr1_value = attr1_value.replace('XXX','does_not_exist')
              else:
                attr1_value = attr1_value.replace('XXX','missing')
            if attr2 == 'restriction':
              if int(api) == 28:
                attr2_value = attr2_value.replace('XXX','does_not_exist')
              else:
                attr2_value = attr2_value.replace('XXX','missing')
            dict_tabl_data[attr1_value][f'{attr2_value}_granted'] = dict_tabl_data[attr1_value][f'{attr2_value}_granted'] + 1
    
    attr2_list = sorted(list(set_attr2))
    for a2 in attr2_list:
      tabl_headers.append(f'{a2} R')
      tabl_headers.append(f'{a2} G')
    for a1 in dict_tabl_data.keys():
      tabl_line = [a1,]
      for a2 in attr2_list:
        try:
          tabl_line.append(dict_tabl_data[a1][f'{a2}_requested'])
          tabl_line.append(dict_tabl_data[a1][f'{a2}_granted'])
        except:
          tabl_line.append(0)
      tabl_data.append(tabl_line)
    
    tabl_data.sort(key = lambda row: row[0])
    print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
    print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_select_mapping_perms(file_lists,file_permissions):
  perms = """android.permission.ACCESS_SURFACE_FLINGER
android.permission.CALL_COMPANION_APP
android.permission.CAPTURE_AUDIO_OUTPUT
android.permission.DELETE_PACKAGES
android.permission.DUMP
android.permission.HARDWARE_TEST
android.permission.MODIFY_PHONE_STATE
android.permission.READ_LOGS
android.permission.READ_PRIVILEGED_PHONE_STATE
android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME
android.permission.SUBSTITUTE_SHARE_TARGET_APP_NAME_AND_ICON
android.permission.UPDATE_APP_OPS_STATS
android.permission.UPDATE_DEVICE_STATS
android.permission.CHANGE_COMPONENT_ENABLED_STATE
android.permission.INSTALL_PACKAGES
android.permission.INTERACT_ACROSS_USERS
android.permission.INTERACT_ACROSS_USERS_FULL
android.permission.MANAGE_USERS
android.permission.MEDIA_CONTENT_CONTROL
android.permission.SET_PROCESS_LIMIT
android.permission.STATUS_BAR
android.permission.DEVICE_POWER
android.permission.INJECT_EVENTS
android.permission.INTERNAL_SYSTEM_WINDOW
android.permission.WRITE_SECURE_SETTINGS
android.permission.HIGH_SAMPLING_RATE_SENSORS
android.permission.READ_INSTALL_SESSIONS
android.permission.WRITE_SOCIAL_STREAM
android.permission.READ_SOCIAL_STREAM
android.permission.SUBSCRIBED_FEEDS_WRITE
android.permission.SUBSCRIBED_FEEDS_READ
android.permission.WRITE_PROFILE
android.permission.MANAGE_OWN_CALLS
android.permission.WRITE_USER_DICTIONARY
android.permission.READ_USER_DICTIONARY
com.android.browser.permission.WRITE_HISTORY_BOOKMARKS
android.permission.USE_BIOMETRIC
android.permission.WRITE_SMS
com.android.browser.permission.READ_HISTORY_BOOKMARKS
android.permission.READ_PROFILE
android.permission.AUTHENTICATE_ACCOUNTS
android.permission.USE_FINGERPRINT
android.permission.FLASHLIGHT
android.permission.MANAGE_ACCOUNTS
android.permission.USE_CREDENTIALS"""
  perms_list = perms.split('\n')
  tabl_headers = ['permission','introduced','tag','restriction','protection','status','usage','type','comment']
  tabl_data = []
  done_perms = []
  data_mapping = OrderedDict()
  with io.open(f'{path_script}/data/mapping_12.json') as inp:
    data_mapping = json.load(inp)

  for p in perms_list:
    if p in data_mapping.keys():
      data_ver = data_mapping[p]
      intr = data_ver['introduced']
      tag = data_ver['tag']
      res_l = data_ver['restriction_list']
      prit_l = data_ver['protection_level']
      stat = data_ver['status']
      usg = data_ver['usage']
      type = data_ver['type']
      com = data_ver['comment']
      tabl_line = [p,intr,tag,res_l,prit_l,stat,usg,type,com]
      tabl_data.append(tabl_line)
    else:
      raise Exception

  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_count_combs_mapping(file_lists,file_permissions):
  
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
      for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
              jdata = json.loads(xline)
              for k,v in jdata.items():
                  if not k in dict_andro_maps:
                      dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  perm_flags_10 = dict()
  perm_flags_11 = dict()
  perm_flags_12 = dict()
  perm_flags_13 = dict()

  for perm, data in dict_andro_maps.items():
    apis_manifest = data['seen_in_manifests']
    apis_lists = data['seen_in_lists']
    apis = list(set(apis_manifest + apis_lists))

    if 29 in apis:
        restr_10 = data['versions']['29']['restriction'].replace('XXX','missing')
    else:
        restr_10 = 'missing'
    if 29 in data['seen_in_manifests']:
        prot_10 = data['versions']['29']['protection']
        tag_10 = data['versions']['29']['tag']
        status_10 = data['versions']['29']['status']
        usage_10 = data['versions']['29']['usage']
        type_10 = data['versions']['29']['type']
    else:
        prot_10 = 'unknown'
        tag_10 = 'unknown'
        status_10 = 'unknown'
        usage_10 = 'unknown'
        type_10 = 'unknown'

    if 30 in apis:
        restr_11 = data['versions']['30']['restriction'].replace('XXX','missing')
    else:
        restr_11 = 'missing'
    if 30 in data['seen_in_manifests']:
        prot_11 = data['versions']['30']['protection']
        tag_11 = data['versions']['30']['tag']
        status_11 = data['versions']['30']['status']
        usage_11 = data['versions']['30']['usage']
        type_11 = data['versions']['30']['type']
    else:
        prot_11 = 'unknown'
        tag_11 = 'unknown'
        status_11 = 'unknown'
        usage_11 = 'unknown'
        type_11 = 'unknown'
    
    if 31 in apis:
        restr_12 = data['versions']['31']['restriction'].replace('XXX','missing')
    else:
        restr_12 = 'missing'
    if 31 in data['seen_in_manifests']:
        prot_12 = data['versions']['31']['protection']
        tag_12 = data['versions']['31']['tag']
        status_12 = data['versions']['31']['status']
        usage_12 = data['versions']['31']['usage']
        type_12 = data['versions']['31']['type']
    else:
        prot_12 = 'unknown'
        tag_12 = 'unknown'
        status_12 = 'unknown'
        usage_12 = 'unknown'
        type_12 = 'unknown'
    
    if 33 in apis:
        restr_13 = data['versions']['33']['restriction'].replace('XXX','missing')
    else:
        restr_13 = 'missing'
    if 33 in data['seen_in_manifests']:
        prot_13 = data['versions']['33']['protection']
        tag_13 = data['versions']['33']['tag']
        status_13 = data['versions']['33']['status']
        usage_13 = data['versions']['33']['usage']
        type_13 = data['versions']['33']['type']
    else:
        prot_13 = 'unknown'
        tag_13 = 'unknown'
        status_13 = 'unknown'
        usage_13 = 'unknown'
        type_13 = 'unknown'

    perm_comb_10 = f'{tag_10} + {restr_10} + {prot_10} + {status_10} + {usage_10} + {type_10}'
    perm_comb_11 = f'{tag_11} + {restr_11} + {prot_11} + {status_11} + {usage_11} + {type_11}'
    perm_comb_12 = f'{tag_12} + {restr_12} + {prot_12} + {status_12} + {usage_12} + {type_12}'
    perm_comb_13 = f'{tag_13} + {restr_13} + {prot_13} + {status_13} + {usage_13} + {type_13}'

    perm_flags_10[perm] = perm_comb_10
    perm_flags_11[perm] = perm_comb_11
    perm_flags_12[perm] = perm_comb_12
    perm_flags_13[perm] = perm_comb_13

  combs_all = OrderedDict()
  combs_all[10] = OrderedDict()
  combs_all[11] = OrderedDict()
  combs_all[12] = OrderedDict()
  combs_all[13] = OrderedDict()
  dicts_perm_to_comb = [perm_flags_10,perm_flags_11,perm_flags_12,perm_flags_13]
  k = 10
  for d in dicts_perm_to_comb:
    for perm,comb in d.items():
      if comb in combs_all[k].keys():
        combs_all[k][comb].append(perm)
      else:
        combs_all[k][comb] = [perm]
    k += 1
  
  # print(1)

  comb_to_allperms = OrderedDict()
  comb_to_newpermcounts = OrderedDict()
  for k in range(10,14):
    for comb,perms in combs_all[k].items():
      if comb not in comb_to_newpermcounts.keys():
        comb_to_allperms[comb] = set(perms)
        comb_to_newpermcounts[comb] = []
        for _ in range(0,k-10):
          comb_to_newpermcounts[comb].append(0)
      comb_to_newpermcounts[comb].append(len(perms))
      # if comb == 'hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS' and k == 13:
      #   for p in perms:
      #     print(p)
  
  combs_sorted = OrderedDict(sorted(comb_to_newpermcounts.items()))

  text_combs = """sdk + public + normal + relevant + general + INSTALL PERMISSIONS
sdk + public + normal + relevant + general + RUNTIME PERMISSIONS
sdk + public + normal + backw_comp + general + INSTALL PERMISSIONS
sdk + public + normal + backw_comp + general + RUNTIME PERMISSIONS
sdk + public + signature + relevant + general + INSTALL PERMISSIONS
sdk + public + signature + relevant + general + RUNTIME PERMISSIONS
sdk + public + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
sdk + public + signature + relevant + restricted + INSTALL PERMISSIONS
sdk + public + signature + relevant + restricted + RUNTIME PERMISSIONS
sdk + public + signature + backw_comp + general + INSTALL PERMISSIONS
sdk + public + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS
sdk + public + dangerous + relevant + general + INSTALL PERMISSIONS
sdk + public + dangerous + relevant + general + RUNTIME PERMISSIONS
sdk + public + dangerous + backw_comp + general + RUNTIME PERMISSIONS
sdk + public + internal + relevant + general + INSTALL PERMISSIONS
sdk + public + internal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + sdk + signature + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + normal + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS
hide + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + relevant + general + RUNTIME PERMISSIONS
hide + conditional_block_max_o + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + relevant + restricted + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + backw_comp + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + backw_comp + general + RUNTIME PERMISSIONS
hide + conditional_block_max_r + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
hide + unsupported + signature + relevant + general + INSTALL PERMISSIONS
hide + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + general + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + general + RUNTIME PERMISSIONS
hide + blacklist + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
hide + blacklist + signature + relevant + restricted + INSTALL PERMISSIONS
hide + missing + signature + relevant + general + INSTALL PERMISSIONS
system + sdk + normal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + normal + backw_comp + general + REMOVED PERMISSIONS
system + sdk + signature + relevant + general + INSTALL PERMISSIONS
system + sdk + signature + relevant + general + RUNTIME PERMISSIONS
system + sdk + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + signature + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + sdk + signature + relevant + restricted + INSTALL PERMISSIONS
system + sdk + signature + backw_comp + general + INSTALL PERMISSIONS
system + sdk + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + dangerous + relevant + general + RUNTIME PERMISSIONS
system + sdk + internal + relevant + general + INSTALL PERMISSIONS
system + sdk + internal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + internal + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + sdk + internal + relevant + restricted + INSTALL PERMISSIONS
system + sdk + internal + relevant + restricted + RUNTIME PERMISSIONS
system + sdk + system + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS
system + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
system + blacklist + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
unknown + public + unknown + unknown + unknown + unknown
unknown + sdk + unknown + unknown + unknown + unknown
unknown + conditional_block_max_o + unknown + unknown + unknown + unknown"""
  list_text = text_combs.split('\n')
  list_text_combs = []
  for c in list_text:
    # if c.endswith('INSTALL') or c.endswith('RUNTIME') or c.endswith('REMOVED'):
    #   c = f'{c} PERMISSIONS'
    list_text_combs.append(c)

  tabl_headers = ['comb','a10','a11','a12','a13']
  tabl_data = []
  for comb in list_text_combs:
    counts = combs_sorted[comb]
    l = len(counts)
    if l < 4:
      for _ in range(0,4-l):
        counts.append(0)
    tabl_line = [comb] + counts
    tabl_data.append(tabl_line)
  
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def table_count_combs_mapping_new(file_lists,file_permissions):
  print(f'-------------NEW PERMISSION COUNTS IN MANIFESTS BY COMBS-------------')
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
      for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
              jdata = json.loads(xline)
              for k,v in jdata.items():
                  if not k in dict_andro_maps:
                      dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  perm_flags_10 = dict()
  perm_flags_11 = dict()
  perm_flags_12 = dict()
  perm_flags_13 = dict()

  for perm, data in dict_andro_maps.items():
    apis_manifest = data['seen_in_manifests']
    apis_lists = data['seen_in_lists']
    apis = list(set(apis_manifest + apis_lists))

    if 29 in apis_lists:
        restr_10 = data['versions']['29']['restriction']
    else:
        restr_10 = 'missing'
    if 29 in data['seen_in_manifests']:
        prot_10 = data['versions']['29']['protection']
        tag_10 = data['versions']['29']['tag']
        status_10 = data['versions']['29']['status']
        usage_10 = data['versions']['29']['usage']
        type_10 = data['versions']['29']['type']
    else:
        prot_10 = 'unknown'
        tag_10 = 'unknown'
        status_10 = 'unknown'
        usage_10 = 'unknown'
        type_10 = 'unknown'
    if 29 in apis:
      perm_comb_10 = f'{tag_10} + {restr_10} + {prot_10} + {status_10} + {usage_10} + {type_10}'
      perm_flags_10[perm] = perm_comb_10

    if 30 in apis_lists:
        restr_11 = data['versions']['30']['restriction']
    else:
        restr_11 = 'missing'
    if 30 in data['seen_in_manifests']:
        prot_11 = data['versions']['30']['protection']
        tag_11 = data['versions']['30']['tag']
        status_11 = data['versions']['30']['status']
        usage_11 = data['versions']['30']['usage']
        type_11 = data['versions']['30']['type']
    else:
        prot_11 = 'unknown'
        tag_11 = 'unknown'
        status_11 = 'unknown'
        usage_11 = 'unknown'
        type_11 = 'unknown'
    if 30 in apis:
      perm_comb_11 = f'{tag_11} + {restr_11} + {prot_11} + {status_11} + {usage_11} + {type_11}'
      perm_flags_11[perm] = perm_comb_11
    
    if 31 in apis_lists:
        restr_12 = data['versions']['31']['restriction']
    else:
        restr_12 = 'missing'
    if 31 in data['seen_in_manifests']:
        prot_12 = data['versions']['31']['protection']
        tag_12 = data['versions']['31']['tag']
        status_12 = data['versions']['31']['status']
        usage_12 = data['versions']['31']['usage']
        type_12 = data['versions']['31']['type']
    else:
        prot_12 = 'unknown'
        tag_12 = 'unknown'
        status_12 = 'unknown'
        usage_12 = 'unknown'
        type_12 = 'unknown'
    if 31 in apis:
      perm_comb_12 = f'{tag_12} + {restr_12} + {prot_12} + {status_12} + {usage_12} + {type_12}'
      perm_flags_12[perm] = perm_comb_12
    
    if 33 in apis_lists:
        restr_13 = data['versions']['33']['restriction']
    else:
        restr_13 = 'missing'
    if 33 in data['seen_in_manifests']:
        prot_13 = data['versions']['33']['protection']
        tag_13 = data['versions']['33']['tag']
        status_13 = data['versions']['33']['status']
        usage_13 = data['versions']['33']['usage']
        type_13 = data['versions']['33']['type']
    else:
        prot_13 = 'unknown'
        tag_13 = 'unknown'
        status_13 = 'unknown'
        usage_13 = 'unknown'
        type_13 = 'unknown'
    if 33 in apis:
      perm_comb_13 = f'{tag_13} + {restr_13} + {prot_13} + {status_13} + {usage_13} + {type_13}'
      perm_flags_13[perm] = perm_comb_13

  combs_all = OrderedDict()
  combs_all[10] = OrderedDict()
  combs_all[11] = OrderedDict()
  combs_all[12] = OrderedDict()
  combs_all[13] = OrderedDict()
  dicts_perm_to_comb = [perm_flags_10,perm_flags_11,perm_flags_12,perm_flags_13]
  k = 10
  for d in dicts_perm_to_comb:
    for perm,comb in d.items():
      if comb in combs_all[k].keys():
        combs_all[k][comb].append(perm)
      else:
        combs_all[k][comb] = [perm]
    k += 1
  
  comb_to_allperms = OrderedDict()
  comb_to_newpermcounts = OrderedDict()
  for k in range(10,14):
    for comb,perms in combs_all[k].items():
      if comb not in comb_to_newpermcounts.keys():
        comb_to_allperms[comb] = set(perms)
        comb_to_newpermcounts[comb] = []
        for _ in range(0,k-10):
          comb_to_newpermcounts[comb].append(0)
        comb_to_newpermcounts[comb].append(len(perms))
      else:
        old_count = len(comb_to_allperms[comb])
        for p in perms:
          comb_to_allperms[comb].add(p)
        new_count = len(comb_to_allperms[comb])
        comb_to_newpermcounts[comb].append(new_count-old_count)
  
  combs_sorted = OrderedDict(sorted(comb_to_newpermcounts.items()))
  combs_allsorted = OrderedDict(sorted(comb_to_allperms.items()))

  tabl_headers = ['comb','a10','a11','a12','a13']
  tabl_data = []
  for comb,counts in combs_sorted.items():
    l = len(counts)
    if l < 4:
      for _ in range(0,4-l):
        counts.append(0)
    tabl_line = [comb] + counts
    tabl_data.append(tabl_line)
  
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def get_all_perms(file_permissions):

  set_perms = set()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in set_perms:
            set_perms.add(k)
  del k,v,line,xline,jdata
  count=0
  for p in set_perms:
    count+=1
    print(f'<uses-permission android:name="{p}" />')
  

#############################################################################################
#############################################################################################
#############################################################################################

def get_perms_conflicts(file_permissions):

  perm_to_attrs = OrderedDict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          perm_to_attrs[k] = v
  del k,v,line,xline,jdata
  
  dict_conflicts = OrderedDict()
  conflicts = ['NR','SR','DC','BG','ET','PT','EL','PL','EI','PI','IG','HG','OG']
  # dict_issues = OrderedDict()
  # issues = ['CB','BL','N3','RE','SY']
  
  for conf in conflicts:
    dict_conflicts[conf] = OrderedDict()
    for ver in range(10,14):
      dict_conflicts[conf][str(ver_to_api[str(ver)])] = []
  # for conf in issues:
  #   dict_issues[conf] = OrderedDict()
  #   for ver in range(10,14):
  #     dict_issues[conf][str(ver_to_api[str(ver)])] = []
  
  for perm,meta in perm_to_attrs.items():
    for ver in api_to_ver.keys():
      if ver in meta['versions'].keys():
        data = meta['versions'][ver]

        # NR
        if data['protection_level'] == 'normal' and data['type'] == 'RUNTIME PERMISSIONS':
          dict_conflicts['NR'][ver].append(perm)
        # SR
        if data['protection'] == 'signature' and data['type'] == 'RUNTIME PERMISSIONS':
          dict_conflicts['SR'][ver].append(perm)
        # DC
        if data['protection'] == 'dangerous' and data['type'] == 'INSTALL PERMISSIONS':
          dict_conflicts['DC'][ver].append(perm)
        # BG
        if data['restriction'] == 'blacklist' and data['usage'] == 'general':
          dict_conflicts['BG'][ver].append(perm)
        # ET
        if data['tag'] == 'sdk' and data['usage'] == 'not_by_third_party_apps':
          dict_conflicts['ET'][ver].append(perm)
        # PT
        if data['restriction'] == 'public' and data['usage'] == 'not_by_third_party_apps':
          dict_conflicts['PT'][ver].append(perm)
        # EL
        if data['tag'] == 'sdk' and data['usage'] == 'restricted':
          dict_conflicts['EL'][ver].append(perm)
        # PL
        if data['restriction'] == 'public' and data['usage'] == 'restricted':
          dict_conflicts['PL'][ver].append(perm)
        # EI
        if data['tag'] == 'sdk' and data['protection'] == 'internal':
          dict_conflicts['EI'][ver].append(perm)
        # PI
        if data['restriction'] == 'public' and data['protection'] == 'internal':
          dict_conflicts['PI'][ver].append(perm)
        # IG
        if data['protection'] == 'internal' and data['usage'] == 'general':
          dict_conflicts['IG'][ver].append(perm)
        # HG
        if data['tag'] == 'hide' and data['usage'] == 'general':
          dict_conflicts['HG'][ver].append(perm)
        # OG
        if data['tag'] == 'system' and data['usage'] == 'general':
          dict_conflicts['OG'][ver].append(perm)
        
        # # CB
        # if data['tag'] == 'system' and data['usage'] == 'general':
        #   dict_conflicts['CB'][ver].append(perm)
        # # BL
        # if data['tag'] == 'system' and data['usage'] == 'general':
        #   dict_conflicts['SY'][ver].append(perm)
        # # N3
        # if data['tag'] == 'system' and data['usage'] == 'general':
        #   dict_conflicts['N3'][ver].append(perm)
        # # RE
        # if data['tag'] == 'system' and data['usage'] == 'general':
        #   dict_conflicts['RE'][ver].append(perm)
        # # SY
        # if data['tag'] == 'system' and data['usage'] == 'general':
        #   dict_conflicts['SY'][ver].append(perm)
  
  for conf,meta in dict_conflicts.items():
    print(conf)
    cur = []
    for ii in range(len(api_to_ver.keys())):
      ver = list(api_to_ver.keys())[ii]
      if ii != 0:
        ver_prev = list(api_to_ver.keys())[ii-1]
      else:
        ver_prev = False
      perms = sorted(meta[ver])
      added = []
      new = []
      old = []
      stayed = []
      removed = []
      gone = []
      changed = []
      cur_new = []
      cur_copy = list(cur)
      for perm in perms:
        if perm not in cur:
          cur_new.append(perm)
          added.append(perm)
          if ver_prev:
            if ver_prev in perm_to_attrs[perm]['versions'].keys():
              old.append(perm)
            else:
              new.append(perm)
        else:
          cur_new.append(perm)
          stayed.append(perm)
          cur_copy.remove(perm)
      for perm in cur_copy:
        removed.append(perm)
        if ver in perm_to_attrs[perm]['versions'].keys():
          changed.append(perm)
        else:
          gone.append(perm)
      cur = cur_new
      for perm in cur_copy:
        if perm in added:
          continue
        if perm in stayed:
          continue
        if perm in removed:
          continue
        print(perm)
      print(f'  [{ver}] {len(added)} added, {len(stayed)} stayed, {len(removed)} removed; current: {len(cur_new)}')
      if ver_prev and added:
        print(f'    added: new - {len(new)}, old - {len(old)}')
        if old:
          print('',end='')
      if removed:
        print(f'    removed: changed - {len(changed)}, gone - {len(gone)}')
        print('',end='')


#############################################################################################
#############################################################################################
#############################################################################################

def count_req_granted_by_text_combs(file_permissions,folder_adb_data,folder_name,sources):
  text_combs = """sdk + public + normal + relevant + general + INSTALL PERMISSIONS
sdk + public + normal + relevant + general + RUNTIME PERMISSIONS
sdk + public + normal + backw_comp + general + INSTALL PERMISSIONS
sdk + public + normal + backw_comp + general + RUNTIME PERMISSIONS
sdk + public + signature + relevant + general + INSTALL PERMISSIONS
sdk + public + signature + relevant + general + RUNTIME PERMISSIONS
sdk + public + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
sdk + public + signature + relevant + restricted + INSTALL PERMISSIONS
sdk + public + signature + relevant + restricted + RUNTIME PERMISSIONS
sdk + public + signature + backw_comp + general + INSTALL PERMISSIONS
sdk + public + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS
sdk + public + dangerous + relevant + general + INSTALL PERMISSIONS
sdk + public + dangerous + relevant + general + RUNTIME PERMISSIONS
sdk + public + dangerous + backw_comp + general + RUNTIME PERMISSIONS
sdk + public + internal + relevant + general + INSTALL PERMISSIONS
sdk + public + internal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + sdk + signature + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + normal + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + normal + backw_comp + general + REMOVED PERMISSIONS
hide + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + relevant + general + RUNTIME PERMISSIONS
hide + conditional_block_max_o + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + relevant + restricted + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + backw_comp + general + INSTALL PERMISSIONS
hide + conditional_block_max_o + signature + backw_comp + general + RUNTIME PERMISSIONS
hide + conditional_block_max_r + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
hide + unsupported + signature + relevant + general + INSTALL PERMISSIONS
hide + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + general + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + general + RUNTIME PERMISSIONS
hide + blacklist + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
hide + blacklist + signature + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
hide + blacklist + signature + relevant + restricted + INSTALL PERMISSIONS
hide + missing + signature + relevant + general + INSTALL PERMISSIONS
system + sdk + normal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + normal + backw_comp + general + REMOVED PERMISSIONS
system + sdk + signature + relevant + general + INSTALL PERMISSIONS
system + sdk + signature + relevant + general + RUNTIME PERMISSIONS
system + sdk + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + signature + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + sdk + signature + relevant + restricted + INSTALL PERMISSIONS
system + sdk + signature + backw_comp + general + INSTALL PERMISSIONS
system + sdk + signature + backw_comp + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + dangerous + relevant + general + RUNTIME PERMISSIONS
system + sdk + internal + relevant + general + INSTALL PERMISSIONS
system + sdk + internal + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
system + sdk + internal + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + sdk + internal + relevant + restricted + INSTALL PERMISSIONS
system + sdk + internal + relevant + restricted + RUNTIME PERMISSIONS
system + sdk + system + relevant + not_by_third_party_apps + RUNTIME PERMISSIONS
system + conditional_block_max_o + signature + relevant + general + INSTALL PERMISSIONS
system + unsupported + signature + removed + not_by_third_party_apps + INSTALL PERMISSIONS
system + blacklist + signature + relevant + not_by_third_party_apps + INSTALL PERMISSIONS
unknown + public + unknown + unknown + unknown + unknown
unknown + sdk + unknown + unknown + unknown + unknown
unknown + conditional_block_max_o + unknown + unknown + unknown + unknown"""
  list_text = text_combs.split('\n')
  list_text_combs = []
  for c in list_text:
    # if c.endswith('INSTALL') or c.endswith('RUNTIME') or c.endswith('REMOVED'):
    #   c = f'{c} PERMISSIONS'
    list_text_combs.append(c)

  print(folder_name)

  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'

  tabl_data = []
  dict_tabl_data = OrderedDict()
  for c in list_text_combs:
    dict_tabl_data[c] = {
      'requested_install':0,
      'granted_install':0,
      'requested_run':0,
      'granted_run':0,
      'requested_both':0,
      'granted_both':0,
      }
  dict_adb_data_lines = OrderedDict()

  apps = 0
  apps_ok = 0

  for source in sources:

    with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
      for line in rif:
        xline = line.replace("\n", "").strip()
        if xline:
          jdata = json.loads(xline)
          for k,v in jdata.items():
            if not k in dict_adb_data_lines:
              dict_adb_data_lines[k] = v
    try:
      del k,v,line,xline,jdata
    except UnboundLocalError:
      pass

  reasons = set()
  dict_g_not_r = OrderedDict()
  perm_to_comb = OrderedDict()
      
  for apk,meta in dict_adb_data_lines.items():

    apps += 1

    if apk not in set_apps_working:
      continue

    apps_ok += 1

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      # if cur_api == ['']:
      #   continue
      cur_api = int(cur_api[0])
      if cur_api == 32:
        cur_api = 31
    else:
      print(1)
        
    if cur_api in test_apis:

      if meta['has_diff']:

        for install_or_run in ['install','run']:
          
          unique_case = f'unique_{install_or_run}'
          req_case = f'requested_{install_or_run}'
          grn_case = f'granted_{install_or_run}'
          requested_perms = meta['diff'][unique_case]['requested permissions'].keys()
          for p in requested_perms:
            if p in dict_andro_maps.keys():
              reason = meta['diff'][unique_case]['requested permissions'][p]['reason']
              reasons.add(reason)
              if reason == 'diff_perm':
                apis_manifest = dict_andro_maps[p]['seen_in_manifests']
                apis_lists = dict_andro_maps[p]['seen_in_lists']
                apis = list(set(apis_manifest + apis_lists))
                if cur_api in apis:
                  combination = get_perm_comb(dict_andro_maps,p,cur_api)
                  dict_tabl_data[combination][req_case] += 1

          granted_perms = meta['diff'][unique_case]['install permissions'].keys()
          for p in granted_perms:
            if p in dict_andro_maps.keys():
              reason = meta['diff'][unique_case]['install permissions'][p]['reason']
              reasons.add(reason)
              if reason == 'diff_perm':
                apis_manifest = dict_andro_maps[p]['seen_in_manifests']
                apis_lists = dict_andro_maps[p]['seen_in_lists']
                apis = list(set(apis_manifest + apis_lists))
                if cur_api in apis:
                  combination = get_perm_comb(dict_andro_maps,p,cur_api)
                  dict_tabl_data[combination][grn_case] += 1
        

      requested_perms = [x for x in meta['install']['requested permissions'].keys() 
                            if x in meta['run']['requested permissions'].keys()]
      
      granted_perms = [x for x in meta['install']['install permissions'].keys() 
                          if x in meta['run']['install permissions'].keys()]


      m_requested_perms = [x for x in requested_perms if x in dict_andro_maps.keys()]
      m_granted_perms = [x for x in granted_perms if x in dict_andro_maps.keys()]
      set_requested_perms = set(m_requested_perms)
      set_granted_perms = set(m_granted_perms)
      req_len = len(m_requested_perms)
      req_u_len = len(list(set_requested_perms))
      gr_len = len(m_granted_perms)
      gr_u_len = len(list(set_granted_perms))
      if req_len > req_u_len:
        print('requested dupes')
      if gr_len > gr_u_len:
        print('granted dupes')
      difference1 = list()
      for item in m_granted_perms:
          if item not in m_requested_perms:
              if item not in dict_g_not_r.keys():
                dict_g_not_r[item] = 1
              else:
                dict_g_not_r[item] += 1
              difference1.append(item)

      difference2 = list()
      for item in m_requested_perms:
          if item not in m_granted_perms:
              difference2.append(item)


      for p in requested_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            combination = get_perm_comb(dict_andro_maps,p,cur_api)
            dict_tabl_data[combination]['requested_both'] += 1

      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            combination = get_perm_comb(dict_andro_maps,p,cur_api)
            if p in dict_g_not_r.keys():
                perm_to_comb[p] = combination
            dict_tabl_data[combination]['granted_both'] += 1


  tabl_headers = [
    'combination',
    'requested_both','granted_both',
    'requested_install','granted_install',
    'requested_run','granted_run',
    ]
  tabl_data = []
  for c in dict_tabl_data.keys():
    tabl_line = [
      c,
      dict_tabl_data[c]['requested_both'],dict_tabl_data[c]['granted_both'],
      dict_tabl_data[c]['requested_install'],dict_tabl_data[c]['granted_install'],
      dict_tabl_data[c]['requested_run'],dict_tabl_data[c]['granted_run'],
      ]
    tabl_data.append(tabl_line)
  
  print(f'apps total: {apps}; apps ok: {apps_ok}')
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()

  for p,n in dict_g_not_r.items():
    print(f'{p}: {n}    {perm_to_comb[p]}')


#############################################################################################
#############################################################################################
#############################################################################################

def count_req_granted_by_depr(dict_apk_api,file_permissions,folder_adb_data,folder_name,version,sources):

  tabl_headers = ['deprecated','requested','granted']
  tabl_data = []
  list_text_combs = ['False','True','noinfo']

  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
  if version == 9:
    api = '28'
  elif version == 10:
    api = '29'
  elif version == 11:
    api = '30'
  elif version == 12:
    api = '31'
  elif version == 13:
    api = '33'
  else:
    raise Exception

  tabl_data = []
  dict_tabl_data = OrderedDict()
  for c in list_text_combs:
    dict_tabl_data[c] = {'requested':0, 'granted':0}
  dict_adb_data_lines = OrderedDict()

  for source in sources:

    with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
      for line in rif:
        xline = line.replace("\n", "").strip()
        if xline:
          jdata = json.loads(xline)
          for k,v in jdata.items():
            if not k in dict_adb_data_lines:
              dict_adb_data_lines[k] = v
    try:
      del k,v,line,xline,jdata
    except UnboundLocalError:
      pass
      
  for apk,meta in dict_adb_data_lines.items():
    try:
      cur_api = dict_apk_api[apk]['api']
    except KeyError:
      continue
    if cur_api in test_apis:

      requested_perms = meta['requested permissions'].keys()
      for p in requested_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            depr = dict_andro_maps[p]['versions'][str(cur_api)]['deprecated']
            dict_tabl_data[str(depr)]['requested'] = dict_tabl_data[str(depr)]['requested'] + 1
          else:
            dict_tabl_data['noinfo']['requested'] = dict_tabl_data['noinfo']['requested'] + 1

      granted_perms = meta['install permissions'].keys()
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          apis_manifest = dict_andro_maps[p]['seen_in_manifests']
          apis_lists = dict_andro_maps[p]['seen_in_lists']
          apis = list(set(apis_manifest + apis_lists))
          if cur_api in apis:
            depr = dict_andro_maps[p]['versions'][str(cur_api)]['deprecated']
            dict_tabl_data[str(depr)]['granted'] = dict_tabl_data[str(depr)]['granted'] + 1
          else:
            dict_tabl_data['noinfo']['granted'] = dict_tabl_data['noinfo']['granted'] + 1

  
  for c in dict_tabl_data.keys():
    tabl_line = [c,dict_tabl_data[c]['requested'],dict_tabl_data[c]['granted']]
    tabl_data.append(tabl_line)
  totr = 0
  totg = 0
  for c in dict_tabl_data.keys():
    totr += dict_tabl_data[c]['requested']
    totg += dict_tabl_data[c]['granted']
  tabl_line = ['total',totr,totg]
  tabl_data.append(tabl_line)
  
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


#############################################################################################
#############################################################################################
#############################################################################################

def apks_same(file_apks):

  e10 = '/home/user01/Desktop/paper_perms/scripts/data/adb_parsed/out/pixel_29_emulator'
  e12 = '/home/user01/Desktop/paper_perms/scripts/data/adb_parsed/out/pixel_31_emulator'
  p10 = '/home/user01/Desktop/paper_perms/scripts/data/adb_parsed/out/10_phone'
  p12 = '/home/user01/Desktop/paper_perms/scripts/data/adb_parsed/out/12_phone'

  devices = [e10,e12,p10,p12]
  levels = [29,30,31,32,33]

  jlines = get_file_lines(file_apks)

  data_json = OrderedDict()
  for item in jlines:
      jtem = json.loads(item)
      for k,v in jtem.items():
          data_json[k] = v

  dict_adb_data_lines = OrderedDict()

  for d in devices:
    skipped = 0
    dict_adb_data_lines[d] = []
    for file in os.listdir(d):
      if 'vs_' not in file:

        with io.open(f'{d}/{file}', 'r') as rif:
          for line in rif:
            xline = line.replace("\n", "").strip()
            if xline:
              jdata = json.loads(xline)
              for k,v in jdata.items():
                if not k in dict_adb_data_lines:
                  if v['err_type'] != 'INSTALL':
                    try:
                      if data_json[k]["api_level_to_use"] in levels:
                        dict_adb_data_lines[d].append(k)
                    except KeyError:
                      skipped+=1
                      pass
                  # else: print(1)
    print(d)
    print(len(dict_adb_data_lines[d]))
    print(skipped)

  
  print('---------------------')
  es = [value for value in dict_adb_data_lines[e10] if value in dict_adb_data_lines[e12]] 
  print(len(es))

  ps = [value for value in dict_adb_data_lines[p10] if value in dict_adb_data_lines[p12]] 
  print(len(ps))

  all = [value for value in ps if value in es] 
  print(len(all))
  print(1)


#############################################################################################
#############################################################################################
#############################################################################################

def count_apk_violating(file_permissions,folder_adb_data,folder_name,sources):
  
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
    
  apks_violate_req = OrderedDict()
  for ap in test_apis:
    apks_violate_req[str(ap)] = [set(),list()]
  apks_violate_grn = OrderedDict()
  for ap in test_apis:
    apks_violate_grn[str(ap)] = [set(),list()]
    
  set_hide = set()
  set_system = set()

  set_errr = set()

  set_cb = set()
  set_bl = set()
  set_n3 = set()
  set_re = set()
  set_sy = set()

  set_errg = set()
  list_err = []
      
  # set_combs = set()
  for apk,meta in dict_adb_data_lines.items():
    
    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      cur_api = int(cur_api[0])
    else:
      print(1)

    if cur_api in test_apis:
      if cur_api == 32:
        use_api = 31
      else: 
        use_api = cur_api
      requested_perms = [x for x in meta['install']['requested permissions'].keys() 
                          if x in meta['run']['requested permissions'].keys()]
      for p in requested_perms:
        if p in dict_andro_maps.keys():
          try:
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'hide':
              set_hide.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'system':
              set_system.add(apk)
          except KeyError:
            CHECK = dict_andro_maps[p]
            set_errr.add(apk)
            list_err.append(apk)
            apks_violate_req[str(cur_api)][0].add(apk)
            apks_violate_req[str(cur_api)][1].append(apk)
      
      granted_perms = [x for x in meta['install']['install permissions'].keys() 
                          if x in meta['run']['install permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          try:
            if dict_andro_maps[p]['versions'][str(use_api)]['restriction'].startswith('conditional_block'):
              set_cb.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['restriction'] == 'blacklist':
              set_bl.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['usage'] == 'not_by_third_party_apps':
              set_n3.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['usage'] == 'restricted':
              set_re.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'system':
              set_sy.add(apk)
          except KeyError:
            set_errg.add(apk)
            list_err.append(apk)
            apks_violate_grn[str(cur_api)][0].add(apk)
            apks_violate_grn[str(cur_api)][1].append(apk)

  return set_hide,set_system,set_cb,set_bl,set_n3,set_re,set_sy,set_errr,set_errg,apks_violate_req,apks_violate_grn


def count_apk_violating_general(file_permissions,folder_adb_data,folder_name,sources):
  
  dict_andro_maps = dict()
  with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
    for line in rif:
      xline = line.replace("\n", "").strip()
      if xline:
        jdata = json.loads(xline)
        for k,v in jdata.items():
          if not k in dict_andro_maps:
            dict_andro_maps[k] = v
  del k,v,line,xline,jdata

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
      
  set_violate = set()

  for apk,meta in dict_adb_data_lines.items():
    
    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      cur_api = int(cur_api[0])
    else:
      print(1)

    if cur_api in test_apis:
      if cur_api == 32:
        use_api = 31
      else: 
        use_api = cur_api
      requested_perms = [x for x in meta['install']['requested permissions'].keys() 
                          if x in meta['run']['requested permissions'].keys()]
      for p in requested_perms:
        if p in dict_andro_maps.keys():
          try:
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'hide':
              set_violate.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'system':
              set_violate.add(apk)
          except KeyError:
            CHECK = dict_andro_maps[p]
            set_violate.add(apk)
      
      granted_perms = [x for x in meta['install']['install permissions'].keys() 
                          if x in meta['run']['install permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          try:
            if dict_andro_maps[p]['versions'][str(use_api)]['restriction'].startswith('conditional_block'):
              set_violate.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['restriction'] == 'blacklist':
              set_violate.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['usage'] == 'not_by_third_party_apps':
              set_violate.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['usage'] == 'restricted':
              set_violate.add(apk)
            if dict_andro_maps[p]['versions'][str(use_api)]['tag'] == 'system':
              set_violate.add(apk)
          except KeyError:
            set_violate.add(apk)

  return set_violate


def count_apk_violating_mapping(file_permissions,folder_adb_data,folder_name,sources):

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
      
  apks_violate_req = OrderedDict()
  for ap in test_apis:
    apks_violate_req[str(ap)] = [set(),list(),OrderedDict()]
  apks_violate_grn = OrderedDict()
  for ap in test_apis:
    apks_violate_grn[str(ap)] = [set(),list(),OrderedDict()]

  tr = 0
  tg = 0
  for apk,meta in dict_adb_data_lines.items():
    
    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      cur_api = int(cur_api[0])
    else:
      print(1)

    if cur_api in test_apis:
      if cur_api == 32:
        use_api = 31
      else: 
        use_api = cur_api
      requested_perms = meta['meta']['used permissions']
      for p in requested_perms:
        if p in dict_andro_maps.keys():
          try:
            tt = dict_andro_maps[p]['versions'][str(use_api)]
          except KeyError:
            apks_violate_req[str(cur_api)][0].add(apk)
            apks_violate_req[str(cur_api)][1].append(apk)
            if p not in apks_violate_req[str(cur_api)][2].keys():
              apks_violate_req[str(cur_api)][2][p] = 1
            else:
              apks_violate_req[str(cur_api)][2][p] += 1

      
      granted_perms = [x for x in meta['install']['install permissions'].keys() 
                          if x in meta['run']['install permissions'].keys()]
      for p in granted_perms:
        if p in dict_andro_maps.keys():
          try:
            tt = dict_andro_maps[p]['versions'][str(use_api)]
          except KeyError:
            apks_violate_grn[str(cur_api)][0].add(apk)
            apks_violate_grn[str(cur_api)][1].append(apk)
            if p not in apks_violate_grn[str(cur_api)][2].keys():
              apks_violate_grn[str(cur_api)][2][p] = 1
            else:
              apks_violate_grn[str(cur_api)][2][p] += 1

  return apks_violate_req,apks_violate_grn


#############################################################################################
#############################################################################################
#############################################################################################

def apk_violating(file_permissions,folder_adb_data):
  set_aht = set()
  set_aot = set()

  set_errrt = set()

  set_cbt = set()
  set_blt = set()
  set_n3t = set()
  set_ret = set()
  set_syt = set()

  set_errgt = set()

  tbl_violate = [
    ['','29 apk','29 inst','30 apk','30 inst','31 apk','31 inst','32 apk','32 inst','33 apk','33 inst',],
    ['req',],
    ['grn',],
  ]
  apks_violate_req_tot = OrderedDict()
  for ap in test_apis:
    apks_violate_req_tot[str(ap)] = [set(),list()]
  apks_violate_grn_tot = OrderedDict()
  for ap in test_apis:
    apks_violate_grn_tot[str(ap)] = [set(),list()]

  print('10 errors req, grn')
  set_hide,set_system,set_cb,set_bl,set_n3,set_re,set_sy,set_errr,set_errg,apks_violate_req,apks_violate_grn = \
    count_apk_violating(file_permissions,folder_adb_data,'out/output_10_phone_2',sources_good)
  print(len(set_errr))
  print(len(set_errg))
  print()
  for hsh in set_hide:
    set_aht.add(hsh)
  for hsh in set_system:
    set_aot.add(hsh)
  for hsh in set_cb:
    set_cbt.add(hsh)
  for hsh in set_bl:
    set_blt.add(hsh)
  for hsh in set_n3:
    set_n3t.add(hsh)
  for hsh in set_re:
    set_ret.add(hsh)
  for hsh in set_sy:
    set_syt.add(hsh)
  for hsh in set_errr:
    set_errrt.add(hsh)
  for hsh in set_errg:
    set_errgt.add(hsh)
  for ap in test_apis:
    for hsh in apks_violate_req[str(ap)][0]:
      apks_violate_req_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_req[str(ap)][1]:
      apks_violate_req_tot[str(ap)][1].append(hsh)
    for hsh in apks_violate_grn[str(ap)][0]:
      apks_violate_grn_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_grn[str(ap)][1]:
      apks_violate_grn_tot[str(ap)][1].append(hsh)
  
  print('11 errors req, grn')
  set_hide,set_system,set_cb,set_bl,set_n3,set_re,set_sy,set_errr,set_errg,apks_violate_req,apks_violate_grn = \
    count_apk_violating(file_permissions,folder_adb_data,'out/output_11_phone_2',sources_good)
  print(len(set_errr))
  print(len(set_errg))
  print()
  for hsh in set_hide:
    set_aht.add(hsh)
  for hsh in set_system:
    set_aot.add(hsh)
  for hsh in set_cb:
    set_cbt.add(hsh)
  for hsh in set_bl:
    set_blt.add(hsh)
  for hsh in set_n3:
    set_n3t.add(hsh)
  for hsh in set_re:
    set_ret.add(hsh)
  for hsh in set_sy:
    set_syt.add(hsh)
  for hsh in set_errr:
    set_errrt.add(hsh)
  for hsh in set_errg:
    set_errgt.add(hsh)
  for ap in test_apis:
    for hsh in apks_violate_req[str(ap)][0]:
      apks_violate_req_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_req[str(ap)][1]:
      apks_violate_req_tot[str(ap)][1].append(hsh)
    for hsh in apks_violate_grn[str(ap)][0]:
      apks_violate_grn_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_grn[str(ap)][1]:
      apks_violate_grn_tot[str(ap)][1].append(hsh)
  
  # # combine_apks([d1,d2])
  print('12 errors req, grn')
  set_hide,set_system,set_cb,set_bl,set_n3,set_re,set_sy,set_errr,set_errg,apks_violate_req,apks_violate_grn = \
    count_apk_violating(file_permissions,folder_adb_data,'out/output_12_phone_2',sources_good)
  print(len(set_errr))
  print(len(set_errg))
  print()
  for hsh in set_hide:
    set_aht.add(hsh)
  for hsh in set_system:
    set_aot.add(hsh)
  for hsh in set_cb:
    set_cbt.add(hsh)
  for hsh in set_bl:
    set_blt.add(hsh)
  for hsh in set_n3:
    set_n3t.add(hsh)
  for hsh in set_re:
    set_ret.add(hsh)
  for hsh in set_sy:
    set_syt.add(hsh)
  for hsh in set_errr:
    set_errrt.add(hsh)
  for hsh in set_errg:
    set_errgt.add(hsh)
  for ap in test_apis:
    for hsh in apks_violate_req[str(ap)][0]:
      apks_violate_req_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_req[str(ap)][1]:
      apks_violate_req_tot[str(ap)][1].append(hsh)
    for hsh in apks_violate_grn[str(ap)][0]:
      apks_violate_grn_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_grn[str(ap)][1]:
      apks_violate_grn_tot[str(ap)][1].append(hsh)
  
  print('13 errors req, grn')
  set_hide,set_system,set_cb,set_bl,set_n3,set_re,set_sy,set_errr,set_errg,apks_violate_req,apks_violate_grn = \
    count_apk_violating(file_permissions,folder_adb_data,'out/output_13_phone_2',sources_good)
  print(len(set_errr))
  print(len(set_errg))
  print()
  for hsh in set_hide:
    set_aht.add(hsh)
  for hsh in set_system:
    set_aot.add(hsh)
  for hsh in set_cb:
    set_cbt.add(hsh)
  for hsh in set_bl:
    set_blt.add(hsh)
  for hsh in set_n3:
    set_n3t.add(hsh)
  for hsh in set_re:
    set_ret.add(hsh)
  for hsh in set_sy:
    set_syt.add(hsh)
  for hsh in set_errr:
    set_errrt.add(hsh)
  for hsh in set_errg:
    set_errgt.add(hsh)
  for ap in test_apis:
    for hsh in apks_violate_req[str(ap)][0]:
      apks_violate_req_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_req[str(ap)][1]:
      apks_violate_req_tot[str(ap)][1].append(hsh)
    for hsh in apks_violate_grn[str(ap)][0]:
      apks_violate_grn_tot[str(ap)][0].add(hsh)
    for hsh in apks_violate_grn[str(ap)][1]:
      apks_violate_grn_tot[str(ap)][1].append(hsh)
  
  for ap in test_apis:
    tbl_violate[1].append(len(apks_violate_req_tot[str(ap)][0]))
    tbl_violate[1].append(len(apks_violate_req_tot[str(ap)][1]))
    tbl_violate[2].append(len(apks_violate_grn_tot[str(ap)][0]))
    tbl_violate[2].append(len(apks_violate_grn_tot[str(ap)][1]))

  print(tabulate(tbl_violate, tablefmt="github"))
  print()
  # combine_apks([d3,d4])
  # combine_apks([d1,d2,d3,d4])

  set_tot_req = set()
  for hsh in set_aht:
    set_tot_req.add(hsh)
  for hsh in set_aot:
    set_tot_req.add(hsh)

  set_tot_grn = set()
  for hsh in set_cbt:
    set_tot_grn.add(hsh)
  for hsh in set_blt:
    set_tot_grn.add(hsh)
  for hsh in set_n3t:
    set_tot_grn.add(hsh)
  for hsh in set_ret:
    set_tot_grn.add(hsh)
  for hsh in set_syt:
    set_tot_grn.add(hsh)

  set_tot_tot = set()
  for hsh in set_tot_req:
    set_tot_tot.add(hsh)
  for hsh in set_tot_grn:
    set_tot_tot.add(hsh)

  print('total requested')
  print(len(set_aht))  
  print(len(set_aot))
  print(len(set_tot_req))
  print(len(set_errrt))
  print()
  print('total granted')
  print(len(set_cbt))  
  print(len(set_blt))  
  print(len(set_n3t))  
  print(len(set_ret))  
  print(len(set_syt))  
  print(len(set_tot_grn))
  print(len(set_errgt))
  print('total')
  print(len(set_tot_tot))


def apk_violating_general(file_permissions,folder_adb_data):
  
  set_violate_tot = set()

  set_violate = \
    count_apk_violating_general(file_permissions,folder_adb_data,'out/output_10_phone_2',sources_good)
  
  for hsh in set_violate:
    set_violate_tot.add(hsh)
  print(len(set_violate_tot))
  
  set_violate = \
    count_apk_violating_general(file_permissions,folder_adb_data,'out/output_11_phone_2',sources_good)
  
  for hsh in set_violate:
    set_violate_tot.add(hsh)
  print(len(set_violate_tot))
  
  # # combine_apks([d1,d2])
  set_violate = \
    count_apk_violating_general(file_permissions,folder_adb_data,'out/output_12_phone_2',sources_good)
  
  for hsh in set_violate:
    set_violate_tot.add(hsh)
  print(len(set_violate_tot))
  
  set_violate = \
    count_apk_violating_general(file_permissions,folder_adb_data,'out/output_13_phone_2',sources_good)
  
  for hsh in set_violate:
    set_violate_tot.add(hsh)
  print(len(set_violate_tot))

  # combine_apks([d3,d4])
  # combine_apks([d1,d2,d3,d4])
  print(len(set_violate_tot))


def apk_violating_mapping(file_permissions,folder_adb_data):
  
  print('apks request smth not persent in mapping')
  
  tbl_violate = [
    ['','29 apk','29 inst','30 apk','30 inst','31 apk','31 inst','32 apk','32 inst','33 apk','33 inst',],
    ['req',],
    ['grn',],
  ]

  outs = [
    'out/output_10_phone_2',
    'out/output_11_phone_2',
    'out/output_12_phone_2',
    'out/output_13_phone_2',
  ]

  for outf in outs:

    set_violate_req,set_violate_grn = \
      count_apk_violating_mapping(file_permissions,folder_adb_data,outf,sources_good)
    
    print(f'\n---------------------------- {outf}')
    tbl = copy.deepcopy(tbl_violate)
    for ap in test_apis:
      tbl[1].append(len(set_violate_req[str(ap)][0]))
      tbl[1].append(len(set_violate_req[str(ap)][1]))
      tbl[2].append(len(set_violate_grn[str(ap)][0]))
      tbl[2].append(len(set_violate_grn[str(ap)][1]))
      print(ap)
      print(' REQUESTED')
      for p,c in set_violate_req[str(ap)][2].items():
        print(f'    {p} : {c}')
        s = dict_andro_maps[p]['seen_in_manifests']
        print(f'    seen in manifests: {s}')
      print(' GRANTED')
      for p,c in set_violate_grn[str(ap)][2].items():
        print(f'    {p} : {c}')
        s = dict_andro_maps[p]['seen_in_manifests']
        print(f'    seen in manifests: {s}')
    print(tabulate(tbl, tablefmt="github"))


#############################################################################################
#############################################################################################
#############################################################################################

def request_diff(folder_adb_data,sources):

  outs = [
    'out/output_10_phone_2',
    'out/output_11_phone_2',
    'out/output_12_phone_2',
    'out/output_13_phone_2',
    ]
  
  req_perm_counts = OrderedDict()

  for outf in outs:

    dict_adb_data_lines = OrderedDict()

    for source in sources:
      with io.open(f'{path_script}/{folder_adb_data}/{outf}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass

    for apk,meta in dict_adb_data_lines.items():
    
      if apk not in set_apps_working:
        continue

      cur_apis = set([meta['target_sdk']['meta'], meta['target_sdk']['install'], meta['target_sdk']['run']])
      cur_api = [x for x in cur_apis if x != None]
      if len(cur_api) == 1:
        cur_api = int(cur_api[0])
      else:
        if not meta['target_sdk']['meta']:
          binsets = meta['in_sets']
          bname = meta['package_name']
          print(f'NO META FOR {bname} - {apk}, in {binsets}')
          continue
        else:
          print(1)

      if cur_api not in test_apis:
        continue

      for p in meta['install']['requested permissions'].keys():

        if p not in dict_andro_maps.keys():
          continue
        if p not in req_perm_counts.keys():
          req_perm_counts[p] = OrderedDict()
          for of in outs:
            req_perm_counts[p][of] = 0
          req_perm_counts[p]['total'] = 0
        req_perm_counts[p][outf] += 1
        req_perm_counts[p]['total'] += 1
  
  outd = dict(sorted(req_perm_counts.items(), key=lambda item: item[1]['total'], reverse=True))

  tbl = []
  th = ['permission']
  ttot = ['total',]
  for outf in outs:
    th.append(outf)
    th.append('diff')
  th = th[:-1]
  th.append('total')
  tbl.append(th)
  dtot = OrderedDict()
  for of in outs:
    dtot[of] = 0
  dtot['total'] = 0

  for p,n in outd.items():
    tl = [p,]
    temp = None
    for k,v in n.items():
      if temp != None and k in outs:
        difv = v - temp
        if difv:
          tl.append(difv)
        else:
          tl.append('')
      tl.append(v)
      temp = copy.deepcopy(v)
      dtot[k] += v
    tbl.append(tl)

  ttot = ['TOTAL',]
  temp = None
  for k,v in dtot.items():
    if temp != None and k in outs:
      difv = v - temp
      if difv:
        ttot.append(difv)
      else:
        ttot.append('')
    ttot.append(v)
    temp = copy.deepcopy(v)
  tbl.append(ttot)

  print(tabulate(tbl, tablefmt="github"))


def perm_adb_counts(folder_adb_data,sources):

  outs = [
    'out/output_10_phone_2',
    'out/output_11_phone_2',
    'out/output_12_phone_2',
    'out/output_13_phone_2',
    ]
  
  req_perm_counts = OrderedDict()
  dtot = OrderedDict()
  for of in outs:
    dtot[of] = OrderedDict()
    for api in test_apis:
      dtot[of][str(api)] = OrderedDict()
      dtot[of][str(api)]['meta'] = 0
      dtot[of][str(api)]['req'] = OrderedDict({
        'total':0,
        'defined':0,
        'undefined':0,
      })
      dtot[of][str(api)]['grn'] = OrderedDict({
        'total':0,
        'defined':0,
        'undefined':0,
      })

  for outf in outs:

    dict_adb_data_lines = OrderedDict()

    for source in sources:
      with io.open(f'{path_script}/{folder_adb_data}/{outf}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass

    for apk,meta in dict_adb_data_lines.items():
    
      if apk not in set_apps_working:
        continue

      cur_apis = set([meta['target_sdk']['meta'], meta['target_sdk']['install'], meta['target_sdk']['run']])
      cur_api = [x for x in cur_apis if x != None]
      if len(cur_api) == 1:
        cur_api = int(cur_api[0])
      else:
        if not meta['target_sdk']['meta']:
          binsets = meta['in_sets']
          bname = meta['package_name']
          print(f'NO META FOR {bname} - {apk}, in {binsets}')
          continue
        else:
          print(1)

      if cur_api not in test_apis:
        continue
      if cur_api == 32:
        use_api = 31
      else: 
        use_api = cur_api
      
      for p in meta['meta']['used permissions']:

        if p not in dict_andro_maps.keys():
          continue
        dtot[outf][str(cur_api)]['meta'] += 1

      for p in meta['install']['requested permissions'].keys():

        # if "READ_MEDIA_AUDIO" in p and cur_api == 30:
        #   print(1)
        # if "BLUETOOTH_SCAN" in p and cur_api == 30:
        #   print(1)

        if p not in dict_andro_maps.keys():
          continue
        dtot[outf][str(cur_api)]['req']['total'] += 1
        try:
          tt = dict_andro_maps[p]['versions'][str(use_api)]
          dtot[outf][str(cur_api)]['req']['defined'] += 1
        except KeyError:
          dtot[outf][str(cur_api)]['req']['undefined'] += 1
      
      for p in meta['install']['install permissions'].keys():

        if p not in dict_andro_maps.keys():
          continue
        dtot[outf][str(cur_api)]['grn']['total'] += 1
        try:
          tt = dict_andro_maps[p]['versions'][str(use_api)]
          dtot[outf][str(cur_api)]['grn']['defined'] += 1
        except KeyError:
          dtot[outf][str(cur_api)]['grn']['undefined'] += 1

  print(dict(dtot))


def meta_to_adb(folder_adb_data,folder_name,sources):

  folder_data = f'{folder_adb_data}/{folder_name}'
      
  dict_adb_data_lines = OrderedDict()

  for source in sources:
      with io.open(f'{path_script}/{folder_data}/{source}_adb_permissions.json', 'r') as rif:
        for line in rif:
          xline = line.replace("\n", "").strip()
          if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
              if not k in dict_adb_data_lines:
                dict_adb_data_lines[k] = v
      try:
        del k,v,line,xline,jdata
      except UnboundLocalError:
        pass
    
  metadiff_stats = OrderedDict({
    'apk_total': 0,
    'apk_nometa': 0,
    'apk_nodiff': 0,
    'apk_diff': 0,
    'apk_uq_meta': 0,
    'apk_uq_install': 0,
    'apk_uq_both': 0,
    'instance_meta': 0,
    'instance_install': 0,
    'instance_meta_in_wmax': 0,
    'instance_meta_in_sdk23': 0,
    'instance_install_in_wmax': 0,
    'instance_install_in_sdk23': 0,
    'perms_meta': OrderedDict(),
    'perms_install': OrderedDict(),
  })

  key_to_desc = OrderedDict({
    'apk_total': 'apks total',
    'apk_nometa': 'APKS WITHOUT META',
    'apk_nodiff': 'apks without difference',
    'apk_diff': 'apks with difference',
    'apk_uq_meta': 'apks with unique permissions requested in manifest',
    'apk_uq_install': 'apks with unique permissions requested in adb dump',
    'apk_uq_both': 'apks with unique permissions requested in manifest and adb dump',
    'instance_meta': 'permission instances in manifest',
    'instance_install': 'permission instances in adb dump',
    'instance_meta_in_wmax': '--- permission not in adb dump because of maxSdkVersion limit in manifest',
    'instance_meta_in_sdk23': '--- permission not in adb dump and uses-sdk23 limit in manifest',
    'instance_install_in_wmax': 'in adb dump and maxSdkVersion limit in manifest',
    'instance_install_in_sdk23': 'in adb dump and uses-sdk23 limit in manifest',
    'perms_meta': 'permissions in manifest only',
    'perms_install': 'permissions in adb dump only',
  })

  print()
  for apk,meta in dict_adb_data_lines.items():
    
    if apk not in set_apps_working:
      continue

    cur_apis = set([meta['target_sdk']['meta'], meta['target_sdk']['install'], meta['target_sdk']['run']])
    cur_api = [x for x in cur_apis if x != None]
    if len(cur_api) == 1:
      cur_api = int(cur_api[0])
    else:
      if not meta['target_sdk']['meta']:
        binsets = meta['in_sets']
        bname = meta['package_name']
        print(f'NO META FOR {bname} - {apk}, in {binsets}')
        metadiff_stats['apk_nometa'] += 1
        continue
      else:
        print(1)

    if cur_api in test_apis:
      if cur_api == 32:
        use_api = 31
      else: 
        use_api = cur_api
      
      metadiff_stats['apk_total'] += 1

      for p in meta['install']['requested permissions']:
        if p in meta['meta']['used_wmax permissions']:
          metadiff_stats['instance_install_in_wmax'] += 1
        if p in meta['meta']['sdk23 permissions']:
          metadiff_stats['instance_install_in_sdk23'] += 1
      
      if not meta['has_diff_meta']:
        metadiff_stats['apk_nodiff'] += 1
        continue
      
      hasdiff_meta = False
      if meta['diff_meta']['unique_meta']:
        
        for p in meta['diff_meta']['unique_meta']:
          if p in meta['meta']['used_wmax permissions']:
            metadiff_stats['instance_meta_in_wmax'] += 1
            continue
          if p in meta['meta']['sdk23 permissions']:
            metadiff_stats['instance_meta_in_sdk23'] += 1
            continue
          hasdiff_meta = True
          metadiff_stats['instance_meta'] += 1
          if p not in metadiff_stats['perms_meta'].keys():
            metadiff_stats['perms_meta'][p] = 1
          else:
            metadiff_stats['perms_meta'][p] += 1
        if hasdiff_meta:
          metadiff_stats['apk_uq_meta'] += 1

      hasdiff_install = False
      if meta['diff_meta']['unique_install']:
        
        for p in meta['diff_meta']['unique_install']:
          if 'READ_MEDIA_AUDIO' in p:
            if 'android.permission.READ_EXTERNAL_STORAGE' not in meta['install']['requested permissions']:# \
            # and 'android.permission.BLUETOOTH_ADMIN' not in meta['install']['requested permissions']:
              print(1)
          if p in meta['meta']['used_wmax permissions']:
            metadiff_stats['instance_install_in_wmax'] += 1
            continue
          if p in meta['meta']['sdk23 permissions']:
            metadiff_stats['instance_install_in_sdk23'] += 1
            continue
          hasdiff_install = True
          metadiff_stats['instance_install'] += 1
          if p not in metadiff_stats['perms_install'].keys():
            metadiff_stats['perms_install'][p] = 1
          else:
            metadiff_stats['perms_install'][p] += 1
        if hasdiff_install:
          metadiff_stats['apk_uq_install'] += 1
      
      if hasdiff_meta or hasdiff_install:
        metadiff_stats['apk_diff'] += 1
      
      if hasdiff_meta and hasdiff_install:
        metadiff_stats['apk_uq_both'] += 1
      
      if not hasdiff_meta and not hasdiff_install:
        metadiff_stats['apk_nodiff'] += 1
          
  print()
  print(folder_name)
  for k,v in metadiff_stats.items():
    kdesc = key_to_desc[k]
    if type(v) == int:
      print(f'  {kdesc} - {v}')
    else:
      print(f'  {kdesc}')
      for kk,vv in v.items():
        print(f'    {kk} : {vv}')






if __name__ == '__main__':
  print()

  perms_a = """android.permission.ACCESS_WIMAX_STATE
android.permission.AUTHENTICATE_ACCOUNTS
android.permission.BACKUP
android.permission.CHANGE_COMPONENT_ENABLED_STATE
android.permission.CHANGE_WIMAX_STATE
android.permission.CONNECTIVITY_INTERNAL
android.permission.FLASHLIGHT
android.permission.GRANT_RUNTIME_PERMISSIONS
android.permission.INSTALL_PACKAGES
android.permission.INTERACT_ACROSS_USERS
android.permission.LOCAL_MAC_ADDRESS
android.permission.MANAGE_ACCOUNTS
android.permission.MANAGE_APP_OPS_MODES
android.permission.MANAGE_NETWORK_POLICY
android.permission.MANAGE_USB
android.permission.OVERRIDE_WIFI_CONFIG
android.permission.PEERS_MAC_ADDRESS
android.permission.READ_INSTALL_SESSIONS
android.permission.READ_LOGS
android.permission.READ_PROFILE
android.permission.READ_SOCIAL_STREAM
android.permission.READ_USER_DICTIONARY
android.permission.REBOOT
android.permission.REVOKE_RUNTIME_PERMISSIONS
android.permission.START_ACTIVITIES_FROM_BACKGROUND
android.permission.SUBSCRIBED_FEEDS_READ
android.permission.SUBSCRIBED_FEEDS_WRITE
android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME
android.permission.TETHER_PRIVILEGED
android.permission.UPDATE_APP_OPS_STATS
android.permission.USE_CREDENTIALS
android.permission.WRITE_MEDIA_STORAGE
android.permission.WRITE_PROFILE
android.permission.WRITE_SECURE_SETTINGS
android.permission.WRITE_SMS
android.permission.WRITE_SOCIAL_STREAM
android.permission.WRITE_USER_DICTIONARY
com.android.browser.permission.READ_HISTORY_BOOKMARKS
com.android.browser.permission.WRITE_HISTORY_BOOKMARKS"""
  perms_b = """android.permission.ACCESS_CACHE_FILESYSTEM
android.permission.ACCESS_INSTANT_APPS
android.permission.ACCESS_MOCK_LOCATION
android.permission.ACCESS_WIMAX_STATE
android.permission.ALLOW_ANY_CODEC_FOR_PLAYBACK
android.permission.AUTHENTICATE_ACCOUNTS
android.permission.BACKUP
android.permission.BIND_DIRECTORY_SEARCH
android.permission.BIND_JOB_SERVICE
android.permission.CAPTURE_VIDEO_OUTPUT
android.permission.CHANGE_WIMAX_STATE
android.permission.CLEAR_APP_USER_DATA
android.permission.CONNECTIVITY_INTERNAL
android.permission.DEVICE_POWER
android.permission.FLASHLIGHT
android.permission.FORCE_STOP_PACKAGES
android.permission.GET_INTENT_SENDER_INTENT
android.permission.GET_RUNTIME_PERMISSIONS
android.permission.GRANT_RUNTIME_PERMISSIONS
android.permission.INTERACT_ACROSS_USERS
android.permission.INTERACT_ACROSS_USERS_FULL
android.permission.INTERNAL_SYSTEM_WINDOW
android.permission.LOCAL_MAC_ADDRESS
android.permission.MANAGE_ACCOUNTS
android.permission.MANAGE_APP_OPS_MODES
android.permission.MANAGE_NETWORK_POLICY
android.permission.MANAGE_USB
android.permission.MANAGE_USERS
android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS
android.permission.MOVE_PACKAGE
android.permission.NETWORK_STACK
android.permission.OVERRIDE_WIFI_CONFIG
android.permission.PEERS_MAC_ADDRESS
android.permission.READ_CELL_BROADCASTS
android.permission.READ_DEVICE_CONFIG
android.permission.READ_INSTALL_SESSIONS
android.permission.READ_PRIVILEGED_PHONE_STATE
android.permission.READ_PROFILE
android.permission.READ_SOCIAL_STREAM
android.permission.READ_USER_DICTIONARY
android.permission.REAL_GET_TASKS
android.permission.REVOKE_RUNTIME_PERMISSIONS
android.permission.SET_VOLUME_KEY_LONG_PRESS_LISTENER
android.permission.START_ACTIVITIES_FROM_BACKGROUND
android.permission.STATUS_BAR_SERVICE
android.permission.SUBSCRIBED_FEEDS_READ
android.permission.SUBSCRIBED_FEEDS_WRITE
android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME
android.permission.TETHER_PRIVILEGED
android.permission.UPDATE_APP_OPS_STATS
android.permission.USE_CREDENTIALS
android.permission.WHITELIST_AUTO_REVOKE_PERMISSIONS
android.permission.WRITE_MEDIA_STORAGE
android.permission.WRITE_PROFILE
android.permission.WRITE_SMS
android.permission.WRITE_SOCIAL_STREAM
android.permission.WRITE_USER_DICTIONARY
com.android.browser.permission.READ_HISTORY_BOOKMARKS
com.android.browser.permission.WRITE_HISTORY_BOOKMARKS"""

  # apks_same(file_apks)
  # dict_apk_api = ''
  # dict_apk_api = get_apk_meta(file_apks)
  # get_perms_in_files(file_lists,file_permissions)
  # table_list_categories_by_api(file_lists,file_permissions)
  # table_category_change_by_api(file_lists,file_permissions)
  data_28,data_29,data_30,data_31,data_33 = get_rput_by_api(file_lists,file_permissions)
  # table_comb_of_rput_by_api(data_29,data_30,data_31,data_33,a=True,r=True,p=True,s=False,u=False,t=False)
  # table_blacklist_change_by_api(file_lists,file_permissions)
  # table_granted_by_rp(file_permissions,folder_adb_data,'out/pixel_29_emulator',10,data_29,sources_all)
  # table_granted_by_rp(file_permissions,folder_adb_data,'out/pixel_31_emulator',12,data_31,sources_all)
  # table_apk_in_datasets(file_apks)
  # table_perm_analysis_sources(file_permissions,folder_adb_data,sources_good,9,data_28,data_29,data_30,data_31,data_33)
  # table_perm_analysis_sources(file_permissions,folder_adb_data,sources_bad,9,data_28,data_29,data_30,data_31,data_33)
  # table_perm_analysis_sources(file_permissions,folder_adb_data,sources_good,12,data_28,data_29,data_30,data_31,data_33)
  # table_granted_by_tp(file_permissions,folder_adb_data,9,data_28)
  # table_granted_by_tp(file_permissions,folder_adb_data,12,data_31)

  # table_restr_list_combs_by_api(file_lists,file_permissions)
  # table_restr_lists_by_api(file_lists,file_permissions)
  # table_comb_of_rput_by_api(data_28,data_29,data_30,data_31,data_33,a=True,r=True,p=True,s=True,u=True,t=True)
  # table_perms_by_rp(data_28,data_29,data_30,data_31,data_33)
  # table_api_in_datasets(file_apks)
  # table_api_all_in_datasets(file_apks,'api_level_to_use')
  # print_combinations(file_permissions,folder_adb_data,'out/pixel_31_emulator',12,sources_all)
  # print_combinations_in_apks(file_permissions,folder_adb_data,'out/pixel_29_emulator',10,sources_good)
  # print()
  # print_combinations_in_apks(file_permissions,folder_adb_data,'out/pixel_31_emulator',12,sources_good)
  # print()
  # print_combinations_in_apks(file_permissions,folder_adb_data,'out/adb_phone_12',12,sources_good)
  # print()
  # print_bad_combinations_in_apks(file_permissions,folder_adb_data,'out/12_phone',12,sources_good)
  # attrs = ('tag'  'restriction' 'protection' 'status' 'usage' 'type')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/pixel_29_emulator',10,data_29,sources_good,'restriction','protection')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/pixel_31_emulator',12,data_31,sources_good,'restriction','protection')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/adb_phone_10',12,data_31,sources_good,'restriction','protection')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/adb_phone_12',12,data_31,sources_good,'restriction','protection')
  # print()
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/pixel_29_emulator',10,data_29,sources_good,'restriction','usage')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/pixel_31_emulator',12,data_31,sources_good,'restriction','usage')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/adb_phone_10',12,data_31,sources_good,'restriction','usage')
  # table_granted_by_attr_attr(file_permissions,folder_adb_data,'out/adb_phone_12',12,data_31,sources_good,'restriction','usage')
  # table_select_mapping_perms(file_lists,file_permissions)
  # table_count_combs_mapping(file_lists,file_permissions)
  # table_count_combs_mapping_new(file_lists,file_permissions)
  # get_all_perms(file_permissions)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_10_phone_2',sources_good)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_11_phone_2',sources_good)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_12_phone_2',sources_good)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_13_phone_2',sources_good)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_11_dummy_2',sources_dummy)
  # count_req_granted_by_text_combs(file_permissions,folder_adb_data,'out/output_13_dummy_2',sources_dummy)
  # count_req_granted_by_depr(dict_apk_api,file_permissions,folder_adb_data,'out/12_phone',12,sources_good)
  # perms_list_tot = []
  # perms_list,_,_ = bad_combinations_in_apks(file_permissions,folder_adb_data,'out/output_10_phone_2',sources_good,show_combs=False)
  # perms_list_tot += perms_list
  # perms_list,_,_ = bad_combinations_in_apks(file_permissions,folder_adb_data,'out/output_11_phone_2',sources_good,show_combs=False)
  # # print(perms_list)
  # perms_list_tot += perms_list
  # perms_list,_,_ = bad_combinations_in_apks(file_permissions,folder_adb_data,'out/output_12_phone_2',sources_good,show_combs=False)
  # # print(perms_list)
  # perms_list_tot += perms_list
  # perms_list,_,_ = bad_combinations_in_apks(file_permissions,folder_adb_data,'out/output_13_phone_2',sources_good,show_combs=False)
  # perms_list_tot += perms_list
  # perms_list_tot = sorted(list(set(perms_list_tot)))
  # for p in perms_list_tot:
  #   print(p)
  # d0 = count_apk_perms(file_permissions,folder_adb_data,'out/output_10_phone_2',sources_good,perms_b)
  # d1 = count_apk_perms(file_permissions,folder_adb_data,'out/output_11_phone_2',sources_good,perms_b)
  # # # combine_apks([d0,d1])
  # d2 = count_apk_perms(file_permissions,folder_adb_data,'out/output_12_phone_2',sources_good,perms_b)
  # d3 = count_apk_perms(file_permissions,folder_adb_data,'out/output_13_phone_2',sources_good,perms_b)
  # # # combine_apks([d2,d3])
  # # # combine_apks([d0,d1,d2,d3])
  # combine_apks([d0])
  # # print()
  # combine_apks([d1])
  # # print()
  # combine_apks([d2])
  # # print()
  # combine_apks([d3])
  # combine_apks_apis([d0,d1,d2,d3],['out/output_10_phone_2','out/output_11_phone_2','out/output_12_phone_2','out/output_13_phone_2',],sources_good)
  # print()
  # get_perms_conflicts(file_permissions)
  # apk_violating(file_permissions,folder_adb_data)
  # apk_violating_general(file_permissions,folder_adb_data)
  # apk_violating_mapping(file_permissions,folder_adb_data)
  # meta_to_adb(folder_adb_data,'out/output_10_phone_2',sources_good)
  # meta_to_adb(folder_adb_data,'out/output_11_phone_2',sources_good)
  # meta_to_adb(folder_adb_data,'out/output_12_phone_2',sources_good)
  # meta_to_adb(folder_adb_data,'out/output_13_phone_2',sources_good)
  # request_diff(folder_adb_data,sources_good)
  perm_adb_counts(folder_adb_data,sources_good)


  


