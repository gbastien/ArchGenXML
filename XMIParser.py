#-----------------------------------------------------------------------------
# Name:        XMIParser.py
# Purpose:     Parse XMI (UML-model) and provide a logical model of it
#
# Author:      Philipp Auersperg
#
# Created:     2003/19/07
# RCS-ID:      $Id$
# Copyright:   (c) 2003 BlueDynamics
# Licence:     GPL
#-----------------------------------------------------------------------------

import sys, os.path, time, string
import getopt
from utils import mapName,toBoolean
from utils import wrap as doWrap
from xml.dom import minidom
from sets import Set
from odict import odict
from types import StringTypes

has_stripogram = 1
try:
    from stripogram import html2text
except ImportError:
    has_stripogram = 0
    def html2text(s, *args, **kwargs):
        return s

#set default wrap width
default_wrap_width = 64

#tag constants

clean_trans = string.maketrans(':-. /$', '______')

class XMI1_0:
    XMI_CONTENT = "XMI.content"
    OWNED_ELEMENT = "Foundation.Core.Namespace.ownedElement"

    # XMI version specific stuff goes there
    STATEMACHINE = 'Behavioral_Elements.State_Machines.StateMachine'
    STATE = 'Behavioral_Elements.State_Machines.State'
    TRANSITION = 'Behavioral_Elements.State_Machines.Transition'
    # each TRANSITION has (in its defn) a TRIGGER which is an EVENT
    EVENT = 'Behavioral_Elements.State_Machines.SignalEvent'
    # and a TARGET (and its SOURCE) which has a STATE
    SOURCE = 'Behavioral_Elements.State_Machines.Transition.source'
    TARGET = 'Behavioral_Elements.State_Machines.Transition.target'
    # ACTIONBODY gives us the rate of the transition
    ACTIONBODY = 'Foundation.Data_Types.Expression.body'

    # STATEs and EVENTs both have NAMEs
    NAME = 'Foundation.Core.ModelElement.name'

    #Collaboration stuff: a
    COLLAB = 'Behavioral_Elements.Collaborations.Collaboration'
    # has some
    CR = 'Behavioral_Elements.Collaborations.ClassifierRole'
    # each of which has a
    BASE = 'Behavioral_Elements.Collaborations.ClassifierRole.base'
    # which we will assume to be a CLASS, collapsing otherwise
    CLASS = 'Foundation.Core.Class'
    PACKAGE = 'Model_Management.Package'
    # To match up a CR with the right start state, we look out for the context
    CONTEXT = 'Behavioral_Elements.State_Machines.StateMachine.context'
    MODEL = 'Model_Management.Model'
    MULTIPLICITY = 'Foundation.Core.StructuralFeature.multiplicity'
    MULT_MIN = 'Foundation.Data_Types.MultiplicityRange.lower'
    MULT_MAX = 'Foundation.Data_Types.MultiplicityRange.upper'
    ATTRIBUTE = 'Foundation.Core.Attribute'
    DATATYPE = 'Foundation.Core.DataType'
    FEATURE = 'Foundation.Core.Classifier.feature'
    TYPE = 'Foundation.Core.StructuralFeature.type'
    ASSOCEND_PARTICIPANT = CLASSIFIER = 'Foundation.Core.Classifier'
    ASSOCIATION = 'Foundation.Core.Association'
    ASSOCIATION_CLASS = 'Foundation.Core.AssociationClass'
    AGGREGATION = 'Foundation.Core.AssociationEnd.aggregation'
    ASSOCEND = 'Foundation.Core.AssociationEnd'
    ASSOCENDTYPE = 'Foundation.Core.AssociationEnd.type'

    METHOD = "Foundation.Core.Operation"
    METHODPARAMETER = "Foundation.Core.Parameter"
    PARAM_DEFAULT = "Foundation.Core.Parameter.defaultValue"
    EXPRESSION = "Foundation.Data_Types.Expression"
    EXPRESSION_BODY = "Foundation.Data_Types.Expression.body"

    GENERALIZATION = "Foundation.Core.Generalization"
    GEN_CHILD = "Foundation.Core.Generalization.child"
    GEN_PARENT = "Foundation.Core.Generalization.parent"
    GEN_ELEMENT = "Foundation.Core.GeneralizableElement"

    TAGGED_VALUE_MODEL = "Foundation.Core.ModelElement.taggedValue"
    TAGGED_VALUE = "Foundation.Extension_Mechanisms.TaggedValue"
    TAGGED_VALUE_TAG = "Foundation.Extension_Mechanisms.TaggedValue.tag"
    TAGGED_VALUE_VALUE = "Foundation.Extension_Mechanisms.TaggedValue.value"

    ATTRIBUTE_INIT_VALUE = "Foundation.Core.Attribute.initialValue"
    STEREOTYPE = "Foundation.Extension_Mechanisms.Stereotype"
    STEREOTYPE_MODELELEMENT = "Foundation.Extension_Mechanisms.Stereotype.extendedElement"
    MODELELEMENT = "Foundation.Core.ModelElement"
    ISABSTRACT = "Foundation.Core.GeneralizableElement.isAbstract"
    INTERFACE = "Foundation.Core.Interface"
    ABSTRACTION = "Foundation.Core.Abstraction"
    DEPENDENCY = "Foundation.Core.Dependency"
    DEP_CLIENT = "Foundation.Core.Dependency.client"
    DEP_SUPPLIER = "Foundation.Core.Dependency.supplier"

    BOOLEAN_EXPRESSION = "Foundation.Data_Types.BooleanExpression"
    #State Machine

    STATEMACHINE = 'Behavioral_Elements.State_Machines.StateMachine'
    STATEMACHINE_CONTEXT = "Behavioral_Elements.State_Machines.StateMachine.context"
    STATEMACHINE_TOP = "Behavioral_Elements.State_Machines.StateMachine.top"
    COMPOSITESTATE = "Behavioral_Elements.State_Machines.CompositeState"
    COMPOSITESTATE_SUBVERTEX = "Behavioral_Elements.State_Machines.CompositeState.subvertex"
    SIMPLESTATE = "Behavioral_Elements.State_Machines.State"
    PSEUDOSTATE = "Behavioral_Elements.State_Machines.Pseudostate"
    PSEUDOSTATE_KIND = "Behavioral_Elements.State_Machines.Pseudostate.kind"
    FINALSTATE = "Behavioral_Elements.State_Machines.Finalstate"
    STATEVERTEX_OUTGOING = "Behavioral_Elements.State_Machines.StateVertex.outgoing"
    STATEVERTEX_INCOMING = "Behavioral_Elements.State_Machines.StateVertex.incoming"
    TRANSITION = "Behavioral_Elements.State_Machines.Transition"
    STATEMACHINE_TRANSITIONS = "Behavioral_Elements.State_Machines.StateMachine.transitions"
    TRANSITON_TARGET = "Behavioral_Elements.State_Machines.Transition.target"
    TRANSITION_SOURCE = "Behavioral_Elements.State_Machines.Transition.source"
    TRANSITION_EFFECT = "Behavioral_Elements.State_Machines.Transition.effect"
    TRANSITION_GUARD = "Behavioral_Elements.State_Machines.Transition.guard"

    ACTION_SCRIPT = "Behavioral_Elements.Common_Behavior.Action.script"
    ACTION_EXPRESSION = "Foundation.Data_Types.ActionExpression"
    ACTION_EXPRESSION_BODY = "Foundation.Data_Types.Expression.body"

    DIAGRAM = "UML:Diagram"
    DIAGRAM_OWNER = "UML:Diagram.owner"
    DIAGRAM_SEMANTICMODEL_BRIDGE = "UML:Uml1SemanticModelBridge"
    DIAGRAM_SEMANTICMODEL_BRIDGE_ELEMENT = "UML:Uml1SemanticModelBridge.element"
    ACTOR = "Behavioral_Elements.Use_Cases.Actor"

    aggregates = ['composite', 'aggregate']

