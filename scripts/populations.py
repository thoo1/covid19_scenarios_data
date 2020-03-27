'''
This script generates the json with the population presets that contain
 * name
 * populationServed
 * initial cases
 * imports
 * hospital beds
 * ICU beds

It should be run from outside the repo as

  python3 covid19_scenarios_data/scripts/make_populations.py

'''

from collections import defaultdict
import csv
import json
import numpy as np
import os
import sys
sys.path.append('..')
from paths import TMP_CASES, BASE_PATH, JSON_DIR, TMP_POPULATION, TMP_CODES

# obsolete
def getImportsPerDay(pop, cases):
    return np.maximum(0.1, 0.00003*np.maximum(pop**0.3,10)*np.maximum(cases,1))

# utility, might be handy in the future. currently no used.
def getCountryAbbreviations():
    toThreeLetter = {}
    toName = {}
    with open(os.path.join(BASE_PATH, TMP_CODES)) as fh:
        header = [x.strip('"') for x in fh.readline().strip().split(',')]
        name_index = header.index('name')
        three_letter_index = header.index('alpha-3')
        for line in fh:
            entries = [x.strip('"') for x in line.strip().split(',')]
            if entries[0]=='SWE':
                print(entries)
            if len(entries) > three_letter_index:
                toThreeLetter[entries[name_index]] = entries[three_letter_index]
                toName[entries[three_letter_index]] = entries[name_index]

    return toThreeLetter, toName

# estimate hemisphere based on country_codes
def getHemispheres():
    toHemisphere = {}
    mn = 'Moderate/North'
    ms = 'Moderate/South'
    eq = 'Moderate/Tropical'
    hemiDict = {}
    # to make this less awkward to fill
    hemiDict[mn]= ['Northern Europe', 'Northern Africa', 'Western Europe', 'Southern Europe', 'Northern America', 'Eastern Europe', 'Eastern Asia', 'Western Asia', 'Central Asia']
    hemiDict[ms]= ['Australia and New Zealand']
    hemiDict[eq]= ['Southern Asia', 'Polynesia', 'Latin America and the Caribbean', 'Melanesia', 'Micronesia', 'Sub-Saharan Africa', 'South-eastern Asia']

    hemiDict2 = {}
    for i in [mn, ms, eq]:
        for j in hemiDict[i]:
            hemiDict2[j] = i
    
    with open(os.path.join(BASE_PATH, TMP_CODES)) as fh:
        header = [x.strip('"') for x in fh.readline().strip().split(',')]
        name_index = header.index('name')
        sub_region_index = header.index('sub-region')
        for entries in  csv.reader(fh, quotechar='"', delimiter=',',
                     quoting=csv.QUOTE_ALL, skipinitialspace=True):        
            if len(entries) > sub_region_index:
                if not entries[name_index] == 'Antarctica': 
                    toHemisphere[entries[name_index]] = hemiDict2[entries[sub_region_index]]

    return toHemisphere

def dumpPopTable(pops, fname):
    with open(fname, 'w') as fh:
        fh.write('\t'.join(['name', 'populationServed', 'ageDistribution', 'hospitalBeds', 'ICUBeds', 'suspectedCaseMarch1st', 'importsPerDay'])+'\n')
        for pop in pops:
            fh.write('\t'.join([pop['name'],
                                str(pop['data']['populationServed']),
                                pop['data']['country'],
                                str(pop['data']['hospitalBeds']),
                                str(pop['data']['ICUBeds']),
                                str(pop['data']['suspectedCasesToday']),
                                str(pop['data']['importsPerDay'])])+'\n')

def loadPopTable(fname):
    pops = []
    with open(fname, 'r') as fh:
        header = fh.readline().strip().split('\t')
        for line in fh:
            entries = line.strip().split('\t')
            tmp = {'name':entries[0], 'data':{}}
            tmp['data']['populationServed'] = int(entries[1])
            tmp['data']['country'] = entries[2]
            tmp['data']['hospitalBeds'] = int(entries[3])
            tmp['data']['ICUBeds'] = int(entries[4])
            tmp['data']['suspectedCasesToday'] = int(entries[5])
            tmp['data']['importsPerDay'] = float(entries[6])
            pops.append(tmp)

    return pops

def getRegions():
    with open(os.path.join(BASE_PATH, JSON_DIR,TMP_CASES)) as fd:
        regions = json.load(fd)
        return set(regions.keys())

def parse():
    pops = loadPopTable(os.path.join(BASE_PATH,"populationData.tsv"))
    popSizes = {d['name']:d['data']['populationServed'] for d in pops}

    regions = getRegions()

    for d in pops:
        d['data']['cases'] = d['name'] if d['name'] in regions else 'none'

    # Set epidemiology based on country_codes
    hemispheres = getHemispheres()    
    for d in pops:
        d['data']['hemisphere'] = hemispheres[d['name']] if d['name'] in hemispheres else 'none'
    

    with open(os.path.join(BASE_PATH, JSON_DIR,TMP_POPULATION), 'w') as fh:
        json.dump(pops, fh)


if __name__ == '__main__':
    parse()
