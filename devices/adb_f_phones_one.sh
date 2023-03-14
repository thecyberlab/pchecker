file=$3
adb=$1
aapt=$2
output_folder=$4
failed_log=$5
done_log=$6
err=$7
bad_apps=$8

output_path='outputs_extension'

file_basename=$(basename ${file})
declare -a error_types
declare -a error_contents
echo "$file" >> "$done_log"
echo "#########################################################"
echo "--- APK FILE: "$file""

out_name_0=""$output_folder"/"$file_basename"_meta.txt"
touch "$out_name_0"
package_data_0=$("$aapt" dump badging "$package_name" 2>&1);
echo "------------ SUCCESS GETTING METADATA ------------"
echo "$package_data_0" >> "$out_name_0"

packages_default=$("$adb" shell 'pm list packages -3');
install_apk=$("$adb" install "$file" 2>&1)
if [[ "$install_apk" == *"Success"* ]]; then
    echo "------------ SUCCESS INSTALLING ------------"
    out_name_1=""$output_folder"/"$file_basename"_install.txt"
    out_name_2=""$output_folder"/"$file_basename"_run.txt"
    touch "$out_name_1"
    touch "$out_name_2"
    packages_current=$("$adb" shell 'pm list packages -3');
    readarray -t arr_default <<<"$packages_default"
    readarray -t arr_current <<<"$packages_current"
    package_name=$(echo ${arr_current[@]} ${arr_default[@]} | tr ' ' '\n' | tr -d "\r" | sort | uniq -u | awk '{ print substr( $0, 9 ) }');
    echo "--- PACKAGE NAME: "$package_name""
    
    package_data_1=$("$adb" shell dumpsys package "$package_name" 2>&1);
    echo "------------ SUCCESS GETTING INSTALL DATA ------------"
    echo "$package_data_1" >> "$out_name_1"
    
    run=$("$adb" shell monkey -p "$package_name" 1 2>&1);
    #wait 1
    run_check=$("$adb" shell ps | grep "$package_name" 2>&1);
    if [[ "$run_check" == *"$package_name"* ]]; then
        echo "------------ SUCCESS RUNNING ------------"
        
        stop=$("$adb" shell am force-stop "$package_name" 2>&1);
        #wait 1
        stop_check=$("$adb" shell ps | grep "$package_name" 2>&1);
        if [[ "$stop_check" == "" ]]; then
            echo "------------ SUCCESS STOPPING ------------"
            package_data_2=$("$adb" shell dumpsys package "$package_name" 2>&1);
            echo "------------ SUCCESS GETTING RUN DATA ------------"
            echo "$package_data_2" >> "$out_name_2"
        
        else
            echo "------------ ERROR STOPPING ------------"
            error_types+=("STOP")
            error_contents+=("$stop")
        fi
        
    else
        echo "------------ ERROR RUNNING ------------"
        error_types+=("RUN")
        error_contents+=("$run")
    fi
    
    uninstall_apk=$("$adb" uninstall "$package_name" 2>&1);
    if [[ "$uninstall_apk" != *"Success"* ]]; then
        echo "------------ ERROR UNINSTALLING ------------"
        error_types+=("UNINSTALL")
        error_contents+=("$uninstall_apk")
        touch $err ##########################################################
        echo "$file" >> "$bad_apps"
    else
        echo "------------ SUCCESS UNINSTALLING ------------"
    fi
    
else
    echo "------------ ERROR INSTALLING ------------"
    error_types+=("INSTALL")
    error_contents+=("$install_apk")
fi

if (( ${#error_types[@]} != 0 )); then
    error_types_str=""
    for e in "${error_types[@]}"; do
        error_types_str+="$e||"
    done
    error_types_str=${error_types_str%??}
    error_contents_str=""
    for e in "${error_contents[@]}"; do
        error_contents_str+="$e\n******************\n"
    done
    error_contents_str=${error_contents_str%??}
    
    echo "["$error_types_str"] "$file"" >> "$failed_log"
    echo "$error_contents_str" >> "$failed_log"
    echo "--------------------------------------------------" >> "$failed_log"
fi

#touch $err
#echo "#########################################################"
