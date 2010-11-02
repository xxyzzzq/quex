#! /usr/bin/env bash

if [[ $1 == "--hwut-info" ]]; then
    echo "Check if the default configuration has been updated."
    # Use "helper_to_generate_default_configuration.txt" in directory
    #
    #  $QUEX_PATH/quex/code_base/analyzer/configuration/
    #
    # to generate a new default configuration
else
    diff $QUEX_PATH/quex/code_base/analyzer/configuration/TXT \
         $QUEX_PATH/quex/code_base/test_environment/TestAnalyzer-configuration \
    | awk ' ! /QUEX_SETTING_BUILD_DATE/ && (/>/ || /</)'
fi
