#!/usr/bin/env python3
# encoding: utf-8

import copy
import glob
import logging
import json
import os.path

# map for the 'canto' variable, to make sure the order is kept with sort()
CANTICA = {'IN' : 'I',
           'PU' : 'P',
           'PA' : 'Z'
          }

# in-point diverse readings in Leonardi
LEONARDI = {
    'I_01_117_0' : 'che la',
    'I_03_008_5' : 'eterna duro',
    'I_14_048_8' : 'maturi',
    'I_15_004_0' : 'Quali i Fiaminghi',
    'I_15_007_1' : 'quali i Padoan',
    'I_16_102_1' : 'douria',
    'I_17_024_3' : 'che di pietra',
    'I_17_024_4' : 'il sabbion',
    'I_26_014_2' : 'auean',
    'I_26_014_3' : 'fatto',
    'I_26_014_4' : 'i borni',
    'I_32_109_3' : 'tu',
    'P_02_044_2' : 'parea beato per iscritto',
    'P_02_108_6' : 'voglie',
    'P_09_054_3' : 'ond e la giu addorno',
    'P_11_129_4' : 'la',
    'P_20_093_0' : 'porta nel Tempio',
    'P_24_036_5' : 'voler',
    'P_25_095_0' : 'in',
    'P_25_095_3' : 'che',
    'P_30_073_1' : 'ben sem ben sem',
    'P_30_095_1' : 'compatire',
    'Z_01_048_0' : 'aquila',
    'Z_03_015_3' : 'tosto',
    'Z_13_018_5' : 'prima',
    'Z_15_036_3' : 'gratia',
    'Z_17_042_3' : 'corrente',
    'Z_21_130_6' : 'i rincalzi',
    'Z_27_100_3' : 'vicissime',
    'Z_31_020_2' : 'plenitudine',
}

def read_data(maxfiles, in_path, include_leo=True, descripti=[]):
    ret = {
        'chars' : {},
        'witnesses' : set(), # LEO not in raw data
    }

    # whether to append LEOnardi
    if include_leo:
        ret['witnesses'].add('LEO')

    # iterate over all json filenames, up to `maxfiles`
    filenames = glob.glob('%s/*.json' % in_path)
    for filename in sorted(filenames[:maxfiles]):
        # extract cantica, canto and verso info
        bname = os.path.basename(filename).split('.')[0]
        canto, cantica, verso = bname.split('_')

        # parse json
        logging.info("Parsing %s...", filename)
        with open(filename) as json_handler:
            data = json.load(json_handler)

            # iterate over all characters (in phylogenetics parlance, usually
            # textual words) for the current verse
            for i, character in enumerate(data):
                # create matrix of results
                label = '%s_%s_%s_%s' % (CANTICA[canto], cantica, verso, i)

                states = {}
                for state in character:
                    # correct omissions and gaps
                    if state in ['*om.**', ' *om.** ']:
                        state_norm = '{{?}}'
                    elif state == '_':
                        state_norm = '{{-}}'
                    else:
                        state_norm = fix_state_label(state)

                    # add to current list of states
                    states[state_norm] = character[state]

                    # append all non-descripti witnesses
                    for l in states:
                        for w in states[l]:
                            if w not in descripti:
                                ret['witnesses'].add(w)

                # add LEOnardi, defaulting to PETrocchi
                if include_leo:
                    if label in LEONARDI:
                        leo_label = fix_state_label(LEONARDI[label])
                        states[leo_label].append('LEO')
                    else:
                        for pet_label in states:
                            if 'PET' in states[pet_label]:
                                states[pet_label].append('LEO')

                # add to returned data
                ret['chars'][label] = states

    return ret

