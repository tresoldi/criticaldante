#!/usr/bin/env python3
# encoding: utf-8

# Reads data from Prue Shaw's NEXUS files and adapt according to our needs
#
# About data from Shaw and Robinson from the AHRC Commedia project, as
# described in the "Phylogenetic Analysis" section of the editorial matter of
# the publication -- and detailed at http://sd-editions.com/commedia/data/ --
# we have:
#
#   - The file M2R1L0.nex including Martini's collations (labelled "Mart-c2"
#     or "M2" in their terminology) in preference to those of the original
#     Aldine edition; the corrections of the "c1" scribe of Rb ("Rb-c1" or
#     "R1": in fact, the original scribe correcting his own work) in preference
#     to the original readings in that manuscript; and the original readings
#     of LauSC ("LauSC-orig" or "L0") and of all other witnesses;
#   - The file M2R1L2.nex also includes the Martini collations ("M2") and the
#     corrections by the original hand in Rb ("R1"), but instead of the
#     original readings includes the corrections by the second hand in
#     LauSC ("LauSC-c2" or "L2");
#   - The file M0R1L0.nex includes the original text of the Aldine edition,
#     the corrections by the original hand in Rb ("R1"), and the original
#     readings in LauSC.
#
# There are many things to consider about the format, in particular that
# the various loci ("words") are stored as taxa, when the manuscripts
# are stored as characters (it should be the opposite)

import logging
#from nexus import NexusReader

# TODO: check 'Absent' for gap
# TODO: check when form starts with an empty string ' a b', which is
#       probably always an indication of gap/omission

# map for the 'canto' variable, to make sure the order is kept with sort()
CANTICA = {'IN' : 'I',
           'PU' : 'P',
           'PA' : 'Z'
          }

def clean_line(line):
    line = line.replace('\t', '')
    line = line.replace('\n', '')

    return line

# fix labels used by Shaw and Robinson so they can be sorted easily
def fix_label(label):
    fields = label.split('_')
    cantica = CANTICA[fields[1][:2]]
    canto = int(fields[1][2:])
    verso = int(fields[2])
    parola = int(fields[3])

    return '{}_{:02d}_{:03d}_{:03d}'.format(cantica, canto, verso, parola)

def read_shaw_nexus(filename):
    # reading line by line, as files are rather large and python nexus
    # libraries (such as Simon Greenhill's one) are failing (maybe the
    # format of the data is not adequate)
    logging.info("Parsing %s...", filename)

    # where we are in the file
    part = None

    # data from the nexus file
    states = {}
    taxa = []
    matrix = {}
    single_states = []

    # method for reading the different parts of the nexus file
    with open(filename) as nexus:
        for line in nexus:
            # check if we are in a new part
            if 'STATELABELS' in line:
                # around line 20
                part = 'STATELABELS'
            elif 'TAXLABELS' in line:
                # around line 90000
                part = 'TAXLABELS'
            elif 'MATRIX' in line:
                # around line 90000; this is stored after the TAXLABELS,
                # so that we can initialize the matrix of witnesses
                # appropriately
                part = 'MATRIX'

                for taxon in taxa:
                    matrix[taxon] = ''
            elif 'endblock' in line:
                # at the bottom of the file, mostly
                part = None

            # parse according to `part`
            if part == 'STATELABELS':
                # clean line and split
                line = clean_line(line)
                fields = line.split(' ', 2)

                # skip noisy lines
                if len(fields) == 3:
                    # we are only storing label and form, as the index
                    # will be kept from the position in the list
                    index, label, form = fields
                    label = fix_label(label)

                    states[label] = { 'form' : form }

            elif part == 'TAXLABELS':
                # clean line and split
                line = clean_line(line)
                fields = line.split(' ', 2)

                # skip noisy lines
                if len(fields) == 2:
                    # we are only storing the name of the taxa, as the
                    # index will be kept from the position in the list
                    index, taxon_name = fields

                    taxa.append(taxon_name)

            elif part == 'MATRIX':
                # clean line and split
                line = clean_line(line)
                fields = line.split(' ', 3)

                # skip noisy lines
                if len(fields) == 3:
                    index, label, data = fields
                    label = fix_label(label)

                    # store the properties
                    for i, char in enumerate(data):
                        taxon = taxa[i]
                        matrix[taxon] += char

                    # check single states  and collect a list of them
                    n_states = len(set(data))
                    states[label]['n_states'] = n_states
                    if n_states == 1:
                        single_states.append(label)

    # return value
    ret = {
        'states' : states,
        'matrix' : matrix,
        'single_states' : single_states,
    }

    return ret

