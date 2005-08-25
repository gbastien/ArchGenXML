"""
Class stereotypes

  The following stereotypes may be applied to classes to alter their behaviour:

stub, odStub -- Don't generate this class. Stub classes may be used for clarity where the model refers to classes from other products, such as when these are used as composited objects or base classes. 

hidden -- Generate the class, but turn off global_allow, thereby making it unavailable in the portal by default. Note that if you use composition to specify that a type should be addable only inside another (folderish) type, then global_allow will be turned off automatically, and the type be made addable only inside the designated parent. (You can use aggregation instead of composition to make a type both globally addable and explicitly addable inside another folderish type) 

archetype -- Explicitly specify that a class represents an Archetypes type. This may be necessary if you are including a class as a base class for another class and ArchGenXML is unable to determine whether the parent class is an Archetype or not. Without knowing that the parent class in an Archetype, ArchGenXML cannot ensure that the parent's schema is available in the derived class.

folder -- Make the type folderish. Folderish types can contain other types. Note that if you use composition and aggregation to specify relationships between types, the container for the aggregation will automatically be made folderish.

ordered -- For folderish types, include folder ordering support. This will allow the user to re-order items in the folder manually.

CMFMember, member -- The class will be treated as a CMFMember member type. It will derive from CMFMember's Member class and be installed as a member data type.

portal_tool -- Install the type as a portal tool. A tool is a singleton which can be accessed with 'getToolByName' from 'Products.CMFCore.utils', typically used to hold shared state or configuration information, or methods which are not bound to a particular object.


variable_schema -- Include variable schema support in a content type by deriving from the VariableSchema mixin class. 

Method stereotypes

  The following stereotypes may be applied to methods to alter their behaviour:

action -- Generate a CMF action which will be available on the object. The tagged values 'action' (defaults to method name), 'id' (defaults to method name), 'category' (defaults to 'object'), 'label' (defaults to method name), 'condition' (defaults to empty), and 'permission' (defaults to empty) set on the method and mapped to the equivalent fields of any CMF action can be used to control the behaviour of the action. 

view -- Generate an action as above, but also copy an empty page template to the skins directory with the same name as the method and set this up as the target of the action. If the template exists, it is not overwritten.

form -- Generate an action as above, but also copy an empty controller page template to the skins directory with the same name as the method and set this up as the target of the action. If the template exists, it is not overwritten.

portlet_view, portlet -- Create a simple portlet page template with the same name as the method. You can override the name by setting the 'view' tagged value on the method. If you add a tagged value 'autoinstall' and set it to 'left' or 'right', the portlet will be automatically installed with your product in either the left or the right slot. If the page template already exists, it will not be overwritten.

Field stereotypes

  The following stereotypes may be applied to fields to alter their behaviour:

vocabulary -- TODO: Describe ATVocabularyManager support

vocabulary_item -- TODO: Describe ATVocabularyManager support

vocabulary: -- TODO: Describe ATVocbularyManager support


"""
