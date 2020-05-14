#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2019 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Graph data types
"""


from neo4j.compat import xstr, deprecated, Mapping


__all__ = [
    "Graph",
    "Entity",
    "Node",
    "Relationship",
    "Path",
]


class Graph(object):
    """ Local, self-contained graph object that acts as a container for
    :class:`.Node` and :class:`.Relationship` instances.
    """

    def __init__(self):
        self._nodes = {}
        self._relationships = {}
        self._relationship_types = {}
        self._node_set_view = EntitySetView(self._nodes)
        self._relationship_set_view = EntitySetView(self._relationships)

    @property
    def nodes(self):
        """ Access a set view of the nodes in this graph.
        """
        return self._node_set_view

    @property
    def relationships(self):
        """ Access a set view of the relationships in this graph.
        """
        return self._relationship_set_view

    def relationship_type(self, name):
        """ Obtain a :class:`.Relationship` subclass for a given
        relationship type name.
        """
        try:
            cls = self._relationship_types[name]
        except KeyError:
            cls = self._relationship_types[name] = type(xstr(name), (Relationship,), {})
        return cls

    def put_node(self, n_id, labels=(), properties=None, **kwproperties):
        inst = Node(self, n_id)
        inst._labels.update(labels)
        inst._update(properties, **kwproperties)
        return inst

    def put_relationship(self, r_id, start_node, end_node, r_type, properties=None, **kwproperties):
        if not isinstance(start_node, Node) or not isinstance(end_node, Node):
            raise TypeError("Start and end nodes must be Node instances (%s and %s passed)" %
                            (type(start_node).__name__, type(end_node).__name__))
        inst = _put_unbound_relationship(self, r_id, r_type, properties, **kwproperties)
        inst._start_node = start_node
        inst._end_node = end_node
        return inst


def _put_unbound_relationship(graph, r_id, r_type, properties=None, **kwproperties):
    inst = Relationship(graph, r_id, r_type)
    inst._update(properties, **kwproperties)
    return inst


class Entity(Mapping):
    """ Base class for :class:`.Node` and :class:`.Relationship` that
    provides :class:`.Graph` membership and property containment
    functionality.
    """

    def __new__(cls, graph, id):
        inst = object.__new__(cls)
        inst._graph = graph
        inst._id = id
        inst._properties = {}
        return inst

    def __eq__(self, other):
        try:
            return type(self) == type(other) and self.graph == other.graph and self.id == other.id
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self._properties)

    def __getitem__(self, name):
        return self._properties.get(name)

    def __contains__(self, name):
        return name in self._properties

    def __iter__(self):
        return iter(self._properties)

    @property
    def graph(self):
        """ The :class:`.Graph` to which this entity belongs.
        """
        return self._graph

    @property
    def id(self):
        """ The identity of this entity in its container :class:`.Graph`.
        """
        return self._id

    def _update(self, properties, **kwproperties):
        properties = dict(properties or {}, **kwproperties)
        self._properties.update((k, v) for k, v in properties.items() if v is not None)

    def get(self, name, default=None):
        """ Get a property value by name, optionally with a default.
        """
        return self._properties.get(name, default)

    def keys(self):
        """ Return an iterable of all property names.
        """
        return self._properties.keys()

    def values(self):
        """ Return an iterable of all property values.
        """
        return self._properties.values()

    def items(self):
        """ Return an iterable of all property name-value pairs.
        """
        return self._properties.items()


class EntitySetView(Mapping):
    """ View of a set of :class:`.Entity` instances within a :class:`.Graph`.
    """

    def __init__(self, entity_dict):
        self._entity_dict = entity_dict

    def __getitem__(self, e_id):
        return self._entity_dict[e_id]

    def __len__(self):
        return len(self._entity_dict)

    def __iter__(self):
        return iter(self._entity_dict.values())


class Node(Entity):
    """ Self-contained graph node.
    """

    def __new__(cls, graph, n_id):
        try:
            inst = graph._nodes[n_id]
        except KeyError:
            inst = graph._nodes[n_id] = Entity.__new__(cls, graph, n_id)
            inst._labels = set()
        return inst

    def __repr__(self):
        return "<Node id=%r labels=%r properties=%r>" % (self._id, self._labels, self._properties)

    @property
    def labels(self):
        """ The set of labels attached to this node.
        """
        return frozenset(self._labels)


class Relationship(Entity):
    """ Self-contained graph relationship.
    """

    def __new__(cls, graph, r_id, r_type):
        try:
            inst = graph._relationships[r_id]
        except KeyError:
            inst = graph._relationships[r_id] = Entity.__new__(cls, graph, r_id)
            inst.__class__ = graph.relationship_type(r_type)
            inst._start_node = None
            inst._end_node = None
        return inst

    def __repr__(self):
        return "<Relationship id=%r nodes=(%r, %r) type=%r properties=%r>" % (
            self._id, self._start_node, self._end_node, self.type, self._properties)

    @property
    def nodes(self):
        """ The pair of nodes which this relationship connects.
        """
        return self._start_node, self._end_node

    @property
    def start_node(self):
        """ The start node of this relationship.
        """
        return self._start_node

    @property
    def end_node(self):
        """ The end node of this relationship.
        """
        return self._end_node

    @property
    def type(self):
        """ The type name of this relationship.
        This is functionally equivalent to ``type(relationship).__name__``.
        """
        return type(self).__name__

    @property
    @deprecated("Relationship.start is deprecated, please use Relationship.start_node.id instead")
    def start(self):
        return self.start_node.id

    @property
    @deprecated("Relationship.end is deprecated, please use Relationship.end_node.id instead")
    def end(self):
        return self.end_node.id


class Path(object):
    """ Self-contained graph path.
    """

    def __init__(self, start_node, *relationships):
        assert isinstance(start_node, Node)
        nodes = [start_node]
        for i, relationship in enumerate(relationships, start=1):
            assert isinstance(relationship, Relationship)
            if relationship.start_node == nodes[-1]:
                nodes.append(relationship.end_node)
            elif relationship.end_node == nodes[-1]:
                nodes.append(relationship.start_node)
            else:
                raise ValueError("Relationship %d does not connect to the last node" % i)
        self._nodes = tuple(nodes)
        self._relationships = relationships

    def __repr__(self):
        return "<Path start=%r end=%r size=%s>" % \
               (self.start_node, self.end_node, len(self))

    def __eq__(self, other):
        try:
            return self.start_node == other.start_node and self.relationships == other.relationships
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        value = hash(self._nodes[0])
        for relationship in self._relationships:
            value ^= hash(relationship)
        return value

    def __len__(self):
        return len(self._relationships)

    def __iter__(self):
        return iter(self._relationships)

    @property
    def graph(self):
        """ The :class:`.Graph` to which this path belongs.
        """
        return self._nodes[0].graph

    @property
    def nodes(self):
        """ The sequence of :class:`.Node` objects in this path.
        """
        return self._nodes

    @property
    def start_node(self):
        """ The first :class:`.Node` in this path.
        """
        return self._nodes[0]

    @property
    def end_node(self):
        """ The last :class:`.Node` in this path.
        """
        return self._nodes[-1]

    @property
    def relationships(self):
        """ The sequence of :class:`.Relationship` objects in this path.
        """
        return self._relationships

    @property
    @deprecated("Path.start is deprecated, please use Path.start_node instead")
    def start(self):
        return self.start_node

    @property
    @deprecated("Path.end is deprecated, please use Path.end_node instead")
    def end(self):
        return self.end_node


def hydrate_path(nodes, relationships, sequence):
    assert len(nodes) >= 1
    assert len(sequence) % 2 == 0
    last_node = nodes[0]
    entities = [last_node]
    for i, rel_index in enumerate(sequence[::2]):
        assert rel_index != 0
        next_node = nodes[sequence[2 * i + 1]]
        if rel_index > 0:
            r = relationships[rel_index - 1]
            r._start_node = last_node
            r._end_node = next_node
            entities.append(r)
        else:
            r = relationships[-rel_index - 1]
            r._start_node = next_node
            r._end_node = last_node
            entities.append(r)
        last_node = next_node
    return Path(*entities)


def hydration_functions(graph):
    return {
        b"N": graph.put_node,
        b"R": lambda r_id, n0_id, n1_id, r_type, properties:
            graph.put_relationship(r_id, Node(graph, n0_id), Node(graph, n1_id), r_type, properties),
        b"r": lambda *args: _put_unbound_relationship(graph, *args),
        b"P": hydrate_path,
    }


def dehydration_functions():
    # There is no support for passing graph types into queries as parameters
    return {}
