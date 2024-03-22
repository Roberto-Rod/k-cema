#!/bin/bash
for i in `find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.txt" \)`; do    sed -i 's/\r//' $i ; done
