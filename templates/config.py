#
# Product configuration. This contents of this module will be imported into
# __init__.py and every content type module.
#
# If you wish to perform custom configuration, you may put a file AppConfig.py
# in your product's root directory. This will be included in this file if
# found.
#
<dtml-if "[cn for cn in generator.getGeneratedClasses(package) if cn.hasStereoType(generator.cmfmember_stereotype)]">
from Products.CMFMember.CMFMemberPermissions import ADD_MEMBER_PERMISSION
</dtml-if>

PROJECTNAME = "<dtml-var "package.getProductName ()">"

DEFAULT_ADD_CONTENT_PERMISSION = "<dtml-var "default_creation_permission">"
<dtml-if "creation_permissions">
ADD_CONTENT_PERMISSIONS = {
<dtml-in "creation_permissions">
<dtml-let perm="_['sequence-item']">
    '<dtml-var "perm[0]">': <dtml-var "perm[1]">,
</dtml-let>
</dtml-in>
}
</dtml-if>

product_globals=globals()

try:
    from Products.<dtml-var "package.getProductName ()">.AppConfig import *
except ImportError:
    pass

# End of config.py
