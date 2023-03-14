from math import perm
import os
import io
import copy
import re
from collections import OrderedDict
import json


def create_perm_meta():
  perm_dict = OrderedDict()
  perm_dict['version'] = 'XXX'
  perm_dict['tag'] = 'XXX'
  perm_dict['restriction_list'] = 'XXX'
  perm_dict['f_group'] = 'XXX'
  perm_dict['deprecated'] = 'XXX'
  perm_dict['status'] = 'XXX'
  perm_dict['protection_level'] = 'XXX'
  perm_dict['usage'] = 'XXX'
  perm_dict['type'] = 'XXX'
  perm_dict['comment'] = 'XXX'

  return perm_dict


input = 'input'
output = 'output'
file_permission_mappings = "android_hidden_flags.json"

list_manifests = [
  "android9-s2-release",
  "android10-s3-release",
  "android11-s1-release",
  "android12-s5-release",
]

ver_to_api = {'9':28,'10':29,'11':30,'12':31,'13':33}

dict_andro_maps = dict()
with io.open(file_permission_mappings, 'r') as rif:
    for line in rif:
        xline = line.replace("\n", "").strip()
        if xline:
            jdata = json.loads(xline)
            for k,v in jdata.items():
                if not k in dict_andro_maps:
                    dict_andro_maps[k] = v
del k,v,line,xline,jdata


for name in list_manifests:

  perm_version = name.split('-')[0].replace('android','')

  dict_perms = OrderedDict()

  with io.open(f'{input}/{name}.txt','r') as f:
    data_file = f.read()
    data_sections = []
    data_content = copy.deepcopy(data_file)
    for data_line in data_content.split('\n'):
      if '============' in data_line:
        p1,p2 = data_content.split(f'{data_line}\n',1)
        data_sections.append(p1)
        data_content = copy.deepcopy(p2)
    data_sections = data_sections[3:]
    del data_line,data_content,p1,p2

    perm_type = None
    for i in range(len(data_sections)):
      section = data_sections[i]
      n_lines = len(section.split('\n')[:-1])
      if 'PERMISSIONS' in section and n_lines == 1:
        perm_type = section.replace('<!--','').replace('-->','').strip()
      if section.strip().startswith('<!-- Permissions') or ( 'REMOVED PERMISSIONS' in section ):
        perm_category = section.replace('<!--','').replace('-->','').strip()
        section_block = data_sections[i+1]

        section_block_list = re.split(r'-->|/>', section_block)
        for j in range(len(section_block_list)):
            section_block_element = section_block_list[j]
            if section_block_element.startswith('\n'):
              section_block_element = section_block_element[1:].strip()
              if section_block_element.startswith('<permission android:name'):
                perm_name = None
                perm_meta = create_perm_meta()

                try:
                  perm_comment = section_block_list[j-1]
                  if '@SystemApi' in perm_comment:
                    perm_tag = 'system'
                  elif '@hide' in perm_comment:
                    perm_tag = 'hide'
                  else:
                    perm_tag = 'sdk'
                  if '@deprecated' in perm_comment:
                    perm_deprecated = True
                  else:
                    perm_deprecated = False
                  if '@removed' in perm_comment or perm_type == 'REMOVED PERMISSIONS':
                    perm_status = 'removed'
                  else:
                    perm_status = 'not_removed'
                  if 'Not for use by third-party' in perm_comment or 'not a third-party' in perm_comment:
                    perm_usage = 'not_by_third_party_apps'
                  else:
                    perm_usage = 'general'
                  perm_comment = re.sub('\s+',' ',perm_comment.replace('\n',' '))
                except IndexError:
                  perm_comment = 'MISSING'
                  perm_tag = 'sdk'
                  perm_deprecated = False
                  if perm_type == 'REMOVED PERMISSIONS':
                    perm_status = 'removed'
                  else:
                    perm_status = 'not_removed'
                  perm_usage = 'general'
                  
                perm_data = section_block_element.split('\n')
                for perm_dataline in perm_data:
                  if 'android:name' in perm_dataline:
                    perm_name = perm_dataline.replace('"','').split('=')[1]
                  elif 'android:protectionLevel' in perm_dataline:
                    perm_protlvl = perm_dataline.replace('"','').split('=')[1]
                  elif 'android:permissionFlags' in perm_dataline:
                    if 'removed' in perm_dataline:
                      perm_status = 'removed'
                perm_restr = 'XXX'
                if perm_name in dict_andro_maps.keys():
                  if ver_to_api[perm_version] in dict_andro_maps[perm_name]['seen_in']:
                    perm_restr = dict_andro_maps[perm_name]['apiver_flags'][str(ver_to_api[perm_version])]['flags']

                perm_meta['version'] = perm_version
                perm_meta['tag'] = perm_tag
                perm_meta['restriction_list'] = perm_restr
                perm_meta['f_group'] = perm_category
                perm_meta['deprecated'] = perm_deprecated
                perm_meta['status'] = perm_status
                perm_meta['protection_level'] = perm_protlvl
                perm_meta['usage'] = perm_usage
                perm_meta['type'] = perm_type
                perm_meta['comment'] = perm_comment

                dict_perms[perm_name] = perm_meta

                # print(1)
  
  perm_meta = OrderedDict()
  perm_meta['version'] = OrderedDict()
  perm_meta['tag'] = OrderedDict()
  perm_meta['restriction_list'] = OrderedDict()
  perm_meta['f_group'] = OrderedDict()
  perm_meta['deprecated'] = OrderedDict()
  perm_meta['status'] = OrderedDict()
  perm_meta['protection_level'] = OrderedDict()
  perm_meta['usage'] = OrderedDict()
  perm_meta['type'] = OrderedDict()
  for p in dict_perms.keys():
    for key in dict_perms[p].keys():
      if key != 'comment':
        if dict_perms[p][key] not in perm_meta[key].keys():
          perm_meta[key][dict_perms[p][key]] = 1
        else:
          perm_meta[key][dict_perms[p][key]] = perm_meta[key][dict_perms[p][key]] + 1
  print(f'\n{perm_version}\n')
  for key in perm_meta.keys():
    print(f'  {key}')
    for k in perm_meta[key].keys():
      print(f'    {k}: {perm_meta[key][k]}')


  with io.open(f'{output}/mapping_{perm_version}.json','w') as out:
    json.dump(dict_perms,out,indent=2)

        
      



  print(1)
