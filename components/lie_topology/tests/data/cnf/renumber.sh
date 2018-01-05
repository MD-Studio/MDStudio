#! /bin/bash

grep . $1 | awk 'BEGIN{ i=1 }{ if (NF != 7 ){ print $0 }else{ printf "%5i %-4s %4s %8i %14.9f %14.9f %14.9f\n", $1, $2, $3, i, $5, $6, $7; i+=1 } }' 
