<dtml-var "generator.generateModuleInfoHeader(package, name='setuphandlers')">
import logging
logger = logging.getLogger('<dtml-var "product_name">: setuphandlers')
from Products.<dtml-var "product_name">.config import PROJECTNAME
from Products.<dtml-var "product_name">.config import DEPENDENCIES
<dtml-if "hasvocabularies or hasrelations">
from config import product_globals
import os
from Globals import package_home
</dtml-if>
<dtml-if "hasvocabularies">
from Products.ATVocabularyManager.config import TOOL_NAME as ATVOCABULARYTOOL
</dtml-if>
from Products.CMFCore.utils import getToolByName
import transaction
##code-section HEAD
##/code-section HEAD

def installGSDependencies(context):
    """Install dependend profiles."""

    # XXX Hacky, but works for now. has to be refactored as soon as generic
    # setup allows a more flexible way to handle dependencies.

    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">':
        # the current import step is triggered too many times, this creates infinite recursions
        # therefore, we'll only run it if it is triggered from proper context
        logger.debug("installGSDependencies will not run in context %s" % shortContext)
        return
    logger.info("installGSDependencies started")
    dependencies = [<dtml-var "', '.join(dependend_profiles)">]
    if not dependencies:
        return

    site = context.getSite()
    setup_tool = getToolByName(site, 'portal_setup')
    qi = getToolByName(site, 'portal_quickinstaller')
    for dependency in dependencies:
        logger.info("  installing GS dependency %s:" % dependency)
        if dependency.find(':') == -1:
            dependency += ':default'
        old_context = setup_tool.getImportContextID()
        setup_tool.setImportContext('profile-%s' % dependency)
        importsteps = setup_tool.getImportStepRegistry().sortSteps()
        excludes = [
            u'<dtml-var "product_name">-QI-dependencies',
            u'<dtml-var "product_name">-GS-dependencies'
        ]
        importsteps = [s for s in importsteps if s not in excludes]
        for step in importsteps:
            logger.debug("     running import step %s" % step)
            setup_tool.runImportStep(step) # purging flag here?
            logger.debug("     finished import step %s" % step)
        # let's make quickinstaller aware that this product is installed now
        product_name = dependency.split(':')[0]
        qi.notifyInstalled(product_name)
        logger.debug("   notified QI that %s is installed now" % product_name)
        # maybe a savepoint is welcome here (I saw some in optilude's examples)? maybe not? well...
        transaction.savepoint()
        if old_context: # sometimes, for some unknown reason, the old_context is None, believe me
            setup_tool.setImportContext(old_context)
        logger.debug("   installed GS dependency %s:" % dependency)

    # re-run some steps to be sure the current profile applies as expected
    importsteps = setup_tool.getImportStepRegistry().sortSteps()
    filter = [
        u'typeinfo',
        u'workflow',
        u'membranetool',
        u'factorytool',
        u'content_type_registry',
        u'membrane-sitemanager'
    ]
    importsteps = [s for s in importsteps if s in filter]
    for step in importsteps:
        setup_tool.runImportStep(step) # purging flag here?
    logger.info("installGSDependencies finished")

def installQIDependencies(context):
    """This is for old-style products using QuickInstaller"""
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        logger.debug("installQIDependencies will not run in context %s" % shortContext)
        return
    logger.info("installQIDependencies starting")
    site = context.getSite()
    qi = getToolByName(site, 'portal_quickinstaller')

    for dependency in DEPENDENCIES:
        if qi.isProductInstalled(dependency):
            logger.info("   re-Installing QI dependency %s:" % dependency)
            qi.reinstallProducts([dependency])
            transaction.savepoint() # is a savepoint really needed here?
            logger.debug("   re-Installed QI dependency %s:" % dependency)
        else:
            if qi.isProductInstallable(dependency):
                logger.info("   installing QI dependency %s:" % dependency)
                qi.installProduct(dependency)
                transaction.savepoint() # is a savepoint really needed here?
                logger.debug("   installed dependency %s:" % dependency)
            else:
                logger.info("   QI dependency %s not installable" % dependency)
                raise "   QI dependency %s not installable" % dependency
    logger.info("installQIDependencies finished")