#    generate_datatypes=['field','compound_field']

    def __init__(self,**kw):
        self.__dict__.update(kw)
        
    def getName(self, domElement):
        try:
            return str(getAttributeValue(domElement, self.NAME)).strip()
        except:
            return None

    def getId(self, domElement):
        return domElement.getAttribute('xmi.id').strip()

    def getIdRef(self, domElement):
        return domElement.getAttribute('xmi.idref').strip()

    def getAssocEndParticipantId(self, el):
        assocend = getElementByTagName(el, self.ASSOCEND_PARTICIPANT, None)

        if not assocend:
            assocend = getElementByTagName(el, self.ASSOCENDTYPE, None)

        if not assocend:
            return None

        classifier = getSubElement(assocend)

        if not classifier:
            print 'Warning: No assocEnd participant found  for: ', XMI.getId(el)
            return None

        return classifier.getAttribute('xmi.idref')

    def isAssocEndAggregation(self, el):
        aggs = el.getElementsByTagName(XMI.AGGREGATION)
        return aggs and aggs[0].getAttribute('xmi.value') in self.aggregates

    def getAssocEndAggregation(self, el):
        aggs = el.getElementsByTagName(XMI.AGGREGATION)
        if not aggs:
            return None
        return aggs[0].getAttribute('xmi.value')

    def getMultiplicity(self, el, multmin=0, multmax=-1):
        mult_min = int(getAttributeValue(el, self.MULT_MIN, default=multmin, recursive=1))
        mult_max = int(getAttributeValue(el, self.MULT_MAX, default=multmax, recursive=1))
        return (mult_min, mult_max)

    def buildRelations(self, doc, objects):
        #XXX: needs refactoring
        rels = doc.getElementsByTagName(XMI.ASSOCIATION) + \
            doc.getElementsByTagName(XMI.ASSOCIATION_CLASS)
        for rel in rels:
            master = None
            detail = None
            ends = rel.getElementsByTagName(XMI.ASSOCEND)
            #assert len(ends) == 2
            if len(ends) != 2:
                #print 'association with != 2 ends found'
                continue

            if self.isAssocEndAggregation(ends[0]) :
                master = ends[0]
                detail = ends[1]
            if self.isAssocEndAggregation(ends[1]) :
                master = ends[1]
                detail = ends[0]

            if master: #ok weve found an aggregation
                masterid = self.getAssocEndParticipantId(master)
                detailid = self.getAssocEndParticipantId(detail)

                #print 'master, detail:', master, detail
                m = objects.get(masterid, None)
                d = objects.get(detailid, None)

                if not m:
                    print 'Warning: Master Object not found for aggregation relation: id=%s' % (XMI.getId(master))
                    continue

                if not d:
                    print 'Warning: Child Object not found for aggregation relation: parent=%s' % (m.getName())
                    continue

                try:
                    m.addSubType(d)
                except KeyError:
                    print 'Warning: Child Object not found for aggregation relation:Child :%s(%s), parent=%s' % (d.getId(), d.getName(), XMI.getName(m))
                    continue

                assoc = XMIAssociation(rel)
                assoc.fromEnd.obj.addAssocFrom(assoc)
                assoc.toEnd.obj.addAssocTo(assoc)

            else: #its an assoc, lets model it as association
                try:
                    #check if an association class already exists
                    relid = self.getId(rel)
                    if allObjects.has_key(relid):
                        assoc = allObjects[relid]
                        assoc.calcEnds()
                    else:
                        assoc = XMIAssociation(rel)
                except KeyError:
                    print 'Warning: Child Object not found for aggregation:%s, parent=%s' % (XMI.getId(rel), XMI.getName(master))
                    continue

                if getattr(assoc.fromEnd, 'obj', None) and getattr(assoc.toEnd, 'obj', None):
                    assoc.fromEnd.obj.addAssocFrom(assoc)
                    assoc.toEnd.obj.addAssocTo(assoc)
                else:
                    print 'Warning:Association has no ends:', assoc.getId()


    def buildGeneralizations(self, doc, objects):
        gens = doc.getElementsByTagName(XMI.GENERALIZATION)

        for gen in gens:
            if not self.getId(gen):continue
            try:
                par0 = getElementByTagName(gen, self.GEN_PARENT, recursive=1)
                child0 = getElementByTagName(gen, self.GEN_CHILD, recursive=1)
                try:
                    #par=objects[getElementByTagName(par0, self.GEN_ELEMENT).getAttribute('xmi.idref')]
                    par = objects[getSubElement(par0).getAttribute('xmi.idref')]
                except KeyError:
                    print 'Warning: Parent Object not found for generalization relation:%s, parent %s' % (XMI.getId(gen), XMI.getName(par0))
                    continue

                #child=objects[getElementByTagName(child0, self.GEN_ELEMENT).getAttribute('xmi.idref')]
                child = objects[getSubElement(child0).getAttribute('xmi.idref')]

                par.addGenChild(child)
                child.addGenParent(par)
            except IndexError:
                print 'gen: index error for generalization:%s'%self.getId(gen)
                raise
                pass

    def buildRealizations(self, doc, objects):
        abs = doc.getElementsByTagName(XMI.ABSTRACTION)

        for ab in abs:
            if not self.getId(ab):continue
            abstraction = XMIAbstraction(ab)
            if not abstraction.hasStereoType('realize'):
                print 'skip dep:', abstraction.getStereoType()
                continue
            try:
                try:
                    par0 = getElementByTagName   (ab, self.DEP_SUPPLIER, recursive=1)
                    par = objects[getSubElement(par0, ignoremult=1).getAttribute('xmi.idref')]
                #    continue
                except (KeyError, IndexError):
                    print 'Warning: Parent Object not found for realization relation:%s, parent %s' % (XMI.getId(ab), XMI.getName(par0))
                    continue

                #child=objects[getElementByTagName(child0, self.REALIZATION_ELEMENT).getAttribute('xmi.idref')]
                try:
                    child0 = getElementByTagName (ab, self.DEP_CLIENT, recursive=1)
                    child_xmid = getSubElement(child0, ignoremult=1).getAttribute('xmi.idref')
                    child = objects[child_xmid]
                except (KeyError, IndexError):
                    print 'Warning: Child element for realization relation not found, parent name + relation xmi_id given:', par.getName(), XMI.getId(ab)

                par.addRealizationChild(child)
                child.addRealizationParent(par)
            except IndexError:
                print 'ab: index error for dependencies:%s'%self.getId(ab)
                raise

    def buildDependencies(self, doc, objects):
        deps = doc.getElementsByTagName(XMI.DEPENDENCY)

        for dep in deps:
            if not self.getId(dep):continue
            depencency = XMIDependency(dep, allObjects=objects)
            
            

    def getExpressionBody(self, element, tagname = None):
        if not tagname:
            tagname = XMI.EXPRESSION
        exp = getElementByTagName(element, XMI.EXPRESSION_BODY, recursive=1, default=None)
        if exp and exp.firstChild:
            return exp.firstChild.nodeValue
        else:
            return None

    def getTaggedValue(self, el):
        #print 'getTaggedValue:', el
        tagname = getAttributeValue(el, XMI.TAGGED_VALUE_TAG, recursive=0, default=None)
        if not tagname:
            raise TypeError, 'element %s has empty taggedValue' % self.getId(el)

        tagvalue = getAttributeValue(el, XMI.TAGGED_VALUE_VALUE, recursive=0, default=None)
        return tagname, tagvalue

    def collectTagDefinitions(self, el):
        ''' dummy function, only needed in xmi >=1.1'''
        pass

    def calculateStereoType(self, o):
        #in xmi its weird, because all objects to which a
        #stereotype applies are stored in the stereotype
        #while in xmi 1.2 its opposite
        for k in stereotypes.keys():
            st = stereotypes[k]
            els = st.getElementsByTagName(self.MODELELEMENT)
            for el in els:
                if el.getAttribute('xmi.idref') == o.getId():
                    name = self.getName(st)
                    #print 'Stereotype found:', name
                    o.setStereoType(name)

    def calcClassAbstract(self, o):
        abs = getElementByTagName(o.domElement, XMI.ISABSTRACT, None)
        if abs:
            o.isabstract = abs.getAttribute('xmi.value') == 'true'
        else:
            o.isabstract = 0

    def calcVisibility(self, o):
        # visibility detection unimplemented for XMI 1.0
        o.visibility = None

    def calcDatatype(self, att):
        global datatypes
        typeinfos = att.domElement.getElementsByTagName(XMI.TYPE)
        if len(typeinfos):
            classifiers = typeinfos[0].getElementsByTagName(XMI.CLASSIFIER)
            if len(classifiers):
                typeid = str(classifiers[0].getAttribute('xmi.idref'))
                typeElement = datatypes[typeid]
                #self.type=getAttributeValue(typeElement, XMI.NAME)
                att.type = XMI.getName(typeElement)
                if att.type not in datatypenames: #collect all datatype names (to prevent pure datatype classes from being generated)
                    datatypenames.append(att.type)
                #print 'attribute:'+self.getName(), typeid, self.type

    def getPackageElements(self, el):
        ''' gets all package nodes below the current node (only one level)'''
        res = []
        #in case the el is a document we have to crawl down until we have ownedElements
        ownedElements = getElementByTagName(el, self.OWNED_ELEMENT, default=None)
        if not ownedElements:
            if el.tagName == self.PACKAGE:
                return []
            el = getElementByTagName(el, self.MODEL, recursive=1)


        ownedElements = getElementByTagName(el, self.OWNED_ELEMENT)
        res = getElementsByTagName(ownedElements, self.PACKAGE)

        return res


    def getOwnedElement(self, el):
        return getElementByTagName(el, self.OWNED_ELEMENT, default=None)

    def getContent(self, doc):
        content = getElementByTagName(doc, XMI.XMI_CONTENT, recursive=1)

        return content

    def getModel(self, doc):
        content = self.getContent(doc)
        model = getElementByTagName(content, XMI.MODEL, recursive=0)

        return model

    def getGenerator(self):
        return getattr(self, 'generator', None)

    def getGenerationOption(self, opt):
        return getattr(self.getGenerator(), opt, None)


