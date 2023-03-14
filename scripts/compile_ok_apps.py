import io
import os
import sys
from collections import OrderedDict
import json

from tabulate import tabulate


path_script = os.path.abspath(os.path.dirname(__file__))

folder_input = 'data/adb_parsed/out'
folder_output = 'data/adb_parsed/ok'

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

apps_devices = OrderedDict()
for source in sources:
  apps_devices[source] = OrderedDict()

all_stats = OrderedDict()
all_stats_apks = OrderedDict()
# total per set | cannot install | % | can install | % | cannot run | % | can run | % |  (can run / total set ) * 100
headers = ['source','total','cannot install','%','can install','%','cannot run','%','can run','%','can run / total %']
numbers = ['total','cannot install','cannot install %','can install','can install %','cannot run','cannot run %','can run','can run %','can run / total %']

control = []
all_apks = set()
for item in os.listdir(f'{path_script}/{folder_input}'):
  path_folder = f'{path_script}/{folder_input}/{item}'
  if os.path.isdir(path_folder):
    # print(f'=== parsing {item}')

    stats = OrderedDict()
    for source in sources:
      stats[source] = OrderedDict()
      for n in numbers:
        stats[source][n] = 0
    
    stats_apks = OrderedDict()
    for source in sources:
      stats_apks[source] = OrderedDict()
      for n in numbers:
        stats_apks[source][n] = []

    total_apk = 0
    total_working = 0
    control.append('y')
    for file in os.listdir(path_folder):
      source = file.replace('_adb_permissions.json','')
      # print(f'{source}')
      with io.open(f'{path_folder}/{file}') as jsonfile:
        lines = jsonfile.readlines()
        # print(f'  apks : {len(lines)}')
        total_apk += len(lines)
        stats[source]['total'] = len(lines) #
        
        apk_ok_count = 0
        for line in lines:
          
          apk_json = json.loads(line)
          apk_sha1 = list(apk_json.keys())[0]
          all_apks.add(apk_sha1)
          stats_apks[source]['total'].append(apk_sha1)

          stat_ok = True

          if 'INSTALL' in apk_json[apk_sha1]['err_type'] or 'EMPTY FILE install' in apk_json[apk_sha1]['err_reason']:
            stats[source]['cannot install'] += 1
            stats_apks[source]['cannot install'].append(apk_sha1)
            stat_ok = False
          else:
            stats[source]['can install'] += 1
            stats_apks[source]['can install'].append(apk_sha1)
            if 'RUN' in apk_json[apk_sha1]['err_type'] or 'EMPTY FILE run' in apk_json[apk_sha1]['err_reason'] or 'STOP' in apk_json[apk_sha1]['err_type']:
              stats[source]['cannot run'] += 1
              stats_apks[source]['cannot run'].append(apk_sha1)
              stat_ok = False
            else:
              stats[source]['can run'] += 1
              stats_apks[source]['can run'].append(apk_sha1)

          # apk_ok = True
          # if apk_json[apk_sha1]['err_bool']:
          #   apk_ok = False
          # if not apk_json[apk_sha1]['install'] or not apk_json[apk_sha1]['run']:
          #   apk_ok = False
          # else:
          #   if not apk_json[apk_sha1]['install']['declared permissions'] and not apk_json[apk_sha1]['install']['requested permissions'] \
          #     and not apk_json[apk_sha1]['install']['install permissions'] and not apk_json[apk_sha1]['install']['runtime permissions']:
          #     apk_ok = False
          #   if not apk_json[apk_sha1]['run']['declared permissions'] and not apk_json[apk_sha1]['run']['requested permissions'] \
          #     and not apk_json[apk_sha1]['run']['install permissions'] and not apk_json[apk_sha1]['run']['runtime permissions']:
          #     apk_ok = False
          
          # if apk_ok:
          #   if apk_sha1 not in apps_devices[source].keys():
          #     apps_devices[source][apk_sha1] = ['y']
          #   else:
          #     apps_devices[source][apk_sha1].append('y')
          #   apk_ok_count += 1
          # else:
          #   if apk_sha1 not in apps_devices[source].keys():
          #     apps_devices[source][apk_sha1] = ['n']
          #   else:
          #     apps_devices[source][apk_sha1].append('n')
          
          # if apk_ok != stat_ok:
          #   print('not ok')
        
        # print(f'  working apks : {apk_ok_count} ({round(apk_ok_count/len(lines)*100,2)}%)')
        total_working += apk_ok_count

    # print(f'total apks : {total_apk}')
    # print(f'total working apks : {total_working} ({round(total_working/total_apk*100,2)}%)')
    # print('==================================')

  for source,stat in stats.items():
    stat['cannot install %'] = round( stat['cannot install'] / stat['total']  * 100 ,2)
    stat['can install %'] = round( stat['can install'] / stat['total']  * 100 ,2)
    stat['cannot run %'] = round( stat['cannot run'] / stat['can install']  * 100 ,2)
    stat['can run %'] = round( stat['can run'] / stat['can install']  * 100 ,2)
    stat['can run / total %'] = round( stat['can run'] / stat['total']  * 100 ,2)
    stats[source] = stat

  stat_total = OrderedDict()
  for n in numbers:
    stat_total[n] = 0
  for n in numbers:
    for source in sources:
      stat_total[n] += stats[source][n]
  stat_total['cannot install %'] = round( stat_total['cannot install'] / stat_total['total'] * 100 ,2)
  stat_total['can install %'] = round( stat_total['can install'] / stat_total['total'] * 100 ,2)
  stat_total['cannot run %'] = round( stat_total['cannot run'] / stat_total['can install'] * 100 ,2)
  stat_total['can run %'] = round( stat_total['can run'] / stat_total['can install'] * 100 ,2)
  stat_total['can run / total %'] = round( stat_total['can run'] / stat_total['total'] * 100 ,2)

  stats['total'] = stat_total

  stat_total = OrderedDict()
  for n in numbers:
    stat_total[n] = []
  for n in numbers:
    for source in sources:
      stat_total[n] += stats_apks[source][n]
  
  stats_apks['total'] = stat_total
  
  all_stats[item] = stats
  all_stats_apks[item] = stats_apks

