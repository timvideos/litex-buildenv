from litex.gen import *
from litex.soc.interconnect import stream
from litex.gen.fhdl.structure import _Operator

# # #

def get_endpoints(obj, filt=stream.Endpoint):
    if hasattr(obj, "get_endpoints") and callable(obj.get_endpoints):
        return obj.get_endpoints(filt)
    r = dict()
    for k, v in xdir(obj, True):
        if isinstance(v, filt):
            r[k] = v
    return r

def get_single_ep(obj, filt):
    eps = get_endpoints(obj, filt)
    if len(eps) != 1:
        raise ValueError("More than one endpoint")
    return list(eps.items())[0]

# # #

def optree(op, operands, lb=None, ub=None, default=None):
    if lb is None:
        lb = 0
    if ub is None:
        ub = len(operands)
    l = ub - lb
    if l == 0:
        if default is None:
            raise AttributeError
        else:
            return default
    elif l == 1:
        return operands[lb]
    else:
        s = lb + l//2
        return _Operator(op,
            [optree(op, operands, lb, s, default),
            optree(op, operands, s, ub, default)])

# # #

def _rawbits_layout(l):
    if isinstance(l, int):
        return [("rawbits", l)]
    else:
        return l


class Cast(stream.CombinatorialActor):
    def __init__(self, layout_from, layout_to, reverse_from=False, reverse_to=False):
        self.sink = stream.Endpoint(_rawbits_layout(layout_from))
        self.source = stream.Endpoint(_rawbits_layout(layout_to))
        stream.CombinatorialActor.__init__(self)

        # # #

        sigs_from = self.sink.payload.flatten()
        if reverse_from:
            sigs_from = list(reversed(sigs_from))
        sigs_to = self.source.payload.flatten()
        if reverse_to:
            sigs_to = list(reversed(sigs_to))
        if sum(len(s) for s in sigs_from) != sum(len(s) for s in sigs_to):
            raise TypeError
        self.comb += Cat(*sigs_to).eq(Cat(*sigs_from))

# # #

class Combinator(Module):
    def __init__(self, layout, subrecords):
        self.source = stream.Endpoint(layout)
        sinks = []
        for n, r in enumerate(subrecords):
            s = stream.Endpoint(layout_partial(layout, *r))
            setattr(self, "sink"+str(n), s)
            sinks.append(s)
        self.busy = Signal()

        ###

        self.comb += [
            self.busy.eq(0),
            self.source.valid.eq(optree("&", [sink.valid for sink in sinks]))
        ]
        self.comb += [sink.ready.eq(self.source.ready & self.source.valid) for sink in sinks]
        self.comb += [self.source.payload.eq(sink.payload) for sink in sinks]
        self.comb += [self.source.param.eq(sink.param) for sink in sinks]


class Splitter(Module):
    def __init__(self, layout, subrecords):
        self.sink = stream.Endpoint(layout)
        sources = []
        for n, r in enumerate(subrecords):
            s = stream.Endpoint(layout_partial(layout, *r))
            setattr(self, "source"+str(n), s)
            sources.append(s)
        self.busy = Signal()

        ###

        self.comb += [source.payload.eq(self.sink.payload) for source in sources]
        self.comb += [source.param.eq(self.sink.param) for source in sources]
        already_acked = Signal(len(sources))
        self.sync += If(self.sink.valid,
                already_acked.eq(already_acked | Cat(*[s.ready for s in sources])),
                If(self.sink.ready, already_acked.eq(0))
            )
        self.comb += self.sink.ready.eq(optree("&",
                [s.ready | already_acked[n] for n, s in enumerate(sources)]))
        for n, s in enumerate(sources):
            self.comb += s.valid.eq(self.sink.valid & ~already_acked[n])


# Actors whose layout should be inferred from what their single sink is connected to.
layout_sink = {stream.Buffer, Splitter}
# Actors whose layout should be inferred from what their single source is connected to.
layout_source = {stream.Buffer, Combinator}
# All actors.
actors = layout_sink | layout_source

