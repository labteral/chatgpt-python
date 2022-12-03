#!/bin/bash
read -ep "Package name: " PACKAGE
read -ep "Package description: " DESCRIPTION
read -ep "Package URL: " URL
echo $URL
read -ep "Author name [Rodrigo Martínez Castaño]: " AUTHOR
AUTHOR=${AUTHOR:-"Rodrigo Martínez Castaño"}

read -ep "Author email [rodrigo@martinez.gal]: " EMAIL
EMAIL=${EMAIL:-"rodrigo@martinez.gal"}

sed -i "s~package_name~$PACKAGE~" package_name/__init__.py 
mv package_name/package_name.py package_name/$PACKAGE.py
mv package_name $PACKAGE
sed -i "s~package_name~$PACKAGE~g" setup.py
sed -i "s~description_value~$DESCRIPTION~g" setup.py
sed -i "s~url_value~$URL~g" setup.py
sed -i "s~author_value~$AUTHOR~g" setup.py
sed -i "s~email_value~$EMAIL~g" setup.py

rm rename.sh