class XMI1_1 (XMI1_0):
    # XMI version specific stuff goes there

    tagDefinitions = None

    NAME = 'UML:ModelElement.name'
    OWNED_ELEMENT = "UML:Namespace.ownedElement"

    MODEL = 'UML:Model'
    #Collaboration stuff: a
    COLLAB = 'Behavioral_Elements.Collaborations.Collaboration'
    CLASS = 'UML:Class'
    PACKAGE = 'UML:Package'

    # To match up a CR with the right start state, we look out for the context
    MULTIPLICITY = 'UML:StructuralFeature.multiplicity'
    ATTRIBUTE = 'UML:Attribute'
    DATATYPE = 'UML:DataType'
    FEATURE = 'UML:Classifier.feature'
    TYPE = 'UML:StructuralFeature.type'
    CLASSIFIER = 'UML:Classifier'
    ASSOCIATION = 'UML:Association'
    AGGREGATION = 'UML:AssociationEnd.aggregation'
    ASSOCEND = 'UML:AssociationEnd'
    ASSOCENDTYPE = 'UML:AssociationEnd.type'
    ASSOCEND_PARTICIPANT = 'UML:AssociationEnd.participant'
    METHOD = "UML:Operation"
    METHODPARAMETER = "UML:Parameter"
    MULTRANGE = 'UML:MultiplicityRange'

    MULT_MIN = 'UML:MultiplicityRange.lower'
    MULT_MAX = 'UML:MultiplicityRange.upper'

    GENERALIZATION = "UML:Generalization"
    GEN_CHILD = "UML:Generalization.child"
    GEN_PARENT = "UML:Generalization.parent"
    GEN_ELEMENT = "UML:Class"

    ATTRIBUTE_INIT_VALUE = "UML:Attribute.initialValue"
    EXPRESSION = "UML:Expression"
    PARAM_DEFAULT = "UML:Parameter.defaultValue"

    TAG_DEFINITION = "UML:TagDefinition"

    TAGGED_VALUE_MODEL = "UML:ModelElement.taggedValue"
    TAGGED_VALUE = "UML:TaggedValue"
    TAGGED_VALUE_TAG = "UML:TaggedValue.tag"
    TAGGED_VALUE_VALUE = "UML:TaggedValue.value"

    MODELELEMENT = "UML:ModelElement"
    STEREOTYPE_MODELELEMENT = "UML:ModelElement.stereotype"

    STEREOTYPE = "UML:Stereotype"
    ISABSTRACT = "UML:GeneralizableElement.isAbstract"
    INTERFACE = "UML:Interface"

    ABSTRACTION = "UML:Abstraction"

    DEPENDENCY = "UML:Dependency"
    DEP_CLIENT = "UML:Dependency.client"
    DEP_SUPPLIER = "UML:Dependency.supplier"

    ASSOCIATION_CLASS = 'UML:AssociationClass'
    BOOLEAN_EXPRESSION = ["UML:BooleanExpression","UML2:OpaqueExpression"]

    #State Machine

    STATEMACHINE = "UML:StateMachine","UML2:StateMachine"
    STATEMACHINE_CONTEXT = "UML:StateMachine.context"
    STATEMACHINE_TOP = "UML:StateMachine.top"
    COMPOSITESTATE = "UML:CompositeState"
    COMPOSITESTATE_SUBVERTEX = "UML:CompositeState.subvertex"
    SIMPLESTATE = "UML:SimpleState","UML2:State"
    PSEUDOSTATE = "UML:Pseudostate","UML2:PseudoState"
    PSEUDOSTATE_KIND = "kind"
    FINALSTATE = "UML:FinalState","UML2:FinalState"
    STATEVERTEX_OUTGOING = "UML:StateVertex.outgoing","UML2:Vertex.outgoing"
    STATEVERTEX_INCOMING = "UML:StateVertex.incoming","UML2:Vertex.incoming"
    TRANSITION = "UML:Transition","UML2:Transition"
    STATEMACHINE_TRANSITIONS = "UML:StateMachine.transitions"
    TRANSITON_TARGET = "UML:Transition.target","UML2:Transition.target"
    TRANSITION_SOURCE = "UML:Transition.source","UML2:Transition.source"
    TRANSITION_EFFECT = "UML:Transition.effect","UML2:Transition.effect"
    TRANSITION_GUARD = "UML:Transition.guard", "UML2:Transition.guard"
    OWNED_BEHAVIOR = "UML2:BehavioredClassifier.ownedBehavior"

    ACTION_SCRIPT = "UML:Action.script"
    ACTION_EXPRESSION = "UML:ActionExpression"
    ACTION_EXPRESSION_BODY = "UML:ActionExpression.body"

    DIAGRAM = "UML:Diagram"
    DIAGRAM_OWNER = "UML:Diagram.owner"
    DIAGRAM_SEMANTICMODEL_BRIDGE = "UML:Uml1SemanticModelBridge"
    DIAGRAM_SEMANTICMODEL_BRIDGE_ELEMENT = "UML:Uml1SemanticModelBridge.element"
    ACTOR = "UML:Actor"

    def getName(self, domElement):
        if domElement:
            return domElement.getAttribute('name').strip()
        else:
            return ''

    def getExpressionBody(self, element, tagname=None):
        if not tagname:
            tagname = XMI.EXPRESSION

        exp = getElementByTagName(element, tagname, recursive=1, default=None)
        if exp:
            return exp.getAttribute('body')
        else:
            return None



class XMI1_2 (XMI1_1):
    TAGGED_VALUE_VALUE = "UML:TaggedValue.dataValue"
    # XMI version specific stuff goes there

    #def getAssocEndParticipantId(self, el):
    #    return getElementByTagName(getElementByTagName(el, self.ASSOCEND_PARTICIPANT), self.CLASS).getAttribute('xmi.idref')

    def isAssocEndAggregation(self, el):
        return str(el.getAttribute('aggregation')) in self.aggregates

    def getAssocEndAggregation(self, el):
        return str(el.getAttribute('aggregation'))

    def getMultiplicity(self, el, multmin=0,multmax=-1):
        min = getElementByTagName(el, self.MULTRANGE, default=None, recursive=1)
        max = getElementByTagName(el, self.MULTRANGE, default=None, recursive=1)

        if min:
            mult_min = int(min.getAttribute('lower'))
        else:
            mult_min = multmin

        if max:
            mult_max = int(max.getAttribute('upper'))
        else:
            mult_max = multmax

        return (mult_min, mult_max)

    def getTaggedValue(self, el):
        tdef = getElementByTagName(el, self.TAG_DEFINITION, default=None, recursive=1)
        # fetch the name from the global tagDefinitions (weird)
        tagname = self.tagDefinitions[tdef.getAttribute('xmi.idref')].getAttribute('name')
        tagvalue = getAttributeValue(el, self.TAGGED_VALUE_VALUE, default=None)
        return tagname, tagvalue

    def collectTagDefinitions(self, el):
        tagdefs = el.getElementsByTagName(self.TAG_DEFINITION)
        if self.tagDefinitions is None:
            self.tagDefinitions = {}

        for t in tagdefs:
            if t.hasAttribute('name'):
                self.tagDefinitions[t.getAttribute('xmi.id')] = t

    def calculateStereoType(self, o):
        #in xmi its weird, because all objects to which a
        #stereotype applies are stored in the stereotype
        #while in xmi 1.2 its opposite

        sts = getElementsByTagName(o.domElement, self.STEREOTYPE_MODELELEMENT, recursive=0)
        for st in sts:
            strefs = getSubElements(st)
            for stref in strefs:
                id = stref.getAttribute('xmi.idref').strip()
                if id:
                    st = stereotypes[id]
                    o.addStereoType(self.getName(st).strip())
                    #print 'stereotype found:', id, self.getName(st), o.getStereoType()
                else:
                    print 'warning: empty stereotype id for class :', o.getName(), o.getId()


    def calcClassAbstract(self, o):
        o.isabstract = o.domElement.hasAttribute('isAbstract') and o.domElement.getAttribute('isAbstract') == 'true'
        #print 'xmi12_calcabstract:', o.getName(), o.isAbstract()

    def calcVisibility(self, o):
        o.visibility = o.domElement.hasAttribute('visibility') and o.domElement.getAttribute('visibility')
        #print 'xmi12_calcVisibility:', o.getName(), o.getVisibility()

    def calcDatatype(self, att):
        global datatypes
        typeinfos = att.domElement.getElementsByTagName(XMI.TYPE)
        if len(typeinfos):
            classifiers = [cn for cn in typeinfos[0].childNodes if cn.nodeType == cn.ELEMENT_NODE] #getElementsByTagName(XMI.CLASS)
            #assert len(classifiers) == 1
            if len(classifiers):
                #print 'classifier found for 1.2'
                typeid = str(classifiers[0].getAttribute('xmi.idref'))
                try:
                    typeElement = datatypes[typeid]
                except KeyError:
                    raise ValueError, 'datatype %s not defined' % typeid
                #self.type=getAttributeValue(typeElement, XMI.NAME)
                att.type = XMI.getName(typeElement)
                if att.type not in datatypenames: #collect all datatype names (to prevent pure datatype classes from being generated)
                    datatypenames.append(att.type)
                #print 'attribute:'+self.getName(), typeid, self.type



class NoObject:
    pass

_marker = NoObject()

allObjects = {}

def getSubElements(domElement):
    return [e for e in domElement.childNodes if e.nodeType == e.ELEMENT_NODE]

def getSubElement(domElement, default=_marker, ignoremult=0):
    els = getSubElements(domElement)
    if len(els) > 1 and not ignoremult:
        raise TypeError, 'more than 1 element found'

    try:
        return els[0]
    except IndexError:
        if default == _marker:
            raise
        else:
            return default


def getAttributeValue(domElement, tagName=None, default=_marker, recursive=0):
    el = domElement
    el.normalize()


    if tagName:
        try:
            el = getElementByTagName(domElement, tagName, recursive=recursive)

        except IndexError:
            if default == _marker:
                raise
            else:
                return default

    if el.hasAttribute('xmi.value'):
        return el.getAttribute('xmi.value')

    if not el.firstChild and default != _marker:
        return default

    return el.firstChild.nodeValue

def getAttributeOrElement(domElement, name, default=_marker, recursive=0):
    ''' tries t get the value from an attribute, if not found, it tries to get
        it from a subelement that has the name {element.name}.{name}
        '''
    val = domElement.getAttribute(name)

    if not val:
        val = getAttributeValue(domElement, domElement.tagName+'.'+name, default, recursive)

    return val

def getElementsByTagName(domElement, tagName, recursive=0):
    ''' returns elements by tag name , the only difference
        to the original getElementsByTagName is, that the optional recursive
        parameter
        '''

    if type(tagName) in StringTypes:
        tagNames=[tagName]
    else:
        tagNames=tagName
        
    if recursive:
        els = []
        for tag in tagNames:
            els.extend(domElement.getElementsByTagName(tag))
    else:
        els = [el for el in domElement.childNodes if str(getattr(el, 'tagName', None)) in tagNames]

    return els

def getElementByTagName(domElement, tagName, default=_marker, recursive=0):
    ''' returns a single element by name and throws an error if more than 1 exist'''
    els = getElementsByTagName(domElement,tagName,recursive=recursive)

    if len(els) > 1:
        raise TypeError, 'more than 1 element found'

    try:
        return els[0]
    except IndexError:
        if default == _marker:
             raise
        else:
            return default

