import io
import os
import sys
from collections import OrderedDict
import json


# ########################################################################


def get_file_content(path_data):
  err = None
  if not os.path.isfile(path_data):
    print("PATH -> ", path_data)
    raise AssertionError("ERROR: unsupported source, has to be a FILE")

  content = list()
  with io.open(path_data, 'r') as rif:
    data = rif.read()
    try:
      data = data.split('Packages:\n')[1].split('Package Changes:')[0]
    except IndexError:
      if not data:
        install_or_run = path_data.split('.')[1].split('_')[1]
        err = f'EMPTY FILE {install_or_run}'
      else:
        err = data
    for line in data.split('\n'):
      xline = line.replace("\n", "")
      if xline:
        content.append(xline)
  return content,err


def get_package_content(path_data,apk_packagename,dict_alt_names):
  err = None
  new_name = None
  if not os.path.isfile(path_data):
    print("PATH -> ", path_data)
    raise AssertionError("ERROR: unsupported source, has to be a FILE")

  data = None
  content = list()
  with io.open(path_data, 'r') as rif:
    try:
      sections = rif.read().split('\n\n')
    except IndexError:
      if not sections:
        install_or_run = path_data.split('.')[1].split('_')[1]
        err = f'EMPTY FILE {install_or_run}'
      else:
        err = sections
    for section in sections:
      if f'Package [{apk_packagename}]' in section:
        parts = section.split('Package [')
        for part in parts:
          if f'{apk_packagename}]' in part:
            data = part.split('\n')
    if not data and apk_packagename in dict_alt_names.keys():
      for altname in dict_alt_names[apk_packagename]:
        for section in sections:
          if f'Package [{altname}]' in section:
            parts = section.split('Package [')
            for part in parts:
              if f'{altname}]' in part:
                data = part.split('\n')
                print(f'changed package name from <{apk_packagename}> to <{altname}>')
                new_name = str(altname)
    if data:
      for line in data:
        xline = line.replace("\n", "")
        if xline:
          content.append(xline)
  return content,err,new_name


# ########################################################################

indentation_length = 2

path_script = os.path.abspath(os.path.dirname(__file__))
file_apks = 'data/sets_all_meta_all_valid.json'
file_lists = 'data/data_lists.json'
file_permissions = 'data/data_permissions.json'
folder_adb_data = 'data/adb_parsed'
folder_input_ok = 'data/adb_parsed/ok'

folder_input = 'data/adb_parsed/raw'
folder_output = 'data/adb_parsed/out'

sources_good = [
  'androgalaxy_2019',
  'androidapkfree_2020',
  'apkgod_2020',
  'apkmaza_2020',
  'apkpure_2021',
  'appsapk_com_2020',
  'crackhash_2022',
  'crackshash_2021',
  'fdroid_2020',
  ]

misc = [
  ''
  ]

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


# ########################################################################

