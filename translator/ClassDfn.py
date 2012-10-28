
def repr_keys(keys):
    ''' String repr of keys '''
    SEP = ', '
    rep = []
    for k in keys:
        rep.append('(' + SEP.join(a for a in k) + ')') 
    return SEP.join(rep)

def repr_indi_key(key):
    ''' String repr of individual key '''
    SEP = ', '
    return '({})'.format(SEP.join([att for att in key]))

def repr_cardinality(card):
    ''' String repr of key '''
    if card in Cardinality.valid_cardinalities:
        if   card == 1:
            repr_str = '1:1'
        elif card == 2:
            repr_str = '1:m'
        elif card == 3:
            repr_str = 'm:1'
        elif card == 4:
            repr_str = 'm:m'

        return repr_str
    else:
        raise ValueError('Invalid cardinality: {}'.format(card))

def repr_entity_type(etype):
    ''' String repr of entity type '''
    if etype in EntityType.valid_entity_type:
        if   etype == 1:
            repr_str = 'regular'
        elif etype == 2:
            repr_str = 'weak'

        return repr_str
    else:
        raise ValueError('Invalid entity type: {}'.format(etype))

def repr_relationship_type(rtype):
    ''' String repr of relationship type '''
    if rtype in RelationshipType.valid_relationship_type:
        if   rtype == 1:
            repr_str = 'regular'
        elif rtype == 2:
            repr_str = 'IDD'
        elif rtype == 3:
            repr_str = 'ISA'

        return repr_str
    else:
        raise ValueError('Invalid entity type: {}'.format(rtype))


# CLASS --------------------------------------------------- 

class Cardinality:
    ''' Representing the enums of cardinality '''
    one2one   = 1
    one2many  = 2
    many2one  = 3
    many2many = 4

    valid_cardinalities = set([1, 2, 3, 4])

class EntityType:
    ''' Represents the enums of Entity Type '''

    regular = 1
    IDD     = 2

    valid_entity_type = set([1, 2])

class RelationshipType:
    ''' Represents the enums of Relationship Type '''

    regular = 1
    IDD     = 2
    ISA     = 3

    valid_relationship_type = set([1, 2, 3])


class Attribute(object):
    ''' Represents an atribute
        The cardinality of each attribute is associated with Entity or Relationship
    '''

    def __init__(self, name, elements, cardinality):
        self._name = name
        if type(elements) == frozenset:
            self._elements = elements # a frozen set of single or composite attributes
        else:
            raise ValueError('Element need to be a frozenset')
        self.cardinality = cardinality

    @property
    def name(self):
        ''' Return the name of the attribute '''
        return self._name

    @property
    def cardinality(self):
        ''' Return the cardinality of the attribute '''
        return self._cardinality

    @property
    def elements(self):
        ''' Return the set of element '''
        return self._elements

    @cardinality.setter
    def cardinality(self, card):
        ''' Set cardinality '''
        if card in Cardinality.valid_cardinalities:
            self._cardinality = card
        else:
            raise ValueError("Invalid cardinality: {}".format(card))

    def to_dict(self):
        ''' Return a dict representation of attribute '''
        attr_dict = {'cardinality': repr_cardinality(self._cardinality)}
        attr_dict.update({'elements': [e for e in self._elements]})

        return attr_dict


    def __str__(self):
        ''' string representation of attribute '''
        return self._name


class ForeignKey(object):
    ''' Represents a foreign key in relation '''

    def __init__(self, key, refed_key, refed_relation):

        self.key = key
        self.refed_key = refed_key
        self.refed_relation = refed_relation

