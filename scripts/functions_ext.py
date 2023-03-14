import io
import os
import sys
from collections import OrderedDict
import json
import statistics

from tabulate import tabulate


path_script = os.path.abspath(os.path.dirname(__file__))

folder_input_data = 'data/adb_parsed/out'
folder_input_ok = 'data/adb_parsed/ok'
folder_output = 'data'
# file_lists = 'data/data_lists.json'
file_permissions = 'data/data_permissions.json'

sources = [
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


apps_working = OrderedDict()
for source in sources:
  apps_working[source] = []

for file in os.listdir(f'{path_script}/{folder_input_ok}'):
  path_file = f'{path_script}/{folder_input_ok}/{file}'
  source = file.replace('_working.txt','')
  with io.open(path_file) as oks:
    for line in oks.readlines():
      line = line.replace('\n','')
      apps_working[source].append(line)
del file,path_file,source,line

set_apps = set()
for source,apps in apps_working.items():
  for app in apps:
    set_apps.add(app)
print(len(set_apps))

apps_all_data = OrderedDict()
apps_working_data = OrderedDict()
output_to_ver = OrderedDict()

for item in os.listdir(f'{path_script}/{folder_input_data}'):
  if 'phone' not in item:
    continue
  path_folder = f'{path_script}/{folder_input_data}/{item}'
  if os.path.isdir(path_folder):
    output_to_ver[item] = item.split('_')[1]
    apps_all_data[item] = OrderedDict()
    apps_working_data[item] = OrderedDict()
    for file in os.listdir(path_folder):
      source = file.replace('_adb_permissions.json','')
      apps_all_data[item][source] = OrderedDict()
      apps_working_data[item][source] = OrderedDict()
      with io.open(f'{path_folder}/{file}') as jsonfile:
        lines = jsonfile.readlines()
        for line in lines:
          apk_json = json.loads(line)
          apk_sha1 = list(apk_json.keys())[0]
          if apk_sha1 in apps_working[source]:
            apps_working_data[item][source][apk_sha1] = apk_json[apk_sha1]
          apps_all_data[item][source][apk_sha1] = apk_json[apk_sha1]
del item,path_folder,file,source,lines,line,apk_json,apk_sha1,jsonfile

ver_to_output = OrderedDict()
for k,v in output_to_ver.items():
  ver_to_output[v] = k

data_permissions = OrderedDict()
with io.open(f'{path_script}/{file_permissions}', 'r') as rif:
  for line in rif:
    xline = line.replace("\n", "").strip()
    if xline:
      jdata = json.loads(xline)
      for k,v in jdata.items():
        if not k in data_permissions:
          data_permissions[k] = v
del k,v,line,xline,jdata


def is_apk_runnable(apk_json):
  stat_ok = True
  if 'INSTALL' in apk_json['err_type'] or 'EMPTY FILE install' in apk_json['err_reason']:
    stat_ok = False
  if 'RUN' in apk_json['err_type'] or 'EMPTY FILE run' in apk_json['err_reason']:
    stat_ok = False
  if 'STOP' in apk_json['err_type']:
    stat_ok = False

  return stat_ok


def check_targetsdk_consistency():

  for source in sources:
    for apk_sha1 in apps_working[source]:
      target_sdk = []
      for output,ver in output_to_ver.items():
        apk_data = apps_working_data[output][source][apk_sha1]
        t1 = apk_data['target_sdk']['install']
        t2 = apk_data['target_sdk']['run']
        if t1 != t2:
          print(f'{output} - {source} - {apk_sha1}')
          print(f'target sdk changed: <{t1}>/<{t2}>')
        else:
          target_sdk.append(t1)
      if len(set(target_sdk)) != 1:
        print(f'{source} - {apk_sha1}')
        print(f'target sdk changed: <{target_sdk}>')


def table_source_targetsdk_all():

  apk_to_targetsdk = OrderedDict()
  set_targetsdk = set()
  for source in sources:
    apk_to_targetsdk[source] = OrderedDict()

  for version in ver_to_output.keys():
    data_ver = apps_working_data[ver_to_output[str(version)]]

    for source in sources:
      for apk_sha1 in data_ver[source].keys():
        apk_data = data_ver[source][apk_sha1]
        if is_apk_runnable(apk_data):
          t1 = apk_data['target_sdk']['install']
          apk_to_targetsdk[source][apk_sha1] = t1
          set_targetsdk.add(t1)
  
  tabl_headers = ['source']
  tabl_vers = sorted(list(set_targetsdk))
  tabl_headers += tabl_vers
  tabl_headers.append('all')
  tabl_data = []
  tt = 0
  totals = OrderedDict()
  for ver in tabl_vers:
    totals[ver] = 0
  for source in sources:
    tabl_line = [source]
    tot_line = 0
    for ver in tabl_vers:
      cnt = sum(x == ver for x in apk_to_targetsdk[source].values())
      tabl_line.append(cnt)
      totals[ver] += cnt
      tot_line +=cnt
      tt += cnt
    tabl_line.append(tot_line)
    tabl_data.append(tabl_line)
  tabl_total = ['total']
  for ver in tabl_vers:
    tabl_total.append(totals[ver])
  tabl_total.append(tt)
  tabl_data.append(tabl_total)
  
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


def table_source_targetsdk_one(version):

  apk_to_targetsdk = OrderedDict()
  set_targetsdk = set()

  data_ver = apps_all_data[ver_to_output[str(version)]]

  for source in sources:
    apk_to_targetsdk[source] = OrderedDict()
    for apk_sha1 in data_ver[source].keys():
      apk_data = data_ver[source][apk_sha1]
      if is_apk_runnable(apk_data):
        t1 = apk_data['target_sdk']['install']
        apk_to_targetsdk[source][apk_sha1] = t1
        set_targetsdk.add(t1)
  
  tabl_headers = ['source']
  tabl_vers = sorted(list(set_targetsdk))
  tabl_headers += tabl_vers
  tabl_headers.append('all')
  tabl_data = []
  tt = 0
  totals = OrderedDict()
  for ver in tabl_vers:
    totals[ver] = 0
  for source in sources:
    tabl_line = [source]
    tot_line = 0
    for ver in tabl_vers:
      cnt = sum(x == ver for x in apk_to_targetsdk[source].values())
      tabl_line.append(cnt)
      totals[ver] += cnt
      tot_line +=cnt
      tt += cnt
    tabl_line.append(tot_line)
    tabl_data.append(tabl_line)
  tabl_total = ['total']
  for ver in tabl_vers:
    tabl_total.append(totals[ver])
  tabl_total.append(tt)
  tabl_data.append(tabl_total)
  
  print(tabulate(tabl_data, tabl_headers, tablefmt="github"))
  print()


def table_permissions_versions(out_name):

  apks_total = 0
  for k,v in apps_working.items():
    apks_total += len(v)
  tabl_headers = [f'permission (in {apks_total} apks)']
  tabl_columns = []
  for output,ver in output_to_ver.items():
    tabl_columns += [f'requested {ver}', f'granted {ver}', f'runtime {ver}', f'err {ver}']
  tabl_headers += tabl_columns
  tabl_data = []

  perm_counts = OrderedDict()
  for perm,pmeta in data_permissions.items():
    perm_counts[perm] = OrderedDict()
    for item in tabl_columns:
      perm_counts[perm][item] = OrderedDict()
      perm_counts[perm][item]['install'] = 0
      perm_counts[perm][item]['run'] = 0
      perm_counts[perm][item]['only_install'] = 0
      perm_counts[perm][item]['only_run'] = 0
  del perm,pmeta,item

  perm_counts_extra = OrderedDict()
  def add_new_perm(d,perm):
    d[perm] = OrderedDict()
    for item in tabl_columns:
      d[perm][item] = OrderedDict()
      d[perm][item]['install'] = 0
      d[perm][item]['run'] = 0

  for output,ver in output_to_ver.items():
    for source in sources:
      for apk_sha1,apk_data in apps_working_data[output][source].items():

        for perm,pdata in apk_data['install']['requested permissions'].items():
          try:
            perm_counts[perm][f'requested {ver}']['install'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'requested {ver}']['install'] += 1

        for perm,pdata in apk_data['install']['install permissions'].items():
          try:
            perm_counts[perm][f'granted {ver}']['install'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'granted {ver}']['install'] += 1

        for perm,pdata in apk_data['install']['runtime permissions'].items():
          try:
            perm_counts[perm][f'runtime {ver}']['install'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'runtime {ver}']['install'] += 1
        

        for perm,pdata in apk_data['run']['requested permissions'].items():
          try:
            perm_counts[perm][f'requested {ver}']['run'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'requested {ver}']['run'] += 1
        
        for perm,pdata in apk_data['run']['install permissions'].items():
          try:
            perm_counts[perm][f'granted {ver}']['run'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'granted {ver}']['run'] += 1
        
        for perm,pdata in apk_data['run']['runtime permissions'].items():
          try:
            perm_counts[perm][f'runtime {ver}']['run'] += 1
          except KeyError:
            add_new_perm(perm_counts_extra,perm)
            perm_counts_extra[perm][f'runtime {ver}']['run'] += 1
  del apk_sha1,apk_data,output,ver,source

  for perm,pdata in perm_counts.items():
    tabl_line = [perm]
    for item in tabl_columns:
      n_install = pdata[item]['install']
      n_run = pdata[item]['run']
      tabl_line.append(f'{n_install} / {n_run}')
    tabl_data.append(tabl_line)
  
  table = tabulate(tabl_data, tabl_headers, tablefmt="github", stralign='center', colalign=("left",))
  with io.open(f'{path_script}/{folder_output}/{out_name}.txt', 'w') as out:
    out.write(table)


def table_apk_runsinversions(out_name):
  all_stats_apks = OrderedDict()
  all_apks = OrderedDict()
  # apk | runs in 10 |  runs in 11| runs in 12| runs in 13| runs in how many versions (list) | (count)
  headers = ['apk_sha1','targetsdk_list','targetsdk_set']
  numbers = ['total','cannot install','cannot install %','can install','can install %','cannot run','cannot run %','can run','can run %','can run / total']
  tabl_vers = sorted([ver for ver in output_to_ver.values()])
  for ver in tabl_vers:
    headers.append(f'runs {ver}')
  headers += ['runs in versions','count']

  set_targetsdk = set()
  for item in os.listdir(f'{path_script}/{folder_input_data}'):
    path_folder = f'{path_script}/{folder_input_data}/{item}'
    if os.path.isdir(path_folder):
      
      stats_apks = OrderedDict()
      for source in sources:
        stats_apks[source] = OrderedDict()
        for n in numbers:
          stats_apks[source][n] = []

      for file in os.listdir(path_folder):
        source = file.replace('_adb_permissions.json','')
        with io.open(f'{path_folder}/{file}') as jsonfile:
          lines = jsonfile.readlines()
          
          for line in lines:
            
            apk_json = json.loads(line)
            apk_sha1 = list(apk_json.keys())[0]
            apk_targetsdk = apk_json[apk_sha1]['target_sdk']['install']
            set_targetsdk.add(apk_targetsdk)
            if apk_sha1 not in all_apks.keys():
              all_apks[apk_sha1] = OrderedDict({'source':source,'targetsdk':[str(apk_targetsdk)]})
            else:
              all_apks[apk_sha1]['targetsdk'].append(apk_targetsdk)
            stats_apks[source]['total'].append(apk_sha1)

            stat_ok = True

            if 'INSTALL' in apk_json[apk_sha1]['err_type'] or 'EMPTY FILE install' in apk_json[apk_sha1]['err_reason']:
              stats_apks[source]['cannot install'].append(apk_sha1)
              stat_ok = False
            else:
              stats_apks[source]['can install'].append(apk_sha1)
              if 'RUN' in apk_json[apk_sha1]['err_type'] or 'EMPTY FILE run' in apk_json[apk_sha1]['err_reason']:
                stats_apks[source]['cannot run'].append(apk_sha1)
                stat_ok = False
              else:
                stats_apks[source]['can run'].append(apk_sha1)

            apk_ok = True
            if apk_json[apk_sha1]['err_bool']:
              apk_ok = False
            if not apk_json[apk_sha1]['install'] or not apk_json[apk_sha1]['run']:
              apk_ok = False
            
            if apk_ok != stat_ok:
              print('not ok')

    stat_total = OrderedDict()
    for n in numbers:
      stat_total[n] = []
    for n in numbers:
      for source in sources:
        stat_total[n] += stats_apks[source][n]
    
    stats_apks['total'] = stat_total
    all_stats_apks[item] = stats_apks

  del apk_json,apk_ok,apk_sha1,apk_targetsdk,file,item,line,lines
  del n,path_folder,source,stat_ok,stat_total,stats_apks,ver

  tabl_data = []
  for apk_sha1,meta in all_apks.items():
    tabl_line = [apk_sha1,meta['targetsdk'],set(meta['targetsdk'])]
    versions = ''
    count = 0
    for ver in tabl_vers:
      for k,v in output_to_ver.items():
        if v==ver: output = k
      del k,v
      data_output = all_stats_apks[output]
      if apk_sha1 in data_output[meta['source']]['can run']:
        tabl_line.append('x')
        versions += f'{ver}-'
        count += 1
      else:
        tabl_line.append('')
    versions = versions[:-1]
    tabl_line += [versions,count]
    tabl_data.append(tabl_line)
  
  table = tabulate(tabl_data, headers, tablefmt="github",)
  with io.open(f'{path_script}/{folder_output}/{out_name}.txt', 'w') as out:
    out.write(table)



if __name__ == '__main__':
  # check_targetsdk_consistency()
  # table_permissions_versions('table_perms_inapks')
  # table_apk_runsinversions('table_apk_runsinversions')
  table_source_targetsdk_one(10)
  table_source_targetsdk_one(11)
  table_source_targetsdk_one(12)
  table_source_targetsdk_one(13)
  table_source_targetsdk_all()




"""

| source              |   29 |   30 |   31 |   32 |
|---------------------|------|------|------|------|
| androgalaxy_2019    |  173 |    0 |    0 |    0 |
| androidapkfree_2020 |  159 |    9 |    0 |    0 |
| apkgod_2020         |  348 |    0 |    0 |    0 |
| apkmaza_2020        |   23 |    0 |    0 |    0 |
| apkpure_2021        |  155 |   10 |    0 |    0 |
| appsapk_com_2020    |  122 |    0 |    0 |    0 |
| crackhash_2022      |   38 |  470 |  177 |   15 |
| crackshash_2021     |  391 |  518 |   57 |    1 |
| fdroid_2020         |  859 |   45 |    0 |    0 |

"""