# # #

from collections import defaultdict

# Abstract actors mean that the actor class should be instantiated with the parameters
# from the dictionary. They are needed to enable actor duplication or sharing during
# elaboration, and automatic parametrization of plumbing actors.


class AbstractActor:
    def __init__(self, actor_class, parameters=dict(), name=None):
        self.actor_class = actor_class
        self.parameters = parameters
        self.name = name
        self.busy = Signal()

    def create_instance(self):
        return self.actor_class(**self.parameters)

    def __repr__(self):
        r = "<abstract " + self.actor_class.__name__
        if self.name is not None:
            r += ": " + self.name
        r += ">"
        return r


class MultiDiGraph:
    def __init__(self):
        self.edges = defaultdict(list)
        self.incoming = defaultdict(set)
        self.outgoing = defaultdict(set)
        self.nodes = set()

    def add_edge(self, a, b, **edge):
        self.edges[(a, b)].append(edge)
        self.incoming[b].add(a)
        self.outgoing[a].add(b)
        self.nodes |= {a, b}

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def edges_iter(self, data=True):
        assert data
        for (a, b), edges in self.edges.items():
            for edge in edges:
                yield a, b, edge

    def get_edge_data(self, a, b):
        return dict(enumerate(self.edges[(a, b)]))

    def add_node(self, node):
        self.nodes.add(node)

    def remove_node(self, node):
        for i in self.incoming.pop(node):
            del self.edges[(i, node)]
            self.outgoing[i].remove(node)
        for i in self.outgoing.pop(node):
            del self.edges[(node, i)]
            self.incoming[i].remove(node)
        self.nodes.remove(node)

    def remove_edge(self, a, b, key):
        e = self.edges[(a, b)]
        del e[key]
        if not e:
            self.incoming[b].remove(a)
            self.outgoing[a].remove(b)

    def in_edges(self, sink, data=True):
        assert data
        e = []
        for source in self.incoming[sink]:
            for edge in self.edges[(source, sink)]:
                e.append((source, sink, edge))
        return e

    def out_edges(self, source, data=True):
        assert data
        e = []
        for sink in self.outgoing[source]:
            for edge in self.edges[(source, sink)]:
                e.append((source, sink, edge))
        return e


