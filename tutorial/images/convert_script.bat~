#!/bin/bash 

for i in *.png; 
do 
j=${i//\.png/}; 
convert -scale 50% $i ${j}_small.png;
done
mv *_small.png smaller