<dtml-if "notsearchabletypes">
def setupHideTypesFromSearch(context):
    """hide selected classes in the search form"""
    # XXX use https://svn.plone.org/svn/collective/DIYPloneStyle/trunk/profiles/default/properties.xml
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    portalProperties = getToolByName(site, 'portal_properties')
    siteProperties = getattr(portalProperties, 'site_properties')
    for klass in <dtml-var "repr(notsearchabletypes)">:
        propertyid = 'types_not_searched'
        lines = list(siteProperties.getProperty(propertyid) or [])
        if klass not in lines:
            lines.append(klass)
            siteProperties.manage_changeProperties(**{propertyid: lines})

</dtml-if>
<dtml-if "hidemetatypes">
def setupHideMetaTypesFromNavigations(context):
    """hide selected classes in the search form"""
    # XXX use https://svn.plone.org/svn/collective/DIYPloneStyle/trunk/profiles/default/properties.xml
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    portalProperties = getToolByName(site, 'portal_properties')
    siteProperties = getattr(portalProperties, 'site_properties')
    for klass in <dtml-var "repr(hidemetatypes)">:
        propertyid = 'metaTypesNotToList'
        lines = list(siteProperties.getProperty(propertyid) or [])
        if klass not in lines:
            lines.append(klass)
            siteProperties.manage_changeProperties(**{propertyid: lines})

</dtml-if>
<dtml-if "toolnames">
def setupHideToolsFromNavigation(context):
    """hide tools"""
    # uncatalog tools
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    toolnames = <dtml-var "repr(toolnames)">
    portalProperties = getToolByName(site, 'portal_properties')
    navtreeProperties = getattr(portalProperties, 'navtree_properties')
    if navtreeProperties.hasProperty('idsNotToList'):
        for toolname in toolnames:
            try:
                portal[toolname].unindexObject()
            except:
                pass
            current = list(navtreeProperties.getProperty('idsNotToList') or [])
            if toolname not in current:
                current.append(toolname)
                kwargs = {'idsNotToList': current}
                navtreeProperties.manage_changeProperties(**kwargs)

</dtml-if>
<dtml-if "catalogmultiplexed">
def setupCatalogMultiplex(context):
    """ Configure CatalogMultiplex.

    explicit add classes (meta_types) be indexed in catalogs (white)
    or removed from indexing in a catalog (black)
    """
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    #dd#
    muliplexed = <dtml-var "repr([m.getCleanName() for m in catalogmultiplexed or []])">

    atool = getToolByName(site, 'archetypes_tool')
    catalogmap = {}
<dtml-in "catalogmultiplexed">
<dtml-let klass="_['sequence-item']">
    catalogmap['<dtml-var "klass.getCleanName()">'] = {}
<dtml-if "generator.getOption('catalogmultiplex:white', klass, None)">
    catalogmap['<dtml-var "klass.getCleanName()">']['white'] = [<dtml-var "', '.join( ['\'%s\'' % s.strip() for s in generator.getOption('catalogmultiplex:white', klass).split(',')])">]
</dtml-if>
<dtml-if "generator.getOption('catalogmultiplex:black', klass, None)">
    catalogmap['<dtml-var "klass.getCleanName()">']['black'] = [<dtml-var "', '.join( ['\'%s\'' % s.strip() for s in generator.getOption('catalogmultiplex:black', klass).split(',')])">]
</dtml-if>
</dtml-let>
</dtml-in>
    for meta_type in catalogmap:
        submap = catalogmap[meta_type]
        current_catalogs = Set([c.id for c in atool.getCatalogsByType(meta_type)])
        if 'white' in submap:
            for catalog in submap['white']:
                if not getToolByName(site, catalog, False):
                    raise AttributeError, 'Catalog "%s" does not exist!' % catalog
                current_catalogs.update([catalog])
        if 'black' in submap:
            for catalog in submap['black']:
                if catalog in current_catalogs:
                    current_catalogs.remove(catalog)
        atool.setCatalogsByType(meta_type, list(current_catalogs))