def output_data(data, out_file, descripti=[], extra_data=None):
    # sorted list of characters
    chars = sorted(data['chars'])

    # collect additional data, witness->statelabel readings
    readings = {}
    for ch in chars:
        # build witness -> text for this char, first attested readings...
        readings[ch] = {}
        for k, v in data['chars'][ch].items():
            for w in v:
                readings[ch][w] = k

        # ...then, non attested, using defaults, test all witnesses
        for w in data['witnesses']:
            if w not in readings[ch]:
                # when there is a missing witness, separate the manuscript
                # from the revision and try them in order
                manuscript = w.split('-')[0]

                if manuscript in readings[ch]:
                    # try the base name first (e.g., 'Ash-c2'->'Ash')
                    lesson = readings[ch][manuscript]
                    readings[ch][w] = lesson
                    if lesson != '{{?}}':
                        data['chars'][ch][lesson].append(w)
                elif manuscript+'-orig' in readings[ch]:
                    # try '-orig' (e.g., 'Ash'->'Ash-orig'; 'Ash-c2'->'Ash')
                    lesson = readings[ch][manuscript+'-orig']
                    readings[ch][w] = lesson
                    if lesson != '{{?}}':
                        data['chars'][ch][lesson].append(w)
                elif manuscript+'-c1' in readings[ch]:
                    # try the first hand (should only get here if there are
                    # problems in data)
                    lesson = readings[ch][manuscript+'-c1']
                    readings[ch][w] = lesson
                    if lesson != '{{?}}':
                        data['chars'][ch][lesson].append(w)
                else:
                    # default to missing
                    readings[ch][w] = '{{?}}'
                    logging.warning('missing data: in %s char %s', w, ch)

    # remove descripti states (if provided)
    if descripti:
        # remove descript from all states
        for char in chars:
            # casting to list to avoid the 'dictionary changed size
            # during iteration' error
            for state in list(data['chars'][char]):
                data['chars'][char][state] = \
                    [w for w in data['chars'][char][state] if w not in descripti]

                # remove all empty states
                if len(data['chars'][char][state]) == 0:
                    del data['chars'][char][state]

    # sorted manuscripts' names
    witnesses = sorted([w for w in data['witnesses'] if w not in descripti])
    taxon_labels = ' '.join([w.replace('-', '_') for w in witnesses])

    # collect additional data, state labels, number of states
    state_labels = {}    
    max_states = 0
    for char in chars:
        states = data['chars'][char].keys()
        states = [s for s in states if s not in ['{{?}}', '{{-}}']]

        state_labels[char] = sorted(states)

        if len(states) > max_states:
            max_states = len(states)

    symbols_str = ' '.join([str(v) for v in range(max_states+1)])

    # output data
    nexus = open(out_file, 'w')

    nexus.write('#NEXUS\n\n')

    nexus.write('BEGIN TAXA;\n')
    nexus.write('\tDIMENSIONS NTAX=%i;\n' % len(witnesses))
    nexus.write('\tTAXLABELS\n')
    nexus.write('\t\t%s\n' % taxon_labels)
    nexus.write('\t;\n')
    nexus.write('END;\n\n')

    print(out_file, 'taxa', len(witnesses), taxon_labels)

    nexus.write('BEGIN CHARACTERS;\n')
    nexus.write('\tDIMENSIONS  NCHAR=%i;\n' % len(chars))
    nexus.write('\tFORMAT DATATYPE=STANDARD GAP=- MISSING=? ')
    nexus.write('SYMBOLS="%s";\n' % symbols_str)

    print(out_file, 'characters', len(chars), symbols_str)

    nexus.write('\tCHARSTATELABELS\n')
    for c_idx, char in enumerate(chars):
        sl_str = ' '.join(state_labels[char])
        nexus.write('\t\t%i %s / %s ,\n' % (c_idx+1, char, sl_str))
    nexus.write('\t;\n')

    nexus.write('\tMATRIX\n')
    for witness in witnesses:
        state_buffer = ''
        for char in chars:
            r = readings[char][witness]
            if r in ['{{?}}', '{{-}}']:
                s = r[2]
            else:
                s = str(state_labels[char].index(r))

            state_buffer += s

        # output buffer 
        nexus.write('\t%s  %s\n' % (witness.replace('-', '_'), state_buffer))

        print(out_file, witness, len(state_buffer), state_buffer[:10])


    # end of matrix
    nexus.write(';\nEND;\n\n')

    if extra_data:
        nexus.write('\n')
        nexus.write(extra_data)
        nexus.write('\n')

    nexus.close()