def compare_matrices(m2r1l0, m2r1l2, m0r1l0):
    # compare to make sure all are equal as expected
    for wit in m2r1l0['matrix']:
        if wit in m2r1l2['matrix']:
            if m2r1l0['matrix'][wit] != m2r1l2['matrix'][wit]:
                logging.warning('%s is different in m2r1l0 and m2r1l2', wit)

        if wit in m0r1l0['matrix']:
            if m2r1l0['matrix'][wit] != m0r1l0['matrix'][wit]:
                logging.warning('%s is different in m2r1l0 and m0r1l0', wit)

    for wit in m2r1l2['matrix']:
        if wit in m0r1l0['matrix']:
            if m2r1l2['matrix'][wit] != m0r1l0['matrix'][wit]:
                logging.warning('%s is different in m2r1l2 and m0r1l0', wit)

def extract_matrix(data, state_names):
    # compare all witnesses; the `reference` is just a random
    # manuscript used for the comparison and identification of single states
    witnesses = list(data.keys())
    reference = witnesses[0]

    # initialize witnesses' and state matrices
    ret = {
        'taxa' : dict.fromkeys(witnesses, ''),
        'states' : [],
        'max_states' : 0,
    }

    for char_idx in range(len(data[reference])):
        # compare all witnesses with the first one in the list, as we will
        # only have a single state if all are equal; we are actually
        # comparing the reference with itself, it makes the code simpler
        ref_state = data[reference][char_idx]
        single_state = True
        for witness in witnesses:
            if data[witness][char_idx] != ref_state:
                logging.debug('different state in %s (#%i - %s)',
                    witness, char_idx, state_names[char_idx])
                single_state = False
                break

        # only append non single state chars
        if not single_state:
            ret['states'].append(state_names[char_idx])

            states = set()
            for witness in witnesses:
                state = data[witness][char_idx]

                ret['taxa'][witness] += state

                if state not in ['?', '-']:
                    states.add(state)

            # count the number of states, excluding gaps and missing, for
            # keeping track of global maximum
            num_states = len(states)
            if num_states > ret['max_states']:
                ret['max_states'] = num_states

    return ret

def output_nexus(data):
    taxa = sorted(list(data['taxa']))
    taxlabels = ' '.join(taxa)
    nchar = len(data['taxa']['Ash'])
    symbols = ' '.join([str(v) for v in range(data['max_states'])])

    with open('data/shaw.nex', 'w') as nexus:
        nexus.write('#NEXUS\n\n')

        nexus.write('BEGIN TAXA;\n')
        nexus.write('\tDIMENSIONS NTAX=%i;\n' % len(taxa))
        nexus.write('\tTAXLABELS\n')
        nexus.write('\t\t%s;\n' % taxlabels)
        nexus.write('END;\n\n')

        nexus.write('BEGIN CHARACTERS;\n')
        nexus.write('\tDIMENSIONS NCHAR=%i\n;' % nchar)
        nexus.write('\tFORMAT DATATYPE = STANDARD GAP = - MISSING = ? ')
        nexus.write('SYMBOLS = "%s";\n' % symbols)
        nexus.write('\tCHARSTATELABELS\n')
        buf = []
        for i, state in enumerate(data['states']):
            buf.append('%i %s' % (i+1, state))
        nexus.write('\t\t%s;\n' % ', '.join(buf))

        nexus.write('\tMATRIX\n')
        for taxon in taxa:
            nexus.write('\t%s %s\n' % (taxon, data['taxa'][taxon]))
        nexus.write(';\n') # end of matrix            

        nexus.write('END;\n\n')

def main():
    # read data and rename keys (witnesses) accordingly
    m2r1l0 = read_shaw_nexus('data/M2R1L0.nex')
    m2r1l0['matrix']['M2'] = m2r1l0['matrix'].pop('Mart')
    m2r1l0['matrix']['R1'] = m2r1l0['matrix'].pop('Rb')
    m2r1l0['matrix']['L0'] = m2r1l0['matrix'].pop('LauSC')

    m2r1l2 = read_shaw_nexus('data/M2R1L2.nex')
    m2r1l2['matrix']['M2'] = m2r1l2['matrix'].pop('Mart')
    m2r1l2['matrix']['R1'] = m2r1l2['matrix'].pop('Rb')
    m2r1l2['matrix']['L2'] = m2r1l2['matrix'].pop('LauSC')

    m0r1l0 = read_shaw_nexus('data/M2R1L0.nex')
    m0r1l0['matrix']['Ald'] = m0r1l0['matrix'].pop('Mart')
    m0r1l0['matrix']['R1']  = m0r1l0['matrix'].pop('Rb')
    m0r1l0['matrix']['L0']  = m0r1l0['matrix'].pop('LauSC')

    # check if entries are equal, as expected
    compare_matrices(m2r1l0, m2r1l2, m0r1l0)

    # join matrices and extract non-single states into `new_data`
    commedia = {**m2r1l0['matrix'], **m2r1l2['matrix'], **m0r1l0['matrix']}
    state_names = sorted(list(m2r1l0['states'].keys()))
    new_data = extract_matrix(commedia, state_names)

    # output new file
    output_nexus(new_data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

