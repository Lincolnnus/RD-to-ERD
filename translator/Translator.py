#!/usr/bin/python 

import re
import sys
import json

from ClassDfn import Relation, Entity, Relationship, Attribute
from ClassDfn import Cardinality, EntityType, RelationshipType  # enum type
from ClassDfn import repr_keys, repr_cardinality, repr_entity_type, repr_relationship_type # function

class Translator(object):
    ''' Traslate Relation schema to ER diagram'''

    # helper functions
    @staticmethod
    def _count_disjoint_keys(keys):
        ''' return the count of disjoint keys '''

        # keys is a set
        attr_seen = set([])
        counter = 0
        for k in keys:
            # k is a frozenset of attributes
            if len(k.intersection(attr_seen)) == 0:
                counter += 1
            attr_seen.update(k)

        return counter


    def __init__(self, relations):
        ''' take a list of object relation as input '''

        tf = [isinstance(r, Relation) for r in relations] 
        if all(tf):
            self._relations = {r.name: r for r in relations}
            self._core_relations = self._comp_relations = None
            self._ISA_relations  = self._IDD_relations  = None
            self._relationships  = None
            self._entities       = None

            self._entity_json       = None
            self._relationship_json = None
            self._unassigned_relations = []
        else:
            raise TypeError('Translator takes an iterable of Relations as input.')

    def _find_core_relations(self):
        ''' find the core relations '''

        # _core_relations is a dict consists k-v pair of
        # R.name: R, R is an instance of Relation
        self._core_relations = {}

        for name, R in self._E_relations.items():
            # CASE 1:
            # R is not involved in any inclusion dependency(stand alone relation)
            if R.fkeys is None and R.refed_by is None:
                self._core_relations.update({name: R})
                self._E_relations_left.remove(name)
                continue

            # CASE 2
            # (a) There is a relation R1 references to R
            # (b) R does NOT contain more than one disjoint foreign keys
            #     it is a strong indication of Relationship if it does
            # (c) No IND whose right attributes are proper subset of pkey of R
            if R.refed_by is not None:
                # condition (b) satisfied automaticaly since E-type relation

                # condition (c)
                pkey = R.pkey
                passed = True
                for R1 in self._relations.values():
                    if R1.fkeys is not None:
                        for fk_name, fk in R1.fkeys.items():
                            refed_key = fk.refed_key 
                            if refed_key != pkey and refed_key.issubset(pkey):
                                # proper subset
                                passed = False
                                break
                if passed:
                    # all conditions satisfied
                    self._core_relations.update({name: R})
                    self._E_relations_left.remove(name)
            else:
                continue

            # CASE 3
            # R is a core-relation by ID-dependency
            pass


    def _find_comp_relations(self):
        ''' find the component relations of each core relation '''

        # _comp_relations is a dict consists of k-v pair
        # name of core relations -> entry(name of comp relation, cardinality)
        self._comp_relations = {}

        for cname, R in self._core_relations.items():
            if R.refed_by is None:
                continue
            for rname in R.refed_by:
                # for each R1 by the name of rname referencing to R
                # (1) R1 references R satisfied
                # (2) and (3) baisically ensure R1 not qualified to be 
                #   an Entity or Relationship

                # (3) R1 does not contain more than one disjoint fkeys
                if rname in self._R_relations:
                    continue

                # (2) No relations references R1
                R1 = self._E_relations[rname]
                if R1.refed_by is not None:
                    continue
                
                # (4) The foreign key which references R is:
                #   (i)   part of the key of R1, or
                #   (ii)  a non prime of R1, or 
                #   (iii) the key of R1
                fkey = R1.fkeys.keys()[0] # the only one foreign key which references R
                nonprimes = R1.non_primes
                if fkey.issubset(nonprimes):
                    # (ii) no need to be just one attribute
                    # this is a 1:m component relation
                    # since the attributes other than fkey -> fkey(pkey of R)
                    entry = (rname, Cardinality.one2many)
                    try:
                        self._comp_relations[cname].add(entry)
                    except KeyError:
                        self._comp_relations[cname] = set([entry])
                    self._E_relations_left.remove(rname)
                    continue

                for k in R1.keys:
                    # (i) and (iii)
                    if fkey.issubset(k):
                        if fkey == k:
                            # this is a m:1 component relation
                            # since the pkey of R is also a key of R1
                            entry = (rname, Cardinality.many2one)
                        elif not nonprimes:
                            # this is a m:m component relation
                            # since pkey of R is part of key of R1
                            # which implies pkey could not functionally 
                            # depend other attributes of R1 and vice versa
                            # * could be a All-key relation translated from 
                            # * a NF ERD
                            entry = (rname, Cardinality.many2many)
                        else:
                            # the existence of nonprime qualifies R
                            # as a independent entity
                            continue
                        try:
                            self._comp_relations[cname].add(entry)
                        except KeyError:
                            self._comp_relations[cname] = set([entry])
                        self._E_relations_left.remove(rname)
                        break


    def _find_IDD_relations(self):
        ''' find ID-dependent relations '''

        # _IDD_relations is a dict consists k-v pair:
        # dependent relation -> core relation 
        self._IDD_relations = {}

        for cname, R0 in self._core_relations.items():
            for rname in R0.refed_by:
                
                # (2) R contains more than one disjoint foreign keys
                if rname not in self._E_relations:
                    continue

                R = self._E_relations[rname]
                # (1) k0 <= k & R[k0] <= R0[k0]
                # which means k0 is a subset of k
                #   and R has a foreign key k0 references to R0[k0]
                # k0, k are primary keys of R0 and R
                k0 = R0.pkey 
                k  = R.pkey 
                # k should be a proper subset of k0
                if (k0.issubset(k) and k0 != k) and (k0 in R.fkeys) \
                   and (R.fkeys[k0].refed_key == k0 and R.fkeys[k0].refed_relation == cname):
                    pass
                else:
                    continue

                # (3) There exists R1 references to R, or
                #       R has a non-prime attribute
                if R.refed_by is None and not len(R.non_primes):
                    continue

                # all conditions satisfied
                # plus rname is not identified as comp relation
                all_comp_names = set()
                '''
                for entries in self._comp_relations.values():
                    all_comp_names.update(ent[0] for ent in entries)
                '''
                if rname not in all_comp_names:
                    self._IDD_relations[rname] = cname
                    self._core_relations[rname] = self._relations[rname] # add to core_relation also
                    self._E_relations_left.remove(rname)


    def _find_ISA_relations(self):
        ''' find the ISA relations '''

        # _ISA_relations is a dict with k-v pair
        # R1 -> R, where R1 ISA R
        self._ISA_relations = {}
        
        # if keys K1 of R1 and K2 of R2 satisfies
        #   R1[K1] <= R2[K2], then R1 ISA R2 (both R1 and R2 are core relatons)
        for name, R1 in self._core_relations.items():
            for k in R1.keys:
                # for each key of R1
                if R1.fkeys is not None and k in R1.fkeys:
                    rkey = R1.fkeys[k].refed_key
                    rrel = R1.fkeys[k].refed_relation
                    if rrel in self._core_relations and \
                       rkey in self._core_relations[rrel].keys:
                        self._ISA_relations[name] = rrel
    

    def _identify_relationships(self):
        ''' Identify relationships in relations
            
            Identify relationships by the following steps
            (1) The relation must have more than one disjoint foreign keys  
                which referencing to identifiers of Entities
                Let such fkey be E_fkey
            (2) Examining primary key
                1). if pkey has NO E_fkey
                    pkey is a 1:m attribute of A Relationship, whose Identifier is 
                    other E_fkey in this relation.
                    The attribute will be assign to the Relationship if exists
                    otherwise the relation unassigned
                2). pkey has ONLY E_fkeys
                    if other E_fkeys exists in relation, 
                    then relation represents m : 1 Relationship
                    m: Entities whose identifiers are in pkey
                    1: other E_fkeys
                    If other attributes exists as nonprimes of relation
                    they are m:1 attributes of Relationship
                    If other keys which are not identifiers of Entitiy exists
                    they are 1:1 attributes of Relationship
                3). pkey has E_fkeys and other attributes
                    if all-key relation
                    then this represents m:m Relationship with multivalued attributes
                    else unassigned

        '''

        def examine_pkey(pkey, E_fkeys, R):
            ''' examine pkey, partition pkey into those in E_fkeys and others '''

            idr_in_pkey ={fk: R.fkeys[fk].refed_key for fk in E_fkeys if fk.issubset(pkey)}
            otr_attr = pkey.difference(set([a for fk in idr_in_pkey for a in fk]))
            return idr_in_pkey, otr_attr

        # The following assume all identifiers are disjoint
        # this assumption would be a probem if exists relations referencing to IDD entites
        # find all Identifiers of Entitnies 
        # relaxed universal assumption, all identifiers are unique
        all_identifiers = {ent.identifier.elements: name for name, ent in self._entities.items()}

        # unassigned_attributes
        unassigned_attributes = {}

        for name, R in self._R_relations.items():
            # find the E_fkeys of relation R
            pkey = R.pkey
            E_fkeys = [fk_name for fk_name, fk  in R.fkeys.items() if fk.refed_key in all_identifiers]
            dsj_fkey_count = self._count_disjoint_keys(E_fkeys)

            # 1) more than one fkeys referencing Entitites
            if dsj_fkey_count > 1:
                idr_in_pkey, otr_attr = examine_pkey(pkey, E_fkeys, R) 
                if not idr_in_pkey:
                    # pkey has NO E_fkey
                    R_identifier = frozenset([npa for npa in R.non_primes if frozenset([npa]) in all_identifiers])
                    otr_non_primes = R.non_primes.difference(R_identifier)
                    if not otr_non_primes:
                        unassigned_attributes.update({R_identifer: pkey})

                elif not otr_attr:
                    # 2) only E_fkeys
                    rel = Relationship(name, RelationshipType.regular, frozenset(pkey))
                    for idr, E_name in all_identifiers.items():
                        if idr in idr_in_pkey.values():
                            rel.add_participating_entity(E_name, 'm')

                    for npa in R.non_primes:
                        key = frozenset([npa])
                        if key in all_identifiers:
                            rel.add_participating_entity(all_identifiers[key], '1')
                        else:
                            attr = Attribute(npa, key, Cardinality.many2one)
                            rel.add_attribute(attr)

                    self._add_relationship(rel, RelationshipType.regular)

                else:
                    # 3) pkey has other attributes
                    if R.attributes == pkey:
                        # all key relation
                        rel = Relationship(name, RelationshipType.regular, frozenset(pkey))
                        for idr, E_name in all_identifiers.items():
                            if idr in idr_in_pkey.values():
                                rel.add_participating_entity(E_name, 'm')
                        for npa in otr_attr:
                            key = frozenset([npa])
                            attr = Attribute(npa, key, Cardinality.many2many)
                            rel.add_attribute(attr)

                        self._add_relationship(rel, RelationshipType.regular)
                    else:
                        self._unassigned_relations.append(R)

        # After determine the main relationships 
        # try to comibine with other E_relations left
        self._combine_relationship()

    def _combine_relationship(self):
        ''' Add attributes to relationship if exist '''

        def add_other_attributes(rel, R, fkey, card):
            ''' Add attributes other than primay kye to rel '''
            other_attr = R.pkey.difference(fkey)
            for attr_name in other_attr:
                attr = Attribute(attr_name, frozenset([attr_name]), card)
                rel.add_attribute(attr)

        # a dict of regular relationships
        rel_dict = {rel.name: rel for rel in self._relationships if rel.relationship_type == RelationshipType.regular}

        # all the relations in _E_relations_left would have one fkey not referening to entity
        for rname in self._E_relations_left:
            # test whether it could be combined with existing regular relationship

            R = self._E_relations[rname]
            pkey = R.pkey
            fkey = R.fkeys.keys()[0] # the only fkey
            refed_rel = R.fkeys[fkey].refed_relation

            if refed_rel in rel_dict:
                # referencing to a regular relationship
                rel = rel_dict[refed_rel]
                if pkey == R.attributes:
                    # all-key relation
                    add_other_attributes(rel, R, fkey, Cardinality.many2many)
                elif pkey == fkey:
                    # primary key is the foreign key
                    add_other_attributes(rel, R, fkey, Cardinality.many2one)
                elif not pkey.intersection(fkey) and pkey.union(fkey) != R.attributes:
                    # primary key is disjoint from foreign key
                    # and there is not other attributes exist
                    # then the primary key is an one2many attribute of rel
                    attr_name = '_'.join(a for a in pkey)
                    attr = Attribute(attr_name, pkey, Cardinality.one2many)
                    rel.add_attribute(attr)
                else:
                    # could not combine
                    continue
                        

    def _partition_relations(self):
        ''' Partition relations to E-type or R-type

            E-type relations are those with AT MOST one disjoint foreign key
                All the Entities would translated from this type
                * The relation of a Relationship whose identifier is only one of its
                  participating Entities' identifier would also be E-type.
                  And such relation could result into a comp relation
            R-type 
                All the Relationships would translated from this type
        '''

        self._E_relations = {name: R for name, R in self._relations.items() \
                                if R.num_disjoint_fkeys <= 1}
        self._R_relations = {name: R for name, R in self._relations.items() \
                                if R.num_disjoint_fkeys >  1}

        self._E_relations_left = set([name for name in self._E_relations])


    def _add_entity(self, relation, Etype):
        ''' Add entity '''

        if not isinstance(relation, Relation):
            raise ValueError("Input need to be an instance of Relation")
        if Etype not in EntityType.valid_entity_type:
            raise ValueError("Invalid Entity Type: {}".format(Etype))

        if self._entities and relation.name in self._entities:
            raise Exception("Entity {} already identified".format(relation.name))
        else:
            entity = Entity(relation.name, Etype = Etype)
            # primary key -> the identifier of Entity
            entity.identifier = relation.pkey

            # key -> 1:1 attribute
            for k in relation.keys:
                if k != relation.pkey:
                    name = '_'.join(k)
                    attr = Attribute(name, k, Cardinality.one2one)
                    entity.add_attribute(attr)
                     
            # non-prime attribute -> m:1 attribute
            for npa in relation.non_primes:
                attr = Attribute(npa, frozenset([npa]), Cardinality.many2one)
                entity.add_attribute(attr)

        if self._entities is None:
            self._entities = {relation.name: entity}
        else:
            self._entities[relation.name] = entity

    def _add_relationship(self, rel, Rtype):
        ''' Add relationship to _relationship '''

        if not isinstance(rel, Relationship):
            raise ValueError("Input need to be an instance of Relationship")
        if Rtype not in RelationshipType.valid_relationship_type:
            raise ValueError("Invalid Relationship type: {}".format(Rtype))
        
        if self._relationships is None:
            self._relationships = [rel]
        else:
            self._relationships.append(rel)


    def _identify_entities(self):
        ''' Identify Entities in ER '''

        # STEP 1: find core relations
        self._find_core_relations()

        # STEP 2: find IDD relations
        self._find_IDD_relations()

        # STEP 3: find component relations
        self._find_comp_relations()

        # STEP 4: find ISA relations
        self._find_ISA_relations()

        # Identify Entities
        # each core relation would result in an Entity
        for cname, R in self._core_relations.items():
            if cname not in self._IDD_relations:
                # a regular entity
                self._add_entity(R, EntityType.regular)
            else:
                # Add IDD to Entities
                # Add corresponding Relationship
                dname = self.IDD_relations[cname] # the relation name on which cname depends
                self._add_entity(self._E_relations[cname], EntityType.IDD)
                rel = Relationship('ID', RelationshipType.IDD)
                rel.add_participating_entity(cname, '1')
                rel.add_participating_entity(dname, 'm')
                self._add_relationship(rel, RelationshipType.IDD)


        # Incorporate each component relation
        for cname, comp in self._comp_relations.items():

            for comp_name, comp_card in comp:
                R = self._E_relations[comp_name]
                identifier = self._entities[cname].identifier

                if comp_card == Cardinality.many2many:
                    # non-prime attributes of R become m:m attributes
                    # other keys not containing identifier of Entity become 1:m attributes
                    # other primes in the same key with identifier of Entity become m:m attributes
                    m2m_attrs  = set(R.non_primes)
                    for k in R.keys:
                        attr_elem = identifier.elements
                        if not len(k.intersection(attr_elem)):
                            attr_name = '-'.join(k)
                            attribute = Attribute(attr_name, k, Cardinality.one2many)
                            self._entities[cname].add_attribute(attribute)
                        else:
                            m2m_attrs.update(k.difference(attr_elem))
                            
                    for attr in m2m_attrs:
                        # set m:m attributes
                        attribute = Attribute(attr, frozenset([attr]), Cardinality.many2many)
                        self._entities[cname].add_attribute(attribute)

                elif comp_card == Cardinality.many2one:
                    # non-primes attributes of R become m:1 attributes
                    # keys other than identifier become 1:1 attributes
                    for k in R.keys:
                        if k != identifier:
                            attr_name = '_'.join(k)
                            attribute = Attribute(attr_name, k, Cardinality.one2one)
                            self._entities[cname].add_attribute(attribute)
                    for attr in R.non_primes:
                        attribute = Attribute(attr, frozenset([attr]), Cardinality.many2one)
                        self._entities[cname].add_attribute(attribute)

                elif comp_card == Cardinality.one2many:
                    # all the keys of R become 1:m attributes
                    # non_prims other than identifier become m:m attributes
                    for k in R.keys:
                        attr_name = '_'.join(k)
                        attribute = Attribute(attr_name, k, Cardinality.one2many)
                        self._entities[cname].add_attribute(attribute)
                    for attr in R.non_primes:
                        if attr != identifier:
                            attribute = Attribute(attr, frozenset([attr]), Cardinality.many2many)
                            self._entities[cname].add_attribute(attribute)



        # Add correspinding ISA Relationship
        # A ISA B
        for RA1, RB1 in self._ISA_relations.items():
            for RA2, RB2 in self._ISA_relations.items():
                if RA1 == RB2 and RA2 == RB1:
                    # TODO: combine together
                    continue
            # add relationship
            rel = Relationship('ISA', RelationshipType.ISA)
            rel.add_participating_entity(RA1, 'm')
            rel.add_participating_entity(RB1, '1')
            self._add_relationship(rel, RelationshipType.ISA)

        # Find the case of mix enttity and relationship relation
        # that is the nonprimes of a core Entity R have other
        # identifiers of Entities

        # all the entity identifiers
        entity_idr = [ent.identifier.elements for ent in self._entities.values()]
        # sort the entity_idr by lenght
        # this is for the case of IDD entity, which would contain other identifier of entity
        entity_idr = sorted(entity_idr, key=len, reverse=True)
        for cname, R in self._core_relations.items():
            # the keys refed by non prime fkeys
            nonprimes = R.non_primes
            if R.fkeys is not None:
                np_refed_keys = {refed_fk.refed_key: fk for fk, refed_fk in R.fkeys.items() if fk.issubset(nonprimes)}
            else:
                continue
            if np_refed_keys:
                for idr in entity_idr:
                    if idr in np_refed_keys:
                        # R is a mix of entity and another binary relationship
                        # 1) exclude the idr from R
                        # 2) add corresponding relationship

                        # exclude idr from R
                        ent = self._entities[cname]
                        ent.remove_attribute(np_refed_keys[idr])
                        # add corresponding relationship
                        for ent_name, ent in self._entities.items():
                            # find the name of the other entity
                            if ent.identifier.elements == idr:
                                break
                        rel_name = '{}_{}'.format(cname, ent_name)
                        rel = Relationship(rel_name, RelationshipType.regular)
                        rel.add_participating_entity(cname, 'm')
                        rel.add_participating_entity(ent_name, '1')
                        self._add_relationship(rel, RelationshipType.regular)

    def translate(self):
        ''' traslate Relations to ER model'''

        # partition relations
        self._partition_relations()
    
        # Identify Entities 
        self._identify_entities()

        # Identity Relationships
        self._identify_relationships()


    @property
    def entity_json(self):
        ''' JSON representation of entities '''

        if self._entities is None:
            self.translate()
    
        if self._entities is not None and self._entity_json is None:

            entities = []
            for ent in self._entities.values():
                ent_dict   = {'name': ent.name, 'type': repr_entity_type(ent.entity_type)}

                identifier = ent.identifier.to_dict()
                ent_dict.update({'identifier': identifier})

                attributes = [attr.to_dict() for attr in ent.attributes.values()]
                ent_dict.update({'attributes': attributes})
                entities.append(ent_dict)
            
            self._entity_json = json.dumps(entities)

        return self._entity_json

    @property
    def relationship_json(self):
        ''' JSON representation of relatonships '''

        if self._entities is None:
            self.translate()

        if self._relationships is not None and self._relationship_json is None:

            relationships = []
            for rel in self._relationships:
                rel_dict = {'name': rel.name, 'type': repr_relationship_type(rel.relationship_type)}
                # TODO
                '''
                if rel.relationship_type != RelationshipType.regular:
                    ent_names = rel.entities.keys()
                    first = entity_names[0]

                else:
                    entities
                '''
                pat_entities = [{'name': ent, 'cardinality': card} for ent, card in rel.entities.items()]
                rel_dict.update({'participating_entities': pat_entities})

                if rel.attributes:
                    attributes = [attr.to_dict() for attr in rel.attributes.values()]
                    rel_dict.update({'attributes': attributes})

                relationships.append(rel_dict)

            self._relationship_json = json.dumps(relationships)

        return self._relationship_json


    @property
    def core_relations(self):
        return self._core_relations

    @property
    def comp_relations(self):
        return self._comp_relations

    @property
    def IDD_relations(self):
        return self._IDD_relations

    @property
    def ISA_relations(self):
        return self._ISA_relations

    @property
    def relationships(self):
        return self._relationships

    @property
    def entities(self):
        return self._entities