def hasClassFeatures(domClass):

    return len(domClass.getElementsByTagName(XMI.FEATURE)) or           \
                len(domClass.getElementsByTagName(XMI.ATTRIBUTE)) or    \
                len(domClass.getElementsByTagName(XMI.METHOD))

class PseudoElement:
    #urgh, needed to pretend a class
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def getName(self):
        return self.name

    def getModuleName(self):
        return self.getName()


class XMIElement:
    package = None
    parent = None

    def __init__(self, domElement=None, name='', *args, **kwargs):
        self.domElement = domElement
        self.name = name
        self.cleanName = ''
        self.atts = {}
        self.children = []
        self.maxOccurs = 1
        self.complex = 0
        self.type = 'NoneType'
        self.attributeDefs = []
        self.methodDefs = []
        self.id = ''
        self.taggedValues = odict()
        self.subTypes = []
        self.stereoTypes = []
        self.clientDependencies = []
        
        self.annotations = {} # space to store values by external access. use
                             # annotate() to store values in this dict, and
                             # getAnnotation() to fetch it.

        #take kwargs as attributes
        self.__dict__.update(kwargs)
        if domElement:
            allObjects[domElement.getAttribute('xmi.id')] = self
            self.initFromDOM(domElement)
            self.buildChildren(domElement)

    def getId(self):
        return self.id

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def parseTaggedValues(self):
        ''' '''
        tgvsm = getElementByTagName(self.domElement, XMI.TAGGED_VALUE_MODEL, default=None, recursive=0)
        if tgvsm is None:
            return

        tgvs = getElementsByTagName(tgvsm, XMI.TAGGED_VALUE, recursive=0)
        for tgv in tgvs:
            try:
                tagname, tagvalue = XMI.getTaggedValue(tgv)
                if self.taggedValues.has_key(tagname):
                    # poseidon multiline fix
                    self.taggedValues[tagname] += '\n'+tagvalue
                else:
                    self.taggedValues[tagname] = tagvalue
            except TypeError, e:
                print 'Warning: broken tagged value in xmi.id %s:' % XMI.getId(self.domElement)
                pass

        #print 'taggedValues:', self.__class__, self.getName(), self.getTaggedValues()

    def setTaggedValue(self, k, v):
        self.taggedValues[k] = v

    def initFromDOM(self, domElement):
        if not domElement:
            domElement = self.domElement

        if domElement:
            self.id = domElement.getAttribute('xmi.id')
            self.name = XMI.getName(domElement)
            #print 'name:', self.name, self.id
            self.parseTaggedValues()
            self.calculateStereoType()
            mult = getElementByTagName(domElement, XMI.MULTIPLICITY, None)
            if mult:
                maxNodes = mult.getElementsByTagName(XMI.MULT_MAX)
                if maxNodes and len(maxNodes):
                    maxNode = maxNodes[0]
                    self.maxOccurs = int(getAttributeValue(maxNode))
                    if self.maxOccurs == -1:
                        self.maxOccurs = 99999

                    #print 'maxOccurs:', self.maxOccurs

            domElement.xmiElement = self
            self.createCleanName()


    def addChild(self, element):
        self.children.append(element)
    def addSubType(self, st):
        self.subTypes.append(st)

    def getChildren(self): return self.children
    def getName(self):
        name = str(self.name)
        if self.name:
            res = name
        else:
            res = self.id

        if type(res) in (type(''), type(u'')):
            res = res.strip()
        return res

    def getCleanName(self): return self.cleanName

    def getTaggedValue(self, name, default=''):
        res = self.taggedValues.get(name, default)
        if type(res) in (type(''), type(u'')):
            res = res.strip()
        return res

    def hasTaggedValue(self, name):
        return self.taggedValues.has_key(name)

    def hasAttributeWithTaggedValue(self, tag, value=None):
        ''' returns true, if any attribute has a TGV with tag
            and (if given) if its equals value.
        '''
        attrs = self.getAttributeDefs()
        for attr in attrs:
            if attr.hasTaggedValue(tag):
                if not value or attr.getTaggedValue(tag, None) == value:
                    return 1
        return 0

    def getTaggedValues(self):
        return self.taggedValues

    def getDocumentation(self, striphtml=0, wrap=-1):
        """ return formatted documentation string:

            try to use stripogram to remove (e.g. poseidon) HTML-tags, wrap and
            indent text. If no stripogram is present it uses wrap and indent
            from own utils module.

            striphtml(boolean) - use stripogram html2text to remove html tags
            wrap(integer)      - default: 60, set to 0: do not wrap,
                                 all other >0: wrap with this value
        """
        #TODO: create an option on command line to control the page width
        doc = self.getTaggedValue('documentation')
        if not doc:
            return ''
        if wrap == -1:
            wrap = default_wrap_width
        if has_stripogram and striphtml:
            doc = html2text(doc, (), 0, 1000000).strip()
        if wrap:
            doc = doWrap(doc, wrap)
        return doc

    def getUnmappedCleanName(self): return self.unmappedCleanName
    def setName(self, name): self.name = name;self.createCleanName()
    def getAttrs(self): return self.attrs
    def getMaxOccurs(self): return self.maxOccurs
    def getType(self): return self.type
    def isComplex(self): return self.complex
    def addAttributeDef(self, attrs, pos=None):
        if pos is None:
            self.attributeDefs.append(attrs)
        else:
            self.attributeDefs.insert(0, attrs)

    def getAttributeDefs(self): return self.attributeDefs

    def getRef(self):
        return None

    def getRefs(self):
        ''' return all referenced schema names '''

        return [str(c.getRef()) for c in self.getChildren() if c.getRef()]

    def show(self, outfile, level):
        showLevel(outfile, level)
        outfile.write('Name: %s  Type: %s\n' % (self.name, self.type))
        showLevel(outfile, level)
        outfile.write('  - Complex: %d  MaxOccurs: %d\n' % \
            (self.complex, self.maxOccurs))
        showLevel(outfile, level)
        outfile.write('  - Attrs: %s\n' % self.attrs)
        showLevel(outfile, level)
        outfile.write('  - AttributeDefs: %s\n' % self.attributeDefs)
        for key in self.attributeDefs.keys():
            showLevel(outfile, level + 1)
            outfile.write('key: %s  value: %s\n' % \
                (key, self.attributeDefs[key]))
        for child in self.getChildren():
            child.show(outfile, level + 1)

    def addMethodDefs(self, m):
        if m.getName():
            self.methodDefs.append(m)


    def createCleanName(self):
        # If there is a namespace, replace it with an underscore.
        if self.getName():
            self.unmappedCleanName = str(self.getName()).translate(clean_trans)
        else:
            self.unmappedCleanName = ''

        self.cleanName = mapName(self.unmappedCleanName)

    def isIntrinsicType(self):
        return str(self.getType()).startswith('xs:')

    def buildChildren(self, domElement):
        pass

    def getMethodDefs(self, recursive=0):
        res = [m for m in self.methodDefs]

        if recursive:
            parents = self.getGenParents(recursive=1)
            for p in parents:
                res.extend(p.getMethodDefs())

        return res

    def calculateStereoType(self):
        return XMI.calculateStereoType(self)

    def setStereoType(self, st):
        self.stereoTypes = [st]

    def getStereoType(self):
        if self.stereoTypes:
            return self.stereoTypes[0]
        else:
            return None

    def addStereoType(self, st):
        self.stereoTypes.append(st)

    def getStereoTypes(self):
        return self.stereoTypes

    def hasStereoType(self, sts):
        if type(sts) in (type(''), type(u'')):
            sts = [sts]

        for st in sts:
            if st in self.getStereoTypes():
                return 1

        return 0

    def getFullQualifiedName():
        return self.getName()

    def getPackage(self):
        ''' returns the package to which this object belongs '''
        return self.package

    def getPath(self):
        return [self.getName()]

    def getModuleName(self):
        ''' gets the name of the module the class is in '''
        return self.getTaggedValue('module') or self.getTaggedValue('module_name') or self.getCleanName()

    def annotate(self, key, value):
        #print "annotate", key, value
        self.annotations[key] = value

    def getAnnotation(self, name):
        return self.annotations.get(name, [])

    def addClientDependency(self, dep):
        self.clientDependencies.append(dep)
        
    def getClientDependencies(self, includeParents=False, dependencyStereotypes=None):
        res = self.clientDependencies
        
        if includeParents:
            o = self.getParent()
            if o:
                res.extend(o.getClientDependencies(includeParents=includeParents))
                    
                res.reverse()

        if dependencyStereotypes:
            res=[r for r in res if r.hasStereoType(dependencyStereotypes)]

        return res
    
    def getClientDependencyClasses(self, includeParents=False, 
        dependencyStereotypes=None, targetStereotypes=None): 
            
        res=[dep.getSupplier() for dep in self.getClientDependencies(
            includeParents=includeParents, dependencyStereotypes=dependencyStereotypes) if 
            dep.getSupplier() and dep.getSupplier().__class__.__name__ in ('XMIClass', 'XMIInterface')]
            
        if targetStereotypes:
            res=[r for r in res if r.hasStereoType(targetStereotypes)]
            
            
        return res
    
