#!/usr/bin/env python3
# encoding: utf-8

# quick and dirty script to find the groups of continuous cantos with more
# or less changes in the tradition, according to Barbi's loci

SPAN = 6

# Inferno
barbi = {
    'I' : [
        6, 2, 5, 5, 6, 1, 1, 2, 4, 4,
        6, 4, 4, 4, 2, 5, 5, 3, 3, 0,
        5, 2, 1, 3, 4, 3, 4, 2, 3, 5,
        2, 1, 4, 4],
    'P' : [
        6, 8, 3, 4, 4, 5, 6, 3, 3, 2,
        5, 7, 7, 3, 1, 3, 3, 6, 5, 5,
        3, 7, 8, 5, 5, 3, 5, 5, 5, 5,
        1, 4, 4],
    'Z' : [
        6, 3, 4, 4, 8, 1, 5, 3, 3, 4,
        2, 1, 1, 6, 1, 5, 3, 4, 2, 2,
        1, 4, 7, 6, 3, 7, 3, 5, 4, 6,
        7, 1, 8],
}

for cantica in sorted(barbi):
    for i in range(len(barbi[cantica])-SPAN+1):
        num_loci = sum(barbi[cantica][i:i+SPAN])
        print(cantica, i, i+SPAN, barbi[cantica][i:i+SPAN], num_loci)