def parse_by_sources(folder_logs,sources):

  print(f'FOLDER: {folder_logs}')

  list_bad_apps = []
  try:
    with io.open(f'{path_script}/{folder_input}/{folder_logs}/temp/bad_apps.txt') as b:
      bad_apps = b.readlines()
      for bap in bad_apps:
        list_bad_apps.append(bap.split('/')[-1].split('.')[0])
    del b,bad_apps,bap
  except FileNotFoundError:
    pass


  skip_lines = [
    'uses-implied-feature',
    'launchable-activity'
    ]
  dict_apksha1_meta = OrderedDict()
  try:
    for source in sources_good:
      input_path = f'{path_script}/{folder_input}/output_apk_meta/{source}_apks'
      for filename in os.listdir(input_path):
        path_file = f'{input_path}/{filename}'
        apk_sha1 = filename.split('.')[0]
        if apk_sha1 in dict_apksha1_meta.keys():
          raise Exception
        dict_apksha1_meta[apk_sha1] = OrderedDict({
          'name': None,
          'compilesdk': None,
          'targetsdk': None,
          'used permissions': [],
          'used_wmax permissions': [],
          'optional permissions': [],
          'sdk23 permissions': [],
        })
        content,err = get_file_content(path_file)
        for line in content:
          # "package: name='com.adguard.android' versionCode='10000050' versionName='3.3.50' platformBuildVersionName='10' platformBuildVersionCode='29' compileSdkVersion='23' compileSdkVersionCodename='6.0-2438415'"
          if 'package: name=' in line:
            apk_packagename = line.split(' ')[1].split("'")[1]
            try:
              apk_compilesdk = line.split('compileSdkVersion=')[1].split("'")[1]
            except IndexError:
              apk_compilesdk = None
          elif 'targetSdkVersion:' in line:
            apk_targetsdk = line.split("'")[1]
          elif 'uses-permission: name=' in line:
            apk_perm = line.split("'")[1].strip()
            dict_apksha1_meta[apk_sha1]['used permissions'].append(apk_perm)
            if 'maxSdkVersion' in line:
              maxsdk = line.split('maxSdkVersion')[1].split("'")[1]
              if int(maxsdk) < 29:
                dict_apksha1_meta[apk_sha1]['used_wmax permissions'].append(apk_perm)
          elif 'optional-permission: name=' in line:
            apk_perm = line.split("'")[1].strip()
            dict_apksha1_meta[apk_sha1]['optional permissions'].append(apk_perm)
          elif 'uses-implied-permission' in line:
            apk_perm = line.split("'")[1].strip()
            dict_apksha1_meta[apk_sha1]['used permissions'].append(apk_perm)
          elif 'uses-permission-sdk-23' in line:
            apk_perm = line.split("'")[1].strip()
            dict_apksha1_meta[apk_sha1]['used permissions'].append(apk_perm)
            dict_apksha1_meta[apk_sha1]['sdk23 permissions'].append(apk_perm)
          elif 'uses-feature-not-required: name=' in line and 'permission' in line:
            apk_perm = line.split("'")[1].strip()
            dict_apksha1_meta[apk_sha1]['optional permissions'].append(apk_perm)
          elif 'permission' in line and True not in [line.strip().startswith(x) for x in skip_lines]:
            print(1)
        
        dict_apksha1_meta[apk_sha1]['name'] = apk_packagename
        dict_apksha1_meta[apk_sha1]['compilesdk'] = apk_compilesdk
        dict_apksha1_meta[apk_sha1]['targetsdk'] = apk_targetsdk

  except FileNotFoundError:
      pass


  dict_apksha1_packagename = OrderedDict()
  dict_alt_names = OrderedDict()
  for item in os.listdir(f'{path_script}/{folder_input}/{folder_logs}'):
    if 'log' in item and os.path.isfile(f'{path_script}/{folder_input}/{folder_logs}/{item}'):
      with io.open(f'{path_script}/{folder_input}/{folder_logs}/{item}') as b:
        data_apks = b.read().split('#########################################################')
        for data_apk in data_apks:
          lines = data_apk.split('\n')
          apk_sha1 = None
          apk_packagename = None
          add = True
          for line in lines:
            if 'APK FILE:' in line:
              apk_sha1 = line.split('/')[-1].split('.')[0]
            if 'PACKAGE NAME:' in line:
              names = line.split(' ')[3:]
              if len(names) > 1:
                add = False
                for name in names:
                  if name in dict_apksha1_packagename.values():
                    names.remove(name)
                if len(names) > 1:
                  print(f'    more than one new package:\n    {line}')
                  # print('   assuming the first one')
                  dict_alt_names[names[0]] = names[1:]
                  # raise Exception
                  list_bad_apps.append(apk_sha1)
                else:
                  add = True
              if add:
                apk_packagename = names[0]
          if apk_sha1 and apk_packagename:
            dict_apksha1_packagename[apk_sha1] = apk_packagename
          # else:
          #   print(1)
      del b

  del item,data_apks,data_apk,lines,line,apk_packagename,apk_sha1,names


  count_nop = 0
  count_p = 0
  for source in sources:
    print(f'  Parsing output for --- {source} ...')

    out_data = OrderedDict()

    input_path = f'{path_script}/{folder_input}/{folder_logs}/{source}_apks'
    for filename in os.listdir(input_path):
    
      path_file = f'{input_path}/{filename}'
      apk_sha1 = filename.split('.')[0]
      install_or_run = filename.split('.')[1].replace('apk_','')

      if apk_sha1 in list_bad_apps:
        continue
    
      if apk_sha1 in dict_apksha1_meta.keys():
        apk_packagename = dict_apksha1_meta[apk_sha1]['name']
        content,err,new_name = get_package_content(path_file,apk_packagename,dict_alt_names)
        if new_name:
          print(1)
        count_p += 1
      elif apk_sha1 in dict_apksha1_packagename.keys():
        apk_packagename = dict_apksha1_packagename[apk_sha1]
        content,err,new_name = get_package_content(path_file,apk_packagename,dict_alt_names)
        if new_name:
          apk_packagename = new_name
        count_p += 1
      else:
        apk_packagename = None
        content,err = get_file_content(path_file)
        count_nop += 1

      joined_content = ' '.join(content)
      if joined_content.count('Package [') > 1: # and apk_sha1 not in list_bad_apps:
        print(f'  More than one package in file {filename}')
        continue
      
      if err != None:
        if apk_sha1 not in out_data.keys():
          perm_data = OrderedDict()
          perm_data["apk_sha1"] = apk_sha1
          perm_data["in_sets"] = source
          perm_data["package_name"] = apk_packagename
          perm_data["target_sdk"] = OrderedDict({'meta': '','install': '','run': ''})
          perm_data['err_bool'] = True
          perm_data['err_type'] = ['OTHER',]
          perm_data['err_reason'] = [err,]
          perm_data['meta'] = OrderedDict()
          perm_data['install'] = OrderedDict()
          perm_data['run'] = OrderedDict()
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()
          
          if apk_sha1 in dict_apksha1_meta.keys():
            perm_data["target_sdk"]['meta'] = dict_apksha1_meta[apk_sha1]['targetsdk']
            perm_data["meta"] = dict_apksha1_meta[apk_sha1]
          else:
            perm_data["meta"] = OrderedDict({
              'name': None,
              'compilesdk': None,
              'targetsdk': None,
              'used permissions': [],
              'used_wmax permissions': [],
              'optional permissions': [],
              'sdk23 permissions': [],
            })

          out_data[perm_data['apk_sha1']] = perm_data

        else:
          perm_data = out_data[apk_sha1]
          perm_data['err_bool'] = True
          perm_data['err_type'].append('OTHER')
          perm_data['err_reason'].append(err)
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data
      
      else:
        if apk_sha1 not in out_data.keys():
          perm_data = OrderedDict()
          perm_data["apk_sha1"] = apk_sha1
          perm_data["in_sets"] = source
          perm_data["package_name"] = apk_packagename
          perm_data["target_sdk"] = OrderedDict({'meta': '','install': '','run': ''})
          perm_data['err_bool'] = False
          perm_data['err_type'] = []
          perm_data['err_reason'] = []
          perm_data['meta'] = OrderedDict()
          perm_data['install'] = OrderedDict()
          perm_data['run'] = OrderedDict()
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          if apk_sha1 in dict_apksha1_meta.keys():
            perm_data["target_sdk"]['meta'] = dict_apksha1_meta[apk_sha1]['targetsdk']
            perm_data["meta"] = dict_apksha1_meta[apk_sha1]
          else:
            perm_data["meta"] = OrderedDict({
              'name': None,
              'compilesdk': None,
              'targetsdk': None,
              'used permissions': [],
              'used_wmax permissions': [],
              'optional permissions': [],
              'sdk23 permissions': [],
            })

          out_data[perm_data['apk_sha1']] = perm_data

        else:
          perm_data = out_data[apk_sha1]
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data

        p_inserting = False
        p_child_indentation = None
        p_perm_type = None

        for xline in content:

          xtline = xline.strip()
          if not xtline:
            continue

          if 'targetSdk=' in xline:
            attrs = xline.split(' ')
            for attr in attrs:
              if 'targetSdk=' in attr:
                attr = attr.replace('\n','').replace('targetSdk=','')
                if attr == '':
                  print(1)
                perm_data["target_sdk"][install_or_run] = attr

          indentation = float(len(xline) - len(xline.lstrip())) / indentation_length
          if indentation % 1 != 0:
            problem = True
            try:
              ind_diff = indentation - p_child_indentation
              if indentation > p_child_indentation and p_inserting:
                if ind_diff < 1:
                  indentation = p_child_indentation
                  problem = False
            except:
              continue
            if problem:
              print(apk_sha1)
              print(xline)
              raise Exception
          
          if p_child_indentation:
            if indentation < p_child_indentation:
              p_inserting = False
              p_child_indentation = None
              p_perm_type = None

          if p_inserting and p_child_indentation == indentation:
            this_perm = OrderedDict()
            yline = xline.strip().split(':')
            this_perm['name'] = yline[0].strip()
            if not yline[0]:
              print(1)
            if len(yline) > 1:
              this_perm['params_bool'] = True
              params = yline[1].strip().split(', ')
              this_perm['params'] = params
            else:
              this_perm['params_bool'] = False
            perm_data[install_or_run][p_perm_type][yline[0]] = this_perm

          if xline.endswith('permissions:') and p_inserting == False:
            p_inserting = True
            p_child_indentation = indentation + 1
            p_perm_type = xline.strip()[:-1]
            perm_data[install_or_run][p_perm_type] = OrderedDict()
        
        if not perm_data["target_sdk"][install_or_run]:
          perm_data["target_sdk"][install_or_run] = None
        out_data[perm_data['apk_sha1']] = perm_data

    path_file = f'{path_script}/{folder_input}/{folder_logs}/failed.txt'
    with io.open(path_file, 'r') as f:
      data = f.readlines()
      for i in range(len(data)):
        if data[i].startswith('['):
          err_types,path = data[i][1:].split('] ')
          err_types = err_types.split('||')
          if source not in path:
            continue
          else:
            err_line = ''
            err_reasons = ''
            index = i
            while '--------------------------------------------------' not in err_line:
              err_reasons += err_line
              err_line = data[index+1].replace('\n',' ')
              index += 1
            err_reasons = err_reasons.split('\n******************\n')
            err_reasons[-1] = err_reasons[-1].replace('\\n******************','')

            filename = path.split('/')[-1]
            apk_sha1 = filename.split('.')[0]

            if apk_sha1 not in out_data.keys():
              perm_data = OrderedDict()
              perm_data["apk_sha1"] = apk_sha1
              perm_data["in_sets"] = source
              perm_data["package_name"] = apk_packagename
              perm_data["target_sdk"] = OrderedDict({'install': '', 'run': ''})
              perm_data['err_bool'] = True
              perm_data['err_type'] = err_types
              perm_data['err_reason'] = err_reasons
              perm_data['meta'] = OrderedDict()
              perm_data['install'] = OrderedDict()
              perm_data['run'] = OrderedDict()

              if apk_sha1 in dict_apksha1_meta.keys():
                perm_data["target_sdk"]['meta'] = dict_apksha1_meta[apk_sha1]['targetsdk']
                perm_data["meta"] = dict_apksha1_meta[apk_sha1]
              else:
                perm_data["meta"] = OrderedDict({
                  'name': None,
                  'compilesdk': None,
                  'targetsdk': None,
                  'used permissions': [],
                  'used_wmax permissions': [],
                  'optional permissions': [],
                  'sdk23 permissions': [],
                })

              out_data[perm_data['apk_sha1']] = perm_data
            
            else:
              perm_data = out_data[apk_sha1]
              perm_data['err_bool'] = True
              perm_data['err_type'] += err_types
              perm_data['err_reason'] += err_reasons

              out_data[perm_data['apk_sha1']] = perm_data
    
    for apk_sha1, perm_data in out_data.items():
      perm_data["has_diff"] = False
      perm_data["diff"] = OrderedDict({'unique_install': OrderedDict(), 'unique_run': OrderedDict()})
      for key in perm_data["diff"].keys():
        perm_data["diff"][key]['declared permissions'] = OrderedDict()
        perm_data["diff"][key]['requested permissions'] = OrderedDict()
        perm_data["diff"][key]['install permissions'] = OrderedDict()
        perm_data["diff"][key]['runtime permissions'] = OrderedDict()
      perm_data["has_diff_meta"] = False
      perm_data["diff_meta"] = OrderedDict({'unique_meta': [], 'unique_install': [], 'sdk23_install': []})
      
      apk_ok = True
      if not perm_data['install'] or not perm_data['run']:
        apk_ok = False
      # else:
      #   if not perm_data['install']['declared permissions'] and not perm_data['install']['requested permissions'] \
      #     and not perm_data['install']['install permissions'] and not perm_data['install']['runtime permissions']:
      #     apk_ok = False
      #   if not perm_data['run']['declared permissions'] and not perm_data['run']['requested permissions'] \
      #     and not perm_data['run']['install permissions'] and not perm_data['run']['runtime permissions']:
      #     apk_ok = False
      
      if apk_ok:
        xperms = perm_data['meta']['used permissions']
        for xperm in xperms:
          if not xperm:
            print(1)
          if xperm not in dict_andro_maps.keys():
            continue
          if xperm not in perm_data['install']['requested permissions'].keys():
            perm_data["has_diff_meta"] = True
            perm_data["diff_meta"]['unique_meta'].append(xperm)
        for xperm in perm_data['install']['requested permissions'].keys():
          if not xperm:
            print(1)
          if xperm not in dict_andro_maps.keys():
            continue
          if xperm not in xperms:
            if xperm in perm_data['meta']['optional permissions']:
              print(1)
            if xperm in perm_data['meta']['sdk23 permissions']:
              perm_data["diff_meta"]['sdk23_install'].append(xperm)
              continue
            perm_data["has_diff_meta"] = True
            perm_data["diff_meta"]['unique_install'].append(xperm)
        
        for xtype,xperms in perm_data['install'].items():
          for xperm,xpermargs in xperms.items():
            if xperm not in perm_data['run'][xtype].keys() or perm_data['run'][xtype][xperm] != perm_data['install'][xtype][xperm]:
              perm_data["has_diff"] = True
              if xperm not in perm_data['run'][xtype].keys():
                reason = 'diff_perm'
              else:
                reason = 'diff_params'
              perm_data["diff"]['unique_install'][xtype][xperm] = OrderedDict({'reason':reason, 'data':xpermargs})
        
        for xtype,xperms in perm_data['run'].items():
          for xperm,xpermargs in xperms.items():
            if xperm not in perm_data['install'][xtype].keys() or perm_data['run'][xtype][xperm] != perm_data['install'][xtype][xperm]:
              perm_data["has_diff"] = True
              if xperm not in perm_data['install'][xtype].keys():
                reason = 'diff_perm'
              else:
                reason = 'diff_params'
              perm_data["diff"]['unique_run'][xtype][xperm] = OrderedDict({'reason':reason, 'data':xpermargs})

      

    print(f'    Line count: {len(out_data.keys())}')
    out_dir = f'{path_script}/{folder_output}/{folder_logs}'
    if not os.path.exists(out_dir): os.mkdir(out_dir)
    with io.open(f'{out_dir}/{source}_adb_permissions.json', 'w') as fp:
      for xh, xm in out_data.items():
        temp_jdict = {xh: xm}
        jline = json.dumps(temp_jdict)
        fp.write(jline + "\n")

  print(f'  apks with retrieved package names: {count_p}')
  print(f'  apks without package names: {count_nop}')