class StateMachineContainer:
    def __init__(self):
        self.statemachines = []

    def findStateMachines(self):

        ownedElement = getElementByTagName(self.domElement, 
            [XMI.OWNED_ELEMENT,XMI.OWNED_BEHAVIOR], default=None)

            
        if not ownedElement:
            ownedElement=self.domElement
            
        statemachines = getElementsByTagName(ownedElement, XMI.STATEMACHINE)
        #print 'statemachines1:', statemachines
        return statemachines

    def buildStateMachines(self, recursive=1):
        #print 'buildClasses:',self.getFilePath(includeRoot=1)
        statemachines = self.findStateMachines()

        for m in statemachines:
            sm = XMIStateMachine(m,parent=self)
            if sm.getName():
                #print 'StateMachine:', sm.getName(), sm.id
                #determine the correct product where it belongs
                products = [c.getPackage().getProduct() for c in sm.getClasses()]
                #associate the WF with the first product
                if products:
                    product = products[0]
                else:
                    products = self

                product.addStateMachine(sm)

        if recursive:
            for p in self.getPackages():
                p.buildStateMachines()

    def addStateMachine(self, sm, reparent=1):
        if not sm in self.statemachines:
            self.statemachines.append(sm)
            if reparent:
                sm.setParent(self)

        if hasattr(self, 'isProduct') and not self.isProduct():
            self.getProduct().addStateMachine(sm, reparent=0)

        if not hasattr(self, 'isProduct'):
            print 'addStateMachine:', self, self.package
            self.getPackage().getProduct().addStateMachine(sm, reparent=0)

    def getStateMachines(self):
        return self.statemachines


class XMIPackage(XMIElement, StateMachineContainer):
    project = None
    isroot = 0

    def __init__(self, el):
        XMIElement.__init__(self, el)
        StateMachineContainer.__init__(self)
        self.classes = []
        self.interfaces = []
        self.packages = []

    def initFromDOM(self, domElement=None):
        self.parentPackage = None
        XMIElement.initFromDOM(self, domElement)

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        return self.parent

    def getClasses(self, recursive=0):
        res = [c for c in self.classes]
        res = self.classes
        
        if recursive:
            res = list(res)
            for p in self.getPackages():
                res.extend(p.getClasses(recursive=1))
                
        return res

    def getAssociations(self, recursive=0):
        classes = self.getClassesAndInterfaces(recursive=recursive)
        res = []
        for c in classes:
            res.extend(c.getFromAssociations())
            
        return res
    
    def addClass(self, cl):
        self.classes.append(cl)
        cl.package = self

    def addInterface(self, cl):
        self.interfaces.append(cl)
        cl.package = self

    def getInterfaces(self, recursive=0):

        res = [c for c in self.classes]
        res = self.interfaces
        
        if recursive:
            res = list(res)
            for p in self.getPackages():
                res.extend(p.getClasses(recursive=1))
                
        return res
    
    def getClassesAndInterfaces(self, recursive=0):
        return self.getClasses(recursive=recursive)+ \
            self.getInterfaces(recursive=recursive)

    def getChildren(self):
        return self.children+self.getClasses() + self.getPackages() + self.getInterfaces()

    def addPackage(self, p):
        self.packages.append(p)
        p.parent = self

    def getPackages(self):
        return self.packages


    def buildPackages(self):
        packEls = XMI.getPackageElements(self.domElement)
        for p in packEls:
            if XMI.getName(p) == 'java':
                continue
            package = XMIPackage(p)
            self.addPackage(package)
            package.buildPackages()

    def buildClasses(self):
        #print 'buildClasses:', self.getFilePath(includeRoot=1)
        ownedElement = XMI.getOwnedElement(self.domElement)
        if not ownedElement:
            print 'warning: empty package:', self.getName()
            return

        classes = getElementsByTagName(ownedElement, XMI.CLASS) + \
           getElementsByTagName(ownedElement, XMI.ASSOCIATION_CLASS)
        for c in classes:
            if c.nodeName == XMI.ASSOCIATION_CLASS:
                xc = XMIAssociationClass(c, package=self)
            else:
                xc = XMIClass(c, package=self)
            if xc.getName():
                #print 'Class:', xc.getName(), xc.id
                self.addClass(xc)

        for p in self.getPackages():
            p.buildClasses()

    def buildInterfaces(self):
        #print 'buildInterfaces:', self.getFilePath(includeRoot=1)
        ownedElement = XMI.getOwnedElement(self.domElement)
        if not ownedElement:
            print 'warning: empty package:', self.getName()
            return

        classes = getElementsByTagName(ownedElement, XMI.INTERFACE)

        for c in classes:
            xc = XMIInterface(c, package=self)
            if xc.getName():
                #print 'Interface:', xc.getName(), xc.id
                self.addInterface(xc)

        for p in self.getPackages():
            p.buildInterfaces()

    def buildClassesAndInterfaces(self):
        self.buildInterfaces()
        self.buildClasses()

    def isRoot(self):
        return self.isroot or self.hasStereoType(['product', 'zopeproduct', 'Product', 'ZopeProduct'])

    isProduct = isRoot

    def getPath(self, includeRoot=1, absolute=0, parent=None):
        res = []
        o = self

        if self.isProduct():
            #products are always handled as top-level
            if includeRoot:
                return [o]
            else:
                return []

        while 1:
            if includeRoot:
                res.append(o)

            if o.isProduct():
                break

            if not o.getParent():
                break

            if o == parent:
                break

            if not includeRoot:
                res.append(o)

            o = o.getParent()

        res.reverse()
        return res

    def getFilePath(self, includeRoot=1, absolute=0):
        names = [p.getModuleName() for p in self.getPath(includeRoot=includeRoot, absolute=absolute)]
        if not names:
            return ''

        res = os.path.join(*names)
        return res

    def getRootPackage(self):
        o = self
        while not o.isRoot():
            o = o.getParent()

        return o

    def getProduct(self):
        o = self
        while not o.isProduct():
            o = o.getParent()

        return o

    def getProductName(self):
        return self.getProduct().getName()

    def getProductModuleName(self):
        return self.getProduct().getModuleName()


    def isSubPackageOf(self, parent):
        o = self
        #print 'isSubPackage:', self.getName(), parent.getName()
        while o:
            #print 'compare:', o.getName()
            if o == parent:
                #print 'ys'
                return 1

            o = o.getParent()

        return 0

    def getQualifiedName(self, ref, includeRoot=True):
        ''' returns the qualified name of that package, depending of the
            reference package 'ref' it generates an absolute path or
            a relative path if the pack(self) is a subpack of 'ref' '''

        path = self.getPath(includeRoot=includeRoot, parent=ref)

        return path


class XMIModel(XMIPackage):
    isroot = 1
    parent = None
    diagrams = {}
    diagramsByModel = {}

    def __init__(self, doc):
        self.document = doc
        self.content = XMI.getContent(doc)
        self.model = XMI.getModel(doc)
        XMIPackage.__init__(self, self.model)

    def findStateMachines(self):
        statemachines = getElementsByTagName(self.content, XMI.STATEMACHINE)
        statemachines.extend(getElementsByTagName(self.model, XMI.STATEMACHINE))

        #print 'statemachines:', statemachines

        ownedElement = XMI.getOwnedElement(self.domElement)
        statemachines.extend(getElementsByTagName(ownedElement, XMI.STATEMACHINE) )
        return statemachines

    def buildDiagrams(self):
        diagram_els = getElementsByTagName(self.content, XMI.DIAGRAM)
        for el in diagram_els:
            diagram = XMIDiagram(el)
            self.diagrams[diagram.getId()] = diagram
            self.diagramsByModel[diagram.getModelElementId()] = diagram