# TODO: rewrite this without non-determinism
class DataFlowGraph(MultiDiGraph):
    def __init__(self):
        MultiDiGraph.__init__(self)
        self.elaborated = False
        self.abstract_busy_signals = dict()

    def add_connection(self, source_node, sink_node,
      source_ep=None, sink_ep=None,        # default: assume nodes have 1 source/sink and use that one
      source_subr=None, sink_subr=None):    # default: use whole record
        self.add_edge(source_node, sink_node,
            source=source_ep, sink=sink_ep,
            source_subr=source_subr, sink_subr=sink_subr)

    def add_buffered_connection(self, source_node, sink_node,
      source_ep=None, sink_ep=None,
      source_subr=None, sink_subr=None):
        buf = AbstractActor(stream.Buffer)
        self.add_connection(source_node, buf, source_ep=source_ep, source_subr=source_subr)
        self.add_connection(buf, sink_node, sink_ep=sink_ep, sink_subr=sink_subr)

    def add_pipeline(self, *nodes):
        for n1, n2 in zip(nodes, nodes[1:]):
            self.add_connection(n1, n2)

    def del_connections(self, source_node, sink_node, data_requirements):
        edges_to_delete = []
        edge_data = self.get_edge_data(source_node, sink_node)
        if edge_data is None:
            # the two nodes are already completely disconnected
            return
        for key, data in edge_data.items():
            if all(k not in data_requirements or data_requirements[k] == v
              for k, v in data.items()):
                edges_to_delete.append(key)
        for key in edges_to_delete:
            self.remove_edge(source_node, sink_node, key)

    def replace_actor(self, old, new):
        self.add_node(new)
        for xold, v, data in self.out_edges(old, data=True):
            self.add_edge(new, v, **data)
        for u, xold, data in self.in_edges(old, data=True):
            self.add_edge(u, new, **data)
        self.remove_node(old)

    def instantiate(self, actor):
        inst = actor.create_instance()
        self.abstract_busy_signals[id(inst)] = actor.busy
        self.replace_actor(actor, inst)

    # Returns a dictionary
    #   source -> [sink1, ..., sinkn]
    # source element is a (node, endpoint) pair.
    # sink elements are (node, endpoint, source subrecord, sink subrecord) triples.
    def _source_to_sinks(self):
        d = dict()
        for u, v, data in self.edges_iter(data=True):
            el_src = (u, data["source"])
            el_dst = (v, data["sink"], data["source_subr"], data["sink_subr"])
            if el_src in d:
                d[el_src].append(el_dst)
            else:
                d[el_src] = [el_dst]
        return d

    # Returns a dictionary
    #   sink -> [source1, ... sourcen]
    # sink element is a (node, endpoint) pair.
    # source elements are (node, endpoint, sink subrecord, source subrecord) triples.
    def _sink_to_sources(self):
        d = dict()
        for u, v, data in self.edges_iter(data=True):
            el_src = (u, data["source"], data["sink_subr"], data["source_subr"])
            el_dst = (v, data["sink"])
            if el_dst in d:
                d[el_dst].append(el_src)
            else:
                d[el_dst] = [el_src]
        return d

    # List sources that feed more than one sink.
    def _list_divergences(self):
        d = self._source_to_sinks()
        return dict((k, v) for k, v in d.items() if len(v) > 1)

    # A graph is abstract if any of these conditions is met:
    #  (1) A node is an abstract actor.
    #  (2) A subrecord is used.
    #  (3) A single source feeds more than one sink.
    # NB: It is not allowed for a single sink to be fed by more than one source
    # (except with subrecords, i.e. when a combinator is used)
    def is_abstract(self):
        return any(isinstance(x, AbstractActor) for x in self) \
            or any(d["source_subr"] is not None or d["sink_subr"] is not None
                for u, v, d in self.edges_iter(data=True)) \
            or bool(self._list_divergences())

    def _eliminate_subrecords_and_divergences(self):
        # Insert combinators.
        for (dst_node, dst_endpoint), sources in self._sink_to_sources().items():
            if len(sources) > 1 or sources[0][2] is not None:
                # build combinator
                # "layout" is filled in during instantiation
                subrecords = [dst_subrecord for src_node, src_endpoint, dst_subrecord, src_subrecord in sources]
                combinator = AbstractActor(Combinator, {"subrecords": subrecords})
                # disconnect source1 -> sink ... sourcen -> sink
                # connect source1 -> combinator_sink1 ... sourcen -> combinator_sinkn
                for n, (src_node, src_endpoint, dst_subrecord, src_subrecord) in enumerate(sources):
                    self.del_connections(src_node, dst_node,
                        {"source": src_endpoint, "sink": dst_endpoint})
                    self.add_connection(src_node, combinator,
                        src_endpoint, "sink{0}".format(n), source_subr=src_subrecord)
                # connect combinator_source -> sink
                self.add_connection(combinator, dst_node, "source", dst_endpoint)
        # Insert splitters.
        for (src_node, src_endpoint), sinks in self._source_to_sinks().items():
            if len(sinks) > 1 or sinks[0][2] is not None:
                subrecords = [src_subrecord for dst_node, dst_endpoint, src_subrecord, dst_subrecord in sinks]
                splitter = AbstractActor(Splitter, {"subrecords": subrecords})
                # disconnect source -> sink1 ... source -> sinkn
                # connect splitter_source1 -> sink1 ... splitter_sourcen -> sinkn
                for n, (dst_node, dst_endpoint, src_subrecord, dst_subrecord) in enumerate(sinks):
                    self.del_connections(src_node, dst_node,
                        {"source": src_endpoint, "sink": dst_endpoint})
                    self.add_connection(splitter, dst_node,
                        "source{0}".format(n), dst_endpoint)
                # connect source -> splitter_sink
                self.add_connection(src_node, splitter, src_endpoint, "sink")

    def _infer_plumbing_layout(self):
        while True:
            ap = [a for a in self if isinstance(a, AbstractActor) and a.actor_class in actors]
            if not ap:
                break
            for a in ap:
                in_edges = self.in_edges(a, data=True)
                out_edges = self.out_edges(a, data=True)
                if a.actor_class in layout_sink and len(in_edges) == 1:
                    other, me, data = in_edges[0]
                    if isinstance(other, AbstractActor):
                        continue
                    other_ep = data["source"]
                    if other_ep is None:
                        other_ep = get_single_ep(other, stream.Endpoint)[1]
                    else:
                        other_ep = getattr(other, other_ep)
                elif a.actor_class in layout_source and len(out_edges) == 1:
                    me, other, data = out_edges[0]
                    if isinstance(other, AbstractActor):
                        continue
                    other_ep = data["sink"]
                    if other_ep is None:
                        other_ep = get_single_ep(other, stream.Endpoint)[1]
                    else:
                        other_ep = getattr(other, other_ep)
                else:
                    raise AssertionError
                layout = other_ep.payload.layout
                a.parameters["layout"] = layout
                self.instantiate(a)

    def _instantiate_actors(self):
        # 1. instantiate all abstract non-plumbing actors
        for actor in list(self):
            if isinstance(actor, AbstractActor) and actor.actor_class not in actors:
                self.instantiate(actor)
        # 2. infer plumbing layout and instantiate plumbing
        self._infer_plumbing_layout()
        # 3. resolve default eps
        for u, v, d in self.edges_iter(data=True):
            if d["source"] is None:
                d["source"] = get_single_ep(u, stream.Endpoint)[0]
            if d["sink"] is None:
                d["sink"] = get_single_ep(v, stream.Endpoint)[0]

    # Elaboration turns an abstract DFG into a physical one.
    #   Pass 1: eliminate subrecords and divergences
    #           by inserting Combinator/Splitter actors
    #   Pass 2: run optimizer (e.g. share and duplicate actors)
    #   Pass 3: instantiate all abstract actors and explicit "None" endpoints
    def elaborate(self, optimizer=None):
        if self.elaborated:
            return
        self.elaborated = True

        self._eliminate_subrecords_and_divergences()
        if optimizer is not None:
            optimizer(self)
        self._instantiate_actors()


