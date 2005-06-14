from AccessControl import ClassSecurityInfo
from Products.Archetypes.Widget import TypesWidget

from types import ListType, TupleType, StringTypes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName

from Products.Archetypes.Field import ObjectField,encode,decode
from Products.Archetypes.Registry import registerField
from Products.Archetypes.utils import DisplayList
from Products.Archetypes import config as atconfig
from Products.Archetypes.Widget import *
from Products.generator import i18n

from Products.<dtml-var "klass.getPackage().getCleanName()"> import config

<dtml-var "generator.getProtectedSection(parsed_class,'module-header')">
<dtml-var "generator.generateDependentImports(klass)">
class <dtml-var "klass.getCleanName()">(<dtml-if "klass.getGenParents()"><dtml-var "','.join([p.getCleanName() for p in klass.getGenParents()])"><dtml-else>TypesWidget</dtml-if>):
    ''' <dtml-var "klass.getDocumentation()">'''

<dtml-var "generator.getProtectedSection(parsed_class,'class-header',1)">
<dtml-var "generator.generateImplements(klass,['TypesWidget']+[p.getCleanName() for p in klass.getGenParents()])">
    _properties = <dtml-var parentname>._properties.copy()
    _properties.update({
        'macro' : '<dtml-var "klass.getName()">',
        'size' : '30',
        'maxlength' : '255',
<dtml-var "generator.getProtectedSection(parsed_class,'widget-properties',2)">
        })

    security = ClassSecurityInfo()

    
<dtml-in "generator.getMethodsToGenerate(klass)[0]">
<dtml-let m="_['sequence-item']">
<dtml-if "m.getParent().__class__.__name__=='XMIInterface'"> 
    #from Interface <dtml-var "m.getParent().getName()">:
</dtml-if>
<dtml-if "parsed_class and m.getCleanName() in parsed_class.methods.keys()">
<dtml-var "parsed_class.methods[m.getCleanName()].getSrc()">    
<dtml-else>

    def <dtml-var "m.getName()">(self,<dtml-var "','.join(m.getParamNames())">):
        pass
</dtml-if>
</dtml-let>
</dtml-in>
<dtml-in "generator.getMethodsToGenerate(klass)[1]">
<dtml-var "_['sequence-item'].getSrc()">            
</dtml-in>


<dtml-var "generator.getProtectedSection(parsed_class,'module-footer')">