class XMIClass (XMIElement, StateMachineContainer):
    package = None
    isinterface = 0
    statemachine = None

    def __init__(self, *args, **kw):
        self.setPackage(kw.get('package', None))
        #print 'package:', self, self.package
        StateMachineContainer.__init__(self)
        XMIElement.__init__(self, *args, **kw)
        self.assocsTo = []
        self.assocsFrom = []
        self.genChildren = []
        self.genParents = []
        self.realizationChildren = []
        self.realizationParents = []
        self.internalOnly = 0
        self.type = self.name

        #self.isabstract = 0

    def setPackage(self, p):
        self.package = p

    def initFromDOM(self, domElement):
        XMIElement.initFromDOM(self, domElement)
        XMI.calcClassAbstract(self)
        XMI.calcVisibility(self)
        self.buildStateMachines(recursive=0)

    def isInternal(self):
        ''' internal class '''
        return self.internalOnly

    def getVisibility(self):
        return self.visibility

    def addGenChild(self, c):
        self.genChildren.append(c)

    def addGenParent(self, c):
        self.genParents.append(c)

    def getAttributeNames(self):
        return [a.getName() for a in self.getAttributeDefs()]

    def hasAttribute(self, a):
        return a in self.getAttributeNames()

    def getGenChildren(self, recursive=0):
        ''' generalization children '''

        res = [c for c in self.genChildren]

        if recursive:
            for r in res:
                res.extend(r.getGenChildren(1))

        return res

    def getGenChildrenNames(self, recursive=0):
        ''' returns the names of the generalization children '''
        return [o.getName() for o in self.getGenChildren(recursive=recursive) ]

    def getGenParents(self, recursive = 0):
        ''' generalization parents '''
        res = [c for c in self.genParents]

        if recursive:
            for r in res:
                res.extend(r.getGenParents(1))

        return res

    def buildChildren(self, domElement):

        for el in domElement.getElementsByTagName(XMI.ATTRIBUTE):
            att = XMIAttribute(el)
            att.setParent(self)
            self.addAttributeDef(att)
        for el in domElement.getElementsByTagName(XMI.METHOD):
            meth = XMIMethod(el)
            meth.setParent(self)
            self.addMethodDefs(meth)

        if XMI.getGenerationOption('default_field_generation'):
            if not self.hasAttribute('title'):
                title = XMIAttribute()
                title.id = 'title'
                title.name = 'title'
                title.setTaggedValue('widget:label_msgid', "label_title")
                title.setTaggedValue('widget:i18n_domain', "plone")
                title.setTaggedValue('widget:description_msgid', "help_title")
                title.setTaggedValue('searchable', 'python:1')
                title.setTaggedValue('accessor', 'Title')
                title.setParent(self)
                self.addAttributeDef(title, 0)

            if not self.hasAttribute('id'):
                id = XMIAttribute()
                id.id = 'id'
                id.name = 'id'
                id.setParent(self)
                id.setTaggedValue('widget:label_msgid', "label_short_name")
                id.setTaggedValue('widget:i18n_domain', "plone")
                id.setTaggedValue('widget:description_msgid', "help_short_name")

                self.addAttributeDef(id, 0)

    def isComplex(self):
        return 1

    def addAssocFrom(self, a):
        self.assocsFrom.append(a)

    def addAssocTo(self, a):
        self.assocsTo.append(a)

    def getToAssociations(self, aggtypes=['none'], 
                          aggtypesTo=['none']):
        # This code doesn't seem to work with below isDependent method
        return [a for a in self.assocsTo if a.fromEnd.aggregation in aggtypes  
                and a.toEnd.aggregation in aggtypesTo]


    def getFromAssociations(self, aggtypes=['none'], aggtypesTo=['none']):
        # This code doesn't seem to work with below isDependent method
        return [a for a in self.assocsFrom if a.fromEnd.aggregation in
                aggtypes and a.toEnd.aggregation in aggtypesTo]
        #return self.assocsFrom

    def isDependent(self):
        """ Return True if class is only accessible through composition

        Every object to which only composite associations point
        shouldn't be created independently.
        """
        aggs = self.getToAssociations(aggtypes=['aggregate'])
        comps = self.getToAssociations(aggtypes=['composite'])

        if comps and not aggs:
            res = 1
        else:
            res = 0

        # if one of the parents is dependent, count the class as dependent
        for p in self.getGenParents():
            if p.isDependent():
                res = 1

        return res

    def isAbstract(self):
        return self.isabstract

    def getSubtypeNames(self, recursive=0, **kw):
        ''' returns the non-intrinsic subtypes '''

        res = [o.getName() for o in self.getAggregatedClasses(recursive=recursive, **kw)]

        return res

    def getAggregatedClasses(self, recursive=0, filter=['class', 'interface'], **kw):
        ''' returns the non-intrinsic subtypes '''

        res = [o for o in self.subTypes if not o.isAbstract() ]

        if recursive:
            for sc in self.subTypes:
                res.extend([o for o in sc.getGenChildren(recursive=1)])

        res = [o for o in res if o.__class__.__name__ in ['XMI'+f.capitalize() for f in filter]]
        return res

    def isI18N(self):
        ''' if at least one method is I18N the class has to be treated as i18N '''
        for a in self.getAttributeDefs():
            if a.isI18N():
                return 1

        return 0

    def getPackage(self):
        return self.package

    getParent = getPackage

    def getRootPackage(self):
        return self.getPackage().getRootPackage()

    def isInterface(self):
        #print 'interface:', self.getName(), self.getStereoType()
        return self.isinterface  or self.getStereoType() == 'interface'
        # the second branch is for older XMI engines where interface is just a stereotype of a class


    # for relization stuff
    def addRealizationChild(self, c):
        self.realizationChildren.append(c)

    def addRealizationParent(self, c):
        self.realizationParents.append(c)

    def getRealizationChildren(self, recursive=0):
        ''' realization children '''

        res = [c for c in self.realizationChildren]

        if recursive:
            for r in res:
                res.extend(r.getRealizationChildren(1))

        return res

    def getRealizationChildrenNames(self, recursive=0):
        ''' returns the names of the realization children '''
        return [o.getName() for o in self.getRealizationChildren(recursive=recursive) ]

    def getRealizationParents(self):
        ''' generalization parents '''
        return self.realizationParents

    def getQualifiedModulePath(self, ref, pluginRoot='Products', forcePluginRoot=0, includeRoot=1):
        ''' returns the qualified name of the class, depending of the
            reference package 'ref' it generates an absolute path or
            a relative path if the pack(self) is a subpack of 'ref'
            if it belongs to a different root package it even needs a 'Products.'
            '''

        package = self.getPackage()
        if package == ref:
            path = package.getPath(includeRoot=includeRoot, parent=ref)
        else:
            if ref and self.package.getProduct() != ref.getProduct() or forcePluginRoot:
                path = package.getPath(includeRoot=1, parent=ref)
                path.insert(0, PseudoElement(name=pluginRoot))
            else:
                path = package.getPath(includeRoot=includeRoot, parent=ref)

        if not self.getPackage().hasStereoType('module'):
            path.append(self)

        return path

    def getQualifiedModuleName(self, ref=None, pluginRoot='Products', forcePluginRoot=0, includeRoot=1):
            
        path = self.getQualifiedModulePath(ref, pluginRoot=pluginRoot, 
                                         forcePluginRoot=forcePluginRoot, 
                                         includeRoot=includeRoot)

        res =  '.'.join([p.getModuleName() for p in path if p])
        return res


    def getQualifiedName(self, ref=None, pluginRoot='Products', forcePluginRoot=0, 
                         includeRoot=1):
        name = self.getQualifiedModuleName(ref, pluginRoot=pluginRoot, 
                                         forcePluginRoot=forcePluginRoot, 
                                         includeRoot=includeRoot)
        res = name+'.'+self.getCleanName()
        return res

    def setStateMachine(self, sm):
        self.statemachine = sm

    def getStateMachine(self):
        return self.statemachine


class XMIInterface(XMIClass):
    isinterface = 1
    pass


class XMIMethodParameter(XMIElement):
    default = None
    has_default = 0

    def getDefault(self):
        return self.default

    def hasDefault(self):
        return self.has_default

    def findDefault(self):
        defparam = getElementByTagName(self.domElement, XMI.PARAM_DEFAULT, None)
        #print defparam
        if defparam:
            default = XMI.getExpressionBody(defparam)
            if default :
                self.default = default
                self.has_default = 1
                #print 'default:', repr(self.default)

    def initFromDOM(self, domElement):
        XMIElement.initFromDOM(self, domElement)
        if domElement:
            self.findDefault()

    def getExpression(self):
        ''' returns the param name and param=default expr if a default is defined '''
        if self.getDefault():
            return "%s=%s" % (self.getName(), self.getDefault())
        else:
            return self.getName()

class XMIMethod (XMIElement):
    params = []
    def findParameters(self):
        self.params = []
        parElements = self.domElement.getElementsByTagName(XMI.METHODPARAMETER)
        for p in parElements:
            self.addParameter(XMIMethodParameter(p))
            #print self.params

    def initFromDOM(self, domElement):
        XMIElement.initFromDOM(self, domElement)
        XMI.calcVisibility(self)
        if domElement:
            self.findParameters()

    def getVisibility(self):
        return self.visibility

    def getParams(self):
        return self.params

    def getParamNames(self):
        return [p.getName() for p in self.params]

    def getParamExpressions(self):
        ''' returns the param names or paramname=default for each param in a list '''
        return [p.getExpression() for p in self.params]

    def addParameter(self, p):
        if p.getName() != 'return':
            self.params.append(p)

    def testmethodName(self):
        """ Return generated name of test method

        userCannotAdd => test_userCannotAdd
        user_cannot_add => test_user_cannot_add
        etcetera
        """
        # The olde way was a bit longish. Something like
        # testTestmyclassnameTestfoldercontainssomething().
        # old = 'test%s%s' % (self.getParent().getCleanName().capitalize(), 
        #                     self.getCleanName().capitalize())
        # The new version starts with 'test_' with the unmodified name
        # after it.
        name = 'test_%s' % self.getCleanName()
        return name

class XMIAttribute (XMIElement):
    default = None
    has_default = 0

    def getDefault(self):
        return self.default

    def hasDefault(self):
        return self.has_default

    def calcType(self):
        return XMI.calcDatatype(self)

    def findDefault(self):
        initval = getElementByTagName(self.domElement, XMI.ATTRIBUTE_INIT_VALUE, None)
        if initval:
            default = XMI.getExpressionBody(initval)
            if default :
                self.default = default
                self.has_default = 1
                #print 'default:', repr(self.default)

    def initFromDOM(self, domElement):
        XMIElement.initFromDOM(self, domElement)
        XMI.calcVisibility(self)
        if domElement:
            self.calcType()
            self.findDefault()
            self.mult = XMI.getMultiplicity(domElement,1,1)

    def isI18N(self):
        ''' with a stereotype 'i18N' or the taggedValue i18n == '1' an attribute is treated as i18n'''
        return self.getStereoType() == 'i18n' or self.getTaggedValue('i18n')  == '1'

    def getVisibility(self):
        return self.visibility

    def getMultiplicity(self):
        return self.mult

    def getLowerBound(self):
        return self.getMultiplicity()[0]

    def getUpperBound(self):
        return self.getMultiplicity()[1]


class XMIAssocEnd (XMIElement):
    def initFromDOM(self, el):
        XMIElement.initFromDOM(self, el)
        self.isNavigable = toBoolean(getAttributeOrElement(el, 'isNavigable', default=0))
        pid = XMI.getAssocEndParticipantId(el)
        if pid:
            self.obj = allObjects[pid]
            self.mult = XMI.getMultiplicity(el)
            self.aggregation = XMI.getAssocEndAggregation(el)
        else:
            print 'Association end missing for association end:'+self.getId()

        #print 'rel:%s navigable:%s' %(self.getName(), self.isNavigable)

    def getTarget(self):
        return self.obj
    
    def getMultiplicity(self):
        return self.mult

    def getLowerBound(self):
        return self.getMultiplicity()[0]

    def getUpperBound(self):
        return self.getMultiplicity()[1]

class XMIAssociation (XMIElement):
    fromEnd = None
    toEnd = None

    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.calcEnds()

    def calcEnds(self):
        #print 'Association:', domElement, self.id
        ends = self.domElement.getElementsByTagName(XMI.ASSOCEND)
        assert len(ends) == 2

        #print 'trying assoc'
        self.fromEnd = XMIAssocEnd(ends[0])
        self.toEnd = XMIAssocEnd(ends[1])

        self.fromEnd.setParent(self)
        self.toEnd.setParent(self)

    def getParent(self):
        ''' '''
        if self.fromEnd:
            return self.fromEnd.getTarget()