def read_data2(maxfiles, in_path):
    ret = {
        # matrix with the state for every char for every witness;
        # 'LEO'nardi, which is added internally by the descript, is appended
        # here
        'matrix' : { 'LEO':{} },
        # dictionary of char descriptions
        'char_desc' : {},
        # global maximum number of states
        'max_states' : 0,
        # characters with a single state
        'single_states' : 0,
    }

    # iterate over all json filenames, up to `maxfiles`
    filenames = glob.glob('%s/*.json' % in_path)
    for filename in sorted(filenames[:maxfiles]):
        # extract cantica, canto and verso info
        bname = os.path.basename(filename).split('.')[0]
        canto, cantica, verso = bname.split('_')

        # parse json
        logging.info("Parsing %s...", filename)
        with open(filename) as json_handler:
            data = json.load(json_handler)

            # iterate over all characters (in phylogenetics parlance, usually
            # textual words) for the current verse
            for i, character in enumerate(data):
                # create matrix of results
                label = '%s_%s_%s_%s' % (CANTICA[canto], cantica, verso, i)
                ret['char_desc'][label] = {}

                # iterate over all states for current character
                state_counter = 0
                for state in character:
                    # correct omissions and gaps
                    if state in ['*om.**', ' *om.** ']:
                        state_label = '-'
                        state_descr = '(omission)'
                    elif state == '_':
                        state_label = '?'
                        state_descr = '(lacuna)'
                    else:
                        state_label = str(state_counter)
                        state_descr = state

                        state_counter += 1

                    # update char description
                    ret['char_desc'][label][state_label] = state_descr

                    # update witnesses lessons
                    for witness in character[state]:
                        # create witness entry, if none; leonardi is
                        # a special case
                        if witness not in ret['matrix']:
                            ret['matrix'][witness] = {}

                        # add the state
                        ret['matrix'][witness][label] = state_label

                # add transcription for 'LEO'nardi, defaulting to
                # 'PET'rocchi
                if label not in LEONARDI:
                    ret['matrix']['LEO'][label] = ret['matrix']['PET'][label]
                else:
                    for k, v in ret['char_desc'][label].items():
                        if v == LEONARDI[label]:
                            ret['matrix']['LEO'][label] = k

                # update the maximum number of states, if needed
                if len(ret['char_desc'][label]) > ret['max_states']:
                    ret['max_states'] = len(ret['char_desc'][label])

                # update the counter of single states, if applicable;
                # states with omissions and gaps are *not* included here
                if len(ret['char_desc'][label]) == 1:
                    ret['single_states'] += 1

    return ret

def fix_state_label(label):
    # simple fixes
    label = label.replace(' ', '_')
    label = label.replace('**', ']')
    label = label.replace('*', '[')

    # manually fix unicode escape problems - as there is no consistency in
    # some transcriptions, this needs to be performed "by hand" on all
    # escaped points
    REPLACES = [
        ['&middot;', '·'],
        ['&ugrave;', 'ù'],
        ['&ograve;', 'ò'],
        ['&#x0303;', '~'], # replacing but normal (not combining) tilde
        ['&#x00F5;', 'õ'],
        ['&#x0103;', 'ă'],
        ['&nbsp;', '_'],   # replacing by underscore, as spaces are separators
        ['&#x014D;', 'ō'],
        ['&#x016B;', 'ū'],
        ['&#x012B;', 'ī'],
        ['&#xF145;', 'm'], # error in the trancription
        ['&#x0113;', 'ē'],
        ['&#x0304;', '-'], # replacing combining macro
        ['&#xF147;', '[p]'], # error in trascription, Z_28_055_5
    ]

    for replace in REPLACES:
        label = label.replace(replace[0], replace[1])

    return label

