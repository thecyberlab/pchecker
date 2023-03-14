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
package_data_0=$("$aapt" dump badging "$file" 2>&1);
echo "------------ SUCCESS GETTING METADATA ------------"
echo "$package_data_0" >> "$out_name_0"