class XMIAssociationClass (XMIClass, XMIAssociation):
    isAssociationClass = 1

    def initFromDOM(self, domElement=None):
        XMIClass.initFromDOM(self, domElement)
        self.calcEnds()

class XMIAbstraction(XMIElement):
    pass


class XMIDependency(XMIElement):
    client = None
    supplier = None
    
    def getSupplier(self):
        return self.supplier
    
    def getClient(self):
        return self.client

    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.calcEnds()

    def calcEnds(self):
        #print 'Association:', domElement, self.id
        client_el = getElementByTagName(self.domElement, XMI.DEP_CLIENT)
        clid = XMI.getIdRef(getSubElement(client_el))
        self.client = self.allObjects[clid]

        supplier_el = getElementByTagName(self.domElement, XMI.DEP_SUPPLIER)
        suppid = XMI.getIdRef(getSubElement(supplier_el))
        self.supplier = self.allObjects[suppid]
        
        self.client.addClientDependency(self)
        
    def getParent(self):
        ''' '''
        if self.client:
            return self.client
    
#-----------------------------------
# here comes the Workflow support
#-----------------------------------

class XMIStateContainer(XMIElement):

    def __init__(self, *args, **kwargs):
        self.states = []
        XMIElement.__init__(self, *args, **kwargs)


    def addState(self, state):
        self.states.append(state)
        state.setParent(self)

    def getStates(self, no_duplicates=None):
        ret = []
        for s in self.states:
            if no_duplicates:
                flag_exists = 0
                for r in ret:
                    if s.getName() == r.getName():
                        flag_exists = 1
                        break
                if flag_exists:
                    continue
            ret.append(s)
        return ret

    def getStateNames(self, no_duplicates=None):
        return [s.getName() for s in self.getStates(no_duplicates=no_duplicates) if s.getName()]

    def getCleanStateNames(self, no_duplicates=None):
        return [s.getCleanName() for s in self.getStates(no_duplicates=no_duplicates) if s.getName()]


class XMIStateMachine(XMIStateContainer):

    def init(self):
        self.transitions = []
        self.classes = []

    def __init__(self, *args, **kwargs):
        self.init()
        self.setParent(kwargs.get('parent',None))
        XMIStateContainer.__init__(self, *args, **kwargs)
        #print 'created statemachine:', self.getId()

    def initFromDOM(self, domElement=None):
        XMIStateContainer.initFromDOM(self, domElement)
        self.buildTransitions()
        self.buildStates()
        self.associateClasses()

    def associateClasses(self):
        context = getElementByTagName(self.domElement, XMI.STATEMACHINE_CONTEXT,None)
        if context:
            clels = getSubElements(context)
            for clel in clels:
                clid = XMI.getIdRef(clel)
                #print 'CLID:', clel, clid
                cl = allObjects[clid]
                self.addClass(cl)
        else:
            self.addClass(self.getParent())
            
    def addTransition(self, transition):
        self.transitions.append(transition)
        transition.setParent(self)

    def getTransitions(self, no_duplicates = None):
        if not no_duplicates:
            return self.transitions

        tran = {}
        for t in self.transitions:
            if not t.getCleanName():
                continue
            if not t.getCleanName() in tran.keys():
                tran.update({t.getCleanName():t})
                #print "add transition", t.getCleanName(), t.getProps()
                continue
            for tname in tran:
                if t.getCleanName() == tname and t.hasStereoType('primary'):
                    #print "overrules transition", tname, t.getProps()
                    tran.update({tname:t})

        return [tran[tname] for tname in tran]

    def getTransitionNames(self, no_duplicates=None):
        return [t.getName() for t in self.getTransitions(no_duplicates=no_duplicates) if t.getName()]

    def buildStates(self):
        sels = getElementsByTagName(self.domElement, XMI.SIMPLESTATE, recursive=1)
        for sel in sels:
            state = XMIState(sel)
            self.addState(state)

        sels = getElementsByTagName(self.domElement, XMI.PSEUDOSTATE, recursive=1)
        for sel in sels:
            state = XMIState(sel)
            if getAttributeValue(sel, XMI.PSEUDOSTATE_KIND, None) == 'initial' or sel.getAttribute('kind') == 'initial':
                print 'initial state:', state.getCleanName()
                state.isinitial = 1
            self.addState(state)

        sels = getElementsByTagName(self.domElement, XMI.FINALSTATE, recursive=1)
        for sel in sels:
            state = XMIState(sel)
            self.addState(state)

    def buildTransitions(self):
        tels = getElementsByTagName(self.domElement, XMI.TRANSITION, recursive=1)
        for tel in tels:
            tran = XMIStateTransition(tel)
            self.addTransition(tran)

    def getClasses(self):
        return self.classes

    def getClassNames(self):
        return [cl.getName() for cl in self.getClasses()]

    def addClass(self, cl):
        self.classes.append(cl)
        cl.setStateMachine(self)

    def getAllPermissionNames(self):
        ret = []
        for s in self.getStates():
            pd = s.getPermissionsDefinitions()
            for p in pd:
                perm = p['permission'].strip()
                if perm not in ret:
                    ret.append(str(perm))
        return ret

    def getInitialState(self):
        states = self.getStates()
        for s in states:
            if s.isInitial():
                return s

        for s in states:
            for k, v in s.getTaggedValues().items():
                if k == 'initial_state':
                    return s
        return states[0]

    def getAllTransitionActions(self):
        res = []
        for t in self.getTransitions():
            if t.getAction():
                res.append(t.getAction())
        return res

    def getTransitionActionByName(self, name):
        for t in self.getTransitions():
            if t.getAction():
                if t.getAction().getBeforeActionName() == name or \
                   t.getAction().getAfterActionName() == name:
                    return t.getAction()
        return None

    def getAllTransitionActionNames(self, before=True, after=True):
        actionnames = Set()
        actions = self.getAllTransitionActions()
        for action in actions:
            if before and action.getBeforeActionName():
                actionnames.add(action.getBeforeActionName())
            if after and action.getAfterActionName():
                actionnames.add(action.getAfterActionName())
        return list(actionnames)

    def getAllRoles(self, ignore=[]):
        roles = []
        ignore.append('label') # reserved name to set the title
        for tran in self.getTransitions(no_duplicates=1):
            dummy = [roles.append(r.strip()) \
                     for r in tran.getGuardRoles().split(';') \
                     if not (r.strip() in roles or r.strip() in ignore)]

        for state in self.getStates():
            perms = state.getPermissionsDefinitions()
            sroles = []
            dummy = [[sroles.append(j) for j in i] \
                     for i in [d['roles'] for d in perms] \
                    ]
            dummy = [roles.append(r.strip()) \
                     for r in sroles \
                     if not (r.strip() in roles or r.strip() in ignore)]
                     
        return [r for r in roles if r]

class XMIStateTransition(XMIElement):
    targetState = None
    action = None
    guard = None

    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.buildEffect()
        self.buildGuard()

    def buildEffect(self):
        el = getElementByTagName(self.domElement, XMI.TRANSITION_EFFECT, None)
        if not el:
            return

        actel = getSubElement(el)
        self.action = XMIAction(actel)
        self.action.setParent(self)

    def buildGuard(self):
        el = getElementByTagName(self.domElement, XMI.TRANSITION_GUARD, default=None)
        if not el:return

        guardel = getSubElement(el)
        self.guard = XMIGuard(guardel)

    def setTargetState(self, state):
        self.targetState = state

    def getTargetState(self):
        return self.targetState

    def getTargetStateName(self):
        if self.getTargetState():
            return self.getTargetState().getName()
        else:
            return None

    def getAction(self):
        return self.action

    def getActionName(self):
        if self.action:
            return self.action.getName()

    def getBeforeActionName(self):
        if self.action:
            return self.action.getBeforeActionName()

    def getAfterActionName(self):
        if self.action:
            return self.action.getAfterActionName()

    def getActionExpression(self):
        if self.action:
            return self.action.getExpression()

    def getProps(self):
        d_ret = {}
        d_expr = {'guard_permissions' : self.getGuardPermissions, 
                  'guard_roles' : self.getGuardRoles, 
                  'guard_expr' : self.getGuardExpr}
        for k, v in d_expr.items():
            g = v()
            if g:
                d_ret.update({k:g})
        return repr(d_ret)

    def getGuardRoles(self):
        if not self.guard:
            return ''
        geb = self.guard.getExpressionBody()
        for ge in geb.split('|'):
            ge = ge.strip()
            if ge.startswith('guard_roles:'):
                return str(ge[12:])
        return ''

    def getGuardPermissions(self):
        if not self.guard:
            return ''
        geb = self.guard.getExpressionBody()
        for ge in geb.split('|'):
            ge = ge.strip()
            if ge.startswith('guard_permissions:'):
                return str(ge[18:])
        return ''

    def getGuardExpr(self):
        if not self.guard:
            return ''
        geb = self.guard.getExpressionBody()
        for ge in geb.split('|'):
            ge = ge.strip()
            if ge.startswith('guard_expr:'):
                return str(ge[11:])
        return ''    

    def getTriggerType(self):
        """ Return the Trigger Type, following what is defined by DCWorkflow
            0 : Automatic
            1 : User Action (default)
            2 : Workflow Method
        """
        try:
            return int(self.getTaggedValue('trigger_type'))
        except ValueError:
            return 1   


class XMIAction(XMIElement):
    expression = None
    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.expression = XMI.getExpressionBody(self.domElement, tagname=XMI.ACTION_EXPRESSION)
        #print '!!!ACTIONEX:', self.getExpressionBody()

    def getExpressionBody(self):
        return self.expression

    def getSplittedName(self, padding=1):
        ''' when the name contains a semicolon the name specifies two
            actions: the one before the transition and the one after the transition
        '''

        res = self.getName().split(';')
        if len(res) == 1 and padding:
            return ['', res[0]]
        else:
            return res

    def getBeforeActionName(self):
        return self.getSplittedName()[0]

    def getAfterActionName(self):
        return self.getSplittedName()[1]