def parse_one(folder_logs,folder_name,out_name):

  list_bad_apps = []
  dict_apksha1_packagename = OrderedDict()
  dict_alt_names = OrderedDict()
  for item in os.listdir(f'{path_script}/{folder_input}/{folder_logs}'):
    if 'log' in item and os.path.isfile(f'{path_script}/{folder_input}/{folder_logs}/{item}'):
      with io.open(f'{path_script}/{folder_input}/{folder_logs}/{item}') as b:
        data_apks = b.read().split('#########################################################')
        for data_apk in data_apks:
          lines = data_apk.split('\n')
          apk_sha1 = None
          apk_packagename = None
          add = True
          for line in lines:
            if 'APK FILE:' in line:
              apk_sha1 = line.split('/')[-1].split('.')[0]
            if 'PACKAGE NAME:' in line:
              names = line.split(' ')[3:]
              if len(names) > 1:
                add = False
                for name in names:
                  if name in dict_apksha1_packagename.values():
                    names.remove(name)
                if len(names) > 1:
                  print(f'    more than one new package:\n    {line}')
                  # print('   assuming the first one')
                  dict_alt_names[names[0]] = names[1:]
                  # raise Exception
                  list_bad_apps.append(apk_sha1)
                else:
                  add = True
              if add:
                apk_packagename = names[0]
          if apk_sha1 and apk_packagename:
            dict_apksha1_packagename[apk_sha1] = apk_packagename
          # else:
          #   print(1)
      del b
  
  del item,data_apks,data_apk,lines,line,apk_packagename,apk_sha1,names

  out_data = OrderedDict()

  input_path = f'{path_script}/{folder_input}/{folder_logs}/{folder_name}'
  for filename in os.listdir(input_path):

      path_file = f'{input_path}/{filename}'
      apk_sha1 = filename.split('.')[0]
      install_or_run = filename.split('.')[1].replace('apk_','')

      if apk_sha1 in list_bad_apps:
        continue

      if apk_sha1 in dict_apksha1_packagename.keys():
        apk_packagename = dict_apksha1_packagename[apk_sha1]
        content,err,new_name = get_package_content(path_file,apk_packagename,dict_alt_names)
        if new_name:
          apk_packagename = new_name
      else:
        apk_packagename = None
        content,err = get_file_content(path_file)

      joined_content = ' '.join(content)
      if joined_content.count('Package [') > 1: # and apk_sha1 not in list_bad_apps:
        print(f'  More than one package in file {filename}')
        continue
      
      if err != None:
        if apk_sha1 not in out_data.keys():
          perm_data = OrderedDict()
          perm_data["apk_sha1"] = apk_sha1
          perm_data["in_sets"] = 'none'
          perm_data["package_name"] = apk_packagename
          perm_data["target_sdk"] = OrderedDict({'install': '', 'run': ''})
          perm_data['err_bool'] = True
          perm_data['err_type'] = ['OTHER',]
          perm_data['err_reason'] = [err,]
          perm_data['install'] = OrderedDict()
          perm_data['run'] = OrderedDict()
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data

        else:
          perm_data = out_data[apk_sha1]
          perm_data['err_bool'] = True
          perm_data['err_type'].append('OTHER')
          perm_data['err_reason'].append(err)
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data
      
      else:
        if apk_sha1 not in out_data.keys():
          perm_data = OrderedDict()
          perm_data["apk_sha1"] = apk_sha1
          perm_data["in_sets"] = 'none'
          perm_data["package_name"] = apk_packagename
          perm_data["target_sdk"] = OrderedDict({'install': '', 'run': ''})
          perm_data['err_bool'] = False
          perm_data['err_type'] = []
          perm_data['err_reason'] = []
          perm_data['install'] = OrderedDict()
          perm_data['run'] = OrderedDict()
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data

        else:
          perm_data = out_data[apk_sha1]
          perm_data[install_or_run]['declared permissions'] = OrderedDict()
          perm_data[install_or_run]['requested permissions'] = OrderedDict()
          perm_data[install_or_run]['install permissions'] = OrderedDict()
          perm_data[install_or_run]['runtime permissions'] = OrderedDict()

          out_data[perm_data['apk_sha1']] = perm_data

        p_inserting = False
        p_child_indentation = None
        p_perm_type = None

        for xline in content:

          if 'targetSdk=' in xline:
            attrs = xline.split(' ')
            for attr in attrs:
              if 'targetSdk=' in attr:
                attr = attr.replace('\n','').replace('targetSdk=','')
                if attr == '':
                  print(1)
                perm_data["target_sdk"][install_or_run] = attr

          indentation = float(len(xline) - len(xline.lstrip())) / indentation_length
          if indentation % 1 != 0:
            problem = True
            try:
              ind_diff = indentation - p_child_indentation
              if indentation > p_child_indentation and p_inserting:
                if ind_diff < 1:
                  indentation = p_child_indentation
                  problem = False
            except:
              continue
            if problem:
              print(apk_sha1)
              print(xline)
              raise Exception
          
          if p_child_indentation:
            if indentation < p_child_indentation:
              p_inserting = False
              p_child_indentation = None
              p_perm_type = None

          if p_inserting and p_child_indentation == indentation:
            this_perm = OrderedDict()
            yline = xline.strip().split(':')
            this_perm['name'] = yline[0]
            if len(yline) > 1:
              this_perm['params_bool'] = True
              params = yline[1].strip().split(', ')
              this_perm['params'] = params
            else:
              this_perm['params_bool'] = False
            perm_data[install_or_run][p_perm_type][yline[0]] = this_perm

          if xline.endswith('permissions:') and p_inserting == False:
            p_inserting = True
            p_child_indentation = indentation + 1
            p_perm_type = xline.strip()[:-1]
            perm_data[install_or_run][p_perm_type] = OrderedDict()
        
        if not perm_data["target_sdk"][install_or_run]:
          perm_data["target_sdk"][install_or_run] = None
        out_data[perm_data['apk_sha1']] = perm_data

  path_file = f'{path_script}/{folder_input}/{folder_logs}/failed.txt'
  with io.open(path_file, 'r') as f:
    data = f.readlines()
    for i in range(len(data)):
      if data[i].startswith('['):
        err_types,path = data[i][1:].split('] ')
        err_types = err_types.split('||')
        if True:
          err_line = ''
          err_reasons = ''
          index = i
          while '--------------------------------------------------' not in err_line:
            err_reasons += err_line
            err_line = data[index+1].replace('\n',' ')
            index += 1
          err_reasons = err_reasons.split('\n******************\n')
          err_reasons[-1] = err_reasons[-1].replace('\\n******************','')

          filename = path.split('/')[-1]
          apk_sha1 = filename.split('.')[0]

          if apk_sha1 not in out_data.keys():
            perm_data = OrderedDict()
            perm_data["apk_sha1"] = apk_sha1
            perm_data["in_sets"] = 'none'
            perm_data["package_name"] = apk_packagename
            perm_data["target_sdk"] = OrderedDict({'install': '', 'run': ''})
            perm_data['err_bool'] = True
            perm_data['err_type'] = err_types
            perm_data['err_reason'] = err_reasons
            perm_data['install'] = OrderedDict()
            perm_data['run'] = OrderedDict()

            out_data[perm_data['apk_sha1']] = perm_data
          
          else:
            perm_data = out_data[apk_sha1]
            perm_data['err_bool'] = True
            perm_data['err_type'] += err_types
            perm_data['err_reason'] += err_reasons

            out_data[perm_data['apk_sha1']] = perm_data
    
    for apk_sha1, perm_data in out_data.items():
      perm_data["has_diff"] = False
      perm_data["diff"] = OrderedDict({'unique_install': OrderedDict(), 'unique_run': OrderedDict()})
      for key in perm_data["diff"].keys():
        perm_data["diff"][key]['declared permissions'] = OrderedDict()
        perm_data["diff"][key]['requested permissions'] = OrderedDict()
        perm_data["diff"][key]['install permissions'] = OrderedDict()
        perm_data["diff"][key]['runtime permissions'] = OrderedDict()
      
      apk_ok = True
      if not perm_data['install'] or not perm_data['run']:
        apk_ok = False
      # else:
      #   if not perm_data['install']['declared permissions'] and not perm_data['install']['requested permissions'] \
      #     and not perm_data['install']['install permissions'] and not perm_data['install']['runtime permissions']:
      #     apk_ok = False
      #   if not perm_data['run']['declared permissions'] and not perm_data['run']['requested permissions'] \
      #     and not perm_data['run']['install permissions'] and not perm_data['run']['runtime permissions']:
      #     apk_ok = False
      
      if apk_ok:
        for xtype,xperms in perm_data['install'].items():
          for xperm,xpermargs in xperms.items():
            if xperm not in perm_data['run'][xtype].keys() or perm_data['run'][xtype][xperm] != perm_data['install'][xtype][xperm]:
              perm_data["has_diff"] = True
              if xperm not in perm_data['run'][xtype].keys():
                reason = 'diff_perm'
              else:
                reason = 'diff_params'
              perm_data["diff"]['unique_install'][xtype][xperm] = OrderedDict({'reason':reason, 'data':xpermargs})
        for xtype,xperms in perm_data['run'].items():
          for xperm,xpermargs in xperms.items():
            if xperm not in perm_data['install'][xtype].keys() or perm_data['run'][xtype][xperm] != perm_data['install'][xtype][xperm]:
              perm_data["has_diff"] = True
              if xperm not in perm_data['install'][xtype].keys():
                reason = 'diff_perm'
              else:
                reason = 'diff_params'
              perm_data["diff"]['unique_run'][xtype][xperm] = OrderedDict({'reason':reason, 'data':xpermargs})


  print(f'Line count: {len(out_data.keys())}')
  out_dir = f'{path_script}/{folder_output}/{folder_logs}'
  if not os.path.exists(out_dir): os.mkdir(out_dir)
  with io.open(f'{out_dir}/{out_name}_adb_permissions.json', 'w') as fp:
    for xh, xm in out_data.items():
      temp_jdict = {xh: xm}
      jline = json.dumps(temp_jdict)
      fp.write(jline + "\n")



