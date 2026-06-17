"""Hook into Alliance Auth"""

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

# AA Industry App
from industry import urls


class PersonalIndustryMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Personal Industry"),
            "fas fa-cube fa-fw",
            "industry:personal_dashboard",
            navactive=["industry:personal_dashboard", "industry:index"],
        )

    def render(self, request):
        if request.user.has_perm("industry.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


class CorporateIndustryMenuItem(MenuItemHook):
    """Menu entry for Corporate Industry"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Corporate Industry"),
            "fas fa-building fa-fw",
            "industry:corporate_dashboard",
            navactive=["industry:corporate_dashboard"],
        )

    def render(self, request):
        if request.user.has_perm("industry.corp_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_personal_menu():
    """Register the personal menu item"""
    return PersonalIndustryMenuItem()


@hooks.register("menu_item_hook")
def register_corporate_menu():
    """Register the corporate menu item"""
    return CorporateIndustryMenuItem()


class MemberOrdersMenuItem(MenuItemHook):
    """Menu entry for Member Orders (Self Service)"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Member Orders"),
            "fas fa-shopping-cart fa-fw",
            "industry:orders_dashboard",
            navactive=[
                "industry:orders_dashboard",
                "industry:create_order",
                "industry:view_quote",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_member_orders_menu():
    """Register the member orders menu item"""
    return MemberOrdersMenuItem()


class IndustrialistMenuItem(MenuItemHook):
    """Menu entry for Industrialist Dashboard"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Industrialist Dash"),
            "fas fa-hammer fa-fw",
            "industry:industrialist_dashboard",
            navactive=[
                "industry:industrialist_dashboard",
                "industry:industrialist_leaderboard",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry.industrialist_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_industrialist_menu():
    """Register the industrialist menu item"""
    return IndustrialistMenuItem()


class DirectorMenuItem(MenuItemHook):
    """Menu entry for Director Control Panel"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Director CP"),
            "fas fa-chess-king fa-fw",
            "industry:director_dashboard",
            navactive=[
                "industry:director_dashboard",
                "industry:director_inventory",
                "industry:director_config",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry.corp_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_director_menu():
    """Register the director menu item"""
    return DirectorMenuItem()


@hooks.register("url_hook")
def register_urls():
    """Register app urls"""

    return UrlHook(urls, "industry", r"^industry/")