def output_data2(data, out_file, tree_str=None):
    # sorted manuscripts' names
    witnesses = sorted(data['matrix'].keys())

    # sorted list of characters
    chars = sorted(data['char_desc'])

    # sorted list of characters with more than one state (for output)
    out_chars = [c for c in chars if len(data['char_desc'][c]) > 1]

    # adapt labels for NEXUS
    taxon_labels = ' '.join([w.replace('-', '_') for w in witnesses])
    symbols_str = ' '.join([str(v) for v in range(data['max_states']+1)])
    n_char = len(out_chars) #len(data['char_desc']) - data['single_states']

    # output data
    nexus = open(out_file, 'w')

    nexus.write('#NEXUS\n\n')

    nexus.write('BEGIN TAXA;\n')
    nexus.write('\tDIMENSIONS NTAX=%i;\n' % len(witnesses))
    nexus.write('\tTAXLABELS\n')
    nexus.write('\t\t%s\n' % taxon_labels)
    nexus.write('\t;\n')
    nexus.write('END;\n\n')

    nexus.write('BEGIN CHARACTERS;\n')
    nexus.write('\tDIMENSIONS  NCHAR=%i;\n' % n_char)
    nexus.write('\tFORMAT DATATYPE=STANDARD GAP=- MISSING=? ')
    nexus.write('SYMBOLS="%s";\n' % symbols_str)

    nexus.write('\tCHARSTATELABELS\n')
    for c_idx, char_label in enumerate(out_chars):
        # extract an ordered list of states for the currenct character
        # (so that we will write them in order), excluding gaps and missing
        # data
        states = [s for s in data['char_desc'][char_label].keys()]
        states = sorted([s for s in states if s not in ['-', '?']])

        # extract the text for all states collected above and build a list
        # of them, replacing white spaces by underscores (as the space is
        # used as delimiter by the NEXUS format here) and other fixes
        state_labels = [data['char_desc'][char_label][s] for s in states]
        state_labels = ' '.join([fix_state_label(l) for l in state_labels])

        nexus.write('\t\t%i %s / %s ,\n' % (c_idx+1, char_label, state_labels))
    nexus.write('\t;\n')

    nexus.write('\tMATRIX\n')
    for witness in witnesses:
        # build buffer
        w_states = ''
        for char in out_chars:
            if char not in data['matrix'][witness]:

                # when there is a missing witness, separate the manuscript
                # from the revision and try them in order
                manuscript = witness.split('-')[0]

                solved = False

                if manuscript+'-orig' in witnesses:
                    # try 'orig' first
                    if char in data['matrix'][manuscript+'-orig']:
                        w_states += data['matrix'][manuscript+'-orig'][char]
                        solved = True

                if not solved and manuscript in witnesses:
                    # try non revised manuscript
                    if char in data['matrix'][manuscript]:
                        w_states += data['matrix'][manuscript][char]
                        solved = True

                if not solved:
                    w_states += '?'
                    logging.warning('missing data: in %s char %s', witness, char)

            else:
                w_states += data['matrix'][witness][char]

        # output buffer
        nexus.write('\t%s  %s\n' % (witness.replace('-', '_'), w_states))
    # end of matrix
    nexus.write(';\nEND;\n\n')

    if tree_str:
        nexus.write('\n\n')
        nexus.write(tree_str)
        nexus.write('\n\n')

    nexus.close()

def tonexus(maxfiles=None, in_path='data/transcription', out_path='data'):
    # read all data and output
    data = read_data(maxfiles, in_path, include_leo=True)
    output_data(data, '%s/tresoldi.nex' % out_path)

    # set descripti, read new data and output reduced
    descripti = [
        'Urb-orig', 'Urb-c1', 'Urb-c2',
        'Rb-orig', 'Rb-c1', 'Rb-c2',
        'Ash-orig', 'Ash-c1', 'Ash-c2',
        'Ham-orig', 'Ham-c1', 'Ham-c2',
        'Mart-orig', 'Mart-c1', 'Mart-c2-1',
        'LauSC-orig', 'LauSC-c1', 'LauSC-c2', 'LauSC-c3', 'LauSC-c4',
        'Triv-orig', 'Triv-c1', 'Triv-c2',
        'PET', 'FS', 'LEO',]

    trees_str = """
BEGIN Trees;
[TREES]
[1] tree 'Tresoldi'=[&R] ((Rb, Urb),((Ash,Ham),((Triv,Mart,Mart_c2),LauSC)));
[2] tree 'MLConsensus'= (Ash:0.0607261009,Ham:0.0645408745,(((LauSC:0.0452406511,(Mart_c2:0.0119671012,Triv:0.0186266738)100:0.0181080000)100:0.0103620000,Mart:0.0314127045)100:0.0101870000,(Rb:0.0488919584,Urb:0.0304592422)100:0.0093700000)100:0.0158500000);
END; [Trees]
"""

    red_data = read_data(maxfiles, in_path, False, descripti)
    output_data(red_data, '%s/tresoldi_red.nex' % out_path, [], trees_str)

    # output inferno reduced
    inferno = copy.deepcopy(red_data)
    inferno['chars'] = \
        dict((k,v) for k, v in inferno['chars'].items() if k[0] == 'I')
    output_data(inferno, '%s/tresoldi_red.I.nex' % out_path, [], trees_str)

    # output purgatorio reduced
    purgatorio = copy.deepcopy(red_data)
    purgatorio['chars'] = \
        dict((k,v) for k, v in purgatorio['chars'].items() if k[0] == 'P')
    output_data(purgatorio, '%s/tresoldi_red.P.nex' % out_path, [], trees_str)

    # output paradiso reduced
    paradiso = copy.deepcopy(red_data)
    paradiso['chars'] = \
        dict((k,v) for k, v in paradiso['chars'].items() if k[0] == 'Z')
    output_data(paradiso, '%s/tresoldi_red.Z.nex' % out_path, [], trees_str)

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL) # DEBUG
    tonexus()