class XMIGuard(XMIElement):
    expression = None
    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.expression = XMI.getExpressionBody(self.domElement, tagname=XMI.BOOLEAN_EXPRESSION)
        #print '!!!GUARDEX:', self.getExpressionBody()

    def getExpressionBody(self):
        return self.expression


class XMIState(XMIElement):
    isinitial = 0

    def __init__(self, *args, **kwargs):
        self.incomingTransitions = []
        self.outgoingTransitions = []
        XMIElement.__init__(self, *args, **kwargs)

    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.associateTransitions()

    def associateTransitions(self):

        vertices = getElementByTagName(self.domElement, XMI.STATEVERTEX_OUTGOING, default=None)
        if vertices:
            for vertex in getSubElements(vertices):
                trid = XMI.getIdRef(vertex)
                tran = allObjects[trid]
                self.addOutgoingTransition(tran)

        vertices = getElementByTagName(self.domElement, XMI.STATEVERTEX_INCOMING, default=None)
        if vertices:
            for vertex in getSubElements(vertices):
                trid = XMI.getIdRef(vertex)
                tran = allObjects[trid]
                self.addIncomingTransition(tran)

        #print 'transitions:', self.getIncomingTransitions(), self.getOutgoingTransitions()

    def addIncomingTransition(self, tran):
        self.incomingTransitions.append(tran)
        tran.setTargetState(self)

    def addOutgoingTransition(self, tran):
        self.outgoingTransitions.append(tran)

    def getIncomingTransitions(self):
        return self.incomingTransitions

    def getOutgoingTransitions(self):
        return self.outgoingTransitions

    def getPermissionsDefinitions(self):
        """ return a list of dictionaries with permission definitions

        Each dict contains a key 'permission' with a string value and
        a key 'roles' with a list of strings as value and a key
        'acquisition' with value 1 or 0.
        """

        ### for the records:
        ### this method contains lots of generation logic. in fact this
        ### should move over to the WorkflowGenerator.py and reduce here in
        ### just deliver the pure data
        ### the parser should really just parse to be as independent as possible

        # permissions_mapping (abbreviations for lazy guys)
        # keys are case insensitive
        permission_mapping = {'access' : 'Access contents information', 
              'view'   : 'View', 
              'modify' : 'Modify portal content'}
        tagged_values = self.getTaggedValues()
        permission_definitions = []

        for tag, tag_value in tagged_values.items():
            # list of tagged values that are NOT permissions
            non_permissions = ['initial_state', 'documentation', 'label']
            if tag in non_permissions or not tag_value:
                continue
            tag = tag.strip()
            # look up abbreviations if any
            permission = permission_mapping.get(tag.lower(), tag)
            # split roles-string into list
            roles = [str(r.strip()) for r in tag_value.split(',') if r.strip()]
            # verify if this permission is acquired
            nv = 'acquire'
            acquisition = 0
            if nv in roles:
                acquisition = 1
                roles.remove(nv)
            permission_definitions.append({'permission' : permission, 
                        'roles' : roles, 
                        'acquisition' : acquisition})

        # If View was defined but Access was not defined, the Access
        # permission should be generated with the same rights defined
        # for View

        has_access = 0
        has_view = 0
        v = {}
        for permission_definition in permission_definitions:
            if (permission_definition.get('permission', None) ==
                permission_mapping['access']): 
                has_access = 1
            if (permission_definition.get('permission', None) ==
                permission_mapping['view']):
                v = permission_definition
                has_view = 1
        if has_view and not has_access:
            permission = permission_mapping['access']
            permission_definitions.append({'permission': permission,
                                           'roles': v['roles'], 
                                           'acquisition': v['acquisition']})
        return permission_definitions

        # If not permissions were defined, uses the default values

        # Removed (~optilude) - this is a terrible mis-feature. It must be
        # possible to avoid setting these properties so that they can be
        # acquired from parent.

        # for p in permission_mapping.values():
        #    has_permission = 0
        #    for r in permission_definitions:
        #        if r.get('permission', None) == p:
        #            has_permission = 1
        #            break
        #    if not has_permission:
        #        permission_definitions.append({'permission' : p, 
        #                    'roles' : ['Owner', 'Manager']})

        # end of getPermissionsDefinitions()

    def isInitial(self):
        return self.isinitial

    def getTitle(self, generator):
        """ Return the title for a state

        The original is in the templates/create_workflow.py:
        <dtml-var "_['sequence-item'].getDocumentation(striphtml=generator.atgenerator.striphtml) or _['sequence-item'].getName()">

        This method mimics that, but also looks at the TGV 'label'
        """
        fromDocumentation = self.getDocumentation(striphtml=generator.atgenerator.striphtml)
        fromTaggedValue = self.getTaggedValue('label', None)
        default = self.getName()
        return fromTaggedValue or fromDocumentation or default

class XMICompositeState(XMIState):
    def __init__(self, *args, **kwargs):
        XMIState.__init__(self, *args, **kwargs)
        XMIStateMachine.init(self)


#necessary for Poseidon because in Poseidon i cannot assign a name to a statemachine, 
#so i have to pull the name of the statemachine from the diagram :(((((
diagrams = {}
diagramsByModel = {}

class XMIDiagram(XMIElement):
    modelElement = None

    def initFromDOM(self, domElement=None):
        XMIElement.initFromDOM(self, domElement)
        self.buildSemanticBridge()

    def buildSemanticBridge(self):
        ownerel = getElementByTagName(self.domElement, XMI.DIAGRAM_OWNER, default=None)
        if not ownerel:
            print 'no ownerel'
            return

        model_el = getElementByTagName(ownerel, XMI.DIAGRAM_SEMANTICMODEL_BRIDGE_ELEMENT, default=None, recursive=1)
        if not model_el:
            print 'no modelel'
            return

        el = getSubElement(model_el)
        idref = XMI.getIdRef(el)
        self.modelElement = allObjects.get(idref, None)


        #workaround for the Poseidon problem
        if issubclass(self.modelElement.__class__, XMIStateMachine):
            self.modelElement.setName(self.getName())


    def getModelElementId(self):
        if self.modelElement:
            return self.modelElement.getId()

    def getModelElement(self):
        return self.modelElement
#----------------------------------------------------------


def buildDataTypes(doc):
    global datatypes

    dts = doc.getElementsByTagName(XMI.DATATYPE)

    for dt in dts:
        datatypes[str(dt.getAttribute('xmi.id'))] = dt

    classes = [c for c in doc.getElementsByTagName(XMI.CLASS) ]

    for dt in classes:
        datatypes[str(dt.getAttribute('xmi.id'))] = dt

    interfaces = [c for c in doc.getElementsByTagName(XMI.INTERFACE) ]

    for dt in interfaces:
        datatypes[str(dt.getAttribute('xmi.id'))] = dt

    interfaces = [c for c in doc.getElementsByTagName(XMI.ACTOR) ]

    for dt in interfaces:
        datatypes[str(dt.getAttribute('xmi.id'))] = dt

    XMI.collectTagDefinitions(doc)

def buildStereoTypes(doc):
    global stereotypes
    sts = doc.getElementsByTagName(XMI.STEREOTYPE)

    for st in sts:
        id = st.getAttribute('xmi.id')
        if not id:continue
        stereotypes[str(id)] = st
        #print 'stereotype:', id, XMI.getName(st)

def buildHierarchy(doc, packagenames):
    """ builds Hierarchy out of the doc """
    global datatypes
    global stereotypes
    global datatypenames
    global packages


    datatypes = {}
    stereotypes = {}
    datatypenames = ['int', 'void', 'string', ]

    #doc = res.model

    buildDataTypes(doc)
    buildStereoTypes(doc)
    res = XMIModel(doc)

    #print 'packagenames:', packagenames
    packageElements = doc.getElementsByTagName(XMI.PACKAGE)
    if packagenames: #XXX: TODO support for more than one package
        packageElements = doc.getElementsByTagName(XMI.PACKAGE)
        for p in packageElements:
            n = XMI.getName(p)
            print 'package name:', n
            if n in packagenames:
                doc = p
                print 'package found'
                break

    buildDataTypes(doc)

    res.buildPackages()
    res.buildClassesAndInterfaces()
    res.buildStateMachines()
    res.buildDiagrams()

    #print 'res:', res.getName()

    #pure datatype classes should not be generated!
    #print 'datatypenames:', datatypenames
    for c in res.getClasses(recursive=1):
        if c.getName() in datatypenames and not c.hasStereoType(XMI.generate_datatypes):
            c.internalOnly = 1
            print 'internal class (not generated):', c.getName()

    XMI.buildRelations(doc, allObjects)
    XMI.buildGeneralizations(doc, allObjects)
    XMI.buildRealizations(doc, allObjects)
    XMI.buildDependencies(doc, allObjects)
    
    return res


def parse(xschemaFileName=None, xschema=None, packages=[], generator=None,**kw):
    """ """
    global XMI
    if xschemaFileName:
        doc = minidom.parse(xschemaFileName)
    else:
        doc = minidom.parseString(xschema)

    try:
        xmi = doc.getElementsByTagName('XMI')[0]
        xmiver = str(xmi.getAttribute('xmi.version'))
        print 'XMI version:', xmiver
        if xmiver >= "1.2":
            print 'using xmi 1.2+ parser'
            XMI = XMI1_2(**kw)
        elif xmiver >= "1.1":
            print 'using xmi 1.1+ parser'
            XMI = XMI1_1(**kw)
        else:
            print 'using xmi 1.1+ parser'
            XMI = XMI1_0(**kw)

    except:
        print 'no version info found, taking XMI1_0'
        pass

    XMI.generator = generator

    root = buildHierarchy(doc, packages)

    return root