class CompositeActor(Module):
    def __init__(self, dfg):
        dfg.elaborate()

        # expose unconnected endpoints
        uc_eps_by_node = dict((node, get_endpoints(node)) for node in dfg)
        for u, v, d in dfg.edges_iter(data=True):
            uc_eps_u = uc_eps_by_node[u]
            source = d["source"]
            try:
                del uc_eps_u[source]
            except KeyError:
                pass
            uc_eps_v = uc_eps_by_node[v]
            sink = d["sink"]
            try:
                del uc_eps_v[sink]
            except KeyError:
                pass
        for node, uc_eps in uc_eps_by_node.items():
            for k, v in uc_eps.items():
                assert(not hasattr(self, k))
                setattr(self, k, v)

        # connect abstract busy signals
        for node in dfg:
            try:
                abstract_busy_signal = dfg.abstract_busy_signals[id(node)]
            except KeyError:
                pass
            else:
                self.comb += abstract_busy_signal.eq(node.busy)

        # generate busy signal
        self.busy = Signal()
        self.comb += self.busy.eq(optree("|", [node.busy for node in dfg]))

        # claim ownership of sub-actors and establish connections
        for node in dfg:
            self.submodules += node
        for u, v, d in dfg.edges_iter(data=True):
            ep_src = getattr(u, d["source"])
            ep_dst = getattr(v, d["sink"])
            self.comb += ep_src.connect_flat(ep_dst)


# # #

from litex.soc.interconnect.csr import *


