#!/usr/bin/python

import re
import sys
import argparse

from ClassDfn import Relation, Relationship
from ClassDfn import Cardinality, ForeignKey
from ClassDfn import repr_cardinality, repr_keys, repr_indi_key

from Translator import Translator

TBL_PAT = r'(?P<name>\w+)\((?P<attributes>[a-zA-Z0-9, ]+)\)$'
IND_PAT = r'(?P<lrel>\w+)\((?P<latt>.*)\) <= (?P<rrel>\w+)\((?P<ratt>.*)\)$'
KEY_PAT = r'(?P<name>\w+):[ ]*(?P<keys>.*)$'

INDIVIDUAL_KEY_PAT = r'\((?P<attr>.+)\)'

renderPath='/var/www/CS4221/render/'
renderURL='http://localhost/CS4221/render'
uploadPath='/var/www/CS4221/upload/'

print "Content-type:text/html\r\n\r\n"
print '<html>'
print '<head>'
print '<title>Translate To ER Diagram</title>'
print '</head>'
print '<body>'
print '<h1>Step 3:Translate the Relational Database</h1>'
print '<p> Please make sure the following variables are correct.If any of these variables are incorrect, please modify them in the translate.py</p>'
print '<p>The render folder path:'+renderPath+'<br>'
print 'The render URL path:'+renderURL+'<br>'
print 'The upload folder path:'+uploadPath+'</p>'
def read_inputs(input_file):
    # get the relational table schema and INDs
    # from input_file
    infile = open(input_file)
    line = None
    relations = {}

    try:
        while True:
            line = next(infile).strip()

            # match table pattern
            matches = re.match(TBL_PAT, line)
            if matches is not None:
                name       = matches.group('name')
                attributes = frozenset([c.strip() for c in matches.group('attributes').split(',')])
                relations[name] = Relation(name, attributes) # add to relations

            # match inclusion dependency pattern
            matches = re.match(IND_PAT, line)
            if matches is not None:
                lrel   = matches.group('lrel')
                rrel   = matches.group('rrel')
                latt   = frozenset(c.strip() for c in matches.group('latt').split(','))
                ratt   = frozenset(c.strip() for c in matches.group('ratt').split(','))
                if lrel in relations and rrel in relations:

                    fkey = ForeignKey(latt, ratt, rrel)
                    relations[lrel].add_fkey(fkey)
                    relations[rrel].add_refed_by(lrel)

                else:
                    print('Skip IND {} since relation definition missing.'.format(line))

            # match key patern
            matches = re.match(KEY_PAT, line)
            if matches is not None:
                name        = matches.group('name')
                keys_clause = matches.group('keys')
                for ind_k in keys_clause.split(';'):
                    ind_k = ind_k.strip()
                    matches = re.match(INDIVIDUAL_KEY_PAT, ind_k)
                    if matches is not None:
                        key = frozenset([k.strip() for k in matches.group('attr').split(',')])
                        try:
                            relations[name].add_key(key)
                        except KeyError:
                            print('Skip key {} since relation definition missing.'.format(line))
                    
    except StopIteration:
        infile.close()
        return relations

def write_to_file(filename, content):
    ''' Write content to file of filename '''
    with open(filename, 'w+') as outf:
        outf.write(content + '\n')

def parse_arguments():
    ''' parse command line arguments '''

    parser = argparse.ArgumentParser(
                description=
                '''
                Use Translator to translate Relation schemas to ERD.
                ''')
    # input file
    #  parser.add_argument('schema_file' , 
    #                    help='The input file containing the definition of relation schemas')
    parser.add_argument('-v', '--verbosity',
                        help='print more detailed info', action="store_true")
    parser.add_argument('-e', '--entity_outfile',    
                        help='filename where JSON of translated Entities will be saved.',
                        default='entity_json.txt')
    parser.add_argument('-r', '--relationship_outfile', 
                        help='filename where JSON of translated Relationships will be saved.',
                        default='relationship_json.txt')

    args = parser.parse_args()
    return args


if __name__ == '__main__':

    # get parsed arguments
    args = parse_arguments()

    # Reading schemas
    print '<h3>Reading schema ... ', 
    indent = '    '
    relations = read_inputs(uploadPath+"database.txt") 

    if args.verbosity:
        print('\nRelations: ')
        for name, R in relations.items():
            print('{}{}: {}'.format(indent, 'Name', name))
            print('{}{}: {}'.format(indent*2, 'Attributes', ', '.join(a for a in R.attributes)))
            print('{}{}: {}'.format(indent*2, 'Keys', repr_keys(R.keys)))
            print('{}{}: {}'.format(indent*2, 'Primary key', '(' + ', '.join(a for a in R.pkey) + ')'))
            if R.fkeys is not None:
                print('{}{}: {}'.format(indent*2, 'Fkeys', repr_keys(R.fkeys)))
            if R.refed_by is not None:
                print('{}{}: {}'.format(indent*2, 'Referenced by', ', '.join(str(r) for r in R.refed_by)))

    print 'done\n'

    # TRANSLATING part
    print 'Translating ... ',
    translator = Translator(relations.values())
    translator.translate()
    print 'done\n</h3>'

    if args.verbosity:
        print 'Intemediate output: '
        # find core relations
        core_relations = translator.core_relations
        print('Core relations: {}'.format(', '.join(c for c in core_relations)))
        print

        # find component relations
        comp_relations = translator.comp_relations
        print('Component relations: ')
        for cname, comps in comp_relations.items():
            print('{}{}: {}'.format(indent, cname, ', '.join(comp[0]+"({})".format(comp[1]) for comp in comps)))
        print

        # find IDD relations
        IDD_relations = translator.IDD_relations
        print('ID-dependent relations: ')
        for dep_R, R in IDD_relations.items():
            print('{}{:15s} -> {}'.format(indent, dep_R, R))
        print

        # find ISA relations
        ISA_relations = translator.ISA_relations
        print('ISA_relations: ')
        for r1, r2 in ISA_relations.items():
            print('{}{:15s} -> {}'.format(indent, r1, r2))
        print


        print "Entities: "
        entities = translator.entities
        for name, ent in entities.items():
            print 'Name : {}'.format(name)
            print 'Type : {}'.format(ent.entity_type)
            print 'Identifier: {}'.format(ent.identifier)
            print 'Attributes: ',
            for elem, attr in ent.attributes.items():
                print '{}:[{}] '.format(repr_indi_key(elem), repr_cardinality(attr.cardinality)),
            print
        print


        # find relationships
        relationships = translator.relationships
        print('Relationship:')
        for rel in relationships:
            name = rel.name
            print('{}{}: {}').format(indent, 'Name', name)
            print('{}{}: {}').format(indent, 'Entities', ', '.join('{}[{}]'.format(name, card) for name, card in rel.entities.items()))
            if rel.attributes:
                print '{}Attributes: '.format(indent),
                for elem, attr in rel.attributes.items():
                    print '{}:[{}] '.format(repr_indi_key(elem), repr_cardinality(attr.cardinality)),
                print
        print

    # write to outfile
    write_to_file(renderPath+args.entity_outfile, translator.entity_json)
    write_to_file(renderPath+args.relationship_outfile, translator.relationship_json)

    print "<p>Finish Translation, JSON saved to render path {}, {}".format(args.entity_outfile, args.relationship_outfile)
    print ', please make sure the directory is readable/writable</p>'
    print '<p> Go to the render URL <a href="'+renderURL+'"> <button>Go To</button></a></p>';
    print '</body>'
    print '</html>'