class Relation(object):
    ''' Represents a relation in Relational model '''

    def __init__(self, name, attributes, 
                       keys=None, pkey=None, 
                       fkeys=None, refed_by=None):

        self._name       = name
        self._attributes = attributes
        self._keys       = keys
        self._pkey       = pkey
        self._fkeys      = fkeys
        self._refed_by   = refed_by

        self._update_primes()
        self._count_disjoint_fkeys()

    def _update_primes(self):
        ''' update prime attributes '''
        self._primes = set([])
        if self._keys is not None:
            for key in self._keys:
                self._primes.update(key)

    def _count_disjoint_fkeys(self):
        ''' count disjoint foreign keys '''
        if self._fkeys is not None:
            attr_seen = set([])
            counter = 0
            for fk in self._fkeys:
                if not len(fk.intersection(attr_seen)):
                    counter += 1
                attr_seen.update(fk)
        else:
            counter = 0
        self._num_disjoint_fkeys = counter

    def add_key(self, key):
        ''' add key to relation '''

        if self._keys is None:
            self._keys = set([key])
            # if pkey not set, the first key becomes the pkey
            self._pkey = key if self._pkey is None else self._pkey
        else:
            self._keys.add(key)

        self._update_primes()

    def add_fkey(self, fkey):
        ''' add foreign key to relation '''

        if not isinstance(fkey, ForeignKey):
            raise ValueError('Input is not an instance of ForeighKey')
        elif not fkey.key.issubset(self._attributes):
            raise ValueError('Key {} is not a subset of attributes of R'.foramt(fkey.key))
        elif self._fkeys is None:
            self._fkeys = {fkey.key: fkey}
        else:
            self._fkeys.update({fkey.key: fkey})

        self._count_disjoint_fkeys()

    def add_refed_by(self, refed_by):
        ''' Add other relation to refed_by ''' 

        if self._refed_by is None:
            self._refed_by = set([refed_by])
        else:
            self._refed_by.add(refed_by)

    def set_primary_key(self, key):
        ''' Set the primay key of relation '''
        if key in self._keys:
            self._pkey = key
        else:
            raise KeyError('{} is not a key of R'.format(key))

    def __str__(self):
        ''' String representation '''
        return '{}{}'.format(self._name, repr_str(self._pkey))

    @property
    def name(self):
        "Get the name of relation."
        return self._name

    @property
    def attributes(self):
        "Get the attributes of relation."
        return self._attributes

    @property
    def keys(self):
        "Get the keys of relation."
        return self._keys

    @property
    def pkey(self):
        "Get the primary key of relation."
        return self._pkey

    @property
    def fkeys(self):
        "Get the foreign keys of relation."
        return self._fkeys

    @property
    def refed_by(self):
        "Get the relations referencing to self."
        return self._refed_by

    @property
    def primes(self):
        "return the primes attributes "
        return self._primes

    @property
    def non_primes(self):
        "return the non-primes attributes "
        return self._attributes.difference(self._primes)

    @property
    def num_disjoint_fkeys(self):
        ''' return the disjoint fkeys count '''
        if self._num_disjoint_fkeys:
            return self._num_disjoint_fkeys
        else:
            return 0

class Entity(object):
    ''' Represents Entity in ER model '''

    def __init__(self, name, Etype = None, identifier = None, attributes = None):
        self._name = name
        self._type = Etype
        self._attributes = attributes

        # call the setter function
        self.identifier = identifier

    def add_attribute(self, attribute):
        ''' Add attribute to Entity 
            attribute is an instance of Attribute
        '''
        if not isinstance(attribute, Attribute):
            raise ValueError('Not an instance of Attribute')

        if self._attributes is None:
            self._attributes = {attribute.elements: attribute}
        else:
            # will update attribute if already in dict
            self._attributes.update({attribute.elements: attribute})

    def remove_attribute(self, attr_elements):
        ''' Remove attribute from Entity 
            attribute is an instance of Attribute
        '''
        if self._attributes is not None and attr_elements in self._attributes:
            # remove
            self._attributes.pop(attr_elements)

    @property
    def attributes(self):
        return self._attributes

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, attr_elem):
        ''' Set identifier of Entity 
            attr is a single attribute of relation or a composite attributes
        '''

        if attr_elem is None:
            # set to None
            self._identifier = None
            return

        if self._attributes is not None and attr_elem in self._attributes:
            # attr_elem already in attributes
            self._attributes[attr_elem].Cardinality = one2one
            self._identifier = attr_elem
            return

        name = '_'.join(attr_elem)
        identifier = Attribute(name, attr_elem, Cardinality.one2one)
        self._identifier = identifier
        self.add_attribute(identifier)

    @property
    def name(self):
        ''' Return the name of Entity '''
        return self._name

    @property
    def entity_type(self):
        ''' Return the type of Entity '''
        return self._type


class Relationship(object):
    ''' Represents Relationship in ER model '''

    def __init__(self, name, Rtype = None, identifier= None):

        self._name        = name
        # identifier is a set of some of the identifiers of participating entities
        self._identifier  = identifier
        # participating entity names, would be a dict of keys in self._entities
        # and value as cardinality of either '1' or 'm'
        self._entities    = {}
        # the same as that in Entity
        self._attributes  = {}
        # the type of Relationship
        self._type        = Rtype

    def add_participating_entity(self, name, cardinality):
        ''' Add participating entity passed by name '''
        self._entities.update({name: cardinality})

    def add_attribute(self, attr):
        ''' Add attribute to the Relationship '''
        if not isinstance(attr, Attribute):
            raise ValueError('Input is not an instance of Attibute.')
        else:
            self._attributes.update({attr.elements: attr})

    @property
    def name(self):
        "Get the name of relationship."
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def entities(self):
        "Get the entities associated with the relationship."
        return self._entities

    @property
    def attributes(self):
        "Get the attributes of relationship."
        return self._attributes

    @property
    def relationship_type(self):
        ''' The Relationship type '''
        return self._type

    @relationship_type.setter
    def relationship_type(self, Rtype):
        ''' Setter for type '''
        if Rtype in RelationshipType.valid_relationship_type:
            self._type = Rtype
        else:
            raise ValueError("Invalid Relationship type: {}".format(Rtype))