# layout is a list of tuples, either:
# - (name, nbits, [reset value], [alignment bits])
# - (name, sublayout)

def _convert_layout(layout):
    r = []
    for element in layout:
        if isinstance(element[1], list):
            r.append((element[0], _convert_layout(element[1])))
        else:
            r.append((element[0], element[1]))
    return r

(MODE_EXTERNAL, MODE_SINGLE_SHOT, MODE_CONTINUOUS) = range(3)


class SingleGenerator(Module, AutoCSR):
    def __init__(self, layout, mode):
        self.source = stream.Endpoint(_convert_layout(layout))
        self.busy = Signal()

        self.comb += self.busy.eq(self.source.valid)

        if mode == MODE_EXTERNAL:
            self.trigger = Signal()
            trigger = self.trigger
        elif mode == MODE_SINGLE_SHOT:
            self._shoot = CSR()
            trigger = self._shoot.re
        elif mode == MODE_CONTINUOUS:
            self._enable = CSRStorage()
            trigger = self._enable.storage
        else:
            raise ValueError
        self.sync += If(self.source.ready | ~self.source.valid, self.source.valid.eq(trigger))

        self._create_csrs(layout, self.source.payload, mode != MODE_SINGLE_SHOT)

    def _create_csrs(self, layout, target, atomic, prefix=""):
        for element in layout:
            if isinstance(element[1], list):
                self._create_csrs(element[1], atomic,
                    getattr(target, element[0]),
                    element[0] + "_")
            else:
                name = element[0]
                nbits = element[1]
                if len(element) > 2:
                    reset = element[2]
                else:
                    reset = 0
                if len(element) > 3:
                    alignment = element[3]
                else:
                    alignment = 0
                regname = prefix + name
                reg = CSRStorage(nbits + alignment, reset=reset, atomic_write=atomic,
                    alignment_bits=alignment, name=regname)
                setattr(self, "_"+regname, reg)
                self.sync += If(self.source.ready | ~self.source.valid,
                    getattr(target, name).eq(reg.storage))


class Collector(Module, AutoCSR):
    def __init__(self, layout, depth=1024):
        self.sink = stream.Endpoint(layout)
        self.busy = Signal()
        dw = sum(len(s) for s in self.sink.payload.flatten())

        self._wa = CSRStorage(bits_for(depth-1), write_from_dev=True)
        self._wc = CSRStorage(bits_for(depth), write_from_dev=True, atomic_write=True)
        self._ra = CSRStorage(bits_for(depth-1))
        self._rd = CSRStatus(dw)

        ###

        mem = Memory(dw, depth)
        self.specials += mem
        wp = mem.get_port(write_capable=True)
        rp = mem.get_port()
        self.specials += wp, rp

        self.comb += [
            self.busy.eq(0),

            If(self._wc.r != 0,
                self.sink.ready.eq(1),
                If(self.sink.valid,
                    self._wa.we.eq(1),
                    self._wc.we.eq(1),
                    wp.we.eq(1)
                )
            ),
            self._wa.dat_w.eq(self._wa.storage + 1),
            self._wc.dat_w.eq(self._wc.storage - 1),

            wp.adr.eq(self._wa.storage),
            wp.dat_w.eq(self.sink.payload.raw_bits()),

            rp.adr.eq(self._ra.storage),
            self._rd.status.eq(rp.dat_r)
        ]


