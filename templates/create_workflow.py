# 
#
# Generated by dumpDCWorkflow.py written by Sebastien Bigaret
# Original workflow id/title: answer_workflow/CMF default workflow [Revision 2]
# Date: 2003/12/02 00:52:22.473 GMT+1
#
# WARNING: this dumps does NOT contain any scripts you might have added to
# the workflow, IT IS YOUR RESPONSABILITY TO MAKE BACKUPS FOR THESE SCRIPTS.
#
# No script detected in this workflow
# 
"""
Programmatically creates a workflow type
"""
__version__ = "$Revision: 1.5 $"[11:-2]

from Products.CMFCore.WorkflowTool import addWorkflowFactory

from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.ExternalMethod.ExternalMethod import ExternalMethod

def setup<dtml-var "statemachine.getCleanName()">(self, wf):
    "..."
    productname='<dtml-var "package.getCleanName()">'
    wf.setProperties(title='<dtml-var "statemachine.getCleanName()">')

    for s in <dtml-var "repr(statemachine.getStateNames())">:
        wf.states.addState(s)
    for t in <dtml-var "repr(statemachine.getTransitionNames())">:
        wf.transitions.addTransition(t)


    for v in ['review_history', 'comments', 'time', 'actor', 'action']:
        wf.variables.addVariable(v)
    for l in ['reviewer_queue']:
        wf.worklists.addWorklist(l)
    for p in <dtml-var "repr(statemachine.getAllPermissionNames())">:
        wf.addManagedPermission(p)
        

    ## Initial State
    wf.states.setInitialState('<dtml-var "statemachine.getInitialState().getCleanName()">')

    ## States initialization
    
    <dtml-in "[s for s in statemachine.getStates() if s.getCleanName()]">
    
    sdef = wf.states['<dtml-var "_['sequence-item'].getCleanName()">']
    sdef.setProperties(title="""<dtml-var "_['sequence-item'].getDocumentation(striphtml=generator.atgenerator.striphtml) or _['sequence-item'].getCleanName()">""",
                       transitions=<dtml-var "repr([t.getCleanName() for t in _['sequence-item'].getOutgoingTransitions()])">)
    sdef.setPermission('Access contents information', 0, ['Manager', 'Owner'])
    sdef.setPermission('Modify portal content', 0, ['Manager', 'Owner'])

    </dtml-in>

    ## Transitions initialization
    <dtml-in "[t for t in statemachine.getTransitions() if t.getCleanName()]">
    <dtml-let tran="_['sequence-item']">

    <dtml-if "tran.getAction()">

    ##creation of workflow scripts
    wf_scriptname='<dtml-var "tran.getAction().getCleanName()">'
    if not wf_scriptname in wf.scripts.objectIds():
        wf.scripts._setObject(wf_scriptname,ExternalMethod(wf_scriptname, wf_scriptname, productname+'.<dtml-var "statemachine.getCleanName()">','<dtml-var "tran.getAction().getCleanName()">'))
    </dtml-if>


    tdef = wf.transitions['<dtml-var "tran.getCleanName()">']
    tdef.setProperties(title="""<dtml-var "tran.getTaggedValue('label') or tran.getCleanName()">""",
                       new_state_id="""<dtml-var "tran.getTargetStateName()">""",
                       trigger_type=1,
                       script_name="""""",
                       after_script_name="""<dtml-var "tran.getActionName() or ''">""",
                       actbox_name="""<dtml-var "tran.getTaggedValue('label') or tran.getCleanName()">""",
                       actbox_url="""""",
                       actbox_category="""workflow""",
                       props={'guard_permissions': 'View', 'guard_roles': 'Anonymous; Owner; Manager'},
                       )
                       
    </dtml-let>
    </dtml-in>


    ## State Variable
    wf.variables.setStateVar('review_state')

    ## Variables initialization
    vdef = wf.variables['review_history']
    vdef.setProperties(description="""Provides access to workflow history""",
                       default_value="""""",
                       default_expr="""state_change/getHistory""",
                       for_catalog=0,
                       for_status=0,
                       update_always=0,
                       props={'guard_permissions': 'Request review; Review portal content'})

    vdef = wf.variables['comments']
    vdef.setProperties(description="""Comments about the last transition""",
                       default_value="""""",
                       default_expr="""python:state_change.kwargs.get('comment', '')""",
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['time']
    vdef.setProperties(description="""Time of the last transition""",
                       default_value="""""",
                       default_expr="""state_change/getDateTime""",
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['actor']
    vdef.setProperties(description="""The ID of the user who performed the last transition""",
                       default_value="""""",
                       default_expr="""user/getId""",
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    vdef = wf.variables['action']
    vdef.setProperties(description="""The last transition""",
                       default_value="""""",
                       default_expr="""transition/getId|nothing""",
                       for_catalog=0,
                       for_status=1,
                       update_always=1,
                       props=None)

    ## Worklists Initialization
    ldef = wf.worklists['reviewer_queue']
    ldef.setProperties(description="""Reviewer tasks""",
                       actbox_name="""Pending (%(count)d)""",
                       actbox_url="""%(portal_url)s/search?review_state=pending""",
                       actbox_category="""global""",
                       props={'guard_permissions': 'Review portal content', 'var_match_review_state': 'pending'})


def create<dtml-var "statemachine.getCleanName()">(self, id):
    "..."
    ob = DCWorkflowDefinition(id)
    setup<dtml-var "statemachine.getCleanName()">(self, ob)
    return ob

addWorkflowFactory(create<dtml-var "statemachine.getCleanName()">,
                   id='<dtml-var "statemachine.getCleanName()">',
                   title='<dtml-var "statemachine.getTaggedValue('label') or statemachine.getCleanName()">')

<dtml-if "statemachine.getAllTransitionActions()">

## Workflow scripts
## <dtml-var "parsedModule.functions.keys()">    
<dtml-in "statemachine.getAllTransitionActions()">
<dtml-let action="_['sequence-item']">

<dtml-if "action.getCleanName() not in parsedModule.functions.keys()">
def <dtml-var "action.getCleanName()">(self,state_change,**kw):
<dtml-var "utils.indent(action.getExpressionBody() or 'pass' ,1)">

<dtml-else>
<dtml-var "parsedModule.functions[action.getCleanName()].getSrc()">
</dtml-if>
</dtml-let>
</dtml-in>

</dtml-if>