if __name__ == '__main__':
  parse_by_sources('output_10_phone_2',sources_good)
  parse_by_sources('output_11_phone_2',sources_good)
  parse_by_sources('output_12_phone_2',sources_good)
  parse_by_sources('output_13_phone_2',sources_good)
  # parse_by_api('outputs_10_phone',sources_good)
  # parse_one('output_11_dummy_2','dummy_apk','dummy')
  # parse_one('output_13_dummy_2','dummy_apk','dummy')








"""
# def parse_by_api(folder_name,sources):

#   valid_apis = [27,28,29,30,31,32,33]

#   jlines = get_file_lines(file_apks)

#   data_json = OrderedDict()
#   for item in jlines:
#       jtem = json.loads(item)
#       for k,v in jtem.items():
#           data_json[k] = v

#   count_apk_sets = OrderedDict()
#   for source in sources:
#     count_apk_sets[source] = 0

#   data_apk_to_set = OrderedDict()
#   for ksha1, kmeta in data_json.items():
#     apk_sha1 = kmeta["sha1"]
#     apk_in_sets = kmeta["in_sets"]
#     api_level = kmeta["api_level_to_use"]
#     if api_level in valid_apis and apk_in_sets in sources:
#       data_apk_to_set[apk_sha1] = apk_in_sets
#       count_apk_sets[apk_in_sets] += 1
#   print(count_apk_sets)

#   for source in sources:
#     print(f'Parsing output for --- {source} --- ...')

#     out_data = OrderedDict()

#     input_path = f'{folder_input}/{folder_name}'
#     for folder in os.listdir(input_path):
#       logfolder_path = f'{input_path}/{folder}'
#       if os.path.isdir(logfolder_path):
#         for filename in os.listdir(logfolder_path):

#           if filename != 'failed.txt':
#             path_file = f'{logfolder_path}/{filename}'
#             apk_sha1 = filename.split('.')[0]

#             if data_apk_to_set[apk_sha1] == source:
#               content,err = get_file_content(path_file)

#               if err != None:
#                 perm_data = OrderedDict()
#                 perm_data["apk_sha1"] = apk_sha1
#                 perm_data["in_sets"] = source
#                 perm_data['err_bool'] = True
#                 perm_data['err_type'] = 'OTHER'
#                 perm_data['err_reason'] = err
#                 perm_data['declared permissions'] = OrderedDict()
#                 perm_data['requested permissions'] = OrderedDict()
#                 perm_data['install permissions'] = OrderedDict()
#                 perm_data['runtime permissions'] = OrderedDict()

#                 out_data[perm_data['apk_sha1']] = perm_data
              
#               else:
#                 perm_data = OrderedDict()
#                 perm_data["apk_sha1"] = apk_sha1
#                 perm_data["in_sets"] = source
#                 perm_data['err_bool'] = False
#                 perm_data['err_type'] = None
#                 perm_data['err_reason'] = None
#                 perm_data['declared permissions'] = OrderedDict()
#                 perm_data['requested permissions'] = OrderedDict()
#                 perm_data['install permissions'] = OrderedDict()
#                 perm_data['runtime permissions'] = OrderedDict()

#                 p_inserting = False
#                 p_child_indentation = None
#                 p_perm_type = None
#                 for xline in content:

#                   indentation = float(len(xline) - len(xline.lstrip())) / indentation_length
#                   if indentation % 1 != 0:
#                     problem = True
#                     try:
#                       ind_diff = indentation - p_child_indentation
#                       if indentation > p_child_indentation and p_inserting:
#                         if ind_diff < 1:
#                           indentation = p_child_indentation
#                           problem = False
#                     except:
#                       continue
#                     if problem:
#                       print(apk_sha1)
#                       print(xline)
#                       raise Exception
                  
#                   if p_child_indentation:
#                     if indentation < p_child_indentation:
#                       p_inserting = False
#                       p_child_indentation = None
#                       p_perm_type = None

#                   if p_inserting and p_child_indentation == indentation:
#                     this_perm = OrderedDict()
#                     yline = xline.strip().split(':')
#                     this_perm['name'] = yline[0]
#                     if len(yline) > 1:
#                       this_perm['params_bool'] = True
#                       params = yline[1].strip().split(', ')
#                       this_perm['params'] = params
#                     else:
#                       this_perm['params_bool'] = False
#                     perm_data[p_perm_type][yline[0]] = this_perm

#                   if xline.endswith('permissions:') and p_inserting == False:
#                     p_inserting = True
#                     p_child_indentation = indentation + 1
#                     p_perm_type = xline.strip()[:-1]
#                     perm_data[p_perm_type] = OrderedDict()
                
#                 out_data[perm_data['apk_sha1']] = perm_data

                  
#         path_file = f'{logfolder_path}/failed.txt'
#         with io.open(path_file, 'r') as f:
#           data = f.readlines()
#           for i in range(len(data)):
#             if data[i].startswith('['):
#               err_type,path = data[i][1:].split('] ')
#               err_reason = data[i+1].replace('\n','')
#               filename = path.split('/')[-1][:-1]
#               apk_sha1 = filename.split('.')[0]
              
#               if apk_sha1 == '': 
#                 continue

#               if apk_sha1 in data_apk_to_set.keys():
#                 if data_apk_to_set[apk_sha1] == source:

#                   if apk_sha1 not in out_data.keys():
#                     perm_data = OrderedDict()
#                     perm_data["apk_sha1"] = apk_sha1
#                     perm_data["in_sets"] = source
#                     perm_data['err_bool'] = True
#                     perm_data['err_type'] = err_type
#                     perm_data['err_reason'] = err_reason
#                     perm_data['declared permissions'] = OrderedDict()
#                     perm_data['requested permissions'] = OrderedDict()
#                     perm_data['install permissions'] = OrderedDict()
#                     perm_data['runtime permissions'] = OrderedDict()

#                     out_data[perm_data['apk_sha1']] = perm_data
                  
#                   else:
#                     perm_data = out_data[apk_sha1]
#                     perm_data['err_bool'] = True
#                     perm_data['err_type'] = err_type
#                     perm_data['err_reason'] = err_reason

#                     out_data[perm_data['apk_sha1']] = perm_data

#     print(f'Line count: {len(out_data.keys())}')
#     with io.open(f'{path_script}/{folder_output}/{source}_adb_permissions.json', 'w') as fp:
#       for xh, xm in out_data.items():
#         temp_jdict = {xh: xm}
#         jline = json.dumps(temp_jdict)
#         fp.write(jline + "\n")



"""
