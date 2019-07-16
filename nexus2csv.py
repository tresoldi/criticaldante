# encoding: utf-8

"""
A quick&dirty script to convert the NEXUS data to a CSV format.

This allows to play with BEASTling and inspect with more ease.
"""

def main():
    # Read the entire contents as lines
    filename = "data/tresoldi.nex"
    with open(filename) as handler:
        lines = [line.strip() for line in handler]

    # Collect char state labels
    labels_start = ["CHARSTATELABELS" in line for line in lines]
    line_idx = labels_start.index(True) + 1
    labels = []
    while True:
        fields = lines[line_idx].strip().split()
        if fields[0] == ";":
            break

        labels.append(fields[1])
        line_idx += 1

    # identify where the matrix starts and collect the vectors, char
    # lists are separated by two spaces
    matrix_start = ["MATRIX" in line for line in lines]
    vectors = lines[matrix_start.index(True)+1:-2]

    with open("data/dante_chars.csv", "w") as handler:
        handler.write("Taxon\tCharacter\tValue\n")

        for vector in vectors:
            taxon, chars = vector.split(" ", 1)
            chars = chars[1:]
            for char_label, char_value in zip(labels, chars):
                handler.write("%s\t%s\t%s\n" % (taxon, char_label, char_value))

if __name__ == "__main__":
    main()
