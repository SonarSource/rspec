#!/bin/sh

# Create the new Rule in a branch
# It is used by the Github Action script "create_new_rspec.yml".

# Stop script in case of error.
set -e

RSPEC_ID=$1
LANGUAGES=$2
RULES_DIRECTORY=$3

scripts_dir=$(dirname "$0")
template_dir="${scripts_dir}/rspec_template"
rule_directory="${RULES_DIRECTORY}/S${RSPEC_ID}"

mkdir $rule_directory
cp $template_dir/common/* $rule_directory/

for language in $(echo $LANGUAGES | sed "s/,/ /g")
do
    mkdir $rule_directory/$language
    cp $template_dir/language_specific/* $rule_directory/$language/
done

cd $rule_directory

grep -rl '${RSPEC_ID}' . | xargs sed -i "s/\${RSPEC_ID}/${RSPEC_ID}/g"