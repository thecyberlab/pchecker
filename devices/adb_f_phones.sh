#!/bin/bash


# -----download-----
# ADB
# download platform tools: https://developer.android.com/studio/releases/platform-tools
# standalone binary in platform-tools (included)

##################################################################################
##################################################################################

# bash ./adb_f_phones.sh 2>&1 | tee log_x.txt


common_path='' # <<<<<< PATH TO COMMON APK FOLDER <<<<<<<<<<
nm="apk_default" # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE NAME <<<<<<<<<
parse_path='/home/user01/Desktop/adb_vm' # <<<<<<<<<<<<<<<<<<<<<<<< PATH TO this FOLDER <<<<<<<<<
sleep_after_reboot=30 # <<<<<<<<<<<<<<<<<<<<<<<< 15-30 <<<<<<<<<<<<<<<<<<<<<<<<<<<<<

declare -A name_to_path
# POINT TO APK
# name_to_path['<output_folder_name>']=""$common_path"/<folder_with_apks>"
# OR
# name_to_path['<output_folder_name>']="<path_to_folder_with_apks>"

name_to_path['androgalaxy_2019_apks']=""$common_path"/androgalaxy_2019"
name_to_path['androidapkfree_2020_apks']=""$common_path"/androidapkfree_2020"
name_to_path['apkgod_2020_apks']=""$common_path"/apkgod_2020"
name_to_path['apkmaza_2020_apks']=""$common_path"/apkmaza_2020"
name_to_path['apkpure_2021_apks']=""$common_path"/apkpure_2021"
name_to_path['appsapk_com_2020_apks']=""$common_path"/appsapk_com_2020"
name_to_path['crackhash_2022_apks']=""$common_path"/crackhash_2022"
name_to_path['crackshash_2021_apks']=""$common_path"/crackshash_2021"
name_to_path['fdroid_2020_apks']=""$common_path"/fdroid_2020"
name_to_path['androidapkfree2_2020_apks']=""$common_path"/androidapkfree2_2020"
#name_to_path['dummy_apk']='/home/user01/Desktop/adb_vm/apks/dummy'
#name_to_path['permtest_apk']='/home/user01/Desktop/adb_vm/apks/test'

use_sets=(
 'androgalaxy_2019_apks'
 'androidapkfree_2020_apks'
 'apkgod_2020_apks'
 'apkmaza_2020_apks'
 'apkpure_2021_apks'
 'appsapk_com_2020_apks'
 'crackhash_2022_apks'
 'crackshash_2021_apks'
 'fdroid_2020_apks'
#'androidapkfree2_2020_apks'
 )
#use_sets=(
# 'dummy_apk'
# 'permtest_apk'
# )


timeout=300

adb=""$parse_path"/adb"
aapt=""$parse_path"/aapt2"
output_path='outputs'
output_folder=""$output_path"/output_"$nm""
temp_folder="temp"
mkdir -p $output_folder
failed_log=""$output_folder"/failed.txt"
done_log=""$parse_path"/temp/done.txt"
err_file=""$parse_path"/temp/ERR"
bad_apps=""$parse_path"/temp/bad_apps.txt"

if [ ! -d "$temp_folder" ]; then
    mkdir -p $temp_folder
fi
touch $failed_log
if [ ! -f "$done_log" ]; then
    touch $done_log
fi

done_apks=$(cat "$done_log");
echo "output $nm"
for key in "${use_sets[@]}"; do
    apks_path="${name_to_path[$key]}"
    set_output_folder=""$output_folder"/"$key""
    mkdir -p $set_output_folder
    for file in "$apks_path"/*; do
        if [[ "$file" != *".apk" ]]; then
            apk_path="$apks_path"/"$file.apk"
        else
            apk_path="$apks_path"/"$file"
        fi
        if [[ "$done_apks" != *"$file"* ]]; then
            #bash ./adb_f_phones_one.sh "$adb" "$aapt" "$file" "$set_output_folder" "$failed_log" "$done_log" "$err_file" "$bad_apps" & command_pid=$!
            bash ./adb_f_phones_one_metaonly.sh "$adb" "$aapt" "$file" "$set_output_folder" "$failed_log" "$done_log" "$err_file" "$bad_apps" & command_pid=$!
            ( sleep $timeout & wait; kill $command_pid 2>/dev/null) &  sleep_pid=$!
            wait $command_pid
            kill $sleep_pid 2>/dev/null 
        fi
        if [ -f "$err_file" ]; then
            #echo "------------ WIPING DATA ------------"
            #wipe=$("$adb" shell wipe data 2>&1);
            #echo "$wipe"
            currentDate=`date`
            echo $currentDate
            echo "------------ REBOOTING DEVICE ------------"
            reboot=$("$adb" reboot 2>&1);
            while :; do
                device_up=$("$adb" devices 2>&1);
                control="${device_up//"devices"}"
                if [[ "$control" == *"device"* ]]; then
                    currentDate=`date`
                    echo $currentDate
                    echo "------------ DEVICE UP ------------"
                    sleep $sleep_after_reboot
                    rm "$err_file"
                    break
                fi
            done
        fi
    done
done

echo ''
echo "========================================================="
echo "====================== FINAL END ========================"
echo "========================================================="