print()
for output,stats in all_stats.items():
  tabl_data = []
  for source in stats.keys():
    tabl_line = [source]
    for stat in numbers:
      tabl_line.append(stats[source][stat])
    tabl_data.append(tabl_line)
  print(output)
  print(tabulate(tabl_data, headers, tablefmt="github"))
  print()


# for source in sources:
#   for apk_sha1 in apps_devices[source].keys():
#     if apps_devices[source][apk_sha1] == control:
#       apps_working[source].append(apk_sha1)

print('\nFOR ALL DEVICES:')


# print(f'TOTAL APKS : {len(all_apks)}')
# print(f'TOTAL WORKING APKS : {tot} ({round(tot/len(all_apks)*100,2)}%)')


source_col = sources + ['total']
all_stats_joined = OrderedDict()
for source in source_col:
  all_stats_joined[source] = OrderedDict()
  for n in numbers:
    all_stats_joined[source][n] = 0

for n in numbers:
  for source in source_col:
    lists = []
    for output,stats in all_stats_apks.items():
      lists.append(stats[source][n])
    if 'cannot' in n:
      all_stats_joined[source][n] = set().union(*lists)
    else:
      all_stats_joined[source][n] = set.intersection(*map(set,lists))

# tot = 0
for source in sources:
  with io.open(f'{path_script}/{folder_output}/{source}_working.txt', 'w') as out:
    for apk in all_stats_joined[source]['can run']:
      out.write(f'{apk}\n')
  # print(f'  {source} : {len(apps_working[source])}')
  # tot += len(apps_working[source])

for n in numbers:
  for source in source_col:
    all_stats_joined[source][n] = len(all_stats_joined[source][n])
for source in source_col:
  all_stats_joined[source]['cannot install %'] = round( all_stats_joined[source]['cannot install'] / all_stats_joined[source]['total']  * 100,2)
  all_stats_joined[source]['can install %'] = round( all_stats_joined[source]['can install'] / all_stats_joined[source]['total']  * 100,2)
  all_stats_joined[source]['cannot run %'] = round( all_stats_joined[source]['cannot run'] / all_stats_joined[source]['can install']  * 100,2)
  all_stats_joined[source]['can run %'] = round( all_stats_joined[source]['can run'] / all_stats_joined[source]['can install']  * 100,2)
  all_stats_joined[source]['can run / total %'] = round( all_stats_joined[source]['can run'] / all_stats_joined[source]['total']  * 100,2)

tabl_data = []
for source in source_col:
  tabl_line = [source]
  for stat in numbers:
    tabl_line.append(all_stats_joined[source][stat])
  tabl_data.append(tabl_line)

print(tabulate(tabl_data, headers, tablefmt="github"))