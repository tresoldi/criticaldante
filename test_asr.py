#!/usr/bin/env python3
# encoding: utf-8

# read data from Mesquite's ASR and compare to a gold standard

import transcription2nexus as t2n

WITNESSES = ['Rb', 'Urb', 'Ash', 'Ham', 'Triv', 'Mart', 'Mart c2', 'LauSC']

def read_asr_data(filename):
    ancestor_states = []
    info_states = 0 # number of informtive states

    with open(filename) as handler:
        in_matrix = False
        for line in handler:
            line = line.rstrip()

            if line.startswith('Char.'):
                witnesses_str = line[len('Char.\\Node\t'):]
                witnesses = witnesses_str.split('\t')
                in_matrix = True
                continue

            if in_matrix:
                if line == '':
                    continue
                fields = line.split('\t')
                char, states = fields[0], fields[1:]

                # character number
                char_idx = int(char.split(' ')[1])

                # whether all elements in 'states' are equal (i.e., if the
                # character is informative)
                char_info = all(x==states[0] for x in states)
                if char_info is False:
                    info_states += 1

                # the last state is the ancestor
                ancestor = states[-1]

                # list of witnesses with the states equal to the ancestor
                # (most times, only one state)
                char_ancestor_states = []

                for state in ancestor.split(' '):
                    # look for a witness with the same state, provided it is
                    # not a reconstructed state (i.e., it is a witness)
                    same_state = None
                    for W in WITNESSES:
                        w_idx = witnesses.index(W)
                        if states[w_idx] == state:
                            char_ancestor_states.append(W.replace(' ', '_'))
                            break

                # returned list
                ancestor_states.append([char_info, char_ancestor_states])

                #print(char, [char_idx], states, char_ancestor_states)

    return ancestor_states, info_states

def test_similarity(asr, nexus, info_states):
    chars = sorted(nexus['chars'])

    # states with right and wrong countings, with one or more than one
    # alterntive
    right_single, right_multi = 0, 0
    wrong_single, wrong_multi = 0, 0

    for i, char in enumerate(chars):
        # check all witnesses
        pet_in_wit = []

        for w in asr[i][1]:
            # collect all manuscripts with a reported lesson, adding '-c2', '-c1',
            # and '-orig', in this order, to it if available when the manuscript 
            # reading is not reported
            all_w = [v for v in nexus['chars'][char].values()]
            all_w = [w for sublist in all_w for w in sublist]
            if w not in all_w:
                if w+'-c2' in all_w:
                    w += '-c2'
                elif w+'-c1' in all_w:
                   w += '-c1'
                else:
                    w += '-orig'

            # if the label is '{{?}}', there is an omission in the manuscript and
            # the ancestral state was reconstructed accondingly
            if '{{?}}' in nexus['chars'][char]:
                if w in nexus['chars'][char]['{{?}}']:
                    pet_in_wit.append(True)

            # identify if state label with witness also includes the reference
            for label in nexus['chars'][char]:
                if w in nexus['chars'][char][label]:
                    if 'PET' in nexus['chars'][char][label]:
                        pet_in_wit.append(True)
                    else:
                        pet_in_wit.append(False)


        if True in pet_in_wit:
            # count right reconstructions with one or more than one option
            if len(pet_in_wit) == 1:
                right_single += 1
            else:
                right_multi += 1
        else:
            if len(pet_in_wit) == 1:
                wrong_single += 1
            else:
                wrong_multi += 1

    # report results
    print('informative states / all states', info_states, len(asr))
    print('right (single/multi)', right_single, right_multi)
    print('wrong (single/multi/sum)', wrong_single, wrong_multi,
        wrong_single+wrong_multi)
    print('score (single+multi)',
        1.0 - ((wrong_single+wrong_multi) / float(info_states)) )    

if __name__ == '__main__':
    ASR_FILE = 'data/asr_tree_tresoldi.txt'
#    ASR_FILE = 'data/asr_tree_mlconsensus.txt'

    # read ASR data
    ancestor_states, info_states = read_asr_data(ASR_FILE)

    # rebuild NEXUS data
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

    nexus = t2n.read_data(None, 'data/transcription', False, descripti)

    # finally test
    test_similarity(ancestor_states, nexus, info_states)

