#!/bin/bash 

for i in *.png; 
do 
j=${i//\.png/}; 
convert -scale 50% $i ${j}_small.png;
done
mv *_small.png smaller

for i in *.jpg;
do
j=${i//\.jpg/};
convert -scale 50% $i ${j}_small.jpg;
done
mv *_small.jpg smaller