class _DMAController(Module):
    def __init__(self, bus_accessor, bus_aw, bus_dw, mode, base_reset=0, length_reset=0):
        self.alignment_bits = bits_for(bus_dw//8) - 1
        layout = [
            ("length", bus_aw + self.alignment_bits, length_reset, self.alignment_bits),
            ("base", bus_aw + self.alignment_bits, base_reset, self.alignment_bits)
        ]
        self.generator = SingleGenerator(layout, mode)
        self._busy = CSRStatus()

        self.length = self.generator._length.storage
        self.base = self.generator._base.storage
        if hasattr(self.generator, "trigger"):
            self.trigger = self.generator.trigger

    def get_csrs(self):
        return self.generator.get_csrs() + [self._busy]


class DMAReadController(_DMAController):
    def __init__(self, bus_accessor, *args, **kwargs):
        bus_aw = len(bus_accessor.address.a)
        bus_dw = len(bus_accessor.data.d)
        _DMAController.__init__(self, bus_accessor, bus_aw, bus_dw, *args, **kwargs)

        g = DataFlowGraph()
        g.add_pipeline(self.generator,
            misc.IntSequence(bus_aw, bus_aw),
            AbstractActor(plumbing.Buffer),
            bus_accessor,
            AbstractActor(plumbing.Buffer))
        comp_actor = CompositeActor(g)
        self.submodules += comp_actor

        self.data = comp_actor.q
        self.busy = comp_actor.busy
        self.comb += self._busy.status.eq(self.busy)


class DMAWriteController(_DMAController):
    def __init__(self, bus_accessor, *args, ack_when_inactive=False, **kwargs):
        bus_aw = len(bus_accessor.address_data.a)
        bus_dw = len(bus_accessor.address_data.d)
        _DMAController.__init__(self, bus_accessor, bus_aw, bus_dw, *args, **kwargs)

        g = DataFlowGraph()
        adr_buffer = AbstractActor(plumbing.Buffer)
        int_sequence = misc.IntSequence(bus_aw, bus_aw)
        g.add_pipeline(self.generator,
            int_sequence,
            adr_buffer)
        g.add_connection(adr_buffer, bus_accessor, sink_subr=["a"])
        g.add_connection(AbstractActor(plumbing.Buffer), bus_accessor, sink_subr=["d"])
        comp_actor = CompositeActor(g)
        self.submodules += comp_actor

        if ack_when_inactive:
            demultiplexer = plumbing.Demultiplexer([("d", bus_dw)], 2)
            self.comb += [
                demultiplexer.sel.eq(~adr_buffer.busy),
                demultiplexer.source0.connect(comp_actor.d),
                demultiplexer.source1.ready.eq(1),
            ]
            self.submodules += demultiplexer
            self.data = demultiplexer.sink
        else:
            self.data = comp_actor.d

        self.busy = comp_actor.busy
        self.comb += self._busy.status.eq(self.busy)

# # #

# Generates integers from start to maximum-1
class IntSequence(Module):
    def __init__(self, nbits, offsetbits=0, step=1):
        parameters_layout = [("maximum", nbits)]
        if offsetbits:
            parameters_layout.append(("offset", offsetbits))

        self.parameters = stream.Endpoint(parameters_layout)
        self.source = stream.Endpoint([("value", max(nbits, offsetbits))])
        self.busy = Signal()

        ###

        load = Signal()
        ce = Signal()
        last = Signal()

        maximum = Signal(nbits)
        if offsetbits:
            offset = Signal(offsetbits)
        counter = Signal(nbits)

        if step > 1:
            self.comb += last.eq(counter + step >= maximum)
        else:
            self.comb += last.eq(counter + 1 == maximum)
        self.sync += [
            If(load,
                counter.eq(0),
                maximum.eq(self.parameters.maximum),
                offset.eq(self.parameters.offset) if offsetbits else None
            ).Elif(ce,
                If(last,
                    counter.eq(0)
                ).Else(
                    counter.eq(counter + step)
                )
            )
        ]
        if offsetbits:
            self.comb += self.source.value.eq(counter + offset)
        else:
            self.comb += self.source.value.eq(counter)

        fsm = FSM()
        self.submodules += fsm
        fsm.act("IDLE",
            load.eq(1),
            self.parameters.ready.eq(1),
            If(self.parameters.valid, NextState("ACTIVE"))
        )
        fsm.act("ACTIVE",
            self.busy.eq(1),
            self.source.valid.eq(1),
            If(self.source.ready,
                ce.eq(1),
                If(last, NextState("IDLE"))
            )
        )