</dtml-if>
<dtml-if "hasrelations">
def installRelations(context):
    """imports the relations.xml file"""
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    qi = getToolByName(site, 'portal_quickinstaller')
    if not qi.isProductInstalled('Relations'):
        # you can't declare relations unless you first install the Relations product
        logger.info("Installing Relations Product")
        qi.installProducts(['Relations'])
    relations_tool = getToolByName(site, 'relations_library')
    xmlpath = os.path.join(package_home(product_globals), 'data',
                           'relations.xml')
    f = open(xmlpath)
    xml = f.read()
    f.close()
    relations_tool.importXML(xml)

</dtml-if>
<dtml-if "hasvocabularies">
def installVocabularies(context):
    """creates/imports the atvm vocabs."""
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    # Create vocabularies in vocabulary lib
    atvm = getToolByName(site, ATVOCABULARYTOOL)
    vocabmap = {<dtml-var "'),\n        '.join( [s[1:] for s in repr(generator.vocabularymap[package.getProductName()]).split(')')] )">}
    for vocabname in vocabmap.keys():
        if not vocabname in atvm.contentIds():
            atvm.invokeFactory(vocabmap[vocabname][0], vocabname)

        if len(atvm[vocabname].contentIds()) < 1:
            if vocabmap[vocabname][0] == "VdexVocabulary":
                vdexpath = os.path.join(
                    package_home(product_globals), 'data', '%s.vdex' % vocabname)
                if not (os.path.exists(vdexpath) and os.path.isfile(vdexpath)):
                    logger.warn('No VDEX import file provided at %s.' % vdexpath)
                    continue
                try:
                    #read data
                    f = open(vdexpath, 'r')
                    data = f.read()
                    f.close()
                except:
                    logger.warn("Problems while reading VDEX import file "+\
                                "provided at %s." % vdexpath)
                    continue
                # this might take some time!
                atvm[vocabname].importXMLBinding(data)
            else:
                pass

</dtml-if>

<dtml-if "memberclasses">
from Products.membrane.interfaces import ICategoryMapper
from Products.membrane.utils import generateCategorySetIdForType
from Products.remember.utils import getAdderUtility

def setupMemberTypes(context):
# Adds our types to MemberDataContainer.allowed_content_types
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
    types_tool = getToolByName(site, 'portal_types')
    act = types_tool.MemberDataContainer.allowed_content_types
    types_tool.MemberDataContainer.manage_changeProperties(allowed_content_types=act+(<dtml-in memberclasses>'<dtml-var "_['sequence-item'].getCleanName()">', </dtml-in>))
    # registers with membrane tool ...
    membrane_tool = getToolByName(site, 'membrane_tool')
<dtml-in "memberclasses">
    <dtml-let mtype="_['sequence-item']">
    <dtml-if "mtype.getTaggedValue('active_workflow_states','private,public')">
    
    membrane_tool.registerMembraneType('<dtml-var "_['sequence-item'].getCleanName()">')
    cat_map = ICategoryMapper(membrane_tool)

    states = <dtml-var "[s.strip() for s in mtype.getTaggedValue('active_workflow_states','private,public').split(',')]">
    cat_set = generateCategorySetIdForType('<dtml-var "mtype.getCleanName()">')
    cat_map.replaceCategoryValues(cat_set,
                                       'active',
                                       states)
    </dtml-if>
    
    <dtml-if "mtype.hasStereoType(['default_member_type','default'])">
    
    adder = getAdderUtility(site)
    adder.default_member_type='<dtml-var "mtype.getCleanName()">'    
    </dtml-if>
    </dtml-let>
    
    # print >> out, SetupMember(site, member_type='<dtml-var "_['sequence-item'].getCleanName()">', register=<dtml-var "str(_['sequence-item'].getTaggedValue('register', False))">).finish()
</dtml-in>
</dtml-if>

def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""

    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    wft = getToolByName(context.getSite(), 'portal_workflow')
    wft.updateRoleMappings()

<dtml-if "'postInstall' not in parsedModule.functions.keys()">

def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    shortContext = context._profile_path.split('/')[-3]
    if shortContext != '<dtml-var "product_name">': # avoid infinite recursions
        return
    site = context.getSite()
<dtml-else>
<dtml-var "parsedModule.functions['postInstall'].getSrc()">
</dtml-if>


##code-section FOOT
##/code-section FOOT
