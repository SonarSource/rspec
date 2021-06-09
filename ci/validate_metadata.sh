# Validate metadata
cd rspec-tools
pipenv install
pipenv run rspec-tools validate-rules-metadata
if [[ $? -ne 0 ]]; then
  exit 1
fi
